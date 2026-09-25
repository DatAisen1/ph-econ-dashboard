import { formatDateLabel } from "@/lib/format";

export default function CpiUnderstanding({
  latestValue,
  latestDate,
}: {
  latestValue: number;
  latestDate: string;
}) {
  return (
    <section aria-labelledby="cpi-understanding" className="border-y border-black/10 py-8 mb-16">
      <h2 id="cpi-understanding" className="font-display text-xl mb-3">What does this mean?</h2>
      <div className="grid gap-4 md:grid-cols-3 text-sm text-muted leading-relaxed">
        <p><strong className="text-ink">CPI.</strong> CPI measures changes in the prices households pay for a basket of goods and services. The index uses 2018 as its base year, where 2018 = 100.</p>
        <p><strong className="text-ink">The selected index.</strong> A CPI of {latestValue.toFixed(1)} means the index is {Math.abs(latestValue - 100).toFixed(1)} points {latestValue >= 100 ? "above" : "below"} its 2018 base in {formatDateLabel(latestDate)}. It does not mean every product changed by exactly that amount.</p>
        <p><strong className="text-ink">Inflation.</strong> Inflation is the rate at which the general price level changes, commonly represented using CPI growth.</p>
        <p><strong className="text-ink">YoY.</strong> Year-over-year compares the current month with the same month one year earlier.</p>
        <p><strong className="text-ink">MoM.</strong> Month-over-month compares the current month with the immediately previous month.</p>
        <p><strong className="text-ink">GDP growth.</strong> GDP growth measures the change in the value of goods and services produced by an economy over time. Employment and unemployment rates describe the share of people working and the share of the labor force without work but seeking it.</p>
      </div>
    </section>
  );
}
