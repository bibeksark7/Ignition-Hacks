"""Standalone FastAPI service so Workstream 03/04 can integration-test against
this engine directly, without the vision pipeline running.

Run with: uvicorn pricing.api:app --reload --port 8001
"""

from fastapi import FastAPI, HTTPException

from .engine import analyze

app = FastAPI(title="Sightline Pricing Engine")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/price")
def price(contract_a: dict) -> dict:
    coverage_amount = contract_a.pop("coverage_amount", None)
    try:
        return analyze(contract_a, coverage_amount=coverage_amount)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
