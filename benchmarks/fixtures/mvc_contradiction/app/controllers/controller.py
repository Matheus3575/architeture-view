from app.models.user import load_user
from app.repositories.store import fetch_user
def get_user():
    return load_user()
