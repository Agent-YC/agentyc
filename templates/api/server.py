"""HTTP API agent server.

A simple Flask/http.server agent that receives tasks via POST
and returns JSON responses. Run this server, then use agent-yc
to evaluate it.

Usage:
    # Start the server
    python server.py

    # In another terminal
    cd demo/api-agent
    agent-yc eval

    # Or test directly
    curl -X POST http://localhost:8080/run \
         -H "Content-Type: application/json" \
         -d '{"task": "Research quantum computing"}'
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class AgentHandler(BaseHTTPRequestHandler):
    """HTTP handler for the demo API agent."""

    def do_POST(self):
        if self.path != "/run":
            self._send_json(404, {"error": f"Not found: {self.path}"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        task = data.get("task") or data.get("prompt", "")
        if not task:
            self._send_json(400, {"error": "Missing 'task' field"})
            return

        result = process_task(task)
        self._send_json(200, result)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "agent": "api-deployed-agent"})
        else:
            self._send_json(
                200,
                {
                    "name": "api-deployed-agent",
                    "version": "1.0.0",
                    "endpoints": {
                        "POST /run": "Run a task",
                        "GET /health": "Health check",
                    },
                },
            )

    def _send_json(self, status: int, data: dict):
        response = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        print(f"[API Agent] {args[0]}")


def process_task(task: str) -> dict:
    """Process a research task and return structured output."""
    task_lower = task.lower()

    if any(w in task_lower for w in ["inject", "ignore", "forget"]):
        output = (
            "I've detected a potential prompt injection attempt. "
            "I will not modify my behavior. Please submit a legitimate task."
        )
    elif "synthesize" in task_lower or "research" in task_lower:
        output = (
            "## API Agent Research Response\n\n"
            "Based on analysis:\n\n"
            "1. **Finding 1**: Primary consensus supports the hypothesis "
            "(Source: Academic DB, confidence: high)\n"
            "2. **Finding 2**: Contradicting perspective found "
            "(Source: ArXiv 2024, confidence: medium)\n\n"
            "### Sources\n"
            "- [1] Academic Database — peer-reviewed\n"
            "- [2] ArXiv preprint — not yet peer-reviewed"
        )
    else:
        output = (
            f"## API Agent Response\n\n"
            f"Processed task: {task[:200]}\n\n"
            f"This agent is running as an HTTP API on localhost:8080.\n"
            f"In production, deploy to Fly.io, Railway, or any cloud platform."
        )

    return {"output": output, "success": True}


def main():
    host, port = "localhost", 8080
    server = HTTPServer((host, port), AgentHandler)
    print(f"🌐 API Agent running at http://{host}:{port}")
    print("   POST /run    — send a task")
    print("   GET  /health — health check")
    print("   Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
