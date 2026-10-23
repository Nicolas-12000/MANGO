"use client";

import { useEffect, useState } from "react";

type GuideItem = { question: string; answer: string };
type GuideSection = { part: string; title: string; items: GuideItem[] };
type GuidePayload = { sections: GuideSection[] };

export function AssignmentGuide() {
  const [sections, setSections] = useState<GuideSection[] | null>(null);

  useEffect(() => {
    fetch("/guide.json")
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: GuidePayload | null) => setSections(payload?.sections ?? null))
      .catch(() => setSections(null));
  }, []);

  if (!sections?.length) return null;

  return (
    <section className="rounded-lg border border-outline bg-surface p-4 sm:p-5">
      <h2 className="type-title">Preguntas del análisis</h2>
      <p className="type-small mt-2 text-secondary">
        Si estás mirando los grupos y quieres saber cómo llegamos aquí, estas son las respuestas del taller de
        segmentación con K-Means.
      </p>
      <div className="mt-6 grid gap-3">
        {sections.map((section) => (
          <details key={section.part} className="rounded-md border border-outline bg-neutral/40 px-4 py-3">
            <summary className="type-heading cursor-pointer list-none marker:content-none">
              {section.part} — {section.title}
            </summary>
            <div className="mt-4 grid gap-5 border-t border-outline pt-4">
              {section.items.map((item) => (
                <article key={item.question}>
                  <h3 className="type-heading">{item.question}</h3>
                  <div className="type-small mt-2 space-y-2 text-secondary">
                    {item.answer.split("\n\n").map((paragraph) => (
                      <p key={paragraph.slice(0, 40)}>{formatInline(paragraph)}</p>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

function formatInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return <span key={index}>{part}</span>;
  });
}
