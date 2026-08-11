# -*- coding: utf-8 -*-
"""
ConstructIQ — FastAPI Server for Hydro Power Plant Estimation & Monitoring.
Exposes REST endpoints for the 4-Model Hydro ML & ChromaDB RAG Agent system.
Multi-threaded parallel execution with automatic database project registration.
"""

import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from db.database import create_tables, get_db, SessionLocal
from agents.estimation.orchestrator import run_estimation_pipeline
from agents.monitoring.agents import (
    status_agent, delay_agent, rootcause_agent,
    material_availability_agent, procurement_risk_agent,
)
from rag.vector_store import get_vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Pre-warming ConstructIQ Vector Engine & Database...")
    create_tables()
    get_vector_store()
    print("[INFO] ConstructIQ Hydro Power API Online & Ready.")
    yield
    print("[INFO] ConstructIQ API Shutdown.")

app = FastAPI(
    title="ConstructIQ — Hydro Power Estimation & Monitoring API",
    description="4-Model ML & ChromaDB RAG Agent System for Hydroelectric Power Projects",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "ConstructIQ Hydro Power Estimation & Monitoring API",
        "documentation": "/docs"
    }

class HydroEstimationRequest(BaseModel):
    capacity_mw: float = Field(250.0, gt=0, description="Installed Capacity in MW")
    number_of_units: int = Field(4, ge=1, description="Number of turbine-generator units")
    project_category: Optional[str] = Field("Large Hydro", description="Large, Medium, Small, Mini, Micro, Pico Hydro")
    gross_head_m: Optional[float] = Field(180.0, description="Gross Head in meters")
    net_head_m: Optional[float] = Field(171.0, description="Net Head in meters")
    design_flow_m3s: Optional[float] = Field(162.5, description="Design flow rate in m3/s")
    dam_height_m: Optional[float] = Field(65.0, description="Dam / Weir height in meters")
    dam_length_m: Optional[float] = Field(260.0, description="Dam / Weir crest length in meters")
    tunnel_length_km: Optional[float] = Field(8.5, description="Headrace Tunnel length in km")
    tunnel_diameter_m: Optional[float] = Field(6.5, description="Tunnel finished diameter in meters")
    penstock_length_m: Optional[float] = Field(450.0, description="Penstock pipe length in meters")
    penstock_diameter_m: Optional[float] = Field(3.8, description="Penstock diameter in meters")
    reservoir_volume_mcm: Optional[float] = Field(120.0, description="Reservoir volume in MCM")
    catchment_area_km2: Optional[float] = Field(1800.0, description="Catchment area in sq km")
    elevation_m: Optional[float] = Field(1400.0, description="Plant elevation above MSL in meters")
    state: str = Field("Uttarakhand", description="Indian State location")
    project_type: str = Field("run-of-river", description="run-of-river, storage, or pumped")
    turbine_type: Optional[str] = Field("Francis", description="Francis, Pelton, Kaplan, or Cross-flow")
    dam_type: Optional[str] = Field("Concrete Gravity", description="Concrete Gravity, Barrage/Weir, Rockfill, etc.")
    powerhouse_type: Optional[str] = Field("Underground", description="Underground, Surface, or Semi-underground")
    terrain_type: Optional[str] = Field("Mountainous", description="Mountainous, Hilly, Plain, or Gorge")
    terrain_complexity_score: Optional[float] = Field(3.5, ge=1.0, le=5.0)
    civil_complexity_score: Optional[float] = Field(3.8, ge=1.0, le=5.0)
    hydro_complexity_score: Optional[float] = Field(3.6, ge=1.0, le=5.0)


@app.post("/api/estimate")
def estimate_project(req: HydroEstimationRequest, db: Session = Depends(get_db)):
    """Run full 4-model estimation pipeline and automatically register project in database."""
    try:
        res = run_estimation_pipeline(req.model_dump())
        proj_id = f"HP-EST-{str(uuid.uuid4())[:6].upper()}"
        res["project_id"] = proj_id

        # Persist newly estimated project into database
        db.execute(text("""
            INSERT OR REPLACE INTO project_master 
            (project_id, project_name, project_category, project_type, state, capacity_mw, number_of_units, unit_capacity_mw, commissioning_year, net_head_m, annual_generation_gwh, project_cost_cr, primary_source)
            VALUES (:pid, :pname, :cat, :ptype, :state, :cap, :units, :ucap, 2026, :head, :gen, :cost, 'ConstructIQ AI Pipeline')
        """), {
            "pid": proj_id,
            "pname": f"Custom {req.capacity_mw} MW {req.project_category or 'Hydro'} Project",
            "cat": req.project_category or "Large Hydro",
            "ptype": req.project_type,
            "state": req.state,
            "cap": req.capacity_mw,
            "units": req.number_of_units,
            "ucap": round(req.capacity_mw / max(req.number_of_units, 1), 2),
            "head": req.net_head_m or 100.0,
            "gen": res.get("model_2_generation", {}).get("annual_generation_gwh", 100.0),
            "cost": res.get("model_3_cost", {}).get("total_project_cost_cr", 1000.0),
        })
        db.commit()
        return res
    except Exception as e:
        print(f"[WARN] Estimation database registration: {e}")
        return run_estimation_pipeline(req.model_dump())


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ConstructIQ Hydro Power API v1.0", "version": "1.0.0"}


@app.get("/api/projects")
def list_projects(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM project_master ORDER BY project_id DESC LIMIT :lim"),
        {"lim": limit}
    ).fetchall()
    return {"success": True, "data": [dict(r._mapping) for r in rows]}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM project_master WHERE project_id=:pid"),
        {"pid": project_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "data": dict(row._mapping)}


@app.get("/api/projects/{project_id}/materials")
def get_project_materials(project_id: str, db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM project_materials WHERE project_id=:pid"),
        {"pid": project_id}
    ).fetchall()
    return {"success": True, "data": [dict(r._mapping) for r in rows]}


# Monitoring Agent Endpoints
@app.get("/api/monitor/{project_id}/status")
def monitor_status(project_id: str, db: Session = Depends(get_db)):
    try:
        return {"success": True, "data": status_agent(db, project_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/{project_id}/delays")
def monitor_delays(project_id: str, db: Session = Depends(get_db)):
    try:
        return {"success": True, "data": delay_agent(db, project_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/{project_id}/rootcause")
def monitor_rootcause(project_id: str, db: Session = Depends(get_db)):
    try:
        return {"success": True, "data": rootcause_agent(db, project_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/{project_id}/materials")
def monitor_materials(project_id: str, db: Session = Depends(get_db)):
    try:
        return {"success": True, "data": material_availability_agent(db, project_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/{project_id}/procurement")
def monitor_procurement(project_id: str, db: Session = Depends(get_db)):
    try:
        return {"success": True, "data": procurement_risk_agent(db, project_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Conversational Hydro Specialist AI Chatbot endpoint running in worker threadpool."""
    try:
        from agents.chatbot import generate_chat_response
        msgs = [m.model_dump() for m in req.messages]
        reply = generate_chat_response(msgs)
        return {"success": True, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
