import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { MetricItem } from "../types";

interface Props {
  data: MetricItem[];
}

const STRAT_COLORS: Record<string, string> = {
  calldata: "#ef4444",
  compressed_calldata: "#f59e0b",
  external_da: "#22c55e",
};

function pivot(data: MetricItem[], field: keyof MetricItem) {
  const strategies = [...new Set(data.map((d) => d.strategy))];
  const tpsValues = [...new Set(data.map((d) => d.tps_target))].sort((a, b) => a - b);

  return tpsValues.map((tps) => {
    const row: Record<string, number> = { tps };
    for (const strat of strategies) {
      const match = data.find((d) => d.strategy === strat && d.tps_target === tps);
      row[strat] = match ? (match[field] as number) : 0;
    }
    return row;
  });
}

export default function CostChart({ data }: Props) {
  const pivoted = pivot(data, "avg_cost_per_tx_usd");
  const strategies = [...new Set(data.map((d) => d.strategy))];

  return (
    <section className="chart-section">
      <h3>Cost per Transaction vs Throughput</h3>
      <p className="chart-desc">DA cost per transaction. Lower is better.</p>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={pivoted}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="tps" label={{ value: "Target TPS", position: "insideBottom", offset: -5 }} />
          <YAxis tickFormatter={(v) => `$${v.toFixed(4)}`} />
          <Tooltip formatter={(v: number) => [`$${v.toFixed(6)}`, ""]} />
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
