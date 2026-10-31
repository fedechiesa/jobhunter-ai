import re
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.discovery.schemas import SearchInput


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "li", "br", "div", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "li", "div"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value: str) -> str:
    parser = PlainText()
    # Greenhouse can return doubly escaped HTML.
    parser.feed(unescape(unescape(value)))
    return "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())


def canonical_url(value: str) -> str:
    parts = urlsplit(value)
    # Preserve job identifiers (including gh_jid). Remove only known tracking parameters.
    query = sorted(
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in {"gh_src", "lever-source"}
    )
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), "")
    )


def publication_date(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def modality(value: str | None, location: str = "") -> str:
    text = (value or "").casefold()
    if text in {"remote", "hybrid", "onsite"}:
        return text
    if text in {"on-site", "on site"}:
        return "onsite"
    location = location.casefold()
    if "hybrid" in location or "híbrido" in location:
        return "hybrid"
    if any(term in location for term in ("remote", "remoto", "home based", "home-based")):
        return "remote"
    return "unknown"


TECHNOLOGIES = [
    "python",
    "sql",
    "postgresql",
    "sql server",
    "fastapi",
    "react",
    "javascript",
    "typescript",
    "java",
    "node.js",
    "c#",
    ".net",
    "pandas",
    "numpy",
    "scikit-learn",
    "embeddings",
    "machine learning",
    "llm",
    "rag",
    "langchain",
    "docker",
]


def detected_requirements(description: str) -> tuple[list[str], int, bool]:
    lower = description.casefold()
    skills = [
        term for term in TECHNOLOGIES if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", lower)
    ]
    number_and_years = r"\b(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s*\+?\s*(?:years?|años?)\s+"
    years = re.search(
        number_and_years + r"(?:of\s+)?(?:(?:professional|software|engineering|industry|continuous|"
        r"hands-on|relevant|work)\s+){0,3}(?:experience|experiencia)\b",
        lower,
    )
    if years is None:
        # Explicit requirement lines such as "3+ years in fraud prevention".
        # Do not treat an incidental "the team spent 3 years in..." as a requirement.
        years = re.search(
            r"^\s*(?:[-*•]\s*)?(?:(?:minimum(?: of)?|at least)\s+)?"
            + number_and_years
            + r"in\s+\w",
            lower,
            flags=re.MULTILINE,
        )
    return skills, min(int(years[1]), 80) if years else 0, years is not None


def is_talent_pool(title: str) -> bool:
    return bool(re.search(r"\b(?:talent[\s-]+pool|bolsa\s+de\s+talento)\b", title, re.IGNORECASE))


def priority(
    title: str, description: str, location: str, years: int, known: bool, preferences: SearchInput
) -> tuple[float, str]:
    title = title.casefold()
    text = (title + " " + description).casefold()
    senior = bool(
        re.search(r"\b(senior|sr\.?|staff|principal|lead|manager|director|head)\b", title)
    )
    junior = bool(re.search(r"\b(junior|jr\.?|trainee|graduate|intern|entry[- ]level)\b", title))
    seniority = "senior" if senior else "junior" if junior else "unknown"
    # Ignore level words so a role with ambiguous seniority remains discoverable.
    role_tokens = [
        set(re.findall(r"[\w]+", role.casefold())) - {"junior", "trainee", "developer", "jr"}
        for role in preferences.roles
    ]
    title_tokens = set(re.findall(r"[\w]+", title))
    role_score = max(
        (len(tokens & title_tokens) / max(len(tokens), 1) for tokens in role_tokens), default=0
    )
    tech_score = min(
        sum(
            bool(re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", text))
            for term in preferences.technologies
        )
        / 3,
        1,
    )
    loc = location.casefold()
    location_score = any(
        term.casefold().replace(" remoto", "") in loc for term in preferences.locations
    )
    # Worldwide/Americas are hints to review, not a claim of Argentina eligibility.
    if any("argentina" in term.casefold() for term in preferences.locations):
        location_score = location_score or any(
            term in loc for term in ("worldwide", "anywhere", "americas", "latam", "latin america")
        )
    experience_score = (
        1
        if junior or (known and years <= preferences.max_experience_years)
        else 0.5
        if not known
        else 0
    )
    score = role_score * 45 + tech_score * 25 + location_score * 15 + experience_score * 15
    if senior and preferences.deprioritize_senior:
        score *= 0.35
    return round(score, 2), seniority
