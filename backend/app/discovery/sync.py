import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.discovery.configuration import ensure_sources, search_preferences
from app.discovery.normalization import canonical_url, detected_requirements, priority
from app.discovery.providers import JobProvider, ProviderError, provider_for
from app.discovery.schemas import BoardConfig, NormalizedJob, SearchInput, SyncRead
from app.models import CandidateProfile, JobPosting, JobSource, SyncRun
from app.services.scores import persist_match

LOCK_KEY = 73420261
logger = logging.getLogger("jobhunter.discovery")


class SyncBusy(Exception):
    pass


def log_event(event: str, **fields) -> None:
    logger.info(json.dumps({"event": event, "timestamp": datetime.now(UTC).isoformat(), **fields}))


def is_running(engine: Engine) -> bool:
    with engine.connect() as connection:
        acquired = connection.scalar(text(f"SELECT pg_try_advisory_lock({LOCK_KEY})"))
        if acquired:
            connection.execute(text(f"SELECT pg_advisory_unlock({LOCK_KEY})"))
        connection.commit()
        return not acquired


def save_snapshot(
    session: Session, source: JobSource, jobs: list[NormalizedJob], preferences: SearchInput
) -> dict:
    now = datetime.now(UTC)
    counts = {
        "fetched": len(jobs),
        "new": 0,
        "updated": 0,
        "unchanged": 0,
        "potentially_inactive": 0,
        "duplicates": 0,
        "matched": 0,
    }
    existing = {
        job.external_id: job
        for job in session.scalars(
            select(JobPosting).where(
                JobPosting.source_id == source.id, JobPosting.external_id.is_not(None)
            )
        )
    }
    seen = set()
    # Same lock order as PUT /profile and manual matching.
    profile = session.scalar(
        select(CandidateProfile).where(CandidateProfile.id == 1).with_for_update()
    )
    for incoming in jobs:
        seen.add(incoming.external_id)
        fingerprint = hashlib.sha256(
            json.dumps(incoming.model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest()
        job = existing.get(incoming.external_id)
        if job is None:
            job = JobPosting(source_id=source.id, external_id=incoming.external_id)
            session.add(job)
            change = "new"
        else:
            change = (
                "updated"
                if job.content_hash != fingerprint
                or job.availability != "active"
                or job.company != (source.company_name or source.name)
                else "unchanged"
            )
        counts[change] += 1
        skills, years, known = detected_requirements(incoming.description)
        job.title, job.description, job.location = (
            incoming.title,
            incoming.description,
            incoming.location,
        )
        job.company = source.company_name or source.name
        job.remote = incoming.workplace_type == "remote"
        job.workplace_type = incoming.workplace_type
        job.url, job.apply_url = str(incoming.url), str(incoming.apply_url)
        job.published_at = incoming.published_at
        job.content_hash = fingerprint
        job.required_skills, job.experience_years = skills, years
        job.requirements_inferred, job.experience_years_known = True, known
        job.last_seen_at, job.availability, job.discovery_status = now, "active", change
        job.canonical_url = canonical_url(str(incoming.apply_url))
        job.search_priority, job.seniority = priority(
            job.title, job.description, job.location, years, known, preferences
        )
        session.flush()
        # Exact canonical application URL + company + title only; never fuzzy merge.
        duplicate = session.scalar(
            select(JobPosting)
            .where(
                JobPosting.id != job.id,
                JobPosting.source_id != source.id,
                JobPosting.canonical_url == job.canonical_url,
                JobPosting.company == job.company,
                JobPosting.title == job.title,
                JobPosting.duplicate_of_id.is_(None),
                JobPosting.availability == "active",
            )
            .order_by(JobPosting.id)
            .limit(1)
        )
        job.duplicate_of_id = duplicate.id if duplicate else None
        counts["duplicates"] += duplicate is not None
        if profile is not None:
            persist_match(session, profile, job)
            counts["matched"] += 1
    for external_id, job in existing.items():
        if external_id not in seen:
            if job.availability != "potentially_inactive":
                counts["potentially_inactive"] += 1
            job.availability = "potentially_inactive"
            job.discovery_status = "potentially_inactive"
    return counts


def synchronize(
    engine: Engine,
    settings: Settings,
    factory: Callable[[str, Settings], JobProvider] = provider_for,
) -> SyncRead:
    # Dedicated connection retains the session lock across per-source commits and network IO.
    with engine.connect() as lock_connection:
        acquired = lock_connection.scalar(text(f"SELECT pg_try_advisory_lock({LOCK_KEY})"))
        lock_connection.commit()
        if not acquired:
            raise SyncBusy("Synchronization already running")
        try:
            with Session(engine) as session:
                sources = ensure_sources(session, settings)
                session.execute(
                    update(SyncRun)
                    .where(SyncRun.status == "running")
                    .values(status="interrupted", finished_at=datetime.now(UTC))
                )
                run = SyncRun(status="running", source_results=[])
                session.add(run)
                session.commit()
                run_id = run.id
                source_ids = [source.id for source in sources if source.enabled]
            results = []
            log_event("sync_started", run_id=run_id, sources=len(source_ids))
            for source_id in source_ids:
                with Session(engine) as session:
                    source = session.get(JobSource, source_id)
                    if not source.enabled:
                        continue
                    source.last_attempt_at = datetime.now(UTC)
                    board = BoardConfig(
                        provider=source.kind,
                        company=source.company_name or source.name,
                        board_token=source.board_token,
                        region=source.region,
                    )
                    session.commit()
                    try:
                        jobs = factory(source.kind, settings).fetch(board)
                        session.refresh(source)
                        if not source.enabled:
                            continue
                        result = save_snapshot(session, source, jobs, search_preferences(session))
                        result.update(
                            {
                                "source_id": source.id,
                                "provider": source.kind,
                                "board": source.board_token,
                                "status": "success",
                            }
                        )
                        source.last_success_at, source.last_error, source.last_result = (
                            datetime.now(UTC),
                            None,
                            result,
                        )
                        session.commit()
                    except (ProviderError, SQLAlchemyError) as error:
                        session.rollback()
                        source = session.get(JobSource, source_id)
                        code = str(error) if isinstance(error, ProviderError) else "database_error"
                        result = {
                            "source_id": source.id,
                            "provider": source.kind,
                            "board": source.board_token,
                            "status": "error",
                            "error": code,
                        }
                        source.last_error, source.last_result = code, result
                        if code in {
                            "http_401",
                            "http_403",
                            "unsupported_region",
                            "unsupported_provider",
                        }:
                            source.enabled = False
                        session.commit()
                    results.append(result)
                    log_event("source_finished", run_id=run_id, **result)
            with Session(engine) as session:
                run = session.get(SyncRun, run_id)
                failures = sum(result["status"] == "error" for result in results)
                run.status = (
                    "success"
                    if failures == 0
                    else "failed"
                    if failures == len(results)
                    else "partial"
                )
                run.source_results, run.finished_at = results, datetime.now(UTC)
                session.commit()
                output = SyncRead.model_validate(run)
                log_event("sync_finished", run_id=run_id, status=run.status)
                return output
        finally:
            lock_connection.execute(text(f"SELECT pg_advisory_unlock({LOCK_KEY})"))
            lock_connection.commit()
