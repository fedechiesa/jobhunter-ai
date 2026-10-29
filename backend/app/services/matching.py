from app.schemas import JobCreate, MatchResult, ProfileInput


def calculate_match(profile: ProfileInput, job: JobCreate) -> MatchResult:
    """Exact normalized skill overlap (70%), experience (20%), location (10%)."""
    required = {skill.strip().casefold() for skill in job.required_skills}
    available = {skill.strip().casefold() for skill in profile.skills}
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
        or profile.preferred_location.casefold() == job.location.casefold()
    )
    location_score = 100.0 if location_ok else 0.0
    return MatchResult(
        score=round(skill_score * 0.7 + experience_score * 0.2 + location_score * 0.1, 2),
        skill_score=round(skill_score, 2),
        experience_score=round(experience_score, 2),
        location_score=location_score,
        matched_skills=matched,
        missing_skills=sorted(required - available),
    )
