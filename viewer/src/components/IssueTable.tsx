import { useState } from "react";
import { filterIssues, NO_FILTERS, type Filters, type Issue } from "../lib/filterIssues";

type Props = {
  issues: Issue[];
  issueCounts: Record<string, number>;
};

const SEVERITY_STYLE = {
  error: "text-red-800",
  warning: "text-amber-800",
  info: "text-gray-700",
};

const fmt = (n: number) => n.toLocaleString("en-US");
const SEVERITIES: Filters["severity"][] = ["all", "error", "warning", "info"];

// Every cell is a plain React text node: file names and details come from an untrusted report.
export default function IssueTable({ issues, issueCounts }: Props) {
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const rows = filterIssues(issues, filters);
  const total = Object.values(issueCounts).reduce((sum, n) => sum + n, 0);

  if (issues.length === 0) return <p className="mt-2 text-gray-700">No problems found.</p>;

  return (
    <div>
      <div className="mt-2 flex flex-wrap gap-4 text-sm">
        <label>
          Severity{" "}
          <select
            className="rounded border border-gray-400 px-2 py-1"
            value={filters.severity}
            onChange={(event) =>
              setFilters({ ...filters, severity: event.target.value as Filters["severity"] })
            }
          >
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "All" : s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Type{" "}
          <select
            className="rounded border border-gray-400 px-2 py-1"
            value={filters.type}
            onChange={(event) => setFilters({ ...filters, type: event.target.value })}
          >
            <option value="all">All</option>
            {Object.entries(issueCounts)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([type, count]) => (
                <option key={type} value={type}>
                  {type} ({fmt(count)})
                </option>
              ))}
          </select>
        </label>
        <label>
          File{" "}
          <input
            type="search"
            className="rounded border border-gray-400 px-2 py-1"
            value={filters.file}
            onChange={(event) => setFilters({ ...filters, file: event.target.value })}
          />
        </label>
      </div>

      <p className="mt-3 text-sm text-gray-700" aria-live="polite">
        Showing {fmt(rows.length)} of {fmt(issues.length)} issues in this report.
        {total > issues.length && ` The report was capped; the real total is ${fmt(total)}.`}
      </p>

      {rows.length === 0 ? (
        <p className="mt-2 text-gray-700">No issues match these filters.</p>
      ) : (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Issues found in the dataset</caption>
            <thead>
              <tr className="border-b border-gray-300">
                <th scope="col" className="py-1 pr-4">Severity</th>
                <th scope="col" className="py-1 pr-4">Type</th>
                <th scope="col" className="py-1 pr-4">File</th>
                <th scope="col" className="py-1">Detail</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((issue, index) => (
                <tr key={index} className="border-b border-gray-200 align-top">
                  <td className={`py-1 pr-4 font-semibold uppercase ${SEVERITY_STYLE[issue.severity]}`}>
                    {issue.severity}
                  </td>
                  <td className="py-1 pr-4">{issue.type}</td>
                  <td className="py-1 pr-4 break-all">{issue.file}</td>
                  <td className="py-1">{issue.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
