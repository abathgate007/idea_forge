import json

import pytest

from idea_forge.database import initialize_database, open_database
from idea_forge.feedback import record_feedback


def insert_idea(connection) -> int:
    cursor = connection.execute(
        "INSERT INTO ideas (title, body) VALUES (?, ?)",
        ("Feedback test idea", "A stored idea that can receive feedback."),
    )
    connection.commit()
    return int(cursor.lastrowid)


def test_feedback_can_be_recorded_for_an_idea() -> None:
    with open_database() as connection:
        initialize_database(connection)
        idea_id = insert_idea(connection)

        event = record_feedback(
            connection,
            idea_id=idea_id,
            action="thumbs_up",
        )

        row = connection.execute("SELECT * FROM feedback_events").fetchone()

    assert event.idea_id == idea_id
    assert event.action == "thumbs_up"
    assert row["idea_id"] == idea_id
    assert row["action"] == "thumbs_up"


def test_feedback_records_link_to_the_correct_idea() -> None:
    with open_database() as connection:
        initialize_database(connection)
        first_idea_id = insert_idea(connection)
        second_idea_id = insert_idea(connection)

        record_feedback(connection, idea_id=second_idea_id, action="star")

        row = connection.execute("SELECT idea_id, action FROM feedback_events").fetchone()

    assert row["idea_id"] == second_idea_id
    assert row["idea_id"] != first_idea_id
    assert row["action"] == "star"


def test_reason_chips_can_be_stored() -> None:
    with open_database() as connection:
        initialize_database(connection)
        idea_id = insert_idea(connection)

        event = record_feedback(
            connection,
            idea_id=idea_id,
            action="test_this",
            reason_chips=("interesting", "weekend MVP"),
        )

        row = connection.execute("SELECT reason_chips FROM feedback_events").fetchone()

    assert event.reason_chips == ("interesting", "weekend MVP")
    assert json.loads(row["reason_chips"]) == ["interesting", "weekend MVP"]


def test_invalid_feedback_action_is_rejected_clearly() -> None:
    with open_database() as connection:
        initialize_database(connection)
        idea_id = insert_idea(connection)

        with pytest.raises(ValueError, match="Unsupported feedback action: save_forever"):
            record_feedback(connection, idea_id=idea_id, action="save_forever")
