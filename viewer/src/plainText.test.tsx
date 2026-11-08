import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import sample from "../public/sample-report.json";
import ReportSummary from "./components/ReportSummary";
import { ReportSchema } from "./schema";

afterEach(cleanup);

// report.json is untrusted: every value must reach the page as text, never as markup.
const hostile = '<img src=x onerror="alert(1)"><script>alert(2)</script>';

test("hostile values in a report are shown as text, not turned into elements", () => {
  const base = ReportSchema.parse(sample);
  const report = {
    ...base,
    dataset: { ...base.dataset, name: hostile },
    sections: base.sections.map((s) => ({ ...s, name: hostile + s.name, reason: hostile })),
    issues: base.issues.map((i) => ({ ...i, type: hostile, file: hostile, detail: hostile })),
    issue_counts: { [hostile]: base.issues.length },
  };
  const { container } = render(<ReportSummary report={report} onReset={() => {}} />);

  expect(container.querySelector("img, script")).toBeNull();
  expect(container.innerHTML).not.toContain("<img");
  expect(container.innerHTML).toContain("&lt;img");
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(hostile);
  expect(screen.getAllByText(hostile).length).toBeGreaterThan(base.issues.length);
});

const sources = import.meta.glob<string>(["/src/**/*.{ts,tsx}", "!/src/**/*.test.{ts,tsx}"], {
  query: "?raw",
  import: "default",
  eager: true,
});

test("no source file can inject HTML", () => {
  const files = Object.entries(sources);
  expect(files.length).toBeGreaterThan(5); // the glob really found the source files
  for (const [path, code] of files) {
    expect(code, path).not.toMatch(/dangerouslySetInnerHTML|\.innerHTML|insertAdjacentHTML/);
  }
});
