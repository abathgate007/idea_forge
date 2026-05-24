"""Basic SQLite search for stored ideas."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from idea_forge.feedback import FEEDBACK_ACTIONS


@dataclass(frozen=True)
class IdeaSearchFilters:
    """Optional filters for idea search."""

    query: str = ""
    portfolio_id: int | None = None
    idea_agent_id: int | None = None
    creative_technique_id: int | None = None
    feedback_action: str = ""


def search_ideas(
    connection: sqlite3.Connection,
    filters: IdeaSearchFilters | None = None,
) -> list[sqlite3.Row]:
    """Return stored ideas matching a keyword query and simple metadata filters."""
    filters = filters or IdeaSearchFilters()
    where_clauses: list[str] = []
    params: list[object] = []

    query = filters.query.strip()
    if query:
        like_value = f"%{query}%"
        where_clauses.append(
            """
            (
                ideas.title LIKE ?
                OR ideas.summary LIKE ?
                OR ideas.target_buyer LIKE ?
                OR ideas.first_validation_step LIKE ?
                OR ideas.why_it_fits LIKE ?
                OR ideas.body LIKE ?
            )
            """
        )
        params.extend([like_value] * 6)

    if filters.portfolio_id is not None:
        where_clauses.append("ideas.portfolio_id = ?")
        params.append(filters.portfolio_id)

    if filters.idea_agent_id is not None:
        where_clauses.append("ideas.idea_agent_id = ?")
        params.append(filters.idea_agent_id)

    if filters.creative_technique_id is not None:
        where_clauses.append("ideas.creative_technique_id = ?")
        params.append(filters.creative_technique_id)

    if filters.feedback_action:
        if filters.feedback_action not in FEEDBACK_ACTIONS:
            raise ValueError(f"Unsupported feedback action filter: {filters.feedback_action}")
        where_clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM feedback_events
                WHERE feedback_events.idea_id = ideas.id
                AND feedback_events.action = ?
            )
            """
        )
        params.append(filters.feedback_action)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    return connection.execute(
        f"""
        SELECT
            ideas.id,
            ideas.title,
            ideas.summary,
            ideas.target_buyer,
            ideas.first_validation_step,
            ideas.why_it_fits,
            ideas.body,
            ideas.created_at,
            portfolios.name AS portfolio_name,
            idea_agents.name AS idea_agent_name,
            creative_techniques.name AS creative_technique_name
        FROM ideas
        LEFT JOIN portfolios ON portfolios.id = ideas.portfolio_id
        LEFT JOIN idea_agents ON idea_agents.id = ideas.idea_agent_id
        LEFT JOIN creative_techniques ON creative_techniques.id = ideas.creative_technique_id
        {where_sql}
        ORDER BY ideas.id DESC
        """,
        params,
    ).fetchall()
