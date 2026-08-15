import { useEffect, useState } from "react";
import { get } from "../api";

/** Overview — Health + SLO + Security + Contract summary (M10-F7). */

export interface OverviewData {
  health_score: number;
  slo_release_ready: boolean;
  security_blocking: boolean;
  contract_breaking: number;
  contract_warnings?: number;
  slo_failures?: string[];
  security_failures?: string[];
}

export function Overview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get<OverviewData>("/m10/overview")
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p>Loading…</p>;

  const slo = data.slo_release_ready ? "READY" : "NOT READY";
  const sec = data.security_blocking ? "BLOCKED" : "SECURE";
  const contract = data.contract_breaking === 0 ? "clean" : `breaking=${data.contract_breaking}`;

  return (
    <div data-testid="overview">
      <h3>AIOS 1.0 Overview</h3>
      <div className="card">
        Health: <strong>{data.health_score}/100</strong>
      </div>
      <div className="card" data-testid="overview-slo">
        SLO Release Gate: <strong>{slo}</strong>
        {data.slo_failures?.length ? ` (${data.slo_failures.join(", ")})` : ""}
      </div>
      <div className="card" data-testid="overview-security">
        Security Baseline: <strong>{sec}</strong>
        {data.security_failures?.length ? ` (${data.security_failures.join(", ")})` : ""}
      </div>
      <div className="card" data-testid="overview-contract">
        Contracts: <strong>{contract}</strong> ({data.contract_warnings ?? 0} warnings)
      </div>
    </div>
  );
}
