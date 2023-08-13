from fastapi import APIRouter, Form, File, UploadFile, HTTPException, status, Depends
import shutil
from sqlalchemy import select, insert, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import SessionLocal
from schemas.deal import DealLook
import datetime as ddd
from db.models.sessions import sessions
from schemas.favorite_deal import FavoriteDeal, FavoriteDealList
from db.models.plans import plans
from db.models.deals import deals
import time
from sqlmodel import select
import os
from datetime import datetime, time as dt_time
from time import mktime
from fastapi.responses import FileResponse
from db.models.favorite_deals import favorite_deals

router = APIRouter()


async def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()


async def check_session(db, session):
    result = await db.execute(select(sessions).where(sessions.c.session == session).where(
        sessions.c.time_start >= time.time() - 24 * 60 * 60))
    result = result.fetchone()
    await db.execute(update(sessions).where(sessions.c.session == session).values(time_start=time.time()))
    await db.commit()
    return result


async def can_add(db, user_id, deal_id):
    result = await db.execute(select(plans).where(plans.c.user_id == user_id))
    our_plans = result.fetchall()
    for plan in our_plans:
        result = await db.execute(select(deals).where(
            and_(
                deals.c.plan_id == plan.plan_id,
                deals.c.group_number == deals.c.group_number
            )))
        our_deals = result.fetchall()
        for deal in our_deals:
            if deal.id == deal_id:
                return True
    return False


async def deal_exists(db, user_id, deal_id):
    select_stmt = select(favorite_deals).where(and_(favorite_deals.c.deal_id == deal_id,
                                                    favorite_deals.c.user_id == user_id
                                                    ))
    result = await db.execute(select_stmt)
    return result.fetchone() is not None


@router.post("/add_favorite_deal", response_model=dict)
async def add_favorite_deal(need_deal: FavoriteDeal, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=need_deal.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if await can_add(db, session_in_db.user_id, need_deal.deal_id):
        if not await deal_exists(db, session_in_db.user_id, need_deal.deal_id):
            await db.execute(favorite_deals.insert().values(user_id=session_in_db.user_id, deal_id=need_deal.deal_id))
            await db.commit()
            return {'message': 'success'}
        else:
            return {'message': 'deal already added'}
    return {'message': 'you do not have access to this deal'}


@router.post("/delete_favorite_deal")
async def delete_favorite_deal(need_deal: FavoriteDeal, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=need_deal.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if await deal_exists(db, session_in_db.user_id, need_deal.deal_id):
        delete_stmt = favorite_deals.delete().where(and_(favorite_deals.c.deal_id == need_deal.deal_id,
                                                         favorite_deals.c.user_id == session_in_db.user_id))
        await db.execute(delete_stmt)
        await db.commit()
        return {'message': 'success'}
    return {'message': "you don't have this deal"}


@router.post("/favorite_deal_list")
async def favorite_deal_list(ses: FavoriteDealList, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    deal_list = []
    result = await db.execute(select(favorite_deals).where(favorite_deals.c.user_id == session_in_db.user_id))
    for elem in result.fetchall():
        deal = await db.execute(select(deals).where(deals.c.id == elem.deal_id))
        deal = deal.fetchone()
        deal_info = {
            'id': deal.id,
            'day': deal.day,
            'day_beautiful': ddd.datetime.fromtimestamp(deal.day).strftime('%d/%m/%Y'),
            'shop_price': deal.shop_price,
            'amazon_price': deal.amazon_price,
            'photo': deal.photo,
            'product_name': deal.product_name,
            'shop_name': deal.shop_name,
            'shop_link': deal.shop_link,
            'amazon_link': deal.amazon_link,
            'plan_id': deal.plan_id,
            'group_number': deal.group_number,
            'roi': deal.roi,
            'net_profit': deal.net_profit,
            'bsr_percent': deal.bsr_percent,
            'fba_seller': deal.fba_seller,
            'fbm_seller': deal.fbm_seller,
            'est_monthly_sale': deal.est_monthly_sale,
            'asin': deal.asin,
            'category': deal.category,
            'brs_rank': deal.brs_rank,
            'upc_ean': deal.upc_ean,
            'restriction_check': deal.restriction_check,
            'favorite': True
        }
        deal_list.append(deal_info)
    return {'result': deal_list}
