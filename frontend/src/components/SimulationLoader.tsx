import { useEffect, useState } from "react";

interface Props {
  tpsMin: number;
  tpsMax: number;
  steps: number;
  strategies: string[];
}

export default function SimulationLoader({ tpsMin, tpsMax, steps, strategies }: Props) {
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 40);
    return () => clearInterval(id);
  }, []);

  // Generate fake transaction blocks flowing through the pipeline
  const blocks = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    x: ((tick * 2 + i * 12.5) % 100),
    y: 30 + Math.sin(tick * 0.1 + i) * 15,
    size: 6 + Math.random() * 4,
    opacity: 0.4 + ((tick + i * 7) % 10) / 10 * 0.6,
  }));

  return (
    <div className="sim-loader">
      {/* Pipeline stages */}
      <div className="pipeline">
        <div className="pipeline-stage">
          <div className="stage-icon">⟳</div>
          <div className="stage-label">Generate</div>
          <div className="stage-stat">{strategies.length * steps} runs</div>
        </div>
        <div className="pipeline-arrow">→</div>
        <div className="pipeline-stage">
          <div className="stage-icon">⊞</div>
          <div className="stage-label">Batch</div>
          <div className="stage-stat">building</div>
        </div>
        <div className="pipeline-arrow">→</div>
        <div className="pipeline-stage">
          <div className="stage-icon">⬆</div>
          <div className="stage-label">Publish</div>
          <div className="stage-stat">{strategies.join(" · ")}</div>
        </div>
      </div>

      {/* Transaction stream animation */}
      <div className="tx-stream">
        <svg viewBox="0 0 100 60" className="tx-stream-svg">
          {/* Pipeline track */}
          <rect x="0" y="26" width="100" height="6" rx="3" fill="#1e3a5f" />

          {/* Flowing transaction blocks */}
          {blocks.map((b) => (
            <rect
              key={b.id}
              x={b.x}
              y={b.y}
              width={b.size}
              height={b.size}
              rx={1.5}
              fill="#60a5fa"
              opacity={b.opacity}
            />
          ))}

          {/* Batch bucket at center */}
          <rect x="42" y="8" width="16" height="22" rx="3" fill="none" stroke="#3b82f6" strokeWidth="0.8" />
          <text x="50" y="21" textAnchor="middle" fill="#93c5fd" fontSize="4">
            Batch
          </text>

          {/* DA layer at right */}
          <rect x="78" y="10" width="18" height="18" rx="2" fill="none" stroke="#22c55e" strokeWidth="0.8" />
          <text x="87" y="22" textAnchor="middle" fill="#86efac" fontSize="3.5">
            DA Layer
          </text>

          {/* Animated pulses */}
          <circle cx="50" cy="19" r={Math.abs(Math.sin(tick * 0.05)) * 8}
            fill="none" stroke="#3b82f6" strokeWidth="0.3" opacity="0.4" />
          <circle cx="87" cy="19" r={Math.abs(Math.sin(tick * 0.05 + 1)) * 7}
            fill="none" stroke="#22c55e" strokeWidth="0.3" opacity="0.4" />
        </svg>
      </div>

      {/* Progress info */}
      <div className="loader-info">
        <div className="loader-spinner" />
        <span>
          Simulating {strategies.length} strategies across {steps} TPS points ({tpsMin}–{tpsMax} TPS)
        </span>
      </div>
    </div>
  );
}
