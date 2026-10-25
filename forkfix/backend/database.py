"""SQLite database persistence engine for Forkfix runs, checkpoints, branches, and events."""

from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, db_path: str = "runs/forkfix.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    issue_text TEXT NOT NULL,
                    base_image_uuid TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_cost REAL DEFAULT 0.0,
                    elapsed_seconds REAL DEFAULT 0.0,
                    winning_branch_id TEXT,
                    winning_patch TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branches (
                    branch_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    parent_checkpoint TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    step_count INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    hint TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    PRIMARY KEY (run_id, branch_id),
                    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    step_idx INTEGER NOT NULL,
                    command TEXT NOT NULL,
                    output TEXT NOT NULL,
                    cost REAL NOT NULL,
                    snapshot_uuid TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_run_branch ON steps (run_id, branch_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_run ON events (run_id)")

    def create_run(self, run_id: str, issue_text: str, base_image_uuid: str = "mock-swe-base") -> dict[str, Any]:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (run_id, issue_text, base_image_uuid, status, created_at, updated_at)
                VALUES (?, ?, ?, 'running', ?, ?)
                """,
                (run_id, issue_text, base_image_uuid, now, now),
            )
        return self.get_run(run_id)  # type: ignore

    def update_run_status(
        self,
        run_id: str,
        status: str,
        total_cost: float | None = None,
        elapsed_seconds: float | None = None,
        winning_branch_id: str | None = None,
        winning_patch: str | None = None,
    ):
        now = time.time()
        updates = ["status = ?", "updated_at = ?"]
        params: list[Any] = [status, now]

        if total_cost is not None:
            updates.append("total_cost = ?")
            params.append(total_cost)
        if elapsed_seconds is not None:
            updates.append("elapsed_seconds = ?")
            params.append(elapsed_seconds)
        if winning_branch_id is not None:
            updates.append("winning_branch_id = ?")
            params.append(winning_branch_id)
        if winning_patch is not None:
            updates.append("winning_patch = ?")
            params.append(winning_patch)

        params.append(run_id)
        query = f"UPDATE runs SET {', '.join(updates)} WHERE run_id = ?"

        with self._get_connection() as conn:
            conn.execute(query, params)

    def record_branch(
        self,
        run_id: str,
        branch_id: str,
        parent_checkpoint: str,
        tier: str,
        model: str,
        status: str = "exploring",
        hint: str = "",
    ):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO branches (branch_id, run_id, parent_checkpoint, tier, model, status, hint, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (branch_id, run_id, parent_checkpoint, tier, model, status, hint, now),
            )

    def record_step(
        self,
        run_id: str,
        branch_id: str,
        step_idx: int,
        command: str,
        output: str,
        cost: float,
        snapshot_uuid: str,
    ):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO steps (run_id, branch_id, step_idx, command, output, cost, snapshot_uuid, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, branch_id, step_idx, command, output, cost, snapshot_uuid, now),
            )
            # Update branch stats
            conn.execute(
                """
                UPDATE branches
                SET step_count = step_count + 1, cost = cost + ?
                WHERE run_id = ? AND branch_id = ?
                """,
                (cost, run_id, branch_id),
            )

    def record_event(self, run_id: str, event_type: str, payload: dict[str, Any]):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO events (run_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, event_type, json.dumps(payload), now),
            )

    log_event = record_event

    def get_run_events(self, run_id: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE run_id = ? ORDER BY id ASC",
                (run_id,),
            ).fetchall()
            events = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("payload"), str):
                    try:
                        item["payload"] = json.loads(item["payload"])
                    except Exception:
                        pass
                events.append(item)
            return events

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if not row:
                return None
            run_data = dict(row)

            # Attach branches
            branch_rows = conn.execute("SELECT * FROM branches WHERE run_id = ?", (run_id,)).fetchall()
            run_data["branches"] = [dict(b) for b in branch_rows]

            return run_data

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_run(self, run_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            return cursor.rowcount > 0


_default_db: Database | None = None


def get_db(db_path: str = "runs/forkfix.db") -> Database:
    global _default_db
    if _default_db is None:
        _default_db = Database(db_path)
    return _default_db
