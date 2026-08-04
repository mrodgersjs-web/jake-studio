"""RIG L10 CLI — doctor + core test for the public harness surface."""
from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def cmd_doctor(_args: argparse.Namespace) -> int:
    mods = [
        "common",
        "certainty_engine.pbt",
        "certainty_engine.refuter",
        "cognition_stack.taste_engine",
        "cognition_stack.adherence",
        "nocturne.daemon",
        "agent_factory.factory",
    ]
    missing = []
    for m in mods:
        try:
            __import__(m)
        except Exception as exc:  # noqa: BLE001
            missing.append({"module": m, "error": str(exc)})
    payload = {"ok": not missing, "checked": len(mods), "missing": missing}
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


def cmd_test(_args: argparse.Namespace) -> int:
    from common import (
        ProofPacket,
        blend_value,
        composite_sigma,
        expected_free_energy,
        robust_madz,
        surprisal,
    )
    from certainty_engine.pbt import InvariantType, Property, PropertyBasedTester

    results = {}
    failed = 0
    for name, fn in [
        ("robust_madz", lambda: robust_madz(7.5, [3.2, 4.1, 3.8, 4.5, 3.9, 4.0, 3.7, 4.3])),
        ("surprisal", lambda: surprisal(0.15)),
        ("blend_value", lambda: blend_value(0.7, 0.8, 0.2)),
        ("expected_free_energy", lambda: expected_free_energy(2.5, 0.3)),
        ("composite_sigma", lambda: composite_sigma(1.5, 2.3)),
    ]:
        r = fn()
        ok = r.get("verdict") == "PASS"
        results[name] = {"ok": ok, "verdict": r.get("verdict")}
        failed += 0 if ok else 1

    pbt = PropertyBasedTester()
    pbt.declare(
        Property(
            name="conservation",
            invariant_type=InvariantType.CONSERVATION,
            description="sum equals sum",
            check_fn=lambda x: sum(x) == sum(sorted(x)),
            generator=lambda: [1, 2, 3, 4, 5],
        )
    )
    pbt_r = pbt.verify_all()
    ok = pbt_r.get("verdict") == "PASS"
    results["pbt"] = {"ok": ok, "verdict": pbt_r.get("verdict")}
    failed += 0 if ok else 1

    seal = ProofPacket(formula_id="smoke", verdict="PASS", returned_value=1).seal()
    results["proof_packet"] = {"ok": bool(seal), "seal_prefix": str(seal)[:24]}

    tests_dir = Path(__file__).resolve().parent.parent / "tests"
    loader = unittest.TestLoader()
    suite = loader.discover(str(tests_dir), pattern="test_l10.py")
    runner = unittest.TextTestRunner(verbosity=1)
    ut = runner.run(suite)
    results["unittest_l10"] = {
        "ok": ut.wasSuccessful(),
        "ran": ut.testsRun,
        "failures": len(ut.failures) + len(ut.errors),
    }
    failed += 0 if ut.wasSuccessful() else 1
    print(json.dumps({"ok": failed == 0, "failed": failed, "results": results}, indent=2))
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rig-l10", description="RIG L10 public harness CLI")
    sub = parser.add_subparsers(dest="cmd")
    p_test = sub.add_parser("test", help="run core L10 verification")
    p_test.set_defaults(func=cmd_test)
    p_doc = sub.add_parser("doctor", help="check import surface")
    p_doc.set_defaults(func=cmd_doctor)
    args = parser.parse_args(argv)
    if not args.cmd:
        return cmd_test(args)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
