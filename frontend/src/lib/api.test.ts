import { afterEach, describe, expect, it, vi } from "vitest";
import { apiDelete, apiGet, apiUpload } from "./api";

function response(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: async () => body,
  };
}

function stubFetch(impl: (input: RequestInfo | URL, init?: RequestInit) => Promise<unknown>) {
  const mock = vi.fn(impl);
  vi.stubGlobal("fetch", mock);
  return mock;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("apiGet", () => {
  it("returns parsed data on success", async () => {
    stubFetch(async () => response({ value: 42 }));

    const result = await apiGet<{ value: number }>("/api/v1/test");

    expect(result).toEqual({ ok: true, data: { value: 42 } });
  });

  it("surfaces the backend detail for HTTP errors", async () => {
    stubFetch(async () => response({ detail: "Report not found" }, 404));

    const result = await apiGet("/api/v1/reports/missing");

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error).toEqual({
      kind: "http",
      status: 404,
      message: "404: Report not found",
    });
  });

  it("surfaces the first FastAPI validation message", async () => {
    stubFetch(async () => response({ detail: [{ loc: ["body"], msg: "field required" }] }, 422));

    const result = await apiGet("/api/v1/findings/nope");

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error.message).toBe("422: field required");
  });

  it("reports unreachable backends", async () => {
    stubFetch(async () => {
      throw new Error("connection refused");
    });

    const result = await apiGet("/api/v1/assets");

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error.kind).toBe("network");
    expect(result.error.message).toContain("Could not reach the Sentinel-AI backend");
  });

  it("reports timeouts distinctly from network failures", async () => {
    stubFetch(async () => {
      throw Object.assign(new Error("timed out"), { name: "TimeoutError" });
    });

    const result = await apiGet("/api/v1/assets");

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error.kind).toBe("timeout");
    expect(result.error.message).toContain("within 10s");
  });

  it("reports malformed JSON responses", async () => {
    stubFetch(async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => {
        throw new SyntaxError("bad json");
      },
    }));

    const result = await apiGet("/api/v1/assets");

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error.kind).toBe("parse");
  });
});

describe("request helpers", () => {
  it("sends uploads as FormData without a JSON content type", async () => {
    const fetchMock = stubFetch(async () => response({ scan_id: "scan-1" }));
    const form = new FormData();

    const result = await apiUpload<{ scan_id: string }>("/api/v1/evidence/nmap", form);

    expect(result).toEqual({ ok: true, data: { scan_id: "scan-1" } });
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.body).toBe(form);
    expect(init.headers).toBeUndefined();
  });

  it("sends DELETE for report removal", async () => {
    const fetchMock = stubFetch(async () => response({ detail: "Report deleted" }));

    await apiDelete("/api/v1/reports/report-1");

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("DELETE");
  });
});
