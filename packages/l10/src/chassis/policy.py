"""GL-L10-CH-07: Policy Engine — policy-before-action gates.

Eight gates run before any tool call: tool registration, role scope,
data scope, approval, secret access, budget, rate, and evidence.
A call proceeds only when every gate passes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Side-effect classes whose calls require a recorded approval.
APPROVAL_CLASSES = {"financial", "irreversible_write", "destructive",
                    "credential_bearing"}

#: Classes allowed to touch secrets.
SECRET_CLASSES = {"credential_bearing"}


@dataclass
class PolicyContext:
    """Everything a gate needs to judge one pending tool call."""

    tool_name: str
    role: str
    data_scope: str
    side_effect_class: str
    budget_consumed: dict[str, float]
    has_approval: bool = False
    secret_access: bool = False
    rate_check: bool = True
    evidence_sufficient: bool = True


@dataclass
class GateReport:
    """Outcome of the full gate chain."""

    passed: bool
    failed_gates: list[str] = field(default_factory=list)


class PolicyEngine:
    """Runs the eight-gate chain against a PolicyContext."""

    def check_all_gates(self, ctx: PolicyContext) -> GateReport:
        failed: list[str] = []

        if not ctx.tool_name:
            failed.append("tool_gate")
        if not ctx.role:
            failed.append("role_gate")
        if not ctx.data_scope:
            failed.append("data_scope")
        if ctx.side_effect_class in APPROVAL_CLASSES and not ctx.has_approval:
            failed.append("approval_check")
        if ctx.secret_access and ctx.side_effect_class not in SECRET_CLASSES:
            failed.append("secret_access")

        budget = ctx.budget_consumed or {}
        over_tokens = budget.get("tokens", 0) > budget.get("budget_limit", 0)
        over_cost = budget.get("cost_usd", 0) > budget.get("budget_cost", 0)
        if over_tokens or over_cost:
            failed.append("budget_check")

        if not ctx.rate_check:
            failed.append("rate_check")
        if not ctx.evidence_sufficient:
            failed.append("evidence_check")

        return GateReport(passed=not failed, failed_gates=failed)
