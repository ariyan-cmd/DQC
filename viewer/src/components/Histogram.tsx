import type { Report } from "../schema";

type Props = { stats: Report["stats"] };

const pct = (ratio: number) => `${Math.round(ratio * 100)}%`;

// Five bars drawn with plain divs: the counts are also printed as text, so nothing depends on the bar.
export default function Histogram({ stats }: Props) {
  const buckets = Object.entries(stats.box_size_histogram);
  const total = buckets.reduce((sum, [, count]) => sum + count, 0);
  const max = Math.max(1, ...buckets.map(([, count]) => count));
  const { boxes_measured: measured, blurry_ratio: blurry } = stats.blur_summary;

  if (total === 0) return <p className="mt-2 text-gray-700">No boxes were measured.</p>;

  return (
    <div>
      <ul className="mt-2 space-y-1" aria-label="Number of boxes by size in pixels">
        {buckets.map(([label, count]) => (
          <li key={label} className="flex items-center gap-3 text-sm">
            <span className="w-16 shrink-0">{label} px</span>
            <span className="h-4 flex-1 rounded bg-gray-100" aria-hidden="true">
              <span
                className="block h-4 rounded bg-blue-700"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </span>
            <span className="w-10 shrink-0 text-right">{count}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-gray-700">Tiny boxes: {pct(stats.tiny_box_ratio)} of {total}.</p>
      {measured !== undefined && blurry !== undefined && (
        <p className="text-sm text-gray-700">
          Blur: {measured} boxes measured, {pct(blurry)} look blurry (a hint, not scored).
        </p>
      )}
    </div>
  );
}
