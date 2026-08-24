from app.domain.ports import UserPort

class SqlAdapter(UserPort):
    def load(self):
        return {"id": 1}
