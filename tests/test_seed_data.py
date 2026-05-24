import sqlite3

from idea_forge.database import (
    DEFAULT_CREATIVE_TECHNIQUES,
    DEFAULT_IDEA_AGENTS,
    DEFAULT_PORTFOLIOS,
    initialize_schema,
    load_default_reference_data,
    open_database,
)


def names_for_table(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"SELECT name FROM {table_name}").fetchall()
    return {row["name"] for row in rows}


def row_count(connection: sqlite3.Connection, table_name: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def test_load_default_reference_data_creates_required_entries(tmp_path) -> None:
    database_path = tmp_path / "idea_forge_test.sqlite"

    with open_database(database_path) as connection:
        initialize_schema(connection)
        load_default_reference_data(connection)

        assert {name for name, _ in DEFAULT_PORTFOLIOS}.issubset(
            names_for_table(connection, "portfolios")
        )
        assert {name for name, _ in DEFAULT_IDEA_AGENTS}.issubset(
            names_for_table(connection, "idea_agents")
        )
        assert {name for name, _ in DEFAULT_CREATIVE_TECHNIQUES}.issubset(
            names_for_table(connection, "creative_techniques")
        )


def test_load_default_reference_data_is_idempotent(tmp_path) -> None:
    database_path = tmp_path / "idea_forge_test.sqlite"

    with open_database(database_path) as connection:
        initialize_schema(connection)
        load_default_reference_data(connection)

        initial_counts = {
            "portfolios": row_count(connection, "portfolios"),
            "idea_agents": row_count(connection, "idea_agents"),
            "creative_techniques": row_count(connection, "creative_techniques"),
        }

        load_default_reference_data(connection)

        assert {
            "portfolios": row_count(connection, "portfolios"),
            "idea_agents": row_count(connection, "idea_agents"),
            "creative_techniques": row_count(connection, "creative_techniques"),
        } == initial_counts
