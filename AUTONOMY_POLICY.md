# Autonomy Policy

## Purpose

This policy defines what Codex CLI and future automation may and may not do in the Idea Forge repository.

## Current Autonomy Level

Idea Forge currently uses Codex CLI as the implementation agent.

Codex may:

- inspect the repository
- create feature branches
- edit files relevant to approved tasks
- run tests
- stage relevant files
- commit changes
- push branches
- create GitHub pull requests

Codex may not:

- merge pull requests
- commit directly to `main`
- force-push
- delete remote branches
- modify secrets
- modify protected files without explicit approval
- build self-improvement features unless explicitly approved in a future milestone

## Daily PR Autonomy

Codex may use the Daily PR Workflow:

1. Create one or more `codex/feature-<short-name>` branches.
2. Implement approved features.
3. Run relevant tests.
4. Commit each feature.
5. Push feature branches.
6. Create or update a `codex/daily-YYYY-MM-DD` integration branch.
7. Merge completed feature branches into the daily branch.
8. Run the full test suite.
9. Push the daily branch.
10. Create one PR from the daily branch into `main`.

Codex must stop after creating the PR.

Only a human may merge into `main`.

## Protected Files

Codex must not modify these without explicit approval:

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

## Secret Handling

Codex must not:

- read secrets unless explicitly authorized
- print secrets
- write secrets into source code
- copy secrets into reports
- include secrets in PR descriptions
- include secrets in test output
- commit secrets

## Database Handling

Local databases are treated as runtime artifacts.

Codex must not commit:

- SQLite database files
- SQLite WAL files
- SQLite SHM files
- exported personal context
- generated private user data

Schema files, migrations, and seed data may be committed.

## CI/CD Handling

Codex must not modify GitHub Actions or other CI/CD configuration unless the task explicitly requests it.

Codex must never modify CI/CD secrets.

## Self-Improvement Policy

Self-improvement is deferred from the MVP.

Idea Forge may eventually suggest improvements to itself, but the MVP must not:

- automatically generate implementation tasks for itself
- automatically invoke Codex
- automatically modify its own repository
- automatically create branches or PRs
- merge its own changes

Any future self-improvement feature must require explicit human approval and a revised autonomy policy.

## Failure Behavior

If Codex cannot complete a task safely, it should stop and report:

- what it attempted
- what failed
- files changed
- tests run
- current branch
- current Git status
- suggested recovery steps

Codex should not keep making broad changes to escape a failure.

## Human Review

Human review is required before:

- merging to `main`
- changing protected files
- adding new dependencies
- modifying CI/CD
- introducing background automation
- changing the autonomy policy
- implementing self-improvement features
