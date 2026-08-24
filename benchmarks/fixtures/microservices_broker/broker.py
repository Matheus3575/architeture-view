from fastapi import FastAPI
app = FastAPI()
def publish_order():
    return {"published": True}
