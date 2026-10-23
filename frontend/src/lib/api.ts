import type { Analysis, Classification, CustomerInput } from "./types";
import { classifyLocally } from "./classify";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

async function readAnalysisBundle(): Promise<Analysis> {
  const response = await fetch("/analysis.json");
  if (!response.ok) {
    throw new Error("No está el paquete local de análisis.");
  }
  return (await response.json()) as Analysis;
}

export async function loadAnalysis(): Promise<{ analysis: Analysis; source: "api" | "bundle" }> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/analysis`, { signal: AbortSignal.timeout(4000) });
    if (!response.ok) throw new Error(String(response.status));
    return { analysis: (await response.json()) as Analysis, source: "api" };
  } catch {
    return { analysis: await readAnalysisBundle(), source: "bundle" };
  }
}

export async function classifyCustomer(
  analysis: Analysis,
  customer: CustomerInput,
  source: "api" | "bundle",
): Promise<Classification> {
  if (source === "bundle") return classifyLocally(analysis, customer);
  try {
    const response = await fetch(`${API_BASE_URL}/v1/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(customer),
      signal: AbortSignal.timeout(4000),
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      throw new Error(body?.detail ?? "classify_failed");
    }
    const result = (await response.json()) as Omit<Classification, "source">;
    return { ...result, source: "api" };
  } catch (error) {
    if (error instanceof Error && error.message.endsWith("_out_of_bounds")) throw error;
    if (error instanceof Error && error.message.startsWith("invalid_")) throw error;
    return classifyLocally(analysis, customer);
  }
}
