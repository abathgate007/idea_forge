"""Manual memory summary persistence."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class MemoryRecord:
    """Stored manual memory summary."""

    id: int
    memory_type: str
    title: str
    content: str


def create_memory(
    connection: sqlite3.Connection,
    *,
    memory_type: str,
    title: str,
    content: str,
) -> MemoryRecord:
    """Create a manual memory summary record."""
    clean_type = memory_type.strip()
    clean_title = title.strip()
    clean_content = content.strip()
    if not clean_type:
        raise ValueError("Memory type is required.")
    if not clean_title:
        raise ValueError("Memory title is required.")
    if not clean_content:
        raise ValueError("Memory content is required.")

    cursor = connection.execute(
        """
        INSERT INTO memories (memory_type, title, content)
        VALUES (?, ?, ?)
        """,
        (clean_type, clean_title, clean_content),
    )
    connection.commit()
    return MemoryRecord(
        id=int(cursor.lastrowid),
        memory_type=clean_type,
        title=clean_title,
        content=clean_content,
    )


def list_memories(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return manual memory summaries newest first."""
    return connection.execute(
        """
        SELECT id, memory_type, title, content, created_at
        FROM memories
        ORDER BY id DESC
        """
    ).fetchall()
