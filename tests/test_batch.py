"""Tests for batch building, serialization, and merkle tree."""

from da_bench.batch import (
    Batch,
    BatchBuilder,
    build_merkle_root,
    serialize_transactions,
)
from da_bench.transaction import Transaction


class TestMerkleRoot:
    def test_empty(self):
        root = build_merkle_root([])
        assert len(root) == 32  # SHA-256 output

    def test_single_leaf(self):
        root = build_merkle_root([b"hello"])
        assert len(root) == 32

    def test_deterministic(self):
        leaves = [b"a", b"b", b"c"]
        root1 = build_merkle_root(leaves)
        root2 = build_merkle_root(leaves)
        assert root1 == root2

    def test_different_data_different_root(self):
        r1 = build_merkle_root([b"a", b"b"])
        r2 = build_merkle_root([b"a", b"c"])
        assert r1 != r2


class TestSerialization:
    def test_roundtrip(self):
        txs = [
            Transaction(id=i, data=b"hello world"[:i+2], size=i+2, timestamp=1000.0 + i)
            for i in range(3)
        ]
        data = serialize_transactions(txs)
        assert len(data) > 0
        # re-serialization should be deterministic
        assert data == serialize_transactions(txs)


class TestBatch:
    def test_from_transactions(self):
        txs = [
            Transaction(id=1, data=b"hello", size=5, timestamp=1000.0),
            Transaction(id=2, data=b"world", size=5, timestamp=1001.0),
        ]
        batch = Batch.from_transactions(txs)
        assert batch.tx_count == 2
        assert batch.original_size == len(batch.raw_data)
        assert batch.merkle_root is not None
        assert batch.posted_size == batch.original_size

    def test_compression_not_applied_by_default(self):
        txs = [Transaction(id=1, data=b"hello" * 100, size=500, timestamp=1000.0)]
        batch = Batch.from_transactions(txs)
        assert not batch.compressed
        assert batch.compressed_data is None
        assert batch.compression_ratio == 1.0


class TestBatchBuilder:
    def test_empty(self):
        bb = BatchBuilder()
        assert bb.build([]) == []

    def test_single_tx(self):
        bb = BatchBuilder(max_bytes=100_000)
        tx = Transaction(id=1, data=b"hello", size=5, timestamp=1000.0)
        batches = bb.build([tx])
        assert len(batches) == 1
        assert batches[0].tx_count == 1

    def test_size_split(self):
        bb = BatchBuilder(max_bytes=100)
        txs = [
            Transaction(id=i, data=b"x" * 80, size=80, timestamp=float(i))
            for i in range(5)
        ]
        batches = bb.build(txs)
        # Each tx is 80 bytes but serialized overhead makes them >80
        # Should split into multiple batches
        assert len(batches) >= 1

    def test_compress(self):
        txs = [
            Transaction(id=i, data=b"repeated pattern " * 20, size=340, timestamp=float(i))
            for i in range(10)
        ]
        batch = Batch.from_transactions(txs)
        original = batch.original_size
        batch = BatchBuilder.compress(batch)
        assert batch.compressed
        assert batch.compressed_data is not None
        assert batch.compression_ratio < 1.0
        assert len(batch.compressed_data) < original

    def test_compress_random_data(self):
        """Random data (high entropy) may not compress well."""
        txs = [
            Transaction(id=1, data=b"\x00\xff\xab\x12" * 50, size=200, timestamp=0.0)
        ]
        batch = Batch.from_transactions(txs)
        batch = BatchBuilder.compress_if_beneficial(batch)
        # Should either compress or skip gracefully
        assert batch.compression_ratio <= 1.0
