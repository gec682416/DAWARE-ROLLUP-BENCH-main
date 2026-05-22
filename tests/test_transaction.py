"""Tests for transaction generation and size distribution."""

from da_bench.config import SimulationConfig
from da_bench.transaction import Transaction, TransactionGenerator


class TestTransaction:
    def test_zero_bytes_count(self):
        tx = Transaction(id=1, data=b"\x00\x00\xff\x00", size=4, timestamp=0.0)
        assert tx.zero_bytes == 3
        assert tx.nonzero_bytes == 1

    def test_all_nonzero(self):
        tx = Transaction(id=1, data=b"\xff\xff\xff", size=3, timestamp=0.0)
        assert tx.zero_bytes == 0
        assert tx.nonzero_bytes == 3


class TestTransactionGenerator:
    def test_generate_one(self):
        cfg = SimulationConfig(tps=100, duration_seconds=1)
        gen = TransactionGenerator(cfg, seed=42)
        tx = gen.generate_one()
        assert tx.id == 1
        assert tx.size > 0
        assert tx.timestamp > 0

    def test_generate_batch(self):
        cfg = SimulationConfig(tps=100, duration_seconds=1)
        gen = TransactionGenerator(cfg, seed=42)
        txs = gen.generate_batch(50)
        assert len(txs) == 50
        assert all(isinstance(tx, Transaction) for tx in txs)

    def test_size_distribution(self):
        cfg = SimulationConfig(tps=100, duration_seconds=1)
        gen = TransactionGenerator(cfg, seed=42)
        txs = gen.generate_batch(1000)

        small = sum(1 for tx in txs if tx.size <= cfg.small_size_range[1])
        medium = sum(1 for tx in txs if cfg.medium_size_range[0] < tx.size <= cfg.medium_size_range[1])
        large = sum(1 for tx in txs if tx.size > cfg.large_size_range[0])

        # Allow ±10% tolerance
        assert 0.60 <= small / 1000 <= 0.80, f"small: {small/1000}"
        assert 0.10 <= medium / 1000 <= 0.30, f"medium: {medium/1000}"
        assert 0.05 <= large / 1000 <= 0.20, f"large: {large/1000}"

    def test_uniform_stream_rate(self):
        cfg = SimulationConfig(tps=100, duration_seconds=1)
        gen = TransactionGenerator(cfg, seed=42)
        txs = gen.generate_uniform_stream(100, 0.5)
        # Should get ~50 txs (100 tps * 0.5s)
        assert 45 <= len(txs) <= 55, f"got {len(txs)} txs"

    def test_poisson_stream(self):
        cfg = SimulationConfig()
        gen = TransactionGenerator(cfg, seed=42)
        txs = gen.generate_poisson_stream(100, 0.5)
        assert len(txs) > 0
        # Poisson is random, just check timestamps are ordered
        for i in range(1, len(txs)):
            assert txs[i].timestamp >= txs[i - 1].timestamp

    def test_generator_uses_seed_for_reproducibility(self):
        cfg = SimulationConfig()
        a = TransactionGenerator(cfg, seed=42)
        b = TransactionGenerator(cfg, seed=42)
        txs_a = a.generate_batch(100)
        txs_b = b.generate_batch(100)
        for tx_a, tx_b in zip(txs_a, txs_b):
            assert tx_a.size == tx_b.size
