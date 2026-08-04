#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/packages/l10"
python3 -m compileall -q src
python3 -m pip install -U pip setuptools wheel -q
python3 -m pip install -e ".[test]" -q
python3 -m pytest -q tests/test_l10.py --tb=line
rig-l10 doctor
rig-l10 test
echo "jake-studio smoke PASS"
