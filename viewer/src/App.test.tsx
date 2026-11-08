import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import sample from "../public/sample-report.json";
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

test("a failed sample download shows a friendly error", async () => {
  stubFetch(new Error("offline"));
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Load sample report" }));
  expect((await screen.findByRole("alert")).textContent).toBe("Could not load the sample report.");
});

test("a file that is not a report shows an error and stays on the landing screen", async () => {
  render(<App />);
  chooseFile('{"hello": 1}');
  expect((await screen.findByRole("alert")).textContent).toContain("does not look like");
  expect(screen.getByRole("button", { name: "Load sample report" })).toBeTruthy();
});

test("a dropped valid report leaves the landing screen", async () => {
  render(<App />);
  const dropzone = screen.getByText(/Drop your report.json here/).parentElement!;
  fireEvent.drop(dropzone, { dataTransfer: { files: [new File([sampleText], "report.json")] } });
  await waitFor(() => expect(screen.queryByRole("button", { name: "Load sample report" })).toBeNull());
});
