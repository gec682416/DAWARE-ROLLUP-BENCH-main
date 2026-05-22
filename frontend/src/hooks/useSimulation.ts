import { useState } from "react";
import axios from "axios";
import type { MetricItem, SweepRequest, SweepResponse, StrategyInfo } from "../types";

const API = axios.create({ baseURL: "/api" });

export function useSimulation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MetricItem[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([
    { name: "calldata", label: "Calldata", description: "" },
    { name: "compressed", label: "Compressed", description: "" },
    { name: "external", label: "External DA", description: "" },
  ]);

  const fetchStrategies = async () => {
    try {
      const res = await API.get<StrategyInfo[]>("/strategies");
      setStrategies(res.data);
    } catch {
      // use defaults
    }
  };

  const runSweep = async (params: SweepRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await API.post<SweepResponse>("/sweep", params);
      setResults(res.data.results);
    } catch (e: unknown) {
      if (axios.isAxiosError(e) && e.response?.data?.detail) {
        const detail = e.response.data.detail;
        const msg = Array.isArray(detail)
          ? detail.map((d: { msg: string }) => d.msg).join("; ")
          : JSON.stringify(detail);
        setError(msg);
      } else {
        setError("Failed to run simulation. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  };

  return { loading, error, results, strategies, fetchStrategies, runSweep };
}
