# Idea Forge

Idea Forge is a local-first idea generation web application.

It uses:

- Codex CLI to build and modify the codebase
- Ollama as the local runtime model provider for repeated idea generation
- FastAPI for the backend
- SQLite for local persistence
- pytest for tests
- a simple local browser UI for the MVP

## Status

This repository is in MVP development. Manual local idea generation is available
through the browser UI when Ollama is running.

## Core Principle

Codex builds the product. Ollama powers the product.

Do not build a custom autonomous coding agent in the MVP. Do not implement self-improvement features yet.

## Planned MVP

The MVP will support:

- seeds
- portfolios
- idea agents/personas
- creative techniques
- Ollama-powered idea generation
- critic scoring
- stored ideas
- feedback controls
- search
- external prompt files

## Local Assumptions

- Windows 11 or equivalent local development environment
- Python 3.11+
- Ollama running locally
- Ollama API at `http://localhost:11434`
- initial model configurable, defaulting to `qwen2.5-coder:7b`

## Ollama Configuration

Idea Forge uses Ollama's local HTTP API through a small client abstraction. The
defaults are:

- base URL: `http://localhost:11434`
- model: `qwen2.5-coder:7b`

Override them with environment variables when needed:

```powershell
$env:IDEA_FORGE_OLLAMA_BASE_URL = "http://localhost:11434"
$env:IDEA_FORGE_OLLAMA_MODEL = "qwen2.5-coder:7b"
```

The client can also be configured directly in Python:

```python
from idea_forge.ollama_client import OllamaClient

client = OllamaClient(base_url="http://localhost:11434", model="qwen2.5-coder:7b")
text = client.generate("Give me one concrete local-first product idea.")
```

Tests use fakes and do not require Ollama to be installed or running.

## Prompt Files

Model prompts live in `prompts/` as plain markdown files. Render them with
explicit variables:

```python
from idea_forge.prompts import render_prompt

prompt = render_prompt(
    "idea_generation.md",
    {
        "seed": "local business pain",
        "portfolio": "Money now",
        "idea_agent": "Money-Hungry Operator",
        "creative_technique": "Tiny Wedge",
        "novelty_mode": "practical",
        "context": "Focus on quick validation.",
        "anti_sludge_rules": "Avoid generic dashboards.",
    },
)
```

## Development

Install dependencies once the Python scaffold exists:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run tests:

```powershell
python -m pytest
```

Run the local FastAPI app:

```powershell
uvicorn idea_forge.app:app --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Open the manual generation form at:

```text
http://127.0.0.1:8000/ideas/generate
```

The form stores generated ideas and generation run metadata in the local SQLite
database at `data/idea_forge.sqlite`. Tests use temporary databases and fake
Ollama clients, so they do not require live Ollama.

## Repository Control Docs

- `AGENTS.md`: Codex operating rules
- `PRODUCT_BRIEF.md`: product vision and MVP scope
- `ROADMAP.md`: implementation milestones
- `AUTONOMY_POLICY.md`: autonomy and safety boundaries
- `docs/adr/`: architecture decision records
