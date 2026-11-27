from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import pandas as pd
from graph_engine.src.collusion_detector import detect_collusion_and_score, build_vendor_graph

app = FastAPI(title="E-NETRA Graph & Collusion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "active", "module": "Member 3 - Graph & Collusion Engine"}

@app.get("/api/v1/graph/risk-scores")
def get_all_graph_risks():
    """Returns 0-100 relational_graph_risk scores for all projects."""
    json_path = "graph_engine/data/graph_risk_scores.json"
    if not os.path.exists(json_path):
        detect_collusion_and_score()
    with open(json_path, "r") as f:
        return json.load(f)

@app.get("/api/v1/graph/project/{project_id}")
def get_project_collusion(project_id: str):
    """Returns detailed collusion flags and network nodes/edges for a specific project."""
    json_path = "graph_engine/data/graph_risk_scores.json"
    if not os.path.exists(json_path):
        detect_collusion_and_score()
    with open(json_path, "r") as f:
        scores = json.load(f)

    project_info = next((item for item in scores if item["project_id"] == project_id), None)
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    df = pd.read_csv("graph_engine/data/sample_vendors.csv")
    proj_df = df[df["project_id"] == project_id]
    G = build_vendor_graph(proj_df)

    nodes = [{"id": n, **attrs} for n, attrs in G.nodes(data=True)]
    edges = [{"source": u, "target": v, **attrs} for u, v, attrs in G.edges(data=True)]

    return {
        "summary": project_info,
        "network_graph": {"nodes": nodes, "edges": edges}
    }
