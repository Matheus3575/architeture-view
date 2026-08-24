from app.domain.ports import UserPort
from app.infrastructure.database import Database

def handle(port: UserPort | None = None):
    Database().load()
    return port.load() if port else None
