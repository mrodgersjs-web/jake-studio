# Jake PAI Openclaw

Merged Jake PAI, Persona OS, OpenClaw, Hermes, founder intelligence, and mission-control surface.

This repository is now the canonical source-copy merge for the requested capability family. The old individual GitHub repos were copied into `sources/<repo>/` before cleanup.

## Merged Sources

| Source repo | Commit | Copied files |
| --- | ---: | ---: |
| `persona-os` | `1cd58b35f0f7` | 125 |
| `jake-openclaw` | `ee3f40811f55` | 9554 |
| `jakestudio-brain` | `1946bc18b119` | 444 |
| `jake-pai-web` | `3251340701be` | 5 |
| `jake-pai` | `e3b4929d2647` | 279 |
| `jake-mission-control` | `7a741e7375f9` | 6158 |
| `jake-hermes-portable` | `391b56fb859c` | 1123 |
| `founder-intelligence-os` | `7de20dedd4ce` | 590 |
| `founder-command-center` | `53f0687c6984` | 83 |
| `apex-ventures-hq` | `21d7ce9d6b30` | 7 |

## CLI

```bash
cd agent-harness
python3 -m pip install -e .
cli-anything-jake-pai info
cli-anything-jake-pai list
cli-anything-jake-pai scan
cli-anything-jake-pai merge-plan
cli-anything-jake-pai smoke
```

Execution commands remain dry-run by default unless `--execute` is supplied.

## RIG V10 readiness design (planning-only)

### V10 product promise
- Product-grade deterministic suite shell for `jake-pai` that supports:
  - local operator CLI workflows,
  - agent-safe planning/proof workflows,
  - future MCP exposure for repo inventory/search/merge-plan/smoke surfaces.

### CLI surface and first deterministic local smoke command
- Existing CLI surface: `info`, `list`, `scan`, `repo *`, `search`, `merge-plan`, `run`, `doctor`, state commands (`select`, `undo`, `redo`).
- First deterministic local smoke command:
  - `cli-anything-jake-pai --json smoke`
  - reports manifest load, repo count, missing local source directories, and `ok|warning` status.
  - no network calls, no secrets, no execution side effects.

### MCP surface (intentionally deferred)
- Deferred in this repo for now (no MCP server/client files yet).
- Planned initial MCP mapping when enabled:
  - tools: `suite_info`, `suite_scan`, `merge_plan`, `smoke`, `repo_info`, `repo_scripts`, `search`
  - resources: `suite_manifest`, `repo_index`, `merge_map`
  - prompts: deterministic triage/readiness prompts only.

### Agent roles, model routing, and quality gates
- Roles:
  - Planner: converts issues into deterministic proof steps.
  - Reviewer: validates safety boundaries and requirement coverage.
  - Fixer: applies minimal surgical code/doc changes.
  - QA: executes smoke/tests and reports proof artifacts.
- Model routing expectation:
  - deterministic checks and command routing remain non-agentic/local first,
  - agentic review/planning only augments, never replaces deterministic proofs.
- Quality gates:
  - tests must pass locally for touched scope,
  - smoke command output collected as proof,
  - no deploy/publish/schedule activation from readiness planning issues.

### Weekly improvement loop (must-not-run rules)
- Weekly loop behavior:
  - run deterministic smoke/tests,
  - review blockers and readiness score deltas,
  - propose minimal PR-sized improvements with proof commands.
- Must never run without explicit human approval:
  - deployment/publishing,
  - external messaging or schedule activation,
  - secret/certificate export,
  - destructive cleanup/reset of user work.

### Current blockers / missing pieces
- Missing MCP implementation files (server/client/tool schemas).
- Missing dedicated quality-readiness docs/checklists beyond this baseline section.
- Missing readiness-focused tests beyond CLI harness scope.
- Missing explicit proof artifact conventions (where to store smoke/test outputs).
- Missing declared API contracts for any future remote integrations.
- Missing required secrets are intentionally not requested at planning stage.

### Proof paths and commands (planning proof, not final PASS)
- Harness tests:
  - `cd agent-harness && PYTHONPATH=. python3 -m pytest -q`
- Deterministic smoke:
  - `cd agent-harness && PYTHONPATH=. python3 -m cli_anything.jake_pai_openclaw --json smoke`
<!-- AGENTFORGE:WORKFLOWS START -->
## AgentForge Workflows

**Repo maturity:** `44.74 / 100`

### 10x Plan


**Visual workflow designer:** [.agentforge/workflows.html](.agentforge/workflows.html)

### Workflows (editable)

> These workflows live in the README and are editable here. Each is a `WorkflowDoc` (`name` · BMS mode · ordered steps) that round-trips losslessly with the visual designer and the agent IR.

#### 1. chief_of_staff/weekly_priority_set  `A1`

_A1 · Python-only (deterministic)_

1. cs-brief
2. cs-scheduler
3. cs-router

#### 2. coding/full_pipeline  `A2`

_A2 · Hybrid (schema-constrained LLM)_
