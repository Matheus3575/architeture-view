from fastapi import FastAPI as Api

from .api import users_router


application = Api()
application.include_router(users_router, prefix="/v1", tags=["users"])
