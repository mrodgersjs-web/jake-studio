"""Faculty 1: The Taste Engine — GL-L10-CS1-01

Not 'a vibe check.' The taste engine is a SKILL + KPI system that grades
output on 5 calibrated dimensions. Where checking is as hard as doing
(taste, judgment, strategy), the self-improvement loop gets stuck and the
system fools its own checker (Tao's 67-problem result).

So taste verdicts are SCALABLE-OVERSIGHT-GATED:
Mike's verdict is mandatory-human, no autonomous certification.

But taste IS grade-able if you write the opinion down strongly enough.
(Anthropic post-training doctrine)
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from common import ProofPacket, BMS, Confidence

class ShipBand(Enum):
    SHIP_WITH_PRIDE = "ship_with_pride"  # >= 4.5
    SHIP_POLISH_LATER = "ship_polish_later"  # 4.0 - 4.4
    TIMELINE_ONLY = "timeline_only"  # 3.5 - 3.9
    REVISE = "revise"  # < 3.5
    REWORK = "rework"  # < 3.0

@dataclass
class TasteDimension:
    """One dimension of the 5-dim taste rubric."""
    name: str
    weight: float  # 0.0 - 1.0, sum = 1.0
    description: str
    score: float = 0.0  # 1.0 - 5.0
    evidence: str = ""

@dataclass
class TasteAudit:
    """Complete taste audit result."""
    artifact_id: str
    dimensions: list[TasteDimension]
    composite_score: float = 0.0
    ship_band: ShipBand = ShipBand.REVISE
    signature_replay_blocked: bool = False
    signature_replay_reason: str = ""
    off_signature: bool = False
    auditor_model: str = ""
    mike_reviewed: bool = False
    mike_override: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ── The 5-Dim Rubric ──────────────────────────────────────────────────
TASTE_RUBRIC = {
    "intentionality": TasteDimension(
        name="Intentionality",
        weight=0.30,
        description="Is every element deliberate? Does nothing feel accidental or default?",
    ),
    "craft_quality": TasteDimension(
        name="Craft Quality",
        weight=0.25,
        description="Precise + consistent execution? No rough edges or half-measures?",
    ),
    "ai_slop": TasteDimension(
        name="AI-Slop Check",
        weight=0.20,
        description="Generic AI patterns present? 'Delve', 'tapestry', 'comprehensive solution'?",
    ),
    "writing_voice": TasteDimension(
        name="Writing/Voice",
        weight=0.15,
        description="Sounds human / on-signature? Distinct voice, not corporate-LLM neutral?",
    ),
    "accessibility": TasteDimension(
        name="Accessibility/Baseline",
        weight=0.10,
        description="Standards met? Format correct? No obvious oversights?",
    ),
}

# ── Supporting Taste Skills (allowlist) ────────────────────────────────
TASTE_SKILLS = {
    "design-ranking": "Rank + explain designs. Separate preference from quality.",
    "taste-vs-trends": "Does this age well, or follow the crowd?",
    "tradeoff-assessment": "Evaluate the tradeoffs made in this artifact.",
    "taste-gap": "Ira Glass gap — the gap between taste and current ability.",
    "taste-as-strategy": "Execution is commoditized; taste is the moat.",
    "constraint-evaluation": "What constraints shaped this? Were they the right ones?",
}

class TasteEngine:
    """Calibrated, self-improving, replayable taste system.
    
    Signature-replay proof obligation: the taste verifier must be able to
    BLOCK a technically-clean, slop-free artifact purely for being OFF-SIGNATURE
    — and log why. If it can't do that, it's a QA tool, not an art director.
    
    Crystallization claim: taste captured as a calibrated, self-improving,
    replayable system compounds — it gets monotonically more 'you' each week.
    That's the superhuman move: not one masterpiece, a system.
    """
    
    def __init__(self, signature_description: str = ""):
        self.signature = signature_description
        self.audits: list[TasteAudit] = []
        self.calibrated = False  # Set True after Mike reviews rubric
    
    def audit(self, artifact_id: str, content: str,
              scores: dict[str, float],
              signature_check: Optional[dict] = None,
              auditor_model: str = "claude") -> TasteAudit:
        """Run a taste audit on an artifact.
        
        Args:
            artifact_id: ID of the artifact
            content: The artifact content (for signature check)
            scores: Dict of dimension_name -> score (1.0-5.0)
            signature_check: Optional dict with 'off_signature' bool and 'reason' str
            auditor_model: Model family of the auditor
        
        Returns:
            TasteAudit with composite score and ship band
        """
        dimensions = []
        for dim_key, dim_template in TASTE_RUBRIC.items():
            dim = TasteDimension(
                name=dim_template.name,
                weight=dim_template.weight,
                description=dim_template.description,
                score=scores.get(dim_key, 0.0),
            )
            dimensions.append(dim)
        
        # Composite: weighted sum
        composite = sum(d.weight * d.score for d in dimensions)
        
        # Ship band
        if composite >= 4.5:
            band = ShipBand.SHIP_WITH_PRIDE
        elif composite >= 4.0:
            band = ShipBand.SHIP_POLISH_LATER
        elif composite >= 3.5:
            band = ShipBand.TIMELINE_ONLY
        elif composite >= 3.0:
            band = ShipBand.REVISE
        else:
            band = ShipBand.REWORK
        
        # Signature-replay check
        sig_blocked = False
        sig_reason = ""
        off_sig = False
        if signature_check:
            off_sig = signature_check.get("off_signature", False)
            sig_reason = signature_check.get("reason", "")
            if off_sig:
                sig_blocked = True
                band = ShipBand.REVISE  # Downgrade
        
        audit = TasteAudit(
            artifact_id=artifact_id,
            dimensions=dimensions,
            composite_score=round(composite, 2),
            ship_band=band,
            signature_replay_blocked=sig_blocked,
            signature_replay_reason=sig_reason,
            off_signature=off_sig,
            auditor_model=auditor_model,
        )
        self.audits.append(audit)
        return audit
    
    def request_mike_review(self, audit: TasteAudit, override_score: Optional[float] = None) -> TasteAudit:
        """Escalate to Mike for scalable oversight.
        
        Where checking is as hard as doing — taste/strategy outcomes —
        Jake's verdict is mandatory-human. No autonomous certification.
        """
        audit.mike_reviewed = True
        if override_score is not None:
            audit.mike_override = override_score
            audit.composite_score = override_score
            # Recompute band
            if override_score >= 4.5:
                audit.ship_band = ShipBand.SHIP_WITH_PRIDE
            elif override_score >= 4.0:
                audit.ship_band = ShipBand.SHIP_POLISH_LATER
            elif override_score >= 3.5:
                audit.ship_band = ShipBand.TIMELINE_ONLY
            elif override_score >= 3.0:
                audit.ship_band = ShipBand.REVISE
            else:
                audit.ship_band = ShipBand.REWORK
        return audit
    
    def get_calibration_summary(self) -> dict:
        """Summary of all audits for Mike's calibration."""
        if not self.audits:
            return {"audits": 0, "calibrated": self.calibrated}
        
        avg = sum(a.composite_score for a in self.audits) / len(self.audits)
        bands = {}
        for a in self.audits:
            bands[a.ship_band.value] = bands.get(a.ship_band.value, 0) + 1
        
        return {
            "audits": len(self.audits),
            "avg_composite": round(avg, 2),
            "ship_bands": bands,
            "blocked_for_signature": sum(1 for a in self.audits if a.signature_replay_blocked),
            "mike_reviewed": sum(1 for a in self.audits if a.mike_reviewed),
            "calibrated": self.calibrated,
            "supported_skills": list(TASTE_SKILLS.keys()),
        }
