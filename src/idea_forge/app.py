"""FastAPI application entrypoint."""

from html import escape
from pathlib import Path
from urllib.parse import parse_qs
import sqlite3

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from idea_forge.database import initialize_database, open_database
from idea_forge.idea_generation import (
    IdeaGenerationClient,
    generate_and_store_ideas,
    list_ideas,
    list_reference_rows,
)
from idea_forge.ollama_client import OllamaClient
from idea_forge.prompts import PromptRenderer


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
.empty {
    border: 1px solid #d9dce1;
    border-radius: 6px;
    padding: 18px;
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
    def list_ideas_page() -> HTMLResponse:
        with open_app_database() as connection:
            ideas = list_ideas(connection)

        if not ideas:
            return page(
                "Ideas",
                """
                <h2>Ideas</h2>
                <section class="empty" aria-label="No ideas">
                    <p>No ideas have been generated or stored yet.</p>
                    <p class="muted">Use the generate form to create the first stored idea.</p>
                </section>
                """,
            )

        ideas_html = "\n".join(
            f"""
            <article class="idea-card">
                <h3>{escape(idea["title"])}</h3>
                <p>{escape(idea["body"])}</p>
                <p class="meta">
                    {escape(idea["portfolio_name"] or "")} /
                    {escape(idea["idea_agent_name"] or "")} /
                    {escape(idea["creative_technique_name"] or "")}
                </p>
            </article>
            """
            for idea in ideas
        )
        return page(
            "Ideas",
            f"""
            <h2>Ideas</h2>
            <section class="idea-list" aria-label="Stored ideas">
{ideas_html}
            </section>
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
                <p>{escape(idea.body)}</p>
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


app = create_app()
