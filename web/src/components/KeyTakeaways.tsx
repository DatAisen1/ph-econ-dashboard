import { formatDateLabel } from "@/lib/format";

export default function KeyTakeaways({
  latestDate,
  nationalCpi,
  yoyPercent,
  yoyDate,
  momPercent,
  momDate,
  foodCpi,
}: {
  latestDate: string;
  nationalCpi: number;
  yoyPercent: number | null;
  yoyDate: string | null;
  momPercent: number | null;
  momDate: string | null;
  foodCpi: number | null;
}) {
  const takeaways = [
    `National CPI was ${nationalCpi.toFixed(1)} in ${formatDateLabel(latestDate)}, measured against a 2018 base of 100.`,
    yoyPercent === null || yoyDate === null
      ? null
      : `National CPI changed ${yoyPercent >= 0 ? "+" : ""}${yoyPercent.toFixed(1)}% year-over-year versus ${formatDateLabel(yoyDate)}.`,
    momPercent === null || momDate === null
      ? null
      : `National CPI changed ${momPercent >= 0 ? "+" : ""}${momPercent.toFixed(1)}% month-over-month versus ${formatDateLabel(momDate)}.`,
    foodCpi === null ? null : `Food CPI was ${foodCpi.toFixed(1)} in ${formatDateLabel(latestDate)}, using the same 2018 base.`,
  ].filter((takeaway): takeaway is string => takeaway !== null);

  return (
    <section aria-labelledby="key-takeaways" className="mb-16">
      <h2 id="key-takeaways" className="font-display text-xl mb-4">Key takeaways</h2>
      <ul className="grid gap-3 md:grid-cols-2 text-sm text-muted leading-relaxed">
        {takeaways.map((takeaway) => <li key={takeaway} className="border-l-2 border-signal pl-4">{takeaway}</li>)}
      </ul>
    </section>
  );
}
