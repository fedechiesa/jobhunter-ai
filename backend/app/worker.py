"""Standalone periodic discovery. No dependency on uvicorn or development reload."""

import argparse
import logging
import signal
from threading import Event

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db import get_engine
from app.discovery.sync import SyncBusy, log_event, synchronize


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval-seconds", type=int)
    args = parser.parse_args()
    settings = get_settings()
    interval = (
        args.interval_seconds
        if args.interval_seconds is not None
        else settings.sync_interval_seconds
    )
    if interval < 60:
        parser.error("Interval must be at least 60 seconds")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    stop = Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    engine = get_engine()
    try:
        while not stop.is_set():
            code = 0
            try:
                result = synchronize(engine, settings)
                code = 1 if result.status in {"failed", "partial"} else 0
            except SyncBusy:
                log_event("sync_skipped", reason="already_running")
            except (SQLAlchemyError, ValueError):
                log_event("worker_error", error="database_or_configuration_error")
                code = 1
            if args.once:
                return code
            stop.wait(interval)
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
