import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Markdown } from "./markdown";

afterEach(cleanup);

describe("Markdown", () => {
  it("renders headers, bold text, lists, rules and code blocks", () => {
    const content = [
      "# Report",
      "",
      "A **bold** statement.",
      "",
      "- first",
      "- second",
      "",
      "---",
      "",
      "```",
      "port 22 open",
      "```",
    ].join("\n");

    const { container } = render(<Markdown content={content} />);

    expect(container.querySelector("h1")?.textContent).toBe("Report");
    expect(container.querySelector("strong")?.textContent).toBe("bold");
    expect(container.querySelectorAll("li")).toHaveLength(2);
    expect(container.querySelector("hr")).not.toBeNull();
    expect(container.querySelector("pre")?.textContent).toContain("port 22 open");
  });

  it("renders a horizontal rule after a paragraph", () => {
    const { container } = render(<Markdown content={"intro\n---\ntail"} />);

    expect(container.querySelector("p")?.textContent).toBe("intro");
    expect(container.querySelector("hr")).not.toBeNull();
    expect(container.textContent).toContain("tail");
  });

  it("renders plain paragraphs and inline bold in list items", () => {
    const { container } = render(<Markdown content={"- risky **RDP** exposure"} />);

    expect(container.querySelector("li strong")?.textContent).toBe("RDP");
    expect(container.querySelector("li")?.textContent).toBe("risky RDP exposure");
  });
});
