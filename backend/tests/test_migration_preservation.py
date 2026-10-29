from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.core.config import ROOT

pytestmark = pytest.mark.integration


def test_upgrade_preserves_foundation_data(migrated_engine):
    schema = f"jh_migration_{uuid4().hex}"
    config = Config(str(ROOT / "backend/alembic.ini"))
    with migrated_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        config.attributes["connection"] = connection
        command.upgrade(config, "0001_foundation")
        connection.execute(
            text(
                "INSERT INTO candidate_profiles "
                "(id, skills, experience_years, preferred_location, prefer_remote) "
                "VALUES (1, '[\"python\"]', 0, '', true)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO job_postings (title, company, description, location, remote, "
                "required_skills, experience_years, source_id) "
                "VALUES ('Example opening', 'Example Labs', 'Fictional migration fixture', "
                "'Example City', true, '[\"python\"]', 0, 1)"
            )
        )
        created = connection.scalar(text("SELECT created_at FROM job_postings"))
        command.upgrade(config, "head")
        row = connection.execute(
            text("SELECT title, first_discovered_at, workplace_type FROM job_postings")
        ).one()
        assert (
            row.title == "Example opening"
            and row.first_discovered_at == created
            and row.workplace_type == "remote"
        )
        assert (
            connection.scalar(text("SELECT experience_years FROM candidate_profiles WHERE id = 1"))
            == 0
        )
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
