import { createHmac } from "node:crypto";
import { cookies } from "next/headers";
import { authenticated, COOKIE, issueSession, originAllowed, sameSecret, sessionReady, SESSION_SECONDS } from "@/lib/auth";
import { loginAttempt, storageReady } from "@/lib/store";
export const dynamic = "force-dynamic";
export async function POST(request: Request) {
  if (!originAllowed(request)) return Response.json({ error: "درخواست از مبدأ مجاز نیست." }, { status: 403 });
  if (!sessionReady() || !storageReady()) return Response.json({ error: "اتصال خصوصی هنوز پیکربندی نشده است." }, { status: 503 });
  if (Number(request.headers.get("content-length") ?? 0) > 1024) return new Response(null, { status: 413 });
  try {
    const body = await request.text();
    if (body.length > 1024) return new Response(null, { status: 413 });
    const { password } = JSON.parse(body);
    const ip = request.headers.get("x-vercel-forwarded-for")?.split(",")[0] ?? request.headers.get("x-forwarded-for")?.split(",")[0] ?? "local";
    const key = createHmac("sha256", process.env.TRADERLAB_SESSION_SECRET!).update(ip).digest("hex");
    if (!(await loginAttempt(key))) return Response.json({ error: "تلاش‌های ورود زیاد است؛ ۱۵ دقیقه بعد تلاش کن." }, { status: 429 });
    if (typeof password !== "string" || !sameSecret(password, process.env.TRADERLAB_VIEWER_PASSWORD!)) return Response.json({ error: "رمز ورود درست نیست." }, { status: 401 });
    (await cookies()).set(COOKIE, issueSession(), { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict", path: "/", maxAge: SESSION_SECONDS });
    return Response.json({ authenticated: true }, { headers: { "Cache-Control": "no-store" } });
  } catch { return Response.json({ error: "ورود ممکن نشد؛ تنظیمات اتصال را بررسی کن." }, { status: 503 }); }
}
export async function DELETE(request: Request) {
  if (!originAllowed(request) || !(await authenticated())) return new Response(null, { status: 403 });
  (await cookies()).delete(COOKIE);
  return Response.json({ authenticated: false }, { headers: { "Cache-Control": "no-store" } });
}
