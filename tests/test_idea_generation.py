import sqlite3

from idea_forge.database import initialize_database, open_database
from idea_forge.idea_generation import generate_and_store_ideas, parse_generated_ideas


class FakeOllamaClient:
    model = "fake-model"

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


def test_parse_generated_ideas_splits_simple_list_output() -> None:
    assert parse_generated_ideas("1. First wedge\n2. Second wedge") == (
        "First wedge",
        "Second wedge",
    )


def test_parse_generated_ideas_falls_back_to_raw_text_for_uncertain_output() -> None:
    raw_output = "A detailed idea\nwith continuation text"

    assert parse_generated_ideas(raw_output) == (raw_output,)


def test_generate_and_store_ideas_persists_ideas_and_run_metadata(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    fake_client = FakeOllamaClient("- Local AppSec workshop wedge\n- Realtor listing prep kit")

    with open_database(database_path) as connection:
        initialize_database(connection)

        result = generate_and_store_ideas(
            connection,
            seed_text="Local services for expert operators",
            portfolio_id=first_id(connection, "portfolios"),
            idea_agent_id=first_id(connection, "idea_agents"),
            creative_technique_id=first_id(connection, "creative_techniques"),
            client=fake_client,
        )

        ideas = connection.execute(
            "SELECT body, generation_run_id FROM ideas ORDER BY id"
        ).fetchall()
        run = connection.execute(
            """
            SELECT status, model_name, prompt_text, raw_output
            FROM generation_runs
            WHERE id = ?
            """,
            (result.run_id,),
        ).fetchone()

    assert fake_client.prompts
    assert "Local services for expert operators" in fake_client.prompts[0]
    assert [idea["body"] for idea in ideas] == [
        "Local AppSec workshop wedge",
        "Realtor listing prep kit",
    ]
    assert all(idea["generation_run_id"] == result.run_id for idea in ideas)
    assert run["status"] == "completed"
    assert run["model_name"] == "fake-model"
    assert "Idea Generation Prompt" in run["prompt_text"]
    assert "Local AppSec workshop wedge" in run["raw_output"]
