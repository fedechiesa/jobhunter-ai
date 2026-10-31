import pytest
from pydantic import ValidationError

from app.schemas import JobCreate, ProfileInput
from app.services.matching import calculate_match
from app.services.opportunities import assess, experience


@pytest.mark.parametrize(
    ("location", "mode", "value", "status", "category"),
    [
        ("Argentina", "remote", "argentina", "confirmed", "argentina_priority"),
        ("CABA", "hybrid", "argentina", "inferred", "argentina_priority"),
        ("GBA", "onsite", "argentina", "inferred", "argentina_priority"),
        ("Buenos Aires", "unknown", "argentina", "inferred", "review_needed"),
        ("Córdoba, Argentina", "onsite", "argentina", "confirmed", "review_needed"),
        ("Worldwide", "remote", "possible_argentina", "inferred", "review_needed"),
        ("LATAM", "remote", "possible_argentina", "inferred", "review_needed"),
        ("Americas", "remote", "possible_argentina", "inferred", "review_needed"),
        ("Remote", "remote", "unknown", "unknown", "review_needed"),
        ("United States only", "remote", "incompatible", "confirmed", "deprioritized"),
        ("Madrid, Spain", "onsite", "other", "confirmed", "deprioritized"),
        ("Córdoba, Spain", "remote", "other", "confirmed", "review_needed"),
        ("Little Rock, AR", "remote", "unknown", "unknown", "review_needed"),
    ],
)
def test_geography_is_not_inferred_from_remote(location, mode, value, status, category):
    result = assess("Python Developer Junior", "Python", location, mode)
    assert result["geography"]["value"] == value
    assert result["geography"]["status"] == status
    assert result["category"] == category
    assert result["reasons"]


def test_description_country_mentions_do_not_prove_eligibility():
    incidental = assess("Data Analyst Jr", "Our customers are in Argentina", "Remote", "remote")
    explicit = assess("Data Analyst Jr", "Candidates from Argentina welcome", "Remote", "remote")
    excluded = assess(
        "Data Analyst Jr",
        "Remote from Argentina. Not available in Argentina",
        "Worldwide",
        "remote",
    )
    assert incidental["geography"]["status"] == "unknown"
    assert explicit["category"] == "international_alternative"
    assert excluded["category"] == "deprioritized"


@pytest.mark.parametrize(
    ("title", "description", "level", "category"),
    [
        ("Data Analyst Trainee", "SQL", "junior", "argentina_priority"),
        ("BI Jr.", "SQL", "junior", "argentina_priority"),
        ("Backend Entry Level", "Python", "junior", "argentina_priority"),
        ("Python Developer", "1-2 years of experience", "junior", "argentina_priority"),
        ("Python Developer", "Experience preferred", "unknown", "review_needed"),
        ("Python Developer", "5 years of experience preferred", "unknown", "review_needed"),
        ("Python Developer Junior", "5 years of experience", "junior", "deprioritized"),
        ("Senior Python Developer", "", "senior", "deprioritized"),
        ("Staff Backend Engineer", "", "senior", "deprioritized"),
        ("Principal Engineer", "", "senior", "deprioritized"),
        ("Lead Data Analyst", "", "senior", "deprioritized"),
        ("Junior Sales Representative", "", "junior", "deprioritized"),
    ],
)
def test_seniority_and_ambiguous_requirements(title, description, level, category):
    result = assess(title, description, "Argentina", "remote")
    assert result["seniority"]["value"] == level
    assert result["category"] == category


@pytest.mark.parametrize(
    ("text", "minimum", "maximum"),
    [
        ("0–2 years of experience", 0, 2),
        ("Mínimo 1 año de experiencia", 1, 1),
        ("2 a 3 años de experiencia profesional", 2, 3),
        ("No previous experience required", 0, 0),
        ("Sin experiencia previa", 0, 0),
        ("Knowledge preferred", None, None),
        ("3 years of experience preferred", None, None),
        ("The team spent 3 years in development", None, None),
    ],
)
def test_experience_uncertainty(text, minimum, maximum):
    result = experience(text)
    assert result["value"] == minimum
    assert result["maximum"] == maximum


def test_english_is_not_assumed_from_posting_language():
    base = assess(
        "Junior Backend Developer", "Requirements: Python experience", "Argentina", "remote"
    )
    advanced = assess(
        "Junior Backend Developer", "Advanced English required", "Argentina", "remote"
    )
    confirmed = assess(
        "Junior Backend Developer",
        "Advanced English required",
        "Argentina",
        "remote",
        english_level="advanced",
    )
    assert base["language"]["status"] == "unknown"
    assert advanced["category"] == "review_needed"
    assert confirmed["category"] == "argentina_priority"


