# Demo Agents

Example agents for testing `agent-yc` with different frameworks.

| Agent | Framework | Entrypoint |
|-------|-----------|------------|
| `python-agent/` | Plain Python | `./agent.py` |
| `langchain-agent/` | LangChain | `./agent.py` |
| `crewai-agent/` | CrewAI | `./agent.py` |
| `docker-agent/` | Docker | `docker://demo-agent:latest` |
| `api-agent/` | HTTP API | `http://localhost:8080/run` |

## Quick test

```bash
cd demo/python-agent
agent-yc screen
agent-yc eval
agent-yc coach

cd ../langchain-agent
pip install langchain langchain-community
agent-yc screen
agent-yc eval
```
