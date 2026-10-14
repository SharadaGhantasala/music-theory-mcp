import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine
from sqlalchemy.orm import Mapped, Session, mapped_column

from server.store.db import Base


class _ArtifactRow(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(primary_key=True)
    kind: Mapped[str]
    content: Mapped[str]
    events: Mapped[str]
    created_at: Mapped[datetime]


@dataclass(frozen=True)
class StoredArtifact:
    """A saved score: its rendered `content` and the `events` (notes and chords) it shows."""

    id: str
    kind: str
    content: str
    events: list[list[str]]


class ArtifactStore:
    """Keeps rendered scores so the UI can fetch them and later tools can build on them."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, kind: str, content: str, events: list[list[str]]) -> str:
        """Save a score and return the id it can be fetched by."""
        artifact_id = uuid.uuid4().hex[:12]
        with Session(self._engine) as session:
            session.add(
                _ArtifactRow(
                    id=artifact_id,
                    kind=kind,
                    content=content,
                    events=json.dumps(events),
                    created_at=datetime.now(UTC),
                )
            )
            session.commit()
        return artifact_id

    def get(self, artifact_id: str) -> StoredArtifact | None:
        """Return the score saved under `artifact_id`, or None if there is none."""
        with Session(self._engine) as session:
            row = session.get(_ArtifactRow, artifact_id)
            if row is None:
                return None
            return StoredArtifact(
                id=row.id, kind=row.kind, content=row.content, events=json.loads(row.events)
            )
