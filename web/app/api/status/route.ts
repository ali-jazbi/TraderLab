import { authenticated, sessionReady } from "@/lib/auth";
import { storageReady } from "@/lib/store";
export const dynamic = "force-dynamic";
export async function GET() {
  return Response.json({ storageConfigured: storageReady(), viewerConfigured: sessionReady(),
    authenticated: await authenticated(), ingestConfigured: (process.env.TRADERLAB_INGEST_KEY?.length ?? 0) >= 32 },
    { headers: { "Cache-Control": "private, no-store" } });
}
