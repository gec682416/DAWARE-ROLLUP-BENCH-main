import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { MetricItem } from "../types";

interface Props {
  data: MetricItem[];
}

const STRAT_COLORS: Record<string, string> = {
  calldata: "#ef4444",
  blob: "#3b82f6",
  compressed_calldata: "#f59e0b",
  external_da: "#22c55e",
};

export default function LatencyChart({ data }: Props) {
  const strategies = [...new Set(data.map((d) => d.strategy))];
  const tpsValues = [...new Set(data.map((d) => d.tps_target))].sort((a, b) => a - b);

  const pivoted = tpsValues.map((tps) => {
    const row: Record<string, number> = { tps };
    for (const s of strategies) {
      const m = data.find((d) => d.strategy === s && d.tps_target === tps);
      row[s] = m ? m.avg_latency_ms : 0;
    }
    return row;
  });

  return (
    <section className="chart-section">
      <h3>Confirmation Latency vs Throughput</h3>
      <p className="chart-desc">End-to-end delay including DA confirmation and compression time.</p>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={pivoted}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="tps" label={{ value: "Target TPS", position: "insideBottom", offset: -5 }} />
          <YAxis tickFormatter={(v) => `${v}ms`} />
          <Tooltip formatter={(v: number) => [`${v.toFixed(1)} ms`, ""]} />
          <Legend />
          {strategies.map((s) => (
            <Line key={s} type="monotone" dataKey={s} stroke={STRAT_COLORS[s] || "#888"}
              strokeWidth={2} dot={{ r: 4 }} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
