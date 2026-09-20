import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="max-w-6xl mx-auto px-6 md:px-16 pt-8 flex items-center justify-between">
      <Link href="/" className="font-display text-lg text-ink">
        PH Econ
      </Link>
      <nav className="flex gap-6 text-sm font-mono">
        <Link href="/" className="text-muted hover:text-ink transition-colors">
          CPI Detail
        </Link>
        <Link href="/compare" className="text-muted hover:text-ink transition-colors">
          Compare
        </Link>
        <Link href="/about" className="text-muted hover:text-ink transition-colors">
          About
        </Link>
      </nav>
    </header>
  );
}