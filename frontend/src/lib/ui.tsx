const COLORS: Record<string, string> = {
  CRITICAL: "bg-red-500/20 text-red-300 border-red-500/40",
  HIGH: "bg-orange-500/20 text-orange-300 border-orange-500/40",
  MEDIUM: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  LOW: "bg-sky-500/20 text-sky-300 border-sky-500/40",
  INFO: "bg-slate-500/20 text-slate-300 border-slate-500/40",
};

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${COLORS[severity] ?? COLORS.INFO}`}>
      {severity}
    </span>
  );
}

const STATUS_COLORS: Record<string, string> = {
  open: "bg-sky-500/20 text-sky-300 border-sky-500/40",
  acknowledged: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  resolved: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[status] ?? STATUS_COLORS.open}`}>
      {status}
    </span>
  );
}

export function Card({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}

/**
 * Rendered only when a request genuinely succeeded and the backend reported no
 * records. Backend failures use `ApiErrorState` instead, so these two states
 * never get confused.
 */
export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-800 bg-slate-900/40 px-4 py-8 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {hint && <p className="mx-auto mt-1 max-w-md text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

function SkeletonBlock({ className }: { className: string }) {
  return <div className={`animate-pulse rounded bg-slate-800/80 ${className}`} />;
}

export function CardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          <SkeletonBlock className="h-3 w-24" />
          <SkeletonBlock className="mt-2 h-7 w-16" />
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-2" aria-hidden>
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className="flex gap-4 border-t border-slate-800 py-2">
          {Array.from({ length: columns }, (_, c) => (
            <SkeletonBlock key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="space-y-6">
      <SkeletonBlock className="h-7 w-56" />
      <CardSkeleton />
      <TableSkeleton />
    </div>
  );
}