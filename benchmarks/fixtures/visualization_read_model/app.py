from fastapi import APIRouter, FastAPI
import os

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")
router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}

app.include_router(router)
