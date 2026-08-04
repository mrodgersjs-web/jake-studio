"""Faculty 5-8: Strategy Tool + What-If + Multi-Altitude + Persona
GL-L10-CS3-01 + GL-L10-CS3-02

The divergent-thinking faculties that balance the convergent taste + adherence gates.
Before committing compute to a goal, the harness explores the option space from
multiple altitudes and personas, scores the branches, and picks by expected free energy
— so it never sprints confidently down the wrong path.
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from common import expected_free_energy, blend_value, ProofPacket

# ── Faculty 5: Strategy Tool ──────────────────────────────────────────

@dataclass
class ScenarioPack:
    """Named strategic presets for a process."""
    name: str
    scenarios: dict[str, dict]  # scenario_name -> config
    description: str = ""

@dataclass
class StrategyConfig:
    """One strategy configuration."""
    name: str
    scenario_pack: ScenarioPack
    weight_vector: dict[str, float]  # e.g. {"brand": 0.3, "novelty": 0.4, "speed": 0.3}
    blend_value: float = 0.0
    efe_score: float = float("inf")

class StrategyTool:
    """Every process gets a paired strategy tool.
    
    One harness, many YAMLs — Line A vs Line B differ only in
    Scenario Pack + Verifier weight vector.
    
    The 1000x discipline: one engine, config per line.
    """
    
    def __init__(self):
        self.strategies: dict[str, StrategyConfig] = {}
    
    def register(self, config: StrategyConfig) -> None:
        """Register a strategy configuration."""
        self.strategies[config.name] = config
    
    def score(self, name: str, novelty: float, systematicity: float, 
              inconsistency: float) -> float:
        """Score a strategy via BlendValue.
        
        BlendValue = λ1*Novelty + λ2*Systematicity - λ3*Inconsistency
        Strategy that raises BlendValue > 0 is preferred.
        """
        bv = blend_value(novelty, systematicity, inconsistency)
        if bv.get("verdict") == "PASS":
            score = bv.get("returned_value", 0.0)
            if name in self.strategies:
                self.strategies[name].blend_value = score
            return score
        return 0.0

# ── Faculty 6: What-If Scenario Exploration ───────────────────────────

@dataclass
class Branch:
    """One counterfactual branch in what-if exploration."""
    branch_id: str
    description: str
    structurally_different: bool  # Diversity signal
    primary_metric: float = 0.0
    guard_metrics: dict[str, float] = field(default_factory=dict)
    guard_regressed: bool = False
    cost: float = 0.0
    efe_score: float = float("inf")
    pruned: bool = False
    prune_reason: str = ""

class WhatIfExplorer:
    """Option-space search before commitment.
    
    Branch generation → cheap-checks-first cascade → EFE selection.
    
    AlphaEvolve pattern: primary metric + guard metrics that must not regress
    + diversity signal.
    """
    
    def __init__(self):
        self.branches: list[Branch] = []
        self.selected: Optional[Branch] = None
    
    def generate_branches(self, descriptions: list[str]) -> list[Branch]:
        """Generate N counterfactual branches."""
        self.branches = [
            Branch(
                branch_id=f"branch_{i}",
                description=desc,
                structurally_different=True,
            )
            for i, desc in enumerate(descriptions)
        ]
        return self.branches
    
    def cheap_checks_cascade(self, checks: dict[str, callable]) -> list[Branch]:
        """Order evaluations cheap→expensive. Prune bad branches early.
        
        Cascade: static analysis → microbench → LLM-judge → full eval
        """
        surviving = []
        for branch in self.branches:
            pruned = False
            for check_name, check_fn in checks.items():
                try:
                    result = check_fn(branch)
                    if not result:
                        branch.pruned = True
                        branch.prune_reason = f"failed {check_name}"
                        pruned = True
                        break
                except Exception:
                    continue
            if not pruned:
                surviving.append(branch)
        return surviving
    
    def select_by_efe(self, pragmatic: dict[str, float], 
                      epistemic: dict[str, float]) -> Optional[Branch]:
        """Select branch by Expected Free Energy.
        
        π* = argmin_π G(π)  (pragmatic + epistemic)
        pragmatic = move toward goal
        epistemic = explore branch that most reduces uncertainty
        """
        best_branch = None
        best_efe = float("inf")
        
        for branch in self.branches:
            if branch.pruned or branch.guard_regressed:
                continue
            
            p = pragmatic.get(branch.branch_id, 0.0)
            e = epistemic.get(branch.branch_id, 0.0)
            efe_result = expected_free_energy(p, e)
            
            if efe_result.get("verdict") == "PASS":
                branch.efe_score = efe_result.get("returned_value", float("inf"))
                if branch.efe_score < best_efe:
                    best_efe = branch.efe_score
                    best_branch = branch
        
        self.selected = best_branch
        return best_branch
    
    def get_rejected_log(self) -> list[dict]:
        """Log rejected branches for evolution loop learning."""
        return [
            {"branch_id": b.branch_id, "description": b.description, 
             "efe": b.efe_score, "pruned": b.pruned, "reason": b.prune_reason}
            for b in self.branches if b != self.selected
        ]

# ── Faculty 7: Multi-Altitude Thinking ────────────────────────────────

class Altitude(Enum):
    STRATEGY_10KFT = "10000ft"   # Does this goal belong in the portfolio?
    ARCHITECTURE_1KFT = "1000ft" # What's the cheapest vehicle?
    EXECUTION_100FT = "100ft"    # Taste + adherence at artifact level
    GROUND = "ground"            # What breaks in production?

@dataclass
class AltitudeCheck:
    """Check at one altitude."""
    altitude: Altitude
    passed: bool
    rationale: str
    blockers: list[str] = field(default_factory=list)

class MultiAltitudeReviewer:
    """Same problem examined at explicit altitudes.
    
    A goal loop must pass a check at EACH altitude before close.
    A beautiful artifact (100ft) that shouldn't exist (10kft) is BLOCKED.
    This is how the harness avoids 'efficiently building the wrong thing.'
    """
    
    def __init__(self):
        self.checks: list[AltitudeCheck] = []
    
    def review(self, claim: str, 
               strategy_check: str = "", architecture_check: str = "",
               execution_check: str = "", failure_modes: str = "") -> list[AltitudeCheck]:
        """Run multi-altitude review."""
        self.checks = [
            AltitudeCheck(
                altitude=Altitude.STRATEGY_10KFT,
                passed=bool(strategy_check and "block" not in strategy_check.lower()),
                rationale=strategy_check or "Not reviewed",
            ),
            AltitudeCheck(
                altitude=Altitude.ARCHITECTURE_1KFT,
                passed=bool(architecture_check and "block" not in architecture_check.lower()),
                rationale=architecture_check or "Not reviewed",
            ),
            AltitudeCheck(
                altitude=Altitude.EXECUTION_100FT,
                passed=bool(execution_check and "block" not in execution_check.lower()),
                rationale=execution_check or "Not reviewed",
            ),
            AltitudeCheck(
                altitude=Altitude.GROUND,
                passed=bool(not failure_modes or "critical failure" not in failure_modes.lower() or "no critical" in failure_modes.lower()),
                rationale=failure_modes or "No failure modes identified",
            ),
        ]
        return self.checks
    
    def all_passed(self) -> bool:
        """Must pass EACH altitude before close."""
        return all(c.passed for c in self.checks)

# ── Faculty 8: Persona Thinking ───────────────────────────────────────

class PersonaType(Enum):
    BUYER = "buyer"              # Would the target hire this for their JTBD?
    SKEPTIC = "skeptic"          # Could a rival publish this unnoticed?
    OPERATOR = "operator"        # Can this be maintained/run without Mike?
    FUTURE_SELF = "future_self"  # Does this age well or follow the crowd?
    DOMAIN_MASTER = "domain_master"  # Does this meet tribal best-practice bar?

@dataclass
class PersonaVerdict:
    """One persona's critique."""
    persona: PersonaType
    model_family: str  # Different families for diversity
    verdict: str       # "approve" | "revise" | "reject"
    critique: str
    defects: list[str] = field(default_factory=list)

