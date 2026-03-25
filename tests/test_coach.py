"""Tests for core.coach — coaching agent."""

import pytest

from core.coach import get_coaching, get_coaching_chat, _build_context
from core.eval_engine import EvalResult, ChallengeResult
from core.scorer import Scorecard


@pytest.fixture
def sample_eval_result():
    return EvalResult(
        agent_id="test-v1",
        scorecard=Scorecard(reliability=70, cost=60, safety=85, speed=55),
        challenges=[
            ChallengeResult(
                challenge_id="reliability/test",
                name="Reliability Test",
                passed=True,
                score=70,
                details="Mostly good.",
            ),
            ChallengeResult(
                challenge_id="cost/test",
                name="Cost Test",
                passed=False,
                score=40,
                details="Over budget.",
            ),
        ],
    )


class TestBuildContext:
    def test_context_with_eval(self, sample_agent_spec, sample_eval_result):
        ctx = _build_context(sample_agent_spec, sample_eval_result)
        assert "Agent Spec" in ctx
        assert "Eval Scorecard" in ctx
        assert "70/100" in ctx
        assert "✅ PASS" in ctx
        assert "❌ FAIL" in ctx

    def test_context_without_eval(self, sample_agent_spec):
        ctx = _build_context(sample_agent_spec, None)
        assert "Agent Spec" in ctx
        assert "No eval results yet" in ctx


class TestGetCoaching:
    def test_single_shot(
        self, sample_agent_spec, sample_eval_result, mock_ollama_response
    ):
        mock = mock_ollama_response(responses=["Focus on reducing cost per task."])
        response = get_coaching(
            sample_agent_spec,
            sample_eval_result,
            "How do I improve my cost score?",
            mock,
        )
        assert "cost" in response.lower()
        assert len(mock.calls) == 1

    def test_without_eval(self, sample_agent_spec, mock_ollama_response):
        mock = mock_ollama_response(responses=["Start by running an eval."])
        response = get_coaching(
            sample_agent_spec,
            None,
            "What should I do first?",
            mock,
        )
        assert isinstance(response, str)


class TestGetCoachingChat:
    def test_multi_turn(
        self, sample_agent_spec, sample_eval_result, mock_ollama_response
    ):
        mock = mock_ollama_response(responses=["Your reliability is decent."])
        messages = [
            {"role": "user", "content": "How's my agent doing?"},
        ]
        response = get_coaching_chat(
            sample_agent_spec, sample_eval_result, messages, mock
        )
        assert isinstance(response, str)
        # Should have the context messages + user message
        call_args = mock.calls[0]
        assert call_args[0] == "chat"
