import { createHmac, timingSafeEqual, randomBytes } from "node:crypto";
import { cookies } from "next/headers";

export const COOKIE = "traderlab_session";
export const SESSION_SECONDS = 8 * 60 * 60;
export const sessionReady = () => (process.env.TRADERLAB_SESSION_SECRET?.length ?? 0) >= 32 && (process.env.TRADERLAB_VIEWER_PASSWORD?.length ?? 0) >= 12;
export function sameSecret(a: string, b: string) {
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}
function signature(value: string) {
  return createHmac("sha256", process.env.TRADERLAB_SESSION_SECRET!).update(`${process.env.TRADERLAB_VIEWER_PASSWORD}:${value}`).digest("hex");
}
export function issueSession() {
  const payload = `${Math.floor(Date.now() / 1000) + SESSION_SECONDS}.${randomBytes(16).toString("hex")}`;
  return `${payload}.${signature(payload)}`;
}
export async function authenticated() {
  if (!sessionReady()) return false;
  const value = (await cookies()).get(COOKIE)?.value ?? "";
  const [expiration, nonce, sig] = value.split(".");
  if (!/^\d{10}$/.test(expiration ?? "") || !/^[a-f0-9]{32}$/.test(nonce ?? "") || !/^[a-f0-9]{64}$/.test(sig ?? "")) return false;
  const now = Math.floor(Date.now() / 1000);
  return Number(expiration) > now && Number(expiration) <= now + SESSION_SECONDS && sameSecret(signature(`${expiration}.${nonce}`), sig);
}
export const originAllowed = (request: Request) => request.headers.get("origin") === new URL(request.url).origin;
