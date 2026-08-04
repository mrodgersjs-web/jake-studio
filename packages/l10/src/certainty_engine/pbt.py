"""Faculty 11: Property-Based Testing Gate — GL-L10-CE-02

The contradiction net for non-formalizable claims.
Declares invariants (properties, not examples) and uses Hypothesis-class
generators to hunt inputs that break them, shrinking to minimal failure.

Defense against weak oracles — catches what the LLM-judge rubber-stamps.
"""
from __future__ import annotations
import json
import random
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from common import ProofPacket, Confidence, run_energy

class InvariantType(Enum):
    ROUND_TRIP = "round_trip"           # decode(encode(x)) == x
    IDEMPOTENCE = "idempotence"         # f(f(x)) == f(x)
    CONSERVATION = "conservation"       # sum(outputs) == sum(inputs)
    MONOTONICITY = "monotonicity"       # x1 <= x2 => f(x1) <= f(x2)
    HOARE_TRIPLE = "hoare_triple"       # precondition => postcondition
    IDENTITY = "identity"               # f(x) == x for identity ops
    COMMUTATIVITY = "commutativity"     # f(a,b) == f(b,a)
    ASSOCIATIVITY = "associativity"     # f(f(a,b),c) == f(a,b,c)

@dataclass
class Property:
    """A declared invariant that must always hold."""
    name: str
    invariant_type: InvariantType
    description: str
    check_fn: Callable[[Any], bool]
    generator: Callable[[], Any]
    min_samples: int = 100
    max_examples: int = 1000

@dataclass
class ShrunkFailure:
    """Minimal failing case found by shrinking."""
    original_input: Any
    shrunk_input: Any
    property_name: str
    error: str
    shrink_steps: int

