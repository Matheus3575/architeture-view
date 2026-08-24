from app.infrastructure.database import Database

def handle():
    return Database().load()
