#!/usr/bin/env python3
"""Streamlit dashboard for DA-aware rollup benchmarking visualization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from da_bench.config import SimulationConfig
from da_bench.da_strategies import (
    BlobStrategy,
    CalldataStrategy,
    CompressedCalldataStrategy,
    ExternalDAStrategy,
)
from da_bench.simulator import run_experiment_matrix

st.set_page_config(
    page_title="DA-Rollup Benchmark",
    page_icon="📊",
    layout="wide",
)

# --- Sidebar ---
st.sidebar.title("Simulation Parameters")

gas_price = st.sidebar.slider("Gas Price (Gwei)", 5.0, 200.0, 30.0, 5.0)
blob_gas_price = st.sidebar.slider("Blob Gas Price (Gwei)", 0.001, 50.0, 1.0, 0.001)
eth_price = st.sidebar.slider("ETH Price (USD)", 1000, 8000, 3000, 100)
duration = st.sidebar.slider("Duration per run (s)", 10, 300, 60, 10)
batch_max_kb = st.sidebar.slider("Max Batch Size (KB)", 32, 512, 120, 32)
batch_interval = st.sidebar.slider("Max Batch Interval (ms)", 500, 10000, 2000, 500)

st.sidebar.markdown("---")
st.sidebar.markdown("### DA Strategies")
use_calldata = st.sidebar.checkbox("Calldata (baseline)", True)
use_blob = st.sidebar.checkbox("Ethereum Blob DA", True)
use_compressed = st.sidebar.checkbox("Compressed Calldata", True)
use_external = st.sidebar.checkbox("External DA", True)

st.sidebar.markdown("---")
st.sidebar.markdown("### TPS Sweep")
tps_min = st.sidebar.number_input("Min TPS", 1, 100, 10)
tps_max = st.sidebar.number_input("Max TPS", 50, 5000, 1000)
tps_step = st.sidebar.selectbox("Sweep Resolution", ["coarse", "medium", "fine"])
STEP_MAP = {"coarse": 8, "medium": 6, "fine": 10}
n_points = STEP_MAP[tps_step]

run = st.sidebar.button("▶ Run Benchmark", type="primary", use_container_width=True)

# --- Main ---
st.title("Data Availability-Aware Rollup Benchmarking")
st.markdown(
    "Evaluate how different **Data Availability** strategies affect rollup "
    "cost, throughput, and latency. Compare Ethereum calldata, compressed calldata, "
    "and external DA layers (Celestia/EigenDA model)."
)

# --- Cached / persisted results ---
if "results_df" not in st.session_state:
    st.session_state.results_df = None
if "all_metrics" not in st.session_state:
    st.session_state.all_metrics = None


def _build_strategies(cfg):
    strategies = []
    if use_calldata:
        strategies.append(CalldataStrategy(cfg.gas_price_gwei, cfg.eth_price_usd))
    if use_blob:
        strategies.append(BlobStrategy(cfg.blob_gas_price_gwei, cfg.eth_price_usd))
    if use_compressed:
        strategies.append(CompressedCalldataStrategy(cfg.gas_price_gwei, cfg.eth_price_usd))
    if use_external:
        strategies.append(ExternalDAStrategy(
            cost_per_mb=cfg.external_da_cost_per_mb,
            confirmation_delay_ms=cfg.external_da_delay_ms,
        ))
    return strategies


if run:
    if not any([use_calldata, use_blob, use_compressed, use_external]):
        st.error("Select at least one DA strategy.")
    else:
        tps_values = [int(tps_min + (tps_max - tps_min) * i / (n_points - 1))
                       for i in range(max(n_points, 2))]
        tps_values = sorted(set(max(1, v) for v in tps_values))

        cfg = SimulationConfig(
            gas_price_gwei=gas_price,
            blob_gas_price_gwei=blob_gas_price,
            eth_price_usd=eth_price,
            duration_seconds=duration,
            batch_max_bytes=batch_max_kb * 1024,
            batch_max_interval_ms=batch_interval,
        )
        strategies = _build_strategies(cfg)

        status = st.status("Running simulations...", expanded=True)
        with status:
            for tps in tps_values:
                st.write(f"TPS={tps}...")
            all_metrics = run_experiment_matrix(
                tps_values=tps_values,
                strategies=strategies,
                base_config=cfg,
                seeds=[42],
            )
            st.write("Done!")
        status.update(label="Simulation complete!", state="complete")

        st.session_state.all_metrics = all_metrics
        st.session_state.results_df = pd.DataFrame([m.to_dict() for m in all_metrics])

# --- Charts ---
if st.session_state.results_df is not None:
    df = st.session_state.results_df

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    # Find best strategy per metric
    best_cost = df.loc[df.groupby("tps_target")["avg_cost_per_tx_usd"].idxmin()]
    best_lat = df.loc[df.groupby("tps_target")["avg_latency_ms"].idxmin()]

    with col1:
        cheapest = df.loc[df["avg_cost_per_tx_usd"].idxmin()]
        st.metric("Cheapest Strategy", cheapest["strategy"],
                  f"${cheapest['avg_cost_per_tx_usd']:.6f}/tx")
    with col2:
        fastest = df.loc[df["avg_latency_ms"].idxmin()]
        st.metric("Lowest Latency", fastest["strategy"],
                  f"{fastest['avg_latency_ms']:.1f}ms")
    with col3:
        max_tps_row = df.loc[df["total_tx"].idxmax()]
        st.metric("Max Throughput", f"{max_tps_row['effective_throughput_tps']:.0f} TPS")
    with col4:
        strategies_run = df["strategy"].nunique()
        tps_points = df["tps_target"].nunique()
        st.metric("Data Points", f"{len(df)} runs", f"{strategies_run} strats × {tps_points} TPS")

    st.markdown("---")

    # --- Chart 1: Cost per TX vs TPS ---
    st.subheader("Cost per Transaction vs Throughput")
    st.markdown("Lower is better. External DA dramatically reduces cost at scale.")

    fig_cost = px.line(
        df,
        x="tps_target",
        y="avg_cost_per_tx_usd",
        color="strategy",
        markers=True,
        labels={
            "tps_target": "Target TPS",
            "avg_cost_per_tx_usd": "Avg Cost per Tx (USD)",
            "strategy": "DA Strategy",
        },
    )
    fig_cost.update_layout(height=400)
    fig_cost.update_yaxes(tickformat="$.6f")
    st.plotly_chart(fig_cost, use_container_width=True)

    # --- Chart 2: Latency vs TPS ---
    st.subheader("Confirmation Latency vs Throughput")
    st.markdown("External DA adds a fixed confirmation delay (simulated DA consensus).")

    fig_lat = px.line(
        df,
        x="tps_target",
        y="avg_latency_ms",
        color="strategy",
        markers=True,
        labels={
            "tps_target": "Target TPS",
            "avg_latency_ms": "Avg Latency (ms)",
            "strategy": "DA Strategy",
        },
    )
    fig_lat.update_layout(height=400)
    st.plotly_chart(fig_lat, use_container_width=True)

    # --- Chart 3: DA Cost as % of Total ---
    st.subheader("DA Cost as % of Total Rollup Cost")
    st.markdown(
        "Shows when DA becomes the dominant cost. "
        "Above ~50%, DA is the primary scaling bottleneck."
    )

    fig_pct = px.line(
        df,
        x="tps_target",
        y="da_cost_percentage",
        color="strategy",
        markers=True,
        labels={
            "tps_target": "Target TPS",
            "da_cost_percentage": "DA Cost %",
            "strategy": "DA Strategy",
        },
    )
    fig_pct.add_hline(y=50, line_dash="dash", line_color="red",
                       annotation_text="DA bottleneck threshold")
    fig_pct.update_layout(height=400)
    st.plotly_chart(fig_pct, use_container_width=True)

    # --- Chart 4: Compression Ratio ---
    st.subheader("Compression Efficiency")
    st.markdown("Ratio of compressed size to original size. Lower = better compression.")

    comp_df = df[df["strategy"] == "compressed_calldata"]
    if not comp_df.empty:
        fig_comp = px.line(
            comp_df,
            x="tps_target",
            y="avg_compression_ratio",
            markers=True,
            labels={
                "tps_target": "Target TPS",
                "avg_compression_ratio": "Compression Ratio",
            },
        )
        fig_comp.update_layout(height=300)
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Run with 'Compressed Calldata' enabled to see compression metrics.")

    # --- Chart 5: Trust/Security Trade-off ---
    st.subheader("Trust & Security Comparison")

    strategies_in_run = df["strategy"].unique()
    trust_data = []
    for s in strategies_in_run:
        if "external" in s:
            trust_data.append({
                "Strategy": s,
                "Data on L1": 0,
                "Trustless Verification": 2,
                "L1 Enforcement": 0,
                "Cost Efficiency": 5,
            })
        elif s == "blob":
            trust_data.append({
                "Strategy": s,
                "Data on L1": 5,
                "Trustless Verification": 5,
                "L1 Enforcement": 5,
                "Cost Efficiency": 4,
            })
        else:
            trust_data.append({
                "Strategy": s,
                "Data on L1": 5,
                "Trustless Verification": 5,
                "L1 Enforcement": 5,
                "Cost Efficiency": 1 if "compressed" in s else 0,
            })

    if trust_data:
        categories = ["Data on L1", "Trustless Verification", "L1 Enforcement", "Cost Efficiency"]
        fig_radar = go.Figure()
        for td in trust_data:
            fig_radar.add_trace(go.Scatterpolar(
                r=[td[c] for c in categories],
                theta=categories,
                fill="toself",
                name=td["Strategy"],
            ))
        fig_radar.update_layout(height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- Raw Data Table ---
    st.markdown("---")
    st.subheader("Raw Results")
    st.dataframe(
        df.style.format({
            "avg_cost_per_tx_usd": "${:.6f}",
            "total_cost_usd": "${:.4f}",
            "avg_latency_ms": "{:.1f}ms",
            "avg_compression_ratio": "{:.4f}",
            "da_cost_percentage": "{:.1f}%",
        }),
        use_container_width=True,
    )

    # Download
    csv_data = df.to_csv(index=False)
    st.download_button(
        "Download CSV",
        csv_data,
        "da_bench_results.csv",
        "text/csv",
    )

else:
    # Landing state
    st.info("Configure parameters in the sidebar and click **Run Benchmark** to start.")
    st.markdown("""
    ### What this dashboard shows

    1. **Cost per Tx** — how DA costs scale with throughput for each strategy
    2. **Latency** — confirmation delays introduced by each DA approach
    3. **DA Bottleneck** — at what TPS does DA become the primary cost driver?
    4. **Compression Efficiency** — how much does compression reduce data footprint?
    5. **Trust Trade-offs** — radar chart comparing security assumptions

    ### DA Strategies Modeled

    | Strategy | Cost Model | Trust Model |
    |----------|-----------|-------------|
    | **Calldata** | 16 gas/non-zero byte, 4 gas/zero byte | Full L1 security |
    | **Ethereum Blob DA** | EIP-4844 blob gas market | Ethereum DA, limited retention window |
    | **Compressed Calldata** | Same gas model, zlib-compressed data | Full L1 security |
    | **External DA** | ~$0.02/MB (Celestia model) + 150ms delay | External validator trust |
    """)
