from sqlalchemy import Table, Column, Integer, String
from db.base import metadata

reset_password = Table(
    "reset_password",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer),
    Column("pin", String(8))
)
