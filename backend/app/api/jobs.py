from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import CandidateProfile, JobPosting, JobSource, MatchScore
from app.schemas import JobCreate, JobRead, MatchRead
from app.services.scores import persist_match

router = APIRouter(prefix="/jobs", tags=["jobs"])
Database = Annotated[Session, Depends(get_session)]


def find_job(session: Session, job_id: int) -> JobPosting:
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=list[JobRead])
def list_jobs(
    session: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(max_length=200)] = None,
    location: Annotated[str | None, Query(max_length=200)] = None,
    provider: Literal["manual", "greenhouse", "lever", "ashby"] | None = None,
    workplace_type: Literal["remote", "hybrid", "onsite", "unknown"] | None = None,
    availability: Literal["active", "potentially_inactive"] | None = None,
    discovered_after: datetime | None = None,
    published_after: datetime | None = None,
    min_score: Annotated[float | None, Query(ge=0, le=100)] = None,
    min_priority: Annotated[float | None, Query(ge=0, le=100)] = None,
    sort: Literal["newest", "priority", "score"] = "newest",
    include_duplicates: bool = False,
) -> list[JobPosting]:
    statement = select(JobPosting)
    if q:
        statement = statement.where(
            or_(
                JobPosting.title.icontains(q, autoescape=True),
                JobPosting.description.icontains(q, autoescape=True),
                JobPosting.company.icontains(q, autoescape=True),
            )
        )
    if location:
        statement = statement.where(JobPosting.location.icontains(location, autoescape=True))
    if provider:
        statement = statement.join(JobSource).where(JobSource.kind == provider)
    if workplace_type:
        statement = statement.where(JobPosting.workplace_type == workplace_type)
    if availability:
        statement = statement.where(JobPosting.availability == availability)
    if discovered_after:
        statement = statement.where(JobPosting.first_discovered_at >= discovered_after)
    if published_after:
        statement = statement.where(JobPosting.published_at >= published_after)
    if min_priority is not None:
        statement = statement.where(JobPosting.search_priority >= min_priority)
    if min_score is not None or sort == "score":
        statement = statement.outerjoin(MatchScore, MatchScore.job_id == JobPosting.id)
        if min_score is not None:
            statement = statement.where(MatchScore.score >= min_score)
        if sort == "score":
            statement = statement.order_by(MatchScore.score.desc().nulls_last())
    if not include_duplicates:
        statement = statement.where(JobPosting.duplicate_of_id.is_(None))
    if sort == "priority":
        statement = statement.order_by(JobPosting.search_priority.desc())
    return list(
        session.scalars(statement.order_by(JobPosting.id.desc()).limit(limit).offset(offset))
    )


@router.post("", response_model=JobRead, status_code=201)
def create_job(payload: JobCreate, session: Database) -> JobPosting:
    if session.get(JobSource, payload.source_id) is None:
        raise HTTPException(status_code=422, detail="Unknown job source")
    job = JobPosting(**payload.model_dump(mode="json"))
    job.workplace_type = "remote" if payload.remote else "unknown"
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, session: Database) -> JobPosting:
    return find_job(session, job_id)


@router.post("/{job_id}/match", response_model=MatchRead)
def match_job(job_id: int, session: Database) -> MatchScore:
    # Serialize matching with profile updates to avoid persisting stale scores.
    profile = session.scalar(
        select(CandidateProfile).where(CandidateProfile.id == 1).with_for_update()
    )
    job = find_job(session, job_id)
    if profile is None:
        raise HTTPException(status_code=409, detail="Save a candidate profile before matching")
    match = persist_match(session, profile, job)
    session.commit()
    session.refresh(match)
    return match
