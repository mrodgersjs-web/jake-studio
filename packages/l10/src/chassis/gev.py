"""GL-L10-CH-06: GEV Separation — no role reviews its own output.

Generator, Evaluator and Verifier are distinct roles. A role may never
verify the packet it generated; evaluation records findings without
touching the verifier decision.
"""
from __future__ import annotations

import uuid
from typing import Any

from .packet import DefectFinding, RunPacket

__all__ = ["GEVRunner", "RunPacket"]


class GEVRunner:
    """Role-checked entry points for evaluation and verification."""

    @staticmethod
    def verify(packet: RunPacket, role: str) -> str:
        """Return the packet's verifier verdict.

        Raises PermissionError when the caller's role generated the
        packet: an agent never closes its own work.
        """
        if role == packet.gev_role:
            raise PermissionError(
                f"role {role!r} generated this packet and cannot verify it"
            )
        if packet.verifier_decision is None:
            raise ValueError("packet carries no verifier decision")
        return packet.verifier_decision["verdict"]

    @staticmethod
    def evaluate(packet: RunPacket, role: str,
                 defects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Record evaluator findings on the packet and return them.

        The evaluator cannot be the generator, and evaluation never
        sets the verifier decision.
        """
        if role == packet.gev_role:
            raise PermissionError(
                f"role {role!r} generated this packet and cannot evaluate it"
            )
        findings: list[dict[str, Any]] = []
        for defect in defects:
            finding = DefectFinding(
                finding_id=f"EV-{uuid.uuid4().hex[:8]}",
                type=str(defect.get("type", "unspecified")),
                severity=str(defect.get("severity", "medium")),
                description=str(defect.get("description", "")),
                location=str(defect.get("location", "")),
            )
            packet.evaluator_findings.append(finding)
            findings.append(dict(defect))
        return findings
