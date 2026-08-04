# Jake Agent Production Chassis — Phase 1 Design

## Context
Building on the L10 stack's existing `common.py` (ProofPacket, BMS, GEVRole),
this design adds a `chassis` module that provides the production-grade
operating system for all RIG agents.

## Decisions

### 1. Extend rig-l10, not a new repo
**Chosen**: Add `src/chassis/` to the existing `rig-l10` package.
**Rationale**: L10 already provides the engine framework (PBT, Refuter,
Taste, Council, Nocturne, Factory, common types). The chassis extends
L10 with the production operating system layer. Same repo, same
Python path, same test suite, same CLI.

**Alternative considered**: New `jake-chassis` repo. Rejected —
duplicates the common types, splits the import path, fragments testing.

### 2. Pydantic for typed schemas
**Chosen**: Use `pydantic` for all schema models.
**Rationale**: Typed, hash-chained packets need runtime validation.
Pydantic v2 provides `model_dump()`, `model_json_schema()`, and
serialization stability required for hash-chained packets.

**Dependency**: Add `pydantic>=2.0` to `pyproject.toml`.

### 3. JSON-file state store for Phase 1
**Chosen**: SQLite for state persistence.
**Rationale**: ACID transactions, single-file deployment, no external
dependency, survives process restart, supports concurrent access.
Local-first per L8 mantra. PostgreSQL comes in Phase 2.

**Alternative considered**: Pure JSON files. Rejected — no ACID
guarantees for concurrent state transitions.

### 4. Verifier as a function, not a process (Phase 1)
**Chosen**: The `Verifier` role is a Python class that can be
instantiated as a separate process or as an in-process component.
In Phase 1, it's in-process but its decision method is sealed —
it reads the packet, checks invariants, and returns PASS/FAIL.
The Generator cannot call Verifier.verify() on its own packet.

### 5. Integration with existing cron-fleet
**Chosen**: The chassis runs as a new `00-chassis` department in the
cron-fleet, providing system-level governance for all agent runs.

## Architecture

```
rig-l10/src/
├── chassis/
│   ├── __init__.py
│   ├── harness.py        # HarnessRegistry, Harness tuple
│   ├── packet.py         # RunPacket (typed, hash-chained)
│   ├── fsm.py            # WorkflowFSM (state machine)
│   ├── store.py          # StateStore (SQLite-backed)
│   ├── tools.py          # ToolRegistry, ToolClassification
│   ├── policy.py         # PolicyEngine, gate checking
│   ├── gev.py            # GEV separation enforcement
│   └── __init__.py
```

### Harness tuple (H=(E,T,C,S,L,V))
- E: ExecutionEnvironment (role, objective, non_goals, boundaries)
- T: ToolAllowlist (scoped tools with permissions and budgets)
- C: ContextSpec (required inputs, schemas, freshness constraints)
- S: StateSpec (checkpoint rules, durable memory, lifecycle, recovery)
- L: LoopSpec (staged workflow, critique cycles, escalation)
- V: VerificationSpec (proof obligations, evaluator tests, verifier authority)

### Run Packet
Extends the existing `ProofPacket` with:
- run_id (UUID4)
- harness_name, harness_version
- goal, measurable outcome
- input_references, freshness_metadata
- assumptions, unresolved_uncertainties
- plan, dependency_graph
- tool_calls, side_effects
- state_transitions, checkpoints
- artifacts (with sha256 hashes)
- evaluator_findings, revisions
- verifier_decision
- human_approvals
- cost, latency, token, failure telemetry
- hash chain (previous_packet_hash → packet_hash)

### Workflow FSM
States: INTAKE, VALIDATE_INPUTS, PLAN, AUTHORIZE_TOOLS, EXECUTE,
EVALUATE, REVISE, VERIFY, HUMAN_APPROVAL, COMMIT, CLOSED
Failure states: BLOCKED_INPUT, POLICY_DENIED, TOOL_FAILURE,
BUDGET_EXCEEDED, EVALUATION_FAILED, VERIFICATION_FAILED,
HUMAN_REJECTED, ROLLBACK_REQUIRED, QUARANTINED

Transitions are typed: each transition has entry_condition, exit_condition,
timeout, owner, recovery_route.

### State Store (SQLite)
Tables: runs, transitions, artifacts, tool_calls, approvals,
idempotency_keys, budgets.
Checkpoint after every consequential transition.
Resume by loading run state and replaying pending tasks.

### Tool Registry
Each tool: name, description, side_effect_class, requires_approval,
budget_cost, allowed_domains, rate_limit.
Policy engine checks: permission, data-scope, side-effect, budget,
approval, secret-access, rate/concurrency, evidence sufficiency.

## Risks & Trade-offs

- **SQLite concurrency**: Multiple workers may contend on the state
  store. Mitigation: write locks + retry with backoff. Phase 2 moves
  to PostgreSQL.
- **Verifier in-process**: Phase 1 keeps the verifier in-process for
  simplicity. The contract (Verifier ≠ Generator) is enforced by
  API design — the generator gets a RunSession that cannot call
  verify() on its own packet. Phase 2 splits to a separate process.
- **No Lean kernel in Phase 1**: L0 verification deferred to Phase 4.
  Phase 1 uses L1 (deterministic assertions) and L2 (schema/policy).

## Migration Plan
No migration needed. This is a new module. Existing L10 modules
continue to work unchanged. The chassis imports from `common.py`.
