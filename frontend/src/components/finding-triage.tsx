"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPatch, type Finding, type FindingStatus } from "@/lib/api";
import { StatusBadge } from "@/lib/ui";

const OPTIONS: { value: FindingStatus; label: string }[] = [
  { value: "open", label: "Open" },
  { value: "acknowledged", label: "Acknowledged" },
  { value: "resolved", label: "Resolved" },
];

/**
 * Rendered with `key={finding.id}` so navigating between two findings remounts
 * this component with fresh state instead of needing an effect to re-seed it.
 */
export function FindingTriage({
  findingId,
  initialStatus,
  initialNote,
}: {
  findingId: string;
  initialStatus: FindingStatus;
  initialNote: string;
}) {
  const router = useRouter();
  const [note, setNote] = useState(initialNote);
  const [status, setStatus] = useState<FindingStatus>(initialStatus);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function save(nextStatus: FindingStatus) {
    const previous = status;
    setStatus(nextStatus);
    setSaving(true);
    setError("");

    const result = await apiPatch<Finding>(`/api/v1/findings/${findingId}`, {
      status: nextStatus,
      note,
    });

    if (!result.ok) {
      setStatus(previous);
      setError(result.error.message);
    } else {
      // Pull the server's view back in, since status and triage are rendered
      // by the server component.
      router.refresh();
    }
    setSaving(false);
  }

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <h2 className="text-lg font-medium text-white">Triage</h2>
        <StatusBadge status={status} />
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => save(option.value)}
            disabled={saving || status === option.value}
            aria-pressed={status === option.value}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-60 ${
              status === option.value
                ? "border-sky-500/60 bg-sky-500/20 text-sky-200"
                : "border-slate-700 text-slate-300 hover:border-slate-500"
            }`}
          >
            {option.label}
          </button>
        ))}
        {saving && <span className="self-center text-xs text-slate-500">Saving…</span>}
      </div>

      <div className="space-y-1">
        <label htmlFor="triage-note" className="block text-xs uppercase tracking-wide text-slate-500">
          Note
        </label>
        <textarea
          id="triage-note"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="Ticket reference, owner, or why this was triaged"
          className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
        />
        <button
          type="button"
          onClick={() => save(status)}
          disabled={saving}
          className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          Save note
        </button>
      </div>

      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </section>
  );
}