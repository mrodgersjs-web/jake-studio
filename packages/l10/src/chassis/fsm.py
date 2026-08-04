"""GL-L10-CH-03: Workflow State Machine — typed transitions + failure states.

State machine with minimum states:
INTAKE → VALIDATE_INPUTS → PLAN → AUTHORIZE_TOOLS → EXECUTE →
EVALUATE → REVISE (bounded loop) → VERIFY → HUMAN_APPROVAL →
COMMIT → RECORD_OUTCOME → CLOSED

Failure states (all terminal):
BLOCKED_INPUT, POLICY_DENIED, TOOL_FAILURE, BUDGET_EXCEEDED,
EVALUATION_FAILED, VERIFICATION_FAILED, HUMAN_REJECTED,
ROLLBACK_REQUIRED, QUARANTINED

Every transition has a typed entry condition, exit condition, timeout,
owner, and recovery route.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Dict, List, Callable


class RunState(str, Enum):
    """Workflow states."""

    # Primary flow
    INTAKE = "INTAKE"
    VALIDATE_INPUTS = "VALIDATE_INPUTS"
    PLAN = "PLAN"
    AUTHORIZE_TOOLS = "AUTHORIZE_TOOLS"
    EXECUTE = "EXECUTE"
    EVALUATE = "EVALUATE"
    REVISE = "REVISE"
    VERIFY = "VERIFY"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    COMMIT = "COMMIT"
    RECORD_OUTCOME = "RECORD_OUTCOME"
    CLOSED = "CLOSED"

    # Failure states (all terminal)
    BLOCKED_INPUT = "BLOCKED_INPUT"
    POLICY_DENIED = "POLICY_DENIED"
    TOOL_FAILURE = "TOOL_FAILURE"
    BUGET_EXCEEDED = "BUDGET_EXCEEDED"
    EVALUATION_FAILED = "EVALUATION_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    QUARANTINED = "QUARANTINED"


# Terminal states — no forward transitions allowed
TERMINAL_STATES = {
    RunState.CLOSED,
    RunState.BLOCKED_INPUT,
    RunState.POLICY_DENIED,
    RunState.TOOL_FAILURE,
    RunState.BUGET_EXCEEDED,
    RunState.EVALUATION_FAILED,
    RunState.VERIFICATION_FAILED,
    RunState.HUMAN_REJECTED,
    RunState.ROLLBACK_REQUIRED,
    RunState.QUARANTINED,
}

# Failure states — terminal with no recovery route
FAILURE_STATES = {
    RunState.BLOCKED_INPUT,
    RunState.POLICY_DENIED,
    RunState.TOOL_FAILURE,
    RunState.BUGET_EXCEEDED,
    RunState.EVALUATION_FAILED,
    RunState.VERIFICATION_FAILED,
    RunState.HUMAN_REJECTED,
    RunState.ROLLBACK_REQUIRED,
    RunState.QUARANTINED,
}


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


@dataclass
class TransitionRule:
    """A typed transition rule with conditions."""
    from_state: RunState
    to_state: RunState
    entry_condition: str = ""
    exit_condition: str = ""
    timeout_seconds: int = 300
    owner: str = "system"
    recovery_route: str = ""


# Valid state transitions
VALID_TRANSITIONS: Dict[RunState, set[RunState]] = {
    # Primary flow
    RunState.INTAKE: {RunState.VALIDATE_INPUTS, RunState.BLOCKED_INPUT,
                      RunState.POLICY_DENIED},
    RunState.VALIDATE_INPUTS: {RunState.PLAN, RunState.BLOCKED_INPUT,
                               RunState.POLICY_DENIED},
    RunState.PLAN: {RunState.AUTHORIZE_TOOLS, RunState.BLOCKED_INPUT,
                    RunState.POLICY_DENIED},
    RunState.AUTHORIZE_TOOLS: {RunState.EXECUTE, RunState.POLICY_DENIED,
                               RunState.BUGET_EXCEEDED},
    RunState.EXECUTE: {RunState.EVALUATE, RunState.TOOL_FAILURE,
                       RunState.BUGET_EXCEEDED, RunState.POLICY_DENIED},
    RunState.EVALUATE: {RunState.REVISE, RunState.VERIFY,
                        RunState.EVALUATION_FAILED, RunState.POLICY_DENIED},
    RunState.REVISE: {RunState.EXECUTE, RunState.VERIFY,
                      RunState.EVALUATION_FAILED, RunState.BUGET_EXCEEDED},
    RunState.VERIFY: {RunState.HUMAN_APPROVAL, RunState.COMMIT,
                      RunState.VERIFICATION_FAILED, RunState.HUMAN_REJECTED},
    RunState.HUMAN_APPROVAL: {RunState.COMMIT, RunState.HUMAN_REJECTED},
    RunState.COMMIT: {RunState.RECORD_OUTCOME, RunState.ROLLBACK_REQUIRED},
    RunState.RECORD_OUTCOME: {RunState.CLOSED},
    RunState.CLOSED: set(),  # Terminal
    # Failure states are terminal
    RunState.BLOCKED_INPUT: set(),
    RunState.POLICY_DENIED: set(),
    RunState.TOOL_FAILURE: set(),
    RunState.BUGET_EXCEEDED: set(),
    RunState.EVALUATION_FAILED: set(),
    RunState.VERIFICATION_FAILED: set(),
    RunState.HUMAN_REJECTED: set(),
    RunState.ROLLBACK_REQUIRED: set(),
    RunState.QUARANTINED: set(),
}


@dataclass
class StateSnapshot:
    """Snapshot of a workflow state at a point in time."""
    state: RunState
    actor: str
    timestamp: str
    reason: Optional[str]
    transition_count: int


class WorkflowFSM:
    """Typed workflow state machine with typed transitions.

    Every transition has:
    - entry_condition, exit_condition
    - timeout, owner, recovery_route

    No free-floating state changes. Every transition is validated
    against the typed transition table.
    """

    def __init__(self):
        self.current_state: RunState = RunState.INTAKE
        self.state_history: List[StateSnapshot] = []
        self._transition_count: int = 0
        self._record_snapshot("system", "initial")

    def transition_to(self, target: RunState, actor: str,
                      reason: Optional[str] = None) -> None:
        """Transition to a new state.

        Raises StateTransitionError if the transition is invalid.
        """
        current = self.current_state

        # Check if current state is terminal
        if current in TERMINAL_STATES:
            raise StateTransitionError(
                f"Cannot transition from terminal state '{current.value}'. "
                f"Attempted: {current.value} → {target.value}"
            )

        # Check if transition is valid
        valid_targets = VALID_TRANSITIONS.get(current, set())
        if target not in valid_targets:
            raise StateTransitionError(
                f"Invalid transition: {current.value} → {target.value}. "
                f"Valid targets from {current.value}: "
                f"{', '.join(s.value for s in valid_targets) or 'none'}"
            )

        # Transition is valid
        self._transition_count += 1
        self.current_state = target
        self._record_snapshot(actor, reason)

    def force_transition(self, target: RunState, actor: str,
                         reason: str) -> None:
        """Force a transition, bypassing validation.

        ONLY for failure states or rollback. Requires explicit reason.
        """
        if target not in FAILURE_STATES and target != RunState.CLOSED:
            raise StateTransitionError(
                "force_transition only allowed for failure states or CLOSED"
            )
        self._transition_count += 1
        self.current_state = target
        self._record_snapshot(actor, f"FORCED: {reason}")

    def get_history(self) -> List[StateSnapshot]:
        """Return the full state transition history."""
        return list(self.state_history)

    def can_transition_to(self, target: RunState) -> bool:
        """Check if a transition to target is valid from current state."""
        if self.current_state in TERMINAL_STATES:
            return False
        return target in VALID_TRANSITIONS.get(self.current_state, set())

    def is_terminal(self) -> bool:
        """Check if the current state is terminal."""
        return self.current_state in TERMINAL_STATES

    def get_transition_rules(self) -> List[TransitionRule]:
        """Return all valid transition rules for the current state."""
        rules = []
        for target in VALID_TRANSITIONS.get(self.current_state, set()):
            rules.append(TransitionRule(
                from_state=self.current_state,
                to_state=target,
                entry_condition=f"All preconditions for {target.value} met",
                exit_condition=f"{self.current_state.value} complete",
                owner="generator" if target not in FAILURE_STATES else "system",
            ))
        return rules

    def _record_snapshot(self, actor: str, reason: Optional[str]) -> None:
        """Record a state snapshot."""
        self.state_history.append(StateSnapshot(
            state=self.current_state,
            actor=actor,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            transition_count=self._transition_count,
        ))
