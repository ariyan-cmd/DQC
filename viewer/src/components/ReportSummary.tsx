import { scoreBand } from "../lib/band";
import type { Report } from "../schema";

type Props = {
  report: Report;
  onReset: () => void;
};

// Every value below is rendered as a plain React text node, never as HTML.
export default function ReportSummary({ report, onReset }: Props) {
  const { dataset, score, sections } = report;
  const band = scoreBand(score.overall);

  return (
    <main className="mx-auto max-w-3xl p-8">
      <button
        type="button"
        onClick={onReset}
        className="rounded border border-gray-400 px-3 py-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
      >
        Load another report
      </button>

      <h1 className="mt-6 text-2xl font-bold">{dataset.name}</h1>
      <p className="text-gray-600">
        {dataset.num_images} images, {dataset.num_labels} labels, {dataset.classes.length} classes
      </p>

      <h2 className="sr-only">Overall score</h2>
      <p className="mt-6">
        <span className={`text-6xl font-bold ${band.className}`}>{score.overall}</span>
        <span className="text-xl text-gray-600"> / 100</span>
      </p>
      <p className={`text-lg font-semibold ${band.className}`}>{band.label}</p>

      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {sections.map((section) => {
          const sectionBand = scoreBand(section.score);
          return (
            <li key={section.name} className="rounded border border-gray-300 p-4">
              <h2 className="font-semibold">{section.name}</h2>
              <p>
                <span className={`text-3xl font-bold ${sectionBand.className}`}>{section.score}</span>
                <span className="text-gray-600"> / 100, {sectionBand.label}</span>
              </p>
              <p className="mt-2 text-sm text-gray-700">{section.reason}</p>
              <p className="mt-2 text-sm text-gray-600">
                {section.issue_count} {section.issue_count === 1 ? "issue" : "issues"}
              </p>
            </li>
          );
        })}
      </ul>
    </main>
  );
}
