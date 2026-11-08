import { z } from "zod";

// Mirrors schema/report.schema.json. report.json is untrusted input, so nothing is shown
// until it passes this schema; schema.test.ts fails if the field names drift apart.
const Severity = z.enum(["error", "warning", "info"]);
const Count = z.number().int().nonnegative();

const Issue = z.object({
  type: z.string(),
  severity: Severity,
  section: z.string(),
  file: z.string(),
  detail: z.string(),
});

const Section = z.object({
  name: z.string(),
  score: z.number().min(0).max(100),
  reason: z.string(),
  issue_count: Count,
});

export const ReportSchema = z.object({
  schema_version: z.literal("1"),
  dataset: z.object({
    name: z.string(),
    num_images: Count,
    num_labels: Count,
    classes: z.array(z.string()),
    splits: z.array(z.string()),
  }),
  score: z.object({
    overall: z.number().min(0).max(100),
    weights: z.record(z.string(), z.number()),
  }),
  sections: z.array(Section),
  issues: z.array(Issue),
  issue_counts: z.record(z.string(), Count),
  stats: z.object({
    box_size_histogram: z.record(z.string(), Count),
    tiny_box_ratio: z.number().min(0).max(1),
    blur_summary: z.record(z.string(), z.number()),
  }),
});

export type Report = z.infer<typeof ReportSchema>;
export { Issue as IssueSchema, Section as SectionSchema };
