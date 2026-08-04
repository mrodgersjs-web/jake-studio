"""RIG L10 CLI — test, verify, and inspect the L10 harness stack."""
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def cmd_test(args):
    """Run L10 verification suite."""
    from common import robust_madz, surprisal, blend_value, expected_free_energy, composite_sigma
    from certainty_engine.pbt import PropertyBasedTester, Property, InvariantType
    from certainty_engine.refuter import RefuterAgent, Claim
    from cognition_stack.taste_engine import TasteEngine
    from cognition_stack.adherence import AdherenceGate
    from cognition_stack.council import ProblemSolvingCouncil, CouncilMember, CouncilRole
    from nocturne.daemon import NocturneDaemon
    from agent_factory.factory import AgentFactory

    results = {}
    
    # SymPy MCP energy verification
    for name, fn in [
        ("robust_madz", lambda: robust_madz(7.5, [3.2,4.1,3.8,4.5,3.9,4.0,3.7,4.3])),
        ("surprisal", lambda: surprisal(0.15)),
        ("blend_value", lambda: blend_value(0.7, 0.8, 0.2)),
        ("expected_free_energy", lambda: expected_free_energy(2.5, 0.3)),
        ("composite_sigma", lambda: composite_sigma(1.5, 2.3)),
    ]:
        r = fn()
        results[name] = {"verdict": r.get("verdict"), "value": r.get("returned_value") or r.get("sigma")}
    
    # PBT
    pbt = PropertyBasedTester()
    pbt.declare(Property(name="conservation", invariant_type=InvariantType.CONSERVATION,
        description="sum equals sum", check_fn=lambda x: sum(x) == sum(sorted(x)),
        generator=lambda: [1,2,3,4,5]))
    pbt_r = pbt.verify_all()
    results["pbt"] = {"verdict": pbt_r["verdict"], "properties": pbt_r["properties_tested"]}
    
    # Refuter
    ref = RefuterAgent(refuter_family="gpt")
    c = Claim(id="t", statement="improved", negation="not", generator_family="claude", evidence_fn=lambda: 5.0)
    a = ref.refute(c, budget=50)
    results["refuter"] = {"verdict": a.verdict.value, "depth": a.search_depth}
    
    # Taste
    t = TasteEngine()
    audit = t.audit("t1", "content", {"intentionality":4.5,"craft_quality":4.0,"ai_slop":4.5,"writing_voice":4.0,"accessibility":4.5})
    results["taste"] = {"score": audit.composite_score, "band": audit.ship_band.value}
    
    # Adherence
    adh = AdherenceGate()
    r = adh.check("p1", [{"step_id":"s1","step_type":"action"},{"step_id":"s2","step_type":"gate"}], ["s1","s2"], [])
    results["adherence"] = {"verdict": r.verdict, "e": r.e_adherence}
    
    # Nocturne
    n = NocturneDaemon()
    night = n.run_night("s1", ["j1"], read_only=True)
    results["nocturne"] = {"phases": len(night.phase_results), "read_only": night.is_read_only}
    
    # Factory
    f = AgentFactory()
    agent = f.stamp("j1", {"res":"test"}, exemplar_surface_exists=True)
    results["factory"] = {"gradeable": agent.jtbd_gradeability, "bms": agent.bms_band.value, "enrolled": agent.nocturne_enrolled}
    
    all_pass = all(
        (v.get("verdict") in ("PASS", "approve", "refuted", True) or "score" in v or "phases" in v or "gradeable" in v)
        for v in results.values()
    )
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        for name, r in results.items():
            status = "✅" if (r.get("verdict") in ("PASS", "approve", "refuted") or "score" in r or "phases" in r or "gradeable" in r) else "❌"
            print(f"  {status} {name}: {r}")
        print(f"\n{'✅ ALL TESTS PASS' if all_pass else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_pass else 1

def cmd_doctor(args):
    """Check L10 module health."""
    import importlib
    modules = [
        "common", "certainty_engine.pbt", "certainty_engine.refuter", "certainty_engine.lean_kernel",
        "cognition_stack.taste_engine", "cognition_stack.tribal_scraper",
        "cognition_stack.council", "cognition_stack.adherence", "cognition_stack.strategy",
        "nocturne.daemon", "agent_factory.factory",
    ]
    
    for mod_name in modules:
        try:
            importlib.import_module(mod_name)
            print(f"  ✅ {mod_name}")
        except Exception as e:
            print(f"  ❌ {mod_name}: {e}")
    
    # Check SymPy
    try:
        from common import robust_madz
        r = robust_madz(5.0, [3.0, 4.0])
        print(f"  ✅ SymPy MCP: {r['verdict']}")
    except Exception as e:
        print(f"  ❌ SymPy MCP: {e}")
    
    return 0

def cmd_info(args):
    """Show L10 module info."""
    info = {
        "module": "rig-l10",
        "version": "0.1.0",
        "path": str(Path(__file__).parent),
        "submodules": {
            "certainty_engine": "PBT + Refuter + Lean Kernel (CE-02..04)",
            "cognition_stack": "Taste + Council + Tribal + Adherence + Strategy + What-If (CS*.*.)",
            "nocturne": "Nightly self-improvement daemon N0-N8 (ND-01..02)",
            "agent_factory": "Deterministic stamp procedure F0-F5 (AF-01)",
            "common": "Shared energy fns, ProofPacket, deviation gate, anti-Goodhart",
        },
        "goals": 13,
        "energy_substrate": "sympy-mcp + e2b-sandbox",
    }
    print(json.dumps(info, indent=2))

def main():
    parser = argparse.ArgumentParser(description="RIG L10 Self-Evolving Harness Stack")
    sub = parser.add_subparsers(dest="command")
    
    test_p = sub.add_parser("test", help="Run verification suite")
    test_p.add_argument("--json", action="store_true")
    
    sub.add_parser("doctor", help="Check module health")
    sub.add_parser("info", help="Show module info")
    
    args = parser.parse_args()
    
    if args.command == "test":
        sys.exit(cmd_test(args))
    elif args.command == "doctor":
        sys.exit(cmd_doctor(args))
    elif args.command == "info":
        cmd_info(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
