import sqlite3
import json

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


def structured_output() -> str:
    return json.dumps(
        {
            "ideas": [
                {
                    "title": "Local AppSec Workshop Wedge",
                    "summary": "A paid workshop that turns AppSec design review pain into a repeatable offer.",
                    "target_buyer": "Security leaders at midsize SaaS companies",
                    "first_validation_step": "Email five security leaders with a one-page workshop outline.",
                    "why_it_fits": "It uses Andrew's AppSec credibility and can be validated quickly.",
                },
                {
                    "title": "Realtor Listing Prep Kit",
                    "summary": "A checklist and vendor bundle for homeowners preparing Lamorinda listings.",
                    "target_buyer": "Lamorinda homeowners planning to sell within six months",
                    "first_validation_step": "Offer the kit to three upcoming seller consultations.",
                    "why_it_fits": "It fits real estate marketing and can generate near-term leads.",
                },
            ]
        }
    )


def test_parse_generated_ideas_reads_strict_json_output() -> None:
    ideas = parse_generated_ideas(structured_output())

    assert [idea.title for idea in ideas] == [
        "Local AppSec Workshop Wedge",
        "Realtor Listing Prep Kit",
    ]
    assert ideas[0].summary.startswith("A paid workshop")
    assert ideas[0].target_buyer == "Security leaders at midsize SaaS companies"
    assert ideas[0].first_validation_step.startswith("Email five")
    assert ideas[0].why_it_fits.startswith("It uses Andrew")


def test_parse_generated_ideas_falls_back_to_one_raw_output_idea() -> None:
    raw_output = "A detailed idea\n## Description\nDo this.\n## Validation\nTry that."

    ideas = parse_generated_ideas(raw_output)

    assert len(ideas) == 1
    assert ideas[0].title == "Unparsed model output"
    assert ideas[0].summary == raw_output


def test_generate_and_store_ideas_persists_ideas_and_run_metadata(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    fake_client = FakeOllamaClient(structured_output())

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
            """
            SELECT
                title,
                summary,
                target_buyer,
                first_validation_step,
                why_it_fits,
                body,
                generation_run_id
            FROM ideas
            ORDER BY id
            """
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
    assert [idea["title"] for idea in ideas] == [
        "Local AppSec Workshop Wedge",
        "Realtor Listing Prep Kit",
    ]
    assert ideas[0]["summary"].startswith("A paid workshop")
    assert ideas[0]["target_buyer"] == "Security leaders at midsize SaaS companies"
    assert ideas[0]["first_validation_step"].startswith("Email five")
    assert ideas[0]["why_it_fits"].startswith("It uses Andrew")
    assert "Target buyer: Security leaders" in ideas[0]["body"]
    assert all(idea["generation_run_id"] == result.run_id for idea in ideas)
    assert run["status"] == "completed"
    assert run["model_name"] == "fake-model"
    assert "strict JSON" in run["prompt_text"]
    assert "Local AppSec Workshop Wedge" in run["raw_output"]


def test_invalid_model_output_is_stored_as_one_fallback_idea(tmp_path) -> None:
    database_path = tmp_path / "idea_forge.sqlite"
    raw_output = "# Idea\n## Description\nBuild it.\n## Validation\nInterview buyers."
    fake_client = FakeOllamaClient(raw_output)

    with open_database(database_path) as connection:
        initialize_database(connection)

        generate_and_store_ideas(
            connection,
            seed_text="Markdown should not split into separate ideas",
            portfolio_id=first_id(connection, "portfolios"),
            idea_agent_id=first_id(connection, "idea_agents"),
            creative_technique_id=first_id(connection, "creative_techniques"),
            client=fake_client,
        )

        ideas = connection.execute(
            "SELECT title, summary, target_buyer, first_validation_step, why_it_fits FROM ideas"
        ).fetchall()

    assert len(ideas) == 1
    assert ideas[0]["title"] == "Unparsed model output"
    assert ideas[0]["summary"] == raw_output
    assert ideas[0]["target_buyer"] == ""
    assert ideas[0]["first_validation_step"] == ""
    assert ideas[0]["why_it_fits"] == ""
