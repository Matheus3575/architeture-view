from fastapi import FastAPI
app = FastAPI()
def get_order():
    return {"id": 1}
