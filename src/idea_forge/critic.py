"""Brutal Critic scoring service."""

from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3
from typing import Protocol

from idea_forge.prompts import PromptRenderer


CRITIC_NAME = "Brutal Critic"
DEFAULT_CONTEXT = "Score the stored idea for practical local-first evaluation."
SCORE_DIMENSIONS = (
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
)


class CriticClient(Protocol):
    """Minimal model client protocol used by critic scoring."""

    def generate(self, prompt: str) -> str:
        """Generate text for the rendered critic prompt."""


@dataclass(frozen=True)
class CritiqueResult:
    """Stored critique result."""

    id: int
    idea_id: int
    raw_output: str
    prompt_text: str
    scores: dict[str, int]


def critique_and_store_idea(
    connection: sqlite3.Connection,
    *,
    idea_id: int,
    client: CriticClient,
    prompt_renderer: PromptRenderer | None = None,
    context: str = DEFAULT_CONTEXT,
) -> CritiqueResult:
    """Run the Brutal Critic against a stored idea and persist the result."""
    idea = get_idea_for_critique(connection, idea_id)
    renderer = prompt_renderer or PromptRenderer()
    prompt_text = renderer.render(
        "critic.md",
        {
            "idea": _idea_prompt_text(idea),
            "portfolio": idea["portfolio_name"] or "Unassigned",
            "evaluation_dimensions": "\n".join(f"- {name}" for name in SCORE_DIMENSIONS),
            "context": context,
        },
    )

    raw_output = client.generate(prompt_text)
    scores = parse_scores(raw_output)
    critique_id = insert_critique(
        connection,
        idea_id=idea_id,
        model_name=str(getattr(client, "model", "")),
        prompt_text=prompt_text,
        raw_output=raw_output,
        scores=scores,
    )
    connection.commit()

    return CritiqueResult(
        id=critique_id,
        idea_id=idea_id,
        raw_output=raw_output,
        prompt_text=prompt_text,
        scores=scores,
    )


def get_idea_for_critique(connection: sqlite3.Connection, idea_id: int) -> sqlite3.Row:
    """Return the stored idea and labels needed for critique prompt assembly."""
    idea = connection.execute(
        """
        SELECT
            ideas.id,
            ideas.title,
            ideas.body,
            portfolios.name AS portfolio_name,
            idea_agents.name AS idea_agent_name,
            creative_techniques.name AS creative_technique_name
        FROM ideas
        LEFT JOIN portfolios ON portfolios.id = ideas.portfolio_id
        LEFT JOIN idea_agents ON idea_agents.id = ideas.idea_agent_id
        LEFT JOIN creative_techniques ON creative_techniques.id = ideas.creative_technique_id
        WHERE ideas.id = ?
        """,
        (idea_id,),
    ).fetchone()
    if idea is None:
        raise ValueError(f"Unknown idea id: {idea_id}")

    return idea


def insert_critique(
    connection: sqlite3.Connection,
    *,
    idea_id: int,
    model_name: str,
    prompt_text: str,
    raw_output: str,
    scores: dict[str, int],
) -> int:
    """Persist a critique and any safely parsed scores."""
    columns = ", ".join(SCORE_DIMENSIONS)
    placeholders = ", ".join("?" for _ in SCORE_DIMENSIONS)
    cursor = connection.execute(
        f"""
        INSERT INTO critiques (
            idea_id,
            critic_name,
            model_name,
            prompt_text,
            raw_output,
            {columns}
        )
        VALUES (?, ?, ?, ?, ?, {placeholders})
        """,
        (
            idea_id,
            CRITIC_NAME,
            model_name,
            prompt_text,
            raw_output,
            *(scores.get(name) for name in SCORE_DIMENSIONS),
        ),
    )
    return int(cursor.lastrowid)


def latest_critiques_by_idea(connection: sqlite3.Connection) -> dict[int, sqlite3.Row]:
    """Return the latest critique row for each idea."""
    rows = connection.execute(
        """
        SELECT critiques.*
        FROM critiques
        INNER JOIN (
            SELECT idea_id, MAX(id) AS latest_id
            FROM critiques
            GROUP BY idea_id
        ) latest ON latest.latest_id = critiques.id
        """
    ).fetchall()
    return {int(row["idea_id"]): row for row in rows}


def parse_scores(raw_output: str) -> dict[str, int]:
    """Extract simple 0-10 integer scores from critic output when safe."""
    scores = {}
    for dimension in SCORE_DIMENSIONS:
        label = dimension.replace("_", r"[_\s-]")
        pattern = rf"(?im)^\s*[-*]?\s*{label}\s*[:=]\s*(10|[0-9])\b"
        match = re.search(pattern, raw_output)
        if match:
            scores[dimension] = int(match.group(1))

    return scores


def _idea_prompt_text(idea: sqlite3.Row) -> str:
    labels = [
        f"Title: {idea['title']}",
        f"Body: {idea['body']}",
    ]
    if idea["idea_agent_name"]:
        labels.append(f"Idea agent: {idea['idea_agent_name']}")
    if idea["creative_technique_name"]:
        labels.append(f"Creative technique: {idea['creative_technique_name']}")

    return "\n".join(labels)
