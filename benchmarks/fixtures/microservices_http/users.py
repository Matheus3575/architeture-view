from fastapi import FastAPI
from orders import get_order
app = FastAPI()
@app.get("/users")
def get_user():
    return get_order()
