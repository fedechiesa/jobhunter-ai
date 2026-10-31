"""Conservative, inspectable rules. A remote label never proves country eligibility."""

import re
import unicodedata

VERSION = "argentina-v1.1"


def folded(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c)
    )


def fact(value, status: str, evidence: str = "") -> dict:
    return {"value": value, "status": status, "evidence": evidence[:400]}


def role_matches(title: str, target_roles: list[str] | None) -> bool:
    families = [
        (
            r"data analyst|analista.*datos|\bbi\b|business intelligence",
            r"data analyst|analista (?:de )?datos|reporting analyst|\bbi\b|business intelligence",
        ),
        (r"python", r"python"),
        (
            r"\bai\b|data scien|machine learning|inteligencia artificial",
            r"\b(?:ai|ml)\b.*(?:engineer|developer|trainee|intern)|data scien|ciencia de datos|"
            r"machine learning.*(?:engineer|trainee)",
        ),
        (
            r"backend|full.?stack|software|desarrollador",
            r"backend|back.end|full.?stack|software (?:engineer|developer)|desarrollador",
        ),
    ]
    if not target_roles:
        return any(re.search(pattern, title) for _, pattern in families)
    for role in target_roles:
        label = folded(role)
        selected = [pattern for marker, pattern in families if re.search(marker, label)]
        if any(re.search(pattern, title) for pattern in selected):
            return True
        if not selected:
            words = set(re.findall(r"\w+", label)) - {"jr", "junior", "trainee", "de"}
            if words and words <= set(re.findall(r"\w+", title)):
                return True
    return False


def experience(description: str) -> dict:
    required, optional = [], []
    optional_section = False
    pattern = re.compile(
        r"\b(\d{1,2})(?:\s*(?:[-–]|to|a)\s*(\d{1,2}))?\s*\+?\s*(?:years?|anos?)"
        r"\s+(?:(?:of|de)\s+)?(?:(?:professional|software|engineering|industry|hands-on|"
        r"relevant|work|laboral|profesional)\s+){0,3}"
        r"(?:experience|experiencia|in\s+\w+|en\s+\w+)",
        re.I,
    )
    for line in description.splitlines():
        text = folded(line)
        if re.search(
            r"^(?:nice.to.have|preferred qualifications|deseable|valoraremos|bonus)\b", text
        ):
            optional_section = True
        elif re.search(
            r"^(?:requirements|requisitos|must.have|what we look for|qualifications|"
            r"required experience)\b",
            text,
        ):
            optional_section = False
        numbers = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "ten": 10,
            "un": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
        }
        # Match redundant number forms only when both spellings agree.
        text = re.sub(
            r"\b(" + "|".join(numbers) + r")\s*\((\d{1,2})\)(?=\s+(?:years?|anos?))",
            lambda match, numbers=numbers: (
                match[2] if numbers[match[1]] == int(match[2]) else "ambiguous-number"
            ),
            text,
        )
        text = re.sub(
            r"\b(" + "|".join(numbers) + r")(?=\s+(?:years?|anos?))",
            lambda match, numbers=numbers: str(numbers[match[0]]),
            text,
        )
        if re.search(r"\b(?:team spent|founded|company has|empresa tiene)\b", text):
            continue
        for match in pattern.finditer(text):
            target = (
                optional
                if optional_section
                or re.search(
                    r"preferred|nice to have|plus|deseable|valorable|idealmente|preferentemente",
                    text,
                )
                else required
            )
            target.append((int(match[1]), int(match[2] or match[1]), line.strip()))
    if required:
        minimum, maximum, line = max(required, key=lambda item: item[0])
        return {**fact(minimum, "inferred", line), "maximum": maximum, "optional": False}
    if re.search(
        r"no (?:prior |previous |professional )?experience (?:is )?required|"
        r"sin experiencia|primera experiencia",
        folded(description),
    ):
        return {
            **fact(0, "confirmed", "Explicit first-experience wording"),
            "maximum": 0,
            "optional": False,
        }
    return {
        **fact(None, "unknown", optional[0][2] if optional else ""),
        "maximum": None,
        "optional": bool(optional),
    }


