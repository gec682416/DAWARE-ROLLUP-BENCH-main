#!/usr/bin/env python3
"""CLI entry point to run DA benchmarking experiments."""

import argparse
import json
import sys
from pathlib import Path

# Allow running as a script from the project root
_project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _project_root)
sys.path.insert(0, str(Path(_project_root) / "src"))

from da_bench.config import SimulationConfig
from da_bench.da_strategies import (
    CalldataStrategy,
    CompressedCalldataStrategy,
    ExternalDAStrategy,
)
from da_bench.simulator import run_comparison, run_experiment_matrix
from experiments.scenarios import ALL_SCENARIOS


STRATEGY_REGISTRY = {
    "calldata": CalldataStrategy,
    "compressed": CompressedCalldataStrategy,
    "external": ExternalDAStrategy,
}


def build_strategies(names: list[str], config: SimulationConfig):
    """Instantiate DA strategies from their names."""
    strategies = []
    for name in names:
        cls = STRATEGY_REGISTRY.get(name)
        if cls is None:
            print(f"Unknown strategy: {name}. Options: {list(STRATEGY_REGISTRY)}")
            sys.exit(1)
        if name == "external":
            strategies.append(cls())
        else:
            strategies.append(cls(
                gas_price_gwei=config.gas_price_gwei,
                eth_price_usd=config.eth_price_usd,
            ))
    return strategies


def print_results(results):
    """Pretty-print aggregated results as a table."""
    header = f"{'Strategy':<22} {'TPS':>6} {'Txs':>8} {'Cost/tx':>10} {'Latency':>10} {'Comp.R':>8} {'DA%':>6}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    for m in results:
        d = m.to_dict()
        print(
            f"{d['strategy']:<22} {d['tps_target']:>6} {d['total_tx']:>8} "
            f"{'$' + str(d['avg_cost_per_tx_usd']):>10} "
            f"{str(d['avg_latency_ms']) + 'ms':>10} "
            f"{d['avg_compression_ratio']:>8.3f} "
            f"{d['da_cost_percentage']:>5.1f}%"
        )
    print("=" * len(header))


def main():
    parser = argparse.ArgumentParser(
        description="DAware Rollup Benchmark — compare Data Availability strategies"
    )
    parser.add_argument(
        "--tps", type=int, default=100,
        help="Target transactions per second (default: 100)"
    )
    parser.add_argument(
        "--duration", type=int, default=120,
        help="Simulation duration in seconds (default: 120)"
    )
    parser.add_argument(
        "--gas-price", type=float, default=30.0,
        help="Gas price in Gwei (default: 30)"
    )
    parser.add_argument(
        "--eth-price", type=float, default=3000.0,
        help="ETH price in USD (default: 3000)"
    )
    parser.add_argument(
        "--strategies", type=str, default="calldata,compressed,external",
        help="Comma-separated DA strategies (default: calldata,compressed,external)"
    )
    parser.add_argument(
        "--scenario", type=str,
        help="Run a predefined scenario: " + ", ".join(ALL_SCENARIOS)
    )
    parser.add_argument(
        "--tps-sweep", action="store_true",
        help="Run a full TPS sweep (10, 50, 100, 200, 500, 1000)"
    )
    parser.add_argument(
        "--output", type=str,
        help="Save results as JSON to the given path"
    )
    parser.add_argument(
        "--csv", type=str,
        help="Save per-batch records as CSV to the given path"
    )

    args = parser.parse_args()

    # Predefined scenario
    if args.scenario:
        if args.scenario not in ALL_SCENARIOS:
            print(f"Unknown scenario: {args.scenario}. Options: {list(ALL_SCENARIOS)}")
            sys.exit(1)
        scenario = ALL_SCENARIOS[args.scenario]
        cfg = scenario["config"]
        strat_names = args.strategies.split(",")
        strategies = build_strategies(strat_names, cfg)

        print(f"Scenario: {scenario['description']}")
        print(f"TPS values: {scenario['tps_values']}, Seeds: {len(scenario['seeds'])}")

        all_results = run_experiment_matrix(
            tps_values=scenario["tps_values"],
            strategies=strategies,
            base_config=cfg,
            seeds=scenario["seeds"],
        )
        print_results(all_results)

        if args.output:
            data = [m.to_dict() for m in all_results]
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"\nSaved summary to {args.output}")

        if args.csv:
            # Save all per-batch records
            import csv
            all_records = []
            for m in all_results:
                all_records.extend(m.records)
            if all_records:
                with open(args.csv, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
                    writer.writeheader()
                    writer.writerows(all_records)
                print(f"Saved per-batch records to {args.csv}")
        return

    # TPS sweep mode
    if args.tps_sweep:
        cfg = SimulationConfig(
            gas_price_gwei=args.gas_price,
            eth_price_usd=args.eth_price,
            duration_seconds=args.duration,
        )
        strat_names = args.strategies.split(",")
        strategies = build_strategies(strat_names, cfg)

        tps_values = [10, 50, 100, 200, 500, 1000]
        all_results = run_experiment_matrix(
            tps_values=tps_values,
            strategies=strategies,
            base_config=cfg,
            seeds=[42],
        )
        print_results(all_results)

        if args.output:
            data = [m.to_dict() for m in all_results]
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"\nSaved summary to {args.output}")
        return

    # Single run mode
    cfg = SimulationConfig(
        gas_price_gwei=args.gas_price,
        eth_price_usd=args.eth_price,
        tps=args.tps,
        duration_seconds=args.duration,
    )
    strat_names = args.strategies.split(",")
    strategies = build_strategies(strat_names, cfg)

    print(f"Running: TPS={args.tps}, duration={args.duration}s, "
          f"gas={args.gas_price} Gwei, ETH=${args.eth_price}")
    print(f"Strategies: {', '.join(s.name for s in strategies)}\n")

    results = run_comparison(cfg, strategies)
    print_results(results)

    if args.output:
        data = [m.to_dict() for m in results]
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved summary to {args.output}")

    if args.csv:
        import csv
        all_records = []
        for m in results:
            all_records.extend(m.records)
        if all_records:
            with open(args.csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
                writer.writeheader()
                writer.writerows(all_records)
            print(f"Saved per-batch records to {args.csv}")


if __name__ == "__main__":
    main()
