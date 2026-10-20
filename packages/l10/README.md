# rig-l10 (the L10 harness)

A Python toolkit for running agent work with verification built in: property
testing, a refuter, a council of models, an overnight batch runner, and a
deterministic agent factory. The name "L10" is internal shorthand; see the
[glossary](../../docs/glossary.md) for plain-English names.

**Status:** maintained | **Tests:** 72 passing | **Module:** `packages/l10/src/`

## Quick start

```bash
pip install -e '.[dev]'
pytest -q            # the 72-test suite
rig-l10 doctor       # check the modules load
```

## Modules (plain English)

- `certainty_engine` | property-based testing, a refuter, and a small
  proof kernel for checking claims about code
- `cognition_stack` | a taste scorer, a multi-model council, adherence and
  strategy helpers, and a tribal-knowledge scraper
- `nocturne` | overnight batch runner: the nightly self-improvement loop
- `agent_factory` | stamps out agent definitions deterministically
- `chassis` | the production runtime: sealed harnesses, typed run packets,
  a workflow state machine, a durable state store, a tool registry with
  side-effect gates, a policy engine, and role separation

## Install

```bash
cd packages/l10
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
```

## Development

```bash
pytest -q --cov
ruff check .
```

## License

MIT.
