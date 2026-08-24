from fastapi import FastAPI
from app.controllers.controller import get_user
app = FastAPI()
app.get("/users/{user_id}")(get_user)
