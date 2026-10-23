"use client";

import { useEffect, useState, type FormEvent } from "react";

import { classifyCustomer } from "@/lib/api";
import { readHistory, rememberClassification, type HistoryEntry } from "@/lib/history";
import { PROFILE_COLOR } from "@/lib/profiles";
import type { Analysis, Classification, CustomerInput } from "@/lib/types";

const ERROR_COPY: Record<string, string> = {
  invalid_gender: "El género tiene que ser Female o Male.",
  invalid_age: "La edad tiene que ser un entero.",
  age_out_of_bounds: "La edad queda fuera de 15 a 100.",
  annual_income_k_out_of_bounds: "El ingreso queda fuera de 0 a 500.",
  spending_score_out_of_bounds: "Las ganas de comprar van de 1 a 100.",
  classify_failed: "No se pudo clasificar el cliente.",
};

export function ClassifyForm({
  analysis,
  source,
}: {
  analysis: Analysis;
  source: "api" | "bundle";
}) {
  const [gender, setGender] = useState<CustomerInput["gender"]>("Female");
  const [age, setAge] = useState("35");
  const [annualIncomeK, setAnnualIncomeK] = useState("70");
  const [spendingScore, setSpendingScore] = useState("50");
  const [result, setResult] = useState<Classification | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setHistory(readHistory());
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const customer: CustomerInput = {
      gender,
      age: Number(age),
      annual_income_k: Number(annualIncomeK),
      spending_score: Number(spendingScore),
    };
    if (!Number.isInteger(customer.age)) {
      setError(ERROR_COPY.invalid_age ?? "La edad tiene que ser un entero.");
      setPending(false);
      return;
    }
    try {
      const classified = await classifyCustomer(analysis, customer, source);
      setResult(classified);
      setHistory(
        rememberClassification({
          ...customer,
          headline: classified.headline,
          profile: classified.profile,
          at: new Date().toISOString(),
        }),
      );
    } catch (caught) {
      const code = caught instanceof Error ? caught.message : "classify_failed";
      setResult(null);
      setError(ERROR_COPY[code] ?? "Revisa los valores e inténtalo de nuevo.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <form onSubmit={onSubmit} className="rounded-lg border border-outline bg-surface p-4 sm:p-5">
        <h2 className="type-title">Probar un cliente</h2>
        <p className="type-small mt-2 text-secondary">
          La edad y el género nos ayudan a imaginarlo. El grupo lo deciden el ingreso y las ganas de comprar.
        </p>
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1">
            <span className="type-heading">Género</span>
            <select
              value={gender}
              onChange={(event) => setGender(event.target.value as CustomerInput["gender"])}
              className="type-num h-12 rounded-md border border-outline bg-surface px-3"
            >
              <option value="Female">Mujer</option>
              <option value="Male">Hombre</option>
            </select>
          </label>
          <NumberField label="Edad" hint="Años cumplidos." value={age} onChange={setAge} min={15} max={100} step={1} />
          <NumberField
            label="Ingreso anual"
            hint="En miles de dólares. 70 significa unos US$ 70.000 al año."
            value={annualIncomeK}
            onChange={setAnnualIncomeK}
            min={0}
            max={500}
            step={1}
          />
          <NumberField
            label="Ganas de comprar"
            hint="De 1 a 100. 100 es quien más compra en la tienda."
            value={spendingScore}
            onChange={setSpendingScore}
            min={1}
            max={100}
            step={1}
          />
        </div>
        <button
          type="submit"
          disabled={pending}
          className="type-heading mt-4 h-12 w-full rounded-md bg-tertiary text-on-tertiary hover:bg-tertiary-container disabled:opacity-60"
        >
          {pending ? "Buscando su grupo…" : "Ver a qué grupo pertenece"}
        </button>
        {error ? <p className="type-small mt-3 text-error">{error}</p> : null}
      </form>
      <section className="rounded-lg border border-outline bg-surface p-4 sm:p-5">
        <h2 className="type-title">Su grupo</h2>
        {result ? (
          <div className="mt-4">
            <p className="type-label" style={{ color: PROFILE_COLOR[result.profile] }}>
              {result.headline}
            </p>
            <p className="type-body mt-3 text-secondary">{result.description}</p>
            <p className="type-body mt-3">
              <span className="font-semibold">Qué hacer: </span>
              {result.strategy}
            </p>
            <p className="type-small mt-4 text-secondary">{fitLabel(result.distance_to_centroid)}</p>
            {result.outside_training_range.length > 0 ? (
              <p className="type-small mt-3 text-error">
                {outsideRangeCopy(result.outside_training_range)} El grupo es una aproximación.
              </p>
            ) : null}
          </div>
        ) : (
          <p className="type-body mt-4 text-secondary">
            Escribe a alguien que todavía no está en la base. Te diremos a quién se parece y qué campaña le queda
            mejor.
          </p>
        )}
      </section>
      {history.length > 0 ? (
        <section className="rounded-lg border border-outline bg-surface p-4 sm:col-span-2 sm:p-5">
          <h2 className="type-title">Consultas guardadas</h2>
          <p className="type-small mt-2 text-secondary">
            Quedan en este navegador. No se suben a ningún servidor.
          </p>
          <ul className="mt-4 grid gap-2">
            {history.map((entry) => (
              <li key={entry.at} className="type-small flex flex-wrap justify-between gap-2 border-b border-outline py-2">
                <span>
                  {entry.gender === "Female" ? "Mujer" : "Hombre"}, {entry.age} años · ingreso {entry.annual_income_k}{" "}
                  mil · compra {entry.spending_score}
                </span>
                <span className="font-semibold" style={{ color: PROFILE_COLOR[entry.profile] }}>
                  {entry.headline}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function fitLabel(distance: number) {
  if (distance < 0.35) return "Encaja de lleno en este grupo.";
  if (distance < 1) return "Está cerca del cliente típico de este grupo.";
  return "Queda hacia el borde del grupo. Conviene mirarlo con calma.";
}

function outsideRangeCopy(fields: string[]) {
  const names = fields.map((field) => (field === "annual_income_k" ? "el ingreso" : "las ganas de comprar"));
  return `No tenemos clientes con ${names.join(" ni ")} tan extremos.`;
}

function NumberField({
  label,
  hint,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  hint: string;
  value: string;
  onChange: (value: string) => void;
  min: number;
  max: number;
  step: number;
}) {
  return (
    <label className="grid gap-1">
      <span className="type-heading">{label}</span>
      <span className="type-small text-secondary">{hint}</span>
      <input
        className="type-num h-12 rounded-md border border-outline bg-surface px-3"
        inputMode="decimal"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
      />
    </label>
  );
}
