const API_URL = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Backend requests are aborted after this many milliseconds so a hung backend
 * surfaces as an error state instead of a page that never finishes loading.
 */
const REQUEST_TIMEOUT_MS = 10_000;

export type ApiErrorKind = "network" | "timeout" | "http" | "parse";

export type ApiError = {
  kind: ApiErrorKind;
  /** Human-readable, safe to render in the UI. */
  message: string;
  /** HTTP status code, when the request reached the backend. */
  status?: number;
};

/**
 * Every request resolves to a result rather than throwing. This keeps "the
 * backend is down" distinguishable from "the backend returned an empty list",
 * which callers must render differently.
 */
export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiError };

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

function isTimeout(err: unknown): boolean {
  return err instanceof Error && err.name === "TimeoutError";
}

async function describeHttpError(res: Response, path: string): Promise<string> {
  const fallback = `${path} responded with ${res.status} ${res.statusText}`.trim();
  try {
    const body: unknown = await res.json();
    if (body !== null && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string" && detail.length > 0) return `${res.status}: ${detail}`;
      // FastAPI validation errors arrive as a list of {loc, msg, type}.
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: unknown };
        if (typeof first?.msg === "string") return `${res.status}: ${first.msg}`;
      }
    }
  } catch {
    // Body was not JSON; fall through to the generic message.
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      cache: "no-store",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    const timedOut = isTimeout(err);
    return {
      ok: false,
      error: {
        kind: timedOut ? "timeout" : "network",
        message: timedOut
          ? `No response from the backend within ${REQUEST_TIMEOUT_MS / 1000}s.`
          : `Could not reach the Sentinel-AI backend at ${API_URL}.`,
      },
    };
  }

  if (!res.ok) {
    return {
      ok: false,
      error: { kind: "http", status: res.status, message: await describeHttpError(res, path) },
    };
  }

  try {
    return { ok: true, data: (await res.json()) as T };
  } catch {
    return {
      ok: false,
      error: {
        kind: "parse",
        status: res.status,
        message: `The backend returned a malformed JSON response for ${path}.`,
      },
    };
  }
}

export async function apiGet<T>(path: string): Promise<ApiResult<T>> {
  return request<T>(path);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return request<T>(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export type Asset = {
  id: string;
  ip: string;
  hostname?: string | null;
  os?: string | null;
  exposure: string;
  services: { port: number; protocol: string; service: string; product?: string | null; version?: string | null; state: string }[];
};

export type FindingStatus = "open" | "acknowledged" | "resolved";

export type Finding = {
  id: string;
  scan_id?: string;
  title: string;
  description: string;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  confidence: string;
  asset?: Asset | null;
  affected_service?: { port: number; protocol: string; service: string; version?: string | null } | null;
  evidence: { source: string; evidence_type: string; data: Record<string, unknown> }[];
  rationale: string;
  remediation: string;
  references: string[];
  status: FindingStatus;
  triage_note?: string;
  triaged_at?: string | null;
  vulnerabilities?: { id: string; title: string; severity: string; cvss?: number | null }[];
  ai_analysis?: {
    summary: string;
    risk_assessment: string;
    priority_findings: string[];
    attack_paths: string[];
    recommendations: string[];
    missing_information: string[];
  } | null;
};

export type Scan = {
  id: string;
  source: string;
  filename?: string | null;
  status: string;
  created_at?: string | null;
  asset_count: number;
  finding_count: number;
};

/** Metadata-only entry as returned by GET /api/v1/reports. */
export type ReportSummary = {
  id: string;
  scan_id: string;
  created_at?: string | null;
};

/** Full report, as returned by GET /api/v1/reports/{id} and POST /api/v1/reports. */
export type Report = ReportSummary & {
  content: string;
};