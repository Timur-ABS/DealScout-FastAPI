from sqlalchemy import Table, Column, Integer, String
from db.base import metadata

favorite_deals = Table(
    "favorite_deals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer),
    Column("deal_id", Integer),
)
