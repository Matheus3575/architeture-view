from fastapi import FastAPI

from .api import users_router


application = FastAPI()
application.include_router(users_router, prefix="/v1", tags=["users"])
