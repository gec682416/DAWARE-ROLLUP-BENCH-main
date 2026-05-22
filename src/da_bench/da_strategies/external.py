"""External DA layer — simulated Celestia/EigenDA cost model."""

import random
import time

from da_bench.batch import Batch
from da_bench.cost_model import external_da_cost_usd
from da_bench.da_strategies.base import DAResult


class ExternalDAStrategy:
    """Post batch data to an external DA layer (e.g., Celestia, EigenDA).

    External DA layers provide much lower cost per byte than Ethereum calldata
    (typically 100-1000x cheaper), but introduce additional trust assumptions:
    - Data availability depends on the external validator set, not L1.
    - L1 validators cannot independently verify DA.
    - Requires a DA bridge/attestation on L1 (simulated as extra latency).

    This implementation uses a cost model based on Celestia/EigenDA pricing
    (~$0.01-0.02 per MB) with configurable confirmation delay.

    Optional: DAS (Data Availability Sampling) mode adds a probabilistic
    verification step.
    """

    name = "external_da"

    def __init__(
        self,
        cost_per_mb: float = 0.02,
        confirmation_delay_ms: float = 150.0,
        das_sampling: bool = False,
    ):
        self.cost_per_mb = cost_per_mb
        self.confirmation_delay_ms = confirmation_delay_ms
        self.das_sampling = das_sampling

    def publish(self, batch: Batch) -> DAResult:
        cost_usd = external_da_cost_usd(batch.original_size, self.cost_per_mb)

        delay = self.confirmation_delay_ms
        if self.das_sampling:
            # DAS adds sampling round-trips; model as 1-3 extra light client queries
            delay += random.uniform(50, 200)

        trust = [
            "data_availability_depends_on_external_validators",
            "no_l1_enforcement_of_da",
        ]
        if self.das_sampling:
            trust.append("das_reduces_trust_under_honest_minority_assumption")

        return DAResult(
            strategy_name=self.name,
            batch_tx_count=batch.tx_count,
            original_size_bytes=batch.original_size,
            posted_size_bytes=batch.original_size,
            cost_wei=0,  # not applicable — external DA uses its own fee token
            cost_usd=cost_usd,
            confirmation_delay_ms=delay,
            trust_assumptions=trust,
            data_on_l1=False,
            compression_ratio=1.0,
        )

    def describe(self) -> str:
        base = (
            f"External DA (Celestia/EigenDA model): ${self.cost_per_mb:.3f}/MB, "
            f"~{self.confirmation_delay_ms:.0f}ms confirmation delay. "
            "Lower cost but data availability relies on external validators."
        )
        if self.das_sampling:
            base += " DAS sampling enabled (reduced trust assumptions)."
        return base
