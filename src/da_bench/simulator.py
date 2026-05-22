"""Core discrete-event simulation engine for rollup DA benchmarking."""

import time

from da_bench.batch import BatchBuilder
from da_bench.config import SimulationConfig
from da_bench.da_strategies.base import DAStrategy
from da_bench.metrics import MetricsCollector, SimulationMetrics
from da_bench.transaction import TransactionGenerator


def run_simulation(
    config: SimulationConfig,
    strategy: DAStrategy,
    seed: int = 42,
) -> SimulationMetrics:
    """Run a single simulation with one DA strategy.

    1. Generate transactions at the target TPS
    2. Build batches (size/time constrained)
    3. Publish each batch through the DA strategy
    4. Collect and aggregate metrics
    """
    gen = TransactionGenerator(config, seed=seed)
    collector = MetricsCollector(
        strategy.name, config.tps,
        gas_price_gwei=config.gas_price_gwei,
        eth_price_usd=config.eth_price_usd,
        simulation_duration_seconds=config.duration_seconds,
    )

    # Generate transactions
    txs = gen.generate_uniform_stream(config.tps, config.duration_seconds)

    # Build batches
    builder = BatchBuilder(
        max_bytes=config.batch_max_bytes,
        max_interval_ms=config.batch_max_interval_ms,
    )
    batches = builder.build(txs)

    # Publish each batch through the DA strategy
    collector.start()
    first_tx_time = txs[0].timestamp if txs else 0.0
    latest_completion_time = first_tx_time + config.duration_seconds
    for batch in batches:
        result = strategy.publish(batch)
        latest_completion_time = max(
            latest_completion_time,
            batch.created_at + result.total_latency_ms / 1000,
        )
        # Compute average wait time for transactions in this batch
        wait_sum = sum(batch.created_at - tx.timestamp for tx in batch.transactions)
        avg_wait_ms = (wait_sum / batch.tx_count) * 1000 if batch.tx_count > 0 else 0.0
        collector.record(result, avg_wait_ms=avg_wait_ms)
    collector.stop()
    if txs:
        collector.set_effective_duration_seconds(latest_completion_time - first_tx_time)

    return collector.aggregate()


def run_comparison(
    config: SimulationConfig,
    strategies: list[DAStrategy],
    seed: int = 42,
) -> list[SimulationMetrics]:
    """Run the same workload through multiple DA strategies and compare results.

    Each strategy gets the same transaction stream (via fixed seed) to ensure
    a fair comparison.
    """
    results = []
    for strategy in strategies:
        metrics = run_simulation(config, strategy, seed=seed)
        results.append(metrics)
    return results


def run_experiment_matrix(
    tps_values: list[int],
    strategies: list[DAStrategy],
    base_config: SimulationConfig,
    seeds: list[int] | None = None,
) -> list[SimulationMetrics]:
    """Run a full matrix of TPS values x DA strategies.

    Returns a flat list of SimulationMetrics, one per (tps, strategy) combination.
    If seeds are provided, runs multiple replicates per combination.
    """
    if seeds is None:
        seeds = [42]

    all_results = []
    for tps in tps_values:
        config = SimulationConfig(
            gas_price_gwei=base_config.gas_price_gwei,
            eth_price_usd=base_config.eth_price_usd,
            blob_gas_price_gwei=base_config.blob_gas_price_gwei,
            tps=tps,
            duration_seconds=base_config.duration_seconds,
            pct_small=base_config.pct_small,
            small_size_range=base_config.small_size_range,
            pct_medium=base_config.pct_medium,
            medium_size_range=base_config.medium_size_range,
            pct_large=base_config.pct_large,
            large_size_range=base_config.large_size_range,
            batch_max_bytes=base_config.batch_max_bytes,
            batch_max_interval_ms=base_config.batch_max_interval_ms,
            external_da_cost_per_mb=base_config.external_da_cost_per_mb,
            external_da_delay_ms=base_config.external_da_delay_ms,
        )
        for seed in seeds:
            batch_results = run_comparison(config, strategies, seed=seed)
            all_results.extend(batch_results)

    return all_results
