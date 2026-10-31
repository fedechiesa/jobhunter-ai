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
        source_min_interval_seconds=0,
        source_error_backoff_seconds=0,
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


def test_argentina_classification_filters_and_profile_reassessment(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = [normalized_job]
    records["lever"] = [
        normalized_job.model_copy(
            update={
                "external_id": "other",
                "title": "Senior Python Developer",
                "location": "Worldwide",
                "workplace_type": "remote",
                "apply_url": HttpUrl("https://example.com/other"),
            }
        )
    ]
    synchronize(engine, settings, factory)
    assert (
        len(client.get("/jobs?country=AR&seniority=junior&compatibility=argentina_priority").json())
        == 1
    )
    assert client.get("/jobs?sort=recommended").json()[0]["title"] == normalized_job.title
    assert len(client.get("/jobs?compatibility=deprioritized").json()) == 1
    assert client.get("/jobs?published_after=2100-01-01T00:00:00Z").json() == []
    job = client.get("/jobs?compatibility=argentina_priority").json()[0]
    assert len(client.get(f"/jobs?source_id={job['source_id']}").json()) == 1
    original_id = job["id"]
    profile = {
        "skills": ["python", "sql"],
        "experience_years": 0,
        "preferred_location": "CABA",
        "professional": {
            "education": [{"title": "Fictional program"}],
            "languages": [{"name": "English", "level": "intermediate"}],
            "projects": [{"name": "Fictional project"}],
        },
    }
    assert client.put("/profile", json=profile).status_code == 200
    synchronize(engine, settings, factory)
    job = client.get(f"/jobs/{original_id}").json()
    assert job["match_score"]["algorithm_version"] == "deterministic-v1.2-ar"
    assert job["assessment"]["geography"]["status"] == "confirmed"
    with Session(engine) as reader:
        assert reader.get(JobPosting, original_id).assessment == job["assessment"]
        assert (
            reader.get(CandidateProfile, 1).professional["education"][0]["confirmation"]
            == "pending"
        )
        assert reader.get(CandidateProfile, 1).experience_years == 0
    changed = profile | {
        "professional": profile["professional"] | {"target_roles": ["Unrelated profession"]}
    }
    client.put("/profile", json=changed)
    assert client.get(f"/jobs/{original_id}").json()["compatibility"] == "deprioritized"
    assert client.get(f"/jobs/{original_id}").json()["match_score"] is None
    assert client.get("/jobs?country=invalid").status_code == 422


def test_source_cooldown_survives_sessions_and_repeated_errors(discovery_env, normalized_job):
    from datetime import timedelta

    from app.models import JobSource

    engine, settings, records, factory, client = discovery_env
    settings.source_min_interval_seconds = 60
    settings.source_error_backoff_seconds = 60
    records["greenhouse"] = [normalized_job]
    records["lever"] = ProviderError("network_or_timeout")
    first = synchronize(engine, settings, factory)
    assert first.status == "partial"
    records["greenhouse"] = []
    deferred = synchronize(engine, settings, factory)
    assert all(result["status"] == "deferred" for result in deferred.source_results)
    assert client.get("/jobs").json()[0]["availability"] == "active"
    with Session(engine) as writer:
        source = writer.scalar(select(JobSource).where(JobSource.kind == "lever"))
        source.next_allowed_at = datetime.now(UTC) - timedelta(seconds=1)
        writer.commit()
    synchronize(engine, settings, factory)
    with Session(engine) as reader:
        source = reader.scalar(select(JobSource).where(JobSource.kind == "lever"))
        assert source.consecutive_failures == 2
        assert source.next_allowed_at > datetime.now(UTC) + timedelta(seconds=110)


def test_unknown_publication_and_worldwide_are_never_confirmed(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    records["greenhouse"] = [
        normalized_job.model_copy(
            update={"location": "Worldwide", "published_at": None, "workplace_type": "remote"}
        )
    ]
    synchronize(engine, settings, factory)
    job = client.get("/jobs").json()[0]
    assert job["country"] == "unknown" and job["compatibility"] == "review_needed"
    assert client.get("/jobs?published_after=2020-01-01T00:00:00Z").json() == []
    client.put("/profile", json={"skills": ["python", "sql"], "professional": {}})
    assert client.post(f"/jobs/{job['id']}/match").json()["location_score"] == 0


def test_release_corrections_persist_through_repeated_sync(discovery_env, normalized_job):
    engine, settings, records, factory, client = discovery_env
    client.put("/profile", json={"skills": ["python", "sql"], "professional": {}})
    records["greenhouse"] = [
        normalized_job.model_copy(
            update={
                "title": "Software Engineer",
                "description": (
                    "Required Qualifications\n2-4 years of experience\n"
                    "Strong written and verbal English communication skills."
                ),
            }
        )
    ]
    synchronize(engine, settings, factory)
    job = client.get("/jobs").json()[0]
    assert job["compatibility"] == "review_needed" and job["seniority"] == "unknown"
    original_id = job["id"]
    repeated = synchronize(engine, settings, factory)
    assert repeated.source_results[0]["unchanged"] == 1
    assert client.get("/jobs").json()[0]["id"] == original_id
    records["greenhouse"] = [
        normalized_job.model_copy(
            update={
                "title": "Fraud Data Analyst",
                "description": "Minimum of two (2) years of experience in a fraud detection role.",
            }
        )
    ]
    synchronize(engine, settings, factory)
    job = client.get(f"/jobs/{original_id}").json()
    assert job["experience_years_known"] and job["experience_years"] == 2
    assert job["match_score"]["experience_score"] == 0
    assert job["compatibility"] == "review_needed"
