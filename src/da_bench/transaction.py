"""Transaction model and generator with realistic size distributions."""

import random
import time
from dataclasses import dataclass, field

from da_bench.config import SimulationConfig


@dataclass
class Transaction:
    id: int
    data: bytes
    size: int
    timestamp: float  # epoch seconds when the tx was created
    nonce: int = 0

    @property
    def zero_bytes(self) -> int:
        return self.data.count(0)

    @property
    def nonzero_bytes(self) -> int:
        return self.size - self.zero_bytes


class TransactionGenerator:
    """Generates synthetic transactions with a mixed size distribution.

    Simulates a realistic rollup workload:
    - ~70% small transfers (100-300 bytes)
    - ~20% medium interactions (300-1000 bytes)
    - ~10% large contract deployments (1-10 KB)
    """

    def __init__(self, config: SimulationConfig, seed: int = 42):
        self.config = config
        self.rng = random.Random(seed)
        self._counter = 0

    def _random_size(self) -> int:
        roll = self.rng.random()
        cfg = self.config
        if roll < cfg.pct_small:
            lo, hi = cfg.small_size_range
        elif roll < cfg.pct_small + cfg.pct_medium:
            lo, hi = cfg.medium_size_range
        else:
            lo, hi = cfg.large_size_range
        return self.rng.randint(lo, hi)

    def generate_one(self, timestamp: float | None = None) -> Transaction:
        if timestamp is None:
            timestamp = time.time()
        self._counter += 1
        size = self._random_size()
        data = bytes(self.rng.randint(0, 255) for _ in range(size))
        return Transaction(
            id=self._counter,
            data=data,
            size=size,
            timestamp=timestamp,
        )

    def generate_batch(self, count: int, start_time: float | None = None) -> list[Transaction]:
        if start_time is None:
            start_time = time.time()
        return [self.generate_one(start_time) for _ in range(count)]

    def generate_poisson_stream(self, tps: float, duration_seconds: float) -> list[Transaction]:
        """Generate transactions following a Poisson arrival process."""
        txs = []
        current_time = time.time()
        end_time = current_time + duration_seconds
        rate = 1.0 / tps  # average inter-arrival time

        while current_time < end_time:
            interval = self.rng.expovariate(1.0 / rate)
            current_time += interval
            if current_time >= end_time:
                break
            txs.append(self.generate_one(current_time))

        return txs

    def generate_uniform_stream(self, tps: float, duration_seconds: float) -> list[Transaction]:
        """Generate transactions at a uniform (deterministic) rate."""
        txs = []
        interval = 1.0 / tps
        start = time.time()
        for i in range(int(tps * duration_seconds)):
            ts = start + i * interval
            txs.append(self.generate_one(ts))
        return txs
