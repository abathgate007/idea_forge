# Agent Instructions for Idea Forge

These instructions apply to Codex CLI and any coding agent working in this repository.

## Project Summary

Idea Forge is a local-first idea generation web application.

Important distinction:

- Codex CLI is the implementation agent that builds and modifies this codebase.
- Ollama is the runtime model provider used by Idea Forge to generate, critique, and score ideas.
- Do not build a custom autonomous coding agent in the MVP.
- Do not implement self-improvement or self-modifying features in the MVP.

## Technology Direction

Use:

- Python
- FastAPI
- SQLite
- pytest
- Simple local browser UI
- Ollama API at `http://localhost:11434`
- Configurable Ollama model, defaulting initially to `qwen2.5-coder:7b`

Do not use unless explicitly requested:

- Docker
- Cloud databases
- Cloud model APIs
- Complex frontend frameworks
- Background job infrastructure
- Authentication systems
- Deployment tooling

## Daily PR Workflow

This project uses a daily integration PR workflow.

Codex may create multiple feature branches during the day using this pattern:

- `codex/feature-<short-name>`

Codex may commit and push those feature branches.

At the end of a work batch, Codex should create or update a daily integration branch using this pattern:

- `codex/daily-YYYY-MM-DD`

The daily branch should contain the completed feature work for that day.

Codex may create one GitHub pull request from the daily branch into `main`.

Codex must not merge the pull request.

Codex must not commit directly to `main`.

Codex must not force-push.

Codex must not delete remote branches.

Codex must not modify secrets, credentials, tokens, private keys, `.env` files, local databases, or CI/CD secrets.

Codex must stage only files relevant to the task.

Codex must run relevant tests before committing.

Codex must summarize:

- daily branch name
- feature branches included
- commits included
- files changed
- tests run
- test result
- PR URL
- known risks or review notes

## Branch Rules

- `main` is the stable, human-approved branch.
- `codex/feature-<short-name>` branches are for individual feature/task work.
- `codex/daily-YYYY-MM-DD` branches are integration branches for daily review.
- Pull requests should target `main` unless explicitly instructed otherwise.
- Never merge a PR automatically.
- Never force-push.
- Never rewrite shared history.

## Protected Files and Paths

Do not modify these without explicit human approval:

- `.env`
- `.env.*`
- `*.pem`
- `*.key`
- `*.p12`
- `*.pfx`
- `data/*.db`
- `data/*.sqlite`
- `data/*.sqlite-shm`
- `data/*.sqlite-wal`
- `.github/workflows/*`
- `AUTONOMY_POLICY.md`
- `.gitignore`
- `secrets/*`
- `auth/*`
- `personal_context/*`
- `config/secrets*`
- `credentials*`
- `tokens*`

Do not print secrets to logs, reports, PR descriptions, test output, or generated documentation.

## Coding Rules

- Inspect before editing.
- Keep diffs small and focused.
- Do not modify unrelated files.
- Do not reformat files unless explicitly requested.
- Do not add dependencies without a clear reason.
- Prefer simple, boring, testable code.
- Prefer explicit error handling over silent failure.
- Keep model calls behind a clean Ollama client abstraction.
- Keep prompts in external prompt files, not hardcoded inside business logic.
- Avoid brittle tests that depend on exact LLM prose.

## Testing Rules

Use pytest for Python tests.

Tests should focus on:

- data validation
- database logic
- API behavior
- prompt assembly structure
- Ollama client behavior using mocks/fakes
- error handling
- non-LLM deterministic behavior

Do not write brittle tests that expect deterministic LLM-generated prose.

When model output must be tested, test structure and schema instead of exact wording.

## MVP Scope Rules

MVP includes:

- local FastAPI app
- SQLite persistence
- basic local UI
- seeds
- portfolios
- idea agents/personas
- creative techniques
- Ollama-powered idea generation
- critic scoring
- feedback controls
- search
- external prompt files
- tests

MVP excludes:

- autonomous self-improvement
- custom Python coding agent
- automatic code modification by Idea Forge
- scheduled autonomous background idea generation
- multi-user authentication
- cloud sync
- production deployment
- payment systems

## Definition of Done

A task is complete only when:

- the requested change is implemented
- tests pass, or failures are clearly explained
- the diff is focused and reviewable
- no protected files were modified without approval
- no secrets were touched or printed
- documentation is updated when behavior changes
- a PR is created when using the Daily PR Workflow
