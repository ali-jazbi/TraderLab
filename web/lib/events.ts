import { asNumber, object, type Bar, type Dataset, type EventRow } from "./types";

export const MAX_LOCAL_ROWS = 20_000;
const utc = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$/;

export function validateEvents(input: unknown, limit = MAX_LOCAL_ROWS): EventRow[] {
  if (!Array.isArray(input) || !input.length || input.length > limit) throw new Error(`تعداد رویداد باید بین ۱ و ${limit} باشد.`);
  let sequence = 0;
  for (const item of input) {
    const row = object(item);
    if (!Number.isSafeInteger(row.seq) || Number(row.seq) <= sequence) throw new Error("شمارهٔ رویدادها باید مثبت و صعودی باشد.");
    sequence = Number(row.seq);
    if (typeof row.event !== "string" || !/^[A-Z][A-Z0-9_]{0,79}$/.test(row.event)) throw new Error("نام رویداد معتبر نیست.");
    if (typeof row.rule !== "string" || row.rule.length > 200 || row.spec_version !== "0.1") throw new Error("نسخه یا شناسهٔ قانون پشتیبانی نمی‌شود.");
    if (row.time !== null && (typeof row.time !== "string" || !utc.test(row.time) || !Number.isFinite(Date.parse(row.time)))) throw new Error("زمان باید UTC صریح باشد؛ زمان نامشخص فقط null است.");
    if (JSON.stringify(row).length > 32_000) throw new Error("یک رویداد از سقف اندازه عبور کرده است.");
  }
  return input as EventRow[];
}

export function parseJournal(text: string, filename: string): Dataset {
  const events = validateEvents(text.split(/\r?\n/).filter(line => line.trim()).map((line, i) => {
    try { return JSON.parse(line); } catch { throw new Error(`JSON نامعتبر در خط ${i + 1}`); }
  }));
  return { id: "local-import", label: filename, source: "imported", events,
    warnings: ["فایل محلی؛ منشأ و واقعی‌بودن داده مستقلاً تأیید نشده است.", ...(events.some(e => e.time === null) ? ["بعضی زمان‌ها نامشخص‌اند؛ بازپخش زمانی دقیق برای آن‌ها ممکن نیست."] : [])] };
}

export function barsFromEvents(events: EventRow[], timeframe: string): Bar[] {
  const bars = new Map<number, Bar>();
  for (const event of events) {
    if (event.kind !== "bar" || event.timeframe !== timeframe || typeof event.opened_at !== "string" || !event.time) continue;
    const values = [event.open, event.high, event.low, event.close].map(asNumber);
    if (values.some(n => n === null)) continue;
    const [open, high, low, close] = values as number[];
    const time = Date.parse(event.opened_at) / 1000;
    if (!Number.isFinite(time) || high < Math.max(open, close) || low > Math.min(open, close) || high < low) continue;
    bars.set(time, { time, availableAt: event.time, open, high, low, close, timeframe });
  }
  return [...bars.values()].sort((a, b) => a.time - b.time);
}

export const eventNames: Record<string, string> = {
  EA_INIT: "شروع ثبت MT5", EA_DEINIT: "پایان اجرای EA", TICK: "قیمت جدید", CLOSED_BAR: "کندل بسته‌شده",
  BIG_CANDLE_CONFIRMED: "Big Candle تأیید شد", FVG_CONFIRMED: "FVG تأیید شد", FVG_FILL_STATE: "وضعیت پرشدن FVG",
  BOS_CANDIDATE_QUALIFIED: "کاندید BOS واجد شرایط", BOS_CANDIDATE_BREAK: "شکست کاندید BOS",
  OB_ANCHOR_OBSERVATION: "مشاهدهٔ کندل مبنای OB",
  SETUP_ANNOTATED: "ثبت ستاپ با منبع", CORE_PLAN: "برنامهٔ ورود", BOS_FIRST_TOUCH: "اولین لمس BOS",
  PAPER_ENTRY: "ورود شبیه‌سازی‌شده", PAPER_EXIT: "خروج شبیه‌سازی‌شده", BE_MOVED: "انتقال استاپ به BE",
  ENTRY_BLOCKED: "ورود مسدود شد", EXECUTION_UNRESOLVED: "قاعدهٔ اجرا نامشخص", CONFIG_UNRESOLVED: "تنظیم نامشخص",
  DAY_RESET: "شروع روز معاملاتی", NY_CONTEXT: "بایاس نیویورک", NY_RANGE_OBSERVATION: "مشاهدهٔ محدودهٔ نیویورک",
  OB_BROKEN: "شکست OB", REVERSE_ARMED: "آمادهٔ ورود معکوس", STRUCTURE_ANNOTATED: "تأیید ساختار با منبع",
  BROKER_CAPABILITIES: "قابلیت‌های حساب و نماد بروکر", BROKER_CAPABILITY_SNAPSHOT: "قابلیت‌های حساب و نماد بروکر",
  BROKER_CONFIG_BLOCKED: "قابلیت بروکر با استراتژی سازگار نیست",
  BROKER_TIME_OFFSET: "اختلاف ساعت سرور بروکر", REQUEST_ALLOWED: "درخواست مجاز", REQUEST_RATE_WARNING: "نزدیک محدودیت درخواست بروکر",
  REQUEST_RATE_BLOCKED: "درخواست به‌علت محدودیت نرخ متوقف شد", REQUEST_PENDING: "درخواست در انتظار تطبیق",
  REQUEST_ACCEPTED: "پذیرش درخواست ثبت شد", REQUEST_REJECTED: "درخواست رد شد", REQUEST_TIMEOUT: "پاسخ درخواست نامشخص/منقضی شد",
  REQUEST_RECONCILED: "درخواست با وضعیت بروکر تطبیق داده شد",
};

export function eventCategory(event: EventRow) {
  if (/BLOCKED|UNRESOLVED/.test(event.event)) return "blocked";
  if (/ENTRY|EXIT|BE_MOVED|REVERSE/.test(event.event)) return "trade";
  if (/CANDLE|FVG|BOS|OB_|STRUCTURE|SETUP/.test(event.event)) return "detection";
  return "system";
}

export function observations(events: EventRow[]) {
  const exits = events.filter(e => e.event === "PAPER_EXIT");
  const lastDay = [...events].reverse().find(e => e.daily_profit !== undefined || e.event === "DAY_RESET");
  const blocks = events.filter(e => /BLOCKED|UNRESOLVED/.test(e.event));
  let pnl = 0;
  const equity = [{ seq: 0, value: 0 }];
  for (const e of exits) { pnl += asNumber(e.pnl_usd) ?? 0; equity.push({ seq: e.seq, value: pnl }); }
  const entries = events.filter(e => e.event === "PAPER_ENTRY");
  return { pnl, equity, exits, entries, blocks,
    dayPnl: asNumber(lastDay?.daily_profit) ?? (lastDay?.event === "DAY_RESET" ? 0 : null),
    stopped: asNumber(lastDay?.stopped_setups) ?? (lastDay?.event === "DAY_RESET" ? 0 : null),
    halted: typeof lastDay?.halted === "boolean" ? lastDay.halted : null,
    lastQuote: [...events].reverse().find(e => e.kind === "tick"),
  };
}
