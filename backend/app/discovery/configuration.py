import json

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.discovery.schemas import BoardConfig, SearchInput
from app.models import JobSource, SearchPreferences


def configured_boards(settings: Settings) -> list[BoardConfig]:
    try:
        boards = TypeAdapter(list[BoardConfig]).validate_python(
            json.loads(settings.sources_file.read_text(encoding="utf-8"))
        )
        keys = {(board.provider, board.board_token, board.region) for board in boards}
        if len(boards) > 20 or len(keys) != len(boards):
            raise ValueError("Invalid source count or repeated boards")
        return boards
    except (OSError, ValueError, ValidationError):
        raise ValueError("Invalid sources configuration; check SOURCES_FILE") from None


def ensure_sources(session: Session, settings: Settings) -> list[JobSource]:
    boards = configured_boards(settings)
    for board in boards:
        statement = insert(JobSource).values(
            name=f"{board.company} ({board.provider}/{board.board_token}/{board.region})",
            company_name=board.company,
            kind=board.provider,
            board_token=board.board_token,
            region=board.region,
            enabled=board.enabled,
        )
        session.execute(
            statement.on_conflict_do_update(
                index_elements=["kind", "board_token", "region"],
                set_={
                    "name": statement.excluded.name,
                    "company_name": statement.excluded.company_name,
                },
            )
        )
    # Only boards still present in the file are eligible; history is retained for removed boards.
    keys = {(board.provider, board.board_token, board.region) for board in boards}
    disabled = {
        (board.provider, board.board_token, board.region) for board in boards if not board.enabled
    }
    sources = list(
        session.scalars(select(JobSource).where(JobSource.kind != "manual").order_by(JobSource.id))
    )
    for source in sources:
        if (source.kind, source.board_token, source.region) not in keys or (
            source.kind,
            source.board_token,
            source.region,
        ) in disabled:
            source.enabled = False
    return sources


def search_preferences(session: Session) -> SearchInput:
    stored = session.get(SearchPreferences, 1)
    return SearchInput.model_validate(stored, from_attributes=True) if stored else SearchInput()
