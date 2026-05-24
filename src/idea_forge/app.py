"""FastAPI application entrypoint."""

from html import escape
from pathlib import Path
from urllib.parse import parse_qs
import sqlite3

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from idea_forge.critic import (
    SCORE_DIMENSIONS,
    critique_and_store_idea,
    latest_critiques_by_idea,
)
from idea_forge.database import initialize_database, open_database
from idea_forge.feedback import (
    FEEDBACK_ACTIONS,
    REASON_CHIPS,
    decode_reason_chips,
    feedback_events_by_idea,
    record_feedback,
)
from idea_forge.idea_generation import (
    IdeaGenerationClient,
    generate_and_store_ideas,
    list_reference_rows,
)
from idea_forge.memory import create_memory, list_memories
from idea_forge.ollama_client import OllamaClient
from idea_forge.prompts import PromptRenderer
from idea_forge.search import IdeaSearchFilters, search_ideas


DEFAULT_DATABASE_PATH = Path("data") / "idea_forge.sqlite"

BASE_STYLES = """
body {
    color: #202124;
    font-family: Arial, sans-serif;
    line-height: 1.5;
    margin: 0;
}
header, main {
    margin: 0 auto;
    max-width: 920px;
    padding: 24px;
}
header {
    border-bottom: 1px solid #d9dce1;
}
nav a {
    color: #0b57d0;
    margin-right: 16px;
}
.muted {
    color: #5f6368;
}
.actions {
    margin-top: 24px;
}
.inline-form {
    display: inline;
}
.button, button {
    background: #0b57d0;
    border-radius: 4px;
    color: #fff;
    display: inline-block;
    padding: 10px 14px;
    text-decoration: none;
}
.idea-list {
    display: grid;
    gap: 14px;
}
.idea-card {
    border: 1px solid #d9dce1;
    border-radius: 6px;
    padding: 16px;
}
.idea-card h3 {
    margin-top: 0;
}
.meta {
    color: #5f6368;
    font-size: 0.92rem;
}
form {
    display: grid;
    gap: 16px;
    max-width: 680px;
}
label {
    display: grid;
    font-weight: 700;
    gap: 6px;
}
input, select, textarea {
    border: 1px solid #b8bec8;
    border-radius: 4px;
    font: inherit;
    padding: 9px;
}
textarea {
    min-height: 120px;
}
button {
    border: 0;
    font: inherit;
    width: fit-content;
}
.critique {
    background: #f6f8fb;
    border-left: 4px solid #0b57d0;
    margin-top: 14px;
    padding: 12px;
}
.scores {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 8px 0;
}
.score {
    background: #fff;
    border: 1px solid #d9dce1;
    border-radius: 4px;
    padding: 4px 8px;
}
.feedback-controls {
    border-top: 1px solid #e4e7eb;
    margin-top: 14px;
    padding-top: 14px;
}
.feedback-actions, .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.feedback-actions button {
    background: #174ea6;
}
.chip {
    align-items: center;
    border: 1px solid #d9dce1;
    border-radius: 4px;
    display: inline-flex;
    font-weight: 400;
    gap: 6px;
    padding: 4px 8px;
}
.chip input {
    margin: 0;
}
.feedback-events {
    background: #f8f9fa;
    border-left: 4px solid #188038;
    margin-top: 12px;
    padding: 10px 12px;
}
.feedback-events ul {
    margin: 6px 0 0;
    padding-left: 20px;
}
.empty {
    border: 1px solid #d9dce1;
    border-radius: 6px;
    padding: 18px;
}
.search-form {
    background: #f8f9fa;
    border: 1px solid #d9dce1;
    border-radius: 6px;
    margin-bottom: 18px;
    padding: 14px;
}
.search-grid {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
.memory-list {
    display: grid;
    gap: 14px;
    margin-top: 18px;
}
.memory-card {
    border: 1px solid #d9dce1;
    border-radius: 6px;
    padding: 16px;
}
.memory-card h3 {
    margin-top: 0;
}
"""


def page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    """Render a small full-page HTML response."""
    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)} - Idea Forge</title>
    <style>{BASE_STYLES}</style>
</head>
<body>
    <header>
        <h1>Idea Forge</h1>
        <nav aria-label="Primary">
            <a href="/">Home</a>
            <a href="/ideas">Ideas</a>
            <a href="/ideas/generate">Generate</a>
            <a href="/memories">Memories</a>
        </nav>
    </header>
    <main>
        {body}
    </main>
