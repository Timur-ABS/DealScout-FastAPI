from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import SessionLocal
from schemas.dashboard import DownloadDeal, SeaMyPLan, ProfitDay
from db.models.sessions import sessions
from db.models.plans import plans
import time
from sqlmodel import select

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


@router.post("/all_history")
async def all_history(ses: SeaMyPLan, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses.session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    result = await db.execute(select(plans).where(plans.c.user_id == session_in_db.user_id))
    our_plans = result.fetchall()
    result = {}
    for plan in our_plans:
        result["plans"].append({'plan_id': plan.plan_id,
                                'buy_time': datetime.fromtimestamp(plan.buy_time.time_stamp_day).strftime("%d-%m-%Y"),
                                'end_time': datetime.fromtimestamp(plan.end_time.time_stamp_day).strftime("%d-%m-%Y")
                                })
    return result
