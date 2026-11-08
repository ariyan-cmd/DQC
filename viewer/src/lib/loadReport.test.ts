import { describe, expect, test } from "vitest";
import sample from "../../public/sample-report.json";
import { MAX_REPORT_BYTES, parseReport, readReportFile } from "./loadReport";

const sampleText = JSON.stringify(sample);

describe("parseReport", () => {
  test("accepts a valid report", () => {
    const result = parseReport(sampleText);
    expect(result.ok && result.report.dataset.name).toBe("sample-dataset");
  });

  test("explains invalid JSON", () => {
    expect(parseReport("{nope")).toEqual({ ok: false, error: "This file is not valid JSON." });
  });

  test("explains JSON that is not a report", () => {
    const result = parseReport('{"hello": 1}');
    expect(!result.ok && result.error).toContain("does not look like a dsc report");
  });

  test("explains an unsupported schema version without echoing it", () => {
    const result = parseReport(JSON.stringify({ ...sample, schema_version: "<b>99</b>" }));
    expect(!result.ok && result.error).toContain("schema version");
    expect(!result.ok && result.error).not.toContain("99");
  });
});

describe("readReportFile", () => {
  test("reads a valid file", async () => {
    const result = await readReportFile(new File([sampleText], "report.json"));
    expect(result.ok).toBe(true);
  });

  test("refuses a file over the size limit without reading it", async () => {
    const file = new File(["{}"], "big.json");
    Object.defineProperty(file, "size", { value: MAX_REPORT_BYTES + 1 });
    const result = await readReportFile(file);
    expect(!result.ok && result.error).toContain("too large");
  });
});
