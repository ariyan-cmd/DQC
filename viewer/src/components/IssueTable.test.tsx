import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import sample from "../../public/sample-report.json";
import { ReportSchema } from "../schema";
import IssueTable from "./IssueTable";

afterEach(cleanup);

const { issues, issue_counts } = ReportSchema.parse(sample);
const body = () => screen.getAllByRole("row").slice(1); // drop the header row

test("lists every issue, errors first", () => {
  render(<IssueTable issues={issues} issueCounts={issue_counts} />);
  expect(body()).toHaveLength(issues.length);
  expect(body()[0]!.textContent).toContain("error");
  expect(screen.getByRole("table", { name: "Issues found in the dataset" })).toBeTruthy();
});

test("the severity filter narrows the rows", () => {
  render(<IssueTable issues={issues} issueCounts={issue_counts} />);
  fireEvent.change(screen.getByLabelText("Severity"), { target: { value: "info" } });
  const infoCount = issues.filter((i) => i.severity === "info").length;
  expect(body()).toHaveLength(infoCount);
  expect(screen.getByText(`Showing ${infoCount} of ${issues.length} issues`, { exact: false })).toBeTruthy();
});

test("the type filter shows true counts and narrows the rows", () => {
  render(<IssueTable issues={issues} issueCounts={issue_counts} />);
  expect(screen.getByRole("option", { name: "missing_label (4)" })).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Type"), { target: { value: "missing_label" } });
  expect(body()).toHaveLength(4);
});

test("the file search narrows the rows, and no match says so", () => {
  render(<IssueTable issues={issues} issueCounts={issue_counts} />);
  fireEvent.change(screen.getByLabelText("File"), { target: { value: "no-such-file" } });
  expect(screen.getByText("No issues match these filters.")).toBeTruthy();
  expect(screen.queryByRole("table")).toBeNull();
});

test("says when the report was capped", () => {
  render(<IssueTable issues={issues} issueCounts={{ missing_label: 4213 }} />);
  expect(screen.getByText("The report was capped; the real total is 4,213.", { exact: false })).toBeTruthy();
});

test("no issues says so instead of showing an empty table", () => {
  render(<IssueTable issues={[]} issueCounts={{}} />);
  expect(screen.getByText("No problems found.")).toBeTruthy();
  expect(screen.queryByRole("table")).toBeNull();
});
