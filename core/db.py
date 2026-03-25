"""Local SQLite storage for agents, evals, and coach sessions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    description   TEXT,
    author        TEXT,
    spec_yaml     TEXT NOT NULL,
    status        TEXT DEFAULT 'submitted',
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evals (
    id            TEXT PRIMARY KEY,
    agent_id      TEXT REFERENCES agents(id),
    batch_id      TEXT,
    verified      INTEGER DEFAULT 0,
    score_reliability INTEGER,
    score_cost    INTEGER,
    score_safety  INTEGER,
    score_speed   INTEGER,
    score_overall INTEGER,
    challenges    TEXT,
    traces        TEXT,
    meta          TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS coach_sessions (
    id            TEXT PRIMARY KEY,
    agent_id      TEXT REFERENCES agents(id),
    mode          TEXT DEFAULT 'local',
    messages      TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);
"""


class LocalDB:
    """SQLite database for local Agent YC storage.

    All data is stored in ``<project_root>/.agentyc/agentyc.db``.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    # -- connection management -------------------------------------------------

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._init_schema()
        return self._conn

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- agents ----------------------------------------------------------------

    def save_agent(
        self,
        agent_id: str,
        name: str,
        spec_yaml: str,
        *,
        description: str = "",
        author: str = "",
        status: str = "submitted",
    ) -> str:
        """Insert or update an agent record. Returns the agent id."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO agents (id, name, description, author, spec_yaml, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                author=excluded.author,
                spec_yaml=excluded.spec_yaml,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (agent_id, name, description, author, spec_yaml, status, now, now),
        )
        self.conn.commit()
        return agent_id

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_agents(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM agents ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def update_agent_status(self, agent_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE agents SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, agent_id),
        )
        self.conn.commit()

    # -- evals -----------------------------------------------------------------

    def save_eval(
        self,
        agent_id: str,
        scores: dict[str, int],
        *,
        eval_id: str | None = None,
        batch_id: str = "",
        verified: bool = False,
        challenges: list[dict[str, Any]] | None = None,
        traces: list[dict[str, Any]] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> str:
        """Save an eval result. Returns the eval id."""
        eid = eval_id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO evals
                (id, agent_id, batch_id, verified,
                 score_reliability, score_cost, score_safety, score_speed, score_overall,
                 challenges, traces, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                eid,
                agent_id,
                batch_id,
                int(verified),
                scores.get("reliability", 0),
                scores.get("cost", 0),
                scores.get("safety", 0),
                scores.get("speed", 0),
                scores.get("overall", 0),
                json.dumps(challenges or []),
                json.dumps(traces or []),
                json.dumps(meta or {}),
            ),
        )
        self.conn.commit()
        return eid

    def get_evals(self, agent_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM evals WHERE agent_id = ? ORDER BY created_at DESC",
            (agent_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["challenges"] = json.loads(d["challenges"]) if d["challenges"] else []
            d["traces"] = json.loads(d["traces"]) if d["traces"] else []
            d["meta"] = json.loads(d["meta"]) if d["meta"] else {}
            results.append(d)
        return results

    def get_latest_eval(self, agent_id: str) -> dict[str, Any] | None:
        evals = self.get_evals(agent_id)
        return evals[0] if evals else None

    # -- coach sessions --------------------------------------------------------

    def save_coach_session(
        self,
        agent_id: str,
        messages: list[dict[str, str]],
        *,
        session_id: str | None = None,
        mode: str = "local",
    ) -> str:
        """Save a coaching session. Returns the session id."""
        sid = session_id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO coach_sessions (id, agent_id, mode, messages)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET messages=excluded.messages
            """,
            (sid, agent_id, mode, json.dumps(messages)),
        )
        self.conn.commit()
        return sid

    def get_coach_sessions(self, agent_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM coach_sessions WHERE agent_id = ? ORDER BY created_at DESC",
            (agent_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["messages"] = json.loads(d["messages"]) if d["messages"] else []
            results.append(d)
        return results


def get_db(project_dir: str | Path | None = None) -> LocalDB:
    """Get a LocalDB instance for the given project directory.

    If *project_dir* is None, uses the current working directory.
    """
    base = Path(project_dir) if project_dir else Path.cwd()
    db_path = base / ".agentyc" / "agentyc.db"
    return LocalDB(db_path)
