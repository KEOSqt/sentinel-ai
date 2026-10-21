"use client";

import { useEffect, useState } from "react";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type ApiError, type Scan } from "@/lib/api";
import { PageSkeleton } from "@/lib/ui";
import ReportsPanel from "@/components/reports-panel";

export default function ReportsPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reports, setReports] = useState<{ id: string; scan_id: string; created_at?: string | null }[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [scansResult, reportsResult] = await Promise.all([
        apiGet<Scan[]>("/api/v1/scans"),
        apiGet<{ id: string; scan_id: string; created_at?: string | null }[]>("/api/v1/reports"),
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
  }, []);

  if (loading) {
    return <PageSkeleton />;
  }

  if (error !== null) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Reports</h1>
        <ApiErrorState errors={[error]} />
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
