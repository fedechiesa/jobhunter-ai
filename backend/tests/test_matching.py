import pytest

from app.schemas import JobCreate, ProfileInput
from app.services.matching import calculate_match


def test_known_partial_match_and_determinism(job_payload):
    profile = ProfileInput(skills=["python"], experience_years=2)
    job = JobCreate(**job_payload)
    result = calculate_match(profile, job)
    assert result.score == 55  # 50 * .7 + 50 * .2 + 100 * .1
    assert result.matched_skills == ["python"]
    assert result.missing_skills == ["sql"]
    assert calculate_match(profile, job) == result


def test_no_requirements_means_no_penalty(job_payload):
    job = JobCreate(**(job_payload | {"required_skills": [], "experience_years": 0}))
    assert calculate_match(ProfileInput(), job).score == 100


def test_zero_match(job_payload):
    job = JobCreate(**(job_payload | {"remote": False}))
    profile = ProfileInput(preferred_location="Other City")
    assert calculate_match(profile, job).score == 0


@pytest.mark.parametrize(
    ("location", "remote", "prefer_remote", "expected"),
    [
        ("example city", False, False, 100),
        ("Other City", True, True, 100),
        ("Other City", True, False, 0),
        ("Other City", False, True, 0),
        ("", False, False, 100),
    ],
)
def test_location_rule(job_payload, location, remote, prefer_remote, expected):
    profile = ProfileInput(preferred_location=location, prefer_remote=prefer_remote)
    job = JobCreate(**(job_payload | {"remote": remote}))
    assert calculate_match(profile, job).location_score == expected


def test_score_capped_and_order_independent(job_payload):
    profile = ProfileInput(skills=["SQL", "PYTHON", "sql"], experience_years=50)
    result = calculate_match(profile, JobCreate(**job_payload))
    assert result.score == 100
    assert result.matched_skills == ["python", "sql"]


@pytest.mark.parametrize(
    ("advertised", "preference", "expected"),
    [
        ("Montevideo / Buenos Aires / Sao Paulo", "Buenos Aires", 100),
        ("Montevideo (Hybrid) / Buenos Aires", "Montevideo", 100),
        ("  Buenos   Aires (Hybrid) ", " buenos aires ", 100),
        ("Buenos Aires / Montevideo", "Argentina", 0),
        ("Buenos Aires / Montevideo", "Aires", 0),
    ],
)
def test_matching_compares_explicit_location_alternatives(
    job_payload, advertised, preference, expected
):
    job = JobCreate(**(job_payload | {"location": advertised, "remote": False}))
    result = calculate_match(ProfileInput(preferred_location=preference, prefer_remote=False), job)
    assert result.location_score == expected
    assert result.algorithm_version == "deterministic-v1.1"
