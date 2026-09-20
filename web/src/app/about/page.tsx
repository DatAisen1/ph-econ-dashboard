import SiteHeader from "@/components/SiteHeader";

export default function AboutPage() {
  return (
    <>
      <SiteHeader />
      <main className="min-h-screen px-6 py-12 md:px-16 md:py-20 max-w-3xl mx-auto">
        <h1 className="font-display text-4xl leading-tight mb-8">About this project</h1>

        <section className="mb-10">
          <h2 className="font-display text-xl mb-3">Data sources</h2>
          <p className="text-muted leading-relaxed">
            Regional and national Consumer Price Index figures come from the{" "}
            <a
              href="https://openstat.psa.gov.ph"
              className="text-institutional underline"
              target="_blank"
              rel="noreferrer"
            >
              Philippine Statistics Authority&apos;s OpenSTAT
            </a>{" "}
            platform (PXWeb API). Cross-country comparison figures - GDP, inflation, unemployment -
            come from the{" "}
            <a
              href="https://data.worldbank.org"
              className="text-institutional underline"
              target="_blank"
              rel="noreferrer"
            >
              World Bank Open Data
            </a>{" "}
            API.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="font-display text-xl mb-3">How the data gets here</h2>
          <p className="text-muted leading-relaxed mb-3">
            Both sources are pulled daily by a scheduled pipeline (dlt for ingestion, dbt for
            transformation and testing, Dagster for orchestration) into a DuckDB warehouse. This
            site doesn&apos;t query a live database - it reads a static export generated after each
            pipeline run, since the underlying data itself only updates once a day. Running a
            live backend for data that changes daily would be infrastructure the problem doesn&apos;t
            need.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="font-display text-xl mb-3">Scope</h2>
          <p className="text-muted leading-relaxed">
            The regional CPI view currently covers two zones - the National Capital Region and
            everywhere else in the country (&quot;Areas Outside NCR&quot;) - reflecting the actual
            granularity of data ingested so far, not the full 18-region breakdown PSA publishes.
            The country comparison covers the Philippines against four ASEAN and regional peers:
            Indonesia, Thailand, Vietnam, and South Korea.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl mb-3">Built as</h2>
          <p className="text-muted leading-relaxed">
            A data engineering learning project - the emphasis throughout was on production
            practices (tested pipelines, dimensional modeling, orchestration, observability) at a
            scale genuinely appropriate to the data involved, rather than defaulting to
            heavier tools the dataset didn&apos;t actually need.
          </p>
        </section>
      </main>
    </>
  );
}