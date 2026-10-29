import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_engine, get_session
from app.discovery.providers import ProviderError
from app.discovery.schemas import NormalizedJob
from app.discovery.sync import LOCK_KEY, SyncBusy, is_running, synchronize
from app.models import CandidateProfile, JobPosting, MatchScore

pytestmark = pytest.mark.integration


@pytest.fixture
def discovery_env(migrated_engine, tmp_path, application, monkeypatch):
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps(
            [
                {"provider": "greenhouse", "board_token": "example", "company": "Example Labs"},
                {"provider": "lever", "board_token": "example", "company": "Example Labs"},
            ]
        ),
        encoding="utf-8",
    )
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://unused@localhost/unused",
        sources_file=path,
    )
    records = {"greenhouse": [], "lever": []}

    def factory(provider, _settings):
        class Fake:
            def fetch(self, _board):
                result = records[provider]
                if isinstance(result, Exception):
                    raise result
                return result

        return Fake()

    def sessions():
        with Session(migrated_engine) as session:
            yield session

    application.dependency_overrides[get_session] = sessions
    application.dependency_overrides[get_engine] = lambda: migrated_engine
    application.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr(
        "app.api.discovery.synchronize", lambda engine, config: synchronize(engine, config, factory)
    )
    with TestClient(application) as client:
        yield migrated_engine, settings, records, factory, client
    with migrated_engine.begin() as connection:
        for table in (
            "match_scores",
            "job_postings",
            "sync_runs",
            "search_preferences",
            "candidate_profiles",
        ):
            connection.execute(text(f"DELETE FROM {table}"))
        connection.execute(text("DELETE FROM job_sources WHERE kind <> 'manual'"))


