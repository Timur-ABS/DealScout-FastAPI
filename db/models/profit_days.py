from sqlalchemy import Table, Column, Integer, String, BOOLEAN
from db.base import metadata

profit_days = Table(
    "profit_days",
    metadata,
    Column("time_stamp_day", Integer, primary_key=True, autoincrement=True),
    Column("profit", Integer)  # умноженный на сто
)
