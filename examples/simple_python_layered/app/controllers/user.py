from app.services.user import get_user


def user_endpoint(user_id: int):
    return get_user(user_id)
