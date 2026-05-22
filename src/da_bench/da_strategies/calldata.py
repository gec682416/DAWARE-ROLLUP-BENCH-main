"""Ethereum calldata posting — the baseline DA strategy."""

from da_bench.batch import Batch
from da_bench.cost_model import calldata_cost_usd, calldata_gas
from da_bench.da_strategies.base import DAResult


class CalldataStrategy:
    """Post full batch data as Ethereum calldata.

    This is the baseline approach used by most rollups today:
    all transaction data is published directly in calldata on L1.
    Every L1 node can verify data availability.

    Trust assumptions: none beyond Ethereum L1 security.
    """

    name = "calldata"

    def __init__(self, gas_price_gwei: float = 30.0, eth_price_usd: float = 3000.0):
        self.gas_price_gwei = gas_price_gwei
        self.eth_price_usd = eth_price_usd

    def publish(self, batch: Batch) -> DAResult:
        gas = calldata_gas(batch.raw_data)
        cost_usd = calldata_cost_usd(
            batch.raw_data,
            self.gas_price_gwei,
            self.eth_price_usd,
        )
        return DAResult(
            strategy_name=self.name,
            batch_tx_count=batch.tx_count,
            original_size_bytes=batch.original_size,
            posted_size_bytes=batch.original_size,
            cost_wei=int(gas * self.gas_price_gwei * 1e9),
            cost_usd=cost_usd,
            confirmation_delay_ms=0.0,  # data is on L1, no extra confirmation
            trust_assumptions=[],
            data_on_l1=True,
            compression_ratio=1.0,
        )

    def describe(self) -> str:
        return (
            "Ethereum Calldata (baseline): all tx data posted as-is to L1 calldata. "
            "Full L1 security, no additional trust assumptions. "
            f"Calldata gas: {self.gas_price_gwei} Gwei, ETH: ${self.eth_price_usd:,.0f}."
        )
