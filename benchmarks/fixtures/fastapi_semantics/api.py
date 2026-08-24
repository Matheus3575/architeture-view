from fastapi import APIRouter, Depends as Inject

from .logic import get_service
from .schemas import UserResponse


users_router = APIRouter()


@users_router.get("/users", response_model=UserResponse)
def list_users(service=Inject(get_service)):
    return service


@users_router.post("/users", response_model=UserResponse)
def create_user(service=Inject(get_service)):
    return service


class FakeRouter:
    def get(self, path):
        return path


fake = FakeRouter()


@fake.get("/not-fastapi")
def not_an_endpoint():
    return None


class SomeOtherFrameworkRouter:
    def get(self, path):
        return path


other_router = SomeOtherFrameworkRouter()


@other_router.get("/other")
def other_framework_route():
    return None


registry = {"service": get_service}


@users_router.get("/ambiguous")
def ambiguous_dependency(service=Inject(registry["service"])):
    return service
