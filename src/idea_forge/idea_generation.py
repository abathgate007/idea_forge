"""Manual idea generation service."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Protocol

from idea_forge.prompts import PromptRenderer


DEFAULT_NOVELTY_MODE = "practical and original"
DEFAULT_CONTEXT = "Manual local UI generation. No critic scoring, feedback, or search."
DEFAULT_ANTI_SLUDGE_RULES = (
    "Avoid generic AI wrappers, vague dashboards, unclear buyers, and ideas that "
    "require venture funding before validation."
)


class IdeaGenerationClient(Protocol):
    """Minimal model client protocol used by manual idea generation."""

    def generate(self, prompt: str) -> str:
        """Generate text for the rendered prompt."""


@dataclass(frozen=True)
class GeneratedIdea:
    """A parsed generated idea returned from a run."""

    id: int
    title: str
    summary: str
    target_buyer: str
    first_validation_step: str
    why_it_fits: str
    body: str


@dataclass(frozen=True)
class ParsedIdea:
    """A structured generated idea ready for persistence."""

    title: str
    summary: str
    target_buyer: str
    first_validation_step: str
    why_it_fits: str

    @property
    def body(self) -> str:
        parts = [
            self.summary,
            f"Target buyer: {self.target_buyer}",
            f"First validation step: {self.first_validation_step}",
            f"Why it fits: {self.why_it_fits}",
        ]
        return "\n".join(part for part in parts if part.strip())


@dataclass(frozen=True)
class GenerationResult:
    """Stored result for a manual generation run."""

    run_id: int
    ideas: tuple[GeneratedIdea, ...]
    raw_output: str
    prompt_text: str


def generate_and_store_ideas(
    connection: sqlite3.Connection,
    *,
    seed_text: str,
    portfolio_id: int,
    idea_agent_id: int,
    creative_technique_id: int,
    client: IdeaGenerationClient,
    prompt_renderer: PromptRenderer | None = None,
    novelty_mode: str = DEFAULT_NOVELTY_MODE,
    context: str = DEFAULT_CONTEXT,
    anti_sludge_rules: str = DEFAULT_ANTI_SLUDGE_RULES,
) -> GenerationResult:
    """Generate ideas through Ollama and store the run, seed, and ideas."""
    clean_seed = seed_text.strip()
    if not clean_seed:
        raise ValueError("Seed text is required.")

    portfolio = _required_reference(connection, "portfolios", portfolio_id)
    idea_agent = _required_reference(connection, "idea_agents", idea_agent_id)
    creative_technique = _required_reference(
        connection,
        "creative_techniques",
        creative_technique_id,
    )

    seed_id = _insert_seed(connection, clean_seed)
    renderer = prompt_renderer or PromptRenderer()
    prompt_text = renderer.render(
        "idea_generation.md",
        {
            "seed": clean_seed,
            "portfolio": _reference_prompt_text(portfolio),
            "idea_agent": _reference_prompt_text(idea_agent),
            "creative_technique": _reference_prompt_text(creative_technique),
            "novelty_mode": novelty_mode,
            "context": context,
            "anti_sludge_rules": anti_sludge_rules,
        },
    )

    run_id = _insert_generation_run(
        connection,
        seed_id=seed_id,
        portfolio_id=portfolio_id,
        idea_agent_id=idea_agent_id,
        creative_technique_id=creative_technique_id,
        novelty_mode=novelty_mode,
        model_name=str(getattr(client, "model", "")),
        prompt_text=prompt_text,
    )

    try:
        raw_output = client.generate(prompt_text)
    except Exception as error:
        _mark_generation_failed(connection, run_id, str(error))
        raise

    parsed_ideas = parse_generated_ideas(raw_output)
    stored_ideas = tuple(
        _insert_idea(
            connection,
            run_id=run_id,
            seed_id=seed_id,
            portfolio_id=portfolio_id,
            idea_agent_id=idea_agent_id,
            creative_technique_id=creative_technique_id,
            idea=idea,
        )
        for idea in parsed_ideas
    )
    _mark_generation_completed(connection, run_id, raw_output)
    connection.commit()

    return GenerationResult(
        run_id=run_id,
        ideas=stored_ideas,
        raw_output=raw_output,
        prompt_text=prompt_text,
    )


def parse_generated_ideas(raw_output: str) -> tuple[ParsedIdea, ...]:
    """Parse structured JSON model output, falling back to one raw-output idea."""
    clean_output = raw_output.strip()
    if not clean_output:
        return (_fallback_idea(""),)

    try:
        payload = json.loads(clean_output)
    except json.JSONDecodeError:
        return (_fallback_idea(clean_output),)

    ideas = payload.get("ideas") if isinstance(payload, dict) else None
    if not isinstance(ideas, list):
        return (_fallback_idea(clean_output),)

    parsed_ideas = []
    for item in ideas:
        if not isinstance(item, dict):
            return (_fallback_idea(clean_output),)

        parsed_idea = ParsedIdea(
            title=_clean_field(item.get("title")),
            summary=_clean_field(item.get("summary")),
            target_buyer=_clean_field(item.get("target_buyer")),
            first_validation_step=_clean_field(item.get("first_validation_step")),
            why_it_fits=_clean_field(item.get("why_it_fits")),
        )
        if not all(
            (
                parsed_idea.title,
                parsed_idea.summary,
                parsed_idea.target_buyer,
                parsed_idea.first_validation_step,
                parsed_idea.why_it_fits,
            )
        ):
            return (_fallback_idea(clean_output),)

        parsed_ideas.append(parsed_idea)

    if not parsed_ideas:
        return (_fallback_idea(clean_output),)

    return tuple(parsed_ideas)


def list_ideas(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return stored ideas with reference labels for display."""
    return connection.execute(
        """
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
        ORDER BY ideas.id DESC
        """
    ).fetchall()


