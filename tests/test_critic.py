import sqlite3

from idea_forge.critic import critique_and_store_idea, parse_scores
from idea_forge.database import initialize_database, open_database
from idea_forge.idea_generation import generate_and_store_ideas


class FakeOllamaClient:
    model = "fake-critic-model"

    def __init__(self, output: str) -> None:
        self.output = output
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.output


def first_id(connection: sqlite3.Connection, table_name: str) -> int:
    return connection.execute(f"SELECT id FROM {table_name} ORDER BY id LIMIT 1").fetchone()[
        "id"
    ]


def stored_idea_id(connection: sqlite3.Connection) -> int:
    generation_client = FakeOllamaClient("1. Local proof-of-value AppSec audit kit")
    result = generate_and_store_ideas(
        connection,
        seed_text="AppSec consulting wedge",
        portfolio_id=first_id(connection, "portfolios"),
        idea_agent_id=first_id(connection, "idea_agents"),
        creative_technique_id=first_id(connection, "creative_techniques"),
        client=generation_client,
    )
    return result.ideas[0].id


def test_parse_scores_extracts_safe_numeric_lines() -> None:
    raw_output = """
    originality: 8
    usefulness: 7/10
    money_potential = 6
    legal_risk: low
    overall_score: 9
    """

    assert parse_scores(raw_output) == {
        "originality": 8,
        "usefulness": 7,
        "money_potential": 6,
        "overall_score": 9,
    }


def test_critique_prompt_is_assembled_and_result_is_stored(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    fake_client = FakeOllamaClient(
        "originality: 8\nusefulness: 7\noverall_score: 8\nStrong reason to build: focused buyer."
    )

    with open_database(database_path) as connection:
        initialize_database(connection)
        idea_id = stored_idea_id(connection)

        result = critique_and_store_idea(
            connection,
            idea_id=idea_id,
            client=fake_client,
        )

        critique = connection.execute(
            """
            SELECT idea_id, model_name, prompt_text, raw_output, originality, usefulness, overall_score
            FROM critiques
            WHERE id = ?
            """,
            (result.id,),
        ).fetchone()

    assert fake_client.prompts
    assert "Critic Scoring Prompt" in fake_client.prompts[0]
    assert "Local proof-of-value AppSec audit kit" in fake_client.prompts[0]
    assert critique["idea_id"] == idea_id
    assert critique["model_name"] == "fake-critic-model"
    assert "originality" in critique["prompt_text"]
    assert "Strong reason to build" in critique["raw_output"]
    assert critique["originality"] == 8
    assert critique["usefulness"] == 7
    assert critique["overall_score"] == 8
