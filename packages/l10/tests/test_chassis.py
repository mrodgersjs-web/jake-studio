"""TDD tests for the Jake Agent Production Chassis — Phase 1.

Tests written FIRST. Implementation follows.
Run: python3 -m pytest tests/test_chassis.py -v
Or:  cd /Users/rig128gb/rig-l10 && python3 tests/test_chassis.py
"""
import sys
import os
import json
import hashlib
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest


class TestHarnessRegistry(unittest.TestCase):
    """GL-L10-CH-01: Harness Registry — sealed, versioned H=(E,T,C,S,L,V)."""

    def test_register_valid_harness(self):
        """Harness with all 6 components gets registered with signature."""
        from chassis.harness import HarnessRegistry, Harness, HarnessTuple
        from chassis.harness import Environment, ToolAllowlist, ContextSpec, StateSpec, LoopSpec, VerificationSpec

        registry = HarnessRegistry()
        harness = Harness(
            name="test-harness",
            version="1.0.0",
            E=Environment(role="generator", objective="test", non_goals=["prod"], boundaries=[]),
            T=ToolAllowlist(tools=["web_search", "read_file"], budgets={"tokens": 1000}),
            C=ContextSpec(inputs=["icp", "target"], freshness_hours=24),
            S=StateSpec(checkpoint_after="every_transition", durable=True),
            L=LoopSpec(stages=["plan", "execute", "verify"], max_revisions=3),
            V=VerificationSpec(proof_obligations=["schema_valid", "source_per_claim"]),
        )
        result = registry.register(harness)
        self.assertEqual(result["status"], "registered")
        self.assertTrue(result["signature"].startswith("sha256:"))
        self.assertEqual(result["harness_name"], "test-harness")
        self.assertEqual(result["version"], "1.0.0")

    def test_reject_incomplete_harness(self):
        """Harness missing a component raises ValidationError."""
        from chassis.harness import Harness, HarnessTuple
        from chassis.harness import Environment, ToolAllowlist, ContextSpec, StateSpec, LoopSpec

        with self.assertRaises(Exception):
            Harness(
                name="bad",
                version="1.0.0",
                E=Environment(role="generator", objective="test", non_goals=[], boundaries=[]),
                T=ToolAllowlist(tools=[], budgets={}),
                C=ContextSpec(inputs=[], freshness_hours=24),
                S=StateSpec(checkpoint_after="transitions", durable=True),
                L=LoopSpec(stages=[], max_revisions=3),
                # V is missing — should fail
            )

    def test_reject_duplicate_version(self):
        """Registering same harness+version again raises ValueError."""
        from chassis.harness import HarnessRegistry, Harness
        from chassis.harness import Environment, ToolAllowlist, ContextSpec, StateSpec, LoopSpec, VerificationSpec

        registry = HarnessRegistry()
        harness = Harness(
            name="dup-test",
            version="1.0.0",
            E=Environment(role="generator", objective="test", non_goals=[], boundaries=[]),
            T=ToolAllowlist(tools=[], budgets={}),
            C=ContextSpec(inputs=[], freshness_hours=24),
            S=StateSpec(checkpoint_after="transitions", durable=True),
            L=LoopSpec(stages=[], max_revisions=3),
            V=VerificationSpec(proof_obligations=[]),
        )
        registry.register(harness)
        with self.assertRaises(ValueError):
            registry.register(harness)

    def test_harness_signature_is_deterministic(self):
        """Same harness content produces same signature."""
        from chassis.harness import Harness, HarnessTuple
        from chassis.harness import Environment, ToolAllowlist, ContextSpec, StateSpec, LoopSpec, VerificationSpec

        env = Environment(role="generator", objective="test", non_goals=[], boundaries=[])
        tools = ToolAllowlist(tools=[], budgets={})
        ctx = ContextSpec(inputs=[], freshness_hours=24)
        state = StateSpec(checkpoint_after="transitions", durable=True)
        loop = LoopSpec(stages=[], max_revisions=3)
        ver = VerificationSpec(proof_obligations=[])

        h = Harness(name="sig-test", version="1.0.0", E=env, T=tools, C=ctx, S=state, L=loop, V=ver)
        sig1 = h.sign()
        sig2 = h.sign()
        self.assertEqual(sig1, sig2)


