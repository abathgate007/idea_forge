from fastapi.testclient import TestClient

from idea_forge.app import create_app
from idea_forge.database import initialize_database, open_database
from idea_forge.idea_generation import generate_and_store_ideas


class FakeOllamaClient:
    model = "fake-ui-critic-model"

    def __init__(self) -> None:
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "Critic Scoring Prompt" in prompt:
            return "originality: 7\noverall_score: 8\nNext action: interview one buyer."
        return "1. Stored UI critique idea"


def setup_idea(database_path) -> int:
    fake_client = FakeOllamaClient()
    with open_database(database_path) as connection:
        initialize_database(connection)
        first_portfolio = connection.execute("SELECT id FROM portfolios ORDER BY id LIMIT 1").fetchone()[
            "id"
        ]
        first_agent = connection.execute("SELECT id FROM idea_agents ORDER BY id LIMIT 1").fetchone()[
            "id"
        ]
        first_technique = connection.execute(
            "SELECT id FROM creative_techniques ORDER BY id LIMIT 1"
        ).fetchone()["id"]
        result = generate_and_store_ideas(
            connection,
            seed_text="UI critic route seed",
            portfolio_id=first_portfolio,
            idea_agent_id=first_agent,
            creative_technique_id=first_technique,
            client=fake_client,
        )
        return result.ideas[0].id


def test_ideas_page_renders_critique_action(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    idea_id = setup_idea(database_path)
    client = TestClient(create_app(database_path=database_path, ollama_client=FakeOllamaClient()))

    response = client.get("/ideas")

    assert response.status_code == 200
    assert f'action="/ideas/{idea_id}/critique"' in response.text
    assert "Run brutal critique" in response.text


def test_critique_route_uses_fake_client_and_stores_result(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    idea_id = setup_idea(database_path)
    fake_client = FakeOllamaClient()
    client = TestClient(create_app(database_path=database_path, ollama_client=fake_client))

    response = client.post(f"/ideas/{idea_id}/critique")

    assert response.status_code == 200
    assert "Brutal Critic" in response.text
    assert "overall_score: 8" in response.text
    assert fake_client.prompts
    assert "Critic Scoring Prompt" in fake_client.prompts[0]

    with open_database(database_path) as connection:
        critique = connection.execute(
            "SELECT idea_id, raw_output, overall_score FROM critiques"
        ).fetchone()

    assert critique["idea_id"] == idea_id
    assert "Next action" in critique["raw_output"]
    assert critique["overall_score"] == 8
