"""GL-L10-CH-02: Typed Run Packet — hash-chained, no hidden retries.

Every task run creates a typed, hash-chained packet containing:
- Run ID, harness name, and harness version
- Goal and measurable outcome
- Input references and freshness metadata
- Assumptions and unresolved uncertainties
- Plan and dependency graph
- Tool calls and side effects
- State transitions and checkpoints
- Generated artifacts and hashes
- Evaluator findings
- Revisions and residual defects
- Verifier decision and supporting evidence
- Human approvals, when required
- Cost, latency, token, and failure telemetry
- Final outcome and post-run learning record
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class GEVRole(str, Enum):
    GENERATOR = "generator"
    EVALUATOR = "evaluator"
    VERIFIER = "verifier"


class Confidence(str, Enum):
    PERFECT = "PERFECT"
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    FEEDBACK = "FEEDBACK"
    FAILED = "FAILED"


@dataclass
class ArtifactRef:
    """Reference to a generated artifact with hash for provenance."""
    path: str
    hash: str  # sha256:...
    size_bytes: int = 0


@dataclass
class InputReference:
    """Reference to an input with freshness metadata."""
    name: str
    source: str
    freshness_hours: int
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ToolCallRecord:
    """Record of a tool call made during execution."""
    tool_name: str
    side_effect_class: str
    input_summary: str
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: Optional[int] = None


@dataclass
class StateTransition:
    """Record of a state transition in the workflow FSM."""
    from_state: str
    to_state: str
    actor: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: Optional[str] = None


@dataclass
class RetryRecord:
    """Record of a retry attempt — always visible, never hidden."""
    attempt: int
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DefectFinding:
    """A defect found by the evaluator."""
    finding_id: str
    type: str
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    location: str


@dataclass
class ApprovalRecord:
    """A human approval for a gated action."""
    gate: str
    approved_by: str
    action: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CostTelemetry:
    """Cost, latency, token, and failure telemetry."""
    tokens_consumed: int = 0
    tokens_remaining: int = 0
    cost_usd: float = 0.0
    cost_budget: float = 0.0
    latency_ms: int = 0
    failures: List[str] = field(default_factory=list)


class RunPacket:
    """Typed, hash-chained execution packet.

    Every field is typed and serialized. The packet hash chains
    to the previous packet, forming an immutable audit trail.
    No hidden retries — every retry is recorded in retries_log.
    """

    def __init__(
        self,
        harness_name: str,
        harness_version: str,
        goal: str,
        gev_role: str,
        outcome: Optional[str] = None,
        previous_packet_hash: Optional[str] = None,
        assumptions: Optional[List[str]] = None,
        uncertainties: Optional[List[str]] = None,
        plan: Optional[str] = None,
        dependency_graph: Optional[str] = None,
    ):
        self.run_id: str = str(uuid4())
        self.harness_name: str = harness_name
        self.harness_version: str = harness_version
        self.goal: str = goal
        self.outcome: Optional[str] = outcome
        self.gev_role: str = gev_role
        self.previous_packet_hash: Optional[str] = previous_packet_hash
        self.timestamp: str = datetime.now(timezone.utc).isoformat()
        self.schema_version: str = "rig.packet.v1"

        # Input references with freshness
        self.input_references: List[InputReference] = []

        # Assumptions and uncertainties
        self.assumptions: List[str] = assumptions or []
        self.unresolved_uncertainties: List[str] = uncertainties or []

        # Plan and dependency graph
        self.plan: Optional[str] = plan
        self.dependency_graph: Optional[str] = dependency_graph

        # Tool calls and side effects
        self.tool_calls: List[ToolCallRecord] = []

        # State transitions and checkpoints
        self.state_transitions: List[StateTransition] = []
        self.checkpoints: List[str] = []

        # Artifacts with hashes
        self.artifacts: List[ArtifactRef] = []

        # Evaluator findings and revisions
        self.evaluator_findings: List[DefectFinding] = []
        self.revisions: List[Dict[str, Any]] = []
        self.residual_defects: List[str] = []

        # Verifier decision
        self.verifier_decision: Optional[Dict[str, Any]] = None

        # Human approvals
        self.human_approvals: List[ApprovalRecord] = []

        # Telemetry
        self.telemetry: CostTelemetry = CostTelemetry()

        # Retries — always visible, never hidden
        self.retries_log: List[RetryRecord] = []
        self.retry_count: int = 0

        # Final outcome metadata
        self.final_outcome: Optional[str] = None
        self.post_run_learning: Optional[str] = None
        self.packet_hash: str = ""

    # ── Builder methods ──────────────────────────────────────────────

    def add_input_reference(self, name: str, source: str, freshness_hours: int) -> "RunPacket":
        """Add an input reference with freshness metadata."""
        self.input_references.append(InputReference(
            name=name, source=source, freshness_hours=freshness_hours
        ))
        return self

    def add_artifact(self, path: str, hash: str, size_bytes: int = 0) -> "RunPacket":
        """Add an artifact reference with provenance hash."""
        self.artifacts.append(ArtifactRef(path=path, hash=hash, size_bytes=size_bytes))
        return self

    def add_tool_call(
        self, tool_name: str, side_effect_class: str,
        input_summary: str, status: str, duration_ms: Optional[int] = None,
    ) -> "RunPacket":
        """Record a tool call made during execution."""
        self.tool_calls.append(ToolCallRecord(
            tool_name=tool_name, side_effect_class=side_effect_class,
            input_summary=input_summary, status=status, duration_ms=duration_ms,
        ))
        return self

    def record_state_transition(self, from_state: str, to_state: str, actor: str,
                                reason: Optional[str] = None) -> "RunPacket":
        """Record a state machine transition."""
        self.state_transitions.append(StateTransition(
            from_state=from_state, to_state=to_state, actor=actor, reason=reason
        ))
        return self

    def record_checkpoint(self, state: str) -> "RunPacket":
        """Record a checkpoint."""
        self.checkpoints.append(state)
        return self

    def record_retry(self, error_type: str, reason: str) -> "RunPacket":
        """Record a retry attempt — always visible, never hidden."""
        self.retry_count += 1
        self.retries_log.append(RetryRecord(
            attempt=self.retry_count,
            reason=f"{error_type}: {reason}",
        ))
        return self

    def add_evaluator_finding(self, finding_id: str, type: str, severity: str,
                              description: str, location: str) -> "RunPacket":
        """Add a defect finding from the evaluator."""
        self.evaluator_findings.append(DefectFinding(
            finding_id=finding_id, type=type, severity=severity,
            description=description, location=location,
        ))
        return self

    def record_revision(self, from_evaluator: str, changes: List[str],
                        verdict: str) -> "RunPacket":
        """Record a revision cycle."""
        self.revisions.append({
            "revision": len(self.revisions) + 1,
            "from_evaluator": from_evaluator,
            "changes": changes,
            "verdict": verdict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return self

    def set_verifier_decision(self, verdict: str, verifier: str,
                              evidence: Dict[str, Any]) -> "RunPacket":
        """Set the verifier's decision.

        Only the Verifier (not Generator) can call this in the GEV contract.
        """
        self.verifier_decision = {
            "verdict": verdict,
            "verifier": verifier,
            "evidence": evidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self

    def add_approval(self, gate: str, approved_by: str, action: str) -> "RunPacket":
        """Record a human approval for a gated action."""
        self.human_approvals.append(ApprovalRecord(
            gate=gate, approved_by=approved_by, action=action,
        ))
        return self

    def set_telemetry(self, tokens_consumed: int, tokens_remaining: int,
                      cost_usd: float, cost_budget: float,
                      latency_ms: int, failures: Optional[List[str]] = None) -> "RunPacket":
        """Set cost/latency/token telemetry."""
        self.telemetry = CostTelemetry(
            tokens_consumed=tokens_consumed,
            tokens_remaining=tokens_remaining,
            cost_usd=cost_usd,
            cost_budget=cost_budget,
            latency_ms=latency_ms,
            failures=failures or [],
        )
        return self

    def seal(self) -> dict:
        """Serialize the packet and compute the hash-chain.

        Returns the full sealed packet as a dict with packet_hash.
        The hash is over the sorted JSON of all fields EXCEPT packet_hash
        itself (which is set by this method).
        """
        data = self.to_dict()
        # Compute hash over all content except the hash itself
        content = {k: v for k, v in data.items() if k != "packet_hash"}
        serialized = json.dumps(content, sort_keys=True, default=str,
                                ensure_ascii=False)
        self.packet_hash = "sha256:" + hashlib.sha256(serialized.encode()).hexdigest()
        data["packet_hash"] = self.packet_hash
        return data

    def to_dict(self) -> dict:
        """Serialize the packet to a dict for JSON output."""
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "harness_name": self.harness_name,
            "harness_version": self.harness_version,
            "goal": self.goal,
            "outcome": self.outcome,
            "gev_role": self.gev_role,
            "previous_packet_hash": self.previous_packet_hash,
            "timestamp": self.timestamp,
            "input_references": [asdict(r) for r in self.input_references],
            "assumptions": self.assumptions,
            "unresolved_uncertainties": self.unresolved_uncertainties,
            "plan": self.plan,
            "dependency_graph": self.dependency_graph,
            "tool_calls": [asdict(c) for c in self.tool_calls],
            "state_transitions": [asdict(t) for t in self.state_transitions],
            "checkpoints": self.checkpoints,
            "artifacts": [asdict(a) for a in self.artifacts],
            "evaluator_findings": [asdict(f) for f in self.evaluator_findings],
            "revisions": self.revisions,
            "residual_defects": self.residual_defects,
            "verifier_decision": self.verifier_decision,
            "human_approvals": [asdict(a) for a in self.human_approvals],
            "telemetry": asdict(self.telemetry),
            "retries_log": [asdict(r) for r in self.retries_log],
            "retry_count": self.retry_count,
            "final_outcome": self.final_outcome,
            "post_run_learning": self.post_run_learning,
            "packet_hash": self.packet_hash,
        }
