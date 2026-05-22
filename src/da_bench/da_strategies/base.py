"""Abstract base for all DA strategies."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class DAResult:
    """Result of publishing a batch to a DA layer."""

    strategy_name: str
    batch_tx_count: int
    original_size_bytes: int
    posted_size_bytes: int

    cost_wei: int
    cost_usd: float

    # Latency components (milliseconds)
    confirmation_delay_ms: float
    compression_time_ms: float = 0.0

    # Trust / security characterization
    trust_assumptions: list[str] = field(default_factory=list)
    data_on_l1: bool = True
    compression_ratio: float = 1.0

    @property
    def cost_per_tx_usd(self) -> float:
        if self.batch_tx_count == 0:
            return 0.0
        return self.cost_usd / self.batch_tx_count

    @property
    def total_latency_ms(self) -> float:
        return self.confirmation_delay_ms + self.compression_time_ms


class DAStrategy(Protocol):
    """Protocol for a Data Availability publication strategy."""

    name: str

    def publish(self, batch: "Batch") -> DAResult:  # noqa: F821
        """Post a batch to the DA layer and return the result."""
        ...

    def describe(self) -> str:
        """Human-readable description of this strategy."""
        ...
