from fastapi import FastAPI
from users import get_user
from orders import get_order
app = FastAPI()
@app.get("/users")
def users():
    return get_user()
@app.get("/orders")
def orders():
    return get_order()
