# Data Availability-Aware Rollup Benchmark Report

## 1. Objective

This project evaluates how different data availability (DA) publication strategies affect the cost, latency, and effective throughput of a rollup-style blockchain system. The simulator focuses on the DA publication path rather than execution cost, because rollups often move computation off-chain while still needing to publish enough data for verification and reconstruction.

The benchmark compares four DA strategies:

| Strategy | Model | Main trust assumption |
|---|---|---|
| Ethereum calldata | Full batch data posted as calldata | Data is fully available from Ethereum L1 |
| Ethereum blob DA | Batch data posted as EIP-4844 blobs | Ethereum DA security, but blob data has limited retention |
| Compressed calldata | zlib-compressed batch data posted as calldata | Same as calldata, plus decompression by verifiers |
| External DA | Mock Celestia/EigenDA-style DA layer | DA depends on an external validator/operator set |

## 2. Experimental Setup

The experiment was run from the current repository version with this command:

```bash
python3 experiments/run_benchmark.py --tps-sweep --duration 30 --strategies calldata,blob,compressed,external --output /private/tmp/da_report_sweep.json
```

Default parameters used by the simulator:

| Parameter | Value |
|---|---:|
| Duration per TPS point | 30 seconds |
| TPS sweep | 10, 50, 100, 200, 500, 1000 |
| Random seed | 42 |
| Ethereum gas price | 30 gwei |
| Ethereum price | 3000 USD/ETH |
| Blob gas price | 1 gwei |
| External DA cost | 0.02 USD/MB |
| External DA confirmation delay | 150 ms |
| Batch max size | 120,000 bytes |
| Batch max interval | 2000 ms |
| Fixed L1 batch submission overhead | 100,000 gas per batch |

The workload uses the built-in synthetic transaction distribution:

| Transaction class | Share | Size range |
|---|---:|---:|
| Small transfer-like transactions | 70% | 100-300 bytes |
| Medium interaction-like transactions | 20% | 300-1000 bytes |
| Large contract-like transactions | 10% | 1000-10000 bytes |

Important modeling note: transaction payloads are high-entropy random bytes in the current simulator. This is useful for stress-testing DA byte costs, but it makes compression look weak. Real rollup batches often contain structured encodings and repeated fields, so compressed calldata may perform better on real traces than in this synthetic run.

## 3. Results

### 3.1 Cost Per Transaction

| TPS | Calldata | Blob | Compressed | External DA |
|---:|---:|---:|---:|---:|
| 10 | $1.862458 | $0.469661 | $1.866229 | $0.450019 |
| 50 | $1.293608 | $0.100194 | $1.295732 | $0.096016 |
| 100 | $1.276864 | $0.068884 | $1.278604 | $0.066016 |
| 200 | $1.266434 | $0.067318 | $1.267820 | $0.064516 |
| 500 | $1.267088 | $0.066379 | $1.268596 | $0.063616 |
| 1000 | $1.265830 | $0.066066 | $1.267212 | $0.063316 |

At 1000 TPS, blob DA reduces cost per transaction from $1.265830 to $0.066066, a 94.78% reduction versus calldata. External DA reduces cost per transaction to $0.063316, a 95.00% reduction versus calldata. In this run, external DA is only slightly cheaper than blobs because the fixed L1 batch submission overhead still dominates the total cost after DA byte costs become small.

Compressed calldata does not reduce cost in this default workload. At 1000 TPS, compressed calldata costs $1.267212 per transaction, about 0.11% higher than calldata. This is caused by the simulator's random high-entropy transaction bytes, where zlib compression adds a small header/metadata overhead without meaningfully shrinking the payload.

### 3.2 Average Latency

| TPS | Calldata | Blob | Compressed | External DA |
|---:|---:|---:|---:|---:|
| 10 | 950.00 ms | 950.00 ms | 950.19 ms | 1100.00 ms |
| 50 | 927.50 ms | 927.50 ms | 928.57 ms | 1077.50 ms |
| 100 | 676.82 ms | 676.82 ms | 678.37 ms | 826.82 ms |
| 200 | 346.34 ms | 346.34 ms | 347.93 ms | 496.34 ms |
| 500 | 140.51 ms | 140.51 ms | 142.16 ms | 290.51 ms |
| 1000 | 70.59 ms | 70.59 ms | 72.29 ms | 220.59 ms |

Latency decreases as TPS increases because batches fill by size before the maximum batch interval is reached. At low TPS, transactions wait longer inside batches. At high TPS, batches fill quickly, so average wait time falls.

External DA consistently adds about 150 ms compared with calldata/blob because the model includes an external DA confirmation delay. Compressed calldata adds only a small CPU compression delay in this implementation.

### 3.3 Effective Throughput

| TPS target | Calldata | Blob | Compressed | External DA |
|---:|---:|---:|---:|---:|
| 10 | 10.00 | 10.00 | 10.00 | 10.00 |
| 50 | 50.00 | 50.00 | 50.00 | 49.80 |
| 100 | 100.00 | 100.00 | 100.00 | 99.50 |
| 200 | 200.00 | 200.00 | 200.00 | 199.00 |
| 500 | 500.00 | 500.00 | 500.00 | 497.50 |
| 1000 | 1000.00 | 1000.00 | 1000.00 | 995.10 |

The simulator now reports throughput using simulated time rather than Python wall-clock runtime. Calldata, blob DA, and compressed calldata meet the target TPS in this run. External DA is slightly lower at higher TPS because the modeled DA confirmation delay extends the completion window.

### 3.4 DA Cost as Percentage of Total Rollup Cost

