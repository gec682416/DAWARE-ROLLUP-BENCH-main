"""Tests for the simulation engine."""

import pytest

from da_bench.config import SimulationConfig
from da_bench.da_strategies import (
    CalldataStrategy,
    CompressedCalldataStrategy,
    ExternalDAStrategy,
)
from da_bench.simulator import run_comparison, run_experiment_matrix, run_simulation


class TestRunSimulation:
    def test_basic_run(self):
        cfg = SimulationConfig(tps=50, duration_seconds=2)
        strategy = CalldataStrategy()
        metrics = run_simulation(cfg, strategy, seed=42)
        assert metrics.total_tx > 0
        assert metrics.total_batches > 0
        assert metrics.total_cost_usd > 0
        assert metrics.strategy_name == "calldata"
        assert metrics.tps_target == 50

    def test_different_seeds_produce_different_data(self):
        cfg = SimulationConfig(tps=50, duration_seconds=1)
        strategy = CalldataStrategy()
        m1 = run_simulation(cfg, strategy, seed=42)
        m2 = run_simulation(cfg, strategy, seed=123)
        # Different seeds = different tx data = different costs
        assert m1.total_data_original_bytes != m2.total_data_original_bytes

    def test_all_strategies_run(self):
        cfg = SimulationConfig(tps=20, duration_seconds=1)
        for strat_cls in [CalldataStrategy, CompressedCalldataStrategy, ExternalDAStrategy]:
            strat = strat_cls()
            metrics = run_simulation(cfg, strat, seed=42)
            assert metrics.total_tx > 0
            assert metrics.avg_cost_per_tx_usd > 0

    def test_metrics_aggregates(self):
        cfg = SimulationConfig(tps=50, duration_seconds=1)
        metrics = run_simulation(cfg, CalldataStrategy(), seed=42)
        metrics.compute_aggregates()
        assert metrics.avg_cost_per_tx_usd > 0
        assert metrics.effective_throughput_tps > 0
        assert metrics.records is not None


class TestRunComparison:
    def test_comparison(self):
        cfg = SimulationConfig(tps=30, duration_seconds=1)
        strategies = [
            CalldataStrategy(),
            CompressedCalldataStrategy(),
            ExternalDAStrategy(),
        ]
        results = run_comparison(cfg, strategies, seed=42)
        assert len(results) == 3
        names = {r.strategy_name for r in results}
        assert names == {"calldata", "compressed_calldata", "external_da"}

    def test_comparison_same_seed_fair(self):
        """All strategies should see the same total tx count (shared seed)."""
        cfg = SimulationConfig(tps=30, duration_seconds=1)
        strategies = [CalldataStrategy(), CompressedCalldataStrategy()]
        results = run_comparison(cfg, strategies, seed=42)
        # Same workload → same number of transactions
        assert results[0].total_tx == results[1].total_tx


class TestRunExperimentMatrix:
    def test_matrix(self):
        cfg = SimulationConfig(duration_seconds=1)
        strategies = [CalldataStrategy(), ExternalDAStrategy()]
        results = run_experiment_matrix(
            tps_values=[10, 50],
            strategies=strategies,
            base_config=cfg,
            seeds=[42],
        )
        # 2 TPS × 2 strategies × 1 seed = 4 results
        assert len(results) == 4
        tps_targets = {r.tps_target for r in results}
        assert tps_targets == {10, 50}
