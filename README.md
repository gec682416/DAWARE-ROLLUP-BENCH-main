# DAware-Rollup-Bench

Data Availability-Aware Rollup Benchmarking Platform. Evaluate how different **Data Availability (DA)** strategies affect the performance, cost, and security trade-offs of rollup-style blockchain systems.

## Overview

As rollups scale execution, data availability becomes the primary bottleneck. Publishing all transaction data to Ethereum L1 via calldata guarantees full verifiability but is expensive. Alternative approaches — compressed calldata, external DA layers like Celestia or EigenDA — reduce costs at the expense of additional trust assumptions.

This platform provides:

- A **discrete-event rollup simulator** that models transaction generation, batch building, and DA publication
- **Three DA strategies**: Ethereum calldata, compressed calldata, and external DA (Celestia/EigenDA cost model)
- A **FastAPI backend** that wraps the simulator as REST APIs
- A **React dashboard** (TypeScript + Recharts) with interactive charts for cost, latency, and trust comparison
- **CLI tool** for running single runs, TPS sweeps, and predefined experiment scenarios
- **Metrics collection**: cost per transaction, end-to-end latency, effective throughput, DA bottleneck percentage

## Installation

### Backend (Python)

```bash
cd DAware-Rollup-Bench
python -m pip install -e ".[dev]"
python -m pip install fastapi uvicorn
```

**Requirements**: Python 3.10+

### Frontend (React)

```bash
npm --prefix frontend install
```

**Requirements**: Node.js 18+

## Quick Start

```bash
# Terminal 1 — start the API backend
PYTHONPATH=src python -m uvicorn backend.main:app --port 8000

# Terminal 2 — start the React dashboard
npm --prefix frontend run dev

# Open http://localhost:5173 in your browser
```

Alternatively, run experiments from the CLI without the UI:

```bash
# Compare all three strategies at 100 TPS
python experiments/run_benchmark.py --tps 100 --duration 30

# Run a full TPS sweep
python experiments/run_benchmark.py --tps-sweep --duration 60 --output results.json

# Run a predefined scenario
python experiments/run_benchmark.py --scenario quick
```

## CLI Usage

```
python experiments/run_benchmark.py [OPTIONS]

Options:
  --tps INT              Target transactions per second (default: 100)
  --duration INT         Simulation duration in seconds (default: 120)
  --gas-price FLOAT      Gas price in Gwei (default: 30)
  --eth-price FLOAT      ETH price in USD (default: 3000)
  --strategies STR       Comma-separated strategies: calldata,compressed,external
  --scenario STR         Predefined scenario: baseline, high_gas, low_gas, quick, large_batches
  --tps-sweep            Run full TPS sweep [10, 50, 100, 200, 500, 1000]
  --output PATH          Save aggregated results as JSON
  --csv PATH             Save per-batch records as CSV
```

### Example Output

```
============================================================================
Strategy                  TPS      Txs    Cost/tx    Latency   Comp.R    DA%
----------------------------------------------------------------------------
calldata                  100      300  $1.412566      0.0ms    1.000  96.3%
compressed_calldata       100      300  $1.415461     1.31ms    0.999  96.3%
external_da               100      300   $1.9e-05    150.0ms    1.000   0.0%
============================================================================
```

## Architecture

The platform has three layers:

```
Frontend (React + Recharts)          Backend (FastAPI)           Simulator (Python)
┌─────────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  Sidebar (params)       │    │  POST /api/sweep     │───→│  TransactionGenerator │
│  CostChart              │    │  GET  /api/strategies│    │  BatchBuilder         │
│  LatencyChart           │───→│  GET  /api/health    │    │  DAStrategy.publish() │
│  BottleneckChart        │    │                      │←───│  MetricsCollector     │
│  TrustRadar             │    │  CORS middleware      │    │                      │
│  ResultsTable           │    └──────────────────────┘    └──────────────────────┘
└─────────────────────────┘
     http://localhost:5173         http://localhost:8000
     (Vite dev server)            (Uvicorn ASGI server)
```

Vite proxies `/api/*` requests to the backend during development, so no CORS issues.

## React Dashboard Features

| Component | Description |
|-----------|-------------|
| `Sidebar` | Gas price, ETH price, duration, batch size, TPS range sliders, strategy toggles |
| `CostChart` | Line chart: DA cost per transaction vs TPS (3 strategies overlaid) |
| `LatencyChart` | Line chart: end-to-end confirmation delay vs TPS |
| `BottleneckChart` | Line chart: DA cost as % of total rollup cost — red line at 50% marks the bottleneck threshold |
| `TrustRadar` | Radar chart comparing "Data on L1", "Trustless", "Cost Efficiency", "Low Latency" across strategies |
| `ResultsTable` | Sortable raw data table with all metrics |

## Backend API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sweep` | Run a TPS sweep simulation. Accepts `SweepRequest` JSON, returns `SweepResponse` with metric list |
| `GET` | `/api/strategies` | List available DA strategies with descriptions |
| `GET` | `/api/health` | Health check |

Interactive API docs: open `http://localhost:8000/docs` while the backend is running.

