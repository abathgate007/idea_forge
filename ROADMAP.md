# Idea Forge Roadmap

This roadmap is designed for Codex CLI to implement in small, reviewable increments using the Daily PR Workflow.

## Milestone 0: Project Control Documents

Goal: Establish repository operating rules and product direction.

Deliverables:

- `AGENTS.md`
- `PRODUCT_BRIEF.md`
- `ROADMAP.md`
- `AUTONOMY_POLICY.md`
- `docs/adr/0001-local-first-ollama-fastapi-sqlite.md`

Definition of done:

- Control documents exist.
- Daily PR Workflow is documented.
- Codex CLI / Ollama responsibilities are clearly separated.
- Self-improvement is explicitly deferred.
- Protected files are listed.

## Milestone 1: Project Scaffold

Goal: Create a minimal Python project skeleton.

Deliverables:

- `pyproject.toml`
- `src/idea_forge/__init__.py`
- `tests/test_project_scaffold.py`
- basic pytest configuration
- README setup instructions

Definition of done:

- `python -m pytest` passes.
- Project imports cleanly.
- No app behavior is implemented yet.

## Milestone 2: FastAPI App Skeleton

Goal: Create a runnable local FastAPI app.

Deliverables:

- FastAPI app factory or app module
- `/health` endpoint
- local run instructions
- tests for health endpoint

Definition of done:

- app starts locally
- health endpoint returns expected JSON
- tests pass

## Milestone 3: SQLite Persistence

Goal: Add basic SQLite database setup.

Deliverables:

- database connection layer
- initialization function
- migrations or schema initialization approach suitable for MVP
- tables for initial core entities

Initial tables:

- ideas
- seeds
- portfolios
- idea_agents
- creative_techniques
- generation_runs

Definition of done:

- database initializes locally
- tests use isolated temporary databases
- schema tests pass

## Milestone 4: Seed Data and Reference Tables

Goal: Add initial portfolios, agents, and creative techniques.

Deliverables:

- default portfolios
- default idea agents
- default creative techniques
- seed loading logic
- tests for default data

Definition of done:

- default data can be loaded idempotently
- tests verify required default entries exist

## Milestone 5: Simple Browser UI

Goal: Add a minimal local UI.

Deliverables:

- home page
- list ideas page
- generate idea form shell
- simple static CSS if needed

Definition of done:

- local browser can access UI
- UI does not require a frontend framework
- tests cover basic route behavior where practical

## Milestone 6: Ollama Client

Goal: Add a clean client abstraction for Ollama.

Deliverables:

- configurable base URL
- configurable model name
- generate method
- timeout handling
- clear error handling
- tests using mocks/fakes, not live Ollama

Definition of done:

- client behavior is tested without requiring Ollama
- live Ollama can be used manually when available

## Milestone 7: External Prompt Files

Goal: Move model prompts into external files.

Deliverables:

- `prompts/idea_generation.md`
- `prompts/critic.md`
- prompt rendering utility
- tests for prompt rendering structure

Definition of done:

- prompts are not hardcoded in business logic
- prompt inputs are explicit
- tests do not depend on exact LLM prose

## Milestone 8: Manual Idea Generation

Goal: Generate and store ideas.

Deliverables:

- UI form selects seed, portfolio, idea agent, and creative technique
- backend assembles prompt
- backend calls Ollama
- generated ideas are stored
- generation run metadata is stored

Definition of done:

- user can generate ideas locally
- ideas appear in stored list
- tests cover persistence and prompt assembly
- live model behavior is manually testable

## Milestone 9: Critic Scoring

Goal: Add one critic pass.

Deliverables:

- Brutal Critic prompt
- scoring fields
- critique persistence
- UI display of critique result

Definition of done:

- ideas can be critiqued
- scores are stored
- tests validate critique schema handling

## Milestone 10: Feedback Controls

Goal: Add basic human feedback.

Deliverables:

- thumbs up
- thumbs down
- star
- reject
- reason chips
- feedback_events table

Definition of done:

- feedback can be recorded
- feedback appears in idea detail
- tests cover feedback persistence

## Milestone 11: Search

Goal: Add basic idea search.

Deliverables:

- keyword search
- filters by portfolio, agent, technique, feedback status
- simple UI search form

Definition of done:

- stored ideas can be searched
- tests cover search behavior

## Milestone 12: Memory Summaries

Goal: Add simple memory tables and manually triggered summaries.

Deliverables:

- memories table
- memory type field
- manually created summaries
- optional prompt support for summarizing selected ideas

Definition of done:

- memory records can be created and read
- memory can be included in future prompt assembly

## Deferred: Self-Improvement

Self-improvement features are intentionally deferred.

Deferred features include:

- self-improvement idea queue
- automatic code task generation
- custom Python autonomous coding agent
- automatic branch creation from Idea Forge
- automatic PR creation from Idea Forge
- autonomous implementation of product improvements

These may be reconsidered after the core app is useful and stable.
