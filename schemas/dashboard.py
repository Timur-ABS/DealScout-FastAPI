from pydantic import BaseModel, validator, Field


class DownloadDeal(BaseModel):
    session: str


class SeaMyPLan(BaseModel):
    session: str


class ProfitDay(BaseModel):
    session: str
