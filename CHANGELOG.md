# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-19

### Added
- `chassis/tools.py`: tool registry with six side-effect classes and an
  approval gate (spec requirement 5).
- `chassis/policy.py`: eight-gate policy engine (spec requirement 7).
- `chassis/gev.py`: generator / evaluator / verifier role separation
  (spec requirement 6).
- `docs/glossary.md`: internal names translated to plain English.
- `tests/test_packaging.py` asserting packaging invariants.
- `CODE_OF_CONDUCT.md`, issue templates, pull request template,
  Dependabot config, and a CI workflow that runs the full test suite
  with coverage and ruff.

### Changed
- `chassis/fsm.py`: COMMIT accepts CLOSED as the spec requires, and
  failure states are reachable from any non-terminal state.
- `chassis/store.py`: `get_run_state` reports `budget_remaining_tokens`.
- `pydantic` is declared as a dependency (the chassis imports it).
- Version 0.1.1 to 0.2.0; requires-python 3.10; README rewritten with
  the measured 72-test count (the old claim was 38); the l10 README
  rewritten; ruff config added; unused imports removed across the
  sources and tests.

### Fixed
- `certainty_engine/pbt.py`: samples_tested no longer reads a leaked
  loop variable (unbound when max_examples is 0).
- `tests/test_chassis.py`: a missing StateTransitionError import and a
  bare-Exception assertion.

## [0.1.1] - 2026-08-04

### Added
- Initial public core: certainty engine, cognition stack, nocturne
  runner, agent factory, and the chassis runtime (harness registry,
  run packets, workflow state machine, state store).

[0.2.0]: https://github.com/mrodgersjs-web/jake-studio/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/mrodgersjs-web/jake-studio/releases/tag/v0.1.1