def assess(
    title: str,
    description: str,
    location: str,
    workplace_type: str,
    *,
    max_years: int = 2,
    english_level: str = "intermediate",
    target_roles: list[str] | None = None,
    preferred_location: str = "CABA / GBA",
    experience_evidence: dict | None = None,
) -> dict:
    loc, text, name = folded(location), folded(description), folded(title)
    reasons = []
    ar_explicit = bool(re.search(r"\b(?:argentina|argentinian|argentine)\b", loc)) or loc == "ar"
    metro = bool(re.search(r"\b(?:caba|gba|capital federal|buenos aires|gran buenos aires)\b", loc))
    other_ar = bool(
        re.search(r"\b(?:cordoba|rosario|mendoza|la plata|tucuman|mar del plata)\b", loc)
    )
    explicit_from = re.search(
        r"(?:remote (?:from|in)|remoto (?:desde|en)|based in|residir en|residencia en|"
        r"candidates (?:from|in))\s+argentina\b",
        text,
    )
    restriction = re.search(
        r"(?:\b(?:us|usa|united states|canada|uk|europe|eu)[ -]only\b|"
        r"\bonly (?:in|from|within) (?:the )?(?:us|usa|united states|canada|uk|europe|eu)\b|"
        r"\bmust (?:be (?:based|located)|reside|live) in (?:the )?"
        r"(?:us|usa|united states|canada|uk)\b|"
        r"\b(?:not available in|excluding|except|no disponible en) argentina\b)",
        loc + "\n" + text,
    )
    region = bool(
        re.search(
            r"\b(?:latam|latin america|latinoamerica|americas|worldwide|anywhere|global)\b", loc
        )
    )
    foreign = bool(
        re.search(
            r"\b(?:united states|usa|new york|san francisco|canada|toronto|london|uk|europe|"
            r"spain|espana|madrid|mexico|brazil|brasil|sao paulo|montevideo|uruguay|chile|"
            r"santiago|colombia|bogota|peru|lima)\b",
            loc,
        )
    )
    if restriction:
        geography = fact("incompatible", "confirmed", restriction[0])
    elif ar_explicit:
        geography = fact("argentina", "confirmed", location)
    elif explicit_from:
        geography = fact("international_argentina", "confirmed", explicit_from[0])
    elif metro or (other_ar and not foreign):
        geography = fact("argentina", "inferred", location)
    elif region and workplace_type == "remote":
        geography = fact("possible_argentina", "inferred", location)
    elif foreign:
        geography = fact("other", "confirmed", location)
    else:
        geography = fact("unknown", "unknown", location)
    years = experience_evidence or experience(description)
    senior = re.search(
        r"\b(?:senior|sr|ssr|semi senior|semi-senior|staff|lead|principal|manager|director|"
        r"head|ceo|cto|vp)\b",
        name,
    )
    junior = re.search(
        r"\b(?:junior|jr|trainee|entry[- ]level|intern|internship|pasante|pasantia|graduate|"
        r"sin experiencia|primer empleo)\b",
        name,
    )
    level = (
        fact("senior", "confirmed", senior[0])
        if senior
        else fact("junior", "confirmed", junior[0])
        if junior
        else fact("junior", "inferred", years["evidence"])
        if years["value"] is not None
        and years["value"] <= max_years
        and years["maximum"] <= max_years
        else fact("unknown", "unknown")
    )
    advanced = re.search(
        r"(?:\b(?:advanced|fluent|native|c1|c2|business[- ]level|excellent)\b.{0,35}\benglish\b|"
        r"\benglish\b.{0,25}\b(?:advanced|fluent|native|c1|c2|proficiency)\b|"
        r"ingles\s+(?:avanzado|fluido|bilingue))",
        text,
    )
    intermediate = re.search(
        r"(?:intermediate english|english.{0,15}intermediate|ingles intermedio|b1|b2)", text
    )
    communication = re.search(
        r"(?:\b(?:strong|professional|excellent)\b[^.\n]{0,50}\benglish\b|"
        r"\bproficiency in english\b|\benglish proficiency\b)",
        text,
    )
    language = (
        fact("advanced_english", "inferred", advanced[0])
        if advanced
        else fact("intermediate_english", "inferred", intermediate[0])
        if intermediate
        else fact("english_communication_required", "inferred", communication[0])
        if communication
        else fact("unspecified", "unknown")
    )
    # Language of the prose is a hint, never a hiring requirement.
    prose_language = (
        "es"
        if re.search(r"\b(?:buscamos|requisitos|experiencia|equipo)\b", text)
        else "en"
        if re.search(r"\b(?:requirements|experience|looking for)\b", text)
        else "unknown"
    )
    prose = fact(prose_language, "unknown" if prose_language == "unknown" else "inferred")
    relevant = role_matches(name, target_roles)
    adjacent = bool(
        re.search(
            r"data (?:developer|engineer|analytics)|frontend|front.end|technical solutions|"
            r"analista programador",
            name,
        )
    )
    domain_requirement = re.search(
        r"(?:prior experience as an (?:accountant|financial analyst)|accounting experience|"
        r"experiencia (?:previa )?(?:como contador|contable))",
        text + "\n" + name,
    )
    fraud_requirement = re.search(
        r"experience\s+in\s+(?:a\s+)?fraud (?:detection|prevention|investigation)", text
    )
    hard_requirements = []
    mandatory_section = False
    for line in description.splitlines():
        line_text = folded(line).strip()
        if re.search(
            r"^(?:required (?:qualifications|skills)|requirements|requisitos|"
            r"what we(?:'re| are)? looking for|what we look for|basic qualifications)\b",
            line_text,
        ):
            mandatory_section = True
            continue
        if re.search(
            r"^(?:nice.to.have|preferred|responsibilities|perks|what you|who would|"
            r"about you|about (?:us|the)|what makes|what we offer|interview|tech stack)\b",
            line_text,
        ):
            mandatory_section = False
            continue
        negative = re.search(
            r"not (?:required|mandatory)|no (?:se requiere|es obligatorio)", line_text
        )
        if (
            line_text
            and not negative
            and (
                mandatory_section
                or re.search(
                    r"\b(?:must|required|mandatory|excluyente|obligatorio|indispensable)\b",
                    line_text,
                )
            )
        ):
            hard_requirements.append(fact(line.strip()[:400], "inferred", line))
    category = "review_needed"
    if geography["value"] == "incompatible" or (
        foreign and workplace_type in {"hybrid", "onsite"} and not (ar_explicit or metro)
    ):
        category = "deprioritized"
        reasons.append("Restricción geográfica incompatible con Argentina")
    elif senior or (years["value"] is not None and years["value"] > max_years):
        category = "deprioritized"
        reasons.append("Seniority o experiencia requerida supera el objetivo inicial")
    elif not relevant:
        category = "review_needed" if adjacent else "deprioritized"
        reasons.append(
            "Rol técnico cercano; revisar requisitos"
            if adjacent
            else "Título fuera de los roles objetivo; se conserva para consulta"
        )
    elif years["maximum"] is not None and years["maximum"] > max_years:
        reasons.append(
            "El rango de experiencia supera el objetivo junior; revisar antes de priorizar"
        )
    elif advanced and english_level not in {"advanced", "fluent", "native"}:
        reasons.append("Revisar inglés avanzado: el perfil no lo declara")
    elif communication and not intermediate and not advanced:
        reasons.append("Revisar exigencia de comunicación en inglés: nivel exacto no especificado")
    elif domain_requirement:
        reasons.append(
            "Revisar experiencia contable específica; "
            "no equivale a experiencia administrativa/comercial"
        )
    elif fraud_requirement:
        reasons.append(
            "Revisar experiencia específica en fraude; conocimientos de SQL no la acreditan"
        )
    elif geography["value"] == "argentina" and level["value"] == "junior":
        local_preference = folded(preferred_location)
        local_match = (
            metro
            if any(term in local_preference for term in ("caba", "gba", "buenos aires"))
            else bool(local_preference and local_preference in loc)
        )
        if (local_match and workplace_type in {"onsite", "hybrid"}) or workplace_type == "remote":
            category = "argentina_priority"
        else:
            reasons.append("Revisar modalidad o traslado fuera de CABA/GBA")
    elif (
        geography["value"] == "international_argentina"
        and workplace_type == "remote"
        and level["value"] == "junior"
    ):
        category = "international_alternative"
    reasons.append(
        f"Geografía: {geography['value']} ({geography['status']}) — "
        f"{geography['evidence'] or 'sin evidencia'}"
    )
    reasons.append(f"Seniority: {level['value']} ({level['status']})")
    if years["value"] is None:
        reasons.append("Años requeridos desconocidos; no equivalen a cero")
    if communication and not advanced and not intermediate:
        reasons.append(
            "La fuente exige comunicación/proficiency en inglés; no se presume nivel avanzado"
        )
    if fraud_requirement:
        reasons.append(
            "La fuente exige antecedentes específicos de detección o prevención de fraude"
        )
    if geography["value"] in {"possible_argentina", "unknown", "other"}:
        reasons.append("La modalidad remota no confirma admisión desde Argentina")
    return {
        "version": VERSION,
        "category": category,
        "geography": geography,
        "country": "AR"
        if ar_explicit or metro or (other_ar and not foreign) or explicit_from
        else "other"
        if foreign
        else "unknown",
        "area": "CABA/GBA" if metro else "other_argentina" if other_ar else "unknown",
        "seniority": level,
        "experience": years,
        "language": language,
        "posting_language": prose,
        "workplace": fact(
            workplace_type, "unknown" if workplace_type == "unknown" else "confirmed", location
        ),
        "reasons": reasons,
        "hard_requirements": hard_requirements[:20],
    }
