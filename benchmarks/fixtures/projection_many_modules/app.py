from fastapi import FastAPI
from domain import handle
app = FastAPI()
@app.get("/health")
def health():
    return handle()
