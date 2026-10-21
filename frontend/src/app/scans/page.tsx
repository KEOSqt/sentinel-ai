"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type ApiError, type Scan } from "@/lib/api";
import { EmptyState, PageSkeleton } from "@/lib/ui";

export default function ScansPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const result = await apiGet<Scan[]>("/api/v1/scans");
      if (cancelled) return;
      if (!result.ok) {
        setError(result.error);
      } else {
        setScans(result.data);
      }
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
        <h1 className="text-2xl font-semibold text-white">Scans</h1>
        <ApiErrorState errors={[error]} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Scans</h1>
      {scans.length === 0 ? (
        <EmptyState
          title="No scans yet"
          hint="Upload an Nmap XML file on the Scan page to populate this list."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="sr-only">All scans, newest first</caption>
            <thead>
              <tr className="text-left text-slate-500">
                <th scope="col" className="pb-2">File</th>
                <th scope="col" className="pb-2">Status</th>
                <th scope="col" className="pb-2">Assets</th>
                <th scope="col" className="pb-2">Findings</th>
                <th scope="col" className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="border-t border-slate-800">
                  <td className="py-2 text-slate-200">
                    <Link className="text-sky-400 hover:underline" href={`/scans/${s.id}`}>
                      {s.filename ?? s.id.slice(0, 8)}
                    </Link>
                    <span className="ml-2 font-mono text-xs text-slate-500">{s.id.slice(0, 8)}</span>
                  </td>
                  <td className="py-2">{s.status}</td>
                  <td className="py-2">{s.asset_count}</td>
                  <td className="py-2">{s.finding_count}</td>
                  <td className="py-2 text-slate-500">
                    {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
