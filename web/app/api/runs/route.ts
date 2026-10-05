import { authenticated } from "@/lib/auth";
import { listRuns, storageReady } from "@/lib/store";
export const dynamic = "force-dynamic";
export async function GET() {
  if (!(await authenticated())) return Response.json({ error: "ابتدا وارد داشبورد خصوصی شو." }, { status: 401 });
  if (!storageReady()) return Response.json({ error: "دیتابیس هنوز متصل نیست." }, { status: 503 });
  try { return Response.json({ runs: await listRuns() }, { headers: { "Cache-Control": "private, no-store" } }); }
  catch { return Response.json({ error: "دریافت اجراها ممکن نشد؛ اتصال دیتابیس یا نصب جدول‌ها را بررسی کن." }, { status: 503 }); }
}
