import { neon } from "@neondatabase/serverless";
import type { EventRow, RunInfo } from "./types";

export const storageReady = () => Boolean(process.env.DATABASE_URL);
function database() {
  if (!process.env.DATABASE_URL) throw new Error("STORAGE_UNCONFIGURED");
  return neon(process.env.DATABASE_URL);
}
export async function listRuns(): Promise<RunInfo[]> {
  const rows = await database()`SELECT id, bot_id, source, label, symbol, last_seq::text,
    last_ingest_at, last_event_received_at FROM traderlab_runs ORDER BY last_ingest_at DESC LIMIT 30`;
  return rows.map(row => ({ ...row, last_seq: Number(row.last_seq) })) as RunInfo[];
}
export async function readEvents(run: string, after: number) {
  const rows = await database()`SELECT payload FROM traderlab_events WHERE run_id = ${run} AND seq > ${after}
    ORDER BY seq ASC LIMIT 1001`;
  return { events: rows.slice(0, 1000).map(row => row.payload) as EventRow[], hasMore: rows.length > 1000 };
}
export async function ingest(run: Record<string, unknown>, events: EventRow[]) {
  const rows = await database()`SELECT traderlab_ingest(${JSON.stringify(run)}::jsonb, ${JSON.stringify(events)}::jsonb) AS result`;
  return rows[0].result;
}
export async function loginAttempt(key: string) {
  const rows = await database()`INSERT INTO traderlab_login_limits (id, attempts, expires_at)
    VALUES (${key}, 1, now() + interval '15 minutes') ON CONFLICT(id) DO UPDATE
    SET attempts = CASE WHEN traderlab_login_limits.expires_at < now() THEN 1 ELSE traderlab_login_limits.attempts + 1 END,
        expires_at = CASE WHEN traderlab_login_limits.expires_at < now() THEN now() + interval '15 minutes' ELSE traderlab_login_limits.expires_at END
    RETURNING attempts`;
  return Number(rows[0].attempts) <= 5;
}
