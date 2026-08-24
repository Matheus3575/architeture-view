from fastapi import FastAPI
from broker import publish_order
app = FastAPI()
@app.get("/users")
def get_user():
    return publish_order()
