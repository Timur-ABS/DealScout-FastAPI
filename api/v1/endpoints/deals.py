from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import secrets
import uuid
import shutil
from sqlalchemy import select, insert, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import SessionLocal
from db.models.user import users
from schemas.deal import DealLook
from db.models.sessions import sessions
from db.models.deals import deals
from db.models.reset_password import reset_password
from schemas.user import User as UserSchema, UserCreate, UserLogin, UserReset, UserChangeLogin, UserChangePhoto
import time
from datetime import datetime, time as dt_time
from time import mktime
import random
import string
from typing import Dict

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


@router.post("/add/{ses}", response_model=dict)
async def add_deal(ses: str, day: int = Form(...), shop_price: float = Form(...), amazon_price: float = Form(...),
                   shop_name: str = Form(...), shop_link: str = Form(...), amazon_link: str = Form(...),
                   plan_id: int = Form(...), group_number: int = Form(...), roi: str = Form(...),
                   net_profit: str = Form(...), bsr_percent: str = Form(...), fba_seller: str = Form(...),
                   fbm_seller: str = Form(...), est_monthly_sale: str = Form(...), asin: str = Form(...),
                   brs_rank: str = Form(...), upc_ean: str = Form(...), restriction_check: str = Form(...),
                   image: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_in_db.user_id != 1:
        return {"error": "You don't have enough permissions"}
    try:
        time_stam = await start_of_day_timestamp() + day * 24 * 3600
        deal = {"day": time_stam, "shop_price": int(round(shop_price, 2) * 100),
                "amazon_price": int(round(amazon_price, 2) * 100),
                "photo": "None", "shop_name": shop_name, "shop_link": shop_link,
                "amazon_link": amazon_link, "plan_id": plan_id, "group_number": group_number,
                "roi": roi, "net_profit": net_profit, "bsr_percent": bsr_percent,
                "fba_seller": fba_seller, "fbm_seller": fbm_seller,
                "est_monthly_sale": est_monthly_sale, "asin": asin, "brs_rank": brs_rank,
                "upc_ean": upc_ean, "restriction_check": restriction_check}
        result = await db.execute(insert(deals).values(**deal).returning(deals))  # insert deal to the database
        created_deal = result.fetchone()
        file_location = f"images/{time_stam}_{plan_id}_{group_number}_{created_deal.id}.{image.filename.split('.')[1]}"
        await db.execute(update(deals).where(deals.c.id == created_deal.id).values(photo=file_location))
        await db.commit()
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(image.file, file_object)
        return {"info": f"File '{image.filename}' uploaded successfully, Deal: '{asin}' added"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/look", response_model=dict)
async def look_deal(need_deal: DealLook, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=need_deal.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
