function formatTimestamp(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  if (Number.isNaN(date.getTime())) return "Unavailable";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date) + " UTC";
}

export default function DataProvenance({
  source,
  sourceUrl,
  dataset,
  frequency,
  basePeriod,
  latestObservation,
  refreshedAt,
}: {
  source: string;
  sourceUrl: string;
  dataset: string;
  frequency: string;
  basePeriod?: string;
  latestObservation: string;
  refreshedAt: string;
}) {
  return (
    <section aria-labelledby="data-provenance" className="border-t border-black/10 pt-8 mt-16">
      <h2 id="data-provenance" className="font-display text-xl mb-4">Source and data freshness</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-sm">
        <div>
          <p className="font-mono text-xs text-muted uppercase tracking-wide">Data source</p>
          <a href={sourceUrl} target="_blank" rel="noreferrer" className="text-institutional underline mt-1 inline-block">{source}</a>
        </div>
        <div>
          <p className="font-mono text-xs text-muted uppercase tracking-wide">Dataset</p>
          <p className="mt-1">{dataset}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted uppercase tracking-wide">Frequency</p>
          <p className="mt-1">{frequency}</p>
        </div>
        {basePeriod && <div>
          <p className="font-mono text-xs text-muted uppercase tracking-wide">Base period</p>
          <p className="mt-1">{basePeriod}</p>
        </div>}
        <div>
          <p className="font-mono text-xs text-muted uppercase tracking-wide">Latest observation</p>
          <p className="mt-1">{latestObservation}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted uppercase tracking-wide">Pipeline refresh</p>
          <p className="mt-1">{formatTimestamp(refreshedAt)}</p>
        </div>
      </div>
    </section>
  );
}
