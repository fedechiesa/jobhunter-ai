from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_candidate_single_user"),
        CheckConstraint("experience_years >= 0", name="ck_candidate_experience"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    skills: Mapped[list[str]] = mapped_column(JSON)
    experience_years: Mapped[int] = mapped_column(Integer)
    preferred_location: Mapped[str] = mapped_column(String(200))
    prefer_remote: Mapped[bool] = mapped_column(Boolean)


class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    kind: Mapped[str] = mapped_column(String(50))


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (CheckConstraint("experience_years >= 0", name="ck_job_experience"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200))
    remote: Mapped[bool] = mapped_column(Boolean)
    required_skills: Mapped[list[str]] = mapped_column(JSON)
    experience_years: Mapped[int] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(String(2048))
    source_id: Mapped[int] = mapped_column(ForeignKey("job_sources.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    match_score: Mapped["MatchScore | None"] = relationship(uselist=False, lazy="selectin")


class MatchScore(Base):
    __tablename__ = "match_scores"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_match_job"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_match_score_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    score: Mapped[float] = mapped_column(Float)
    skill_score: Mapped[float] = mapped_column(Float)
    experience_score: Mapped[float] = mapped_column(Float)
    location_score: Mapped[float] = mapped_column(Float)
    matched_skills: Mapped[list[str]] = mapped_column(JSON)
    missing_skills: Mapped[list[str]] = mapped_column(JSON)
    algorithm_version: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
