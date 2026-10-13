import { ApiErrorState } from "@/components/api-error-state";
import { ReportsPanel } from "@/components/reports-panel";
import { apiGet, type ReportSummary } from "@/lib/api";

export default async function ReportsPage() {
  const result = await apiGet<ReportSummary[]>("/api/v1/reports");

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Reports</h1>
        <ApiErrorState errors={[result.error]} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Reports</h1>
      <ReportsPanel initialReports={result.data} />
    </div>
  );
}