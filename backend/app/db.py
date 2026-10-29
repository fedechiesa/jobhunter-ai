from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        str(get_settings().database_url),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
