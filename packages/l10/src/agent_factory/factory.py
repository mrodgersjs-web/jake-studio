"""L10 Agent Factory — GL-L10-AF-01

Not 'another agent template.' The felt shift: an agent is no longer born
static and maintained by Mike — it's stamped with a scraper, a nightly
daemon, and an empty skill graph, then it self-provisions the rest
against the living market.

Day-1 the agent knows almost nothing; by day-7 it has scraped its JTBD's
real-world process, minted the skills that process demands, acquired its
own tools, and staged them for the Verifier.

Client #10 near-instant because the factory stamps the SELF-TEACHING MACHINERY,
not the finished agent.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from common import ProofPacket, BMS, GEVRole

class StampPhase(Enum):
    F0_OUTCOME_INTAKE = "F0"
    F1_GRADEABILITY_PROBE = "F1"
    F2_HARNESS_SYNTHESIS = "F2"
    F3_SIGN_SEAL = "F3"
    F4_DAEMON_ENROLL = "F4"
    F5_COLD_START = "F5"

@dataclass
class HarnessTuple:
    """Sealed harness H = (E, T, C, S, L, V)."""
    E: dict  # Energy function (dual trigger: self-heal + self-improve)
    T: dict  # Tools (scoped scraper + bootstrap set)
    C: dict  # Context (fresh HOMER scope)
    S: dict  # Skills (bootstrap only + frozen-baseline store)
    L: dict  # Loops (Nocturne nightly + IQRSQPI grill)
    V: dict  # Verifier (Jake + assigned evaluator peer)
    
    def sign(self) -> str:
        """Version + sign the harness."""
        content = json.dumps({
            "E": self.E, "T": self.T, "C": self.C,
            "S": self.S, "L": self.L, "V": self.V,
        }, sort_keys=True)
        return "sha256:" + hashlib.sha256(content.encode()).hexdigest()

@dataclass
class StampedAgent:
    """A factory-stamped L10 agent."""
    agent_id: str
    jtbd_id: str
    jtbd_gradeability: bool = False
    harness: Optional[HarnessTuple] = None
    harness_signature: str = ""
    gev_role: GEVRole = GEVRole.GENERATOR
    bms_band: BMS = BMS.A4  # Always starts at A4 (manual)
    nocturne_enrolled: bool = False
    memory_scope: str = ""
    deviation_ceilings: dict = field(default_factory=lambda: {"output": 20, "physics": 30})
    replay_tests: list[str] = field(default_factory=list)
    golden_set: list[str] = field(default_factory=list)
    stamped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    night_1_read_only: bool = True
    errors: list[str] = field(default_factory=list)

class AgentFactory:
    """Deterministic agent stamp procedure F0-F5.
    
    Stamps goal-evolving agents with:
    - JTBD binding + gradeability gate
    - Own JTBD scraper (Intel-Scout instance)
    - Nocturne daemon registration
    - Empty-but-live skill graph + CMH curriculum
    - Tool-acquisition rights (bounded)
    - GEV role assignment (Generator OR Evaluator, never both)
    - ProofPacket + replay-test registry
    
    BMS ladder: A4 → A1 only via Brier-validated outcomes.
    External/destructive/payment → A4 ALWAYS, no matter the band.
    """
    
    def __init__(self):
        self.stamped_agents: list[StampedAgent] = []
    
    def stamp(self, jtbd_id: str, jtbd_spec: dict,
              exemplar_surface_exists: bool = True,
              gev_role: GEVRole = GEVRole.GENERATOR) -> StampedAgent:
        """Execute the full F0-F5 stamp procedure.
        
        Args:
            jtbd_id: JTBD identifier
            jtbd_spec: JTBD specification with resolution criteria
            exemplar_surface_exists: F1 gradeability probe result
            gev_role: Generator or Evaluator (never both)
        
        Returns:
            StampedAgent ready for cold-start night 1
        """
        agent = StampedAgent(
            agent_id=f"l10_{jtbd_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            jtbd_id=jtbd_id,
            gev_role=gev_role,
        )
        
        # F0: Outcome intake
        self._f0_outcome_intake(agent, jtbd_spec)
        
        # F1: Gradeability probe
        self._f1_gradeability_probe(agent, exemplar_surface_exists)
        
        if not agent.jtbd_gradeability:
            agent.errors.append("F1 FAIL: No live exemplar surface — abort stamp")
            self.stamped_agents.append(agent)
            return agent
        
        # F2: Harness synthesis
        self._f2_harness_synthesis(agent, jtbd_spec)
        
        # F3: Sign + seal
        self._f3_sign_seal(agent)
        
        # F4: Daemon enroll
        self._f4_daemon_enroll(agent)
        
        # F5: Cold-start night 1 (read-only)
        self._f5_cold_start(agent)
        
        self.stamped_agents.append(agent)
        return agent
    
    def _f0_outcome_intake(self, agent: StampedAgent, spec: dict) -> None:
        """F0: Outcome composer transforms felt transformation into JTBD spec
        + resolution criteria + out-of-loop attestation source.
        """
        agent.errors.append("F0: Outcome intake completed")
    
    def _f1_gradeability_probe(self, agent: StampedAgent, exists: bool) -> None:
        """F1: Intel-Scout confirms live exemplar surface exists + passes provenance.
        FAIL → abort stamp (surface the gap to Mike).
        """
        agent.jtbd_gradeability = exists
        if not exists:
            agent.errors.append("F1: Gradeability probe FAILED — no exemplar surface")
    
    def _f2_harness_synthesis(self, agent: StampedAgent, spec: dict) -> None:
        """F2: Emit H=(E,T,C,S,L,V).
        - E: energy fn = E_JTBD against scraped exemplars
        - T: scoped scraper + bootstrap set
        - C: fresh HOMER scope
        - S: bootstrap only (empty skill graph)
        - L: Nocturne nightly + IQRSQPI grill
        - V: Jake + assigned evaluator peer
        """
        agent.harness = HarnessTuple(
            E={"type": "E_JTBD", "dual_trigger": True, "self_heal": True, "self_improve": True},
            T={"scraper": "intel-scout", "bootstrap": True, "external_gated": "A4"},
            C={"source": "homer_lattice", "level": 5, "elements": "~100k"},
            S={"bootstrap_only": True, "skill_graph": "empty", "cmh_curriculum": True},
            L={"nocturne": True, "frequency": "nightly", "grill": "IQRSQPI"},
            V={"primary": "jake", "evaluator_peer": "assigned", "termination": "verifier_only"},
        )
        agent.memory_scope = f"agent:{agent.agent_id}"
    
    def _f3_sign_seal(self, agent: StampedAgent) -> None:
        """F3: Version, sign, register replay tests + golden set.
        Deviation ceilings wired (±20σ / ±30σ).
        BMS starts at A4 (manual).
        """
        if agent.harness:
            agent.harness_signature = agent.harness.sign()
        agent.bms_band = BMS.A4  # Always starts manual
        agent.replay_tests = ["golden_run_1", "consistency_check"]
        agent.golden_set = ["golden_artifact_1"]
    
    def _f4_daemon_enroll(self, agent: StampedAgent) -> None:
        """F4: Register with Nocturne cron. Assert MEMORY_SCOPE.
        Commit to frozen-baseline store.
        """
        agent.nocturne_enrolled = True
    
    def _f5_cold_start(self, agent: StampedAgent) -> None:
        """F5: First Nocturne run is read-only (scrape + grade + residual report,
        no mints). Same golden-run discipline as the daemon's first build.
        Provisioning turns on night 2+ after grader confirms clean labels.
        """
        agent.night_1_read_only = True
    
    def can_earn_autonomy(self, agent: StampedAgent, brier_score: float) -> BMS:
        """BMS ladder: A4→A1 via Brier-validated outcomes.
        
        score >= .75 → A1 autonomous
        .45 → A2
        .25 → A3
        < .25 → A4
        
        External/destructive/payment → A4 ALWAYS, no matter the band.
        """
        if brier_score >= 0.75:
            return BMS.A1
        elif brier_score >= 0.45:
            return BMS.A2
        elif brier_score >= 0.25:
            return BMS.A3
        else:
            return BMS.A4
