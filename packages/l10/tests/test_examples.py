"""The runnable example in examples/ is executed here so it cannot rot."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "closed_loop_demo.py"


def test_demo_runs_and_returns_expected_result(capsys):
    sys.path.insert(0, str(EXAMPLE.parents[1] / "packages" / "l10" / "src"))
    try:
        module = runpy.run_path(str(EXAMPLE))
        result = module["run_demo"]()
        rc = module["main"]()
    finally:
        sys.path.pop(0)
    out = capsys.readouterr().out
    assert rc == 0
    assert result["policy_passed"] is True
    assert result["failed_gates"] == []
    assert result["budget_remaining_tokens"] == 990
    assert result["self_review_blocked"] is True
    assert result["verdict"] == "PASS"
    assert result["artifacts"] == 1
    assert '"self_review_blocked": true' in out
