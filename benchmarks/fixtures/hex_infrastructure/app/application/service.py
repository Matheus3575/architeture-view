from app.domain.ports import UserPort

def handle(port: UserPort | None = None):
    return port.load() if port else None
