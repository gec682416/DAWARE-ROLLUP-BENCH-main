"""All tunable parameters for the DA benchmarking simulation."""

from dataclasses import dataclass, field

# --- Ethereum Gas Constants ---
GAS_PER_CALLDATA_BYTE_ZERO = 4
GAS_PER_CALLDATA_BYTE_NONZERO = 16
FIXED_TX_GAS_OVERHEAD = 21_000
GAS_PER_BLOB = 2 ** 17  # ~131,072 gas per blob (EIP-4844)
MAX_BLOB_SIZE = 131_072  # bytes (~128 KB per blob)
BLOB_TARGET_PER_BLOCK = 3

# --- DA Pricing Defaults ---
DEFAULT_GAS_PRICE_GWEI = 30.0
DEFAULT_ETH_PRICE_USD = 3000.0
CELESTIA_COST_USD_PER_MB = 0.02
EIGENDA_COST_USD_PER_MB = 0.015
EXTERNAL_DA_CONFIRMATION_DELAY_MS = 150

# --- Blob Pricing (EIP-4844) ---
# Blob gas is priced separately via a fee market. Historical ~1 Gwei range.
DEFAULT_BLOB_GAS_PRICE_GWEI = 1.0


@dataclass
class SimulationConfig:
    """Master configuration for a simulation run."""

    # Gas / economic
    gas_price_gwei: float = DEFAULT_GAS_PRICE_GWEI
    eth_price_usd: float = DEFAULT_ETH_PRICE_USD
    blob_gas_price_gwei: float = DEFAULT_BLOB_GAS_PRICE_GWEI

    # Transaction generation
    tps: int = 100
    duration_seconds: int = 120

    # Transaction size distribution
    pct_small: float = 0.70
    small_size_range: tuple = (100, 300)
    pct_medium: float = 0.20
    medium_size_range: tuple = (300, 1000)
    pct_large: float = 0.10
    large_size_range: tuple = (1000, 10_000)

    # Batching
    batch_max_bytes: int = 120_000  # target max batch size before posting
    batch_max_interval_ms: int = 2000  # force post if batch age exceeds this

    # External DA
    external_da_cost_per_mb: float = CELESTIA_COST_USD_PER_MB
    external_da_delay_ms: int = EXTERNAL_DA_CONFIRMATION_DELAY_MS

    # Output
    output_csv: str | None = None
