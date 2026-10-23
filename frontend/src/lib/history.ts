import type { CustomerInput, ProfileName } from "./types";

const STORAGE_KEY = "mango.classification_history";
const LIMIT = 12;

export type HistoryEntry = CustomerInput & {
  headline: string;
  profile: ProfileName;
  at: string;
};

export function readHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter(isEntry).slice(0, LIMIT) : [];
  } catch {
    return [];
  }
}

export function rememberClassification(entry: HistoryEntry): HistoryEntry[] {
  const next = [entry, ...readHistory().filter((item) => item.at !== entry.at)].slice(0, LIMIT);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

function isEntry(value: unknown): value is HistoryEntry {
  if (!value || typeof value !== "object") return false;
  const entry = value as Partial<HistoryEntry>;
  return typeof entry.headline === "string" && typeof entry.at === "string" && typeof entry.age === "number";
}
