// Placeholder cut points. The label is shown next to the colour so colour is never the only cue.
export function scoreBand(score: number): { label: string; className: string } {
  if (score >= 80) return { label: "Good", className: "text-green-800" };
  if (score >= 50) return { label: "Needs work", className: "text-amber-800" };
  return { label: "Poor", className: "text-red-800" };
}
