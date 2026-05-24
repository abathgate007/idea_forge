"""FastAPI application entrypoint."""

from html import escape

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from idea_forge.database import (
    DEFAULT_CREATIVE_TECHNIQUES,
    DEFAULT_IDEA_AGENTS,
    DEFAULT_PORTFOLIOS,
)


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
.button {
    background: #0b57d0;
    border-radius: 4px;
    color: #fff;
    display: inline-block;
    padding: 10px 14px;
    text-decoration: none;
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
    background: #5f6368;
    border: 0;
    border-radius: 4px;
    color: #fff;
    font: inherit;
    padding: 10px 14px;
    width: fit-content;
}
.empty {
    border: 1px solid #d9dce1;
    border-radius: 6px;
    padding: 18px;
}
"""


def page(title: str, body: str) -> HTMLResponse:
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
    return HTMLResponse(html)


def options(items: tuple[tuple[str, str], ...]) -> str:
    """Render option tags for reference data tuples."""
    return "\n".join(
        f'            <option value="{escape(name)}">{escape(name)}</option>'
        for name, _description in items
    )


def create_app() -> FastAPI:
    """Create the Idea Forge FastAPI application."""
    app = FastAPI(title="Idea Forge")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def home() -> HTMLResponse:
        return page(
            "Home",
            """
            <h2>Local idea foundry</h2>
            <p class="muted">Capture seeds, browse stored ideas, and prepare generation inputs.</p>
            <p class="muted">Ollama generation and critic scoring are not wired in yet.</p>
            <p class="actions">
                <a class="button" href="/ideas/generate">Open generate form</a>
            </p>
            """,
        )

    @app.get("/ideas", response_class=HTMLResponse)
    def list_ideas() -> HTMLResponse:
        return page(
            "Ideas",
            """
            <h2>Ideas</h2>
            <section class="empty" aria-label="No ideas">
                <p>No ideas have been generated or stored yet.</p>
                <p class="muted">Idea persistence will be connected in a later milestone.</p>
            </section>
            """,
        )

    @app.get("/ideas/generate", response_class=HTMLResponse)
    def generate_idea_form() -> HTMLResponse:
        return page(
            "Generate Idea",
            f"""
            <h2>Generate idea</h2>
            <p class="muted">This form is a shell only. It does not call Ollama or store ideas.</p>
            <form method="get" action="/ideas/generate">
                <label>
                    Seed
                    <textarea name="seed" placeholder="Describe the starting point"></textarea>
                </label>
                <label>
                    Portfolio
                    <select name="portfolio">
{options(DEFAULT_PORTFOLIOS)}
                    </select>
                </label>
                <label>
                    Idea agent
                    <select name="idea_agent">
{options(DEFAULT_IDEA_AGENTS)}
                    </select>
                </label>
                <label>
                    Creative technique
                    <select name="creative_technique">
{options(DEFAULT_CREATIVE_TECHNIQUES)}
                    </select>
                </label>
                <button type="submit" disabled>Generation not available yet</button>
            </form>
            """,
        )

    return app


app = create_app()
