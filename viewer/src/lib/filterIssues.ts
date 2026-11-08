import type { Report } from "../schema";

export type Issue = Report["issues"][number];
export type Filters = { severity: "all" | Issue["severity"]; type: string; file: string };

export const NO_FILTERS: Filters = { severity: "all", type: "all", file: "" };

const SEVERITY_ORDER = { error: 0, warning: 1, info: 2 };

// Errors first; Array.sort is stable, so scan order is kept within a severity.
export function filterIssues(issues: Issue[], filters: Filters): Issue[] {
  const needle = filters.file.trim().toLowerCase();
  return issues
    .filter(
      (issue) =>
        (filters.severity === "all" || issue.severity === filters.severity) &&
        (filters.type === "all" || issue.type === filters.type) &&
        issue.file.toLowerCase().includes(needle),
    )
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
}
