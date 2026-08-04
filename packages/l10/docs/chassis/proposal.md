# Jake Agent Production Chassis — Phase 1 (Chassis)

## Why
Jake's team operates as scattered AGENTS and skills across Hermes, Claude Code,
Codex, and cron jobs. There is no sealed, versioned, typed execution chassis
that enforces H=(E,T,C,S,L,V) for every production run, persists state across
process failure, gates external writes by side-effect class, and requires
independent verification before declaring completion.

The model is the engine; the chassis is the production guarantee. This phase
builds the irreducible minimum: harness registry, typed run packet, workflow
state machine, durable state store, and tool registry with side-effect
classification.

## What Changes
- **New module** `rig_l10/src/chassis/` with five core components
- **New tests** in `tests/test_chassis.py` (TDD, golden-run replay)
- **New BDD spec** in `docs/chassis/spec.md` (Gherkin fenced acceptance criteria)
- **No breaking changes** to existing L10 modules

## Capabilities
- **New**: `harness-registry` — seald, versioned harness H=(E,T,C,S,L,V)
- **New**: `run-packet` — typed, hash-chained execution packet
- **New**: `workflow-fsm` — state machine with typed transitions + failure states
- **New**: `state-store` — JSON+file durable state with checkpoint/resume
- **New**: `tool-registry` — tool allowlist with side-effect classification

## Impact
- New directory: `rig-l10/src/chassis/`
- New test file: `rig-l10/tests/test_chassis.py`
- New docs: `rig-l10/docs/chassis/`
- Imports from existing `rig_l10.src.common` (ProofPacket, BMS, GEVRole)
