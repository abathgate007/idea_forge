from fastapi.testclient import TestClient

from idea_forge.app import create_app
from idea_forge.database import open_database


def test_memories_page_renders_create_form(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/memories")

    assert response.status_code == 200
    assert '<form method="post" action="/memories">' in response.text
    assert 'name="memory_type"' in response.text
    assert 'name="title"' in response.text
    assert 'name="content"' in response.text
    assert "No memory summaries have been created yet." in response.text


def test_memory_ui_route_creates_and_lists_memory(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    client = TestClient(create_app(database_path=database_path))

    response = client.post(
        "/memories",
        data={
            "memory_type": "domain summary",
            "title": "AppSec buyer memory",
            "content": "Narrow validation offers are more useful than vague platforms.",
        },
    )

    assert response.status_code == 200
    assert "AppSec buyer memory" in response.text
    assert "domain summary" in response.text
    assert "Narrow validation offers" in response.text

    with open_database(database_path) as connection:
        row = connection.execute(
            "SELECT memory_type, title, content FROM memories"
        ).fetchone()

    assert row["memory_type"] == "domain summary"
    assert row["title"] == "AppSec buyer memory"
    assert "vague platforms" in row["content"]
