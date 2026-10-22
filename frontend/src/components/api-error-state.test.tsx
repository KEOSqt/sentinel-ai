import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiErrorState } from "./api-error-state";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

afterEach(cleanup);

describe("ApiErrorState", () => {
  it("calls the provided retry callback", () => {
    const retry = vi.fn();

    render(<ApiErrorState errors={[{ kind: "network", message: "backend down" }]} onRetry={retry} />);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(retry).toHaveBeenCalledOnce();
  });

  it("shows every error message", () => {
    render(
      <ApiErrorState
        errors={[
          { kind: "network", message: "assets failed" },
          { kind: "http", status: 500, message: "scans failed" },
        ]}
      />
    );

    expect(screen.getByText(/assets failed/)).toBeTruthy();
    expect(screen.getByText(/scans failed/)).toBeTruthy();
  });
});
