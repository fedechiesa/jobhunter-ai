import pytest
from pydantic import ValidationError

from app.schemas import JobCreate, ProfileInput
from tests.conftest import isolated_test_url


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "   "),
        ("company", ""),
        ("description", " \n "),
        ("experience_years", -1),
        ("experience_years", 1.5),
        ("experience_years", True),
        ("url", "javascript:alert(1)"),
        ("url", "ftp://example.com"),
        ("required_skills", [""]),
        ("source_id", 0),
        ("unexpected", "value"),
    ],
)
def test_invalid_jobs(job_payload, field, value):
    with pytest.raises(ValidationError):
        JobCreate(**(job_payload | {field: value}))


def test_normalization(job_payload):
    job = JobCreate(**(job_payload | {"required_skills": [" PYTHON ", "python", "SQL"]}))
    assert job.required_skills == ["python", "sql"]
    assert ProfileInput(skills=["SQL", " sql "]).skills == ["sql"]


@pytest.mark.parametrize("value", [-1, 81, 2.5])
def test_invalid_profile_experience(value):
    with pytest.raises(ValidationError):
        ProfileInput(experience_years=value)


@pytest.mark.parametrize(
    "url",
    [None, "sqlite:///test.db", "postgresql+psycopg://u@localhost/jobhunter"],
)
def test_database_guard_rejects_unsafe_targets(url):
    with pytest.raises(ValueError):
        isolated_test_url(url, None)


def test_database_guard_rejects_same_development_target():
    with pytest.raises(ValueError):
        isolated_test_url(
            "postgresql+psycopg://test@localhost/shared_test",
            "postgresql+psycopg://dev@localhost:5432/shared_test",
        )
