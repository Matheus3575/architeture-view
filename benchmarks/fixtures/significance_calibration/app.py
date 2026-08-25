from fastapi import FastAPI

from domain import list_items

application = FastAPI()


@application.get("/items")
def items():
    return list_items()
