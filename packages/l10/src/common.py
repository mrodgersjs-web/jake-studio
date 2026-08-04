"""RIG L10 Common — Shared types, energy functions, and invariants.

Every L10 module imports from here. This is the single source of truth for:
- Energy computation (wraps rig-math-exec SymPy substrate)
- ProofPacket types
- GEV roles (Generator ≠ Evaluator ≠ Verifier)
- BMS autonomy bands (A1..A4)
- Deviation gating (RobustMADZ)
- Anti-Goodhart invariants
"""
from __future__ import annotations
import json
import subprocess
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# ── Paths ──────────────────────────────────────────────────────────────
RIG_MATHEXEC = Path.home() / ".rig" / "bin" / "rig-math-exec"
PACKET_STORE = Path.home() / ".rig" / "global" / "mathexec" / "packets"

# ── BMS Autonomy Bands ─────────────────────────────────────────────────
class BMS(Enum):
    A1 = "A1"  # Autonomous
    A2 = "A2"  # Supervised-autonomous
    A3 = "A3"  # Assisted
    A4 = "A4"  # Manual (Mike required)

# ── GEV Roles ──────────────────────────────────────────────────────────
class GEVRole(Enum):
    GENERATOR = "generator"
    EVALUATOR = "evaluator"
    VERIFIER = "verifier"  # Jake only

# ── Verification Ladder ────────────────────────────────────────────────
class VerifyLevel(Enum):
    L0 = "L0_kernel"       # Machine-checked certificate (Lean/SymPy)
    L1 = "L1_deterministic" # Assertion/exit-code/golden
    L2 = "L2_rule"          # Linter/schema/policy
    L3 = "L3_field_truth"   # Delayed real outcome
    L4 = "L4_model_judge"   # Cross-family model rubric
    L5 = "L5_human"         # Mike checkpoint

# ── Confidence Ladder ──────────────────────────────────────────────────
class Confidence(Enum):
    PERFECT = "PERFECT"
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    FEEDBACK = "FEEDBACK"
    FAILED = "FAILED"

# ── BaseModule ─────────────────────────────────────────────────────────
class BaseModule:
    """Minimal base class for L10 modules."""
    def ready(self) -> bool:
        return True


# ── ProofPacket ────────────────────────────────────────────────────────
# The @dataclass below belongs to ProofPacket and must stay attached to it.
# It was previously sitting on BaseModule: BaseModule had been inserted between
# this section header and the class the decorator was written for, so ProofPacket
# silently lost it. Because ProofPacket's fields are only ANNOTATIONS, losing the
# decorator does not raise at import — the annotations stay inert, the
# `field(default_factory=...)` calls become plain class attributes, and every
# construction fails at runtime with `ProofPacket() takes no arguments`. That broke
# every caller that seals a proof, including the conference refuter gate (7 tests).
# BaseModule has no fields, so it never needed to be a dataclass at all.
@dataclass
class ProofPacket:
    """Typed, hash-chained proof artifact."""
    formula_id: str
    verdict: str  # PASS | FAIL | BLOCK
    returned_value: Any
    substrate: str = "sympy-mcp"
    agreement_delta: float = 0.0
    packet_hash: str = ""
    prev_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    falsifiable_prediction: str = ""
    metadata: dict = field(default_factory=dict)

    def seal(self) -> str:
        """Compute hash chain over this packet."""
        content = json.dumps(asdict(self), sort_keys=True, default=str)
        self.packet_hash = "sha256:" + hashlib.sha256(content.encode()).hexdigest()
        return self.packet_hash

# ── Energy Computation (SymPy substrate) ───────────────────────────────
def run_energy(formula: str, **kwargs) -> dict:
    """Execute an energy function via rig-math-exec (SymPy MCP substrate).
    
    Args:
        formula: One of robust-madz, blend-value, e-total, expected-free-energy,
                 composite-sigma, surprisal, poisson-merge
        **kwargs: Formula-specific arguments
    
    Returns:
        Dict with verdict, returned_value, packet_hash, agreement_delta
    """
    cmd = [str(RIG_MATHEXEC), formula]
    for k, v in kwargs.items():
        cmd.extend([f"--{k.replace('_', '-')}", str(v)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"verdict": "ERROR", "error": result.stderr[:500]}
    except Exception as e:
        return {"verdict": "ERROR", "error": str(e)[:500]}

def robust_madz(score: float, baseline: list[float]) -> dict:
    """RobustMADZ = 0.6745 * (score - median) / MAD. Deviation gate."""
    return run_energy("robust-madz", score=score, baseline=",".join(str(b) for b in baseline))

def surprisal(probability: float) -> dict:
    """S(o) = -ln P(o). Surprisal/entropy measure."""
    return run_energy("surprisal", probability=probability)

def blend_value(novelty: float, systematicity: float, inconsistency: float) -> dict:
    """BlendValue = λ1*Novelty + λ2*Systematicity - λ3*Inconsistency."""
    return run_energy("blend-value", novelty=novelty, systematicity=systematicity, inconsistency=inconsistency)

def expected_free_energy(expected_surprise: float, kl_divergence: float) -> dict:
    """G(π) = expected_surprise + D_KL(q||p). EFE for action selection."""
    return run_energy("expected-free-energy", expected_surprise=expected_surprise, kl_divergence=kl_divergence)

def composite_sigma(d_struct: float, d_behavior: float) -> dict:
    """σ = 0.3*d_struct + 0.7*d_behavior. Composite deviation score."""
    return run_energy("composite-sigma", d_struct=d_struct, d_behavior=d_behavior)

# ── Deviation Gate ─────────────────────────────────────────────────────
def deviation_gate(score: float, baseline: list[float], 
                   reject_sigma: float = 5.0, auto_reject_sigma: float = 30.0) -> str:
    """Gate a value against baseline. Returns 'accept', 'reject', or 'auto_reject'.
    
    Per AHE/Lin et al.: ≥5σ → reject (deep review), ≥30σ → auto-reject (physics ceiling).
    """
    result = robust_madz(score, baseline)
    if result.get("verdict") != "PASS":
        return "error"
    sigma = abs(result.get("sigma", 0))
    if sigma >= auto_reject_sigma:
        return "auto_reject"
    if sigma >= reject_sigma:
        return "reject"
    return "accept"

# ── Anti-Goodhart Check ───────────────────────────────────────────────
def anti_goodhart_check(metric_source: str, agent_writable: bool) -> bool:
    """BLOCK if the metric is writable by the agent that uses it.
    
    Anti-Goodhart: certification requires an out-of-loop signal the agent cannot write.
    RL widens the reward-hacking gap under pressure.
    """
    if agent_writable:
        return False  # BLOCK — metric is gameable
    return True  # OK — external signal

# ── Gate JSON ──────────────────────────────────────────────────────────
def emit_gate_json(stage: str, e_stage: float, theta: float, 
                   best_practice_adherence: float, critical_gate_skipped: bool,
                   source_per_claim: bool, brier: float, surprisal_s: float) -> dict:
    """Emit hash-chained gate.json per the Adherence KPI card."""
    return {
        "stage": stage,
        "e_stage": e_stage,
        "theta": theta,
        "best_practice_adherence_score": best_practice_adherence,
        "critical_gate_skipped": critical_gate_skipped,
        "source_per_claim": source_per_claim,
        "brier": brier,
        "surprisal_S": surprisal_s,
        "status": "DRAFT_NOT_APPROVED_FOR_DELIVERY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