| TPS | Calldata | Blob | Compressed | External DA |
|---:|---:|---:|---:|---:|
| 10 | 75.8% | 4.2% | 75.9% | 0.0% |
| 50 | 92.6% | 4.2% | 92.6% | 0.0% |
| 100 | 94.8% | 4.2% | 94.8% | 0.0% |
| 200 | 94.9% | 4.2% | 94.9% | 0.0% |
| 500 | 95.0% | 4.2% | 95.0% | 0.0% |
| 1000 | 95.0% | 4.2% | 95.0% | 0.0% |

For calldata and compressed calldata, DA byte publication dominates the total cost once the workload is above 50 TPS. Around 95% of the total rollup cost comes from data posting rather than fixed batch submission overhead.

Blob DA changes the cost structure. Blob byte costs are low enough that fixed L1 batch submission overhead becomes the main cost, leaving blob DA byte cost at about 4.2% of total cost in this model.

External DA byte publication is so cheap under the mock 0.02 USD/MB model that it rounds to 0.0% of total rollup cost in the table. This does not mean external DA is free; it means the fixed L1 batch submission overhead dominates after moving data off Ethereum calldata/blob pricing.

## 4. Interpretation

### Finding 1: Calldata is the most expensive DA strategy

Calldata gives the strongest and simplest availability guarantee because all transaction data is directly available from Ethereum L1. The cost is high because calldata gas scales linearly with posted bytes. At 1000 TPS, calldata costs $1.265830 per transaction in this experiment.

This supports the project premise: as execution scales, publishing data directly to L1 calldata becomes a major scaling bottleneck.

### Finding 2: Blob DA provides most of the cost benefit without leaving Ethereum DA

Blob DA reduces cost by 94.78% at 1000 TPS compared with calldata. It keeps DA under Ethereum consensus assumptions, but the data is not stored forever in the same way as calldata. This makes blobs a strong middle-ground strategy: much cheaper than calldata while avoiding the stronger external-validator trust assumption of an external DA layer.

### Finding 3: External DA is cheapest, but the security model changes

External DA is the cheapest strategy in this run, at $0.063316 per transaction at 1000 TPS. However, this comes with additional trust assumptions. Ethereum L1 no longer directly carries the full transaction data; the rollup must rely on an external DA network, bridge, attestation, light-client sampling, or similar mechanism to convince users that the data is available.

The key trade-off is therefore not only "lower cost"; it is "lower cost in exchange for a larger trust and integration surface."

### Finding 4: Compression depends heavily on workload entropy

Compressed calldata performs slightly worse than plain calldata on the default synthetic workload because the generated bytes are random. The average compression ratio is about 0.998 at high TPS, which is not enough to offset compression overhead.

This should not be interpreted as "compression is useless." It means this specific workload is not compressible. A stronger future experiment should add a structured transaction generator or replay real encoded rollup transactions. Under repeated addresses, ABI selectors, RLP fields, or similar structure, compression could produce much larger savings.

### Finding 5: Batch formation affects latency

At 10 TPS, calldata/blob latency is about 950 ms because transactions wait for batch formation. At 1000 TPS, latency falls to about 70.59 ms because batches fill quickly. This shows that latency is driven not only by DA strategy but also by batching policy.

External DA shifts the latency curve upward by about 150 ms in this model. That is acceptable for some throughput-oriented rollup workloads, but may be problematic for latency-sensitive applications.

## 5. Trust and Security Trade-off

| Strategy | Cost efficiency | Latency | Trust/security profile |
|---|---|---|---|
| Calldata | Worst | Low extra DA delay | Strongest availability model; all data is directly on Ethereum L1 |
| Blob DA | Strong | Low extra DA delay | Ethereum DA security, but data has limited retention |
| Compressed calldata | Workload-dependent | Slight CPU overhead | Same trust model as calldata if decompression is deterministic and verifier-compatible |
| External DA | Best in this run | Adds external DA confirmation delay | Requires trust in external DA network, bridge, attestation, or sampling assumptions |

The benchmark suggests that DA is indeed a major bottleneck when using calldata. Blobs and external DA both relieve this bottleneck, but they do so with different security and architectural trade-offs.

## 6. Limitations

This is a simulator, not a full production rollup. The following limitations should be considered when interpreting the results:

1. Gas price, blob gas price, ETH price, and external DA cost are fixed inputs rather than live market data.
2. External DA is modeled as a simple per-MB cost plus fixed confirmation delay; it does not include real protocol behavior, validator failures, sampling probabilities, bridge costs, or slashing mechanisms.
3. The workload uses random synthetic bytes, so it is unfavorable to compression.
4. Execution cost, proof generation cost, prover latency, L1 finality, and withdrawal finality are outside the current benchmark scope.
5. Blob retention is represented qualitatively as a trust/security note, not as a full archival-data availability model.

## 7. Conclusion

The experiment supports the main hypothesis of the project: data availability publication can dominate rollup operating cost, especially when using Ethereum calldata. In this run, calldata DA accounts for about 95% of total cost at 100 TPS and above.

Ethereum blobs reduce the cost per transaction by about 94.78% at 1000 TPS while keeping DA within Ethereum's security model. External DA reduces cost slightly further, but introduces additional trust assumptions and latency. Compressed calldata does not help under the current high-entropy workload, so future experiments should add structured transaction traces to evaluate compression more fairly.

Overall, the benchmark shows that the best DA strategy depends on what the rollup optimizes for: maximum Ethereum-native verifiability, lower cost, lower latency, or acceptable external trust assumptions.
