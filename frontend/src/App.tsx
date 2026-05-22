import { useEffect, useState } from "react";
import { useSimulation } from "./hooks/useSimulation";
import Sidebar from "./components/Sidebar";
import CostChart from "./components/CostChart";
import LatencyChart from "./components/LatencyChart";
import BottleneckChart from "./components/BottleneckChart";
import TrustRadar from "./components/TrustRadar";
import ResultsTable from "./components/ResultsTable";
import SimulationLoader from "./components/SimulationLoader";
import type { SweepRequest } from "./types";
import "./App.css";

export default function App() {
  const { loading, error, results, strategies, fetchStrategies, runSweep } =
    useSimulation();

  const [lastParams, setLastParams] = useState<SweepRequest | null>(null);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const handleRun = (params: SweepRequest) => {
    setLastParams(params);
    runSweep(params);
  };

  const hasData = results.length > 0;
  const activeStrats = [...new Set(results.map((r) => r.strategy))];

  const statCards = hasData
    ? (() => {
        const byStrat = new Map<string, (typeof results)[0][]>();
        for (const r of results) byStrat.set(r.strategy, [...(byStrat.get(r.strategy) ?? []), r]);

        const cheapest = results.reduce((a, b) =>
          a.avg_cost_per_tx_usd < b.avg_cost_per_tx_usd ? a : b
        );
        const highestTps = results.reduce((a, b) =>
          a.effective_throughput_tps > b.effective_throughput_tps ? a : b
        );
        const totalRuns = results.length;

        return { cheapest, highestTps, totalRuns };
      })()
    : null;

  return (
    <div className="app-layout">
      <Sidebar loading={loading} strategies={strategies} onRun={handleRun} />

      <main className="main">
        <h1>DA-Rollup Benchmark Dashboard</h1>
        <p className="subtitle">
          Compare Data Availability strategies across cost, latency, and trust
        </p>

        {error && <div className="error-banner">{error}</div>}

        {statCards && (
          <div className="stat-row">
            <div className="stat-card">
              <span className="stat-label">Cheapest Strategy</span>
              <span className="stat-value">{statCards.cheapest.strategy}</span>
              <span className="stat-sub">${statCards.cheapest.avg_cost_per_tx_usd.toFixed(6)}/tx</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Max Throughput</span>
              <span className="stat-value">{statCards.highestTps.effective_throughput_tps.toFixed(0)} TPS</span>
              <span className="stat-sub">{statCards.highestTps.strategy}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Data Points</span>
              <span className="stat-value">{statCards.totalRuns} runs</span>
              <span className="stat-sub">{activeStrats.length} strategies</span>
            </div>
          </div>
        )}

        {!hasData && !loading && !error && (
          <div className="welcome">
            <h2>Welcome</h2>
            <p>Configure parameters in the sidebar and run a benchmark to see charts.</p>
          </div>
        )}

        {loading && lastParams && (
          <SimulationLoader
            tpsMin={lastParams.tps_min}
            tpsMax={lastParams.tps_max}
            steps={lastParams.tps_steps}
            strategies={lastParams.strategies}
          />
        )}

        {hasData && (
          <>
            <CostChart data={results} />
            <LatencyChart data={results} />
            <BottleneckChart data={results} />
            <TrustRadar activeStrategies={activeStrats} />
            <ResultsTable data={results} />
          </>
        )}
      </main>
    </div>
  );
}