@dataclass
class PBTResult:
    """Result of a property-based test run."""
    property_name: str
    samples_tested: int
    passed: bool
    failures: list[ShrunkFailure] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PropertyBasedTester:
    """Hypothesis-class property-based testing for RIG claims.
    
    Declares invariants as properties, generates random inputs,
    and shrinks failures to minimal counterexamples.
    
    Anti-pattern: reject specs that fuse 'what' with 'how'.
    The property states the CONTRACT, never the implementation.
    """
    
    def __init__(self):
        self.properties: dict[str, Property] = {}
        self.results: list[PBTResult] = []
    
    def declare(self, prop: Property) -> None:
        """Register a property invariant."""
        self._validate_spec_hygiene(prop)
        self.properties[prop.name] = prop
    
    def declare_round_trip(self, name: str, encode: Callable, decode: Callable,
                           generator: Callable, **kwargs) -> None:
        """Convenience: declare decode(encode(x)) == x."""
        self.declare(Property(
            name=name,
            invariant_type=InvariantType.ROUND_TRIP,
            description=f"decode(encode(x)) == x for {name}",
            check_fn=lambda x: decode(encode(x)) == x,
            generator=generator,
            **kwargs,
        ))
    
    def declare_idempotence(self, name: str, fn: Callable, 
                            generator: Callable, **kwargs) -> None:
        """Convenience: declare f(f(x)) == f(x)."""
        self.declare(Property(
            name=name,
            invariant_type=InvariantType.IDEMPOTENCE,
            description=f"f(f(x)) == f(x) for {name}",
            check_fn=lambda x: fn(fn(x)) == fn(x),
            generator=generator,
            **kwargs,
        ))
    
    def declare_conservation(self, name: str, process: Callable,
                             input_sum: Callable, output_sum: Callable,
                             generator: Callable, **kwargs) -> None:
        """Convenience: declare sum(outputs) == sum(inputs)."""
        def check(x):
            result = process(x)
            return output_sum(result) == input_sum(x)
        self.declare(Property(
            name=name,
            invariant_type=InvariantType.CONSERVATION,
            description=f"conservation for {name}",
            check_fn=check,
            generator=generator,
            **kwargs,
        ))
    
    def declare_monotonicity(self, name: str, fn: Callable,
                              generator: Callable, compare: Callable = None,
                              **kwargs) -> None:
        """Convenience: declare x1 <= x2 => f(x1) <= f(x2)."""
        cmp = compare or (lambda a, b: a <= b)
        def check(pair):
            x1, x2 = pair
            if not cmp(x1, x2):
                return True  # skip if not ordered
            return cmp(fn(x1), fn(x2))
        self.declare(Property(
            name=name,
            invariant_type=InvariantType.MONOTONICITY,
            description=f"monotonicity for {name}",
            check_fn=check,
            generator=generator,
            **kwargs,
        ))
    
    def run(self, prop_name: Optional[str] = None) -> list[PBTResult]:
        """Run property tests. If prop_name given, test only that one."""
        targets = {prop_name: self.properties[prop_name]} if prop_name else self.properties
        results = []
        
        for name, prop in targets.items():
            failures = []
            for i in range(prop.max_examples):
                try:
                    input_val = prop.generator()
                    if not prop.check_fn(input_val):
                        shrunk = self._shrink(prop, input_val)
                        failures.append(shrunk)
                        if len(failures) >= 5:  # cap failures
                            break
                except Exception as e:
                    failures.append(ShrunkFailure(
                        original_input=None, shrunk_input=None,
                        property_name=name, error=str(e), shrink_steps=0,
                    ))
            
            result = PBTResult(
                property_name=name,
                samples_tested=min(prop.max_examples, prop.min_samples + i),
                passed=len(failures) == 0,
                failures=failures,
            )
            results.append(result)
            self.results.append(result)
        
        return results
    
    def verify_all(self) -> dict:
        """Run all declared properties and return summary."""
        results = self.run()
        all_passed = all(r.passed for r in results)
        total_failures = sum(len(r.failures) for r in results)
        
        return {
            "verdict": "PASS" if all_passed else "FAIL",
            "properties_tested": len(results),
            "properties_passed": sum(1 for r in results if r.passed),
            "total_failures": total_failures,
            "shrunk_failures": [
                {"property": f.property_name, "shrunk": str(f.shrunk_input)[:200]}
                for r in results for f in r.failures
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def _shrink(self, prop: Property, failing_input: Any, max_steps: int = 50) -> ShrunkFailure:
        """Shrink a failing input to the minimal counterexample."""
        current = failing_input
        steps = 0
        
        for _ in range(max_steps):
            shrunk = self._try_shrink_once(current)
            if shrunk is None or shrunk == current:
                break
            try:
                if not prop.check_fn(shrunk):
                    current = shrunk
                    steps += 1
                else:
                    break
            except Exception:
                break
        
        return ShrunkFailure(
            original_input=failing_input,
            shrunk_input=current,
            property_name=prop.name,
            error="invariant violated",
            shrink_steps=steps,
        )
    
    def _try_shrink_once(self, val: Any) -> Any:
        """Attempt one shrink step. Generic: try halving, removing elements, etc."""
        if isinstance(val, (int, float)):
            return val // 2 if isinstance(val, int) else val / 2
        if isinstance(val, list) and len(val) > 1:
            return val[:len(val) // 2]
        if isinstance(val, str) and len(val) > 1:
            return val[:len(val) // 2]
        if isinstance(val, tuple) and len(val) > 1:
            return val[:len(val) // 2]
        return None
    
    def _validate_spec_hygiene(self, prop: Property) -> None:
        """Reject specs that fuse 'what' with 'how'.
        
        A spec committing to an algorithm inherits its incidental details,
        defeating the point. The property states the contract, never the implementation.
        """
        if "sort" in prop.description.lower() and "bubble" in prop.description.lower():
            raise ValueError(f"Spec fuses what with how: {prop.description}")
        if "implement" in prop.description.lower():
            raise ValueError(f"Spec describes implementation, not contract: {prop.description}")

def to_proof_packet(result: dict) -> ProofPacket:
    """Convert PBT result to a ProofPacket."""
    return ProofPacket(
        formula_id="PBT",
        verdict=result["verdict"],
        returned_value=result,
        substrate="hypothesis-pbt",
        agreement_delta=0.0,
    )
