from sqlalchemy import Table, Column, Integer, String
from db.base import metadata

deals = Table(
    "deals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("day", Integer),  # time_stamp начало дня
    Column("shop_price", Integer),  # Умноженное на сто
    Column("amazon_price", Integer),  # Умноженное на сто
    Column("photo", String(1024)),
    Column("shop_name", String(1024)),
    Column("shop_link", String(1024)),
    Column("amazon_link", String(1024)),
    Column("plan_id", Integer),
    Column("group_number", Integer),
    Column("roi", String(128)),
    Column("net_profit", String(128)),
    Column("bsr_percent", String(128)),
    Column("fba_seller", String(128)),
    Column("fbm_seller", String(128)),
    Column("est_monthly_sale", String(128)),
    Column("asin", String(128)),
    Column("brs_rank", String(128)),
    Column("upc_ean", String(128)),
    Column("restriction_check", String(128))
)
