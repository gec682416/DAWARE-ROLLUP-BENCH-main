import { useState } from "react";
import type { SweepRequest, StrategyInfo } from "../types";

interface Props {
  loading: boolean;
  strategies: StrategyInfo[];
  onRun: (params: SweepRequest) => void;
}

export default function Sidebar({ loading, strategies, onRun }: Props) {
  const [gasPrice, setGasPrice] = useState(30);
  const [blobGasPrice, setBlobGasPrice] = useState(1);
  const [ethPrice, setEthPrice] = useState(3000);
  const [duration, setDuration] = useState(30);
  const [batchMaxKb, setBatchMaxKb] = useState(120);
  const [batchIntervalMs, setBatchIntervalMs] = useState(2000);
  const [tpsMin, setTpsMin] = useState(10);
  const [tpsMax, setTpsMax] = useState(1000);
  const [tpsSteps, setTpsSteps] = useState(6);
  const [selectedStrats, setSelectedStrats] = useState<string[]>([
    "calldata",
    "blob",
    "compressed",
    "external",
  ]);

  const toggleStrat = (name: string) => {
    setSelectedStrats((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  };

  const handleRun = () => {
    onRun({
      gas_price_gwei: gasPrice,
      blob_gas_price_gwei: blobGasPrice,
      eth_price_usd: ethPrice,
      duration_seconds: duration,
      batch_max_kb: batchMaxKb,
      batch_interval_ms: batchIntervalMs,
      tps_min: tpsMin,
      tps_max: tpsMax,
      tps_steps: tpsSteps,
      strategies: selectedStrats,
    });
  };

  return (
    <aside className="sidebar">
      <h2>Parameters</h2>

      <fieldset>
        <legend>Gas & Price</legend>
        <label>
          Gas Price (Gwei)
          <input type="number" value={gasPrice} min={1} max={500}
            onChange={(e) => setGasPrice(Number(e.target.value))} />
        </label>
        <label>
          Blob Gas Price (Gwei)
          <input type="number" value={blobGasPrice} min={0.001} max={500} step={0.001}
            onChange={(e) => setBlobGasPrice(Number(e.target.value))} />
        </label>
        <label>
          ETH Price (USD)
          <input type="number" value={ethPrice} min={100} max={20000} step={100}
            onChange={(e) => setEthPrice(Number(e.target.value))} />
        </label>
      </fieldset>

      <fieldset>
        <legend>Simulation</legend>
        <label>
          Duration (s)
          <input type="number" value={duration} min={5} max={600}
            onChange={(e) => setDuration(Number(e.target.value))} />
        </label>
        <label>
          Max Batch (KB)
          <input type="number" value={batchMaxKb} min={16} max={1024}
            onChange={(e) => setBatchMaxKb(Number(e.target.value))} />
        </label>
        <label>
          Batch Interval (ms)
          <input type="number" value={batchIntervalMs} min={100} max={30000} step={100}
            onChange={(e) => setBatchIntervalMs(Number(e.target.value))} />
        </label>
      </fieldset>

      <fieldset>
        <legend>TPS Sweep</legend>
        <label>
          Min TPS
          <input type="number" value={tpsMin} min={1} max={1000}
            onChange={(e) => setTpsMin(Number(e.target.value))} />
        </label>
        <label>
          Max TPS
          <input type="number" value={tpsMax} min={10} max={10000}
            onChange={(e) => setTpsMax(Number(e.target.value))} />
        </label>
        <label>
          Steps
          <input type="number" value={tpsSteps} min={2} max={12}
            onChange={(e) => setTpsSteps(Number(e.target.value))} />
        </label>
      </fieldset>

      <fieldset>
        <legend>DA Strategies</legend>
        {strategies.map((s) => (
          <label key={s.name} className="checkbox-label">
            <input type="checkbox" checked={selectedStrats.includes(s.name)}
              onChange={() => toggleStrat(s.name)} />
            {s.label}
          </label>
        ))}
      </fieldset>

      <button className="run-btn" onClick={handleRun} disabled={loading || selectedStrats.length === 0}>
        {loading ? "Running..." : "Run Benchmark"}
      </button>
    </aside>
  );
}
