from sqlalchemy import Table, Column, Integer, String, BOOLEAN
from db.base import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("login", String(50)),
    Column("mailing", BOOLEAN, default=False),
    Column("photo", String(50)),
    Column("email", String(50)),
    Column("password", String(50)),
    Column("referral_code", String(50)),
    Column("my_code", String(50))
)
