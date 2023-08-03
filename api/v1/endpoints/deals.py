from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import shutil
from sqlalchemy import select, insert, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import SessionLocal
from schemas.deal import DealLook, DownloadDeal
import datetime as ddd
from db.models.sessions import sessions
from db.models.deals import deals
from db.models.plans import plans
import time
import os
from datetime import datetime, time as dt_time
from time import mktime
import pandas as pd
from fastapi.responses import FileResponse
import tempfile

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
                   category: str = Form(...), shop_name: str = Form(...), shop_link: str = Form(...),
                   amazon_link: str = Form(...),
                   plan_id: int = Form(...), group_number: int = Form(...), roi: str = Form(...),
                   net_profit: str = Form(...), bsr_percent: str = Form(...), fba_seller: str = Form(...),
                   fbm_seller: str = Form(...), est_monthly_sale: str = Form(...), asin: str = Form(...),
                   brs_rank: str = Form(...), upc_ean: str = Form(...), restriction_check: str = Form(...),
                   image: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_in_db.user_id != 1 and session_in_db.user_id != 4:
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
                "category": category, "upc_ean": upc_ean, "restriction_check": restriction_check}
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
    today = await start_of_day_timestamp()
    back = {
        "today": 0, "week": today - 24 * 7 * 60 * 60,
        "month": today - 24 * 30 * 60 * 60, "all": today - 10 * 24 * 360 * 60 * 60
    }

    if need_deal.plan_id != 0:
        result = await db.execute(select(plans).where(
            and_(
                plans.c.user_id == session_in_db.user_id,
                plans.c.plan_id == need_deal.plan_id,
                plans.c.end_time >= today - back.get(need_deal.time)
            )))
    else:
        result = await db.execute(select(plans).where(
            and_(
                plans.c.user_id == session_in_db.user_id,
                plans.c.end_time >= today - back.get(need_deal.time)
            )))
    our_plans = result.fetchall()
    answer = {'deals': []}
    for plan in our_plans:
        result = await db.execute(select(deals).where(
            and_(
                deals.c.plan_id == plan.plan_id,
                deals.c.group_number == deals.c.group_number,
                deals.c.day >= today - back.get(need_deal.time)
            )))
        our_deals = result.fetchall()
        for deal in our_deals:
            deal_info = {
                'id': deal.id,
                'day': deal.day,
                'day_beautiful': ddd.datetime.fromtimestamp(deal.day).strftime('%d/%m/%Y'),
                'shop_price': deal.shop_price,
                'amazon_price': deal.amazon_price,
                'photo': deal.photo,
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
                'restriction_check': deal.restriction_check
            }
            answer['deals'].append(deal_info)
    return answer


@router.post("/look_size", response_model=dict)
async def look_deal_size(need_deal: DealLook, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=need_deal.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    today = await start_of_day_timestamp()
    back = {
        "today": 0, "week": today - 24 * 7 * 60 * 60,
        "month": today - 24 * 30 * 60 * 60, "all": today - 10 * 24 * 360 * 60 * 60
    }

    if need_deal.plan_id != 0:
        result = await db.execute(select(plans).where(
            and_(
                plans.c.user_id == session_in_db.user_id,
                plans.c.plan_id == need_deal.plan_id,
                plans.c.end_time >= today - back.get(need_deal.time)
            )))
    else:
        result = await db.execute(select(plans).where(
            and_(
                plans.c.user_id == session_in_db.user_id,
                plans.c.end_time >= today - back.get(need_deal.time)
            )))
    our_plans = result.fetchall()
    answer = {'len': 0}
    for plan in our_plans:
        result = await db.execute(select(deals).where(
            and_(
                deals.c.plan_id == plan.plan_id,
                deals.c.group_number == deals.c.group_number,
                deals.c.day >= today - back.get(need_deal.time)
            )))
        our_deals = result.fetchall()
        answer['len'] += len(our_deals)
    return answer


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
                'day': deal.day,
                'day_beautiful': ddd.datetime.fromtimestamp(deal.day).strftime('%d/%m/%Y'),
                'shop_price': deal.shop_price,
                'amazon_price': deal.amazon_price,
                'photo': deal.photo,
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
                'restriction_check': deal.restriction_check
            }
            all_deals.append(deal_info)

    df = pd.DataFrame(all_deals)
    fd, path = tempfile.mkstemp(suffix=".xlsx")

    try:
        with os.fdopen(fd, 'w') as tmp:
            # Записываем датафрейм в Excel-файл
            df.to_excel(tmp.name, index=False)

        # Возвращаем файл как FileResponse
        return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            filename="deals.xlsx")

    finally:
        os.remove(path)  # удаляем файл после использования


@router.get("/photos/{photo_path:path}")
async def read_item(photo_path: str):
    if not photo_path.startswith("images/"):
        raise HTTPException(status_code=400, detail="Invalid photo path")
    if os.path.exists(photo_path) and os.path.isfile(photo_path):
        return FileResponse(photo_path)
    else:
        raise HTTPException(status_code=404, detail="Photo not found")
