# RIG L10 SELF-EVOLVING HARNESS STACK — DOCTRINE

Version: 2026-07-22.1
Owner: Mike Rodgers
Status: ACTIVE — SIGNED
Scope: All RIG harnesses (Claude Code, Codex, Hermes, Jake)
Module: `/Users/rig128gb/rig-l10/src/`
Companion doctrines:
  - `/Users/rig128gb/.rig/agent-doctrine/RIG_TAC_DOCTRINE.md` (load first)
  - `/Users/rig128gb/.rig/agent-doctrine/JAKE_OPENSPEC_BDD_WORK_DOCTRINE.md` (load second)

---

## The One-Line Doctrine

The harness stops *arguing* that something is great and starts *proving or
refuting* it with checkers that cannot be talked to.

---

## Operating Rule

For any meaningful build, review, evaluation, or self-improvement work, Jake
loads TAC first, then OpenSpec BDD, then this doctrine. L10 provides the
verification faculties that make goal-loop closure *falsifiable* — not vibes,
not plausible arguments, but structured evidence that survives refutation.

This is not a public-action grant. Gate-D still governs all public actions.

---

## When to Load

Load this doctrine when any of these are true:

- Mike asks Jake to verify, prove, refute, or taste-check any artifact.
- The task involves energy computation, deviation gating, or quality scoring.
- A goal loop is closing and needs proof obligations beyond lint/test.
- The harness is self-improving (Nocturne) or stamping new agents (Factory).
- Mike says "use L10" or references any L10 faculty.
- The task involves multi-model deliberation (Council), scenario exploration
  (What-If), or best-practice adherence (Adherence KPI).

---

## The 12 Faculties

### Certainty Engine (Cognition Stack IV) — "The Checker That Cannot Be Talked To"

| Faculty | Name | Purpose | Verification Level |
|---------|------|---------|-------------------|
| 9 | Proof Kernel (L0) | Machine-checked certificates via Lean kernel | L0 — kernel doesn't read chat |
| 10 | Refutation Search | Proof-by-contradiction engine | Cross-family, adversarial depth |
| 11 | Property-Based Testing | Invariant declaration + shrinking | Automated, counterexample-driven |
| 12 | SymPy MCP | Actual math, not token-prediction of math | Symbolically exact |

### Cognition Stack (Parts I-III)

| Faculty | Name | Purpose | Verification Level |
|---------|------|---------|-------------------|
| 1 | Taste Engine | 5-dim rubric + signature-replay | L5 — Mike mandatory for taste |
| 2 | Problem-Solving Council | Multi-model Architect/Worker/Evaluator/Verifier | L4 — cross-family, KS-stability |
| 3 | Tribal-Knowledge Scraper | Process exemplar pipeline | Deviation-gated, provenance-validated |
| 4 | Adherence KPI | Best-practice as hard gate | BLOCK on critical gate skip |
| 5 | Strategy Tool | Scenario Pack + BlendValue scorer | Scalable-oversight sealed |
| 6 | What-If Exploration | Branch generation + EFE selection | Cheap-checks-first cascade |
| 7 | Multi-Altitude | 10kft/1kft/100ft/ground | Must pass EACH altitude |
| 8 | Persona Thinking | Buyer/Skeptic/Operator/Future-Self/Domain-Master | Model-family diverse |

### Daemon + Factory

| Module | Name | Purpose |
|--------|------|---------|
| Nocturne | Nightly Daemon | N0-N8 self-improvement cycle (stages, never promotes) |
| Agent Factory | Stamp Procedure | F0-F5 deterministic agent stamp (BMS A4→A1) |

---

## The Two-Clause Law (Non-Negotiable)

1. **The kernel checks the proof — NEVER the LLM.** A small trusted kernel
   checks an untrusted search. Maker ≠ grader is upgraded to maker ≠ kernel.

2. **A human checks the theorem is the RIGHT theorem.** The kernel proves T;
   it cannot know T means "great." Theorem-authoring for taste/strategy →
   Mike (scalable oversight on the SPEC, not the proof).

---

## Non-Negotiable Invariants

These apply to ALL L10 operations. Violation = E=∞, BLOCK, escalate to Mike.

1. **Model frozen; only the harness evolves nightly.** (AHE)
2. **Every nightly edit is a file + a falsifiable prediction.** (AHE observability)
3. **No agent reviews its own output; no agent recalibrates against its own forecast.**
4. **Maker ≠ grader ≠ terminator.** The critic that scores output is a *different* agent.
5. **External/destructive/payment → Mike (A4) always**, no matter the BMS band.
6. **Anti-Goodhart: certification requires an out-of-loop signal the rig cannot write.**
   RL widens the reward-hacking gap under pressure.
7. **Concurrency governor: ≤16 concurrent / ≤1000 per run.**
8. **JTBD-gated: no agent stamped without live scrapeable exemplar surface.**
9. **Deviation ceiling: ±20σ output, ±30σ physics → auto-reject.**
10. **sorry / native_decide in Lean proofs → E=∞, auto-reject.**
11. **Anti-collusion: no two council seats share model family for generate AND grade.**
12. **The daemon self-declares NOTHING done — all staged for weekly Verifier.**

---

## Verification Ladder

