"""Predefined experiment scenarios for DA benchmarking."""

from da_bench.config import SimulationConfig

# Standard TPS sweep for bottleneck analysis
TPS_SWEEP = [10, 50, 100, 200, 500, 1000]

# Focused TPS range for detailed analysis
TPS_FINE = [10, 25, 50, 75, 100, 150, 200, 300, 500]

# Quick smoke-test configuration
TPS_QUICK = [10, 100, 500]


def default_config(**overrides) -> SimulationConfig:
    """Create a SimulationConfig with sensible defaults, optionally overridden."""
    params = dict(
        gas_price_gwei=30.0,
        eth_price_usd=3000.0,
        tps=100,
        duration_seconds=120,
        batch_max_bytes=120_000,
        batch_max_interval_ms=2000,
    )
    params.update(overrides)
    return SimulationConfig(**params)


# Pre-built experiment scenarios

SCENARIO_BASELINE = {
    "description": "Baseline comparison across TPS sweep with 3 DA strategies",
    "config": default_config(duration_seconds=120),
    "tps_values": TPS_SWEEP,
    "seeds": [42, 123, 456],  # 3 replicates
}

SCENARIO_HIGH_GAS = {
    "description": "High gas price scenario (100 Gwei) — stress test for L1 DA costs",
    "config": default_config(gas_price_gwei=100.0, duration_seconds=120),
    "tps_values": TPS_SWEEP,
    "seeds": [42],
}

SCENARIO_LOW_GAS = {
    "description": "Low gas price scenario (10 Gwei) — favorable L1 conditions",
    "config": default_config(gas_price_gwei=10.0, duration_seconds=120),
    "tps_values": TPS_SWEEP,
    "seeds": [42],
}

SCENARIO_QUICK = {
    "description": "Quick smoke test (30s per run)",
    "config": default_config(duration_seconds=30),
    "tps_values": TPS_QUICK,
    "seeds": [42],
}

SCENARIO_LARGE_BATCHES = {
    "description": "Large batch sizes (500 KB max) to test batching efficiency",
    "config": default_config(duration_seconds=120, batch_max_bytes=500_000, batch_max_interval_ms=5000),
    "tps_values": TPS_SWEEP,
    "seeds": [42],
}

ALL_SCENARIOS = {
    "baseline": SCENARIO_BASELINE,
    "high_gas": SCENARIO_HIGH_GAS,
    "low_gas": SCENARIO_LOW_GAS,
    "quick": SCENARIO_QUICK,
    "large_batches": SCENARIO_LARGE_BATCHES,
}
