from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import CandidateProfile, MatchScore
from app.schemas import ProfileInput, ProfileRead

router = APIRouter(prefix="/profile", tags=["profile"])
Database = Annotated[Session, Depends(get_session)]


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
    session.commit()
    session.refresh(profile)
    return profile
