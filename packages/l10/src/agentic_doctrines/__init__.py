"""L10 Module: Agentic Doctrines Engine

Source: Synthesized from:
  - Agentic Coding School — Ray Amjad (2,800+ hrs)
  - Agentic Coding book — Ofri Wolfus (agenticoding.ai)
  - The Ideal Agentic Setup — Yaron Been
  - RIG TAC Doctrine — IndyDevDan
  - RIG Convergence Core

Purpose: Registry, selector, scorer, and evolver for the 10 Agentic Doctrines.
Encodes production-grade agentic coding patterns as a self-improving system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from ..common import BaseModule, ProofPacket
import hashlib
import json


MODULE_ID = "AD-01"
VERSION = "0.1.0"


class DoctrineID(str, Enum):
    """The 10 Agentic Doctrines."""
    FOUR_PHASE = "four-phase"           # Research > Plan > Execute > Validate
    CONTEXT_ENG = "context-engineering"  # Control what's in the window
    GROUNDING = "grounding"             # Inject reality before generation
    TESTS_GUARD = "tests-guardrails"     # Tests as constraint systems
    SPEC_DRIVEN = "spec-driven"         # Specs are scaffolding, code is truth
    FRESH_REVIEW = "fresh-review"       # Review in separate context
    EVIDENCE_DEBUG = "evidence-debug"   # Never accept fix without proof
    LOOP_ENG = "loop-engineering"       # Build-verify loops run without you
    PARALLEL = "parallelization"        # Multiple agents, multiple projects
    ONBOARDING = "onboarding"           # AGENTS.md / context files


@dataclass
class Doctrine:
    """A single agentic doctrine with metadata."""
    id: DoctrineID
    name: str
    principle: str
    trigger: str  # when to apply
    anti_patterns: list[str]
    rig_equivalent: str
    source: str
    effectiveness_score: float = 0.0  # 0-1, updated by evolver
    usage_count: int = 0


@dataclass
class TaskContext:
    """Context about the current task for doctrine selection."""
    task_type: str  # "feature", "bugfix", "refactor", "review", "debug", "setup"
    complexity: str  # "simple", "moderate", "complex"
    codebase_size: str  # "small" (<10k), "medium" (10k-100k), "large" (100k+)
    parallel: bool = False
    multi_session: bool = False
    has_tests: bool = False
    trust_level: str = "low"  # "low", "medium", "high"


# ─── The 10 Doctrines Registry ───

DOCTRINES: dict[DoctrineID, Doctrine] = {
    DoctrineID.FOUR_PHASE: Doctrine(
        id=DoctrineID.FOUR_PHASE,
        name="Four-Phase Workflow",
        principle="Research → Plan → Execute → Validate. Every significant agent interaction follows this pattern.",
        trigger="Always. This is the master workflow.",
        anti_patterns=["Jumping straight to code", "No research phase", "Skipping validation"],
        rig_equivalent="IQRSQPI (Intent → Question → Research → Solution → Quality → Proof → Integrate)",
        source="Ofri Wolfus (agenticoding.ai) + Ray Amjad",
    ),
    DoctrineID.CONTEXT_ENG: Doctrine(
        id=DoctrineID.CONTEXT_ENG,
        name="Context Engineering",
        principle="Control what's in the context window. The agent's entire world is the text flowing through it. Vague context → wandering behavior.",
        trigger="Before every agent interaction. Context is the control interface.",
        anti_patterns=["Dumping everything into context", "Ignoring signal-to-noise", "Not using progressive disclosure"],
        rig_equivalent="TAC Core Four (Context) + Hierarchical context files",
        source="Ray Amjad + Ofri Wolfus",
    ),
    DoctrineID.GROUNDING: Doctrine(
        id=DoctrineID.GROUNDING,
        name="Grounding",
        principle="Inject reality before generation. Without grounding, agents hallucinate plausible solutions from training data patterns.",
        trigger="Before any code generation. Ground in codebase + web sources.",
        anti_patterns=["Trusting agent's 'knowledge'", "Not requiring evidence", "Skipping codebase search"],
        rig_equivalent="Research step in IQRSQPI + GBrain semantic search",
        source="Ofri Wolfus",
    ),
    DoctrineID.TESTS_GUARD: Doctrine(
        id=DoctrineID.TESTS_GUARD,
        name="Tests as Guardrails",
        principle="Tests define operational boundaries agents cannot cross. They're living documentation that agents read to understand intent.",
        trigger="Before and during code generation. Tests are constraints, not afterthoughts.",
        anti_patterns=["Writing tests after code in same context", "Heavy mocking", "Green tests ≠ working software"],
        rig_equivalent="Gate 04 (Test Floor) + TDD skill",
        source="Ofri Wolfus",
    ),
    DoctrineID.SPEC_DRIVEN: Doctrine(
        id=DoctrineID.SPEC_DRIVEN,
        name="Spec-Driven Development",
        principle="Specs are temporary scaffolding. Code is the single source of truth. Delete specs after implementation; regenerate on-demand.",
        trigger="For features that need planning. Specs have a lifecycle.",
        anti_patterns=["Living specs that drift", "Spec as permanent artifact", "Two sources of truth"],
        rig_equivalent="OpenSpec BDD + IQRSQPI Spec step",
        source="Ofri Wolfus",
    ),
    DoctrineID.FRESH_REVIEW: Doctrine(
        id=DoctrineID.FRESH_REVIEW,
        name="Fresh-Context Review",
        principle="Review in a separate context from where code was written. An agent reviewing its own work in the same conversation will defend its decisions.",
        trigger="Every code review. Fresh context = objective analysis.",
        anti_patterns=["Reviewing in same conversation", "Agent reviewing own output", "Confirmation bias"],
        rig_equivalent="GEV Separation (Maker ≠ Grader ≠ Terminator)",
        source="Ofri Wolfus + Yaron Been + RIG Convergence Core",
    ),
    DoctrineID.EVIDENCE_DEBUG: Doctrine(
        id=DoctrineID.EVIDENCE_DEBUG,
        name="Evidence-Based Debugging",
        principle="Never accept a fix without reproducible proof it works. 'What do you think is wrong?' → 'Prove the bug exists, then prove your fix works.'",
        trigger="Every debugging session. Evidence at every step.",
        anti_patterns=["Accepting speculative fixes", "No reproduction script", "Not verifying fixes"],
        rig_equivalent="ProofPacket requirement + No mechanism, no claim",
        source="Ofri Wolfus",
    ),
    DoctrineID.LOOP_ENG: Doctrine(
        id=DoctrineID.LOOP_ENG,
        name="Loop Engineering",
        principle="Build-verify loops run without you. Inner loops build and verify features; outer loops supervise them; scheduled routines watch what you shipped.",
        trigger="For autonomous execution. The agent loops: build → verify → iterate.",
        anti_patterns=["No kill switch", "No verification in loop", "Babysitting every iteration"],
        rig_equivalent="Goal Loops + Closed Loops (Builder + Verifier)",
        source="Ray Amjad (Loopy AI module)",
    ),
    DoctrineID.PARALLEL: Doctrine(
        id=DoctrineID.PARALLEL,
        name="Parallelization",
        principle="Multiple terminal tabs = multiple agents working on different projects simultaneously. Git worktrees enable true parallelization without conflicts.",
        trigger="When you have multiple independent tasks. Don't serialize what can be parallel.",
        anti_patterns=["One agent at a time", "Shared git context", "No worktree isolation"],
        rig_equivalent="P-Threads (5-15 agents) + Fleet Toolchain",
        source="Ray Amjad + Ofri Wolfus + RIG TAC",
    ),
    DoctrineID.ONBOARDING: Doctrine(
        id=DoctrineID.ONBOARDING,
        name="Project Onboarding",
        principle="Codify project context in hierarchical, machine-readable files. AGENTS.md (vendor-neutral) or CLAUDE.md (hierarchical). Context files give agents 'project memory'.",
        trigger="When starting a new project or onboarding to an existing one.",
        anti_patterns=["No context files", "Outdated AGENTS.md", "Duplicated README content"],
        rig_equivalent="AGENTS.md / CLAUDE.md + Jake PAI Substrate + Doctrine files",
        source="Ofri Wolfus + Ray Amjad",
    ),
}


class AgenticDoctrines(BaseModule):
    """The Agentic Doctrines engine — registry, selector, scorer, evolver.

    Encodes 10 production-grade agentic coding doctrines as a self-improving system.
    Given a task context, recommends which doctrines apply and scores adherence.
    """

    MODULE_ID = MODULE_ID
    VERSION = VERSION

    def __init__(self):
        self.doctrines = DOCTRINES.copy()

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the doctrines engine.

        Args:
            input_data: Must contain 'action' and relevant params.
                action: 'select' | 'score' | 'list' | 'explain'
                task_context: TaskContext dict (for 'select')
                workflow_description: str (for 'score')

        Returns:
            Result with proof packet attached.
        """
        action = input_data.get("action", "select")

        if action == "select":
            ctx = TaskContext(**input_data.get("task_context", {}))
            result = self.select_doctrines(ctx)
        elif action == "score":
            result = self.score_adherence(
                input_data.get("workflow_description", ""),
                input_data.get("applied_doctrines", []),
            )
        elif action == "list":
            result = self.list_doctrines()
        elif action == "explain":
            result = self.explain_doctrine(input_data.get("doctrine_id", ""))
        else:
            result = {"error": f"Unknown action: {action}"}

        return {
            "result": result,
            "proof": self._seal_proof(input_data, result),
        }

    def select_doctrines(self, ctx: TaskContext) -> dict[str, Any]:
        """Select applicable doctrines for a task context.

        Returns doctrines ranked by relevance with application guidance.
        """
        applicable = []

        for did, doctrine in self.doctrines.items():
            relevance = self._compute_relevance(ctx, did)
            if relevance > 0.3:
                applicable.append({
                    "doctrine": doctrine.name,
                    "id": did.value,
                    "principle": doctrine.principle,
                    "relevance": round(relevance, 2),
                    "trigger": doctrine.trigger,
                    "anti_patterns": doctrine.anti_patterns[:2],
                    "rig_equivalent": doctrine.rig_equivalent,
                })

        applicable.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "task_type": ctx.task_type,
            "complexity": ctx.complexity,
            "recommended_doctrines": applicable,
            "always_apply": [
                "four-phase",
                "context-engineering",
            ],
        }

    def score_adherence(
        self, workflow_description: str, applied_doctrines: list[str]
    ) -> dict[str, Any]:
        """Score how well a workflow follows the doctrines.

        Returns adherence score and gaps.
        """
        total = len(self.doctrines)
        applied = set(applied_doctrines)
        missing = set(d.value for d in DoctrineID) - applied

        # Score based on how many doctrines are represented
        coverage = len(applied) / total if total > 0 else 0

        # Check for anti-pattern mentions
        anti_pattern_hits = []
        for did in DoctrineID:
            doctrine = self.doctrines[did]
            for ap in doctrine.anti_patterns:
                if ap.lower() in workflow_description.lower():
                    anti_pattern_hits.append({
                        "doctrine": doctrine.name,
                        "anti_pattern": ap,
                    })

        penalty = len(anti_pattern_hits) * 0.05
        score = max(0, coverage - penalty)

        return {
            "adherence_score": round(score, 2),
            "doctrines_applied": list(applied),
            "doctrines_missing": list(missing),
            "anti_pattern_hits": anti_pattern_hits,
            "recommendation": self._generate_recommendation(score, missing),
        }

    def list_doctrines(self) -> dict[str, Any]:
        """List all 10 doctrines with metadata."""
        return {
            "doctrines": [
                {
                    "id": d.id.value,
                    "name": d.name,
                    "principle": d.principle,
                    "source": d.source,
                    "effectiveness": d.effectiveness_score,
                    "usage_count": d.usage_count,
                }
                for d in self.doctrines.values()
            ],
            "total": len(self.doctrines),
        }

    def explain_doctrine(self, doctrine_id: str) -> dict[str, Any]:
        """Explain a specific doctrine in detail."""
        try:
            did = DoctrineID(doctrine_id)
        except ValueError:
            return {"error": f"Unknown doctrine: {doctrine_id}"}

        d = self.doctrines[did]
        return {
            "id": d.id.value,
            "name": d.name,
            "principle": d.principle,
            "trigger": d.trigger,
            "anti_patterns": d.anti_patterns,
            "rig_equivalent": d.rig_equivalent,
            "source": d.source,
            "effectiveness": d.effectiveness_score,
            "usage_count": d.usage_count,
        }

    def _compute_relevance(self, ctx: TaskContext, did: DoctrineID) -> float:
        """Compute how relevant a doctrine is to the task context."""
        score = 0.0

        # Always-relevant doctrines
        if did in (DoctrineID.FOUR_PHASE, DoctrineID.CONTEXT_ENG):
            score += 0.8

        # Task-type specific
        if ctx.task_type == "feature":
            if did in (DoctrineID.SPEC_DRIVEN, DoctrineID.TESTS_GUARD, DoctrineID.GROUNDING):
                score += 0.7
            if ctx.parallel and did == DoctrineID.PARALLEL:
                score += 0.9
            if ctx.multi_session and did == DoctrineID.SPEC_DRIVEN:
                score += 0.8

        elif ctx.task_type == "bugfix":
            if did == DoctrineID.EVIDENCE_DEBUG:
                score += 0.9
            if did == DoctrineID.GROUNDING:
                score += 0.7

        elif ctx.task_type == "review":
            if did == DoctrineID.FRESH_REVIEW:
                score += 0.95
            if did == DoctrineID.GROUNDING:
                score += 0.6

        elif ctx.task_type == "debug":
            if did == DoctrineID.EVIDENCE_DEBUG:
                score += 0.95
            if did == DoctrineID.TESTS_GUARD:
                score += 0.6

        elif ctx.task_type == "setup":
            if did == DoctrineID.ONBOARDING:
                score += 0.95

        # Complexity scaling
        if ctx.complexity == "complex":
            if did in (DoctrineID.LOOP_ENG, DoctrineID.PARALLEL):
                score += 0.5

        # Codebase size scaling
        if ctx.codebase_size == "large":
            if did == DoctrineID.GROUNDING:
                score += 0.3

        # Trust level
        if ctx.trust_level == "high":
            if did == DoctrineID.LOOP_ENG:
                score += 0.4
        elif ctx.trust_level == "low":
            if did in (DoctrineID.FRESH_REVIEW, DoctrineID.EVIDENCE_DEBUG):
                score += 0.3

        return min(1.0, score)

    def _generate_recommendation(self, score: float, missing: set) -> str:
        """Generate a recommendation based on adherence score."""
        if score >= 0.85:
            return "Excellent adherence. Workflow follows production-grade practices."
        elif score >= 0.65:
            gaps = ", ".join(sorted(missing)[:3])
            return f"Good adherence. Consider adding: {gaps}"
        elif score >= 0.45:
            gaps = ", ".join(sorted(missing)[:5])
            return f"Moderate adherence. Key gaps: {gaps}"
        else:
            return "Low adherence. Review the Agentic Doctrines and apply the missing doctrines."

    def _seal_proof(self, input_data: dict, result: dict) -> dict:
        """Create proof packet for this run."""
        return {
            "module_id": self.MODULE_ID,
            "version": self.VERSION,
            "input_hash": hashlib.sha256(
                json.dumps(input_data, sort_keys=True).encode()
            ).hexdigest(),
            "output_hash": hashlib.sha256(
                json.dumps(result, sort_keys=True).encode()
            ).hexdigest(),
        }
