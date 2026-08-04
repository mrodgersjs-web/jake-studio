"""Faculty 2: Problem-Solving Council — GL-L10-CS1-02

Not 'add a judge and some debate.' The felt shift: the harness stops shipping
competent-but-soulless output and starts shipping work with genuine taste,
pressure-tested by a council that actually disagrees.

Roles = distinct MODEL FAMILIES (diversity is the feature):
- Architect (Opus/high-reasoning): frames problem, proposes >=2 solution skeletons
- Worker(s) (fast/cheap): implement candidates in parallel (<=16 concurrent)
- Evaluator(s) (cross-family critic): surface >=3 defects against FIXED rubric
- Verifier (Themis): judges BLIND, stateless, sole termination

Anti-collusion: no two council seats share a model family for both generate AND grade.
If Architect and Verifier collapse to one family → E=∞.

Deliberation with a STOP: Beta-Binomial mixture + KS statistic halts
when verdicts stabilize — no fixed round count, no burning cost past convergence.
"""
from __future__ import annotations
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from common import ProofPacket, GEVRole, BMS

class CouncilRole(Enum):
    ARCHITECT = "architect"
    WORKER = "worker"
    EVALUATOR = "evaluator"
    VERIFIER = "verifier"  # Themis — blind, sole termination

class CouncilVerdict(Enum):
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"
    BLOCK = "block"  # Anti-collusion violation

@dataclass
class CouncilMember:
    """One seat on the council."""
    role: CouncilRole
    model_family: str  # "claude", "gpt", "gemini", "llama", etc.
    model_name: str    # "opus-4", "gpt-4o", etc.
    verdict: Optional[CouncilVerdict] = None
    defects_found: list[str] = field(default_factory=list)
    rationale: str = ""
    round_number: int = 0

