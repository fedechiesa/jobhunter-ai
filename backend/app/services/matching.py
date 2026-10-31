import re

from app.schemas import JobCreate, MatchResult, ProfileInput
from app.services.opportunities import assess


def location_matches(preference: str, advertised: str) -> bool:
    def normalized(value: str) -> str:
        value = re.sub(
            r"\s*\((?:hybrid|remote|onsite|híbrido|remoto|presencial)\)\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )
        return " ".join(value.casefold().split())

    expected = normalized(preference)
    return expected == normalized(advertised) or expected in {
        normalized(location) for location in re.split(r"[/;|\n]", advertised)
    }


def calculate_match(
    profile: ProfileInput, job: JobCreate, geography: dict | None = None
) -> MatchResult:
    """Exact normalized skill overlap (70%), experience (20%), location (10%)."""
    required = {skill.strip().casefold() for skill in job.required_skills}
    available = {skill.strip().casefold() for skill in profile.skills}
    if profile.professional and "c#/.net" in available:
        available.update({"c#", ".net"})
    matched = sorted(required & available)
    skill_score = len(matched) / len(required) * 100 if required else 100.0
    experience_score = (
        min(profile.experience_years / job.experience_years, 1) * 100
        if job.experience_years
        else 100.0
    )
    location_ok = (
        not profile.preferred_location
        or (profile.prefer_remote and job.remote)
        or location_matches(profile.preferred_location, job.location)
    )
    location_score = 100.0 if location_ok else 0.0
    version = "deterministic-v1.1"
    if profile.professional is not None:
        evidence = assess(
            job.title, job.description, job.location, "remote" if job.remote else "unknown"
        )
        eligibility = geography or evidence["geography"]
        city_ok = location_matches(profile.preferred_location, job.location)
        metro_ok = evidence["area"] == "CABA/GBA" and any(
            term in profile.preferred_location.casefold()
            for term in ("caba", "gba", "buenos aires")
        )
        location_score = (
            100.0
            if eligibility["value"] in {"argentina", "international_argentina"}
            and (
                (job.remote and profile.prefer_remote)
                or (not job.remote and (not profile.preferred_location or city_ok or metro_ok))
            )
            else 0.0
        )
        if profile.professional.residence_country != "AR":
            location_score = 0.0
        version = "deterministic-v1.2-ar"
    return MatchResult(
        score=round(skill_score * 0.7 + experience_score * 0.2 + location_score * 0.1, 2),
        skill_score=round(skill_score, 2),
        experience_score=round(experience_score, 2),
        location_score=location_score,
        matched_skills=matched,
        missing_skills=sorted(required - available),
        algorithm_version=version,
    )
