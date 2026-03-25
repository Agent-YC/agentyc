"""Agent runner — executes real agents against challenge prompts.

Supports three entrypoint types:
  - Python script (local .py file with a run() function)
  - Docker container (docker:// URI)
  - API endpoint (http:// or https:// URL)

Also supports popular frameworks:
  - LangChain agents
  - CrewAI agents
  - AutoGen agents
  - Generic callable agents
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from core.spec import AgentSpec


@dataclass
class RunResult:
    """Result from running an agent against a prompt."""

    output: str
    duration_seconds: float
    success: bool
    error: str = ""
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata or {},
        }


# -- Entrypoint type detection ------------------------------------------------

def detect_entrypoint_type(entrypoint: str) -> str:
    """Detect the type of agent entrypoint.

    Returns:
        One of: 'python', 'docker', 'api', 'unknown'
    """
    if entrypoint.startswith("docker://"):
        return "docker"
    if entrypoint.startswith(("http://", "https://")):
        return "api"
    if entrypoint.endswith(".py"):
        return "python"
    return "unknown"


# -- Main runner ---------------------------------------------------------------

def run_agent(
    spec: AgentSpec,
    prompt: str,
    *,
    timeout: float = 120.0,
    cwd: str | Path | None = None,
) -> RunResult:
    """Run an agent against a single prompt.

    Automatically detects the entrypoint type and dispatches to the
    appropriate runner.

    Args:
        spec: The agent specification.
        prompt: The challenge prompt / task to run.
        timeout: Maximum execution time in seconds.
        cwd: Working directory (defaults to current dir).

    Returns:
        A RunResult with the agent's output and metadata.
    """
    entrypoint = spec.entrypoint
    ep_type = detect_entrypoint_type(entrypoint)

    if ep_type == "python":
        return run_python_agent(entrypoint, prompt, timeout=timeout, cwd=cwd)
    elif ep_type == "docker":
        return run_docker_agent(entrypoint, prompt, timeout=timeout)
    elif ep_type == "api":
        return run_api_agent(entrypoint, prompt, timeout=timeout)
    else:
        return RunResult(
            output="",
            duration_seconds=0.0,
            success=False,
            error=f"Unknown entrypoint type: '{entrypoint}'. "
                  f"Use a .py file, docker:// URI, or http(s):// URL.",
        )


# -- Python script runner -----------------------------------------------------

def run_python_agent(
    script_path: str,
    prompt: str,
    *,
    timeout: float = 120.0,
    cwd: str | Path | None = None,
) -> RunResult:
    """Run a Python agent script.

    The script must either define a ``run(task: str) -> str`` function
    or accept the task as a command-line argument.

    Also supports LangChain, CrewAI, and other framework agents
    by trying to call their standard entry points.

    Args:
        script_path: Path to the Python script.
        prompt: The task prompt.
        timeout: Maximum execution time.
        cwd: Working directory.

    Returns:
        RunResult with the agent's output.
    """
    start = time.time()
    resolved = Path(cwd or ".") / script_path if not Path(script_path).is_absolute() else Path(script_path)

    if not resolved.exists():
        return RunResult(
            output="", duration_seconds=0.0, success=False,
            error=f"Agent script not found: {resolved}",
        )

    # Try 1: Import and call run() function directly
    try:
        result = _call_run_function(resolved, prompt)
        duration = time.time() - start
        return RunResult(
            output=result,
            duration_seconds=round(duration, 2),
            success=True,
            metadata={"method": "import", "script": str(resolved)},
        )
    except Exception:
        pass

    # Try 2: Execute as subprocess
    try:
        proc = subprocess.run(
            [sys.executable, str(resolved), prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )
        duration = time.time() - start

        if proc.returncode == 0:
            return RunResult(
                output=proc.stdout.strip(),
                duration_seconds=round(duration, 2),
                success=True,
                metadata={"method": "subprocess", "script": str(resolved)},
            )
        else:
            return RunResult(
                output=proc.stdout.strip(),
                duration_seconds=round(duration, 2),
                success=False,
                error=proc.stderr.strip() or f"Exit code {proc.returncode}",
                metadata={"method": "subprocess", "exit_code": proc.returncode},
            )
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=f"Agent timed out after {timeout}s",
        )
    except Exception as e:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=str(e),
        )


def _call_run_function(script_path: Path, prompt: str) -> str:
    """Import a Python script and call its run() function."""
    spec_loader = importlib.util.spec_from_file_location("agent_module", str(script_path))
    if spec_loader is None or spec_loader.loader is None:
        raise ImportError(f"Cannot load {script_path}")

    module = importlib.util.module_from_spec(spec_loader)
    spec_loader.loader.exec_module(module)

    if hasattr(module, "run"):
        result = module.run(prompt)
        return str(result) if result is not None else ""
    else:
        raise AttributeError(f"No run() function in {script_path}")


# -- Docker runner -------------------------------------------------------------

def run_docker_agent(
    image_uri: str,
    prompt: str,
    *,
    timeout: float = 120.0,
) -> RunResult:
    """Run a Docker-based agent.

    The image URI should be in the format ``docker://image:tag``.
    The prompt is passed via stdin.

    Args:
        image_uri: Docker image URI (e.g., ``docker://myagent:latest``).
        prompt: The task prompt.
        timeout: Maximum execution time.

    Returns:
        RunResult with the container's stdout.
    """
    start = time.time()
    image = image_uri.replace("docker://", "")

    try:
        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", "none",  # No network by default (safety)
                "-i",                 # Accept stdin
                "--memory", "512m",   # Memory limit
                "--cpus", "1",        # CPU limit
                image,
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.time() - start

        if proc.returncode == 0:
            return RunResult(
                output=proc.stdout.strip(),
                duration_seconds=round(duration, 2),
                success=True,
                metadata={"method": "docker", "image": image},
            )
        else:
            return RunResult(
                output=proc.stdout.strip(),
                duration_seconds=round(duration, 2),
                success=False,
                error=proc.stderr.strip() or f"Container exit code {proc.returncode}",
                metadata={"method": "docker", "image": image, "exit_code": proc.returncode},
            )
    except FileNotFoundError:
        return RunResult(
            output="", duration_seconds=0.0, success=False,
            error="Docker is not installed or not in PATH.",
        )
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=f"Docker container timed out after {timeout}s",
        )


# -- API endpoint runner -------------------------------------------------------

def run_api_agent(
    endpoint_url: str,
    prompt: str,
    *,
    timeout: float = 120.0,
    headers: dict[str, str] | None = None,
) -> RunResult:
    """Run a remotely deployed agent via HTTP API.

    Sends a POST request with the task prompt and expects a JSON
    response with an ``output`` field.

    Args:
        endpoint_url: The agent's API endpoint.
        prompt: The task prompt.
        timeout: Maximum request time.
        headers: Optional HTTP headers (e.g., auth).

    Returns:
        RunResult with the API response.
    """
    start = time.time()

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                endpoint_url,
                json={"task": prompt, "prompt": prompt},
                headers=headers or {},
            )
            duration = time.time() - start

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    output = data.get("output", data.get("response", data.get("result", str(data))))
                except (json.JSONDecodeError, ValueError):
                    output = resp.text

                return RunResult(
                    output=str(output),
                    duration_seconds=round(duration, 2),
                    success=True,
                    metadata={"method": "api", "endpoint": endpoint_url, "status": 200},
                )
            else:
                return RunResult(
                    output=resp.text,
                    duration_seconds=round(duration, 2),
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    metadata={"method": "api", "endpoint": endpoint_url, "status": resp.status_code},
                )
    except httpx.TimeoutException:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=f"API request timed out after {timeout}s",
        )
    except httpx.ConnectError:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=f"Cannot connect to {endpoint_url}",
        )
    except Exception as e:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=str(e),
        )


# -- Framework-specific runners ------------------------------------------------

def run_langchain_agent(
    agent_or_chain: Any,
    prompt: str,
    *,
    timeout: float = 120.0,
) -> RunResult:
    """Run a LangChain agent or chain.

    Supports: AgentExecutor, Chain, Runnable, and any object with
    `invoke()`, `run()`, or `__call__()` methods.

    Args:
        agent_or_chain: A LangChain agent, chain, or runnable.
        prompt: The task prompt.
        timeout: Maximum execution time.

    Returns:
        RunResult with the agent's output.
    """
    start = time.time()

    try:
        # LangChain Runnables (LCEL) — .invoke()
        if hasattr(agent_or_chain, "invoke"):
            result = agent_or_chain.invoke({"input": prompt})
        # Legacy chains — .run()
        elif hasattr(agent_or_chain, "run"):
            result = agent_or_chain.run(prompt)
        # Callable
        elif callable(agent_or_chain):
            result = agent_or_chain(prompt)
        else:
            return RunResult(
                output="", duration_seconds=0.0, success=False,
                error="LangChain agent must have invoke(), run(), or __call__()",
            )

        duration = time.time() - start

        # Extract output from various LangChain result formats
        if isinstance(result, dict):
            output = result.get("output", result.get("result", result.get("text", str(result))))
        elif isinstance(result, str):
            output = result
        else:
            output = str(result)

        return RunResult(
            output=output,
            duration_seconds=round(duration, 2),
            success=True,
            metadata={"method": "langchain", "agent_type": type(agent_or_chain).__name__},
        )
    except Exception as e:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=f"LangChain error: {e}",
        )


def run_crewai_agent(
    crew: Any,
    prompt: str,
    *,
    timeout: float = 120.0,
) -> RunResult:
    """Run a CrewAI crew.

    Args:
        crew: A CrewAI Crew instance.
        prompt: The task prompt (passed as input).
        timeout: Maximum execution time.

    Returns:
        RunResult with the crew's output.
    """
    start = time.time()

    try:
        if hasattr(crew, "kickoff"):
            result = crew.kickoff(inputs={"task": prompt})
        else:
            return RunResult(
                output="", duration_seconds=0.0, success=False,
                error="CrewAI crew must have kickoff() method.",
            )

        duration = time.time() - start
        output = str(result) if result is not None else ""

        return RunResult(
            output=output,
            duration_seconds=round(duration, 2),
            success=True,
            metadata={"method": "crewai", "crew_type": type(crew).__name__},
        )
    except Exception as e:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=f"CrewAI error: {e}",
        )


def run_callable_agent(
    fn: Callable[[str], str],
    prompt: str,
    *,
    timeout: float = 120.0,
) -> RunResult:
    """Run any callable that accepts a string and returns a string.

    This is the simplest integration point — wrap your agent in a function.

    Args:
        fn: A callable ``(str) -> str``.
        prompt: The task prompt.
        timeout: Maximum execution time.

    Returns:
        RunResult with the function's output.
    """
    start = time.time()
    try:
        result = fn(prompt)
        duration = time.time() - start
        return RunResult(
            output=str(result) if result is not None else "",
            duration_seconds=round(duration, 2),
            success=True,
            metadata={"method": "callable", "fn_name": fn.__name__},
        )
    except Exception as e:
        duration = time.time() - start
        return RunResult(
            output="", duration_seconds=round(duration, 2), success=False,
            error=str(e),
        )
