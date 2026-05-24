import sqlite3

from idea_forge.database import initialize_schema, open_database


EXPECTED_TABLES = {
    "ideas",
    "seeds",
    "portfolios",
    "idea_agents",
    "creative_techniques",
    "generation_runs",
    "critiques",
    "feedback_events",
}


def table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    return {row["name"] for row in rows}


def column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def test_initialize_schema_creates_expected_tables_in_temp_database(tmp_path) -> None:
    database_path = tmp_path / "idea_forge_test.sqlite"

    with open_database(database_path) as connection:
        initialize_schema(connection)

        assert EXPECTED_TABLES.issubset(table_names(connection))


def test_open_database_enables_foreign_keys() -> None:
    with open_database() as connection:
        foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]

    assert foreign_keys_enabled == 1


def test_generation_runs_schema_includes_manual_generation_metadata() -> None:
    with open_database() as connection:
        initialize_schema(connection)

        assert {
            "model_name",
            "prompt_text",
            "raw_output",
            "error_message",
        }.issubset(column_names(connection, "generation_runs"))


def test_ideas_schema_includes_structured_generation_fields() -> None:
    with open_database() as connection:
        initialize_schema(connection)

        assert {
            "summary",
            "target_buyer",
            "first_validation_step",
            "why_it_fits",
        }.issubset(column_names(connection, "ideas"))


def test_critiques_schema_includes_score_columns() -> None:
    with open_database() as connection:
        initialize_schema(connection)

        assert {
            "idea_id",
            "raw_output",
            "originality",
            "usefulness",
            "money_potential",
            "time_to_market",
            "capital_needed",
            "technical_difficulty",
            "operational_burden",
            "legal_risk",
            "reputational_risk",
            "personal_fit",
            "lifestyle_fit",
            "strategic_alignment",
            "overall_score",
        }.issubset(column_names(connection, "critiques"))


def test_feedback_events_schema_links_to_ideas() -> None:
    with open_database() as connection:
        initialize_schema(connection)

        assert {
            "idea_id",
            "action",
            "reason_chips",
            "created_at",
        }.issubset(column_names(connection, "feedback_events"))
