# jake-studio

A local-first operator layer that routes agent work across builders, verifiers,
and verification gates. The `rig-l10` harness (`packages/l10`) does the
certainty checks: a builder produces work, a read-only verifier re-checks it,
and a completion claim is refused without evidence. Internal names are
translated in `docs/glossary.md`.

## Layout

- `packages/l10` - the rig-l10 harness package (`src/`, `tests/`, `rules/`,
  `proofpackets/`, its own `pyproject.toml`). This is where the code lives.
- `packages/operator` - operator-facing helpers around the harness.
- `mcp/` - the MCP server surface. `examples/` - runnable examples exercised
  by the test suite. `docs/` - design notes and the glossary.
- `scripts/smoke.sh` - the one-line install-and-smoke check CI runs.

## Setup and test (exact commands)

```bash
cd packages/l10
python3 -m pip install -e ".[test]"
pytest -q tests
```

End-to-end check from the repo root (what CI runs):

```bash
bash scripts/smoke.sh
```

Coverage: `cd packages/l10 && pytest -q --cov`.

## Lint

```bash
ruff check .
```

Must be clean before a PR, together with `pytest -q`.

## Conventions

- Conventional commit subjects (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- Every change ships a test that can fail; a completion claim needs evidence,
  not an adjective.
- No secrets, tokens or credentials in tracked files. No machine-specific
  paths (`/Users/...`, `~/Developer/...`) in tracked files.
- Numbers in docs and README must come from a command you ran; quote the
  command, not a remembered figure. If a number changes, re-run the command.
