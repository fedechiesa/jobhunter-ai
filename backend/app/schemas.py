from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, field_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Skill = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Skills = Annotated[list[Skill], Field(max_length=100)]
Years = Annotated[int, Field(ge=0, le=80, strict=True)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProfileInput(InputModel):
    skills: Skills = Field(default_factory=list)
    experience_years: Years = 0
    preferred_location: str = Field(default="", max_length=200)
    prefer_remote: bool = True

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        return sorted({skill.casefold() for skill in value})


class ProfileRead(ProfileInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class JobCreate(InputModel):
    title: ShortText
    company: ShortText
    description: str = Field(min_length=1, max_length=20000)
    location: str = Field(default="", max_length=200)
    remote: bool = False
    required_skills: Skills = Field(default_factory=list)
    experience_years: Years = 0
    url: HttpUrl | None = Field(default=None, max_length=2048)
    source_id: int = Field(default=1, ge=1)

    @field_validator("required_skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        return sorted({skill.casefold() for skill in value})


class MatchResult(BaseModel):
    score: float
    skill_score: float
    experience_score: float
    location_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    algorithm_version: str = "deterministic-v1.1"


class MatchRead(MatchResult):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    candidate_id: int
    created_at: datetime


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    description: str
    location: str
    remote: bool
    required_skills: list[str]
    experience_years: int
    url: str | None
    source_id: int
    created_at: datetime
    match_score: MatchRead | None
    provider: str
    external_id: str | None
    apply_url: str | None
    published_at: datetime | None
    first_discovered_at: datetime
    last_seen_at: datetime
    availability: str
    discovery_status: str
    workplace_type: str
    duplicate_of_id: int | None
    search_priority: float
    seniority: str
    requirements_inferred: bool
    experience_years_known: bool
