# Contributing

## Bar
1. Public-boundary safe (no PII, secrets, client dumps, ToS-risk bots).
2. `pytest -q` and `ruff check .` must pass in a fresh venv with
   `pip install -e '.[dev]'` from `packages/l10`.
3. README claims must match runnable commands.
4. Prefer small diffs with proof over large narrative refactors.

## Flow
1. Fork or branch from `main`.
2. Add or adjust tests for the change.
3. Run `pytest -q --cov` and `ruff check .` from `packages/l10`.
4. Open a PR with: what changed, how verified, boundary impact.
