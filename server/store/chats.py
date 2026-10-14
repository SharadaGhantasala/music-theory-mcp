import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from server.store.db import Base


class _MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(index=True)
    role: Mapped[str]
    content: Mapped[str]
    created_at: Mapped[datetime]


class ChatStore:
    """Keeps each chat's messages, exactly as they are sent to Claude, so follow-ups work."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def load(self, session_id: str) -> list[dict[str, Any]]:
        """Return the chat's messages in order, oldest first."""
        with Session(self._engine) as session:
            rows = session.scalars(
                select(_MessageRow)
                .where(_MessageRow.session_id == session_id)
                .order_by(_MessageRow.id)
            )
            return [{"role": row.role, "content": json.loads(row.content)} for row in rows]

    def append(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        """Add messages to the end of the chat. Earlier messages are never changed."""
        with Session(self._engine) as session:
            for message in messages:
                session.add(
                    _MessageRow(
                        session_id=session_id,
                        role=message["role"],
                        content=json.dumps(message["content"]),
                        created_at=datetime.now(UTC),
                    )
                )
            session.commit()
