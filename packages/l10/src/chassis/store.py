"""GL-L10-CH-04: State Store — durable, checkpoint, resume.

SQLite-backed state store that persists:
- Current state and next legal transitions
- Completed and pending tasks
- Artifact references
- Tool-side transaction identifiers
- Budget consumed and remaining
- Approval state
- Open risks and evaluator defects

A process restart must resume safely without repeating a committed side effect.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Dict, List
from contextlib import contextmanager

from .fsm import RunState


class StateStore:
    """Durable SQLite-backed state store for workflow execution.

    Checkpoint after every consequential transition.
    Resume by loading run state and replaying pending tasks.
    Idempotency keys prevent duplicate side effects on resume.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._db_path = Path(db_path) if db_path != ":memory:" else None
        self._conn = sqlite3.connect(db_path) if db_path == ":memory:" else sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database tables."""
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                harness_name TEXT NOT NULL,
                harness_version TEXT NOT NULL,
                initial_state TEXT NOT NULL,
                current_state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                budget_tokens INTEGER DEFAULT 0,
                budget_consumed_tokens INTEGER DEFAULT 0,
                budget_consumed_usd REAL DEFAULT 0.0,
                goal TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                payload TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                run_id TEXT NOT NULL,
                path TEXT NOT NULL,
                hash TEXT NOT NULL,
                size_bytes INTEGER DEFAULT 0,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (run_id, path),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                side_effect_class TEXT NOT NULL,
                input_summary TEXT,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration_ms INTEGER,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                run_id TEXT NOT NULL,
                key TEXT NOT NULL,
                committed_at TEXT NOT NULL,
                side_effect TEXT,
                PRIMARY KEY (run_id, key),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                run_id TEXT NOT NULL,
                gate TEXT NOT NULL,
                approved_by TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                PRIMARY KEY (run_id, gate, action),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS defects (
                run_id TEXT NOT NULL,
                finding_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT,
                resolved INTEGER DEFAULT 0,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        self._conn.commit()

    def create_run(self, run_id: str, harness_name: str, harness_version: str,
                   goal: Optional[str] = None, budget_tokens: int = 0) -> None:
        """Create a new run record."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO runs (run_id, harness_name, harness_version,
                              initial_state, current_state, created_at, updated_at,
                              budget_tokens, goal, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, harness_name, harness_version,
              RunState.INTAKE.value, RunState.INTAKE.value, now, now,
              budget_tokens, goal, json.dumps({})))
        self._conn.commit()

    def set_state(self, run_id: str, state: RunState, actor: str,
                  reason: Optional[str] = None) -> None:
        """Update the current state and record the transition."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        # Get previous state
        cursor.execute("SELECT current_state FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        prev_state = row["current_state"] if row else RunState.INTAKE.value

        # Record transition
        cursor.execute("""
            INSERT INTO transitions (run_id, from_state, to_state, actor, timestamp, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (run_id, prev_state, state.value, actor, now, reason))

        # Update run state
        cursor.execute("""
            UPDATE runs SET current_state = ?, updated_at = ? WHERE run_id = ?
        """, (state.value, now, run_id))
        self._conn.commit()

    def get_state(self, run_id: str) -> Optional[RunState]:
        """Get the current state of a run."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT current_state FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if row:
            return RunState(row["current_state"])
        return None

    def get_run_state(self, run_id: str) -> Optional[dict]:
        """Get the full run state as a dict."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT run_id, harness_name, harness_version, current_state,
                   budget_tokens, budget_consumed_tokens, budget_consumed_usd,
                   goal, metadata, created_at, updated_at
            FROM runs WHERE run_id = ?
        """, (run_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def checkpoint(self, run_id: str) -> None:
        """Checkpoint the run state (explicit persist)."""
        # In SQLite, writes are already persisted via commit on each op.
        # This method exists for interface compatibility and explicit signaling.
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE runs SET updated_at = ? WHERE run_id = ?", (now, run_id))
        self._conn.commit()

    def commit_idempotency_key(self, run_id: str, key: str,
                               side_effect: Optional[str] = None) -> None:
        """Commit an idempotency key to prevent duplicate side effects."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO idempotency_keys
            (run_id, key, committed_at, side_effect)
            VALUES (?, ?, ?, ?)
        """, (run_id, key, now, side_effect))
        self._conn.commit()

    def is_idempotency_committed(self, run_id: str, key: str) -> bool:
        """Check if an idempotency key has been committed."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT 1 FROM idempotency_keys WHERE run_id = ? AND key = ?
        """, (run_id, key))
        return cursor.fetchone() is not None

    def consume_budget(self, run_id: str, tokens: int = 0,
                       cost_usd: float = 0.0) -> None:
        """Track budget consumption for a run."""
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE runs
            SET budget_consumed_tokens = budget_consumed_tokens + ?,
                budget_consumed_usd = budget_consumed_usd + ?
            WHERE run_id = ?
        """, (tokens, cost_usd, run_id))
        self._conn.commit()

    def add_artifact(self, run_id: str, path: str, hash: str,
                     size_bytes: int = 0) -> None:
        """Record an artifact reference with provenance hash."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO artifacts
            (run_id, path, hash, size_bytes, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, path, hash, size_bytes, now))
        self._conn.commit()

    def record_tool_call(self, run_id: str, tool_name: str,
                         side_effect_class: str, input_summary: str,
                         status: str, duration_ms: Optional[int] = None) -> None:
        """Record a tool call."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO tool_calls
            (run_id, tool_name, side_effect_class, input_summary, status, timestamp, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run_id, tool_name, side_effect_class, input_summary, status, now, duration_ms))
        self._conn.commit()

    def record_approval(self, run_id: str, gate: str, approved_by: str,
                        action: str) -> None:
        """Record a human approval."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO approvals
            (run_id, gate, approved_by, action, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, gate, approved_by, action, now))
        self._conn.commit()

    def add_task(self, run_id: str, task_id: str, name: str,
                 payload: Optional[str] = None) -> None:
        """Add a task to the run."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO tasks (task_id, run_id, name, status, payload, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
        """, (task_id, run_id, name, payload, now))
        self._conn.commit()

    def start_task(self, run_id: str, task_id: str) -> None:
        """Mark a task as in-progress."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE tasks SET status = 'in_progress', started_at = ?
            WHERE task_id = ? AND run_id = ?
        """, (now, task_id, run_id))
        self._conn.commit()

    def complete_task(self, run_id: str, task_id: str) -> None:
        """Mark a task as completed."""
        cursor = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE tasks SET status = 'completed', completed_at = ?
            WHERE task_id = ? AND run_id = ?
        """, (now, task_id, run_id))
        self._conn.commit()

    def get_pending_tasks(self, run_id: str) -> List[dict]:
        """Get all pending/in-progress tasks for a run (for resume)."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT task_id, name, status, payload, created_at, started_at, completed_at
            FROM tasks WHERE run_id = ? AND status IN ('pending', 'in_progress')
            ORDER BY created_at
        """, (run_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_transition_history(self, run_id: str) -> List[dict]:
        """Get all state transitions for a run."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT from_state, to_state, actor, timestamp, reason
            FROM transitions
            WHERE run_id = ?
            ORDER BY id
        """, (run_id,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
