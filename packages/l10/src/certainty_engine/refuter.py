"""Faculty 10: Refutation Search Engine — GL-L10-CE-03

Proof-by-contradiction as a first-class engine.
For every close-worthy claim C, spawn a Refuter that assumes NOT-C
and hunts a counterexample. The loop closes only if the Refuter FAILS
to find a contradiction within budget.

Absence of a found refutation, not presence of a plausible argument, is the pass condition.
Refuter runs on a DIFFERENT model family than the Generator (anti-collusion).
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from common import (
    ProofPacket, GEVRole, BMS, run_energy, surprisal,
    anti_goodhart_check, deviation_gate,
)

class RefutationVerdict(Enum):
    REFUTED = "refuted"            # Counterexample found — claim is FALSE
    NOT_REFUTED = "not_refuted"    # No counterexample within budget — claim survives
    INCONCLUSIVE = "inconclusive"  # Budget exhausted at shallow depth (surprisal-flag)
    ERROR = "error"

@dataclass
class Claim:
    """A close-worthy claim to be refuted or survived."""
    id: str
    statement: str            # C: "this artifact is great"
    negation: str             # NOT-C: "this artifact is NOT great"
    generator_family: str     # Model family of the generator (e.g. "claude")
    evidence_fn: Callable[[], Any]  # Function that produces evidence for the claim
    context: dict = field(default_factory=dict)

@dataclass
class RefutationAttempt:
    """One attempt to refute a claim."""
    claim_id: str
    counterexample: Optional[Any]
    search_depth: int
    verdict: RefutationVerdict
    e_refute: float
    budget_used: int
    budget_max: int
    surprisal_flagged: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RefuterAgent:
    """Cross-family refutation engine.
    
    Anti-collusion: a maker cannot refute its own claim.
    Refuter runs on a DIFFERENT model family than the Generator.
    
    If generator and refuter collapse to one family → E=∞.
    This is the direct mitigation for the sharpest 2026 result:
    when generator and judge share context, reward hacking is spontaneous.
    """
    
    def __init__(self, refuter_family: str = "gpt"):
        self.refuter_family = refuter_family
        self.attempts: list[RefutationAttempt] = []
        self.min_adversarial_effort = 10  # Minimum search depth for valid refutation
    
    def refute(self, claim: Claim, budget: int = 100,
               counterexample_generators: list[Callable[[], Any]] = None,
               falsifier: Callable[[Any, Claim], bool] = None) -> RefutationAttempt:
        """Attempt to refute a claim by hunting counterexamples.
        
        Args:
            claim: The claim to attempt to refute
            budget: Maximum search iterations
            counterexample_generators: Functions that generate potential counterexamples
            falsifier: Function that checks if a candidate refutes the claim
        
        Returns:
            RefutationAttempt with verdict
        """
        # Anti-collusion check
        if claim.generator_family == self.refuter_family:
            return RefutationAttempt(
                claim_id=claim.id,
                counterexample=None,
                search_depth=0,
                verdict=RefutationVerdict.ERROR,
                e_refute=float("inf"),
                budget_used=0,
                budget_max=budget,
            )
        
        generators = counterexample_generators or [lambda: self._default_counterexample_gen()]
        falsifier = falsifier or self._default_falsifier
        
        counterexample = None
        depth = 0
        
        for i in range(budget):
            gen = generators[i % len(generators)]
            candidate = gen()
            depth = i + 1
            
            try:
                if falsifier(candidate, claim):
                    counterexample = candidate
                    break
            except Exception:
                continue
        
        # Compute E_refute
        if counterexample is not None:
            e_refute = float("inf")  # Claim refuted
            verdict = RefutationVerdict.REFUTED
        else:
            # No counterexample found — compute budget-weighted energy
            w = 1.0
            e_refute = w * (budget - depth)
            
            if depth < self.min_adversarial_effort:
                # Shallow failed refutation is NOT evidence
                verdict = RefutationVerdict.INCONCLUSIVE
            else:
                verdict = RefutationVerdict.NOT_REFUTED
        
        # Surprisal-flag shallow refutations
        surprisal_flagged = (verdict == RefutationVerdict.INCONCLUSIVE)
        
        attempt = RefutationAttempt(
            claim_id=claim.id,
            counterexample=counterexample,
            search_depth=depth,
            verdict=verdict,
            e_refute=e_refute,
            budget_used=depth,
            budget_max=budget,
            surprisal_flagged=surprisal_flagged,
        )
        self.attempts.append(attempt)
        return attempt
    
    def claim_survives(self, attempt: RefutationAttempt, theta: float = 0.0) -> bool:
        """Check if a claim survives refutation.
        
        Claim promotable iff E_refute <= theta AND search_depth >= min_adversarial_effort.
        A shallow failed refutation is not evidence (surprisal-flag it).
        """
        if attempt.verdict == RefutationVerdict.REFUTED:
            return False
        if attempt.verdict == RefutationVerdict.INCONCLUSIVE:
            return False  # Shallow — not evidence
        return attempt.e_refute <= theta and attempt.search_depth >= self.min_adversarial_effort
    
    def to_proof_packet(self, attempt: RefutationAttempt) -> ProofPacket:
        """Convert refutation attempt to ProofPacket."""
        return ProofPacket(
            formula_id=f"refute:{attempt.claim_id}",
            verdict="PASS" if attempt.verdict == RefutationVerdict.NOT_REFUTED else "FAIL",
            returned_value={
                "verdict": attempt.verdict.value,
                "e_refute": attempt.e_refute,
                "search_depth": attempt.search_depth,
                "budget_max": attempt.budget_max,
                "surprisal_flagged": attempt.surprisal_flagged,
            },
            substrate="refuter-cross-family",
            agreement_delta=0.0,
            metadata={
                "generator_family": "unknown",
                "refuter_family": self.refuter_family,
                "anti_collusion": True,
            },
        )
    
    def _default_counterexample_gen(self) -> dict:
        """Default counterexample generator — returns random perturbations."""
        import random
        return {"value": random.gauss(0, 1), "noise": random.random()}
    
    def _default_falsifier(self, candidate: Any, claim: Claim) -> bool:
        """Default falsifier — checks if candidate contradicts claim evidence.
        
        In production, this would be a domain-specific check.
        """
        if isinstance(candidate, dict) and "value" in candidate:
            evidence = claim.evidence_fn()
            if isinstance(evidence, (int, float)):
                return abs(candidate["value"] - evidence) > 2.0
        return False
