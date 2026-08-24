from storage import X


class Y:
    def __init__(self, dependency):
        self.dependency = dependency

    def execute(self):
        return self.dependency.find()
