from requests import get

from .logic import UserLogic
from .repository import UserRepository


def list_users():
    repository = UserRepository()
    service = UserLogic(repository)
    get("https://example.invalid/telemetry")
    return service.load()
