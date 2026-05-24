import sqlite3

from idea_forge.database import initialize_schema, open_database


EXPECTED_TABLES = {
    "ideas",
    "seeds",
    "portfolios",
    "idea_agents",
    "creative_techniques",
    "generation_runs",
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
