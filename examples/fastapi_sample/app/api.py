import os

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.services import get_user


class User(BaseModel):
    name: str


application = FastAPI()


@application.get("/users")
def user_endpoint(user=Depends(get_user)) -> User:
    return User(name=str(user))
