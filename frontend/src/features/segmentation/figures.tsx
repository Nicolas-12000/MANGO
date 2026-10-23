export function FigureCard({ src, title, note }: { src: string; title: string; note: string }) {
  return (
    <section className="rounded-lg border border-outline bg-surface p-4 sm:p-5">
      <h2 className="type-label text-secondary">{title}</h2>
      {/* The PNG is the figure saved with the notebook analysis, not a chart redrawn in the browser. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={title} className="mt-3 h-auto w-full rounded-md bg-neutral" />
      <p className="type-small mt-2 text-secondary">{note}</p>
    </section>
  );
}
