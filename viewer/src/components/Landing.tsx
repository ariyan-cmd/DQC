import { useState, type DragEvent } from "react";
import type { LoadFailure } from "../lib/loadReport";

type Props = {
  error: LoadFailure | null;
  onSample: () => void;
  onFile: (file: File) => void;
};

const QUICK_START = `cd engine
uv sync
uv run dsc check /path/to/dataset -o report.json`;

export default function Landing({ error, onSample, onFile }: Props) {
  const [dragging, setDragging] = useState(false);

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) onFile(file);
  };

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-3xl font-bold">Dataset Readiness Checker</h1>
      <p className="mt-2 text-gray-600">
        Know if your object-detection dataset is safe to train on, before you spend the compute.
        Everything runs in your browser: your report never leaves your machine.
      </p>

      <button
        type="button"
        onClick={onSample}
        className="mt-6 rounded bg-blue-700 px-4 py-2 font-medium text-white hover:bg-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
      >
        Load sample report
      </button>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`mt-6 rounded border-2 border-dashed p-8 text-center ${dragging ? "border-blue-700 bg-blue-50" : "border-gray-300"}`}
      >
        <p>Drop your report.json here, or</p>
        <label className="mt-3 inline-block cursor-pointer rounded border border-gray-400 px-3 py-1 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-blue-700">
          Choose file
          <input
            type="file"
            accept=".json,application/json"
            className="sr-only"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) onFile(file);
              event.target.value = ""; // lets the same file be chosen again after an error
            }}
          />
        </label>
      </div>

      {error && (
        <div role="alert" className="mt-4 rounded bg-red-50 p-3 text-red-800">
          <p className="font-medium">{error.error}</p>
          <p>{error.hint}</p>
        </div>
      )}

      <h2 className="mt-8 text-lg font-semibold">Make your own report</h2>
      <pre className="mt-2 overflow-x-auto rounded bg-gray-900 p-4 text-sm text-gray-100">
        <code>{QUICK_START}</code>
      </pre>
    </main>
  );
}
