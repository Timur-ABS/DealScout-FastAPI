from pydantic import BaseModel, validator, Field


class FavoriteDeal(BaseModel):
    session: str
    deal_id: int


class FavoriteDealList(BaseModel):
    session: str
