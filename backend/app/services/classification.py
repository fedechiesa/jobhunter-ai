from app.models import CandidateProfile, JobPosting
from app.services.opportunities import assess


def classify_job(job: JobPosting, profile: CandidateProfile | None = None) -> None:
    details = profile.professional if profile else None
    options = {"preferred_location": profile.preferred_location} if profile else {}
    if job.external_id is None and job.experience_years_known is not False:
        options["experience_evidence"] = {
            "value": job.experience_years,
            "maximum": job.experience_years,
            "status": "confirmed",
            "evidence": "Carga manual: años requeridos",
            "optional": False,
        }
    if details:
        options["max_years"] = details.get("max_experience_years", 2)
        options["target_roles"] = details.get("target_roles")
        english = next(
            (
                item
                for item in details.get("languages", [])
                if item["name"].casefold() in {"english", "ingles", "inglés", "en"}
            ),
            None,
        )
        options["english_level"] = (
            english["level"]
            if english and english.get("confirmation") == "user_confirmed"
            else "intermediate"
        )
    result = assess(
        job.title,
        job.description,
        job.location_details or job.location,
        job.workplace_type,
        **options,
    )
    result["language_preferred"] = bool(
        details and result["posting_language"]["value"] in details.get("preferred_languages", [])
    )
    if details and details.get("residence_country", "AR") != "AR":
        result["category"] = "review_needed"
        result["reasons"].insert(0, "Perfil fuera de Argentina: revisar alcance de estas reglas")
    if profile and not profile.prefer_remote and job.workplace_type == "remote":
        result["category"] = "deprioritized"
        result["reasons"].insert(0, "El perfil no prefiere ofertas remotas")
    if details and any(item.get("confirmation") == "pending" for item in details.get("skills", [])):
        result["reasons"].append(
            "Competencias del perfil pendientes de confirmación; no se presumen niveles de dominio"
        )
    previous_workplace = (job.assessment or {}).get("workplace")
    if previous_workplace:
        result["workplace"] = previous_workplace
    job.assessment = result
    job.country = result["country"]
    job.compatibility = result["category"]
    job.seniority = result["seniority"]["value"]
