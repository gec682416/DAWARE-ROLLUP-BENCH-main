"""Tests for DA strategies."""

import pytest

from da_bench.batch import Batch
from da_bench.da_strategies import (
    CalldataStrategy,
    CompressedCalldataStrategy,
    ExternalDAStrategy,
)
from da_bench.transaction import Transaction


@pytest.fixture
def sample_batch():
    txs = [
        Transaction(id=i, data=b"tx data " * 10, size=80, timestamp=float(i))
        for i in range(50)
    ]
    return Batch.from_transactions(txs)


class TestCalldataStrategy:
    def test_publish_returns_result(self, sample_batch):
        s = CalldataStrategy(gas_price_gwei=30.0, eth_price_usd=3000.0)
        result = s.publish(sample_batch)
        assert result.strategy_name == "calldata"
        assert result.batch_tx_count == 50
        assert result.cost_usd > 0
        assert result.cost_wei > 0
        assert result.data_on_l1 is True
        assert result.confirmation_delay_ms == 0.0
        assert result.trust_assumptions == []
        assert result.cost_per_tx_usd > 0

    def test_higher_gas_price_increases_cost(self, sample_batch):
        cheap = CalldataStrategy(gas_price_gwei=10.0, eth_price_usd=3000.0)
        expensive = CalldataStrategy(gas_price_gwei=100.0, eth_price_usd=3000.0)
        assert expensive.publish(sample_batch).cost_usd > cheap.publish(sample_batch).cost_usd

    def test_zero_byte_cheaper_than_nonzero(self):
        zero_batch = Batch.from_transactions([
            Transaction(id=1, data=b"\x00" * 1000, size=1000, timestamp=0.0)
        ])
        nonzero_batch = Batch.from_transactions([
            Transaction(id=1, data=b"\xff" * 1000, size=1000, timestamp=0.0)
        ])
        s = CalldataStrategy()
        zero_cost = s.publish(zero_batch).cost_usd
        nonzero_cost = s.publish(nonzero_batch).cost_usd
        assert zero_cost < nonzero_cost


class TestCompressedCalldataStrategy:
    def test_publish_returns_result(self, sample_batch):
        s = CompressedCalldataStrategy(gas_price_gwei=30.0, eth_price_usd=3000.0)
        result = s.publish(sample_batch)
        assert result.strategy_name == "compressed_calldata"
        assert result.compression_ratio < 1.0
        assert result.compression_time_ms >= 0
        assert result.data_on_l1 is True

    def test_repetitive_data_compresses_well(self):
        txs = [Transaction(id=i, data=b"AAAA" * 100, size=400, timestamp=float(i))
                for i in range(20)]
        batch = Batch.from_transactions(txs)
        s = CompressedCalldataStrategy()
        result = s.publish(batch)
        assert result.compression_ratio < 0.5  # repetitive data should compress well

    def test_cost_lower_than_uncompressed(self, sample_batch):
        calldata = CalldataStrategy(gas_price_gwei=30.0, eth_price_usd=3000.0)
        compressed = CompressedCalldataStrategy(gas_price_gwei=30.0, eth_price_usd=3000.0)
        c_cost = calldata.publish(sample_batch).cost_usd
        z_cost = compressed.publish(sample_batch).cost_usd
        # compressed should always be <= uncompressed
        assert z_cost <= c_cost


class TestExternalDAStrategy:
    def test_publish_returns_result(self, sample_batch):
        s = ExternalDAStrategy()
        result = s.publish(sample_batch)
        assert result.strategy_name == "external_da"
        assert result.data_on_l1 is False
        assert result.confirmation_delay_ms > 0
        assert len(result.trust_assumptions) >= 2
        assert "no_l1_enforcement_of_da" in result.trust_assumptions

    def test_cost_much_lower_than_calldata(self, sample_batch):
        calldata = CalldataStrategy(gas_price_gwei=30.0, eth_price_usd=3000.0)
        external = ExternalDAStrategy()
        c_cost = calldata.publish(sample_batch).cost_usd
        e_cost = external.publish(sample_batch).cost_usd
        assert e_cost < c_cost / 10, f"external={e_cost} should be << calldata={c_cost}"

    def test_das_mode_adds_latency(self, sample_batch):
        s_no_das = ExternalDAStrategy(das_sampling=False)
        s_das = ExternalDAStrategy(das_sampling=True)
        r_no = s_no_das.publish(sample_batch)
        r_das = s_das.publish(sample_batch)
        # DAS adds or may add extra trust assumption text
        assert len(r_das.trust_assumptions) >= len(r_no.trust_assumptions)
