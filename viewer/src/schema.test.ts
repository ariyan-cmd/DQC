import { describe, expect, test } from "vitest";
import jsonSchema from "../../schema/report.schema.json";
import sample from "../public/sample-report.json";
import { IssueSchema, ReportSchema, SectionSchema } from "./schema";

const keys = (shape: object) => Object.keys(shape).sort();
const props = (def: { properties: object }) => Object.keys(def.properties).sort();

describe("report schema", () => {
  test("the committed sample report is valid", () => {
    expect(ReportSchema.safeParse(sample).success).toBe(true);
  });

  test("field names match the engine's schema/report.schema.json", () => {
    const { $defs } = jsonSchema;
    expect(keys(ReportSchema.shape)).toEqual(props(jsonSchema));
    expect(keys(ReportSchema.shape.dataset.shape)).toEqual(props($defs.DatasetInfo));
    expect(keys(ReportSchema.shape.score.shape)).toEqual(props($defs.Score));
    expect(keys(ReportSchema.shape.stats.shape)).toEqual(props($defs.Stats));
    expect(keys(SectionSchema.shape)).toEqual(props($defs.Section));
    expect(keys(IssueSchema.shape)).toEqual(props($defs.Issue));
    expect(IssueSchema.shape.severity.options).toEqual($defs.Issue.properties.severity.enum);
  });

  test.each([
    ["a missing field", { ...sample, dataset: undefined }],
    ["a score above 100", { ...sample, score: { ...sample.score, overall: 150 } }],
    ["a negative issue count", { ...sample, issue_counts: { corrupt_image: -1 } }],
    ["a different schema version", { ...sample, schema_version: "2" }],
    [
      "an unknown severity",
      { ...sample, issues: [{ ...sample.issues[0], severity: "fatal" }] },
    ],
    ["a non-object", "hello"],
  ])("rejects %s", (_name, value) => {
    expect(ReportSchema.safeParse(value).success).toBe(false);
  });
});
