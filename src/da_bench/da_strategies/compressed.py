"""Compressed calldata posting — reduces L1 footprint via zlib compression."""

import time

from da_bench.batch import Batch, BatchBuilder
from da_bench.cost_model import calldata_cost_usd, calldata_gas
from da_bench.da_strategies.base import DAResult


class CompressedCalldataStrategy:
    """Compress batch data before posting as Ethereum calldata.

    The sequencer compresses the serialized batch data with zlib,
    then posts the compressed blob to L1 calldata. Verifiers decompress
    before validating.

    Trust assumptions: same as calldata baseline — all data is on L1.
    The only difference is a small CPU overhead for compression/decompression.
    """

    name = "compressed_calldata"

    def __init__(self, gas_price_gwei: float = 30.0, eth_price_usd: float = 3000.0):
        self.gas_price_gwei = gas_price_gwei
        self.eth_price_usd = eth_price_usd

    def publish(self, batch: Batch) -> DAResult:
        t0 = time.perf_counter()
        batch = BatchBuilder.compress(batch)
        compression_time_ms = (time.perf_counter() - t0) * 1000

        assert batch.compressed_data is not None
        gas = calldata_gas(batch.compressed_data)
        cost_usd = calldata_cost_usd(
            batch.compressed_data,
            self.gas_price_gwei,
            self.eth_price_usd,
        )
        return DAResult(
            strategy_name=self.name,
            batch_tx_count=batch.tx_count,
            original_size_bytes=batch.original_size,
            posted_size_bytes=batch.posted_size,
            cost_wei=int(gas * self.gas_price_gwei * 1e9),
            cost_usd=cost_usd,
            confirmation_delay_ms=0.0,
            compression_time_ms=compression_time_ms,
            trust_assumptions=[],
            data_on_l1=True,
            compression_ratio=batch.compression_ratio,
        )

    def describe(self) -> str:
        return (
            "Compressed Calldata: batch data is zlib-compressed before L1 posting. "
            "Same L1 security as baseline, with reduced data footprint. "
            f"Calldata gas: {self.gas_price_gwei} Gwei, ETH: ${self.eth_price_usd:,.0f}."
        )
