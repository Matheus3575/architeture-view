import os

DATABASE_URL = os.getenv("DATABASE_URL")

def load():
    return DATABASE_URL