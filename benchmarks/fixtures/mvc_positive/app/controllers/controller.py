from app.models.user import load_user
from app.views.user import render_user
def get_user():
    return render_user(load_user())
