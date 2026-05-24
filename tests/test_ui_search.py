from fastapi.testclient import TestClient

from idea_forge.app import create_app
from idea_forge.database import initialize_database, open_database
from idea_forge.feedback import record_feedback


def setup_search_ideas(database_path) -> tuple[int, int]:
    with open_database(database_path) as connection:
        initialize_database(connection)
        portfolio_id = connection.execute(
            "SELECT id FROM portfolios WHERE name = ?",
            ("Cybersecurity and AppSec",),
        ).fetchone()["id"]
        cursor = connection.execute(
            """
            INSERT INTO ideas (title, summary, body, portfolio_id)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Threat modeling workshop",
                "A focused AppSec validation offer.",
                "A focused AppSec validation offer.",
                portfolio_id,
            ),
        )
        matching_id = int(cursor.lastrowid)
        cursor = connection.execute(
            "INSERT INTO ideas (title, summary, body) VALUES (?, ?, ?)",
            (
                "Neighborhood content engine",
                "A real estate writing workflow.",
                "A real estate writing workflow.",
            ),
        )
        other_id = int(cursor.lastrowid)
        record_feedback(connection, idea_id=matching_id, action="test_this")
        return matching_id, other_id


def test_ideas_page_renders_search_form(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    setup_search_ideas(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/ideas")

    assert response.status_code == 200
    assert 'method="get" action="/ideas"' in response.text
    assert 'name="q"' in response.text
    assert 'name="portfolio_id"' in response.text
    assert 'name="feedback_action"' in response.text


def test_ideas_page_filters_results_by_keyword_and_feedback(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    setup_search_ideas(database_path)
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/ideas?q=threat&feedback_action=test_this")

    assert response.status_code == 200
    assert "Threat modeling workshop" in response.text
    assert "Neighborhood content engine" not in response.text
