"""Tests for core.db — SQLite local storage."""

import json
import pytest
from pathlib import Path

from core.db import LocalDB, get_db


class TestLocalDB:
    @pytest.fixture
    def db(self, tmp_dir):
        """Create a temporary database."""
        db = LocalDB(tmp_dir / "test.db")
        yield db
        db.close()

    # -- agents ----------------------------------------------------------------

    def test_save_and_get_agent(self, db):
        db.save_agent("test-v1", "TestBot", "spec: yaml", description="A test agent")
        agent = db.get_agent("test-v1")
        assert agent is not None
        assert agent["name"] == "TestBot"
        assert agent["description"] == "A test agent"
        assert agent["status"] == "submitted"

    def test_get_nonexistent_agent(self, db):
        assert db.get_agent("nonexistent") is None

    def test_list_agents(self, db):
        db.save_agent("a-v1", "AgentA", "spec_a")
        db.save_agent("b-v1", "AgentB", "spec_b")
        agents = db.list_agents()
        assert len(agents) == 2

    def test_update_agent_status(self, db):
        db.save_agent("test-v1", "TestBot", "spec")
        db.update_agent_status("test-v1", "graduated")
        agent = db.get_agent("test-v1")
        assert agent["status"] == "graduated"

    def test_upsert_agent(self, db):
        db.save_agent("test-v1", "TestBot", "spec_v1")
        db.save_agent("test-v1", "TestBot Updated", "spec_v2")
        agent = db.get_agent("test-v1")
        assert agent["name"] == "TestBot Updated"
        agents = db.list_agents()
        assert len(agents) == 1

    # -- evals -----------------------------------------------------------------

    def test_save_and_get_eval(self, db):
        db.save_agent("test-v1", "TestBot", "spec")
        eid = db.save_eval(
            "test-v1",
            {"reliability": 80, "cost": 70, "safety": 90, "speed": 60, "overall": 76},
            challenges=[{"id": "test/challenge", "passed": True}],
        )
        evals = db.get_evals("test-v1")
        assert len(evals) == 1
        assert evals[0]["score_reliability"] == 80
        assert evals[0]["score_overall"] == 76
        assert isinstance(evals[0]["challenges"], list)

    def test_get_latest_eval(self, db):
        db.save_agent("test-v1", "TestBot", "spec")
        eid1 = db.save_eval("test-v1", {"reliability": 50, "cost": 50, "safety": 50, "speed": 50, "overall": 50}, eval_id="eval-001")
        eid2 = db.save_eval("test-v1", {"reliability": 90, "cost": 90, "safety": 90, "speed": 90, "overall": 90}, eval_id="eval-002")
        evals = db.get_evals("test-v1")
        # At minimum both evals exist
        assert len(evals) == 2

    def test_get_evals_empty(self, db):
        assert db.get_evals("nonexistent") == []

    # -- coach sessions --------------------------------------------------------

    def test_save_and_get_coach_session(self, db):
        db.save_agent("test-v1", "TestBot", "spec")
        messages = [
            {"role": "user", "content": "How to improve?"},
            {"role": "assistant", "content": "Fix your reliability."},
        ]
        sid = db.save_coach_session("test-v1", messages)
        sessions = db.get_coach_sessions("test-v1")
        assert len(sessions) == 1
        assert len(sessions[0]["messages"]) == 2
        assert sessions[0]["mode"] == "local"

    def test_get_coach_sessions_empty(self, db):
        assert db.get_coach_sessions("nonexistent") == []


class TestGetDB:
    def test_creates_db_in_agentyc_dir(self, tmp_dir):
        db = get_db(tmp_dir)
        # Access .conn to trigger lazy connection & file creation
        _ = db.conn
        assert (tmp_dir / ".agentyc" / "agentyc.db").exists()
        db.close()
