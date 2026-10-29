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
    __table_args__ = (UniqueConstraint("kind", "board_token", "region", name="uq_source_board"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True)
    company_name: Mapped[str | None] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(50))
    board_token: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(10), default="global", server_default="global")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(200))
    last_result: Mapped[dict | None] = mapped_column(JSON)


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (
        CheckConstraint("experience_years >= 0", name="ck_job_experience"),
        UniqueConstraint("source_id", "external_id", name="uq_job_external"),
    )

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
    source: Mapped[JobSource] = relationship(lazy="joined")
    external_id: Mapped[str | None] = mapped_column(String(300))
    apply_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    availability: Mapped[str] = mapped_column(String(30), default="active", server_default="active")
    discovery_status: Mapped[str] = mapped_column(String(30), default="new", server_default="new")
    workplace_type: Mapped[str] = mapped_column(
        String(20), default="unknown", server_default="unknown"
    )
    content_hash: Mapped[str | None] = mapped_column(String(64))
    canonical_url: Mapped[str | None] = mapped_column(Text, index=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id", name="fk_job_duplicate")
    )
    search_priority: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    seniority: Mapped[str] = mapped_column(String(20), default="unknown", server_default="unknown")
    requirements_inferred: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    experience_years_known: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    @property
    def provider(self) -> str:
        return self.source.kind


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


class SearchPreferences(Base):
    __tablename__ = "search_preferences"
    __table_args__ = (CheckConstraint("id = 1", name="ck_search_single_user"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    roles: Mapped[list[str]] = mapped_column(JSON)
    technologies: Mapped[list[str]] = mapped_column(JSON)
    locations: Mapped[list[str]] = mapped_column(JSON)
    max_experience_years: Mapped[int] = mapped_column(Integer)
    deprioritize_senior: Mapped[bool] = mapped_column(Boolean)


class SyncRun(Base):
    __tablename__ = "sync_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_results: Mapped[list[dict]] = mapped_column(JSON, default=list)
