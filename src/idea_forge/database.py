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

DEFAULT_PORTFOLIOS = (
    (
        "Money now",
        "Near-term revenue, services, lead generation, consulting offers, and quick validation.",
    ),
    (
        "Long-term business",
        "Larger products or platforms that may require compounding effort.",
    ),
    (
        "AI-related ideas",
        "Software, workflow, content, and automation ideas centered on AI.",
    ),
    (
        "Cybersecurity and AppSec",
        "Security leadership, AppSec workflows, design review, threat modeling, and AI security.",
    ),
    (
        "Writing and content",
        "Books, stories, newsletters, LinkedIn posts, workshops, and authority-building content.",
    ),
    (
        "Health and lifestyle",
        "Fitness, habits, energy, pain reduction, happiness, and retirement quality.",
    ),
    (
        "Vlatka and real estate",
        "Realtor marketing, Lamorinda content, listing prep, neighborhood pages, lead generation, and workflow ideas.",
    ),
    (
        "Retirement income",
        "Low-burden income systems aligned with retirement goals.",
    ),
    (
        "Wild moonshots",
        "High-novelty ideas that may be impractical now but useful as creative raw material.",
    ),
)

DEFAULT_IDEA_AGENTS = (
    (
        "Quirky Professor",
        "Weird synthesis, analogy, hidden connections, and original frameworks.",
    ),
    (
        "Seasoned VC",
        "Market size, timing, buyer, moat, distribution, and scale realism.",
    ),
    (
        "Money-Hungry Operator",
        "Cash flow, fast validation, services, upsells, and practical selling.",
    ),
    (
        "AppSec War Veteran",
        "Enterprise AppSec reality, buyer trust, review burden, evidence, and workflow fit.",
    ),
    (
        "Lazy Genius",
        "Automation, low maintenance, minimum effort, and high leverage.",
    ),
    (
        "Highly Intelligent Teenage Goth Punk",
        "Anti-bullshit, cultural edge, emotional charge, branding, and cringe detection.",
    ),
    (
        "Environmentalist Girl",
        "Long-term consequence, sustainability, resilience, and moral legitimacy.",
    ),
)

DEFAULT_CREATIVE_TECHNIQUES = (
    ("Word Association Ladder", "Explore linked associations to move from a seed toward less obvious ideas."),
    ("Random Word Collision", "Combine the seed with an unrelated word to force new angles."),
    ("Inversion", "Reverse the obvious assumption and inspect what becomes useful."),
    ("Constraint Forcing", "Apply hard limits to reveal simpler or more focused ideas."),
    ("Analogy Transfer", "Borrow structures from another domain and map them onto the seed."),
    ("SCAMPER", "Use substitute, combine, adapt, modify, put to another use, eliminate, and reverse prompts."),
    ("Future-Backward", "Start from a future successful state and work backward to the first move."),
    ("Failure-First", "Imagine why the idea fails, then design around the failure mode."),
    ("Forbidden Obvious Answers", "Exclude generic answers so the idea must move into less crowded territory."),
    ("Cross-Pollination Matrix", "Combine portfolios, audiences, or mechanisms to surface new intersections."),
    ("Metaphor Mining", "Use metaphors to uncover hidden product, content, or positioning structures."),
    ("Tiny Wedge", "Find the smallest useful entry point for fast validation."),
    ("Buyer Objection Reversal", "Turn likely buyer objections into product or positioning requirements."),
    ("Pain-to-Product Ladder", "Convert a specific pain into service, content, workflow, and product options."),
    ("Reputation Flywheel", "Design ideas that compound authority, trust, and distribution over time."),
)


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


def load_default_reference_data(connection: sqlite3.Connection) -> None:
    """Load default portfolios, idea agents, and creative techniques."""
    insert_sql = "INSERT OR IGNORE INTO {table} (name, description) VALUES (?, ?)"
    connection.executemany(insert_sql.format(table="portfolios"), DEFAULT_PORTFOLIOS)
    connection.executemany(insert_sql.format(table="idea_agents"), DEFAULT_IDEA_AGENTS)
    connection.executemany(
        insert_sql.format(table="creative_techniques"),
        DEFAULT_CREATIVE_TECHNIQUES,
    )
    connection.commit()