</body>
</html>"""
    return HTMLResponse(html, status_code=status_code)


def options(items: list[sqlite3.Row]) -> str:
    """Render option tags for reference data rows."""
    return "\n".join(
        f'            <option value="{item["id"]}">{escape(item["name"])}</option>'
        for item in items
    )


def create_app(
    *,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    ollama_client: IdeaGenerationClient | None = None,
    prompt_renderer: PromptRenderer | None = None,
) -> FastAPI:
    """Create the Idea Forge FastAPI application."""
    app = FastAPI(title="Idea Forge")
    app.state.ollama_client = ollama_client
    app.state.prompt_renderer = prompt_renderer

    def open_app_database() -> sqlite3.Connection:
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        connection = open_database(database_path)
        initialize_database(connection)
        return connection

    def generation_client() -> IdeaGenerationClient:
        if app.state.ollama_client is not None:
            return app.state.ollama_client

        return OllamaClient.from_environment()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def home() -> HTMLResponse:
        return page(
            "Home",
            """
            <h2>Local idea foundry</h2>
            <p class="muted">Capture seeds, generate ideas through local Ollama, and browse stored ideas.</p>
            <p class="actions">
                <a class="button" href="/ideas/generate">Open generate form</a>
            </p>
            """,
        )

    @app.get("/ideas", response_class=HTMLResponse)
    def list_ideas_page(request: Request) -> HTMLResponse:
        filters = _search_filters_from_query(request)
        with open_app_database() as connection:
            portfolios = list_reference_rows(connection, "portfolios")
            idea_agents = list_reference_rows(connection, "idea_agents")
            creative_techniques = list_reference_rows(connection, "creative_techniques")
            try:
                ideas = search_ideas(connection, filters)
            except ValueError as error:
                return page(
                    "Ideas",
                    f"""
                    <h2>Ideas</h2>
                    <section class="empty" aria-label="Search failed">
                        <p>Search failed.</p>
                        <p class="muted">{escape(str(error))}</p>
                    </section>
                    """,
                    status_code=400,
                )
            critiques = latest_critiques_by_idea(connection)
            feedback_events = feedback_events_by_idea(connection)

        search_form = _search_form_html(
            filters,
            portfolios,
            idea_agents,
            creative_techniques,
        )
        if not ideas:
            empty_title = (
                "No matching ideas were found."
                if _search_is_active(filters)
                else "No ideas have been generated or stored yet."
            )
            empty_hint = (
                "Try a broader search or generate a new stored idea."
                if _search_is_active(filters)
                else "Use the generate form to create the first stored idea."
            )
            return page(
                "Ideas",
                f"""
                <h2>Ideas</h2>
                {search_form}
                <section class="empty" aria-label="No ideas">
                    <p>{empty_title}</p>
                    <p class="muted">{empty_hint}</p>
                </section>
                """,
            )

        ideas_html = _ideas_html(ideas, critiques, feedback_events)
        return page(
            "Ideas",
            f"""
            <h2>Ideas</h2>
            {search_form}
            <section class="idea-list" aria-label="Stored ideas">
{ideas_html}
            </section>
            """,
        )

    @app.post("/ideas/{idea_id}/feedback", response_class=HTMLResponse)
    async def submit_feedback(idea_id: int, request: Request) -> HTMLResponse:
        try:
            form = parse_qs((await request.body()).decode("utf-8"))
            action = _form_value(form, "action")
            reason_chips = tuple(reason.strip() for reason in form.get("reason_chips", []))
            with open_app_database() as connection:
                record_feedback(
                    connection,
                    idea_id=idea_id,
                    action=action,
                    reason_chips=reason_chips,
                )
        except ValueError as error:
            return page(
                "Feedback",
                f"""
                <h2>Feedback</h2>
                <section class="empty" aria-label="Feedback failed">
                    <p>Feedback was not recorded.</p>
                    <p class="muted">{escape(str(error))}</p>
                </section>
                <p class="actions"><a class="button" href="/ideas">Back to ideas</a></p>
                """,
                status_code=400,
            )

        with open_app_database() as connection:
            ideas = search_ideas(connection)
            critiques = latest_critiques_by_idea(connection)
            feedback_events = feedback_events_by_idea(connection)

        return page(
            "Ideas",
            f"""
            <h2>Ideas</h2>
            <section class="idea-list" aria-label="Stored ideas">
{_ideas_html(ideas, critiques, feedback_events)}
            </section>
            """,
        )

    @app.post("/ideas/{idea_id}/critique", response_class=HTMLResponse)
    def submit_critique_idea(idea_id: int) -> HTMLResponse:
        try:
            with open_app_database() as connection:
                critique_and_store_idea(
                    connection,
                    idea_id=idea_id,
                    client=generation_client(),
                    prompt_renderer=app.state.prompt_renderer,
                )
        except Exception as error:
            return page(
                "Critique Idea",
                f"""
                <h2>Critique idea</h2>
                <section class="empty" aria-label="Critique failed">
                    <p>Critique failed.</p>
                    <p class="muted">{escape(str(error))}</p>
                </section>
                <p class="actions"><a class="button" href="/ideas">Back to ideas</a></p>
                """,
                status_code=500,
            )

        with open_app_database() as connection:
            ideas = search_ideas(connection)
            critiques = latest_critiques_by_idea(connection)
            feedback_events = feedback_events_by_idea(connection)

        ideas_html = _ideas_html(ideas, critiques, feedback_events)
        return page(
            "Ideas",
            f"""
            <h2>Ideas</h2>
            <section class="idea-list" aria-label="Stored ideas">
{ideas_html}
            </section>
            """,
        )

    @app.get("/memories", response_class=HTMLResponse)
    def memories_page() -> HTMLResponse:
        with open_app_database() as connection:
            memories = list_memories(connection)

        return page(
            "Memories",
            f"""
            <h2>Memory summaries</h2>
            {_memory_form_html()}
            {_memories_html(memories)}
            """,
        )

    @app.post("/memories", response_class=HTMLResponse)
    async def submit_memory(request: Request) -> HTMLResponse:
        try:
            form = parse_qs((await request.body()).decode("utf-8"))
            with open_app_database() as connection:
                create_memory(
                    connection,
                    memory_type=_form_value(form, "memory_type"),
                    title=_form_value(form, "title"),
                    content=_form_value(form, "content"),
                )
                memories = list_memories(connection)
        except ValueError as error:
            return page(
                "Memories",
                f"""
                <h2>Memory summaries</h2>
                <section class="empty" aria-label="Memory failed">
                    <p>Memory was not recorded.</p>
                    <p class="muted">{escape(str(error))}</p>
                </section>
                {_memory_form_html()}
                """,
                status_code=400,
            )

        return page(
            "Memories",
            f"""
            <h2>Memory summaries</h2>
            {_memory_form_html()}
            {_memories_html(memories)}
            """,
        )

    @app.get("/ideas/generate", response_class=HTMLResponse)
    def generate_idea_form() -> HTMLResponse:
        with open_app_database() as connection:
            portfolios = list_reference_rows(connection, "portfolios")
            idea_agents = list_reference_rows(connection, "idea_agents")
            creative_techniques = list_reference_rows(connection, "creative_techniques")

        return page(
            "Generate Idea",
            f"""
            <h2>Generate idea</h2>
            <form method="post" action="/ideas/generate">
                <label>
                    Seed
                    <textarea name="seed_text" placeholder="Describe the starting point" required></textarea>
                </label>
                <label>
                    Portfolio
                    <select name="portfolio_id">
{options(portfolios)}
                    </select>
                </label>
                <label>
                    Idea agent
                    <select name="idea_agent_id">
{options(idea_agents)}
                    </select>
                </label>
                <label>
                    Creative technique
                    <select name="creative_technique_id">
{options(creative_techniques)}
                    </select>
                </label>
                <button type="submit">Generate ideas</button>
            </form>
            """,
        )

    @app.post("/ideas/generate", response_class=HTMLResponse)
    async def submit_generate_idea_form(request: Request) -> HTMLResponse:
        try:
            form = parse_qs((await request.body()).decode("utf-8"))
            seed_text = _form_value(form, "seed_text")
            portfolio_id = int(_form_value(form, "portfolio_id"))
            idea_agent_id = int(_form_value(form, "idea_agent_id"))
            creative_technique_id = int(_form_value(form, "creative_technique_id"))
            with open_app_database() as connection:
                result = generate_and_store_ideas(
                    connection,
                    seed_text=seed_text,
                    portfolio_id=portfolio_id,
                    idea_agent_id=idea_agent_id,
                    creative_technique_id=creative_technique_id,
                    client=generation_client(),
                    prompt_renderer=app.state.prompt_renderer,
                )
        except Exception as error:
            return page(
                "Generate Idea",
                f"""
                <h2>Generate idea</h2>
                <section class="empty" aria-label="Generation failed">
                    <p>Generation failed.</p>
                    <p class="muted">{escape(str(error))}</p>
                </section>
                <p class="actions"><a class="button" href="/ideas/generate">Try again</a></p>
                """,
                status_code=500,
            )

        ideas_html = "\n".join(
            f"""
            <article class="idea-card">
                <h3>{escape(idea.title)}</h3>
                {_generated_idea_body_html(idea)}
            </article>
            """
            for idea in result.ideas
        )
        return page(
            "Generated Ideas",
            f"""
            <h2>Generated ideas</h2>
            <p class="meta">Generation run #{result.run_id}</p>
            <section class="idea-list" aria-label="Generated ideas">
{ideas_html}
            </section>
            <p class="actions"><a class="button" href="/ideas">View stored ideas</a></p>
            """,
        )

    return app


def _form_value(form: dict[str, list[str]], name: str) -> str:
    value = form.get(name, [""])[0].strip()
    if not value:
        raise ValueError(f"Missing form field: {name}")

    return value


def _search_filters_from_query(request: Request) -> IdeaSearchFilters:
    return IdeaSearchFilters(
        query=(request.query_params.get("q") or "").strip(),
        portfolio_id=_optional_int(request.query_params.get("portfolio_id")),
        idea_agent_id=_optional_int(request.query_params.get("idea_agent_id")),
        creative_technique_id=_optional_int(
            request.query_params.get("creative_technique_id")
        ),
        feedback_action=(request.query_params.get("feedback_action") or "").strip(),
    )


def _search_is_active(filters: IdeaSearchFilters) -> bool:
    return any(
        (
            filters.query,
            filters.portfolio_id is not None,
            filters.idea_agent_id is not None,
            filters.creative_technique_id is not None,
            filters.feedback_action,
        )
    )


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None

    return int(value)


def _search_form_html(
    filters: IdeaSearchFilters,
    portfolios: list[sqlite3.Row],
    idea_agents: list[sqlite3.Row],
    creative_techniques: list[sqlite3.Row],
) -> str:
    return f"""
    <form class="search-form" method="get" action="/ideas" aria-label="Search ideas">
        <div class="search-grid">
            <label>
                Keyword
                <input name="q" value="{escape(filters.query)}" placeholder="Search stored ideas">
            </label>
            <label>
                Portfolio
                <select name="portfolio_id">
                    <option value="">Any portfolio</option>
                    {_selected_options(portfolios, filters.portfolio_id)}
                </select>
            </label>
            <label>
                Idea agent
                <select name="idea_agent_id">
                    <option value="">Any agent</option>
                    {_selected_options(idea_agents, filters.idea_agent_id)}
                </select>
            </label>
            <label>
                Creative technique
                <select name="creative_technique_id">
                    <option value="">Any technique</option>
                    {_selected_options(creative_techniques, filters.creative_technique_id)}
                </select>
            </label>
            <label>
                Feedback
                <select name="feedback_action">
                    <option value="">Any feedback</option>
                    {_feedback_action_options(filters.feedback_action)}
                </select>
            </label>
        </div>
        <button type="submit">Search ideas</button>
    </form>
    """


def _selected_options(items: list[sqlite3.Row], selected_id: int | None) -> str:
    return "\n".join(
        (
            f'<option value="{item["id"]}" selected>{escape(item["name"])}</option>'
            if selected_id == int(item["id"])
            else f'<option value="{item["id"]}">{escape(item["name"])}</option>'
        )
        for item in items
    )


def _feedback_action_options(selected_action: str) -> str:
    return "\n".join(
        (
            f'<option value="{escape(action)}" selected>{escape(_label(action))}</option>'
            if selected_action == action
            else f'<option value="{escape(action)}">{escape(_label(action))}</option>'
        )
        for action in FEEDBACK_ACTIONS
    )


def _memory_form_html() -> str:
    return """
    <form method="post" action="/memories">
        <label>
            Memory type
            <input name="memory_type" placeholder="daily summary" required>
        </label>
        <label>
            Title
            <input name="title" required>
        </label>
        <label>
            Content
            <textarea name="content" required></textarea>
        </label>
        <button type="submit">Save memory</button>
    </form>
    """


def _memories_html(memories: list[sqlite3.Row]) -> str:
    if not memories:
        return """
        <section class="empty" aria-label="No memories">
            <p>No memory summaries have been created yet.</p>
        </section>
        """

    items = "\n".join(
        f"""
        <article class="memory-card">
            <h3>{escape(memory["title"])}</h3>
            <p class="meta">{escape(memory["memory_type"])} / {escape(memory["created_at"])}</p>
            <p>{escape(memory["content"])}</p>
        </article>
        """
        for memory in memories
    )
    return f"""
    <section class="memory-list" aria-label="Memory summaries">
        {items}
    </section>
    """


def _critique_html(critique: sqlite3.Row | None) -> str:
    if critique is None:
        return ""

    score_items = [
        f'<span class="score">{escape(name)}: {critique[name]}</span>'
        for name in SCORE_DIMENSIONS
        if critique[name] is not None
    ]
    scores_html = "".join(score_items)
    raw_preview = critique["raw_output"].strip()[:500]
    return f"""
    <section class="critique" aria-label="Latest critique">
        <strong>{escape(critique["critic_name"])}</strong>
        <div class="scores">{scores_html}</div>
        <p>{escape(raw_preview)}</p>
    </section>
    """


def _ideas_html(
    ideas: list[sqlite3.Row],
    critiques: dict[int, sqlite3.Row],
    feedback_events: dict[int, list[sqlite3.Row]],
) -> str:
    return "\n".join(
        f"""
        <article class="idea-card">
            <h3>{escape(idea["title"])}</h3>
            {_idea_body_html(idea)}
            <p class="meta">
                {escape(idea["portfolio_name"] or "")} /
                {escape(idea["idea_agent_name"] or "")} /
                {escape(idea["creative_technique_name"] or "")}
            </p>
            {_critique_html(critiques.get(idea["id"]))}
            {_feedback_events_html(feedback_events.get(int(idea["id"]), []))}
            <form class="inline-form" method="post" action="/ideas/{idea["id"]}/critique">
                <button type="submit">Run brutal critique</button>
            </form>
            {_feedback_controls_html(int(idea["id"]))}
        </article>
        """
        for idea in ideas
    )


def _feedback_controls_html(idea_id: int) -> str:
    action_buttons = "\n".join(
        f'<button type="submit" name="action" value="{escape(action)}">{escape(_label(action))}</button>'
        for action in FEEDBACK_ACTIONS
    )
    reason_inputs = "\n".join(
        f"""
        <label class="chip">
            <input type="checkbox" name="reason_chips" value="{escape(reason)}">
            {escape(reason)}
        </label>
        """
        for reason in REASON_CHIPS
    )
    return f"""
    <form class="feedback-controls" method="post" action="/ideas/{idea_id}/feedback">
        <div class="feedback-actions" aria-label="Feedback actions">
            {action_buttons}
        </div>
        <div class="chips" aria-label="Reason chips">
            {reason_inputs}
        </div>
    </form>
    """


def _feedback_events_html(events: list[sqlite3.Row]) -> str:
    if not events:
        return ""

    items = "\n".join(
        f"<li>{escape(_label(event['action']))}{_reason_suffix(event)}</li>"
        for event in events[:5]
    )
    return f"""
    <section class="feedback-events" aria-label="Feedback events">
        <strong>Feedback</strong>
        <ul>{items}</ul>
    </section>
    """


def _reason_suffix(event: sqlite3.Row) -> str:
    reasons = decode_reason_chips(event)
    if not reasons:
        return ""

    return f" - {escape(', '.join(reasons))}"


def _label(value: str) -> str:
    return value.replace("_", " ")


def _idea_body_html(idea: sqlite3.Row) -> str:
    return _structured_idea_html(
        summary=idea["summary"] or idea["body"],
        target_buyer=idea["target_buyer"],
        first_validation_step=idea["first_validation_step"],
        why_it_fits=idea["why_it_fits"],
    )


def _generated_idea_body_html(idea) -> str:
    return _structured_idea_html(
        summary=idea.summary or idea.body,
        target_buyer=idea.target_buyer,
        first_validation_step=idea.first_validation_step,
        why_it_fits=idea.why_it_fits,
    )


def _structured_idea_html(
    *,
    summary: str,
    target_buyer: str,
    first_validation_step: str,
    why_it_fits: str,
) -> str:
    fields = [
        ("Summary", summary),
        ("Target buyer", target_buyer),
        ("First validation step", first_validation_step),
        ("Why it fits", why_it_fits),
    ]
    return "\n".join(
        f"<p><strong>{label}:</strong> {escape(value)}</p>"
        for label, value in fields
        if value.strip()
    )


app = create_app()
