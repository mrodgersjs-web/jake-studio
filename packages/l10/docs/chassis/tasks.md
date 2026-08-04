# Phase 1 Tasks — Jake Agent Production Chassis

## 1. Setup
- [x] 1.1 Create chassis module directory `src/chassis/`
- [x] 1.2 Create OpenSpec BDD proposal, spec, design
- [ ] 1.3 Add pydantic dependency to pyproject.toml
- [ ] 1.4 Create `__init__.py` for chassis module

## 2. Core Implementation
- [ ] 2.1 Implement `harness.py` — HarnessRegistry, Harness, HarnessTuple
- [ ] 2.2 Implement `packet.py` — RunPacket (typed, hash-chained)
- [ ] 2.3 Implement `fsm.py` — WorkflowFSM with typed transitions
- [ ] 2.4 Implement `store.py` — StateStore (SQLite-backed)
- [ ] 2.5 Implement `tools.py` — ToolRegistry, ToolClassification
- [ ] 2.6 Implement `policy.py` — PolicyEngine with gate checking
- [ ] 2.7 Implement `gev.py` — GEV separation enforcement

## 3. Tests
- [ ] 3.1 Write `tests/test_chassis.py` with golden-run replay tests
- [ ] 3.2 Write BDD acceptance tests from spec.md gherkin features
- [ ] 3.3 Run tests and verify all pass

## 4. Integration
- [ ] 4.1 Create `docs/chassis/proofpacket.json` with verification evidence
- [ ] 4.2 Register chassis as new L10 module
- [ ] 4.3 Wire into cron-fleet as `00-chassis` department
