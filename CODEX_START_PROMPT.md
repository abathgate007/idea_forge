# Codex Start Prompt

Use this prompt when starting the Idea Forge project in Codex CLI.

```text
Read AGENTS.md, PRODUCT_BRIEF.md, ROADMAP.md, AUTONOMY_POLICY.md, and docs/adr/0001-local-first-ollama-fastapi-sqlite.md.

Use the Daily PR Workflow.

Important clarification:
- Codex CLI is the implementation agent.
- Ollama is the runtime model provider for Idea Forge idea generation.
- Do not build a Python autonomous coding agent.
- Do not implement self-improvement features yet.

Implement Milestone 0 and Milestone 1 only if they are not already complete.

Create or update:
- AGENTS.md
- PRODUCT_BRIEF.md
- ROADMAP.md
- AUTONOMY_POLICY.md
- README.md
- docs/adr/0001-local-first-ollama-fastapi-sqlite.md
- pyproject.toml
- src/idea_forge/__init__.py
- tests/test_project_scaffold.py

Do not build the FastAPI app yet unless the roadmap says Milestone 1 is already complete.

Run pytest.
Commit.
Push.
Create a GitHub PR into main.
Do not merge.

Final response must include:
- feature branches created
- daily branch name
- commit hash
- files changed
- tests run
- test result
- PR URL
- anything requiring human review
```
