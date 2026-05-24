from fastapi.testclient import TestClient

from idea_forge.app import create_app
from idea_forge.database import initialize_database, open_database


def setup_idea(database_path) -> int:
    with open_database(database_path) as connection:
        initialize_database(connection)
        cursor = connection.execute(
            "INSERT INTO ideas (title, body) VALUES (?, ?)",
            ("UI feedback idea", "A stored idea shown on the UI."),
        )
        connection.commit()
        return int(cursor.lastrowid)


def test_ideas_page_renders_feedback_controls(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    idea_id = setup_idea(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/ideas")

    assert response.status_code == 200
    assert f'action="/ideas/{idea_id}/feedback"' in response.text
    assert 'name="action" value="thumbs_up"' in response.text
    assert 'name="action" value="more_like_this"' in response.text
    assert 'name="reason_chips" value="too generic"' in response.text
    assert 'name="reason_chips" value="good for AppSec"' in response.text


def test_feedback_ui_route_records_action_and_reason_chips(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    idea_id = setup_idea(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.post(
        f"/ideas/{idea_id}/feedback",
        data={
            "action": "more_like_this",
            "reason_chips": ["interesting", "good fit"],
        },
    )

    assert response.status_code == 200
    assert "more like this" in response.text
    assert "interesting, good fit" in response.text

    with open_database(database_path) as connection:
        feedback = connection.execute(
            "SELECT idea_id, action, reason_chips FROM feedback_events"
        ).fetchone()

    assert feedback["idea_id"] == idea_id
    assert feedback["action"] == "more_like_this"
    assert "interesting" in feedback["reason_chips"]
    assert "good fit" in feedback["reason_chips"]


def test_feedback_ui_route_rejects_invalid_action(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    idea_id = setup_idea(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.post(
        f"/ideas/{idea_id}/feedback",
        data={"action": "save_forever"},
    )

    assert response.status_code == 400
    assert "Unsupported feedback action: save_forever" in response.text
