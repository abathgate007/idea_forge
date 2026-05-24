from fastapi.testclient import TestClient

from idea_forge.app import create_app
from idea_forge.database import open_database


class FakeOllamaClient:
    model = "fake-ui-model"

    def __init__(self) -> None:
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "1. Stored UI idea"


def first_id(database_path, table_name: str) -> int:
    with open_database(database_path) as connection:
        return connection.execute(
            f"SELECT id FROM {table_name} ORDER BY id LIMIT 1"
        ).fetchone()["id"]


def generation_run_count(database_path) -> int:
    with open_database(database_path) as connection:
        return connection.execute("SELECT COUNT(*) FROM generation_runs").fetchone()[0]


def test_generate_form_route_exists(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    client = TestClient(create_app(database_path=database_path))

    response = client.get("/ideas/generate")

    assert response.status_code == 200
    assert '<form method="post" action="/ideas/generate">' in response.text
    assert 'textarea name="seed_text"' in response.text
    assert 'select name="portfolio_id"' in response.text
    assert 'select name="idea_agent_id"' in response.text
    assert 'select name="creative_technique_id"' in response.text
    assert "Generate ideas" in response.text


def test_submitting_generate_form_uses_fake_client_and_stores_result(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    fake_client = FakeOllamaClient()
    test_client = TestClient(
        create_app(database_path=database_path, ollama_client=fake_client)
    )
    test_client.get("/ideas/generate")

    response = test_client.post(
        "/ideas/generate",
        data={
            "seed_text": "Manual generation through the local UI",
            "portfolio_id": first_id(database_path, "portfolios"),
            "idea_agent_id": first_id(database_path, "idea_agents"),
            "creative_technique_id": first_id(database_path, "creative_techniques"),
        },
    )

    assert response.status_code == 200
    assert "Stored UI idea" in response.text
    assert fake_client.prompts
    assert "Manual generation through the local UI" in fake_client.prompts[0]

    with open_database(database_path) as connection:
        idea = connection.execute("SELECT body FROM ideas").fetchone()
        run = connection.execute(
            "SELECT status, model_name, raw_output FROM generation_runs"
        ).fetchone()

    assert idea["body"] == "Stored UI idea"
    assert run["status"] == "completed"
    assert run["model_name"] == "fake-ui-model"
    assert run["raw_output"] == "1. Stored UI idea"
    assert generation_run_count(database_path) == 1
