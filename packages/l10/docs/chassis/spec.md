# Jake Agent Production Chassis — Phase 1 Spec

## Context
Every production capability runs through a sealed, versioned harness
H=(E,T,C,S,L,V). This spec defines the Phase 1 chassis: the irreducible
runtime that enforces that contract, the typed run packet, the workflow
state machine, the durable state store, and the tool registry.

## Requirement: Harness Registry
The harness registry manages sealed, versioned harness definitions. Each harness
binds identity, tools, context, state, loop, and verification into a single
hash-chained artifact.

```gherkin
Feature: Harness Registry

  Rule: A harness is a sealed, versioned H=(E,T,C,S,L,V) tuple
    Each harness MUST contain exactly E, T, C, S, L, V components.
    Each harness MUST have a version string and a signature hash.
    The signature MUST be over the sorted JSON of all six components.

    Scenario: Register a valid harness
      Given a complete H=(E,T,C,S,L,V) tuple
      When register_harness is called with version "1.0.0"
      Then the harness is stored with a signature hash
      And the signature hash starts with "sha256:"

    Scenario: Reject incomplete harness
      Given an incomplete tuple missing component "V"
      When register_harness is called
      Then a ValidationError is raised
      And no harness is stored

  Rule: Harness versions are immutable
    Once a harness is registered with version X, it CANNOT be modified.
    A new version MUST be used for any change.

    Scenario: Reject duplicate version
      Given harness "example" version "1.0.0" is registered
      When register_harness is called again with version "1.0.0"
      Then a ValueError is raised
      And the original harness is unchanged
```

## Requirement: Typed Run Packet
Every task run creates a typed, hash-chained packet.

```gherkin
Feature: Typed Run Packet

  Rule: Every run packet has a unique run_id and harness reference
    A RunPacket MUST have run_id, harness_name, harness_version, goal.
    A RunPacket MUST track input_references with freshness_metadata.
    A RunPacket MUST track tool_calls, state_transitions, and artifacts.
    A RunPacket MUST track evaluator_findings and verifier_decision.
    A RunPacket MUST track cost, latency, and failure telemetry.

    Scenario: Create a valid run packet
      Given a harness "test-harness" version "1.0.0"
      And goal "Test the run packet schema"
      When RunPacket is instantiated
      Then run_id is a valid UUID
      And harness_name is "test-harness"
      And harness_version is "1.0.0"

    Scenario: Packet signature chain
      Given a RunPacket with previous_packet_hash "sha256:abc123"
      When seal() is called
      Then the packet hash is computed
      And previous_packet_hash is preserved in the sealed output

    Scenario: No hidden retries
      Given a RunPacket with 2 retry entries in state_transitions
      When the packet is sealed
      Then the retry_count is visible in the packet metadata
      And each retry has a timestamp and reason
```

## Requirement: Workflow State Machine
The state machine enforces typed transitions with entry/exit conditions.

```gherkin
Feature: Workflow State Machine

  Rule: Valid state transitions
    The state machine MUST accept transitions from INTAKE to VALIDATE_INPUTS.
    The state machine MUST accept transitions from VALIDATE_INPUTS to PLAN.
    The state machine MUST accept transitions from PLAN to AUTHORIZE_TOOLS.
    The state machine MUST accept transitions from AUTHORIZE_TOOLS to EXECUTE.
    The state machine MUST accept transitions from EXECUTE to EVALUATE.
    The state machine MUST accept transitions from EVALUATE to VERIFY.
    The state machine MUST accept transitions from VERIFY to COMMIT.
    The state machine MUST accept transitions from COMMIT to CLOSED.

    Scenario: Happy path through the state machine
      Given a new workflow instance
      When valid transitions are applied in order
      Then the final state is CLOSED

    Scenario: Reject invalid transition
      Given the state is INTAKE
      When transition_to(EXECUTION) is attempted
      Then a StateTransitionError is raised
      And the state remains INTAKE

  Rule: Failure states are terminal
    BLOCKED_INPUT, POLICY_DENIED, TOOL_FAILURE, BUDGET_EXCEEDED,
    EVALUATION_FAILED, VERIFICATION_FAILED, HUMAN_REJECTED,
    ROLLBACK_REQUIRED, QUARANTINED
    MUST all be terminal states with no forward transitions.

    Scenario: Policy denial is terminal
      Given the state is AUTHORIZE_TOOLS
      When transition_to(POLICY_DENIED) is applied
      Then no further transitions are allowed
      And the failure reason is recorded

    Scenario: Budget exceeded during execution
      Given the state is EXECUTE
      When budget is exceeded
      Then transition_to(BUDGET_EXCEEDED) is allowed
      And the state becomes terminal
```

## Requirement: Durable State Store
State persists after every consequential transition and survives process restart.

```gherkin
Feature: Durable State Store

  Rule: State persists after transitions
    After any state transition, the current state MUST be written to disk.
    After any state transition, pending tasks MUST be written to disk.
    After any state transition, budget consumed MUST be written to disk.

    Scenario: State survives restart
      Given a workflow in state EXECUTE with partial state
      When the store is checkpointed
      And a new process loads the same store
      Then the state is EXECUTE
      And pending tasks are preserved

  Rule: Idempotency on resume
    Resuming a completed side-effect MUST NOT repeat it.
    The store MUST track idempotency keys for external writes.

    Scenario: Resume without duplicate side effect
      Given a workflow with idempotency key "write:user:123" committed
      When the store is resumed
      Then the idempotency key is marked committed
      And no retry of that side effect occurs
```

## Requirement: Tool Registry
Tools are classified by side-effect class and require approval for gated classes.

```gherkin
Feature: Tool Registry

  Rule: Side-effect classification
    Every tool MUST be classified as one of:
    read_only, reversible_write, irreversible_write, destructive,
    financial, credential_bearing.

    Scenario: Register a read-only tool
      Given tool "list_users" with side_effect_class "read_only"
      When register_tool is called
      Then the tool is stored with its classification

    Scenario: Register a financial tool
      Given tool "charge_card" with side_effect_class "financial"
      When register_tool is called
      Then the tool requires approval by default

  Rule: Policy-before-action
    A tool call MUST pass permission, data-scope, side-effect, budget,
    and approval checks before execution.
    A failed gate MUST prevent execution (not merely warn).

    Scenario: Blocked external write without approval
      Given a financial tool "charge_card" with no approval token
      When execute_tool is called
      Then POLICY_DENIED is raised
      And no side effect occurs
```

## Requirement: GEV Separation
Generator, Evaluator, and Verifier are operationally separated.

```gherkin
Feature: GEV Separation

  Rule: No agent reviews its own output
    The generator that produced an artifact MUST NOT be the verifier
    that approves it.
    The verifier MUST be a distinct process or agent instance.

    Scenario: Generator cannot self-verify
      Given a Generator produces artifact "result-1"
      When verification is requested
      Then the Verifier is a different instance
      And the Generator's verdict field remains null
```
