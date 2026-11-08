import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import sample from "../public/sample-report.json";
import viteConfig from "../vite.config";
import App from "./App";

const sampleText = JSON.stringify(sample);

afterEach(() => {
  cleanup(); // Vitest globals are off, so testing-library does not clean up by itself
  vi.unstubAllGlobals();
});

function stubFetch(response: Partial<Response> | Error) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => (response instanceof Error ? Promise.reject(response) : Promise.resolve(response))),
  );
}

function chooseFile(contents: string) {
  const input = screen.getByLabelText("Choose file");
  fireEvent.change(input, { target: { files: [new File([contents], "report.json")] } });
}

test("landing screen offers the sample, a file chooser and the CLI snippet", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "Dataset Readiness Checker" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Load sample report" })).toBeTruthy();
  expect(screen.getByLabelText("Choose file")).toBeTruthy();
  expect(screen.getByText(/uv run dsc check/)).toBeTruthy();
});

test("loading the sample shows the overall score and a card per section, and can go back", async () => {
  stubFetch({ ok: true, text: () => Promise.resolve(sampleText) });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Load sample report" }));
  expect(await screen.findByText(String(sample.score.overall))).toBeTruthy();
  for (const section of sample.sections) {
    expect(screen.getByRole("heading", { name: section.name })).toBeTruthy();
    expect(screen.getByText(section.reason)).toBeTruthy();
  }
  fireEvent.click(screen.getByRole("button", { name: "Load another report" }));
  expect(screen.getByRole("button", { name: "Load sample report" })).toBeTruthy();
});

test("the sample is fetched relative to the app's base path", async () => {
  stubFetch({ ok: true, text: () => Promise.resolve(sampleText) });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Load sample report" }));
  await screen.findByText(String(sample.score.overall));
  expect(fetch).toHaveBeenCalledWith(`${import.meta.env.BASE_URL}sample-report.json`);
});

test("the build is configured for the GitHub Pages path", () => {
  // Vitest overrides BASE_URL, so check the config itself; `npm run build` uses this value.
  expect(viteConfig.base).toBe("/DQC/");
});

test("a failed sample download shows a friendly error", async () => {
  stubFetch(new Error("offline"));
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Load sample report" }));
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("Could not load the sample report.");
  expect(alert.textContent).toContain("Check your connection");
});

test("a file that is not a report shows an error and stays on the landing screen", async () => {
  render(<App />);
  chooseFile('{"hello": 1}');
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("does not look like");
  expect(alert.textContent).toContain("dsc check"); // the hint tells the user what to do next
  expect(screen.getByRole("button", { name: "Load sample report" })).toBeTruthy();
});

test("a dropped valid report leaves the landing screen", async () => {
  render(<App />);
  const dropzone = screen.getByText(/Drop your report.json here/).parentElement!;
  fireEvent.drop(dropzone, { dataTransfer: { files: [new File([sampleText], "report.json")] } });
  await waitFor(() => expect(screen.queryByRole("button", { name: "Load sample report" })).toBeNull());
});
