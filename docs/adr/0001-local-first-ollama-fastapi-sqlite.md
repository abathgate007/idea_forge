# ADR 0001: Local-First Ollama + FastAPI + SQLite

## Status

Accepted.

## Context

Idea Forge is intended to run locally and generate many ideas, critiques, variants, and summaries. Repeated model calls are expected. Using paid cloud model APIs for routine generation could become unnecessarily expensive.

The project also benefits from local privacy because some ideas may involve personal plans, business strategy, writing projects, security ideas, and real estate marketing concepts.

## Decision

Idea Forge will be built as a local-first application using:

- FastAPI for the backend
- SQLite for persistence
- a simple local browser UI for the MVP
- Ollama as the local runtime model provider
- pytest for testing

Codex CLI will be used to implement the codebase.

Ollama will be used inside the product for idea generation, critique, scoring, and summarization.

The MVP will not include a custom autonomous coding agent or self-improvement system.

## Consequences

Benefits:

- low marginal cost for repeated idea generation
- local privacy
- simple deployment model
- easy local development
- straightforward persistence with SQLite
- clean separation between implementation agent and runtime model provider

Tradeoffs:

- local model quality may vary by installed model
- user must have Ollama installed and running
- performance depends on local hardware
- cloud sync and multi-user support are not included in the MVP
- model output must be treated as non-deterministic

## Implementation Notes

Configuration should allow:

- Ollama base URL
- Ollama model name
- request timeout
- optional future model switching

Tests should mock or fake Ollama calls by default. Tests should not require live Ollama unless explicitly marked as integration tests.

Prompt files should live outside business logic, likely under `prompts/`.

## Deferred Decisions

Deferred until after MVP:

- background generation jobs
- model benchmarking
- semantic search or embeddings
- vector database
- custom autonomous coding agent
- self-improvement workflow
- cloud deployment
- authentication
