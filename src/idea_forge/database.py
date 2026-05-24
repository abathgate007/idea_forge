"""SQLite database setup for Idea Forge."""

from pathlib import Path
import sqlite3

DATABASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS idea_agents (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS creative_techniques (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generation_runs (
    id INTEGER PRIMARY KEY,
    seed_id INTEGER,
    portfolio_id INTEGER,
    idea_agent_id INTEGER,
    creative_technique_id INTEGER,
    novelty_mode TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'created',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seed_id) REFERENCES seeds (id),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
    FOREIGN KEY (idea_agent_id) REFERENCES idea_agents (id),
    FOREIGN KEY (creative_technique_id) REFERENCES creative_techniques (id)
);

CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY,
    generation_run_id INTEGER,
    seed_id INTEGER,
    portfolio_id INTEGER,
    idea_agent_id INTEGER,
    creative_technique_id INTEGER,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation_run_id) REFERENCES generation_runs (id),
    FOREIGN KEY (seed_id) REFERENCES seeds (id),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
    FOREIGN KEY (idea_agent_id) REFERENCES idea_agents (id),
    FOREIGN KEY (creative_technique_id) REFERENCES creative_techniques (id)
);
"""


def open_database(database_path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a SQLite database connection with project defaults."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the MVP database schema if it does not already exist."""
    connection.executescript(DATABASE_SCHEMA)
    connection.commit()
