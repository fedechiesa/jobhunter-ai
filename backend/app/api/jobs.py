from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import CandidateProfile, JobPosting, JobSource, MatchScore
from app.schemas import JobCreate, JobRead, MatchRead, ProfileInput
from app.services.matching import calculate_match

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
) -> list[JobPosting]:
    return list(
        session.scalars(
            select(JobPosting).order_by(JobPosting.id.desc()).limit(limit).offset(offset)
        )
    )


@router.post("", response_model=JobRead, status_code=201)
def create_job(payload: JobCreate, session: Database) -> JobPosting:
    if session.get(JobSource, payload.source_id) is None:
        raise HTTPException(status_code=422, detail="Unknown job source")
    job = JobPosting(**payload.model_dump(mode="json"))
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
    result = calculate_match(
        ProfileInput.model_validate(profile, from_attributes=True),
        JobCreate.model_validate(job, from_attributes=True),
    )
    match = session.scalar(select(MatchScore).where(MatchScore.job_id == job_id))
    if match is None:
        match = MatchScore(job_id=job_id, candidate_id=1, **result.model_dump())
        session.add(match)
    else:
        for key, value in result.model_dump().items():
            setattr(match, key, value)
    session.commit()
    session.refresh(match)
    return match
