from sqlalchemy import Table, Column, Integer, String
from db.base import metadata

plans = Table(
    "plans",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("plan_id", Integer),  # 1,2,3,...
    Column("group", Integer),
    Column("user_id", Integer),
    Column("buy_time", Integer),  # time_stamp
    Column("end_time", Integer)  # time_stamp
)
