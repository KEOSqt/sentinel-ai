import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet, type Finding } from "@/lib/api";
import FindingsPage from "./page";

vi.mock("next/navigation", () => ({
  usePathname: () => "/findings",
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    onClick,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a
      href={href}
      onClick={(event) => {
        event.preventDefault();
        onClick?.(event);
      }}
      {...props}
    />
  ),
}));

vi.mock("@/lib/api", () => ({
  apiGet: vi.fn(),
}));

const finding: Finding = {
  id: "finding-1",
  title: "Example finding",
  description: "",
  severity: "HIGH",
  risk_score: 8,
  confidence: "high",
  evidence: [],
  rationale: "",
  remediation: "",
  references: [],
  status: "open",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("FindingsPage filters", () => {
  it.each([
    ["All", "/findings?status=null"],
    ["Open", "/findings?status=open"],
    ["Acknowledged", "/findings?status=acknowledged"],
    ["Resolved", "/findings?status=resolved"],
  ])(
    "keeps findings visible when clicking the active %s filter",
    async (label, url) => {
      window.history.replaceState({}, "", url);
      vi.mocked(apiGet).mockResolvedValue({ ok: true, data: [finding] });

      render(<FindingsPage />);
      await screen.findByText("Example finding");

      fireEvent.click(screen.getByRole("link", { name: label }));

      expect(screen.getByText("Example finding")).toBeTruthy();
      expect(document.querySelector(".animate-pulse")).toBeNull();
    },
  );
});
