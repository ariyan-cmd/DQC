import { useState } from "react";
import Landing from "./components/Landing";
import ReportSummary from "./components/ReportSummary";
import { parseReport, readReportFile, type LoadFailure, type LoadResult } from "./lib/loadReport";
import type { Report } from "./schema";

export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<LoadFailure | null>(null);

  const show = (result: LoadResult) => {
    setError(result.ok ? null : result);
    if (result.ok) setReport(result.report);
  };

  const loadSample = async () => {
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}sample-report.json`);
      if (!response.ok) throw new Error("sample not found");
      show(parseReport(await response.text()));
    } catch {
      setError({
        ok: false,
        error: "Could not load the sample report.",
        hint: "Check your connection and try again, or choose a report.json file.",
      });
    }
  };

  if (report) return <ReportSummary report={report} onReset={() => setReport(null)} />;
  return (
    <Landing
      error={error}
      onSample={loadSample}
      onFile={async (file) => show(await readReportFile(file))}
    />
  );
}
