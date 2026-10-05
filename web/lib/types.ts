export type EventRow = {
  seq: number;
  time: string | null;
  event: string;
  rule: string;
  spec_version: string;
  [key: string]: unknown;
};
export type Bar = { time: number; availableAt: string; open: number; high: number; low: number; close: number; timeframe: string };
export type RunInfo = {
  id: string; bot_id: string; source: "native" | "paper"; label: string;
  symbol: string; last_seq: number; last_ingest_at: string;
  last_event_received_at: string | null;
};
export type Dataset = {
  id: string; label: string; source: "synthetic" | "imported" | "native" | "paper";
  events: EventRow[]; bars?: Bar[]; warnings: string[];
};
export function asNumber(value: unknown) {
  const number = typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value) ? Number(value) : typeof value === "number" ? value : NaN;
  return Number.isFinite(number) ? number : null;
}
export const object = (value: unknown): Record<string, unknown> => value !== null && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
