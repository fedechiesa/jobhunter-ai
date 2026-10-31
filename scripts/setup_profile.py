"""Load explicit private profile data, then reclassify history without deleting jobs."""

import argparse

from app.core.config import get_settings
from app.db import get_engine
from app.models import CandidateProfile, JobPosting, MatchScore
from app.schemas import ProfileInput
from app.services.classification import classify_job
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing profile with the local draft",
    )
    parser.add_argument(
        "--reclassify-only",
        action="store_true",
        help="Reclassify existing jobs using the saved profile",
    )
    args = parser.parse_args()
    try:
        payload = (
            None
            if args.reclassify_only
            else ProfileInput.model_validate_json(
                get_settings().profile_draft_file.read_text(encoding="utf-8")
            )
        )
        with Session(get_engine()) as session:
            profile = session.scalar(
                select(CandidateProfile)
                .where(CandidateProfile.id == 1)
                .with_for_update()
            )
            if payload:
                if profile and not args.replace:
                    print(
                        "Existing profile preserved. Use the frontend or explicit --replace."
                    )
                    return 1
                if profile is None:
                    profile = CandidateProfile(id=1, **payload.model_dump())
                    session.add(profile)
                else:
                    for key, value in payload.model_dump().items():
                        setattr(profile, key, value)
                session.execute(delete(MatchScore))
            count = 0
            for job in session.scalars(select(JobPosting)):
                classify_job(job, profile)
                count += 1
            session.commit()
        print(
            f"Profile processed; {count} historical jobs classified. No personal data logged."
        )
        return 0
    except (OSError, ValidationError):
        print("Missing or invalid private profile draft; no changes saved.")
        return 1
    except SQLAlchemyError:
        print("Database unavailable or migrations missing; no changes saved.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