@pytest.fixture
def normalized_job():
    return NormalizedJob(
        external_id="external-1",
        title="Junior Python Developer",
        description="Python and SQL; 1 year of experience",
        location="Buenos Aires, Argentina",
        workplace_type="hybrid",
        url="https://example.com/jobs/1",
        apply_url="https://example.com/jobs/1/apply",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_repeated_sync_is_idempotent_and_persisted(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = [normalized_job]
    client.put("/profile", json={"skills": ["python", "sql"], "experience_years": 1})
    first = synchronize(engine, settings, factory)
    second = synchronize(engine, settings, factory)
    assert first.source_results[0]["new"] == 1
    assert second.source_results[0]["new"] == 0 and second.source_results[0]["unchanged"] == 1
    with Session(engine) as reader:
        assert reader.scalar(select(func.count()).select_from(JobPosting)) == 1
        assert reader.scalar(select(func.count()).select_from(MatchScore)) == 1
    job = client.get("/jobs").json()[0]
    assert job["match_score"]["score"] == 100
    assert job["provider"] == "greenhouse" and job["requirements_inferred"] is True
    assert job["experience_years_known"] is True
    assert job["first_discovered_at"] <= job["last_seen_at"]


def test_update_absence_reappearance_and_failure(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = [normalized_job]
    synchronize(engine, settings, factory)
    discovered = client.get("/jobs").json()[0]["first_discovered_at"]
    records["greenhouse"] = [
        normalized_job.model_copy(update={"title": "Updated Python Developer"})
    ]
    assert synchronize(engine, settings, factory).source_results[0]["updated"] == 1
    records["greenhouse"] = ProviderError("network_or_timeout")
    assert synchronize(engine, settings, factory).status == "partial"
    job = client.get("/jobs").json()[0]
    assert job["availability"] == "active" and job["title"] == "Updated Python Developer"
    records["greenhouse"] = []
    assert synchronize(engine, settings, factory).source_results[0]["potentially_inactive"] == 1
    assert client.get("/jobs").json()[0]["availability"] == "potentially_inactive"
    records["greenhouse"] = [normalized_job]
    synchronize(engine, settings, factory)
    job = client.get("/jobs").json()[0]
    assert job["availability"] == "active" and job["first_discovered_at"] == discovered


def test_exact_url_duplicate_detection_without_deleting_history(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = [normalized_job]
    records["lever"] = [normalized_job.model_copy(update={"external_id": "other-id"})]
    result = synchronize(engine, settings, factory)
    assert result.source_results[1]["duplicates"] == 1
    assert len(client.get("/jobs").json()) == 1
    assert len(client.get("/jobs?include_duplicates=true").json()) == 2
    # If the primary disappears the still-observed alias is promoted.
    records["greenhouse"] = []
    synchronize(engine, settings, factory)
    assert len(client.get("/jobs?availability=active").json()) == 1


def test_provider_error_does_not_block_others_and_restrictions_disable(
    discovery_env, normalized_job
):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = ProviderError("http_403")
    records["lever"] = [normalized_job]
    result = synchronize(engine, settings, factory)
    assert result.status == "partial"
    sources = client.get("/sources").json()
    greenhouse = next(source for source in sources if source["kind"] == "greenhouse")
    assert greenhouse["enabled"] is False and greenhouse["last_error"] == "http_403"
    assert len(client.get("/jobs").json()) == 1
    assert (
        client.patch(f"/sources/{greenhouse['id']}", json={"enabled": True}).json()["enabled"]
        is True
    )


def test_api_sync_status_preferences_and_filters(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    assert client.get("/sync/status").json() == {"running": False, "latest": None}
    sources = client.get("/sources").json()
    assert len(sources) == 2
    preferences = client.get("/search-preferences").json()
    assert preferences["max_experience_years"] == 2 and "Python" in preferences["technologies"]
    records["greenhouse"] = [normalized_job]
    records["lever"] = [
        normalized_job.model_copy(
            update={
                "external_id": "lever-2",
                "title": "Senior Data Engineer",
                "url": HttpUrl("https://example.com/jobs/2"),
                "apply_url": HttpUrl("https://example.com/jobs/2/apply"),
                "location": "Other City",
                "workplace_type": "remote",
            }
        )
    ]
    response = client.post("/sync")
    assert response.status_code == 200 and response.json()["status"] == "success"
    assert client.get("/sync/status").json()["latest"]["id"] == response.json()["id"]
    assert (
        len(
            client.get(
                "/jobs?q=python&location=Buenos&provider=greenhouse&workplace_type=hybrid"
            ).json()
        )
        == 1
    )
    assert client.get("/jobs?q=nonexistent").json() == []
    assert client.get("/jobs?q=%25").json() == []
    assert len(client.get("/jobs?published_after=2025-12-31T00:00:00Z").json()) == 2
    assert client.get("/jobs?discovered_after=2100-01-01T00:00:00Z").json() == []
    assert client.get("/jobs?min_score=1").json() == []  # no invented candidate profile
    assert client.get("/jobs?sort=priority").json()[0]["provider"] == "greenhouse"
    client.put("/profile", json={"skills": ["python", "sql"], "experience_years": 1})
    synchronize(engine, settings, factory)
    assert len(client.get("/jobs?min_score=90&sort=score").json()) == 2
    updated = preferences | {
        "roles": ["Data Engineer"],
        "locations": ["Other City"],
        "technologies": [],
        "deprioritize_senior": False,
    }
    assert client.put("/search-preferences", json=updated).json() == updated
    assert client.get("/jobs?sort=priority").json()[0]["provider"] == "lever"
    assert client.get("/jobs?min_score=101").status_code == 422
    assert client.get("/jobs?provider=unknown").status_code == 422
    assert client.patch("/sources/999999", json={"enabled": False}).status_code == 404
    assert client.put("/search-preferences", json={"roles": [""]}).status_code == 422
    with Session(engine) as reader:
        assert reader.get(CandidateProfile, 1).experience_years == 1


def test_concurrent_sync_returns_conflict_and_unlocks(discovery_env):
    engine, settings, records, factory, client = discovery_env
    with engine.connect() as lock:
        lock.execute(text(f"SELECT pg_advisory_lock({LOCK_KEY})"))
        lock.commit()
        try:
            assert is_running(engine)
            assert client.get("/sync/status").json()["running"] is True
            assert client.post("/sync").status_code == 409
            with pytest.raises(SyncBusy):
                synchronize(engine, settings, factory)
        finally:
            lock.execute(text(f"SELECT pg_advisory_unlock({LOCK_KEY})"))
            lock.commit()
    assert not is_running(engine)
    assert client.post("/sync").status_code == 200


def test_disabled_sources_and_missing_config(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    source = client.get("/sources").json()[0]
    client.patch(f"/sources/{source['id']}", json={"enabled": False})
    records["greenhouse"] = [normalized_job]
    assert client.post("/sync").json()["source_results"][0]["provider"] == "lever"
    assert client.get("/jobs").json() == []
    settings.sources_file.write_text('{"bad": "config"}', encoding="utf-8")
    assert client.post("/sync").status_code == 503
    assert not is_running(engine)


def test_profile_updates_do_not_fabricate_experience(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = [
        normalized_job.model_copy(
            update={"description": "Some Python knowledge; experience preferred"}
        )
    ]
    synchronize(engine, settings, factory)
    job = client.get("/jobs").json()[0]
    assert job["experience_years"] == 0 and job["experience_years_known"] is False
    assert client.get("/profile").status_code == 404
