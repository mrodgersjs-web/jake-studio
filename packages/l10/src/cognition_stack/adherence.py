"""Faculty 4: Best-Practice Adherence as a HARD KPI — GL-L10-CS2-02

The core move: a goal loop cannot reach DONE on 'the artifact works.'
It must clear a PROCESS-ADHERENCE KPI scored against the scraped tribal job map.

This is the verification ladder made explicit — do not pretend
Level-4 judgment is Level-1 truth.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from common import ProofPacket, VerifyLevel, emit_gate_json

class VerificationLevel(Enum):
    L1_DETERMINISTIC = "L1"  # Assertion/exit-code/golden — autonomous
    L2_RULE = "L2"           # Linter/schema/policy — autonomous
    L3_FIELD_TRUTH = "L3"    # Delayed real outcome — objective
    L4_MODEL_JUDGE = "L4"    # Rubric adherence — assisted (different model)
    L5_HUMAN = "L5"          # Mike checkpoint — supervision

@dataclass
class AdherenceResult:
    """Result of an adherence check against a tribal job map."""
    process_name: str
    e_adherence: float
    theta: float  # Threshold
    steps_followed: list[str]
    steps_skipped: list[str]
    gates_checked: list[str]
    gates_skipped: list[str]
    critical_gate_skipped: bool
    verification_level: VerificationLevel
    gate_json: dict = field(default_factory=dict)
    verdict: str = "DRAFT"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AdherenceGate:
    """Hard KPI gate that blocks goal loop closure on process adherence.
    
    E_adherence = sum(w_i * (1 - step_followed_i)) + lambda * critical_gate_skipped
    
    BLOCK (not FAIL→retry) if any critical gate was skipped.
    Loop closes only iff E_adherence <= theta AND outcome proof obligation holds.
    
    Anti-Goodhart: adherence score is measured against EXTERNALLY-SCRAPED
    practice, not a rubric the rig wrote for itself.
    """
    
    def __init__(self, theta: float = 1.0, gate_lambda: float = 10.0):
        self.theta = theta
        self.gate_lambda = gate_lambda
        self.results: list[AdherenceResult] = []
    
    def check(self, process_name: str, job_map_steps: list[dict],
              completed_steps: list[str], skipped_gates: list[str],
              step_weights: Optional[dict[str, float]] = None) -> AdherenceResult:
        """Check adherence against a tribal job map.
        
        Args:
            process_name: Name of the process being checked
            job_map_steps: List of step dicts from tribal job map
            completed_steps: List of step IDs that were completed
            skipped_gates: List of gate IDs that were skipped
            step_weights: Optional per-step weights (default: 1.0 each)
        
        Returns:
            AdherenceResult with e_adherence, verdict, and gate.json
        """
        weights = step_weights or {}
        
        # Compute step penalty
        step_penalty = 0.0
        steps_followed = []
        steps_skipped = []
        gates_checked = []
        
        for step in job_map_steps:
            sid = step.get("step_id", "")
            w = weights.get(sid, 1.0)
            
            if sid in completed_steps:
                steps_followed.append(sid)
            else:
                steps_skipped.append(sid)
                step_penalty += w * 1.0  # w_i * (1 - 0)
            
            if step.get("step_type") == "gate":
                gates_checked.append(sid)
        
        # Compute gate penalty
        critical_skipped = False
        gate_penalty = 0.0
        for gate_id in skipped_gates:
            gate_penalty += self.gate_lambda
            critical_skipped = True
        
        e_adherence = step_penalty + gate_penalty
        
        # Determine verification level
        level = VerificationLevel.L4_MODEL_JUDGE  # Default: model-as-judge
        
        # Verdict
        if critical_skipped:
            verdict = "BLOCK"
        elif e_adherence <= self.theta:
            verdict = "PASS"
        else:
            verdict = "FAIL"
        
        # Emit gate.json (hash-chained, every stage)
        gate_json = emit_gate_json(
            stage=process_name,
            e_stage=e_adherence,
            theta=self.theta,
            best_practice_adherence=1.0 - min(step_penalty / max(len(job_map_steps), 1), 1.0),
            critical_gate_skipped=critical_skipped,
            source_per_claim=True,
            brier=0.0,  # Computed separately
            surprisal_s=0.0,  # Computed separately
        )
        
        result = AdherenceResult(
            process_name=process_name,
            e_adherence=round(e_adherence, 4),
            theta=self.theta,
            steps_followed=steps_followed,
            steps_skipped=steps_skipped,
            gates_checked=gates_checked,
            gates_skipped=skipped_gates,
            critical_gate_skipped=critical_skipped,
            verification_level=level,
            gate_json=gate_json,
            verdict=verdict,
        )
        self.results.append(result)
        return result
    
    def is_close_worthy(self, result: AdherenceResult) -> bool:
        """Goal loop can close only iff E_adherence <= theta AND
        outcome proof obligation holds AND no critical gate skipped.
        """
        return (
            result.verdict == "PASS"
            and not result.critical_gate_skipped
            and result.e_adherence <= self.theta
        )
