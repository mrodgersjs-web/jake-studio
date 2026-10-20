"""GL-L10-CH-05: Tool Registry — side-effect classification + policy gates.

Every tool an agent can call is registered with a side-effect class.
Calls to tools above READ_ONLY pass a gate: without a recorded approval
the registry refuses the call with PolicyViolation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SideEffectClass(str, Enum):
    """What a tool call can do to the outside world."""

    READ_ONLY = "read_only"
    REVERSIBLE_WRITE = "reversible_write"
    IRREVERSIBLE_WRITE = "irreversible_write"
    DESTRUCTIVE = "destructive"
    FINANCIAL = "financial"
    CREDENTIAL_BEARING = "credential_bearing"


#: Classes whose calls always need a recorded human approval.
APPROVAL_REQUIRED = {
    SideEffectClass.IRREVERSIBLE_WRITE,
    SideEffectClass.DESTRUCTIVE,
    SideEffectClass.FINANCIAL,
    SideEffectClass.CREDENTIAL_BEARING,
}


class PolicyViolation(Exception):
    """Raised when a tool call is blocked by the gate."""


@dataclass(frozen=True)
class ToolDefinition:
    """One registrable tool."""

    name: str
    description: str
    side_effect_class: SideEffectClass


@dataclass
class GateResult:
    """Outcome of a gate check."""

    allowed: bool
    tool_name: str
    detail: str = ""


class ToolRegistry:
    """Registry of callable tools plus the approval gate."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def requires_approval(self, name: str) -> bool:
        tool = self._get(name)
        return tool.side_effect_class in APPROVAL_REQUIRED

    def check_gate(self, name: str, run_packet: Any = None,
                   has_approval: bool = False) -> GateResult:
        """Check whether a call may proceed.

        Raises PolicyViolation when the tool needs approval and none is
        recorded. run_packet is accepted for audit hooks; the gate does
        not mutate it.
        """
        tool = self._get(name)
        if self.requires_approval(name) and not has_approval:
            raise PolicyViolation(
                f"tool {name!r} ({tool.side_effect_class.value}) requires approval"
            )
        return GateResult(allowed=True, tool_name=name, detail="gate passed")

    def _get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]
