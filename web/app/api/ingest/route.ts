import { sameSecret } from "@/lib/auth";
import { validateEvents } from "@/lib/events";
import { ingest, storageReady } from "@/lib/store";
import { object } from "@/lib/types";
export const dynamic = "force-dynamic";
export async function POST(request: Request) {
  const key = process.env.TRADERLAB_INGEST_KEY;
  if (!key || key.length < 32 || !storageReady()) return Response.json({ error: "INGEST_UNCONFIGURED" }, { status: 503 });
  if (!sameSecret(request.headers.get("authorization") ?? "", `Bearer ${key}`)) return new Response(null, { status: 401 });
  if (Number(request.headers.get("content-length") ?? 0) > 262_144) return new Response(null, { status: 413 });
  try {
    const text = await request.text();
    if (Buffer.byteLength(text) > 262_144) return new Response(null, { status: 413 });
    const body = object(JSON.parse(text)), run = object(body.run);
    if (!/^[A-Za-z0-9_-]{1,80}$/.test(String(run.id ?? "")) || !/^[A-Za-z0-9_-]{1,80}$/.test(String(run.bot_id ?? "")) ||
      !["native", "paper"].includes(String(run.source)) || typeof run.label !== "string" || !run.label.length || run.label.length > 120 ||
      typeof run.symbol !== "string" || !run.symbol.length || run.symbol.length > 40) throw new Error("INVALID_RUN");
    const events = Array.isArray(body.events) && body.events.length === 0 ? [] : validateEvents(body.events, 100);
    try {
      return Response.json(await ingest(run, events), { headers: { "Cache-Control": "no-store" } });
    } catch (error) {
      const conflict = error instanceof Error && /CONFLICT|SEQUENCE_GAP/.test(error.message);
      return Response.json({ error: conflict ? "RUN_OR_EVENT_CONFLICT" : "STORAGE_UNAVAILABLE" }, { status: conflict ? 409 : 503 });
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "";
    const conflict = /CONFLICT|SEQUENCE_GAP/.test(message);
    return Response.json({ error: conflict ? "RUN_OR_EVENT_CONFLICT" : "BATCH_REJECTED" }, { status: conflict ? 409 : 400 });
  }
}
