import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import sample from "../../public/sample-report.json";
import { ReportSchema } from "../schema";
import Histogram from "./Histogram";

afterEach(cleanup);

const { stats } = ReportSchema.parse(sample);

test("shows every bucket with its count as text, in order", () => {
  render(<Histogram stats={stats} />);
  const rows = screen.getAllByRole("listitem").map((li) => li.textContent);
  expect(rows).toEqual(Object.entries(stats.box_size_histogram).map(([l, n]) => `${l} px${n}`));
});

test("bar widths are relative to the biggest bucket", () => {
  const { container } = render(
    <Histogram stats={{ ...stats, box_size_histogram: { "<8": 5, "8-16": 10 } }} />,
  );
  const widths = [...container.querySelectorAll<HTMLElement>("li span[style]")].map((e) => e.style.width);
  expect(widths).toEqual(["50%", "100%"]);
});

test("shows the tiny-box percentage and the blur summary", () => {
  render(
    <Histogram
      stats={{
        ...stats,
        box_size_histogram: { "<8": 1, "96+": 3 },
        tiny_box_ratio: 0.25,
        small_box_ratio: 0.5,
        blur_summary: { boxes_measured: 4, blurry_ratio: 0.5 },
      }}
    />,
  );
  expect(screen.getByText("Tiny boxes: 25% of 4 (this sets the score).")).toBeTruthy();
  expect(screen.getByText("Small boxes (COCO: under 32 px): 50%, shown but not scored.")).toBeTruthy();
  expect(screen.getByText("Blur: 4 boxes measured, 50% look blurry (a hint, not scored).")).toBeTruthy();
});

test("a report without blur numbers just omits that line", () => {
  render(<Histogram stats={{ ...stats, blur_summary: {} }} />);
  expect(screen.queryByText(/Blur:/)).toBeNull();
});

test("no boxes says so instead of drawing empty bars", () => {
  render(<Histogram stats={{ ...stats, box_size_histogram: { "<8": 0, "96+": 0 } }} />);
  expect(screen.getByText("No boxes were measured.")).toBeTruthy();
  expect(screen.queryByRole("list")).toBeNull();
});
