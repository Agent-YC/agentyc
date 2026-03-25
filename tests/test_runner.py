"""Tests for core.runner — agent runner."""

from core.runner import (
    RunResult,
    detect_entrypoint_type,
    run_python_agent,
    run_agent,
    run_callable_agent,
    run_langchain_agent,
)


class TestDetectEntrypointType:
    def test_python_script(self):
        assert detect_entrypoint_type("./agent.py") == "python"
        assert detect_entrypoint_type("agents/main.py") == "python"

    def test_docker(self):
        assert detect_entrypoint_type("docker://myagent:latest") == "docker"

    def test_api(self):
        assert detect_entrypoint_type("https://api.example.com/run") == "api"
        assert detect_entrypoint_type("http://localhost:8000/agent") == "api"

    def test_unknown(self):
        assert detect_entrypoint_type("something_else") == "unknown"


class TestRunPythonAgent:
    def test_run_with_run_function(self, tmp_dir):
        script = tmp_dir / "agent.py"
        script.write_text(
            'def run(task):\n    return f"Processed: {task}"\n',
            encoding="utf-8",
        )
        result = run_python_agent(str(script), "test task")
        assert result.success is True
        assert "Processed: test task" in result.output

    def test_run_as_subprocess(self, tmp_dir):
        script = tmp_dir / "agent.py"
        script.write_text(
            'import sys\nprint(f"Got: {sys.argv[1]}")\n',
            encoding="utf-8",
        )
        result = run_python_agent(str(script), "hello", cwd=tmp_dir)
        assert result.success is True
        assert "Got: hello" in result.output

    def test_script_not_found(self, tmp_dir):
        result = run_python_agent(str(tmp_dir / "nonexistent.py"), "test")
        assert result.success is False
        assert "not found" in result.error


class TestRunCallableAgent:
    def test_simple_callable(self):
        def my_agent(task):
            return f"Done: {task}"

        result = run_callable_agent(my_agent, "test")
        assert result.success is True
        assert result.output == "Done: test"

    def test_callable_error(self):
        def bad_agent(task):
            raise ValueError("Something broke")

        result = run_callable_agent(bad_agent, "test")
        assert result.success is False
        assert "Something broke" in result.error


class TestRunLangchainAgent:
    def test_with_invoke(self):
        class FakeRunnable:
            def invoke(self, inputs):
                return {"output": f"Invoked with: {inputs['input']}"}

        result = run_langchain_agent(FakeRunnable(), "test prompt")
        assert result.success is True
        assert "Invoked with: test prompt" in result.output

    def test_with_run(self):
        class FakeChain:
            def run(self, prompt):
                return f"Ran: {prompt}"

        result = run_langchain_agent(FakeChain(), "test prompt")
        assert result.success is True
        assert "Ran: test prompt" in result.output

    def test_with_callable(self):
        class FakeAgent:
            def __call__(self, prompt):
                return f"Called: {prompt}"

        result = run_langchain_agent(FakeAgent(), "test")
        assert result.success is True
        assert "Called: test" in result.output

    def test_unsupported_agent(self):
        result = run_langchain_agent(42, "test")
        assert result.success is False
        assert "invoke()" in result.error


class TestRunAgent:
    def test_dispatches_to_python(self, tmp_dir, sample_agent_spec):
        # Create the entrypoint script
        script = tmp_dir / "agent.py"
        script.write_text(
            'def run(task):\n    return f"Agent: {task}"\n',
            encoding="utf-8",
        )
        # Override spec entrypoint
        sample_agent_spec.entrypoint = "./agent.py"
        result = run_agent(sample_agent_spec, "test", cwd=tmp_dir)
        assert result.success is True

    def test_unknown_entrypoint(self, sample_agent_spec):
        sample_agent_spec.entrypoint = "weird_format"
        result = run_agent(sample_agent_spec, "test")
        assert result.success is False
        assert "Unknown entrypoint type" in result.error


class TestRunResult:
    def test_to_dict(self):
        r = RunResult(output="hello", duration_seconds=1.5, success=True)
        d = r.to_dict()
        assert d["output"] == "hello"
        assert d["success"] is True
        assert d["duration_seconds"] == 1.5
