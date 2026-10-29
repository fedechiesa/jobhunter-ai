import json
import time
from collections.abc import Callable
from typing import Protocol

import httpx2
from pydantic import ValidationError

from app.core.config import Settings
from app.discovery.normalization import is_talent_pool, modality, plain_text, publication_date
from app.discovery.schemas import BoardConfig, NormalizedJob


class ProviderError(Exception):
    """Safe error code; never includes response bodies or connection details."""


class JobProvider(Protocol):
    def fetch(self, board: BoardConfig) -> list[NormalizedJob]: ...


class JsonReader:
    def __init__(self, settings: Settings, transport=None, sleep: Callable = time.sleep):
        self.settings = settings
        self.transport = transport
        self.sleep = sleep

    def get(self, url: str, params: dict | None = None):
        for attempt in range(self.settings.provider_max_attempts):
            self.sleep(self.settings.provider_request_delay_seconds)
            try:
                with httpx2.Client(
                    timeout=self.settings.provider_timeout_seconds,
                    transport=self.transport,
                    follow_redirects=False,
                ) as client:
                    response = client.get(
                        url,
                        params=params,
                        headers={
                            "Accept": "application/json",
                            "User-Agent": "JobHunterAI/0.2 (public job-board reader)",
                        },
                    )
            except httpx2.TransportError:
                if attempt + 1 == self.settings.provider_max_attempts:
                    raise ProviderError("network_or_timeout") from None
                self.sleep(2**attempt)
                continue
            if response.status_code in {429, 500, 502, 503, 504}:
                retry_after = response.headers.get("Retry-After", "")
                try:
                    delay = float(retry_after) if retry_after else 2**attempt
                except ValueError:
                    # An HTTP-date must not be ignored; defer to the next scheduled run.
                    raise ProviderError("retry_later") from None
                if delay > 10 or attempt + 1 == self.settings.provider_max_attempts:
                    raise ProviderError(f"http_{response.status_code}")
                self.sleep(max(delay, 0))
                continue
            if response.status_code != 200:
                raise ProviderError(f"http_{response.status_code}")
            if len(response.content) > 10_000_000:
                raise ProviderError("response_too_large")
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError):
                raise ProviderError("invalid_json") from None
        raise ProviderError("retry_exhausted")


class PublicBoardProvider:
    def __init__(self, provider: str, reader: JsonReader):
        self.provider = provider
        self.reader = reader

    def fetch(self, board: BoardConfig) -> list[NormalizedJob]:
        if board.region == "eu" and self.provider != "lever":
            raise ProviderError("unsupported_region")
        try:
            if self.provider == "greenhouse":
                body = self.reader.get(
                    f"https://boards-api.greenhouse.io/v1/boards/{board.board_token}/jobs",
                    {"content": "true"},
                )
                rows = body["jobs"]
                if not isinstance(rows, list) or body.get("meta", {}).get(
                    "total", len(rows)
                ) != len(rows):
                    raise ProviderError("incomplete_response")
            elif self.provider == "ashby":
                body = self.reader.get(
                    f"https://api.ashbyhq.com/posting-api/job-board/{board.board_token}"
                )
                rows = body["jobs"]
            else:
                rows = []
                host = "api.eu.lever.co" if board.region == "eu" else "api.lever.co"
                for page in range(20):
                    batch = self.reader.get(
                        f"https://{host}/v0/postings/{board.board_token}",
                        {"mode": "json", "skip": page * 100, "limit": 100},
                    )
                    if not isinstance(batch, list):
                        raise ProviderError("invalid_response")
                    rows.extend(batch)
                    if len(batch) < 100:
                        break
                else:
                    raise ProviderError("pagination_limit")
            if not isinstance(rows, list):
                raise ProviderError("invalid_response")
            normalized = {}
            for row in rows:
                title = row.get("text" if self.provider == "lever" else "title", "")
                if is_talent_pool(title):
                    continue
                if self.provider == "ashby" and row.get("isListed") is False:
                    continue
                if self.provider == "greenhouse" and row.get("internal_job_id", True) is None:
                    continue  # Prospect/talent-pool sections are not an open job.
                job = self.normalize(row)
                normalized[job.external_id] = job
            return list(normalized.values())
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError, ValidationError):
            raise ProviderError("invalid_response") from None

    def normalize(self, row: dict) -> NormalizedJob:
        if self.provider != "ashby" and row.get("id") is None:
            raise ValueError("Missing external reference")
        if self.provider == "greenhouse":
            location = row["location"]["name"]
            return NormalizedJob(
                external_id=str(row["id"]),
                title=row["title"],
                description=plain_text(row["content"]),
                location=location[:200],
                workplace_type=modality(None, location),
                url=row["absolute_url"],
                apply_url=row["absolute_url"],
                published_at=publication_date(row.get("first_published")),
            )
        if self.provider == "lever":
            location = " / ".join(
                row.get("categories", {}).get("allLocations")
                or [row.get("categories", {}).get("location", "")]
            )
            description = row.get("descriptionPlain") or plain_text(row.get("description", ""))
            sections = [
                plain_text(item["text"] + "\n" + item["content"]) for item in row.get("lists", [])
            ]
            description = "\n".join([description, *sections, row.get("additionalPlain", "")])
            return NormalizedJob(
                external_id=row["id"],
                title=row["text"],
                description=description,
                location=location[:200],
                workplace_type=modality(row.get("workplaceType"), location),
                url=row["hostedUrl"],
                apply_url=row["applyUrl"],
                published_at=publication_date(row.get("createdAt")),
            )
        location = " / ".join(
            [row["location"], *[item["location"] for item in row.get("secondaryLocations", [])]]
        )
        original = row["jobUrl"]
        # Ashby's documented feed may omit id. The stable hosted URL is then the external reference.
        return NormalizedJob(
            external_id=str(row.get("id") or original.rstrip("/").rsplit("/", 1)[-1]),
            title=row["title"],
            description=row.get("descriptionPlain") or plain_text(row["descriptionHtml"]),
            location=location[:200],
            workplace_type=modality(
                row.get("workplaceType") or ("remote" if row.get("isRemote") else None), location
            ),
            url=original,
            apply_url=row["applyUrl"],
            published_at=publication_date(row.get("publishedAt")),
        )


def provider_for(provider: str, settings: Settings) -> JobProvider:
    if provider not in {"greenhouse", "lever", "ashby"}:
        raise ProviderError("unsupported_provider")
    return PublicBoardProvider(provider, JsonReader(settings))
