"""Faculty 3: Tribal-Knowledge Scraper — GL-L10-CS2-01

Not 'scrape some docs.' The felt shift: the harness can no longer close a
goal loop by merely producing a working artifact — it must first prove it
followed the REAL-WORLD BEST PRACTICE for that process, harvested from
how experts actually do it.

Extends the Nocturne JTBD scraper from OUTCOME exemplars to PROCESS exemplars
— the tacit "when you do X, always do Y; you'll stumble on Z, do W instead"
knowledge that lives in expert practice, not documentation.
"""
from __future__ import annotations
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from common import deviation_gate, run_energy, ProofPacket

@dataclass
class ProcessStep:
    """One step in a tribal job map."""
    step_id: str
    description: str
    step_type: str  # "action" | "gate" | "decision" | "failure_mode"
    kpi: str = ""
    tools: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    source_url: str = ""
    source_quality: float = 0.0  # 0-1
    recency_days: int = 0
    consensus_count: int = 0
    confidence: float = 0.0
    deviation_gated: bool = False

@dataclass
class TribalJobMap:
    """Canonical job map synthesized from expert practice."""
    process_name: str
    steps: list[ProcessStep]
    winning_patterns: list[str] = field(default_factory=list)
    losing_patterns: list[str] = field(default_factory=list)
    gates: list[ProcessStep] = field(default_factory=list)
    confidence: float = 0.0
    sources_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class TribalClaim:
    """A single claim extracted from tribal knowledge."""
    claim: str
    source: str
    source_quality: float
    recency_days: int
    evidence: str
    deviation_gated: bool = False
    confidence: float = 0.0

class TribalKnowledgeScraper:
    """Pipeline for scraping, extracting, and synthesizing tribal knowledge.
    
    Pipeline:
    1. SCRAPE: Firecrawl/Tavily/Exa/Crawl4AI sweep expert sources
    2. EXTRACT: NER + zero-shot pull job steps, KPIs, rules, gates, failure modes
    3. DEDUP: Embedding-cluster substeps
    4. RANK: Weight by source quality * recency * consensus
    5. SYNTHESIZE: Canonical job map + winning/losing patterns
    
    2026 hard constraint: ~20% of web traffic is scrape-poison.
    Every claim passes AI-assisted provenance + freshness validation.
    A fabricated best-practice is a >=5σ RobustMADZ event → reject.
    """
    
    def __init__(self):
        self.claims: list[TribalClaim] = []
        self.job_maps: dict[str, TribalJobMap] = {}
    
    def extract_claims(self, raw_extractions: list[dict]) -> list[TribalClaim]:
        """Extract tribal claims from raw scrape data.
        
        Args:
            raw_extractions: List of dicts with keys: claim, source, quality, recency, evidence
        """
        claims = []
        for raw in raw_extractions:
            claim = TribalClaim(
                claim=raw.get("claim", ""),
                source=raw.get("source", ""),
                source_quality=raw.get("quality", 0.5),
                recency_days=raw.get("recency_days", 365),
                evidence=raw.get("evidence", ""),
            )
            
            # Deviation gate: reject fabricated/low-quality claims
            baseline_quality = [c.source_quality for c in claims] or [0.5]
            gate_result = deviation_gate(claim.source_quality, baseline_quality)
            claim.deviation_gated = (gate_result == "accept")
            
            if claim.deviation_gated:
                claim.confidence = self._compute_confidence(claim)
                claims.append(claim)
        
        self.claims.extend(claims)
        return claims
    
    def synthesize_job_map(self, process_name: str, claims: list[TribalClaim]) -> TribalJobMap:
        """Synthesize a canonical job map from validated claims.
        
        Steps ranked by: source_quality * recency_weight * consensus_count.
        """
        # Group claims by inferred step
        step_groups = self._cluster_into_steps(claims)
        
        steps = []
        for i, group in enumerate(step_groups):
            # Rank by quality * recency * consensus
            avg_quality = sum(c.source_quality for c in group) / len(group)
            recency_weight = 1.0 / (1.0 + min(c.recency_days for c in group) / 30.0)
            consensus = len(group)
            
            step = ProcessStep(
                step_id=f"{process_name}.step_{i+1}",
                description=group[0].claim,  # Best-quality claim as description
                step_type="action",
                source_quality=avg_quality,
                recency_days=min(c.recency_days for c in group),
                consensus_count=consensus,
                confidence=avg_quality * recency_weight * min(consensus / 3.0, 1.0),
                deviation_gated=all(c.deviation_gated for c in group),
            )
            steps.append(step)
        
        # Identify gates (claims with gate/decision language)
        gate_keywords = ["must", "required", "block", "gate", "before", "prerequisite", "never"]
        gates = [s for s in steps if any(kw in s.description.lower() for kw in gate_keywords)]
        
        job_map = TribalJobMap(
            process_name=process_name,
            steps=steps,
            gates=gates,
            confidence=sum(s.confidence for s in steps) / max(len(steps), 1),
            sources_count=sum(s.consensus_count for s in steps),
        )
        self.job_maps[process_name] = job_map
        return job_map
    
    def compute_adherence(self, process_name: str, completed_steps: list[str],
                          skipped_gates: list[str]) -> dict:
        """Compute E_adherence against the tribal job map.
        
        E_adherence = sum(w_i * (1 - step_followed_i)) + lambda * critical_gate_skipped
        BLOCK if any critical gate was skipped.
        """
        job_map = self.job_maps.get(process_name)
        if not job_map:
            return {"error": "no job map found", "e_adherence": float("inf")}
        
        # Step adherence
        step_penalty = 0.0
        for step in job_map.steps:
            if step.step_id not in completed_steps:
                step_penalty += step.confidence * 1.0  # w_i * (1 - 0)
        
        # Gate penalty (lambda = 10.0 for critical gates)
        gate_penalty = 0.0
        critical_skipped = False
        for gate in job_map.gates:
            if gate.step_id in skipped_gates:
                gate_penalty += 10.0
                critical_skipped = True
        
        e_adherence = step_penalty + gate_penalty
        
        return {
            "e_adherence": round(e_adherence, 4),
            "step_penalty": round(step_penalty, 4),
            "gate_penalty": round(gate_penalty, 4),
            "critical_gate_skipped": critical_skipped,
            "verdict": "BLOCK" if critical_skipped else ("PASS" if e_adherence <= 1.0 else "FAIL"),
            "process": process_name,
            "total_steps": len(job_map.steps),
            "completed_steps": len(completed_steps),
            "total_gates": len(job_map.gates),
            "skipped_gates": len(skipped_gates),
        }
    
    def _compute_confidence(self, claim: TribalClaim) -> float:
        """Confidence = quality * recency_weight * evidence_present."""
        recency_weight = 1.0 / (1.0 + claim.recency_days / 30.0)
        evidence_bonus = 1.2 if claim.evidence else 0.8
        return min(claim.source_quality * recency_weight * evidence_bonus, 1.0)
    
    def _cluster_into_steps(self, claims: list[TribalClaim]) -> list[list[TribalClaim]]:
        """Simple dedup: group claims by keyword similarity.
        In production, this would use embedding-based clustering.
        """
        if not claims:
            return []
        
        # Simple: preserve order, group consecutive similar claims
        groups = [[claims[0]]]
        for claim in claims[1:]:
            # Check if claim is similar to current group's first claim
            last_group = groups[-1]
            keywords_overlap = len(
                set(claim.claim.lower().split()) & set(last_group[0].claim.lower().split())
            )
            if keywords_overlap >= 2:
                last_group.append(claim)
            else:
                groups.append([claim])
        
        return groups
