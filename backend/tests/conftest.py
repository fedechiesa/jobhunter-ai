import os
from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import ROOT, Settings
from app.db import get_session


@pytest.fixture
def application():
    from app.factory import create_app

    return create_app(
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://unused@127.0.0.1/unused",
        )
    )


@pytest.fixture
def client(application) -> Generator[TestClient, None, None]:
    with TestClient(application) as test_client:
        yield test_client


def isolated_test_url(raw_url: str | None, development_url: str | None) -> str:
    if not raw_url:
        raise ValueError("Set TEST_DATABASE_URL; start docker compose --profile test up -d --wait")
    url = make_url(raw_url)
    if url.drivername != "postgresql+psycopg" or not (url.database or "").endswith("_test"):
        raise ValueError(
            "TEST_DATABASE_URL must use postgresql+psycopg and a database ending in _test"
        )
    if development_url:
        dev = make_url(development_url)
        if (url.host, url.port or 5432, url.database) == (dev.host, dev.port or 5432, dev.database):
            raise ValueError("Test and development databases must be different")
    return raw_url


@pytest.fixture(scope="session")
def migrated_engine():
    local = dotenv_values(ROOT / ".env")
    try:
        url = isolated_test_url(
            os.getenv("TEST_DATABASE_URL", local.get("TEST_DATABASE_URL")),
            os.getenv("DATABASE_URL", local.get("DATABASE_URL")),
        )
    except ValueError as exc:
        pytest.fail(str(exc))
    schema = f"jh_test_{uuid4().hex}"
    admin_engine = create_engine(url, connect_args={"connect_timeout": 3})
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url, connect_args={"options": f"-csearch_path={schema}", "connect_timeout": 3}
    )
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    try:
        # Check migration reversibility on an empty, disposable schema.
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            command.downgrade(config, "base")
            command.upgrade(config, "head")
            command.check(config)
        yield engine
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


@pytest.fixture
def db_session(migrated_engine):
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()


@pytest.fixture
def db_client(application, db_session):
    application.dependency_overrides[get_session] = lambda: db_session
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()


@pytest.fixture
def job_payload():
    return {
        "title": "Backend Engineer",
        "company": "Example Labs",
        "description": "Fictional test opening for a Python service.",
        "location": "Example City",
        "remote": True,
        "required_skills": ["Python", "SQL"],
        "experience_years": 4,
        "url": "https://example.com/jobs/1",
    }
