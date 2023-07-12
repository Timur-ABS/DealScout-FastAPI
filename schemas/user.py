from pydantic import BaseModel, validator, Field

import re


class User(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    login: str
    email: str
    password: str
    referral_code: str

    @validator('login', 'email')
    def lower_case(cls, v):
        return v.lower()

    @validator('email')
    def check(cls, v):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if re.match(pattern, v):
            return v
        raise ValueError("Wrong email format")

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    login_or_email: str
    password: str

    @validator('login_or_email')
    def lower_case(cls, v):
        return v.lower()


class UserReset(BaseModel):
    login_or_email: str
    new_password: str
    pin: str

    @validator('login_or_email')
    def lower_case(cls, v):
        return v.lower()


class UserChangeLogin(BaseModel):
    user_session: str
    new_login: str

    @validator('new_login')
    def check(cls, v):
        if 1 <= len(v) <= 35:
            return v
        raise ValueError("Wrong new_login format, too long")


class UserChangePhoto(BaseModel):
    user_session: str


class UserAddPlan(BaseModel):
    session: str
    plan_id: int

    @validator('plan_id')
    def check(cls, v):
        if 1 <= v <= 3:
            return v
        raise ValueError("Wrong new_login format, too long")
