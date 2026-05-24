"""Human feedback persistence for stored ideas."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3


FEEDBACK_ACTIONS = (
    "thumbs_up",
    "thumbs_down",
    "star",
    "reject",
    "duplicate",
    "test_this",
    "expand",
    "more_like_this",
)

REASON_CHIPS = (
    "too generic",
    "too hard",
    "too expensive",
    "boring",
    "interesting",
    "good fit",
    "could make money",
    "bad lifestyle fit",
    "good for Vlatka",
    "good for AppSec",
    "good book idea",
    "weekend MVP",
    "needs research",
    "low maintenance",
    "high burden",
)


@dataclass(frozen=True)
class FeedbackEvent:
    """Stored feedback event."""

    id: int
    idea_id: int
    action: str
    reason_chips: tuple[str, ...]


def record_feedback(
    connection: sqlite3.Connection,
    *,
    idea_id: int,
    action: str,
    reason_chips: tuple[str, ...] | list[str] = (),
) -> FeedbackEvent:
    """Persist one human feedback event for a stored idea."""
    if action not in FEEDBACK_ACTIONS:
        raise ValueError(f"Unsupported feedback action: {action}")

    if not _idea_exists(connection, idea_id):
        raise ValueError(f"Unknown idea id: {idea_id}")

    clean_reasons = tuple(reason.strip() for reason in reason_chips if reason.strip())
    invalid_reasons = [reason for reason in clean_reasons if reason not in REASON_CHIPS]
    if invalid_reasons:
        raise ValueError(f"Unsupported feedback reason: {invalid_reasons[0]}")

    cursor = connection.execute(
        """
        INSERT INTO feedback_events (idea_id, action, reason_chips)
        VALUES (?, ?, ?)
        """,
        (idea_id, action, json.dumps(list(clean_reasons))),
    )
    connection.commit()

    return FeedbackEvent(
        id=int(cursor.lastrowid),
        idea_id=idea_id,
        action=action,
        reason_chips=clean_reasons,
    )


def feedback_events_by_idea(connection: sqlite3.Connection) -> dict[int, list[sqlite3.Row]]:
    """Return stored feedback events grouped by idea id."""
    rows = connection.execute(
        """
        SELECT id, idea_id, action, reason_chips, created_at
        FROM feedback_events
        ORDER BY id DESC
        """
    ).fetchall()
    events: dict[int, list[sqlite3.Row]] = {}
    for row in rows:
        events.setdefault(int(row["idea_id"]), []).append(row)

    return events


def decode_reason_chips(row: sqlite3.Row) -> tuple[str, ...]:
    """Decode reason chips stored on a feedback row."""
    try:
        values = json.loads(row["reason_chips"])
    except json.JSONDecodeError:
        return ()

    if not isinstance(values, list):
        return ()

    return tuple(value for value in values if isinstance(value, str))


def _idea_exists(connection: sqlite3.Connection, idea_id: int) -> bool:
    row = connection.execute("SELECT 1 FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    return row is not None