def test_structured_profile_is_validated_without_fabricating_it_experience():
    profile = ProfileInput(
        skills=["Python"],
        professional={
            "education": [{"title": "Fictional course"}],
            "work_experience": [{"role": "Office assistant", "is_it": False}],
            "projects": [{"name": "Fictional lab"}],
        },
    )
    assert profile.experience_years == 0
    assert profile.professional.skills[0].confirmation == "pending"
    assert profile.professional.education[0].status == "unknown"
    assert profile.professional.work_experience[0].paid is None
    with pytest.raises(ValidationError):
        ProfileInput(professional={"education": [{"title": ""}]})
    with pytest.raises(ValidationError):
        ProfileInput(professional={"skills": [{"name": "Unlisted skill"}]})
    with pytest.raises(ValidationError):
        ProfileInput(professional={"languages": [{"name": "English", "level": "expert"}]})


def test_structured_matching_retains_weights_but_does_not_reward_unknown_remote():
    profile = ProfileInput(skills=["python"], professional={}, preferred_location="CABA / GBA")
    remote = JobCreate(
        title="Junior Python",
        company="Example",
        description="Python",
        location="Worldwide",
        remote=True,
        required_skills=["python"],
    )
    result = calculate_match(profile, remote)
    assert result.score == 90 and result.location_score == 0
    assert result.algorithm_version == "deterministic-v1.2-ar"
    argentina = calculate_match(profile, remote.model_copy(update={"location": "Argentina"}))
    assert argentina.score == 100


def test_preference_is_editable():
    result = assess("Python Jr", "", "Córdoba, Argentina", "onsite", preferred_location="Córdoba")
    assert result["category"] == "argentina_priority"


def test_business_mentions_of_ai_do_not_become_developer_roles():
    assert (
        assess("AI-enabled Accountant", "AI tools", "Argentina", "remote")["category"]
        == "deprioritized"
    )
    assert (
        assess("CEO - AI Staffing", "AI tools", "Argentina", "remote")["category"]
        == "deprioritized"
    )
    adjacent = assess("Data Developer", "Python and SQL knowledge", "Argentina", "remote")
    assert adjacent["category"] == "review_needed"


def test_specific_domain_requirements_need_review():
    result = assess(
        "Junior Software Engineer",
        "Prior experience as an accountant or financial analyst. Python is required.",
        "Argentina",
        "remote",
    )
    assert result["category"] == "review_needed"
    assert result["hard_requirements"][0]["status"] == "inferred"


def test_optional_sections_and_spelled_years():
    optional = experience(
        "Nice to have:\n5 years of experience\nRequirements:\nOne year of experience"
    )
    assert optional["value"] == 1
    assert experience("At least five years of hands-on experience")["value"] == 5


def test_local_draft_does_not_echo_private_invalid_inputs(client, application, tmp_path):
    from app.core.config import Settings, get_settings

    draft = tmp_path / "fictional-profile.json"
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://unused@localhost/unused",
        profile_draft_file=draft,
    )
    application.dependency_overrides[get_settings] = lambda: settings
    assert client.get("/profile/draft").status_code == 404
    draft.write_text(
        '{"skills": ["python"], "professional": {"projects": [{"name": "Fictional lab"}]}}',
        encoding="utf-8",
    )
    result = client.get("/profile/draft")
    assert result.status_code == 200 and result.json()["experience_years"] == 0
    draft.write_text('{"private_input": "do not echo this"}', encoding="utf-8")
    result = client.get("/profile/draft")
    assert result.status_code == 422 and "do not echo" not in result.text
    application.dependency_overrides.clear()


def test_combined_dotnet_declaration_covers_explicit_component_skills():
    profile = ProfileInput(skills=["C#/.NET"], professional={})
    job = JobCreate(
        title="Backend Jr",
        company="Example",
        description="C# and .NET",
        required_skills=["c#", ".net"],
    )
    assert calculate_match(profile, job).skill_score == 100


@pytest.mark.parametrize("title", ["Software Engineer", "Junior Backend Developer"])
def test_range_extending_beyond_target_is_never_automatically_prioritized(title):
    result = assess(
        title,
        "Required Qualifications\n2-4 years of experience\nIndustry experience is not required.",
        "Buenos Aires",
        "remote",
    )
    assert result["category"] == "review_needed"
    assert result["experience"]["value"] == 2 and result["experience"]["maximum"] == 4
    assert result["seniority"]["value"] == ("junior" if title.startswith("Junior") else "unknown")
    assert not any("not required" in item["evidence"] for item in result["hard_requirements"])


@pytest.mark.parametrize(
    "description",
    [
        "Strong written and verbal English communication skills.",
        "Professional written and spoken English",
        "Proficiency in English.",
    ],
)
def test_english_communication_requirement_keeps_uncertain_level(description):
    result = assess("Python Developer Junior", description, "Argentina", "remote")
    assert result["language"]["value"] == "english_communication_required"
    assert result["category"] == "review_needed"


def test_redundant_number_notation_and_domain_requirement():
    text = (
        "What We Look For:\nMinimum of two (2) years of experience in a fraud detection role.\n"
        "Minimum of two (2) years of experience working with SQL and Python."
    )
    result = assess("Fraud Data Analyst", text, "Argentina", "remote")
    assert result["experience"]["value"] == 2
    assert result["category"] == "review_needed"
    assert len(result["hard_requirements"]) == 2
    assert experience("two (5) years of experience")["value"] is None
