from .repository import UserRepository


class UserLogic:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def load(self):
        return self.repository.find()
