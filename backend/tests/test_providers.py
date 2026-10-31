import copy

import httpx2
import pytest

from app.core.config import Settings
from app.discovery.normalization import canonical_url, detected_requirements, plain_text, priority
from app.discovery.providers import JsonReader, ProviderError, PublicBoardProvider
from app.discovery.schemas import BoardConfig, SearchInput


@pytest.fixture
def provider_settings():
    return Settings(_env_file=None, database_url="postgresql+psycopg://unused@localhost/unused")


@pytest.mark.parametrize("header", ["NaN", "Infinity", "-1"])
def test_malformed_retry_delay_cannot_crash_sync_or_trigger_busy_retries(provider_settings, header):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx2.Response(429, headers={"Retry-After": header})

    reader = JsonReader(provider_settings, httpx2.MockTransport(respond), sleep=lambda _: None)
    with pytest.raises(ProviderError, match="retry_later") as caught:
        reader.get("https://example.com")
    assert len(calls) == 1 and caught.value.retry_after_seconds == 3600


def test_ashby_preserves_structured_country_and_secondary_locations(
    provider_settings, public_responses
):
    row = public_responses["ashby"]["jobs"][0]
    row["location"] = "Remote " + "x" * 220
    row["address"] = {"postalAddress": {"addressCountry": "AR"}}
    row["secondaryLocations"] = [{"location": "Buenos Aires", "address": {"addressCountry": "ARG"}}]
    provider = PublicBoardProvider("ashby", JsonReader(provider_settings))
    result = provider.normalize(row)
    assert len(result.location) == 200
    assert "Argentina" in result.location_details and "Buenos Aires" in result.location_details
    assert result.workplace_confirmed


def test_verified_boards_configuration(provider_settings):
    from app.discovery.configuration import configured_boards

    boards = configured_boards(provider_settings)
    assert {("greenhouse", "sezzle"), ("lever", "despegar"), ("ashby", "silver")} <= {
        (b.provider, b.board_token) for b in boards
    }


@pytest.fixture
def public_responses():
    greenhouse = {
        "id": 11,
        "title": "Junior Python Developer",
        "content": "&lt;p&gt;Python and SQL. 1 year of experience.&lt;/p&gt;",
        "location": {"name": "Home Based - Americas"},
        "absolute_url": "https://example.com/jobs/11",
        "first_published": "2026-01-01T00:00:00Z",
    }
    lever = {
        "id": "lever-11",
        "text": "QA Automation Junior",
        "descriptionPlain": "Python testing",
        "lists": [{"text": "Requirements", "content": "<li>SQL</li>"}],
        "categories": {"location": "Buenos Aires", "allLocations": ["Buenos Aires", "Montevideo"]},
        "workplaceType": "hybrid",
        "hostedUrl": "https://example.com/jobs/12",
        "applyUrl": "https://example.com/jobs/12/apply",
        "createdAt": 1767225600000,
    }
    ashby = {
        "title": "Data Analyst Junior",
        "location": "Argentina",
        "isListed": True,
        "isRemote": True,
        "descriptionPlain": "SQL and Python",
        "jobUrl": "https://example.com/company/ashby-11",
        "applyUrl": "https://example.com/company/ashby-11/apply",
        "publishedAt": "2026-01-01T00:00:00Z",
    }
    return {
        "greenhouse": {"jobs": [greenhouse], "meta": {"total": 1}},
        "lever": [lever],
        "ashby": {"jobs": [ashby]},
    }


@pytest.mark.parametrize("provider", ["greenhouse", "lever", "ashby"])
def test_normalize_public_boards(provider, public_responses, provider_settings):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx2.Response(200, json=public_responses[provider])

    reader = JsonReader(provider_settings, httpx2.MockTransport(respond), sleep=lambda _: None)
    jobs = PublicBoardProvider(provider, reader).fetch(
        BoardConfig(provider=provider, board_token="example", company="Example Labs")
    )
    assert len(jobs) == 1
    assert jobs[0].description and "<li>" not in jobs[0].description
    assert jobs[0].published_at.tzinfo is not None
    assert calls[0].method == "GET"
    assert calls[0].url.scheme == "https"
    assert "Authorization" not in calls[0].headers
    assert jobs[0].workplace_type == ("hybrid" if provider == "lever" else "remote")
    if provider == "ashby":
        assert jobs[0].external_id == "ashby-11"
    if provider == "greenhouse":
        assert calls[0].url.params["content"] == "true"


def test_lever_pagination_and_eu_host(public_responses, provider_settings):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx2.Response(
            200, json=public_responses["lever"] * 100 if request.url.params["skip"] == "0" else []
        )

    provider = PublicBoardProvider(
        "lever", JsonReader(provider_settings, httpx2.MockTransport(respond), sleep=lambda _: None)
    )
    jobs = provider.fetch(
        BoardConfig(provider="lever", board_token="example", company="Example Labs", region="eu")
    )
    assert len(jobs) == 1  # Same external reference deduplicated within a feed.
    assert len(requests) == 2 and requests[1].url.params["skip"] == "100"
    assert requests[0].url.host == "api.eu.lever.co"


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
def test_http_failures_are_bounded_and_safe(status, provider_settings):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx2.Response(status, text="private upstream body")

    reader = JsonReader(provider_settings, httpx2.MockTransport(respond), sleep=lambda _: None)
    with pytest.raises(ProviderError, match=f"http_{status}"):
        reader.get("https://example.com")
    assert len(requests) == (2 if status in {429, 500} else 1)