## Core Modules (Simulator)

| Module | Description |
|--------|-------------|
| `config.py` | All tunable parameters: gas constants, ETH price, batch limits, DA pricing |
| `transaction.py` | Transaction model with realistic mixed-size distribution (70/20/10 split) |
| `batch.py` | Batch builder: serialization, Merkle tree root, zlib compression |
| `cost_model.py` | Gas calculation, USD conversion, EIP-4844 blob pricing |
| `da_strategies/` | Abstract base + 3 concrete DA publication strategies |
| `simulator.py` | Discrete-event engine: generate → batch → publish → measure |
| `metrics.py` | Collector and aggregator with CSV/JSON export |

## DA Strategies

### 1. Ethereum Calldata (baseline)

Full transaction data posted as-is to L1 calldata. Cost model: 16 gas per non-zero byte, 4 gas per zero byte.

- **Cost**: High, scales linearly with data size and gas price
- **Latency**: None (data on L1, instantly verifiable)
- **Trust**: None beyond Ethereum L1 security

### 2. Compressed Calldata

Batch data is zlib-compressed before L1 posting. Same trust model as baseline with reduced data footprint.

- **Cost**: At most baseline, significantly lower for structured/repetitive data
- **Latency**: Sub-millisecond compression overhead
- **Trust**: Same as baseline

### 3. External DA (Celestia/EigenDA model)

Data posted to an external DA layer at ~$0.02/MB. The L1 only stores a DA attestation/certificate.

- **Cost**: 10,000–100,000× cheaper than calldata
- **Latency**: ~150ms simulated DA consensus delay (configurable)
- **Trust**: Data availability depends on external validator set; L1 cannot independently verify

## Experiment Scenarios

Predefined scenarios in `experiments/scenarios.py`:

| Scenario | Description |
|----------|-------------|
| `baseline` | TPS sweep [10..1000], 3 seeds, 120s per run |
| `high_gas` | 100 Gwei stress test — shows when L1 DA becomes untenable |
| `low_gas` | 10 Gwei favorable L1 conditions |
| `quick` | Smoke test: 30s per run, 3 TPS points |
| `large_batches` | 500 KB max batches to test batching efficiency |

## Running Tests

```bash
pytest tests/ -v

# With coverage
pytest tests/ --cov=da_bench --cov-report=term-missing
```

## Project Structure

```
DAware-Rollup-Bench/
├── pyproject.toml
├── backend/                          # FastAPI REST API
│   ├── main.py                       # App entry, CORS, routes
│   └── api/simulation.py             # /api/sweep, /api/strategies, /api/health
├── frontend/                         # React dashboard (Vite + TypeScript)
│   ├── index.html
│   ├── vite.config.ts                # Dev server + /api proxy
│   ├── package.json
│   └── src/
│       ├── main.tsx                  # React entry
│       ├── App.tsx                   # Layout: sidebar + chart grid
│       ├── App.css                   # Dark theme styles
│       ├── types/index.ts            # TypeScript interfaces
│       ├── hooks/useSimulation.ts    # API call hook (axios)
│       └── components/
│           ├── Sidebar.tsx           # Parameter controls
│           ├── CostChart.tsx         # Cost vs TPS (Recharts)
│           ├── LatencyChart.tsx      # Latency vs TPS
│           ├── BottleneckChart.tsx   # DA cost bottleneck %
│           ├── TrustRadar.tsx        # Security radar chart
│           └── ResultsTable.tsx      # Raw data table
├── src/da_bench/                     # Simulation engine (Python)
│   ├── config.py                     # All simulation parameters
│   ├── transaction.py                # Transaction model + generator
│   ├── batch.py                      # Batch builder, merkle tree, compression
│   ├── cost_model.py                 # Gas / USD / blob cost calculations
│   ├── da_strategies/
│   │   ├── base.py                   # Abstract DAStrategy + DAResult
│   │   ├── calldata.py               # Ethereum calldata posting
│   │   ├── compressed.py             # Compressed calldata posting
│   │   └── external.py               # External DA (Celestia/EigenDA model)
│   ├── simulator.py                  # Simulation engine + experiment runner
│   └── metrics.py                    # Metrics collection + aggregation
├── experiments/
│   ├── run_benchmark.py              # CLI entry point
│   └── scenarios.py                  # Predefined experiment matrices
├── notebooks/analysis.ipynb          # Jupyter analysis notebook
└── tests/
    ├── test_transaction.py
    ├── test_batch.py
    ├── test_da_strategies.py
    └── test_simulator.py
```

## Key Insights

1. **DA is the dominant cost at scale**: At 30 Gwei and $3000 ETH, DA accounts for ~95% of total rollup operating cost at any significant TPS
2. **Compression helps with structured data**: Random data sees negligible gains, but real-world rollup transactions (RLP-encoded, repeated patterns) should compress 30–60%
3. **External DA is 4-5 orders of magnitude cheaper**: But introduces the trust assumption that external validators honestly serve data
4. **The cross-over point matters**: At what TPS or gas price does the cost saving justify the additional trust assumption? The React dashboard lets you interactively find that threshold
