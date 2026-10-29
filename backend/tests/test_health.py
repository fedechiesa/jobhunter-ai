from sqlalchemy.exc import OperationalError

from app.db import get_session


def test_liveness_without_database(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_database_unavailable_is_sanitized(application, client):
    class BrokenSession:
        def execute(self, _statement):
            raise OperationalError("private connection string", {}, Exception("secret"))

    application.dependency_overrides[get_session] = lambda: BrokenSession()
    response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_cors_allows_local_frontend(client):
    response = client.options(
        "/jobs",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin(client):
    response = client.options(
        "/jobs", headers={"Origin": "https://example.com", "Access-Control-Request-Method": "POST"}
    )
    assert response.status_code == 400