def test_retry_after_is_respected_and_not_capped_down(provider_settings):
    delays = []
    replies = iter(
        [httpx2.Response(429, headers={"Retry-After": "2"}), httpx2.Response(200, json=[])]
    )
    reader = JsonReader(
        provider_settings, httpx2.MockTransport(lambda _: next(replies)), sleep=delays.append
    )
    assert reader.get("https://example.com") == []
    assert 2 in delays
    reader = JsonReader(
        provider_settings,
        httpx2.MockTransport(lambda _: httpx2.Response(429, headers={"Retry-After": "120"})),
        sleep=lambda _: None,
    )
    with pytest.raises(ProviderError, match="http_429"):
        reader.get("https://example.com")


def test_timeout_and_invalid_json(provider_settings):
    def timeout(request):
        raise httpx2.ReadTimeout("private details", request=request)

    with pytest.raises(ProviderError, match="network_or_timeout"):
        JsonReader(provider_settings, httpx2.MockTransport(timeout), sleep=lambda _: None).get(
            "https://example.com"
        )
    with pytest.raises(ProviderError, match="invalid_json"):
        JsonReader(
            provider_settings,
            httpx2.MockTransport(lambda _: httpx2.Response(200, text="not json")),
            sleep=lambda _: None,
        ).get("https://example.com")


@pytest.mark.parametrize(
    "body", [{}, {"jobs": None}, {"jobs": [{"id": 1}]}, {"jobs": [], "meta": {"total": 1}}]
)
def test_invalid_snapshot_is_not_an_empty_success(body, provider_settings):
    provider = PublicBoardProvider(
        "greenhouse",
        JsonReader(
            provider_settings,
            httpx2.MockTransport(lambda _: httpx2.Response(200, json=body)),
            sleep=lambda _: None,
        ),
    )
    with pytest.raises(ProviderError):
        provider.fetch(
            BoardConfig(provider="greenhouse", board_token="example", company="Example Labs")
        )


def test_unlisted_ashby_jobs_excluded(public_responses, provider_settings):
    body = copy.deepcopy(public_responses["ashby"])
    body["jobs"][0]["isListed"] = False
    provider = PublicBoardProvider(
        "ashby",
        JsonReader(
            provider_settings,
            httpx2.MockTransport(lambda _: httpx2.Response(200, json=body)),
            sleep=lambda _: None,
        ),
    )
    assert (
        provider.fetch(BoardConfig(provider="ashby", board_token="example", company="Example Labs"))
        == []
    )


def test_plain_text_and_conservative_url_normalization():
    assert plain_text("&lt;p&gt;Python&lt;/p&gt;<script>secret()</script>") == "Python"
    assert (
        canonical_url("https://EXAMPLE.com/jobs/?utm_source=test&gh_jid=11#apply")
        == "https://example.com/jobs?gh_jid=11"
    )
    assert canonical_url("https://example.com/jobs?gh_jid=11") != canonical_url(
        "https://example.com/jobs?gh_jid=12"
    )


def test_requirements_are_explicit_and_ambiguous_experience_remains_unknown():
    assert detected_requirements("Python and SQL; 2+ years of experience") == (
        ["python", "sql"],
        2,
        True,
    )
    assert detected_requirements("Some experience with Python preferred") == (["python"], 0, False)
    assert detected_requirements("Experience with drag and draw tools") == ([], 0, False)


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("8+ years of software engineering experience", (8, True)),
        ("3+ years in fraud prevention or a closely related risk domain.", (3, True)),
        ("Requirements:\n- At least 4 years in a related engineering role.", (4, True)),
        ("Our team spent 3 years in a research partnership.", (0, False)),
    ],
)
def test_explicit_experience_phrases(description, expected):
    assert detected_requirements(description)[1:] == expected


@pytest.mark.parametrize("provider", ["greenhouse", "lever", "ashby"])
def test_explicit_talent_pool_is_not_imported_as_a_vacancy(
    provider, public_responses, provider_settings
):
    body = copy.deepcopy(public_responses[provider])
    row = body[0] if provider == "lever" else body["jobs"][0]
    row["text" if provider == "lever" else "title"] = "Example Talent Pool"
    adapter = PublicBoardProvider(
        provider,
        JsonReader(
            provider_settings,
            httpx2.MockTransport(lambda _: httpx2.Response(200, json=body)),
            sleep=lambda _: None,
        ),
    )
    assert (
        adapter.fetch(BoardConfig(provider=provider, board_token="example", company="Example Labs"))
        == []
    )


def test_senior_deprioritized_without_being_discarded():
    preferences = SearchInput()
    junior, level = priority(
        "Junior Python Developer", "Python SQL Docker", "Argentina", 1, True, preferences
    )
    senior, _ = priority(
        "Senior Python Developer", "Python SQL Docker", "Argentina", 8, True, preferences
    )
    ambiguous, _ = priority(
        "Python Developer", "Python SQL Docker", "Argentina", 0, False, preferences
    )
    assert level == "junior" and junior > ambiguous > senior > 0
