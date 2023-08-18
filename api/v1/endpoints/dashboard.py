from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import SessionLocal
from schemas.dashboard import DownloadDeal, SeaMyPLan, ProfitDay
from db.models.sessions import sessions
from db.models.deals import deals
from db.models.plans import plans
from db.models.profit_days import profit_days
import time
from sqlmodel import select
from sqlalchemy import or_
from datetime import datetime
from fastapi.responses import FileResponse
import pandas as pd
import tempfile
import datetime as ddd
from datetime import datetime, time as dt_time
from time import mktime

router = APIRouter()


# Dependency
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


async def start_of_day_timestamp():
    now = datetime.now().date()
    start_of_day = datetime.combine(now, dt_time())
    return int(mktime(start_of_day.timetuple()))


@router.post("/my_active_plans")
async def sea_my_plans(ses: SeaMyPLan, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    result = await db.execute(select(plans).where(and_(plans.c.user_id == session_in_db.user_id,
                                                       plans.c.end_time > int(time.time()))))

    our_plans = result.fetchall()
    result = {"plans": []}
    for plan in our_plans:
        result["plans"].append({'plan_id': plan.plan_id})
    return result


@router.post("/processed_goods")
async def sea_my_plans(ses: SeaMyPLan, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {
        "Electronics": "2.5K",
        "Clothing": "3.4K",
        "Home & Kitchen": "4.1K",
        "Toys & Games": "1.9K",
        "Beauty & Personal Care": "2.8K",
        "Books": "3.2K",
        "Sports & Outdoors": "2.7K",
        "Automotive": "1.6K",
        "Other": "3.3K"
    }


@router.post("/my_plans")
async def sea_my_plans(ses: SeaMyPLan, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    result = await db.execute(select(plans).where(plans.c.user_id == session_in_db.user_id))
    our_plans = result.fetchall()[::-1]
    our_plans = our_plans[0:min(len(our_plans), 5)][::-1]
    result = {"plans": []}
    for plan in our_plans:
        dt_object = datetime.fromtimestamp(plan.end_time)
        result["plans"].append({'plan_id': plan.plan_id,
                                'end_time': dt_object.strftime("%d-%m-%Y")})
    return result


@router.post('/fill_profit_day_{day}_{profit}')
async def fill_profit_day(day: int, profit: float, ses: ProfitDay, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_in_db.user_id != 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect user")
    d = await start_of_day_timestamp() + day * 24 * 60 * 60
    result = await db.execute(select(profit_days).where(profit_days.c.time_stamp_day == d))
    if result.fetchone():
        await db.execute(update(profit_days)
                         .where(profit_days.c.time_stamp_day == d)
                         .values(profit=int(profit * 100)))
        await db.commit()
        return {'message': 'update'}
    await db.execute(profit_days.insert().values(time_stamp_day=d, profit=int(profit * 100)))
    await db.commit()
    return {'message': 'add'}


@router.post('/profit_day')
async def profit_day(ses: ProfitDay, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    today = await start_of_day_timestamp()
    yesterday = today - 24 * 60 * 60
    result = await db.execute(
        select(profit_days).where(
            or_(profit_days.c.time_stamp_day == today, profit_days.c.time_stamp_day == yesterday)
        )
    )

    days = result.fetchall()
    result = {
        'today': {'profit': days[1].profit / 100,
                  'date': datetime.fromtimestamp(days[1].time_stamp_day).strftime("%d-%m-%Y, %A")
                  },
        'yesterday': {'profit': days[0].profit / 100,
                      'date': datetime.fromtimestamp(days[0].time_stamp_day).strftime("%d-%m-%Y, %A")
                      },
        'tommorow': {
            'date': datetime.fromtimestamp(days[1].time_stamp_day + 24 * 60 * 60).strftime("%d-%m-%Y, %A")
        }
    }
    return result


@router.post("/download_all_deals")
async def download_all_deals(ses: DownloadDeal, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    all_deals = []
    result = await db.execute(select(plans).where(plans.c.user_id == session_in_db.user_id))
    our_plans = result.fetchall()
    for plan in our_plans:
        result = await db.execute(select(deals).where(
            and_(
                deals.c.plan_id == plan.plan_id,
                deals.c.group_number == deals.c.group_number
            )))
        our_deals = result.fetchall()
        for deal in our_deals:
            deal_info = {
                'id': deal.id,
                'day': ddd.datetime.fromtimestamp(deal.day).strftime('%d/%m/%Y'),
                'shop_price': deal.shop_price / 100,
                'amazon_price': deal.amazon_price / 100,
                'shop_name': deal.shop_name,
                'shop_link': deal.shop_link,
                'amazon_link': deal.amazon_link,
                'plan_id': deal.plan_id,
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
                'restriction_check': deal.restriction_check
            }
            all_deals.append(deal_info)

    df = pd.DataFrame(all_deals)

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        df.to_excel(tmp.name, index=False)
        tmp_path = tmp.name

    return FileResponse(
        path=tmp_path,
        filename="deals.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=deals.xlsx"},
    )
