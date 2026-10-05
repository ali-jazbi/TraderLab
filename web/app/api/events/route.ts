import { authenticated } from "@/lib/auth";
import { readEvents } from "@/lib/store";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  if (!(await authenticated())) return Response.json({ error: "نشست خصوصی معتبر نیست." }, { status: 401 });
  const query = new URL(request.url).searchParams;
  const run = query.get("run") ?? "", after = Number(query.get("after") ?? "0");
  if (!/^[A-Za-z0-9_-]{1,80}$/.test(run) || !Number.isSafeInteger(after) || after < 0) return new Response(null, { status: 400 });
  try { return Response.json(await readEvents(run, after), { headers: { "Cache-Control": "private, no-store" } }); }
  catch { return Response.json({ error: "دریافت رویدادها ممکن نشد." }, { status: 503 }); }
}
