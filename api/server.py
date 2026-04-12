"""Backend FastAPI server for Agent YC Dashboard."""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.db import get_db
from core.eval_engine import load_challenges

app = FastAPI(title="Agent YC Dashboard API")

# Add CORS so vite dev server can hit this during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- API Routes ----

@app.get("/api/agents")
async def list_agents():
    """List all submitted agents."""
    db = get_db()
    agents = db.list_agents()
    # Augment with latest eval scores
    for a in agents:
        latest = db.get_latest_eval(a["id"])
        if latest:
            a["score_overall"] = latest.get("score_overall")
            a["score_reliability"] = latest.get("score_reliability")
            a["score_safety"] = latest.get("score_safety")
            a["score_cost"] = latest.get("score_cost")
            a["score_speed"] = latest.get("score_speed")
        else:
            a["score_overall"] = None
    return JSONResponse({"agents": agents})

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details."""
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return JSONResponse(agent)

@app.get("/api/agents/{agent_id}/evals")
async def get_evals(agent_id: str):
    """Get evaluations for an agent."""
    db = get_db()
    evals = db.get_evals(agent_id)
    return JSONResponse({"evals": evals})

@app.get("/api/challenges")
async def list_challenges():
    """List all available challenges."""
    from dataclasses import asdict
    challenges = load_challenges()
    return JSONResponse({"challenges": [asdict(c) for c in challenges]})

class CoachRequest(BaseModel):
    message: str

@app.post("/api/agents/{agent_id}/coach")
async def coach_chat(agent_id: str, req: CoachRequest):
    """Interact with the coach."""
    # (Simplified for now - in reality this would hit Ollama just like CLI)
    from cli.ollama import OllamaClient
    from core.coach import get_coaching
    from core.spec import AgentSpec
    import yaml
    
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    eval_record = db.get_latest_eval(agent_id)
    
    # Parse spec
    spec_data = yaml.safe_load(agent["spec_yaml"])
    spec = AgentSpec(**spec_data)
    
    # In a real app we'd construct a rich context here, but using base CLI function
    client = OllamaClient()
    
    try:
        class FakeEvalResult:
            def __init__(self, d):
                self.scorecard = type("Scorecard", (), d)()
                self.challenges = []
                self.agent_id = agent_id

        if eval_record:
            mock_res_data = {
                "overall": eval_record.get("score_overall", 0),
                "reliability": eval_record.get("score_reliability", 0),
                "safety": eval_record.get("score_safety", 0),
                "cost": eval_record.get("score_cost", 0),
                "speed": eval_record.get("score_speed", 0)
            }
            mock_res = FakeEvalResult(mock_res_data)
        else:
            mock_res = None
            
        feedback = get_coaching(spec, mock_res, req.message, client)
        return JSONResponse({"reply": feedback})
    except Exception as e:
        return JSONResponse({"reply": f"Error connecting to coach: {str(e)}"})

# ---- Static Files Mount ----
# If `dist` exists, serve it.
# This implements the Staff SWE monolothic deployment strategy.
DIST_DIR = Path(__file__).parent.parent / "dashboard" / "dist"

@app.get("/")
@app.get("/{catchall:path}")
async def serve_static(catchall: str = "", request: Request = None):
    # If the user accesses /api/* that doesn't exist, let it 404
    if catchall.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    # Serve static assets or fallback to index.html for React Router
    if DIST_DIR.exists():
        file_path = DIST_DIR / catchall
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
            
        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
            
    return JSONResponse(
        status_code=503, 
        content={"error": "Dashboard not built. Run `npm run build` in /dashboard."}
    )
