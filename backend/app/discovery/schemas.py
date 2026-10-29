from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints


class BoardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    provider: Literal["greenhouse", "lever", "ashby"]
    board_token: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    company: str = Field(min_length=1, max_length=100)
    region: Literal["global", "eu"] = "global"
    enabled: bool = True


class NormalizedJob(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    external_id: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=200000)
    location: str = Field(max_length=200)
    workplace_type: Literal["remote", "hybrid", "onsite", "unknown"]
    url: HttpUrl = Field(max_length=2048)
    apply_url: HttpUrl = Field(max_length=2048)
    published_at: datetime | None = None


PreferenceText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class SearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    roles: list[PreferenceText] = Field(
        default_factory=lambda: [
            "Data Analyst Junior / Trainee",
            "Python Developer Junior / Trainee",
            "AI / LLM Developer Junior",
            "Data Engineer Junior / Trainee",
            "QA Automation Junior",
        ],
        max_length=30,
    )
    technologies: list[PreferenceText] = Field(
        default_factory=lambda: [
            "Python",
            "SQL",
            "PostgreSQL",
            "SQL Server",
            "FastAPI",
            "React",
            "JavaScript",
            "Machine Learning",
            "LLM",
            "RAG",
            "LangChain",
            "Docker",
        ],
        max_length=100,
    )
    locations: list[PreferenceText] = Field(
        default_factory=lambda: ["Argentina remoto", "CABA", "GBA", "Buenos Aires"], max_length=30
    )
    max_experience_years: int = Field(default=2, ge=0, le=80, strict=True)
    deprioritize_senior: bool = True


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    kind: str
    board_token: str | None
    region: str
    enabled: bool
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    last_result: dict | None


class SourceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class SyncRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    source_results: list[dict]
