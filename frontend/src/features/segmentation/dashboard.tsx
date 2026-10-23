"use client";

import { useEffect, useState } from "react";

import { Logo } from "@/components/logo";
import { loadAnalysis } from "@/lib/api";
import { PROFILE_COLOR } from "@/lib/profiles";
import type { Analysis, ProfileName } from "@/lib/types";

import { ClassifyForm } from "./classify-form";
import { ProfileLegend } from "./charts";
import { FigureCard } from "./figures";

export function Dashboard() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [source, setSource] = useState<"api" | "bundle" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadAnalysis()
      .then((loaded) => {
        if (cancelled) return;
        setAnalysis(loaded.analysis);
        setSource(loaded.source);
      })
      .catch(() => {
        if (!cancelled) setError("No hay API ni paquete de análisis. Entrena el modelo primero.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="type-label text-tertiary">Centro comercial</p>
          <div className="mt-3 flex items-center gap-4">
            <Logo className="size-16 shrink-0 sm:size-20" />
            <div>
              <h1 className="type-hero">Mango</h1>
              <p className="type-body mt-3 max-w-xl text-secondary">
                Mira qué tipos de cliente tienes y prueba a cuál se parece alguien nuevo, antes de
                mandarle una campaña.
              </p>
            </div>
          </div>
        </div>
        <p className="type-small shrink-0 rounded-full border border-outline bg-surface px-3 py-2 text-secondary">
          {source === "api" ? "Datos en vivo" : source === "bundle" ? "Datos listos" : "Cargando"}
        </p>
      </header>

      {error ? <p className="type-body text-error">{error}</p> : null}
      {!analysis && !error ? <p className="type-body text-secondary">Cargando segmentos…</p> : null}

      {analysis ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Clientes" value={String(analysis.dataset.rows)} hint="personas en la base" />
            <Metric label="Grupos" value={String(analysis.selected_k)} hint="así se separan mejor" />
            <Metric
              label="Qué tan claros"
              value={analysis.model_silhouette.toLocaleString("es-CO", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
              hint="1 sería una separación perfecta"
            />
            <Metric label="Dónde crecer" value={analysis.growth_headline} hint="el grupo con más margen por ganar" compact />
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <FigureCard
              src="/figures/elbow.png"
              title="Cuántos grupos conviene usar"
              note="Figura del análisis. La curva baja rápido y luego se aplana. El doblez, en 5, es donde partir más ya no aporta."
            />
            <FigureCard
              src="/figures/silhouette.png"
              title="Qué tan nítido queda cada corte"
              note={
                analysis.k_selection.methods_agree
                  ? "Figura del análisis. Con 5 grupos la separación es la mejor, y coincide con la curva de al lado."
                  : `Figura del análisis. La separación más alta está en ${analysis.k_selection.silhouette_k} grupos.`
              }
            />
          </section>

          <FigureCard
            src="/figures/boxplots.png"
            title="Cómo se reparte cada variable"
            note="Figura del análisis. Muestra ingreso, ganas de comprar y edad, y marca los extremos."
          />

          <section className="rounded-lg border border-outline bg-surface p-4 sm:p-5">
            <h2 className="type-title">Los cinco tipos de cliente</h2>
            <p className="type-small mt-2 text-secondary">
              Cada punto es una persona. A la derecha, quién compra más. Arriba en ingreso, quién puede gastar más.
              La cruz marca el cliente típico del grupo.
            </p>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/figures/clusters.png"
              alt="Mapa de los cinco grupos de clientes"
              className="mt-4 h-auto w-full rounded-md bg-neutral"
            />
            <div className="mt-4">
              <ProfileLegend analysis={analysis} />
            </div>
            <div className="mt-6 grid gap-3 md:grid-cols-2">
              {analysis.clusters.map((cluster) => (
                <article
                  key={cluster.profile}
                  className="rounded-md border border-outline border-l-4 p-4"
                  style={{ borderLeftColor: PROFILE_COLOR[cluster.profile as ProfileName] }}
                >
                  <h3 className="type-title">{cluster.headline}</h3>
                  <p className="type-small mt-2 text-secondary">
                    {cluster.size} clientes · {moneyFromThousands(cluster.centroid.annual_income_k)} al año · compran{" "}
                    {Math.round(cluster.centroid.spending_score)} de 100
                  </p>
                  <p className="type-small mt-3 text-secondary">{cluster.description}</p>
                  <p className="type-small mt-2">
                    <span className="font-semibold">Qué hacer: </span>
                    {cluster.strategy}
                  </p>
                </article>
              ))}
            </div>
          </section>

          <ClassifyForm analysis={analysis} source={source ?? "bundle"} />
        </>
      ) : null}
    </div>
  );
}

const annualIncome = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
}).format;

function moneyFromThousands(thousands: number) {
  return annualIncome(thousands * 1000);
}

function Metric({
  label,
  value,
  hint,
  compact = false,
}: {
  label: string;
  value: string;
  hint: string;
  compact?: boolean;
}) {
  return (
    <article className="rounded-lg border border-outline bg-surface p-4">
      <h2 className="type-label text-secondary">{label}</h2>
      <p className={compact ? "type-title mt-2 text-balance" : "type-num-xl mt-2 text-balance"}>{value}</p>
      <p className="type-small mt-2 text-secondary">{hint}</p>
    </article>
  );
}