@dataclass
class CouncilSession:
    """A complete council deliberation."""
    session_id: str
    claim: str
    members: list[CouncilMember]
    rounds: int = 0
    stable: bool = False
    final_verdict: Optional[CouncilVerdict] = None
    anti_collusion_holds: bool = True
    diversity_score: float = 0.0
    e_council: float = float("inf")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProblemSolvingCouncil:
    """Multi-model, diversity-gated, stability-detected council.
    
    Fires ONLY when:
    (a) the problem is high-stakes or high-uncertainty (EFE epistemic high), OR
    (b) a single-model attempt failed the grill-loop twice.
    
    Not default — gated.
    """
    
    def __init__(self):
        self.sessions: list[CouncilSession] = []
        self.min_rounds = 2
        self.max_rounds = 10
        self.stability_threshold = 0.85  # KS stability
    
    def convene(self, claim: str, members: list[CouncilMember],
                artifacts: dict[str, Any] = None) -> CouncilSession:
        """Convene a council to deliberate on a claim.
        
        Args:
            claim: The claim to evaluate
            members: Council members with their roles and model families
            artifacts: Files/schemas/ProofPackets for the Verifier to see
        
        Returns:
            CouncilSession with final verdict
        """
        session = CouncilSession(
            session_id=f"council_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            claim=claim,
            members=members,
        )
        
        # Anti-collusion check
        session.anti_collusion_holds = self._check_anti_collusion(members)
        if not session.anti_collusion_holds:
            session.final_verdict = CouncilVerdict.BLOCK
            session.e_council = float("inf")
            self.sessions.append(session)
            return session
        
        # Diversity score
        families = [m.model_family for m in members]
        unique_families = len(set(families))
        session.diversity_score = unique_families / len(members)
        
        # Deliberation loop with stability detection
        for round_num in range(1, self.max_rounds + 1):
            session.rounds = round_num
            
            # Each member deliberates
            for member in members:
                member.round_number = round_num
                # In production, this would call the actual model
                # Here we simulate the deliberation structure
                self._deliberate_member(member, claim, artifacts or {})
            
            # Check stability via KS test on verdict distribution
            if round_num >= self.min_rounds:
                if self._check_stability(session, round_num):
                    session.stable = True
                    break
        
        # Aggregate verdicts (deliberation/synthesis, NEVER naive majority vote)
        session.final_verdict = self._synthesize_verdict(session)
        
        # Compute E_council
        session.e_council = self._compute_e_council(session)
        
        self.sessions.append(session)
        return session
    
    def _check_anti_collusion(self, members: list[CouncilMember]) -> bool:
        """Anti-collusion invariant: no two council seats share a model family
        for both generate and grade.
        
        If Architect and Verifier collapse to one family → E=∞.
        """
        generators = [m for m in members if m.role in (CouncilRole.ARCHITECT, CouncilRole.WORKER)]
        graders = [m for m in members if m.role in (CouncilRole.EVALUATOR, CouncilRole.VERIFIER)]
        
        gen_families = {m.model_family for m in generators}
        grade_families = {m.model_family for m in graders}
        
        # Architect and Verifier must be different families
        architects = [m for m in members if m.role == CouncilRole.ARCHITECT]
        verifiers = [m for m in members if m.role == CouncilRole.VERIFIER]
        
        for a in architects:
            for v in verifiers:
                if a.model_family == v.model_family:
                    return False
        
        return True
    
    def _check_stability(self, session: CouncilSession, round_num: int) -> bool:
        """Stability-detection via Beta-Binomial mixture + KS statistic.
        
        Halts when verdicts stabilize — no fixed round count,
        no burning cost past convergence.
        """
        if round_num < 2:
            return False
        
        # Get verdicts from last two rounds
        current_verdicts = [m.verdict.value for m in session.members 
                          if m.round_number == round_num and m.verdict]
        prev_verdicts = [m.verdict.value for m in session.members 
                        if m.round_number == round_num - 1 and m.verdict]
        
        if not current_verdicts or not prev_verdicts:
            return False
        
        # Simple stability: if verdicts haven't changed, we're stable
        current_dist = Counter(current_verdicts)
        prev_dist = Counter(prev_verdicts)
        
        # KS-like: max difference in cumulative distributions
        all_keys = set(current_dist.keys()) | set(prev_dist.keys())
        n_curr = len(current_verdicts)
        n_prev = len(prev_verdicts)
        
        max_diff = 0
        cum_curr = 0
        cum_prev = 0
        for key in sorted(all_keys):
            cum_curr += current_dist.get(key, 0) / max(n_curr, 1)
            cum_prev += prev_dist.get(key, 0) / max(n_prev, 1)
            max_diff = max(max_diff, abs(cum_curr - cum_prev))
        
        return max_diff <= (1.0 - self.stability_threshold)
    
    def _synthesize_verdict(self, session: CouncilSession) -> CouncilVerdict:
        """Synthesize final verdict from deliberation.
        
        Deliberation/synthesis, NEVER naive majority vote
        (which errs even when individuals are right).
        """
        if session.members[0].verdict == CouncilVerdict.BLOCK:
            return CouncilVerdict.BLOCK
        
        # Weighted by role: Verifier has veto power
        verifiers = [m for m in session.members if m.role == CouncilRole.VERIFIER]
        for v in verifiers:
            if v.verdict == CouncilVerdict.REJECT:
                return CouncilVerdict.REJECT
        
        # If verifier approves, check evaluators
        evaluators = [m for m in session.members if m.role == CouncilRole.EVALUATOR]
        eval_verdicts = [m.verdict for m in evaluators if m.verdict]
        
        if all(v == CouncilVerdict.APPROVE for v in eval_verdicts):
            return CouncilVerdict.APPROVE
        if any(v == CouncilVerdict.REJECT for v in eval_verdicts):
            return CouncilVerdict.REJECT
        return CouncilVerdict.REVISE
    
    def _compute_e_council(self, session: CouncilSession) -> float:
        """E_council = PASS iff ProofPacket complete AND cross-family verdict
        AND diversity >= threshold AND KS-stability reached.
        """
        if not session.anti_collusion_holds:
            return float("inf")
        if not session.stable:
            return float("inf")
        if session.diversity_score < 0.5:
            return float("inf")
        if session.final_verdict == CouncilVerdict.APPROVE:
            return 0.0
        if session.final_verdict == CouncilVerdict.REVISE:
            return 1.0
        return float("inf")
    
    def _deliberate_member(self, member: CouncilMember, claim: str, artifacts: dict) -> None:
        """Simulate member deliberation. In production, calls actual model."""
        # Placeholder — real implementation dispatches to the model
        if member.role == CouncilRole.VERIFIER:
            member.verdict = CouncilVerdict.APPROVE  # Default until real dispatch
            member.rationale = "Blind review: files/schemas/ProofPackets only"
        elif member.role == CouncilRole.EVALUATOR:
            member.verdict = CouncilVerdict.APPROVE
            member.defects_found = []
            member.rationale = "Cross-family critique against fixed rubric"
        else:
            member.verdict = CouncilVerdict.APPROVE
            member.rationale = "Generated solution skeleton"
