import anyio
import redis
from psycopg import connect


def load_items():
    # The imports are observations; the compose resources provide the
    # architectural persistence evidence.
    return {"redis": redis.Redis, "database": connect, "runtime": anyio}
