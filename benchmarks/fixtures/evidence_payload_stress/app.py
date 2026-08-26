from fastapi import FastAPI
from helper import status

app = FastAPI()


@app.get("/health")
def health():
    return status()