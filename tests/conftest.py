"""Shared test fixtures for Agent YC tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_spec_data():
    """Return a valid agent spec dict."""
    return {
        "name": "TestBot",
        "version": "1.0.0",
        "author": "tester",
        "description": "A test agent for unit tests.",
        "tools": ["web_search", "calculator"],
        "constraints": {
            "max_cost_per_task": 0.05,
            "max_latency": "30s",
            "safety_level": "standard",
        },
        "expected_behaviors": ["Always cite sources", "Stay within budget"],
        "entrypoint": "./agent.py",
    }


@pytest.fixture
def sample_spec_yaml(sample_spec_data):
    """Return valid agent spec as YAML string."""
    import yaml

    return yaml.dump(sample_spec_data, default_flow_style=False)


@pytest.fixture
def sample_spec_file(tmp_dir, sample_spec_yaml):
    """Write a valid agent spec to disk and return its path."""
    spec_path = tmp_dir / "agent.yml"
    spec_path.write_text(sample_spec_yaml, encoding="utf-8")
    # Also create the entrypoint file
    (tmp_dir / "agent.py").write_text("# placeholder", encoding="utf-8")
    return spec_path


@pytest.fixture
def sample_agent_spec(sample_spec_file):
    """Parse and return an AgentSpec from the sample spec file."""
    from core.spec import parse_spec

    return parse_spec(sample_spec_file)


@pytest.fixture
def mock_ollama_response():
    """Return a factory for mock Ollama responses."""

    class MockOllamaClient:
        def __init__(self, responses=None):
            self.responses = responses or ["Mock response"]
            self._call_idx = 0
            self.model = "test-model"
            self.calls = []

        def generate(self, prompt, **kwargs):
            self.calls.append(("generate", prompt, kwargs))
            resp = self.responses[self._call_idx % len(self.responses)]
            self._call_idx += 1
            return resp

        def chat(self, messages, **kwargs):
            self.calls.append(("chat", messages, kwargs))
            resp = self.responses[self._call_idx % len(self.responses)]
            self._call_idx += 1
            return resp

        def list_models(self):
            return ["test-model"]

        def is_available(self):
            return True

    return MockOllamaClient
