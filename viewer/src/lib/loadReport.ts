import { ReportSchema, type Report } from "../schema";

export const MAX_REPORT_BYTES = 20 * 1024 * 1024;

export type LoadResult = { ok: true; report: Report } | { ok: false; error: string };

const fail = (error: string): LoadResult => ({ ok: false, error });

export function parseReport(text: string): LoadResult {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    return fail("This file is not valid JSON.");
  }
  const result = ReportSchema.safeParse(data);
  if (result.success) return { ok: true, report: result.data };
  // The version is not echoed back: it comes from an untrusted file.
  if (typeof data === "object" && data !== null && "schema_version" in data && data.schema_version !== "1") {
    return fail("This report uses a schema version this viewer does not support.");
  }
  return fail("This file does not look like a dsc report.json.");
}

export async function readReportFile(file: File): Promise<LoadResult> {
  if (file.size > MAX_REPORT_BYTES) return fail("This file is too large to be a report (over 20 MB).");
  try {
    return parseReport(await file.text());
  } catch {
    return fail("Could not read that file.");
  }
}
