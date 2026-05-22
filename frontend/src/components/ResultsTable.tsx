import type { MetricItem } from "../types";

interface Props {
  data: MetricItem[];
}

function fmtUsd(v: number): string {
  if (v < 0.001) return `$${v.toExponential(1)}`;
  if (v < 1) return `$${v.toFixed(4)}`;
  return `$${v.toFixed(2)}`;
}

export default function ResultsTable({ data }: Props) {
  if (data.length === 0) return null;

  return (
    <section className="chart-section">
      <h3>Raw Results</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Strategy</th>
              <th>TPS</th>
              <th>Txs</th>
              <th>Batches</th>
              <th>Cost/Tx</th>
              <th>Latency</th>
              <th>Comp.R</th>
              <th>DA%</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => (
              <tr key={i}>
                <td>{r.strategy}</td>
                <td>{r.tps_target}</td>
                <td>{r.total_tx}</td>
                <td>{r.total_batches}</td>
                <td>{fmtUsd(r.avg_cost_per_tx_usd)}</td>
                <td>{r.avg_latency_ms.toFixed(1)}ms</td>
                <td>{r.avg_compression_ratio.toFixed(3)}</td>
                <td>{r.da_cost_percentage.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
