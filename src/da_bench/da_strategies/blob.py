"""Ethereum blob posting — EIP-4844 DA strategy."""

from da_bench.batch import Batch
from da_bench.cost_model import blob_cost_usd, blob_gas
from da_bench.da_strategies.base import DAResult


class BlobStrategy:
    """Post batch data to Ethereum blobs instead of calldata.

    EIP-4844 blobs use Ethereum consensus for data availability with a separate
    blob fee market. Compared with calldata, blobs are much cheaper per byte but
    are retained for a limited window rather than stored forever by execution
    clients.
    """

    name = "blob"

    def __init__(
        self,
        blob_gas_price_gwei: float = 1.0,
        eth_price_usd: float = 3000.0,
    ):
        self.blob_gas_price_gwei = blob_gas_price_gwei
        self.eth_price_usd = eth_price_usd

    def publish(self, batch: Batch) -> DAResult:
        gas = blob_gas(batch.original_size)
        cost_usd = blob_cost_usd(
            batch.original_size,
            self.blob_gas_price_gwei,
            self.eth_price_usd,
        )
        return DAResult(
            strategy_name=self.name,
            batch_tx_count=batch.tx_count,
            original_size_bytes=batch.original_size,
            posted_size_bytes=batch.original_size,
            cost_wei=int(gas * self.blob_gas_price_gwei * 1e9),
            cost_usd=cost_usd,
            confirmation_delay_ms=0.0,
            trust_assumptions=["ethereum_blob_retention_window"],
            data_on_l1=True,
            compression_ratio=1.0,
        )

    def describe(self) -> str:
        return (
            "Ethereum Blob DA (EIP-4844): batch data is posted as blobs under "
            "Ethereum consensus DA with a separate blob fee market. "
            f"Blob gas: {self.blob_gas_price_gwei} Gwei, ETH: ${self.eth_price_usd:,.0f}."
        )