class TestRunPacket(unittest.TestCase):
    """GL-L10-CH-02: Typed Run Packet — hash-chained, no hidden retries."""

    def test_create_valid_packet(self):
        """RunPacket has all required fields."""
        from chassis.packet import RunPacket
        from chassis.harness import Environment

        packet = RunPacket(
            harness_name="test-harness",
            harness_version="1.0.0",
            goal="Test the run packet schema",
            gev_role="generator",
        )
        self.assertTrue(packet.run_id)
        self.assertEqual(packet.harness_name, "test-harness")
        self.assertEqual(packet.harness_version, "1.0.0")
        self.assertEqual(packet.goal, "Test the run packet schema")

    def test_packet_seal_produces_hash_chain(self):
        """Sealing produces a hash that includes previous_packet_hash."""
        from chassis.packet import RunPacket

        prev_hash = "sha256:abc123def456"
        packet = RunPacket(
            harness_name="h", harness_version="1.0.0", goal="g", gev_role="generator",
            previous_packet_hash=prev_hash,
        )
        sealed = packet.seal()
        self.assertEqual(sealed["previous_packet_hash"], prev_hash)
        self.assertTrue(sealed["packet_hash"].startswith("sha256:"))

    def test_no_hidden_retries(self):
        """Quality gate errors are visible in packet."""
        from chassis.packet import RunPacket

        packet = RunPacket(
            harness_name="h", harness_version="1.0.0", goal="g", gev_role="generator",
        )
        packet.record_retry("tool_timeout", reason="network blip")
        packet.record_retry("tool_timeout", reason="second attempt")
        self.assertEqual(packet.retry_count, 2)
        self.assertEqual(len(packet.retries_log), 2)

    def test_full_packet_seals_with_all_evidence(self):
        """A complete packet with all fields produces a stable seal."""
        from chassis.packet import RunPacket

        packet = RunPacket(
            harness_name="full-test",
            harness_version="2.1.0",
            goal="Full integration test",
            gev_role="generator",
            outcome="success",
        )
        packet.add_input_reference("icp", "schema://icp-v3", freshness_hours=12)
        packet.add_artifact("result.json", "sha256:deadbeef", size_bytes=2048)
        packet.add_tool_call("web_search", "read_only", "search query", "completed")
        packet.record_state_transition("INTAKE", "PLAN", "planner-001")
        packet.set_verifier_decision("PASS", "verifier-001", {"all_checks": True})

        sealed = packet.seal()
        self.assertEqual(sealed["outcome"], "success")
        self.assertTrue(sealed["retry_count"] == 0)
        self.assertEqual(len(sealed["artifacts"]), 1)
        self.assertEqual(len(sealed["state_transitions"]), 1)


class TestWorkflowFSM(unittest.TestCase):
    """GL-L10-CH-03: Workflow State Machine — typed transitions + failure states."""

    def test_happy_path(self):
        """Full state progression: INTAKE → ... → CLOSED."""
        from chassis.fsm import WorkflowFSM, RunState

        fsm = WorkflowFSM()
        for target in [
            RunState.VALIDATE_INPUTS,
            RunState.PLAN,
            RunState.AUTHORIZE_TOOLS,
            RunState.EXECUTE,
            RunState.EVALUATE,
            RunState.VERIFY,
            RunState.COMMIT,
            RunState.CLOSED,
        ]:
            fsm.transition_to(target, actor="test")

        self.assertEqual(fsm.current_state, RunState.CLOSED)

    def test_reject_invalid_transition(self):
        """INTAKE → EXECUTE is not allowed."""
        from chassis.fsm import WorkflowFSM, RunState, StateTransitionError

        fsm = WorkflowFSM()
        with self.assertRaises(StateTransitionError):
            fsm.transition_to(RunState.EXECUTE, actor="test")

    def test_failure_state_is_terminal(self):
        """POLICY_DENIED has no forward transitions."""
        from chassis.fsm import WorkflowFSM, RunState

        fsm = WorkflowFSM()
        fsm.transition_to(RunState.VALIDATE_INPUTS, actor="test")
        fsm.transition_to(RunState.PLAN, actor="test")
        fsm.transition_to(RunState.AUTHORIZE_TOOLS, actor="test")
        fsm.transition_to(RunState.POLICY_DENIED, actor="test", reason="budget exceeded")

        self.assertEqual(fsm.current_state, RunState.POLICY_DENIED)
        # No further transitions allowed
        with self.assertRaises(StateTransitionError):
            fsm.transition_to(RunState.EXECUTE, actor="test")

    def test_all_failure_states_terminal(self):
        """All failure states are terminal."""
        from chassis.fsm import WorkflowFSM, RunState, StateTransitionError

        failure_states = [
            RunState.BLOCKED_INPUT,
            RunState.POLICY_DENIED,
            RunState.TOOL_FAILURE,
            RunState.BUGET_EXCEEDED,
            RunState.EVALUATION_FAILED,
            RunState.VERIFICATION_FAILED,
            RunState.HUMAN_REJECTED,
            RunState.ROLLBACK_REQUIRED,
            RunState.QUARANTINED,
        ]
        for state in failure_states:
            fsm = WorkflowFSM()
            fsm.transition_to(state, actor="test", reason="test failure")
            self.assertEqual(fsm.current_state, state)
            with self.assertRaises(StateTransitionError):
                fsm.transition_to(RunState.CLOSED, actor="test")


