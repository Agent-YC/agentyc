"""Tests for core.spec — agent spec parser and validator."""

import pytest
import yaml
from pathlib import Path

from core.spec import (
    AgentSpec,
    Constraints,
    parse_spec,
    validate_spec_data,
    spec_to_yaml,
    VALID_SAFETY_LEVELS,
)


class TestConstraints:
    def test_default_safety_level(self):
        c = Constraints()
        assert c.safety_level == "standard"

    def test_valid_safety_levels(self):
        for level in VALID_SAFETY_LEVELS:
            c = Constraints(safety_level=level)
            assert c.safety_level == level

    def test_invalid_safety_level(self):
        with pytest.raises(ValueError, match="Invalid safety_level"):
            Constraints(safety_level="invalid")


class TestAgentSpec:
    def test_id_generation(self):
        spec = AgentSpec(
            name="Research Bot",
            version="1.0.0",
            description="A research agent.",
            entrypoint="./agent.py",
        )
        assert spec.id == "research-bot-v1.0.0"

    def test_id_handles_spaces(self):
        spec = AgentSpec(
            name="My Cool Agent",
            version="2.0",
            description="Test",
            entrypoint="./agent.py",
        )
        assert spec.id == "my-cool-agent-v2.0"


class TestParseSpec:
    def test_parse_valid_spec(self, sample_spec_file):
        spec = parse_spec(sample_spec_file)
        assert spec.name == "TestBot"
        assert spec.version == "1.0.0"
        assert spec.author == "tester"
        assert "web_search" in spec.tools
        assert spec.constraints.safety_level == "standard"
        assert spec.constraints.max_cost_per_task == 0.05

    def test_parse_nonexistent_file(self, tmp_dir):
        with pytest.raises(FileNotFoundError):
            parse_spec(tmp_dir / "nonexistent.yml")

    def test_parse_invalid_yaml(self, tmp_dir):
        bad_file = tmp_dir / "bad.yml"
        bad_file.write_text("just a string, not a mapping", encoding="utf-8")
        with pytest.raises(ValueError, match="YAML mapping"):
            parse_spec(bad_file)

    def test_parse_missing_required_fields(self, tmp_dir):
        spec_file = tmp_dir / "agent.yml"
        spec_file.write_text(
            yaml.dump({"name": "Incomplete"}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Missing required field"):
            parse_spec(spec_file)

    def test_parse_minimal_spec(self, tmp_dir):
        """Minimal valid spec with just required fields."""
        (tmp_dir / "agent.py").write_text("# agent", encoding="utf-8")
        spec_file = tmp_dir / "agent.yml"
        spec_file.write_text(
            yaml.dump({
                "name": "MinimalBot",
                "version": "0.1",
                "description": "A minimal agent.",
                "entrypoint": "./agent.py",
            }),
            encoding="utf-8",
        )
        spec = parse_spec(spec_file)
        assert spec.name == "MinimalBot"
        assert spec.tools == []
        assert spec.constraints.safety_level == "standard"


class TestValidateSpecData:
    def test_valid_data(self, sample_spec_data):
        errors = validate_spec_data(sample_spec_data)
        assert errors == []

    def test_missing_name(self, sample_spec_data):
        del sample_spec_data["name"]
        errors = validate_spec_data(sample_spec_data)
        assert any("name" in e for e in errors)

    def test_missing_description(self, sample_spec_data):
        del sample_spec_data["description"]
        errors = validate_spec_data(sample_spec_data)
        assert any("description" in e for e in errors)

    def test_invalid_safety_level(self, sample_spec_data):
        sample_spec_data["constraints"]["safety_level"] = "yolo"
        errors = validate_spec_data(sample_spec_data)
        assert any("safety_level" in e for e in errors)

    def test_negative_cost(self, sample_spec_data):
        sample_spec_data["constraints"]["max_cost_per_task"] = -1
        errors = validate_spec_data(sample_spec_data)
        assert any("non-negative" in e for e in errors)

    def test_tools_not_list(self, sample_spec_data):
        sample_spec_data["tools"] = "web_search"
        errors = validate_spec_data(sample_spec_data)
        assert any("list" in e for e in errors)

    def test_entrypoint_not_found(self, sample_spec_data, tmp_dir):
        sample_spec_data["entrypoint"] = "./nonexistent.py"
        errors = validate_spec_data(sample_spec_data, spec_dir=tmp_dir)
        assert any("Entrypoint not found" in e for e in errors)

    def test_docker_entrypoint_skips_check(self, sample_spec_data, tmp_dir):
        sample_spec_data["entrypoint"] = "docker://myagent:latest"
        errors = validate_spec_data(sample_spec_data, spec_dir=tmp_dir)
        assert not any("Entrypoint not found" in e for e in errors)


class TestSpecToYaml:
    def test_roundtrip(self, sample_spec_file):
        spec = parse_spec(sample_spec_file)
        yaml_str = spec_to_yaml(spec)
        data = yaml.safe_load(yaml_str)
        assert data["name"] == "TestBot"
        assert data["version"] == "1.0.0"
        assert data["constraints"]["safety_level"] == "standard"
