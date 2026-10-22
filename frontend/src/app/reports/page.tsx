"use client";

import { useEffect, useState } from "react";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type ApiError, type ReportSummary, type Scan } from "@/lib/api";
import { useRetry } from "@/lib/use-retry";
import { PageSkeleton } from "@/lib/ui";
import ReportsPanel from "@/components/reports-panel";

export default function ReportsPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const { attempt, retry } = useRetry();

  function handleRetry() {
    setLoading(true);
    setError(null);
    retry();
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [scansResult, reportsResult] = await Promise.all([
        apiGet<Scan[]>("/api/v1/scans"),
        apiGet<ReportSummary[]>("/api/v1/reports"),
      ]);
      if (cancelled) return;
      if (!scansResult.ok) {
        setError(scansResult.error);
        setLoading(false);
        return;
      }
      if (!reportsResult.ok) {
        setError(reportsResult.error);
        setLoading(false);
        return;
      }
      setScans(scansResult.data);
      setReports(reportsResult.data);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  if (loading) {
    return <PageSkeleton />;
  }

  if (error !== null) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Reports</h1>
        <ApiErrorState errors={[error]} onRetry={handleRetry} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Reports</h1>
      <ReportsPanel initialReports={reports} scans={scans} />
    </div>
  );
}
