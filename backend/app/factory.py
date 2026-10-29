from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import discovery, health, jobs, profile
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    application = FastAPI(title="JobHunter AI", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(SQLAlchemyError)
    async def database_error(_request: Request, _error: SQLAlchemyError) -> JSONResponse:
        # Avoid returning connection strings, SQL statements or submitted data.
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    application.include_router(health.router)
    application.include_router(jobs.router)
    application.include_router(profile.router)
    application.include_router(discovery.router)
    return application
