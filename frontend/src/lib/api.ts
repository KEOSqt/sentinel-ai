const API_URL = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export type Asset = {
  id: string;
  ip: string;
  hostname?: string | null;
  os?: string | null;
  exposure: string;
  services: { port: number; protocol: string; service: string; product?: string | null; version?: string | null; state: string }[];
};

export type Finding = {
  id: string;
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
  status: string;
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
