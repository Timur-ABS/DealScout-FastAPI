from pydantic import BaseModel, validator, Field
from fastapi import FastAPI, File

import re


class DealLook(BaseModel):
    session: str
    time: str
    plan_id: int

    @validator('time')
    def check(cls, v):
        ls = ["today", "week", "month", "all"]
        if v not in ls:
            raise ValueError("Wrong time")
        return v

    @validator('plan_id')
    def check_plan(cls, v):
        ls = [0, 1, 2, 3]
        if v not in ls:
            raise ValueError("Wrong pland_id")
        return v

    class Config:
        orm_mode = True
