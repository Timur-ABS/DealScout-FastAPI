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
            raise ValueError("Wrong time format")
        return v

    class Config:
        orm_mode = True
