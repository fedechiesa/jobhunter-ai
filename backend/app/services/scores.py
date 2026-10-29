from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CandidateProfile, JobPosting, MatchScore
from app.schemas import JobCreate, ProfileInput
from app.services.matching import calculate_match


def persist_match(session: Session, profile: CandidateProfile, job: JobPosting) -> MatchScore:
    result = calculate_match(
        ProfileInput.model_validate(profile, from_attributes=True),
        JobCreate(
            title=job.title,
            company=job.company,
            description=job.description[:20000],
            location=job.location,
            remote=job.remote,
            required_skills=job.required_skills,
            experience_years=job.experience_years,
        ),
    )
    match = session.scalar(select(MatchScore).where(MatchScore.job_id == job.id))
    if match is None:
        match = MatchScore(job_id=job.id, candidate_id=profile.id, **result.model_dump())
        session.add(match)
    else:
        for key, value in result.model_dump().items():
            setattr(match, key, value)
    return match
