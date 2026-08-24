import os

class App:
    def __init__(self):
        # 1. Clear database env var access
        self.db_url = os.getenv("DATABASE_URL")
        # 2. Redis env var access via os.environ.get
        self.redis_url = os.environ.get("REDIS_URL")
        # 3. Dynamic or unknown env var target
        self.unknown_url = os.getenv("UNKNOWN_URL")
        # 4. Fake postgres / database var
        self.fake_db = os.getenv("FAKE_DB")

    def run(self):
        print(f"Connecting to database at {self.db_url}")
        print(f"Connecting to cache at {self.redis_url}")