| Level | Check | Foolable? |
|-------|-------|-----------|
| L0 (new) | Machine-checked certificate (Lean kernel / SymPy) | **No** — kernel doesn't read chat |
| L1 | Deterministic assertion / exit code / golden | No, but narrow |
| L2 | Rule / linter / schema / policy | No, but shallow |
| L3 | Delayed field truth (real outcome) | No, but slow |
| L4 | Model-as-judge (rubric) | **Yes** — different model, never maker |
| L5 | Human checkpoint (taste/strategy) | Supervision, not verification |

**Close-worthy iff:**
- L0 kernel certificate emitted (for formalizable claims), OR
- E_refute ≤ θ with adversarial-depth met (Refuter failed to break it), AND
- All declared invariants survive PBT (no shrunk counterexample), AND
- Every energy gate SymPy-verified exact, AND
- Theorem/spec authored or approved by Mike where checking = doing

---

## Energy Functions (SymPy Substrate)

All energy computations go through `rig-math-exec` on SymPy MCP substrate.
No estimation, no hallucination. MathProofPacket sealed with hash chain.

```python
from common import robust_madz, surprisal, blend_value, expected_free_energy
from common import composite_sigma, deviation_gate, ProofPacket
```

| Function | Formula | Purpose |
|----------|---------|---------|
| RobustMADZ | 0.6745 × (score - median) / MAD | Deviation gate |
| Surprisal | S(o) = -ln P(o) | Entropy/uncertainty |
| BlendValue | λ₁·Novelty + λ₂·Systematicity - λ₃·Inconsistency | Strategic ranking |
| Expected Free Energy | G(π) = E_surprise + D_KL(q‖p) | Action selection |
| Composite Sigma | σ = 0.3·d_struct + 0.7·d_behavior | Deviation score |

**Mandatory doctrine:** `/Users/rig128gb/Documents/JakeStudio/Doctrine/sympy-math-mcp-mandatory.md`

---

## BMS Autonomy Ladder

Agents are stamped at **A4 (every action → Mike)** and climb only on
Brier-validated real outcomes:

| Brier Score | BMS Band | Meaning |
|-------------|----------|---------|
| ≥ 0.75 | A1 | Autonomous |
| ≥ 0.45 | A2 | Supervised-autonomous |
| ≥ 0.25 | A3 | Assisted |
| < 0.25 | A4 | Manual (Mike required) |

**External/destructive/payment → A4 ALWAYS**, no matter the band.

---

## Nocturne Cadence

```
WEEKLY META CYCLE (Verifier + Mike: promote / reject)
  └─ NIGHTLY NOCTURNE ×7 (scrape + self-teach + stage; NEVER self-promote)
       └─ PER-JTBD grill-loop (IQRSQPI, E vs scraped exemplar, ≥3 Q/R)
```

Nightly = generate + evaluate. Weekly = verify + approve.
Autonomy is bought per night with attestation banked for the week.

---

## Agent Factory Stamp Procedure

**F0** — Outcome intake → JTBD spec + resolution criteria
**F1** — Gradeability probe → live exemplar surface exists (FAIL → abort)
**F2** — Harness synthesis → H=(E,T,C,S,L,V)
**F3** — Sign + seal → version, sign, register replay tests
**F4** — Daemon enroll → Nocturne cron, MEMORY_SCOPE
**F5** — Cold-start night 1 → read-only (scrape + grade, no mints)

---

## CLI Reference

```bash
rig-l10 test           # Module-level quick test (11 checks)
rig-l10-test           # Full 38-test suite (28 unit + 10 scenarios)
rig-l10-scenarios      # 10 end-to-end L10 scenarios
rig-l10 doctor         # 12-module health check + SymPy MCP
rig-l10 info           # Module info
```

## Python Import

```python
import sys; sys.path.insert(0, "/Users/rig128gb/rig-l10/src")
from common import ProofPacket, robust_madz, deviation_gate, anti_goodhart_check
from certainty_engine.pbt import PropertyBasedTester
from certainty_engine.refuter import RefuterAgent
from certainty_engine.lean_kernel import LeanKernel
from cognition_stack.taste_engine import TasteEngine
from cognition_stack.council import ProblemSolvingCouncil
from cognition_stack.tribal_scraper import TribalKnowledgeScraper
from cognition_stack.adherence import AdherenceGate
from cognition_stack.strategy import WhatIfExplorer, MultiAltitudeReviewer, PersonaThinking
from nocturne.daemon import NocturneDaemon
from agent_factory.factory import AgentFactory
```

---

## Confidence Ladder

| Level | Meaning |
|-------|---------|
| PERFECT | Every claim verified, zero gaps |
| VERIFIED | All checks passed, minor gaps |
| PARTIAL | No failures, but unverifiable gaps |
| FEEDBACK | Claim failed, correction sent |
| FAILED | Couldn't verify, escalate to human |

---

## First Build Reference

Pong game demo: `/Users/rig128gb/rig-l10/examples/pong/index.html`
Test suite: `/Users/rig128gb/rig-l10/tests/test_l10.py` (38/38 pass)
Proof packets: `/Users/rig128gb/rig-l10/proofpackets/`

---

## Sources

- Lin et al. "Agentic Harness Engineering" (AHE), CoRR abs/2604.25850, 2026
- IndyDevDan Tactical Agentic Coding (14 lessons)
- SymPy Math MCP Mandatory Doctrine (signed 2026-06-30)
