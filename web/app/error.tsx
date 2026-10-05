"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <main className="boot"><h1>نمایش داشبورد ممکن نشد</h1><p>داده‌ای تغییر نکرده است. دوباره تلاش کن.</p><button className="button accent" onClick={reset}>تلاش دوباره</button></main>;
}
