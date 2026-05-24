from fastapi.testclient import TestClient

from idea_forge.app import create_app
from idea_forge.database import (
    DEFAULT_CREATIVE_TECHNIQUES,
    DEFAULT_IDEA_AGENTS,
    DEFAULT_PORTFOLIOS,
)


def test_home_page_renders_navigation() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Idea Forge" in response.text
    assert 'href="/ideas"' in response.text
    assert 'href="/ideas/generate"' in response.text


def test_list_ideas_page_renders_empty_state_without_database() -> None:
    client = TestClient(create_app(database_path=":memory:"))

    response = client.get("/ideas")

    assert response.status_code == 200
    assert "No ideas have been generated or stored yet." in response.text


def test_generate_idea_form_shell_renders_reference_options() -> None:
    client = TestClient(create_app(database_path=":memory:"))

    response = client.get("/ideas/generate")

    assert response.status_code == 200
    assert '<textarea name="seed_text"' in response.text
    assert 'select name="portfolio_id"' in response.text
    assert 'select name="idea_agent_id"' in response.text
    assert 'select name="creative_technique_id"' in response.text
    assert DEFAULT_PORTFOLIOS[0][0] in response.text
    assert DEFAULT_IDEA_AGENTS[0][0] in response.text
    assert DEFAULT_CREATIVE_TECHNIQUES[0][0] in response.text
    assert "Generate ideas" in response.text