class TestStateStore(unittest.TestCase):
    """GL-L10-CH-04: State Store — durable, checkpoint, resume."""

    def test_state_survives_restart(self):
        """State persists to disk and loads back."""
        from chassis.store import StateStore
        from chassis.fsm import RunState

        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(db_path=os.path.join(tmpdir, "test.db"))
            run_id = str(uuid.uuid4())
            store.create_run(run_id, harness_name="test", harness_version="1.0.0")
            store.set_state(run_id, RunState.EXECUTE, actor="generator")
            store.checkpoint(run_id)

            # Simulate restart
            store2 = StateStore(db_path=os.path.join(tmpdir, "test.db"))
            state = store2.get_state(run_id)
            self.assertEqual(state, RunState.EXECUTE)

    def test_idempotency_key_prevents_duplicate(self):
        """Committed idempotency keys are not retried."""
        from chassis.store import StateStore
        from chassis.fsm import RunState

        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(db_path=os.path.join(tmpdir, "test.db"))
            run_id = str(uuid.uuid4())
            store.create_run(run_id, harness_name="test", harness_version="1.0.0")
            store.set_state(run_id, RunState.EXECUTE, actor="generator")

            # Commit an idempotency key
            store.commit_idempotency_key(run_id, "write:user:123")

            # Check it's committed
            self.assertTrue(store.is_idempotency_committed(run_id, "write:user:123"))

    def test_budget_tracking(self):
        """Budget consumed and remaining are tracked."""
        from chassis.store import StateStore
        from chassis.fsm import RunState

        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(db_path=os.path.join(tmpdir, "test.db"))
            run_id = str(uuid.uuid4())
            store.create_run(run_id, harness_name="test", harness_version="1.0.0",
                           budget_tokens=1000)
            store.consume_budget(run_id, tokens=300, cost_usd=0.05)
            state = store.get_run_state(run_id)
            self.assertEqual(state["budget_consumed_tokens"], 300)
            self.assertEqual(state["budget_consumed_usd"], 0.05)
            self.assertEqual(state["budget_remaining_tokens"], 700)


class TestToolRegistry(unittest.TestCase):
    """GL-L10-CH-05: Tool Registry — side-effect classification + policy gates."""

    def test_register_read_only_tool(self):
        """Read-only tools don't require approval."""
        from chassis.tools import ToolRegistry, ToolDefinition, SideEffectClass

        registry = ToolRegistry()
        tool = ToolDefinition(
            name="list_users",
            description="List users",
            side_effect_class=SideEffectClass.READ_ONLY,
        )
        registry.register(tool)
        self.assertTrue(registry.has_tool("list_users"))
        self.assertFalse(registry.requires_approval("list_users"))

    def test_register_financial_tool_requires_approval(self):
        """Financial tools always require approval."""
        from chassis.tools import ToolRegistry, ToolDefinition, SideEffectClass

        registry = ToolRegistry()
        tool = ToolDefinition(
            name="charge_card",
            description="Charge a card",
            side_effect_class=SideEffectClass.FINANCIAL,
        )
        registry.register(tool)
        self.assertTrue(registry.requires_approval("charge_card"))

    def test_gate_blocked_without_approval(self):
        """Financial tool call without approval token is blocked."""
        from chassis.tools import ToolRegistry, ToolDefinition, SideEffectClass, PolicyViolation

        registry = ToolRegistry()
        tool = ToolDefinition(
            name="charge_card",
            description="Charge a card",
            side_effect_class=SideEffectClass.FINANCIAL,
        )
        registry.register(tool)

        with self.assertRaises(PolicyViolation):
            registry.check_gate("charge_card", run_packet=None, has_approval=False)

    def test_gate_allowed_with_approval(self):
        """Financial tool call with approval token is allowed."""
        from chassis.tools import ToolRegistry, ToolDefinition, SideEffectClass

        registry = ToolRegistry()
        tool = ToolDefinition(
            name="charge_card",
            description="Charge a card",
            side_effect_class=SideEffectClass.FINANCIAL,
        )
        registry.register(tool)

        result = registry.check_gate("charge_card", run_packet=None, has_approval=True)
        self.assertTrue(result.allowed)

    def test_all_side_effect_classes(self):
        """All 6 side-effect classes are represented."""
        from chassis.tools import SideEffectClass

        expected = {
            "READ_ONLY",
            "REVERSIBLE_WRITE",
            "IRREVERSIBLE_WRITE",
            "DESTRUCTIVE",
            "FINANCIAL",
            "CREDENTIAL_BEARING",
        }
        actual = {e.name for e in SideEffectClass}
        self.assertEqual(actual, expected)