def list_reference_rows(connection: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    """Return reference data rows ordered by id."""
    if table_name not in {"portfolios", "idea_agents", "creative_techniques"}:
        raise ValueError(f"Unsupported reference table: {table_name}")

    return connection.execute(
        f"SELECT id, name, description FROM {table_name} ORDER BY id"
    ).fetchall()


def _required_reference(
    connection: sqlite3.Connection,
    table_name: str,
    row_id: int,
) -> sqlite3.Row:
    if table_name not in {"portfolios", "idea_agents", "creative_techniques"}:
        raise ValueError(f"Unsupported reference table: {table_name}")

    row = connection.execute(
        f"SELECT id, name, description FROM {table_name} WHERE id = ?",
        (row_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Unknown {table_name} id: {row_id}")

    return row


def _reference_prompt_text(row: sqlite3.Row) -> str:
    description = row["description"].strip()
    if description:
        return f"{row['name']}: {description}"

    return row["name"]


def _insert_seed(connection: sqlite3.Connection, seed_text: str) -> int:
    title = _title_from_text(seed_text)
    cursor = connection.execute(
        "INSERT INTO seeds (title, body) VALUES (?, ?)",
        (title, seed_text),
    )
    return int(cursor.lastrowid)


def _insert_generation_run(
    connection: sqlite3.Connection,
    *,
    seed_id: int,
    portfolio_id: int,
    idea_agent_id: int,
    creative_technique_id: int,
    novelty_mode: str,
    model_name: str,
    prompt_text: str,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO generation_runs (
            seed_id,
            portfolio_id,
            idea_agent_id,
            creative_technique_id,
            novelty_mode,
            model_name,
            prompt_text,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            seed_id,
            portfolio_id,
            idea_agent_id,
            creative_technique_id,
            novelty_mode,
            model_name,
            prompt_text,
            "running",
        ),
    )
    connection.commit()
    return int(cursor.lastrowid)


def _mark_generation_completed(
    connection: sqlite3.Connection,
    run_id: int,
    raw_output: str,
) -> None:
    connection.execute(
        """
        UPDATE generation_runs
        SET raw_output = ?, status = ?
        WHERE id = ?
        """,
        (raw_output, "completed", run_id),
    )


def _mark_generation_failed(
    connection: sqlite3.Connection,
    run_id: int,
    error_message: str,
) -> None:
    connection.execute(
        """
        UPDATE generation_runs
        SET error_message = ?, status = ?
        WHERE id = ?
        """,
        (error_message, "failed", run_id),
    )
    connection.commit()


def _insert_idea(
    connection: sqlite3.Connection,
    *,
    run_id: int,
    seed_id: int,
    portfolio_id: int,
    idea_agent_id: int,
    creative_technique_id: int,
    idea: ParsedIdea,
) -> GeneratedIdea:
    cursor = connection.execute(
        """
        INSERT INTO ideas (
            generation_run_id,
            seed_id,
            portfolio_id,
            idea_agent_id,
            creative_technique_id,
            title,
            summary,
            target_buyer,
            first_validation_step,
            why_it_fits,
            body
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            seed_id,
            portfolio_id,
            idea_agent_id,
            creative_technique_id,
            idea.title,
            idea.summary,
            idea.target_buyer,
            idea.first_validation_step,
            idea.why_it_fits,
            idea.body,
        ),
    )
    return GeneratedIdea(
        id=int(cursor.lastrowid),
        title=idea.title,
        summary=idea.summary,
        target_buyer=idea.target_buyer,
        first_validation_step=idea.first_validation_step,
        why_it_fits=idea.why_it_fits,
        body=idea.body,
    )


def _title_from_text(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line:
        return "Untitled idea"

    return first_line[:80]


def _clean_field(value: object) -> str:
    if not isinstance(value, str):
        return ""

    return value.strip()


def _fallback_idea(raw_output: str) -> ParsedIdea:
    return ParsedIdea(
        title="Unparsed model output",
        summary=raw_output,
        target_buyer="",
        first_validation_step="",
        why_it_fits="",
    )
