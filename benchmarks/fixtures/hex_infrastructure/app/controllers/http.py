from app.application.service import handle
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_user():
    return handle()
