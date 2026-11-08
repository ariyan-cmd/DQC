import { expect, test } from "vitest";
import { filterIssues, NO_FILTERS, type Issue } from "./filterIssues";

const make = (type: string, severity: Issue["severity"], file: string): Issue => ({
  type,
  severity,
  section: "Files",
  file,
  detail: "d",
});

const issues = [
  make("tiny_resolution", "warning", "images/Tiny.png"),
  make("empty_label", "info", "labels/a.txt"),
  make("corrupt_image", "error", "images/bad.png"),
  make("zero_size_box", "error", "labels/zero.txt"),
];

const files = (list: Issue[]) => list.map((i) => i.file);

test("no filters keeps everything, errors first, scan order kept within a severity", () => {
  expect(files(filterIssues(issues, NO_FILTERS))).toEqual([
    "images/bad.png",
    "labels/zero.txt",
    "images/Tiny.png",
    "labels/a.txt",
  ]);
});

test("filters by severity", () => {
  expect(files(filterIssues(issues, { ...NO_FILTERS, severity: "error" }))).toEqual([
    "images/bad.png",
    "labels/zero.txt",
  ]);
});

test("filters by type", () => {
  expect(files(filterIssues(issues, { ...NO_FILTERS, type: "empty_label" }))).toEqual(["labels/a.txt"]);
});

test("file search ignores case and surrounding spaces", () => {
  expect(files(filterIssues(issues, { ...NO_FILTERS, file: "  TINY " }))).toEqual(["images/Tiny.png"]);
});

test("filters combine, and can match nothing", () => {
  expect(files(filterIssues(issues, { severity: "error", type: "corrupt_image", file: "images" }))).toEqual([
    "images/bad.png",
  ]);
  expect(filterIssues(issues, { severity: "info", type: "corrupt_image", file: "" })).toEqual([]);
});

test("does not change the list it is given", () => {
  const copy = [...issues];
  filterIssues(issues, NO_FILTERS);
  expect(issues).toEqual(copy);
});
