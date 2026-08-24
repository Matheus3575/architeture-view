from sample_app.services import UserService as US


def load():
    service = US()
    return service.get_user()
