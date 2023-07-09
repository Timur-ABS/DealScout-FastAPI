from sqlalchemy import Table, Column, Integer, String
from db.base import metadata

sessions = Table(
    "sessions",
    metadata,
    Column("session", String(64), primary_key=True),
    Column("user_id", Integer),
    Column("time_start", Integer) #time_stamp
)
