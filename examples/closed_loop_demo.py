"""A closed Builder/Verifier loop in one script.

Run directly:  python examples/closed_loop_demo.py
Runs offline:  uses the chassis runtime with a temp state store.

The demo shows the law this repo enforces: the role that generated a
packet can never verify it.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "l10" / "src"))

from chassis.fsm import RunState, WorkflowFSM  # noqa: E402
from chassis.gev import GEVRunner  # noqa: E402
from chassis.packet import RunPacket  # noqa: E402
from chassis.policy import PolicyContext, PolicyEngine  # noqa: E402
from chassis.store import StateStore  # noqa: E402
from chassis.tools import SideEffectClass, ToolDefinition, ToolRegistry  # noqa: E402


def run_demo() -> dict:
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="read_file",
        description="Read a file",
        side_effect_class=SideEffectClass.READ_ONLY,
    ))

    policy = PolicyEngine()
    verdict = policy.check_all_gates(PolicyContext(
        tool_name="read_file",
        role="generator",
        data_scope="public",
        side_effect_class="read_only",
        budget_consumed={"tokens": 10, "budget_limit": 1000,
                         "cost_usd": 0.0, "budget_cost": 1.0},
    ))

    packet = RunPacket(
        harness_name="demo", harness_version="1.0.0",
        goal="demonstrate the closed loop", gev_role="generator",
    )
    fsm = WorkflowFSM()
    fsm.transition_to(RunState.VALIDATE_INPUTS, actor="generator")
    packet.record_state_transition("INTAKE", "VALIDATE_INPUTS", "generator")
    packet.add_artifact("demo-output.txt", "sha256:demo", 12)

    with tempfile.TemporaryDirectory() as tmp:
        store = StateStore(db_path=str(Path(tmp) / "demo.db"))
        store.create_run(packet.run_id, harness_name="demo",
                         harness_version="1.0.0", budget_tokens=1000)
        store.consume_budget(packet.run_id, tokens=10, cost_usd=0.0)
        remaining = store.get_run_state(packet.run_id)["budget_remaining_tokens"]

    # The generator can never close its own packet.
    try:
        GEVRunner.verify(packet, role="generator")
        self_review_blocked = False
    except PermissionError:
        self_review_blocked = True

    packet.set_verifier_decision("PASS", "verifier", {"policy": verdict.passed})
    sealed = packet.seal()

    return {
        "policy_passed": verdict.passed,
        "failed_gates": verdict.failed_gates,
        "budget_remaining_tokens": remaining,
        "self_review_blocked": self_review_blocked,
        "verdict": sealed["verifier_decision"]["verdict"],
        "artifacts": len(sealed["artifacts"]),
    }


def main() -> int:
    result = run_demo()
    print(json.dumps(result, indent=2, sort_keys=True))
    ok = (result["policy_passed"] and result["self_review_blocked"]
          and result["verdict"] == "PASS" and result["budget_remaining_tokens"] == 990)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
