"""REST API routes for running DA benchmarking simulations."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from da_bench.config import SimulationConfig
from da_bench.da_strategies import (
    BlobStrategy,
    CalldataStrategy,
    CompressedCalldataStrategy,
    ExternalDAStrategy,
)
from da_bench.simulator import run_experiment_matrix

router = APIRouter(prefix="/api", tags=["simulation"])

AVAILABLE_STRATEGIES = {
    "calldata": CalldataStrategy,
    "blob": BlobStrategy,
    "compressed": CompressedCalldataStrategy,
    "external": ExternalDAStrategy,
}


class SweepRequest(BaseModel):
    gas_price_gwei: float = Field(default=30.0, ge=1.0, le=500.0, description="Gas price in Gwei")
    blob_gas_price_gwei: float = Field(default=1.0, ge=0.001, le=500.0, description="Blob gas price in Gwei")
    eth_price_usd: float = Field(default=3000.0, ge=100.0, le=20000.0, description="ETH price in USD")
    duration_seconds: int = Field(default=30, ge=5, le=600, description="Simulation duration per TPS point")
    batch_max_kb: int = Field(default=120, ge=16, le=1024, description="Max batch size in KB")
    batch_interval_ms: int = Field(default=2000, ge=100, le=30000, description="Max batch interval in ms")
    tps_min: int = Field(default=10, ge=1, le=1000)
    tps_max: int = Field(default=1000, ge=10, le=10000)
    tps_steps: int = Field(default=6, ge=2, le=12, description="Number of TPS points in sweep")
    strategies: list[str] = Field(
        default=["calldata", "blob", "compressed", "external"],
        description="DA strategies to compare"
    )


class MetricItem(BaseModel):
    strategy: str
    tps_target: int
    duration_s: float
    total_tx: int
    total_batches: int
    effective_duration_s: float
    wall_clock_runtime_s: float
    total_cost_usd: float
    avg_cost_per_tx_usd: float
    avg_latency_ms: float
    avg_batch_size_tx: float
    avg_compression_ratio: float
    effective_throughput_tps: float
    da_cost_percentage: float


class SweepResponse(BaseModel):
    results: list[MetricItem]
    request: SweepRequest


class StrategyInfo(BaseModel):
    name: str
    label: str
    description: str


@router.post("/sweep", response_model=SweepResponse)
def run_sweep(req: SweepRequest):
    """Run a TPS sweep across the selected DA strategies."""
    cfg = SimulationConfig(
        gas_price_gwei=req.gas_price_gwei,
        blob_gas_price_gwei=req.blob_gas_price_gwei,
        eth_price_usd=req.eth_price_usd,
        duration_seconds=req.duration_seconds,
        batch_max_bytes=req.batch_max_kb * 1024,
        batch_max_interval_ms=req.batch_interval_ms,
    )

    strategies = []
    for name in req.strategies:
        cls = AVAILABLE_STRATEGIES.get(name)
        if cls is None:
            continue
        if name == "external":
            strategies.append(cls(
                cost_per_mb=cfg.external_da_cost_per_mb,
                confirmation_delay_ms=cfg.external_da_delay_ms,
            ))
        elif name == "blob":
            strategies.append(cls(
                blob_gas_price_gwei=req.blob_gas_price_gwei,
                eth_price_usd=req.eth_price_usd,
            ))
        else:
            strategies.append(cls(
                gas_price_gwei=req.gas_price_gwei,
                eth_price_usd=req.eth_price_usd,
            ))

    tps_values = [
        int(req.tps_min + (req.tps_max - req.tps_min) * i / max(req.tps_steps - 1, 1))
        for i in range(req.tps_steps)
    ]
    tps_values = sorted(set(max(1, v) for v in tps_values))

    metrics = run_experiment_matrix(
        tps_values=tps_values,
        strategies=strategies,
        base_config=cfg,
        seeds=[42],
    )

    results = [MetricItem(**m.to_dict()) for m in metrics]
    return SweepResponse(results=results, request=req)


@router.get("/strategies", response_model=list[StrategyInfo])
def list_strategies():
    """Return available DA strategies with descriptions."""
    return [
        StrategyInfo(
            name="calldata",
            label="Calldata (Baseline)",
            description="Full L1 calldata posting. Maximum security, highest cost.",
        ),
        StrategyInfo(
            name="blob",
            label="Ethereum Blob DA",
            description="EIP-4844 blob posting. Ethereum DA security, separate blob fee market.",
        ),
        StrategyInfo(
            name="compressed",
            label="Compressed Calldata",
            description="zlib-compressed calldata. Same security, reduced data footprint.",
        ),
        StrategyInfo(
            name="external",
            label="External DA",
            description="Celestia/EigenDA model. Lowest cost, external validator trust.",
        ),
    ]


@router.get("/health")
def health():
    return {"status": "ok"}