class TestGEVSeparation(unittest.TestCase):
    """GL-L10-CH-06: GEV Separation — no agent reviews its own output."""

    def test_generator_cannot_verify_own_packet(self):
        """Generator cannot call verify on its own packet."""
        from chassis.gev import GEVRunner, RunPacket

        packet = RunPacket(
            harness_name="test", harness_version="1.0.0",
            goal="test", gev_role="generator",
        )
        # Generator session cannot verify
        with self.assertRaises(PermissionError):
            GEVRunner.verify(packet, role="generator")

    def test_verifier_can_close(self):
        """Verifier can verify a packet."""
        from chassis.gev import GEVRunner, RunPacket

        packet = RunPacket(
            harness_name="test", harness_version="1.0.0",
            goal="test", gev_role="generator",
        )
        packet.add_artifact("result.txt", "sha256:deadbeef", 100)
        packet.record_state_transition("INTAKE", "PLAN", "generator")
        packet.set_verifier_decision("PASS", "verifier", {})

        # Verifier (separate instance) can verify
        result = GEVRunner.verify(packet, role="verifier")
        self.assertEqual(result, "PASS")

    def test_evaluator_is_distinct_from_generator(self):
        """Evaluator role is separate from generator."""
        from chassis.gev import GEVRunner, RunPacket

        packet = RunPacket(
            harness_name="test", harness_version="1.0.0",
            goal="test", gev_role="generator",
        )
        # Evaluator can critique, but cannot mark verifier decision
        findings = GEVRunner.evaluate(packet, role="evaluator",
                                      defects=[{"type": "missing_source", "severity": "medium"}])
        self.assertEqual(len(findings), 1)
        self.assertIsNone(packet.verifier_decision)


class TestPolicyEngine(unittest.TestCase):
    """GL-L10-CH-07: Policy Engine — policy-before-action gates."""

    def test_policy_gate_chain(self):
        """All 8 policy checks are enforced."""
        from chassis.policy import PolicyEngine, PolicyContext

        engine = PolicyEngine()
        ctx = PolicyContext(
            tool_name="charge_card",
            role="generator",
            data_scope="public",
            side_effect_class="financial",
            budget_consumed={
                "tokens": 500, "budget_limit": 1000,
                "cost_usd": 0.01, "budget_cost": 0.10,
            },
            has_approval=True,
            secret_access=False,
            rate_check=True,
            evidence_sufficient=True,
        )

        # Should pass all gates
        result = engine.check_all_gates(ctx)
        self.assertTrue(result.passed)

    def test_policy_blocked_on_secret_access(self):
        """Non-credential-bearing tool cannot access secrets."""
        from chassis.policy import PolicyEngine, PolicyContext

        engine = PolicyEngine()
        ctx = PolicyContext(
            tool_name="web_search",
            role="generator",
            data_scope="public",
            side_effect_class="read_only",
            budget_consumed={
                "tokens": 100, "budget_limit": 1000,
                "cost_usd": 0.001, "budget_cost": 0.10,
            },
            has_approval=False,
            secret_access=True,  # Not allowed for read-only tool
            rate_check=True,
            evidence_sufficient=True,
        )

        result = engine.check_all_gates(ctx)
        self.assertFalse(result.passed)
        self.assertIn("secret_access", result.failed_gates)

    def test_policy_blocked_on_budget(self):
        """Budget exceeded blocks execution."""
        from chassis.policy import PolicyEngine, PolicyContext

        engine = PolicyEngine()
        ctx = PolicyContext(
            tool_name="web_search",
            role="generator",
            data_scope="public",
            side_effect_class="read_only",
            budget_consumed={
                "tokens": 1500, "budget_limit": 1000,  # Over budget
                "cost_usd": 0.001, "budget_cost": 0.10,
            },
            has_approval=False,
            secret_access=False,
            rate_check=True,
            evidence_sufficient=True,
        )

        result = engine.check_all_gates(ctx)
        self.assertFalse(result.passed)
        self.assertIn("budget_check", result.failed_gates)


