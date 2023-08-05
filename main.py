from fastapi import FastAPI
from api.v1.endpoints import user
from db.base import create_tables
from api.v1.endpoints import deals
from api.v1.endpoints import dashboard
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить любые источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await create_tables()


# @app.on_event("shutdown")
# async def shutdown():
#     await base.database.disconnect()


app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(deals.router, prefix="/deal", tags=["deal"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
