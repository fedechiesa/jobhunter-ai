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


def test_argentina_upgrade_preserves_sprint2_profile_jobs_and_scores(migrated_engine):
    schema = f"jh_migration_{uuid4().hex}"
    config = Config(str(ROOT / "backend/alembic.ini"))
    with migrated_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        config.attributes["connection"] = connection
        command.upgrade(config, "2e57c63bd9b7")
        connection.execute(
            text(
                "INSERT INTO candidate_profiles "
                "(id, skills, experience_years, preferred_location, prefer_remote) "
                "VALUES (1, '[\"python\"]', 0, 'Example City', true)"
            )
        )
        job_id = connection.scalar(
            text(
                "INSERT INTO job_postings (title, company, description, location, remote, "
                "required_skills, experience_years, source_id) VALUES ('Example job', "
                "'Example Labs', 'Fictional fixture', 'Example City', true, '[]', 0, 1) "
                "RETURNING id"
            )
        )
        connection.execute(
            text(
                "INSERT INTO match_scores (job_id, candidate_id, score, skill_score, "
                "experience_score, location_score, matched_skills, missing_skills, "
                "algorithm_version) VALUES (:id, 1, 80, 100, 0, 100, '[]', '[]', "
                "'deterministic-v1.1')"
            ),
            {"id": job_id},
        )
        command.upgrade(config, "head")
        assert connection.scalar(text("SELECT score FROM match_scores")) == 80
        assert connection.scalar(text("SELECT professional FROM candidate_profiles")) is None
        assert connection.scalar(text("SELECT compatibility FROM job_postings")) == "review_needed"
        assert connection.scalar(text("SELECT count(*) FROM job_postings")) == 1
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
