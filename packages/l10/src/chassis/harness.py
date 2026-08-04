"""GL-L10-CH-01: Harness Registry — sealed, versioned H=(E,T,C,S,L,V).

Every production capability runs through a sealed, versioned harness.
The harness binds Identity/Execution, Tools, Context, State, Loop, and
Verification into a single hash-chained artifact.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field, field_validator, model_validator


# ── H=(E,T,C,S,L,V) Components ─────────────────────────────────────────


class Environment(BaseModel):
    """E — Identity/Execution contract: role, objective, non-goals, boundaries."""
    role: str  # "generator" | "evaluator" | "verifier"
    objective: str
    non_goals: List[str] = Field(default_factory=list)
    boundaries: List[str] = Field(default_factory=list)

    model_config = {"validate_assignment": True}


class ToolAllowlist(BaseModel):
    """T — Explicit tool allowlist with permissions, budgets, side-effect classes."""
    tools: List[str] = Field(default_factory=list)
    budgets: Dict[str, int] = Field(default_factory=dict)
    approval_required: Dict[str, bool] = Field(default_factory=dict)
    rate_limits: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ContextSpec(BaseModel):
    """C — Required inputs, schemas, retrieval rules, freshness constraints."""
    inputs: List[str] = Field(default_factory=list)
    schemas: List[str] = Field(default_factory=list)
    freshness_hours: int = 24
    retrieval_rules: Dict[str, str] = Field(default_factory=dict)


class StateSpec(BaseModel):
    """S — Checkpoints, durable memory, ownership, lifecycle, recovery."""
    checkpoint_after: str = "every_transition"
    durable: bool = True
    memory_scope: str = ""
    recovery_route: str = ""
    ownership: str = ""


class LoopSpec(BaseModel):
    """L — Staged workflow, critique/revision cycles, escalation conditions."""
    stages: List[str] = Field(default_factory=list)
    max_revisions: int = 3
    critique_cycles: int = 3
    escalation_conditions: List[str] = Field(default_factory=list)


class VerificationSpec(BaseModel):
    """V — Proof obligations, evaluator tests, verifier authority, promotion gate."""
    proof_obligations: List[str] = Field(default_factory=list)
    evaluator_tests: List[str] = Field(default_factory=list)
    verifier_authority: str = "jake"
    promotion_gate: str = "closed"


# ── Harness Tuple ──────────────────────────────────────────────────────


class Harness(BaseModel):
    """Sealed, versioned harness H=(E,T,C,S,L,V).

    The signature is over the sorted JSON of all six components,
    ensuring that any change to any component invalidates the signature.
    """
    name: str
    version: str
    E: Environment
    T: ToolAllowlist
    C: ContextSpec
    S: StateSpec
    L: LoopSpec
    V: VerificationSpec

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "system"

    @model_validator(mode="after")
    def validate_components(self) -> "Harness":
        """Ensure all six H=(E,T,C,S,L,V) components are present and valid."""
        # Pydantic already enforces presence, but we add semantic checks
        if self.E.role not in ("generator", "evaluator", "verifier"):
            raise ValueError(f"Invalid role '{self.E.role}' — must be generator/evaluator/verifier")
        return self

    def sign(self) -> str:
        """Compute signature hash over sorted JSON of all six components."""
        content = {
            "E": self.E.model_dump(),
            "T": self.T.model_dump(),
            "C": self.C.model_dump(),
            "S": self.S.model_dump(),
            "L": self.L.model_dump(),
            "V": self.V.model_dump(),
        }
        serialized = json.dumps(content, sort_keys=True, default=str)
        return "sha256:" + hashlib.sha256(serialized.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Return the full harness as a dict, including signature."""
        result = self.model_dump()
        result["signature"] = self.sign()
        return result


class HarnessRegistry:
    """Manages sealed, versioned harness definitions.

    Harnesses are immutable once registered. New versions create new entries.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._harnesses: Dict[str, Harness] = {}
        self._signatures: Dict[str, str] = {}
        self._storage_path = Path(storage_path) if storage_path else None
        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)

    def register(self, harness: Harness) -> dict:
        """Register a harness. Returns status dict with signature.

        Raises ValueError if a harness with the same name+version already exists.
        """
        key = f"{harness.name}@{harness.version}"
        if key in self._harnesses:
            raise ValueError(
                f"Harness '{key}' already registered. "
                f"New versions must use a new version string."
            )

        signature = harness.sign()
        self._harnesses[key] = harness
        self._signatures[key] = signature

        if self._storage_path:
            self._persist(harness)

        return {
            "status": "registered",
            "harness_name": harness.name,
            "version": harness.version,
            "signature": signature,
            "created_at": harness.created_at,
        }

    def get(self, name: str, version: str) -> Optional[Harness]:
        """Retrieve a registered harness by name and version."""
        key = f"{name}@{version}"
        return self._harnesses.get(key)

    def verify(self, harness: Harness) -> bool:
        """Verify a harness signature matches its content."""
        key = f"{harness.name}@{harness.version}"
        stored_sig = self._signatures.get(key)
        if stored_sig is None:
            return False
        return stored_sig == harness.sign()

    def list(self) -> List[str]:
        """List all registered harness names+versions."""
        return list(self._harnesses.keys())

    def _persist(self, harness: Harness) -> None:
        """Persist harness to storage."""
        path = self._storage_path / f"{harness.name}@{harness.version}.json"
        path.write_text(json.dumps(harness.to_dict(), indent=2))


class HarnessTuple(BaseModel):
    """Serializable harness tuple for interchange.

    This is the sealed artifact format that travels between systems.
    """
    name: str
    version: str
    signature: str
    E: dict
    T: dict
    C: dict
    S: dict
    L: dict
    V: dict

    @classmethod
    def from_harness(cls, harness: Harness) -> "HarnessTuple":
        """Create a HarnessTuple from a Harness."""
        return cls(
            name=harness.name,
            version=harness.version,
            signature=harness.sign(),
            E=harness.E.model_dump(),
            T=harness.T.model_dump(),
            C=harness.C.model_dump(),
            S=harness.S.model_dump(),
            L=harness.L.model_dump(),
            V=harness.V.model_dump(),
        )
