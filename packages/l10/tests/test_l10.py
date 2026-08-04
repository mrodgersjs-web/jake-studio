"""RIG L10 Test Suite — comprehensive verification of all 13 goals."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest

class TestCommon(unittest.TestCase):
    """Test shared common module."""
    
    def test_robust_madz(self):
        from common import robust_madz
        r = robust_madz(7.5, [3.2, 4.1, 3.8, 4.5, 3.9, 4.0, 3.7, 4.3])
        self.assertEqual(r["verdict"], "PASS")
        self.assertIn("sigma", r)
    
    def test_surprisal(self):
        from common import surprisal
        r = surprisal(0.15)
        self.assertEqual(r["verdict"], "PASS")
        self.assertAlmostEqual(r["returned_value"], 1.8971, places=2)
    
    def test_blend_value(self):
        from common import blend_value
        r = blend_value(0.7, 0.8, 0.2)
        self.assertEqual(r["verdict"], "PASS")
        self.assertAlmostEqual(r["returned_value"], 0.66, places=2)
    
    def test_expected_free_energy(self):
        from common import expected_free_energy
        r = expected_free_energy(2.5, 0.3)
        self.assertEqual(r["verdict"], "PASS")
        self.assertAlmostEqual(r["returned_value"], 2.8, places=1)
    
    def test_composite_sigma(self):
        from common import composite_sigma
        r = composite_sigma(1.5, 2.3)
        self.assertEqual(r["verdict"], "PASS")
    
    def test_deviation_gate_accept(self):
        from common import deviation_gate
        r = deviation_gate(4.0, [3.5, 4.0, 3.8, 4.2])
        self.assertEqual(r, "accept")
    
    def test_deviation_gate_reject(self):
        from common import deviation_gate
        r = deviation_gate(50.0, [3.0, 4.0, 3.5, 4.5], reject_sigma=3.0)
        self.assertIn(r, ["reject", "auto_reject"])
    
    def test_anti_goodhart_check(self):
        from common import anti_goodhart_check
        self.assertTrue(anti_goodhart_check("external_kpi", False))
        self.assertFalse(anti_goodhart_check("self_written_metric", True))
    
    def test_proof_packet_seal(self):
        from common import ProofPacket
        p = ProofPacket(formula_id="test", verdict="PASS", returned_value=42)
        h = p.seal()
        self.assertTrue(h.startswith("sha256:"))
    
    def test_bms_enum(self):
        from common import BMS
        self.assertEqual(BMS.A4.value, "A4")
    
    def test_gev_roles(self):
        from common import GEVRole
        self.assertNotEqual(GEVRole.GENERATOR, GEVRole.EVALUATOR)


class TestPBT(unittest.TestCase):
    """GL-L10-CE-02: Property-Based Testing."""
    
    def test_conservation_property(self):
        from certainty_engine.pbt import PropertyBasedTester, Property, InvariantType
        pbt = PropertyBasedTester()
        pbt.declare(Property(
            name="conservation", invariant_type=InvariantType.CONSERVATION,
            description="sum equals sum", check_fn=lambda x: sum(x) == sum(sorted(x)),
            generator=lambda: [1, 2, 3], max_examples=10,
        ))
        r = pbt.verify_all()
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(r["total_failures"], 0)
    
    def test_failing_property_gets_shrunk(self):
        from certainty_engine.pbt import PropertyBasedTester, Property, InvariantType
        pbt = PropertyBasedTester()
        pbt.declare(Property(
            name="always_false", invariant_type=InvariantType.IDENTITY,
            description="always fails", check_fn=lambda x: False,
            generator=lambda: 42, max_examples=5,
        ))
        r = pbt.verify_all()
        self.assertEqual(r["verdict"], "FAIL")
        self.assertGreater(r["total_failures"], 0)
    
    def test_spec_hygiene_rejects_how(self):
        from certainty_engine.pbt import PropertyBasedTester, Property, InvariantType
        pbt = PropertyBasedTester()
        with self.assertRaises(ValueError):
            pbt.declare(Property(
                name="bad", invariant_type=InvariantType.IDENTITY,
                description="implement bubble sort", check_fn=lambda x: True,
                generator=lambda: 1,
            ))


class TestRefuter(unittest.TestCase):
    """GL-L10-CE-03: Refutation Search."""
    
    def test_refuter_cross_family(self):
        from certainty_engine.refuter import RefuterAgent, Claim
        ref = RefuterAgent(refuter_family="gpt")
        c = Claim(id="c1", statement="good", negation="bad", generator_family="claude", evidence_fn=lambda: 5.0)
        a = ref.refute(c, budget=50)
        self.assertIn(a.verdict.value, ["refuted", "not_refuted", "inconclusive"])
    
    def test_anti_collusion_blocks(self):
        from certainty_engine.refuter import RefuterAgent, Claim, RefutationVerdict
        ref = RefuterAgent(refuter_family="claude")  # Same family!
        c = Claim(id="c1", statement="good", negation="bad", generator_family="claude", evidence_fn=lambda: 5.0)
        a = ref.refute(c, budget=50)
        self.assertEqual(a.verdict, RefutationVerdict.ERROR)


class TestTasteEngine(unittest.TestCase):
    """GL-L10-CS1-01: Taste Engine."""
    
    def test_audit_scoring(self):
        from cognition_stack.taste_engine import TasteEngine, ShipBand
        t = TasteEngine()
        a = t.audit("t1", "content", {
            "intentionality": 4.5, "craft_quality": 4.0, "ai_slop": 4.5,
            "writing_voice": 4.0, "accessibility": 4.5,
        })
        self.assertGreaterEqual(a.composite_score, 4.0)
        self.assertIn(a.ship_band, [ShipBand.SHIP_WITH_PRIDE, ShipBand.SHIP_POLISH_LATER])
    
    def test_signature_replay_blocks(self):
        from cognition_stack.taste_engine import TasteEngine, ShipBand
        t = TasteEngine()
        a = t.audit("t1", "generic AI output", {
            "intentionality": 4.5, "craft_quality": 4.5, "ai_slop": 5.0,
            "writing_voice": 4.5, "accessibility": 4.5,
        }, signature_check={"off_signature": True, "reason": "sounds generic"})
        self.assertTrue(a.signature_replay_blocked)
    
    def test_mike_review(self):
        from cognition_stack.taste_engine import TasteEngine
        t = TasteEngine()
        a = t.audit("t1", "content", {
            "intentionality": 3.0, "craft_quality": 3.0, "ai_slop": 3.0,
            "writing_voice": 3.0, "accessibility": 3.0,
        })
        t.request_mike_review(a, override_score=4.2)
        self.assertTrue(a.mike_reviewed)
        self.assertEqual(a.composite_score, 4.2)


class TestAdherence(unittest.TestCase):
    """GL-L10-CS2-02: Adherence KPI."""
    
    def test_pass_when_all_followed(self):
        from cognition_stack.adherence import AdherenceGate
        adh = AdherenceGate()
        r = adh.check("p1", [
            {"step_id": "s1", "step_type": "action"},
            {"step_id": "s2", "step_type": "gate"},
        ], ["s1", "s2"], [])
        self.assertEqual(r.verdict, "PASS")
        self.assertFalse(r.critical_gate_skipped)
    
    def test_block_on_critical_skip(self):
        from cognition_stack.adherence import AdherenceGate
        adh = AdherenceGate()
        r = adh.check("p1", [
            {"step_id": "s1", "step_type": "action"},
            {"step_id": "g1", "step_type": "gate"},
        ], ["s1"], ["g1"])
        self.assertEqual(r.verdict, "BLOCK")
        self.assertTrue(r.critical_gate_skipped)


class TestNocturne(unittest.TestCase):
    """GL-L10-ND-01..02: Nocturne Daemon."""
    
    def test_read_only_run(self):
        from nocturne.daemon import NocturneDaemon
        n = NocturneDaemon()
        night = n.run_night("studio_1", ["jtbd_1"], read_only=True)
        self.assertTrue(night.is_read_only)
        self.assertGreaterEqual(len(night.phase_results), 4)
        self.assertEqual(len(night.errors), 0)
    
    def test_full_run(self):
        from nocturne.daemon import NocturneDaemon
        n = NocturneDaemon()
        night = n.run_night("studio_1", ["jtbd_1"], read_only=False)
        self.assertFalse(night.is_read_only)
        self.assertGreaterEqual(len(night.phase_results), 8)


class TestFactory(unittest.TestCase):
    """GL-L10-AF-01: Agent Factory."""
    
    def test_stamp_procedure(self):
        from agent_factory.factory import AgentFactory, BMS
        f = AgentFactory()
        agent = f.stamp("jtbd_1", {"resolution": "test"})
        self.assertTrue(agent.jtbd_gradeability)
        self.assertEqual(agent.bms_band, BMS.A4)
        self.assertTrue(agent.nocturne_enrolled)
        self.assertIsNotNone(agent.harness)
        self.assertTrue(agent.night_1_read_only)
    
    def test_gradeability_fail(self):
        from agent_factory.factory import AgentFactory
        f = AgentFactory()
        agent = f.stamp("jtbd_bad", {}, exemplar_surface_exists=False)
        self.assertFalse(agent.jtbd_gradeability)
        self.assertGreater(len(agent.errors), 0)
    
    def test_bms_ladder(self):
        from agent_factory.factory import AgentFactory, BMS
        f = AgentFactory()
        agent = f.stamp("jtbd_1", {})
        self.assertEqual(f.can_earn_autonomy(agent, 0.80), BMS.A1)
        self.assertEqual(f.can_earn_autonomy(agent, 0.50), BMS.A2)
        self.assertEqual(f.can_earn_autonomy(agent, 0.30), BMS.A3)
        self.assertEqual(f.can_earn_autonomy(agent, 0.10), BMS.A4)


class TestCouncil(unittest.TestCase):
    """GL-L10-CS1-02: Problem-Solving Council."""
    
    def test_council_convenes(self):
        from cognition_stack.council import ProblemSolvingCouncil, CouncilMember, CouncilRole
        council = ProblemSolvingCouncil()
        members = [
            CouncilMember(role=CouncilRole.ARCHITECT, model_family="claude", model_name="opus"),
            CouncilMember(role=CouncilRole.WORKER, model_family="gpt", model_name="gpt-4o"),
            CouncilMember(role=CouncilRole.EVALUATOR, model_family="gemini", model_name="gemini-pro"),
            CouncilMember(role=CouncilRole.VERIFIER, model_family="llama", model_name="llama-4"),
        ]
        session = council.convene("test claim", members)
        self.assertIsNotNone(session.final_verdict)
        self.assertTrue(session.anti_collusion_holds)
        self.assertGreater(session.diversity_score, 0)
    
    def test_anti_collusion_violation(self):
        from cognition_stack.council import ProblemSolvingCouncil, CouncilMember, CouncilRole, CouncilVerdict
        council = ProblemSolvingCouncil()
        members = [
            CouncilMember(role=CouncilRole.ARCHITECT, model_family="claude", model_name="opus"),
            CouncilMember(role=CouncilRole.VERIFIER, model_family="claude", model_name="sonnet"),  # SAME!
        ]
        session = council.convene("test", members)
        self.assertFalse(session.anti_collusion_holds)
        self.assertEqual(session.final_verdict, CouncilVerdict.BLOCK)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestL10Scenarios(unittest.TestCase):
    """10 end-to-end scenarios testing every L10 faculty."""
    
    def test_s01_sympy_energy(self):
        from common import robust_madz, surprisal, blend_value, expected_free_energy, composite_sigma
        self.assertEqual(robust_madz(7.5, [3.2,4.1,3.8,4.5,3.9,4.0,3.7,4.3])["verdict"], "PASS")
        self.assertEqual(surprisal(0.15)["verdict"], "PASS")
        self.assertEqual(blend_value(0.7, 0.8, 0.2)["verdict"], "PASS")
        self.assertEqual(expected_free_energy(2.5, 0.3)["verdict"], "PASS")
        self.assertEqual(composite_sigma(1.5, 2.3)["verdict"], "PASS")
    
    def test_s02_deviation_gate(self):
        from common import deviation_gate
        self.assertEqual(deviation_gate(4.0, [3.5, 4.0, 3.8, 4.2]), "accept")
        self.assertIn(deviation_gate(50.0, [3.0, 4.0, 3.5, 4.5], reject_sigma=3.0), ("reject", "auto_reject"))
        self.assertEqual(deviation_gate(1000.0, [3.0, 4.0, 3.5, 4.5], auto_reject_sigma=5.0), "auto_reject")
    
    def test_s03_pbt_multi_invariant(self):
        import json as j
        from certainty_engine.pbt import PropertyBasedTester, Property, InvariantType
        pbt = PropertyBasedTester()
        pbt.declare(Property(name="c", invariant_type=InvariantType.CONSERVATION,
            description="sum equals sum", check_fn=lambda x: sum(x) == sum(sorted(x)),
            generator=lambda: [1,2,3], max_examples=50))
        pbt.declare(Property(name="i", invariant_type=InvariantType.IDEMPOTENCE,
            description="sort is idempotent", check_fn=lambda x: sorted(sorted(x)) == sorted(x),
            generator=lambda: [3,1,2], max_examples=50))
        pbt.declare(Property(name="r", invariant_type=InvariantType.ROUND_TRIP,
            description="json roundtrip", check_fn=lambda x: j.loads(j.dumps(x)) == x,
            generator=lambda: {"a": 1}, max_examples=50))
        r = pbt.verify_all()
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(r["properties_tested"], 3)
    
    def test_s04_refuter_anticollusion(self):
        from certainty_engine.refuter import RefuterAgent, Claim, RefutationVerdict
        ref = RefuterAgent(refuter_family="gpt")
        c = Claim(id="c", statement="good", negation="bad", generator_family="claude", evidence_fn=lambda: 5.0)
        a = ref.refute(c, budget=50)
        self.assertIn(a.verdict.value, ("refuted", "not_refuted", "inconclusive"))
        ref_bad = RefuterAgent(refuter_family="claude")
        c2 = Claim(id="c2", statement="g", negation="b", generator_family="claude", evidence_fn=lambda: 1.0)
        self.assertEqual(ref_bad.refute(c2, budget=10).verdict, RefutationVerdict.ERROR)
    
    def test_s05_taste_signature_replay(self):
        from cognition_stack.taste_engine import TasteEngine, ShipBand
        t = TasteEngine()
        a1 = t.audit("good", "precise", {"intentionality":4.8,"craft_quality":4.5,"ai_slop":5.0,"writing_voice":4.5,"accessibility":4.5})
        a2 = t.audit("bad", "generic", {"intentionality":4.5,"craft_quality":4.5,"ai_slop":2.0,"writing_voice":2.0,"accessibility":4.5},
            signature_check={"off_signature": True, "reason": "generic"})
        self.assertGreater(a1.composite_score, a2.composite_score)
        self.assertTrue(a2.signature_replay_blocked)
    
    def test_s06_council_diversity(self):
        from cognition_stack.council import ProblemSolvingCouncil, CouncilMember, CouncilRole, CouncilVerdict
        council = ProblemSolvingCouncil()
        good = [CouncilMember(r, f, m) for r, f, m in [
            (CouncilRole.ARCHITECT, "claude", "opus"), (CouncilRole.WORKER, "gpt", "gpt-4o"),
            (CouncilRole.EVALUATOR, "gemini", "gemini-pro"), (CouncilRole.VERIFIER, "llama", "llama-4")]]
        s = council.convene("test", good)
        self.assertTrue(s.anti_collusion_holds)
        bad = [CouncilMember(CouncilRole.ARCHITECT, "claude", "opus"), CouncilMember(CouncilRole.VERIFIER, "claude", "sonnet")]
        self.assertFalse(council.convene("t", bad).anti_collusion_holds)
    
    def test_s07_tribal_adherence(self):
        from cognition_stack.tribal_scraper import TribalKnowledgeScraper
        from cognition_stack.adherence import AdherenceGate
        scraper = TribalKnowledgeScraper()
        claims = scraper.extract_claims([
            {"claim": "validate input", "source": "blog", "quality": 0.9, "recency_days": 30, "evidence": "e"},
        ])
        jm = scraper.synthesize_job_map("p1", claims)
        adh = AdherenceGate()
        r = adh.check("p1", [{"step_id": s.step_id, "step_type": s.step_type} for s in jm.steps],
            [s.step_id for s in jm.steps], [])
        self.assertEqual(r.verdict, "PASS")
    
    def test_s08_strategy_altitude_persona(self):
        from cognition_stack.strategy import WhatIfExplorer, MultiAltitudeReviewer, PersonaThinking
        e = WhatIfExplorer()
        self.assertEqual(len(e.generate_branches(["a", "b", "c"])), 3)
        a = MultiAltitudeReviewer()
        a.review("t", strategy_check="ok", architecture_check="ok", execution_check="ok", failure_modes="No critical failure modes")
        self.assertTrue(a.all_passed())
        p = PersonaThinking()
        self.assertEqual(len(p.run_all("t")), 5)
    
    def test_s09_nocturne_full_cycle(self):
        from nocturne.daemon import NocturneDaemon
        n = NocturneDaemon()
        ro = n.run_night("s1", ["j1"], read_only=True)
        self.assertTrue(ro.is_read_only)
        full = n.run_night("s1", ["j1"], read_only=False)
        self.assertFalse(full.is_read_only)
        self.assertGreater(len(full.proof_packets), 0)
        self.assertEqual(full.proof_packets[0].verdict, "STAGED")
    
    def test_s10_factory_self_upgrade(self):
        from agent_factory.factory import AgentFactory, BMS
        from common import ProofPacket
        f = AgentFactory()
        agent = f.stamp("j1", {"r": "test"})
        self.assertEqual(f.can_earn_autonomy(agent, 0.80), BMS.A1)
        self.assertEqual(f.can_earn_autonomy(agent, 0.10), BMS.A4)
        p = ProofPacket(formula_id="test", verdict="PASS", returned_value=True)
        self.assertTrue(p.seal().startswith("sha256:"))
