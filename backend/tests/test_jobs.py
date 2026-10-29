import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import JobPosting, MatchScore

pytestmark = pytest.mark.integration


def test_database_health(db_client):
    assert db_client.get("/health/db").json() == {"status": "ok", "database": "ok"}


def test_create_list_get_and_persist(db_client, db_session, job_payload):
    assert db_client.get("/jobs").json() == []
    response = db_client.post("/jobs", json=job_payload)
    assert response.status_code == 201
    job = response.json()
    assert job["required_skills"] == ["python", "sql"]
    assert job["match_score"] is None
    assert db_client.get(f"/jobs/{job['id']}").json() == job
    assert db_client.get("/jobs").json() == [job]
    # A second ORM session reads the committed savepoint in the isolated outer transaction.
    with Session(db_session.connection()) as reader:
        persisted = reader.get(JobPosting, job["id"])
        assert persisted.company == "Example Labs"
        assert persisted.created_at.tzinfo is not None


def test_missing_jobs(db_client):
    assert db_client.get("/jobs/999999").status_code == 404
    assert db_client.post("/jobs/999999/match").status_code == 404


def test_invalid_job_and_unknown_source(db_client, job_payload):
    assert db_client.post("/jobs", json=job_payload | {"title": " "}).status_code == 422
    assert db_client.post("/jobs", json=job_payload | {"source_id": 99999}).status_code == 422


def test_pagination_and_validation(db_client, job_payload):
    first = db_client.post("/jobs", json=job_payload).json()
    second = db_client.post("/jobs", json=job_payload | {"title": "Second"}).json()
    assert db_client.get("/jobs?limit=1").json() == [second]
    assert db_client.get("/jobs?limit=1&offset=1").json() == [first]
    assert db_client.get("/jobs?limit=101").status_code == 422
    assert db_client.get("/jobs?offset=-1").status_code == 422


def test_profile_match_persistence_and_invalidation(db_client, db_session, job_payload):
    assert db_client.get("/profile").status_code == 404
    job = db_client.post("/jobs", json=job_payload).json()
    assert db_client.post(f"/jobs/{job['id']}/match").status_code == 409
    profile = {"skills": ["python"], "experience_years": 2}
    assert db_client.put("/profile", json=profile).status_code == 200
    assert db_client.get("/profile").json()["skills"] == ["python"]
    first = db_client.post(f"/jobs/{job['id']}/match").json()
    second = db_client.post(f"/jobs/{job['id']}/match").json()
    assert first == second
    assert first["score"] == 55
    assert db_client.get(f"/jobs/{job['id']}").json()["match_score"]["score"] == 55
    assert db_session.scalar(select(func.count()).select_from(MatchScore)) == 1
    db_client.put("/profile", json={"skills": ["sql", "python"], "experience_years": 4})
    assert db_client.get("/jobs").json()[0]["match_score"] is None
    assert db_session.scalar(select(func.count()).select_from(MatchScore)) == 0
    assert db_client.post(f"/jobs/{job['id']}/match").json()["score"] == 100


def test_migration_revision(db_session):
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from app.core.config import ROOT

    head = ScriptDirectory.from_config(Config(str(ROOT / "backend/alembic.ini"))).get_current_head()
    assert db_session.scalar(text("SELECT version_num FROM alembic_version")) == head


def test_committed_data_survives_new_connection(migrated_engine, job_payload):
    job_id = None
    try:
        with Session(migrated_engine) as writer:
            job = JobPosting(**job_payload, source_id=1)
            writer.add(job)
            writer.commit()
            job_id = job.id
        with Session(migrated_engine) as reader:
            assert reader.get(JobPosting, job_id).title == "Backend Engineer"
    finally:
        if job_id is not None:
            with migrated_engine.begin() as connection:
                connection.execute(text("DELETE FROM job_postings WHERE id = :id"), {"id": job_id})
