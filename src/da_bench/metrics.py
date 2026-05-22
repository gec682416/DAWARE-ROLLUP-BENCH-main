"""Metrics collector: aggregates and exports simulation results."""

import csv
import json
from dataclasses import dataclass, field

from da_bench.da_strategies.base import DAResult


@dataclass
class SimulationMetrics:
    """Aggregated metrics from a single simulation run."""

    strategy_name: str
    tps_target: int
    duration_seconds: float

    total_tx: int
    total_batches: int
    total_cost_usd: float
    total_data_posted_bytes: int
    total_data_original_bytes: int

    # Extra fields for dynamic metrics
    total_batch_submission_cost_usd: float = 0.0
    total_data_posting_cost_usd: float = 0.0
    total_wait_time_ms: float = 0.0
    effective_duration_seconds: float = 0.0
    wall_clock_runtime_seconds: float = 0.0

    avg_cost_per_tx_usd: float = 0.0
    avg_latency_ms: float = 0.0
    avg_batch_size_tx: float = 0.0
    avg_compression_ratio: float = 1.0
    effective_throughput_tps: float = 0.0
    da_cost_percentage: float = 0.0

    # Time-series records
    records: list[dict] = field(default_factory=list)

    def compute_aggregates(self):
        if self.total_tx > 0:
            self.avg_cost_per_tx_usd = self.total_cost_usd / self.total_tx
            self.avg_batch_size_tx = self.total_tx / max(self.total_batches, 1)
        if self.records:
            self.avg_latency_ms = sum(
                r["total_latency_ms"] for r in self.records
            ) / len(self.records)
            self.avg_compression_ratio = sum(
                r["compression_ratio"] for r in self.records
            ) / len(self.records)
        throughput_window = self.effective_duration_seconds or self.duration_seconds
        if throughput_window > 0:
            self.effective_throughput_tps = self.total_tx / throughput_window

        # DA cost as % of total rollup cost
        # total_cost_usd = data posting cost + batch submission overhead
        if self.total_cost_usd > 0 and self.total_data_posting_cost_usd > 0:
            self.da_cost_percentage = (self.total_data_posting_cost_usd / self.total_cost_usd) * 100

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy_name,
            "tps_target": self.tps_target,
            "duration_s": self.duration_seconds,
            "total_tx": self.total_tx,
            "total_batches": self.total_batches,
            "effective_duration_s": round(self.effective_duration_seconds, 4),
            "wall_clock_runtime_s": round(self.wall_clock_runtime_seconds, 4),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "avg_cost_per_tx_usd": round(self.avg_cost_per_tx_usd, 6),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "avg_batch_size_tx": round(self.avg_batch_size_tx, 1),
            "avg_compression_ratio": round(self.avg_compression_ratio, 4),
            "effective_throughput_tps": round(self.effective_throughput_tps, 1),
            "da_cost_percentage": round(self.da_cost_percentage, 1),
        }

    def save_csv(self, path: str):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.records[0].keys())
            writer.writeheader()
            writer.writerows(self.records)

    def save_summary_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class MetricsCollector:
    """Collects DAResult records and produces aggregated SimulationMetrics."""

    def __init__(self, strategy_name: str, tps_target: int,
                 gas_price_gwei: float = 30.0, eth_price_usd: float = 3000.0,
                 simulation_duration_seconds: float = 0.0):
        self.strategy_name = strategy_name
        self.tps_target = tps_target
        self._gas_price_gwei = gas_price_gwei
        self._eth_price_usd = eth_price_usd
        self._simulation_duration_seconds = simulation_duration_seconds
        self._effective_duration_seconds = simulation_duration_seconds
        self._records: list[DAResult] = []
        self._total_wait_time_ms = 0.0
        self._total_tx_for_wait = 0
        self._batch_submission_costs: list[float] = []
        self._start_time: float | None = None
        self._end_time: float | None = None

    def start(self):
        import time
        self._start_time = time.time()

    def stop(self):
        import time
        self._end_time = time.time()

    def set_effective_duration_seconds(self, duration_seconds: float):
        self._effective_duration_seconds = max(duration_seconds, 0.0)

    def record(self, result: DAResult, avg_wait_ms: float = 0.0):
        self._records.append((result, avg_wait_ms))
        self._total_wait_time_ms += avg_wait_ms * result.batch_tx_count
        self._total_tx_for_wait += result.batch_tx_count

        from da_bench.cost_model import batch_submission_cost_usd
        self._batch_submission_costs.append(
            batch_submission_cost_usd(self._gas_price_gwei, self._eth_price_usd)
        )

    @property
    def duration_seconds(self) -> float:
        return self._simulation_duration_seconds

    @property
    def wall_clock_runtime_seconds(self) -> float:
        if self._start_time and self._end_time:
            return self._end_time - self._start_time
        return 0.0

    def aggregate(self) -> SimulationMetrics:
        d_results = [r for r, _ in self._records]
        wait_times = [w for _, w in self._records]
        total_tx = sum(r.batch_tx_count for r in d_results)
        total_data_cost = sum(r.cost_usd for r in d_results)
        total_batch_overhead = sum(self._batch_submission_costs)
        total_cost = total_data_cost + total_batch_overhead
        total_posted = sum(r.posted_size_bytes for r in d_results)
        total_original = sum(r.original_size_bytes for r in d_results)

        records_data = [
            {
                "batch_idx": i,
                "tx_count": r.batch_tx_count,
                "original_size_bytes": r.original_size_bytes,
                "posted_size_bytes": r.posted_size_bytes,
                "cost_usd": r.cost_usd,
                "confirmation_delay_ms": r.confirmation_delay_ms,
                "compression_time_ms": r.compression_time_ms,
                "total_latency_ms": wait_times[i] + r.total_latency_ms,
                "compression_ratio": r.compression_ratio,
                "data_on_l1": r.data_on_l1,
            }
            for i, r in enumerate(d_results)
        ]

        m = SimulationMetrics(
            strategy_name=self.strategy_name,
            tps_target=self.tps_target,
            duration_seconds=self.duration_seconds,
            total_tx=total_tx,
            total_batches=len(d_results),
            total_cost_usd=total_cost,
            total_data_posted_bytes=total_posted,
            total_data_original_bytes=total_original,
            total_batch_submission_cost_usd=total_batch_overhead,
            total_data_posting_cost_usd=total_data_cost,
            total_wait_time_ms=self._total_wait_time_ms,
            effective_duration_seconds=self._effective_duration_seconds,
            wall_clock_runtime_seconds=self.wall_clock_runtime_seconds,
            records=records_data,
        )
        m.compute_aggregates()
        return m