class TestIntegration(unittest.TestCase):
    """Integration tests: harness + packet + fsm + store + policy."""

    def test_full_run_simulation(self):
        """Simulate a complete run through all components."""
        from chassis.harness import HarnessRegistry, Harness
        from chassis.harness import Environment, ToolAllowlist, ContextSpec, StateSpec, LoopSpec, VerificationSpec
        from chassis.packet import RunPacket
        from chassis.fsm import WorkflowFSM, RunState
        from chassis.store import StateStore
        from chassis.tools import ToolRegistry, ToolDefinition, SideEffectClass
        from chassis.policy import PolicyEngine, PolicyContext
        from chassis.gev import GEVRunner

        # 1. Register harness
        registry = HarnessRegistry()
        harness = Harness(
            name="integration-test",
            version="1.0.0",
            E=Environment(role="generator", objective="test", non_goals=[], boundaries=[]),
            T=ToolAllowlist(tools=["read_file"], budgets={"tokens": 5000}),
            C=ContextSpec(inputs=[], freshness_hours=24),
            S=StateSpec(checkpoint_after="every_transition", durable=True),
            L=LoopSpec(stages=["plan", "execute", "verify"], max_revisions=3),
            V=VerificationSpec(proof_obligations=["schema_valid"]),
        )
        registry.register(harness)

        # 2. Create run packet
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(db_path=os.path.join(tmpdir, "integration.db"))
            run_id = str(uuid.uuid4())
            store.create_run(run_id, harness_name="integration-test", harness_version="1.0.0")

            packet = RunPacket(
                harness_name="integration-test",
                harness_version="1.0.0",
                goal="Integration test",
                gev_role="generator",
            )

            # 3. FSM transitions
            fsm = WorkflowFSM()
            fsm.transition_to(RunState.VALIDATE_INPUTS, actor="generator")
            store.set_state(run_id, RunState.VALIDATE_INPUTS, actor="generator")
            store.checkpoint(run_id)

            packet.record_state_transition("INTAKE", "VALIDATE_INPUTS", "generator")

            # 4. Policy gate for read-only tool
            registry_tools = ToolRegistry()
            tool = ToolDefinition(
                name="read_file",
                description="Read a file",
                side_effect_class=SideEffectClass.READ_ONLY,
            )
            registry_tools.register(tool)

            ctx = PolicyContext(
                tool_name="read_file",
                role="generator",
                data_scope="public",
                side_effect_class="read_only",
                budget_consumed={
                    "tokens": 100, "budget_limit": 5000,
                    "cost_usd": 0.001, "budget_cost": 1.00,
                },
                has_approval=False,
                secret_access=False,
                rate_check=True,
                evidence_sufficient=True,
            )
            result = PolicyEngine().check_all_gates(ctx)
            self.assertTrue(result.passed)

            # 5. Postconditions
            packet.add_artifact("result.txt", "sha256:deadbeef", 100)
            packet.record_state_transition("VALIDATE_INPUTS", "PLAN", "generator")

            fsm.transition_to(RunState.PLAN, actor="generator")
            store.set_state(run_id, RunState.PLAN, actor="generator")
            store.checkpoint(run_id)

            # 6. Verifier closes
            packet.set_verifier_decision("PASS", "verifier", {"all_gates": True})
            sealed = packet.seal()

            self.assertEqual(sealed["verifier_decision"]["verdict"], "PASS")
            self.assertEqual(len(sealed["artifacts"]), 1)
            self.assertEqual(len(sealed["state_transitions"]), 2)

            # 7. Verify state survived restart
            store2 = StateStore(db_path=os.path.join(tmpdir, "integration.db"))
            self.assertEqual(store2.get_state(run_id), RunState.PLAN)


if __name__ == "__main__":
    unittest.main()
