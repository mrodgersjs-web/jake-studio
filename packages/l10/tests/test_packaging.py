"""Tests for packaging invariants that drifted before.

Plain regex parsing keeps this runnable on every supported Python.
"""
from __future__ import annotations

import re
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = (PKG_ROOT / "pyproject.toml").read_text()
PACKAGES = ["agent_factory", "agentic_doctrines", "certainty_engine",
            "chassis", "cognition_stack", "nocturne"]


def test_pyproject_version_is_0_2_0():
    match = re.search(r'^version = "([^"]+)"', PYPROJECT, re.MULTILINE)
    assert match is not None
    assert match.group(1) == "0.2.0"


def test_runtime_dependencies_include_pydantic_and_sympy():
    deps = re.search(r'^dependencies = \[(.*?)\]', PYPROJECT, re.MULTILINE)
    assert deps is not None
    assert "pydantic" in deps.group(1)
    assert "sympy" in deps.group(1)


def test_every_package_ships_py_typed():
    for name in PACKAGES:
        assert (PKG_ROOT / "src" / name / "py.typed").is_file(), name


def test_package_data_declares_py_typed():
    assert '["py.typed"]' in PYPROJECT
