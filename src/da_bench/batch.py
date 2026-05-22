"""Batch builder: aggregates transactions, builds merkle tree, applies compression."""

import hashlib
import struct
import zlib
from dataclasses import dataclass, field

from da_bench.transaction import Transaction


def _hash_pair(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(left + right).digest()


def build_merkle_root(leaves: list[bytes]) -> bytes:
    """Build a Merkle tree from leaf hashes and return the root."""
    if not leaves:
        return hashlib.sha256(b"").digest()
    if len(leaves) == 1:
        return hashlib.sha256(leaves[0]).digest()

    level = [hashlib.sha256(leaf).digest() for leaf in leaves]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])  # duplicate last if odd
        level = [_hash_pair(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def serialize_transactions(txs: list[Transaction]) -> bytes:
    """Serialize a list of transactions into a deterministic byte string.

    Format: for each tx: [4-byte id][8-byte timestamp double][4-byte size][raw data]
    """
    buf = bytearray()
    for tx in txs:
        buf.extend(struct.pack(">I", tx.id))
        buf.extend(struct.pack(">d", tx.timestamp))
        buf.extend(struct.pack(">I", tx.size))
        buf.extend(tx.data)
    return bytes(buf)


@dataclass
class Batch:
    """A batch of transactions ready for DA posting."""

    transactions: list[Transaction]
    raw_data: bytes
    merkle_root: bytes
    created_at: float  # epoch timestamp

    # Compression results (populated by BatchBuilder)
    compressed: bool = False
    compressed_data: bytes | None = None
    compression_ratio: float = 1.0

    @property
    def tx_count(self) -> int:
        return len(self.transactions)

    @property
    def original_size(self) -> int:
        return len(self.raw_data)

    @property
    def posted_size(self) -> int:
        return len(self.compressed_data) if self.compressed else self.original_size

    @classmethod
    def from_transactions(cls, txs: list[Transaction]) -> "Batch":
        raw = serialize_transactions(txs)
        leaves = [tx.data for tx in txs]
        root = build_merkle_root(leaves)
        return cls(
            transactions=txs,
            raw_data=raw,
            merkle_root=root,
            created_at=txs[-1].timestamp if txs else 0.0,
        )


class BatchBuilder:
    """Builds batches from a transaction stream, optionally applying compression."""

    def __init__(self, max_bytes: int = 120_000, max_interval_ms: int = 2000):
        self.max_bytes = max_bytes
        self.max_interval_ms = max_interval_ms

    def build(self, txs: list[Transaction]) -> list[Batch]:
        """Split transactions into batches based on size and time constraints."""
        if not txs:
            return []

        batches = []
        current: list[Transaction] = []
        current_size = 0
        batch_start = txs[0].timestamp

        for tx in txs:
            elapsed_ms = (tx.timestamp - batch_start) * 1000
            would_exceed_size = current_size + tx.size > self.max_bytes
            timed_out = elapsed_ms >= self.max_interval_ms and current

            if would_exceed_size or timed_out:
                batches.append(Batch.from_transactions(current))
                current = []
                current_size = 0
                batch_start = tx.timestamp

            current.append(tx)
            current_size += tx.size

        if current:
            batches.append(Batch.from_transactions(current))

        return batches

    @staticmethod
    def compress(batch: Batch) -> Batch:
        """Apply zlib compression to the batch's raw data (in-place mutation)."""
        batch.compressed_data = zlib.compress(batch.raw_data, level=6)
        batch.compressed = True
        batch.compression_ratio = len(batch.compressed_data) / batch.original_size
        return batch

    @staticmethod
    def compress_if_beneficial(batch: Batch) -> Batch:
        """Only compress if it actually reduces size."""
        compressed = zlib.compress(batch.raw_data, level=6)
        if len(compressed) < batch.original_size:
            batch.compressed_data = compressed
            batch.compressed = True
            batch.compression_ratio = len(compressed) / batch.original_size
        return batch
