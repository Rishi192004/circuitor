"""
FastAPI wrapper for the Circuitor validation engine.

Run with:
    uvicorn api_server:app --reload --port 8000
"""

import json
import os
import sys
import tempfile

# Ensure project root is on the path so `src.*` imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.main import run_pipeline

app = FastAPI(title="Circuitor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/run_pipeline")
async def validate_circuit(circuit_data: dict):
    """
    Validate a circuit. Accepts the full Circuit JSON schema, returns a PipelineResult.
    The engine currently reads from file paths, so we write a temp file, run, then clean up.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(circuit_data, f)
        result = run_pipeline(tmp_path)
        return result.to_dict()
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.get("/health")
async def health():
    return {"status": "ok", "service": "circuitor-api"}
