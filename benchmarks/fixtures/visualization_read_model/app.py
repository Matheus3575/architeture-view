from fastapi import APIRouter, FastAPI

app = FastAPI()
router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}

app.include_router(router)
