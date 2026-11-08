import { ReportSchema, type Report } from "../schema";

// A real report is a few hundred KB at most (the engine caps issues per type).
export const MAX_REPORT_BYTES = 5 * 1024 * 1024;

export type LoadFailure = { ok: false; error: string; hint: string };
export type LoadResult = { ok: true; report: Report } | LoadFailure;

// Messages are fixed strings: nothing from the untrusted file is echoed back.
const fail = (error: string, hint: string): LoadFailure => ({ ok: false, error, hint });

const MAKE_ONE = "Choose the report.json written by `dsc check`, or load the sample report.";

export function parseReport(text: string): LoadResult {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    return fail("This file is not valid JSON.", MAKE_ONE);
  }
  const result = ReportSchema.safeParse(data);
  if (result.success) return { ok: true, report: result.data };
  if (typeof data === "object" && data !== null && "schema_version" in data && data.schema_version !== "1") {
    return fail(
      "This report uses a schema version this viewer does not support.",
      "Create it again with the version of dsc that matches this viewer.",
    );
  }
  return fail("This file does not look like a dsc report.json.", MAKE_ONE);
}

export async function readReportFile(file: File): Promise<LoadResult> {
  if (file.size > MAX_REPORT_BYTES) {
    return fail(
      `This file is too large to be a report (over ${MAX_REPORT_BYTES / 1024 / 1024} MB).`,
      "Check that you chose report.json and not the dataset itself.",
    );
  }
  try {
    return parseReport(await file.text());
  } catch {
    return fail("Could not read that file.", "Try choosing it again.");
  }
}
