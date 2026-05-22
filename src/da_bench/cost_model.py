"""Gas calculation, USD conversion, and DA pricing models."""

import math

from da_bench.config import (
    GAS_PER_BLOB,
    GAS_PER_CALLDATA_BYTE_NONZERO,
    GAS_PER_CALLDATA_BYTE_ZERO,
    MAX_BLOB_SIZE,
)


def calldata_gas(data: bytes) -> int:
    """Calculate total gas for posting data as Ethereum calldata."""
    zero = data.count(0)
    nonzero = len(data) - zero
    return zero * GAS_PER_CALLDATA_BYTE_ZERO + nonzero * GAS_PER_CALLDATA_BYTE_NONZERO


def gas_to_usd(gas: int, gas_price_gwei: float, eth_price_usd: float) -> float:
    """Convert gas units to USD cost."""
    return (gas * gas_price_gwei * 1e-9) * eth_price_usd


def calldata_cost_usd(data: bytes, gas_price_gwei: float, eth_price_usd: float) -> float:
    """Cost in USD to post data as Ethereum calldata."""
    gas = calldata_gas(data)
    return gas_to_usd(gas, gas_price_gwei, eth_price_usd)


def blob_count(data_size: int) -> int:
    """Number of blobs needed for a given data size."""
    return math.ceil(data_size / MAX_BLOB_SIZE)


def blob_cost_usd(data_size: int, blob_gas_price_gwei: float, eth_price_usd: float) -> float:
    """Cost in USD to post data via EIP-4844 blobs."""
    blobs = blob_count(data_size)
    total_gas = blobs * GAS_PER_BLOB
    return gas_to_usd(total_gas, blob_gas_price_gwei, eth_price_usd)


def external_da_cost_usd(data_size_bytes: int, cost_per_mb: float) -> float:
    """Cost in USD to post data to an external DA layer (Celestia/EigenDA model)."""
    size_mb = data_size_bytes / (1024 * 1024)
    return size_mb * cost_per_mb


# Fixed L1 gas overhead per batch submission (base tx + verification)
BATCH_SUBMISSION_GAS = 100_000


def batch_submission_cost_usd(gas_price_gwei: float, eth_price_usd: float) -> float:
    """Fixed cost in USD to submit one batch to L1, regardless of data size."""
    return gas_to_usd(BATCH_SUBMISSION_GAS, gas_price_gwei, eth_price_usd)


def format_usd(amount: float) -> str:
    """Format a USD amount for human-readable display."""
    if amount < 0.01:
        return f"${amount:.6f}"
    elif amount < 1.0:
        return f"${amount:.4f}"
    else:
        return f"${amount:.2f}"
