from fastapi.testclient import TestClient
import json

from idea_forge.app import create_app
from idea_forge.database import open_database


class FakeOllamaClient:
    model = "fake-ui-model"

    def __init__(self) -> None:
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(
            {
                "ideas": [
                    {
                        "title": "Stored UI idea",
                        "summary": "A structured idea shown from the generate response.",
                        "target_buyer": "Local operators",
                        "first_validation_step": "Ask three operators if they want it.",
                        "why_it_fits": "It matches the selected seed and portfolio.",
                    }
                ]
            }
        )


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
    assert "A structured idea shown from the generate response." in response.text
    assert "Target buyer" in response.text
    assert "Local operators" in response.text
    assert "First validation step" in response.text
    assert "Why it fits" in response.text
    assert fake_client.prompts
    assert "Manual generation through the local UI" in fake_client.prompts[0]

    with open_database(database_path) as connection:
        idea = connection.execute(
            """
            SELECT title, summary, target_buyer, first_validation_step, why_it_fits
            FROM ideas
            """
        ).fetchone()
        run = connection.execute(
            "SELECT status, model_name, raw_output FROM generation_runs"
        ).fetchone()

    assert idea["title"] == "Stored UI idea"
    assert idea["summary"] == "A structured idea shown from the generate response."
    assert idea["target_buyer"] == "Local operators"
    assert idea["first_validation_step"] == "Ask three operators if they want it."
    assert idea["why_it_fits"] == "It matches the selected seed and portfolio."
    assert run["status"] == "completed"
    assert run["model_name"] == "fake-ui-model"
    assert "Stored UI idea" in run["raw_output"]
    assert generation_run_count(database_path) == 1
