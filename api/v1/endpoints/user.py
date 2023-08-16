import uuid
import secrets
import base64
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select, insert, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import SessionLocal
from db.models.user import users
from db.models.sessions import sessions
from db.models.reset_password import reset_password
from db.models.plans import plans
from schemas.user import User as UserSchema, UserCreate, UserLogin, UserReset, UserChangeLogin, UserAddPlan
import time
import random
import string
from typing import Dict
import time
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


async def create_user_session(db, user_id):
    # Удаляем все предыдущие сессии
    await db.execute(
        sessions.delete().where(sessions.c.user_id == user_id)
    )

    # Создаем новую сессию
    session = secrets.token_hex(32)
    insert_stmt = sessions.insert().values(session=session, user_id=user_id, time_start=int(time.time()))
    await db.execute(insert_stmt)
    await db.commit()
    return session


async def check_session(db, session):
    result = await db.execute(select(sessions).where(
        and_(sessions.c.session == session, sessions.c.time_start >= time.time() - 24 * 60 * 60)))
    result = result.fetchone()
    await db.execute(update(sessions).where(sessions.c.session == session).values(time_start=time.time()))
    await db.commit()
    return result


async def generate_unique_code(db: AsyncSession, length=8):
    while True:
        my_code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        stmt = select(users).where(users.c.my_code == my_code)
        result = await db.execute(stmt)
        user = result.fetchone()

        if not user:
            return my_code


@router.get("/{ses}")
async def read_user(ses: str, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    result = await db.execute(select(users).where(users.c.id == session_in_db.user_id))
    user_in_db = result.fetchone()
    data = {'login': user_in_db.login,
            'my_code': user_in_db.my_code,
            'referral_code': user_in_db.referral_code,
            'mailing': user_in_db.mailing}
    try:
        with open(user_in_db.photo, "rb") as photo:
            photo_encoded = base64.b64encode(photo.read()).decode('utf-8')
            data["photo"] = photo_encoded
            return data
    except:
        data["photo"] = "no photo"
        return data


@router.get("/session_in_db/{ses}")
async def session_in_db(ses: str, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {'message': True}


@router.post("/registration", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if a user with the given login or email already exists
    stmt = select(users).where(or_(users.c.login == user.login, users.c.email == user.email))
    result = await db.execute(stmt)
    existing_user = result.fetchone()

    if existing_user:
        if existing_user.login.lower() == user.login.lower():
            raise HTTPException(status_code=400, detail="User with this login already exists")
        elif existing_user.email.lower() == user.email.lower():
            raise HTTPException(status_code=400, detail="User with this email already exists")
    my_code = await generate_unique_code(db)
    stmt = insert(users).values(
        login=user.login,
        email=user.email,
        password=user.password,
        referral_code=user.referral_code,
        my_code=my_code
    ).returning(users)

    result = await db.execute(stmt)
    created_user = result.fetchone()

    if not created_user:
        raise HTTPException(status_code=500, detail="Error occurred while creating user")
    await db.commit()
    session = await create_user_session(db=db, user_id=created_user.id)
    return {"session": session}


@router.post("/login", response_model=dict)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # Проверяем, есть ли пользователь с указанным логином или электронной почтой и паролем
    result = await db.execute(
        select(users).where(
            or_(
                users.c.login == user.login_or_email,
                users.c.email == user.login_or_email
            ),
            users.c.password == user.password
        )
    )

    user_in_db = result.fetchone()

    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    session = await create_user_session(db=db, user_id=user_in_db.id)
    return {"session": session}


@router.post("/reset/{email}", response_model=dict)
async def reset_passwordd(email: str, db: AsyncSession = Depends(get_db)):
    email = email.lower()
    result = await db.execute(
        select(users).where(
            or_(users.c.login == email,
                users.c.email == email)
        )
    )
    user_in_db = result.fetchone()

    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    pin = str(random.randint(10 ** 5, 10 ** 6 - 1))
    await db.execute(reset_password.delete().where(reset_password.c.user_id == user_in_db.id))
    await db.execute(reset_password.insert().values(user_id=user_in_db.id, pin=pin))
    await db.commit()
    from send_email import send_message
    await send_message(recipient=user_in_db.email, pin=pin)
    return {'pin': pin}


@router.post("/reset_check", response_model=dict)
async def reset(user: UserReset, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(reset_password).where(reset_password.c.pin == user.pin))
    pin_in_bd = result.fetchone()
    if not pin_in_bd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pin not found")
    result = await db.execute(select(users).where(
        or_(users.c.email == user.login_or_email,
            users.c.login == user.login_or_email)
    ))
    user_in_db = result.fetchone()
    if not user_in_db or user_in_db.id != pin_in_bd.user_id:
        await db.execute(reset_password.delete().where(reset_password.c.pin == user.pin))
        await db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Обновляем пароль пользователя
    query = update(users).where(users.c.id == user_in_db.id).values(password=user.new_password)
    await db.execute(query)
    await db.execute(reset_password.delete().where(reset_password.c.user_id == user_in_db.id))
    await db.commit()
    session = await create_user_session(db=db, user_id=user_in_db.id)
    return {"info": "Password updated successfully",
            "user_session": session}


@router.post("/change_login", response_model=dict)
async def change_login(user: UserChangeLogin, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=user.user_session)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await db.execute(
        update(users).where(users.c.id == session_in_db.user_id).values(login=user.new_login))
    await db.commit()
    return {"message": "login changed"}


@router.post("/change_photo/{ses}", response_model=dict)
async def change_photo(ses: str, image: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    try:
        file_location = f"images/{session_in_db.user_id}.{image.filename.split('.')[-1]}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(image.file, file_object)
        await db.execute(update(users).where(users.c.id == session_in_db.user_id).values(photo=file_location))
        await db.commit()
        return {"info": f"File '{image.filename}' uploaded successfully"}

    except Exception as e:
        return {"error": str(e)}


@router.post("/change_mailing/{ses}", response_model=dict)
async def change_mailing(ses: str, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=ses)
    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    result = await db.execute(select(users).where(users.c.id == session_in_db.user_id))
    user_in_db = result.fetchone()
    value = False
    if user_in_db.mailing == value:
        value = True
    await db.execute(update(users).where(users.c.id == session_in_db.user_id).values(mailing=value))
    await db.commit()
    return {"message": 'updated'}


async def start_of_day_timestamp():
    now = datetime.now().date()
    start_of_day = datetime.combine(now, dt_time())
    return int(mktime(start_of_day.timetuple()))


@router.post("/add_plan", response_model=dict)
async def add_plan(plan: UserAddPlan, db: AsyncSession = Depends(get_db)):
    session_in_db = await check_session(db=db, session=plan.session)

    if not session_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    places = {1: 13,
              2: 10,
              3: 7}
    for group in range(1, 99):
        result = await db.execute(
            select(plans).where(and_(plans.c.plan_id == plan.plan_id,
                                     plans.c.end_time >= time.time()
                                     )))
        if len(result.fetchall()) < places.get(plan.plan_id):
            start = await start_of_day_timestamp()
            await db.execute(
                plans.insert().values(plan_id=plan.plan_id, group=group, user_id=session_in_db.user_id,
                                      buy_time=start,
                                      end_time=start + 30 * 24 * 60 * 60))
            await db.commit()
            return {"message": "success"}
    return {"message": "go to support"}
