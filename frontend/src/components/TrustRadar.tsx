import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer,
} from "recharts";

const STRAT_COLORS: Record<string, string> = {
  calldata: "#ef4444",
  blob: "#3b82f6",
  compressed_calldata: "#f59e0b",
  external_da: "#22c55e",
};

const TRUST_DATA = [
  { strategy: "calldata", "Data on L1": 5, "Trustless": 5, "Cost Efficiency": 1, "Low Latency": 5 },
  { strategy: "blob", "Data on L1": 5, "Trustless": 5, "Cost Efficiency": 4, "Low Latency": 5 },
  { strategy: "compressed_calldata", "Data on L1": 5, "Trustless": 5, "Cost Efficiency": 2, "Low Latency": 4 },
  { strategy: "external_da", "Data on L1": 0, "Trustless": 2, "Cost Efficiency": 5, "Low Latency": 3 },
];

interface Props {
  activeStrategies: string[];
}

export default function TrustRadar({ activeStrategies }: Props) {
  const filtered = TRUST_DATA.filter((d) => activeStrategies.includes(d.strategy));

  if (filtered.length === 0) return null;

  return (
    <section className="chart-section">
      <h3>Trust & Security Comparison</h3>
      <p className="chart-desc">
        Qualitative comparison across security dimensions. Higher = better (except for cost, where higher = cheaper).
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={filtered}>
          <PolarGrid />
          <PolarAngleAxis dataKey="strategy" tick={false} />
          <PolarRadiusAxis angle={30} domain={[0, 5]} />
          {["Data on L1", "Trustless", "Cost Efficiency", "Low Latency"].map((axis) => (
            <Radar key={axis} name={axis} dataKey={axis}
              stroke={STRAT_COLORS[filtered[0]?.strategy] || "#888"}
              fill={STRAT_COLORS[filtered[0]?.strategy] || "#888"}
              fillOpacity={0.15} />
          ))}
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </section>
  );
}
