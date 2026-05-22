"""FastAPI application entry point for the DA benchmarking dashboard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.simulation import router as simulation_router

app = FastAPI(
    title="DA-Rollup Benchmark API",
    description="REST API for the Data Availability-Aware Rollup Benchmarking Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router)


@app.get("/")
def root():
    return {
        "service": "DA-Rollup Benchmark API",
        "docs": "/docs",
        "endpoints": {
            "sweep": "/api/sweep",
            "strategies": "/api/strategies",
            "health": "/api/health",
        },
    }
