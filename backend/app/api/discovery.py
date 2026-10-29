from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_engine, get_session
from app.discovery.configuration import ensure_sources, search_preferences
from app.discovery.normalization import priority
from app.discovery.schemas import SearchInput, SourceRead, SourceUpdate, SyncRead
from app.discovery.sync import SyncBusy, is_running, synchronize
from app.models import JobPosting, JobSource, SearchPreferences, SyncRun

router = APIRouter(tags=["discovery"])
Database = Annotated[Session, Depends(get_session)]
Configuration = Annotated[Settings, Depends(get_settings)]
SyncEngine = Annotated[Engine, Depends(get_engine)]


@router.get("/sources", response_model=list[SourceRead])
def get_sources(session: Database, settings: Configuration):
    try:
        sources = ensure_sources(session, settings)
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    session.commit()
    return sources


@router.patch("/sources/{source_id}", response_model=SourceRead)
def update_source(source_id: int, payload: SourceUpdate, session: Database):
    source = session.get(JobSource, source_id)
    if source is None or source.kind == "manual":
        raise HTTPException(status_code=404, detail="Discovery source not found")
    source.enabled = payload.enabled
    session.commit()
    session.refresh(source)
    return source


@router.get("/search-preferences", response_model=SearchInput)
def get_search_preferences(session: Database):
    return search_preferences(session)


@router.put("/search-preferences", response_model=SearchInput)
def update_search_preferences(payload: SearchInput, session: Database):
    stored = session.get(SearchPreferences, 1)
    if stored is None:
        session.add(SearchPreferences(id=1, **payload.model_dump()))
    else:
        for key, value in payload.model_dump().items():
            setattr(stored, key, value)
    for job in session.scalars(select(JobPosting)):
        job.search_priority, job.seniority = priority(
            job.title,
            job.description,
            job.location,
            job.experience_years,
            job.experience_years_known,
            payload,
        )
    session.commit()
    return payload


@router.get("/sync/status")
def get_sync_status(session: Database, engine: SyncEngine):
    latest = session.scalar(select(SyncRun).order_by(SyncRun.id.desc()).limit(1))
    return {
        "running": is_running(engine),
        "latest": SyncRead.model_validate(latest) if latest else None,
    }


@router.post("/sync", response_model=SyncRead)
def manual_sync(engine: SyncEngine, settings: Configuration):
    try:
        return synchronize(engine, settings)
    except SyncBusy:
        raise HTTPException(status_code=409, detail="Synchronization already running") from None
    except ValueError:
        raise HTTPException(status_code=503, detail="Invalid discovery configuration") from None
