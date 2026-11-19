from functools import lru_cache
from os import getenv

from sqlalchemy import Engine, create_engine


@lru_cache
def get_engine() -> Engine:
    url = getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL to a postgresql+psycopg URL.")
    return create_engine(url, pool_pre_ping=True)
