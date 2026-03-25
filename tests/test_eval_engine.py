"""Tests for core.eval_engine — evaluation engine."""

import json

from core.eval_engine import (
    Challenge,
    ChallengeResult,
    EvalResult,
    load_challenges,
    run_challenge,
    run_eval,
)


class TestChallenge:
    def test_from_yaml(self, tmp_dir):
        yml = tmp_dir / "test_challenge.yml"
        yml.write_text(
            """\
id: test/basic
name: Basic Test
category: reliability
difficulty: easy
description: A basic test challenge.
setup:
  prompt: "Answer the question: What is 2+2?"
evaluation:
  type: exact_match
  expected: "4"
""",
            encoding="utf-8",
        )
        ch = Challenge.from_yaml(yml)
        assert ch.id == "test/basic"
        assert ch.category == "reliability"
        assert ch.evaluation["type"] == "exact_match"


class TestLoadChallenges:
    def test_load_from_builtin_registry(self):
        challenges = load_challenges()
        # Should find our 10 built-in challenges
        assert len(challenges) >= 10
        categories = {c.category for c in challenges}
        assert "reliability" in categories
        assert "cost" in categories
        assert "safety" in categories
        assert "speed" in categories

    def test_load_with_category_filter(self):
        challenges = load_challenges(category="reliability")
        assert len(challenges) >= 3
        assert all(c.category == "reliability" for c in challenges)

    def test_load_empty_directory(self, tmp_dir):
        challenges = load_challenges(tmp_dir)
        assert challenges == []


class TestRunChallenge:
    def test_run_with_llm_judge(self, sample_agent_spec, mock_ollama_response):
        challenge = Challenge(
            id="test/llm_judge",
            name="LLM Judge Test",
            category="reliability",
            evaluation={
                "type": "llm_judge",
                "judge_prompt": "Rate the output.",
            },
        )
        mock = mock_ollama_response(
            responses=[
                "Here is my synthesized response...",  # agent output
                json.dumps(
                    {"score": 75, "passed": True, "details": "Good job."}
                ),  # judge
            ]
        )
        result = run_challenge(sample_agent_spec, challenge, mock)
        assert isinstance(result, ChallengeResult)
        assert result.score == 75
        assert result.passed is True

    def test_run_with_exact_match(self, sample_agent_spec, mock_ollama_response):
        challenge = Challenge(
            id="test/exact",
            name="Exact Match Test",
            category="cost",
            evaluation={
                "type": "exact_match",
                "expected": "42",
            },
        )
        mock = mock_ollama_response(responses=["42"])
        result = run_challenge(sample_agent_spec, challenge, mock)
        assert result.passed is True
        assert result.score == 100

    def test_run_with_regex(self, sample_agent_spec, mock_ollama_response):
        challenge = Challenge(
            id="test/regex",
            name="Regex Test",
            category="safety",
            evaluation={
                "type": "regex",
                "pattern": r"\d{3}-\d{2}-\d{4}",
            },
        )
        mock = mock_ollama_response(responses=["SSN: 123-45-6789"])
        result = run_challenge(sample_agent_spec, challenge, mock)
        assert result.passed is True


class TestRunEval:
    def test_full_eval(self, sample_agent_spec, mock_ollama_response):
        challenges = [
            Challenge(
                id="r/test",
                name="R Test",
                category="reliability",
                evaluation={"type": "llm_judge"},
            ),
            Challenge(
                id="c/test",
                name="C Test",
                category="cost",
                evaluation={"type": "llm_judge"},
            ),
            Challenge(
                id="s/test",
                name="S Test",
                category="safety",
                evaluation={"type": "llm_judge"},
            ),
            Challenge(
                id="sp/test",
                name="Sp Test",
                category="speed",
                evaluation={"type": "llm_judge"},
            ),
        ]
        # Each challenge needs 2 responses: agent output + judge verdict
        judge_response = json.dumps({"score": 80, "passed": True, "details": "Good."})
        mock = mock_ollama_response(
            responses=[
                "Agent output 1",
                judge_response,
                "Agent output 2",
                judge_response,
                "Agent output 3",
                judge_response,
                "Agent output 4",
                judge_response,
            ]
        )
        result = run_eval(sample_agent_spec, challenges=challenges, ollama=mock)
        assert isinstance(result, EvalResult)
        assert result.agent_id == sample_agent_spec.id
        assert len(result.challenges) == 4
        assert result.scorecard.overall > 0

    def test_eval_result_to_dict(self, sample_agent_spec, mock_ollama_response):
        judge_response = json.dumps({"score": 70, "passed": True, "details": "OK."})
        mock = mock_ollama_response(responses=["Output", judge_response])
        challenges = [
            Challenge(
                id="test/ch",
                name="Test",
                category="reliability",
                evaluation={"type": "llm_judge"},
            ),
        ]
        result = run_eval(sample_agent_spec, challenges=challenges, ollama=mock)
        d = result.to_dict()
        assert "scores" in d
        assert "challenges" in d
        assert "meta" in d
