"""Measure public configured feeds. No DB, candidate data, scraping or submissions."""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.discovery.configuration import configured_boards
from app.discovery.providers import ProviderError, provider_for
from app.discovery.schemas import NormalizedJob
from app.services.opportunities import VERSION, assess


def metrics(jobs: list[NormalizedJob]) -> dict:
    counts = Counter(
        {
            key: 0
            for key in (
                "fetched",
                "explicit_argentina",
                "junior_explicit",
                "argentina_and_junior_explicit",
                "junior_inferred",
                "geography_unknown",
                "seniority_unknown",
                "published_unknown",
                "argentina_inferred",
                "geography_or_seniority_unknown",
                "experience_unknown",
            )
        }
    )
    categories = Counter()
    for job in jobs:
        result = assess(
            job.title,
            job.description,
            job.location_details or job.location,
            job.workplace_type,
        )
        ar = result["geography"]["status"] == "confirmed" and result["geography"][
            "value"
        ] in {"argentina", "international_argentina"}
        junior = (
            result["seniority"]["value"] == "junior"
            and result["seniority"]["status"] == "confirmed"
        )
        counts.update(
            {
                "fetched": 1,
                "explicit_argentina": int(ar),
                "junior_explicit": int(junior),
                "argentina_and_junior_explicit": int(ar and junior),
                "junior_inferred": int(
                    result["seniority"]["value"] == "junior" and not junior
                ),
                "geography_unknown": int(result["geography"]["status"] == "unknown"),
                "seniority_unknown": int(result["seniority"]["status"] == "unknown"),
                "published_unknown": int(job.published_at is None),
                "argentina_inferred": int(
                    result["country"] == "AR"
                    and result["geography"]["status"] == "inferred"
                ),
                "geography_or_seniority_unknown": int(
                    result["geography"]["status"] == "unknown"
                    or result["seniority"]["status"] == "unknown"
                ),
                "experience_unknown": int(result["experience"]["status"] == "unknown"),
            }
        )
        categories[result["category"]] += 1
    return dict(counts) | {"categories": dict(categories)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshots",
        type=Path,
        help="Recompute from previously saved normalized feeds without HTTP",
    )
    parser.add_argument(
        "--output", type=Path, default=Path(".local/sprint3a-metrics.json")
    )
    parser.add_argument(
        "--save-snapshots",
        type=Path,
        help="Save normalized public jobs locally for offline reproduction",
    )
    args = parser.parse_args()
    settings = get_settings()
    results = []
    for board in configured_boards(settings):
        if not board.enabled:
            continue
        item = {
            "provider": board.provider,
            "board": board.board_token,
            "company": board.company,
        }
        try:
            if args.snapshots:
                jobs = [
                    NormalizedJob.model_validate(j)
                    for j in json.loads(
                        (
                            args.snapshots / f"{board.board_token}-sprint3a.json"
                        ).read_text(encoding="utf-8")
                    )
                ]
            else:
                jobs = provider_for(board.provider, settings).fetch(board)
                if args.save_snapshots:
                    args.save_snapshots.mkdir(parents=True, exist_ok=True)
                    (
                        args.save_snapshots / f"{board.board_token}-sprint3a.json"
                    ).write_text(
                        json.dumps([j.model_dump(mode="json") for j in jobs]),
                        encoding="utf-8",
                    )
            item.update(metrics(jobs))
            item["status"] = "success"
        except ProviderError as error:
            item.update(status="error", error=str(error))
        except (OSError, ValueError):
            item.update(status="error", error="missing_or_invalid_snapshot")
        results.append(item)
    totals = Counter()
    for item in results:
        totals.update(
            {key: value for key, value in item.items() if isinstance(value, int)}
        )
    report = {
        "measured_at": datetime.now(UTC).isoformat(),
        "mode": "offline_reclassification" if args.snapshots else "live_public_api",
        "classification_version": VERSION,
        "note": "Posting records before cross-source deduplication. Explicit junior includes non-IT roles. Unknown is never compatible.",
        "sources": results,
        "totals": dict(totals),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=True))
    return int(any(item["status"] == "error" for item in results))


if __name__ == "__main__":
    raise SystemExit(main())