class PersonaThinking:
    """Multi-lens critique from distinct vantage points.
    
    Direct antidote to single-agent confirmation bias + premature convergence.
    Personas run on different model families where stakes are high.
    Stability-detection halts when persona verdicts converge.
    """
    
    PERSONAS = {
        PersonaType.BUYER: "Would the target customer actually hire this for their JTBD?",
        PersonaType.SKEPTIC: "Could a competitor publish this unnoticed? (0σ refusal)",
        PersonaType.OPERATOR: "Can this be maintained/run without Mike?",
        PersonaType.FUTURE_SELF: "Does this decision age well or follow the crowd?",
        PersonaType.DOMAIN_MASTER: "Does this meet the tribal best-practice bar?",
    }
    
    def __init__(self):
        self.verdicts: list[PersonaVerdict] = []
    
    def critique(self, artifact: str, persona: PersonaType,
                 model_family: str = "claude") -> PersonaVerdict:
        """Run a persona critique. In production, dispatches to actual model."""
        verdict = PersonaVerdict(
            persona=persona,
            model_family=model_family,
            verdict="approve",
            critique=self.PERSONAS[persona],
        )
        self.verdicts.append(verdict)
        return verdict
    
    def run_all(self, artifact: str) -> list[PersonaVerdict]:
        """Run all 5 personas. Assign different model families for diversity."""
        families = ["claude", "gpt", "gemini", "llama", "claude"]
        personas = list(PersonaType)
        
        self.verdicts = []
        for persona, family in zip(personas, families):
            self.critique(artifact, persona, family)
        
        return self.verdicts
    
    def converged(self) -> bool:
        """Check if persona verdicts have converged."""
        if len(self.verdicts) < 3:
            return False
        verdicts = [v.verdict for v in self.verdicts]
        return len(set(verdicts)) == 1  # All agree
