export interface MetricItem {
  strategy: string;
  tps_target: number;
  duration_s: number;
  total_tx: number;
  total_batches: number;
  total_cost_usd: number;
  avg_cost_per_tx_usd: number;
  avg_latency_ms: number;
  avg_batch_size_tx: number;
  avg_compression_ratio: number;
  effective_throughput_tps: number;
  da_cost_percentage: number;
}

export interface SweepRequest {
  gas_price_gwei: number;
  eth_price_usd: number;
  duration_seconds: number;
  batch_max_kb: number;
  batch_interval_ms: number;
  tps_min: number;
  tps_max: number;
  tps_steps: number;
  strategies: string[];
}

export interface SweepResponse {
  results: MetricItem[];
}

export interface StrategyInfo {
  name: string;
  label: string;
  description: string;
}

export interface SimulationState {
  loading: boolean;
  error: string | null;
  results: MetricItem[];
}
