import { useState } from "react";
import Landing from "./components/Landing";
import { parseReport, readReportFile, type LoadResult } from "./lib/loadReport";
import type { Report } from "./schema";

export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  const show = (result: LoadResult) => {
    setError(result.ok ? null : result.error);
    if (result.ok) setReport(result.report);
  };

  const loadSample = async () => {
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}sample-report.json`);
      if (!response.ok) throw new Error("sample not found");
      show(parseReport(await response.text()));
    } catch {
      setError("Could not load the sample report.");
    }
  };

  // Summary screen arrives in the next commit.
  if (report) return <main className="p-8">{report.dataset.name}</main>;
  return (
    <Landing
      error={error}
      onSample={loadSample}
      onFile={async (file) => show(await readReportFile(file))}
    />
  );
}
