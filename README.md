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

This repository is being scaffolded. The MVP is not complete yet.

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

## Repository Control Docs

- `AGENTS.md`: Codex operating rules
- `PRODUCT_BRIEF.md`: product vision and MVP scope
- `ROADMAP.md`: implementation milestones
- `AUTONOMY_POLICY.md`: autonomy and safety boundaries
- `docs/adr/`: architecture decision records
