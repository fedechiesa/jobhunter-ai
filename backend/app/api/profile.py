from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_session
from app.models import CandidateProfile, JobPosting, MatchScore
from app.schemas import ProfileInput, ProfileRead
from app.services.classification import classify_job

router = APIRouter(prefix="/profile", tags=["profile"])
Database = Annotated[Session, Depends(get_session)]


@router.get("/draft", response_model=ProfileInput)
def get_local_draft(settings: Annotated[Settings, Depends(get_settings)]):
    """Explicit local user input, never a checked-in personal default or a CV parser."""
    try:
        return ProfileInput.model_validate_json(
            settings.profile_draft_file.read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No local profile draft") from None
    except (OSError, ValidationError):
        raise HTTPException(status_code=422, detail="Invalid local profile draft") from None


@router.get("", response_model=ProfileRead)
def get_profile(session: Database) -> CandidateProfile:
    profile = session.get(CandidateProfile, 1)
    if profile is None:
        raise HTTPException(status_code=404, detail="Save a candidate profile first")
    return profile


@router.put("", response_model=ProfileRead)
def save_profile(payload: ProfileInput, session: Database) -> CandidateProfile:
    profile = session.scalar(
        select(CandidateProfile).where(CandidateProfile.id == 1).with_for_update()
    )
    if profile is None:
        profile = CandidateProfile(id=1, **payload.model_dump())
        session.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    # Scores refer to this profile's current inputs; invalidate them atomically.
    session.execute(delete(MatchScore))
    for job in session.scalars(select(JobPosting)):
        classify_job(job, profile)
    session.commit()
    session.refresh(profile)
    return profile
