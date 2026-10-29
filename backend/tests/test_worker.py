import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app import worker
from app.discovery.sync import SyncBusy, log_event


@pytest.fixture
def worker_env(monkeypatch):
    engine = Mock()
    synchronize = Mock(return_value=SimpleNamespace(status="success"))
    monkeypatch.setattr(worker, "get_engine", lambda: engine)
    monkeypatch.setattr(worker, "get_settings", lambda: SimpleNamespace(sync_interval_seconds=3600))
    monkeypatch.setattr(worker, "synchronize", synchronize)
    monkeypatch.setattr(worker.signal, "signal", lambda *_: None)
    return engine, synchronize


def test_worker_once(worker_env, monkeypatch):
    engine, sync = worker_env
    monkeypatch.setattr("sys.argv", ["worker", "--once"])
    assert worker.main() == 0
    sync.assert_called_once()
    engine.dispose.assert_called_once()


def test_periodic_worker_uses_configured_interval(worker_env, monkeypatch):
    engine, sync = worker_env

    class FakeEvent:
        stopped = False
        delays = []

        def is_set(self):
            return self.stopped

        def set(self):
            self.stopped = True

        def wait(self, seconds):
            self.delays.append(seconds)
            if len(self.delays) == 2:
                self.stopped = True

    stop = FakeEvent()
    monkeypatch.setattr(worker, "Event", lambda: stop)
    monkeypatch.setattr("sys.argv", ["worker", "--interval-seconds", "60"])
    assert worker.main() == 0
    assert sync.call_count == 2 and stop.delays == [60, 60]


def test_worker_busy_and_partial_results(worker_env, monkeypatch):
    engine, sync = worker_env
    monkeypatch.setattr("sys.argv", ["worker", "--once"])
    sync.side_effect = SyncBusy()
    assert worker.main() == 0
    sync.side_effect = None
    sync.return_value = SimpleNamespace(status="partial")
    assert worker.main() == 1


def test_worker_rejects_zero_interval(worker_env, monkeypatch):
    monkeypatch.setattr("sys.argv", ["worker", "--interval-seconds", "0"])
    with pytest.raises(SystemExit):
        worker.main()


def test_logs_are_structured(caplog):
    with caplog.at_level("INFO", logger="jobhunter.discovery"):
        log_event("source_finished", provider="greenhouse", new=2)
    event = json.loads(caplog.records[-1].message)
    assert event["event"] == "source_finished" and event["new"] == 2 and event["timestamp"]
