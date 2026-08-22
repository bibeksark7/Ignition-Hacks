"""Standalone FastAPI service so Workstream 03/04 can integration-test against
this engine directly, without the vision pipeline running.

Run with: uvicorn pricing.api:app --reload --port 8001
Interactive docs at: http://localhost:8001/docs
"""

import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine import analyze
from .fixtures import ALL_FIXTURES
from .generate_fixtures import OUTPUT_DIR

app = FastAPI(title="Sightline Pricing Engine")

# Permissive on purpose: this is a local hackathon dev tool, not a production
# deployment, and it holds no secrets — the friction of a real CORS policy
# isn't worth it for a 36-hour build.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContractARequest(BaseModel):
    lat: float
    lon: float
    roof_area_m2: float = Field(gt=0)
    roof_material: str
    roof_damage_score: float = Field(ge=0, le=1)
    canopy_overlap_pct: float = Field(ge=0, le=100)
    canopy_within_5m_pct: float = Field(ge=0, le=100)
    impervious_pct: float = Field(ge=0, le=100)
    lot_area_m2: float = Field(gt=0)
    nearest_structure_m: float = Field(ge=0)
    imagery_date: Optional[str] = None
    zoom: Optional[int] = None
    confidence: Optional[float] = None
    estimated_value: Optional[float] = None
    value_basis: Optional[str] = None
    value_confidence: Optional[str] = None
    coverage_amount: Optional[float] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/price")
def price(contract_a: ContractARequest) -> dict:
    data = contract_a.model_dump(exclude_none=True)
    coverage_amount = data.pop("coverage_amount", None)
    try:
        return analyze(data, coverage_amount=coverage_amount)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/demo")
def list_demo_fixtures() -> dict:
    return {"fixtures": list(ALL_FIXTURES.keys())}


@app.get("/demo/{name}")
def get_demo_fixture(name: str) -> dict:
    path = os.path.join(OUTPUT_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"No cached fixture named '{name}'. See GET /demo for options.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
