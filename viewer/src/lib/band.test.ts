import { expect, test } from "vitest";
import { scoreBand } from "./band";

test.each([
  [100, "Good"],
  [80, "Good"],
  [79.9, "Needs work"],
  [50, "Needs work"],
  [49.9, "Poor"],
  [0, "Poor"],
])("score %s is %s", (score, label) => {
  expect(scoreBand(score).label).toBe(label);
});
