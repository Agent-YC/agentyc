"""Tests for core.screener — screening agent."""

import json

from core.screener import screen_agent, ScreeningResult, _parse_response


class TestScreeningResult:
    def test_overall_computation(self):
        r = ScreeningResult(
            verdict="ADMIT",
            clarity=80,
            feasibility=70,
            safety=90,
            market_fit=60,
        )
        # 0.25*80 + 0.25*70 + 0.30*90 + 0.20*60 = 20+17.5+27+12 = 76.5 ≈ 76
        assert r.overall == 76

    def test_to_dict(self):
        r = ScreeningResult(
            verdict="REJECT", clarity=10, feasibility=10, safety=10, market_fit=10
        )
        d = r.to_dict()
        assert d["verdict"] == "REJECT"
        assert "scores" in d
        assert "feedback" in d


class TestParseResponse:
    def test_valid_json(self):
        raw = json.dumps(
            {
                "verdict": "ADMIT",
                "clarity": 85,
                "feasibility": 70,
                "safety": 90,
                "market_fit": 60,
                "feedback": "Good agent.",
            }
        )
        r = _parse_response(raw)
        assert r.verdict == "ADMIT"
        assert r.clarity == 85
        assert r.feedback == "Good agent."

    def test_invalid_json_falls_back(self):
        r = _parse_response("not json at all")
        assert r.verdict == "CONDITIONAL"
        assert "unparseable" in r.feedback.lower()

    def test_unknown_verdict_normalized(self):
        raw = json.dumps({"verdict": "maybe", "clarity": 50})
        r = _parse_response(raw)
        assert r.verdict == "CONDITIONAL"

    def test_clamps_scores(self):
        raw = json.dumps({"verdict": "ADMIT", "clarity": 150, "safety": -10})
        r = _parse_response(raw)
        assert r.clarity == 100
        assert r.safety == 0


class TestScreenAgent:
    def test_screen_returns_result(self, sample_agent_spec, mock_ollama_response):
        response = json.dumps(
            {
                "verdict": "ADMIT",
                "clarity": 80,
                "feasibility": 75,
                "safety": 85,
                "market_fit": 70,
                "feedback": "Strong spec. Consider adding error handling documentation.",
            }
        )
        mock = mock_ollama_response(responses=[response])
        result = screen_agent(sample_agent_spec, mock)
        assert isinstance(result, ScreeningResult)
        assert result.verdict == "ADMIT"
        assert result.clarity == 80

    def test_screen_handles_bad_response(self, sample_agent_spec, mock_ollama_response):
        mock = mock_ollama_response(responses=["garbled response"])
        result = screen_agent(sample_agent_spec, mock)
        assert result.verdict == "CONDITIONAL"
