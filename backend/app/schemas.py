from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Skill = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Skills = Annotated[list[Skill], Field(max_length=100)]
Years = Annotated[int, Field(ge=0, le=80, strict=True)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


Confirmation = Literal["pending", "user_confirmed"]


class SkillEvidence(InputModel):
    name: Skill
    confirmation: Confirmation = "pending"
    details: str = Field(default="", max_length=1000)


class Education(InputModel):
    title: ShortText
    institution: str = Field(default="", max_length=200)
    status: Literal["completed", "in_progress", "unknown"] = "unknown"
    confirmation: Confirmation = "pending"


class WorkExperience(InputModel):
    role: ShortText
    details: str = Field(default="", max_length=2000)
    is_it: bool = False
    paid: bool | None = None
    confirmation: Confirmation = "pending"


class Project(InputModel):
    name: ShortText
    description: str = Field(default="", max_length=2000)
    technologies: Skills = Field(default_factory=list)
    confirmation: Confirmation = "pending"


class Language(InputModel):
    name: ShortText
    level: Literal["unknown", "basic", "intermediate", "advanced", "fluent", "native"] = "unknown"
    confirmation: Confirmation = "pending"


class ProfessionalDetails(InputModel):
    schema_version: Literal[1] = 1
    origin: Literal["user_declared", "local_cv"] = "user_declared"
    skills: list[SkillEvidence] = Field(default_factory=list, max_length=100)
    education: list[Education] = Field(default_factory=list, max_length=30)
    work_experience: list[WorkExperience] = Field(default_factory=list, max_length=50)
    projects: list[Project] = Field(default_factory=list, max_length=50)
    languages: list[Language] = Field(default_factory=list, max_length=20)
    target_roles: list[ShortText] = Field(default_factory=list, max_length=30)
    residence_country: str = Field(default="AR", pattern=r"^[A-Z]{2}$")
    preferred_languages: list[Literal["es", "en"]] = Field(
        default_factory=lambda: ["es"], max_length=2
    )
    first_it_job: bool = True
    max_experience_years: Years = 2


class ProfileInput(InputModel):
    skills: Skills = Field(default_factory=list)
    experience_years: Years = 0
    preferred_location: str = Field(default="", max_length=200)
    prefer_remote: bool = True
    professional: ProfessionalDetails | None = None

    @model_validator(mode="after")
    def align_skill_evidence(self):
        if self.professional is not None:
            evidence = {item.name.casefold(): item for item in self.professional.skills}
            if set(evidence) - set(self.skills):
                raise ValueError("Skill evidence must refer to declared skills")
            self.professional.skills = [
                SkillEvidence(
                    name=name,
                    confirmation=evidence[name].confirmation if name in evidence else "pending",
                    details=evidence[name].details if name in evidence else "",
                )
                for name in self.skills
            ]
        return self

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
    country: str
    compatibility: str
    assessment: dict
