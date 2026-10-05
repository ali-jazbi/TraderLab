"use client";

import dynamic from "next/dynamic";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { ActivityIcon, ArrowDownIcon, ArrowUpIcon, ArrowClockwiseIcon, ArrowSquareOutIcon, ChartLineUpIcon, CheckIcon, ClockIcon, CloudArrowUpIcon, DatabaseIcon, DownloadSimpleIcon, FileTextIcon, GearSixIcon, InfoIcon, ListBulletsIcon, LockSimpleIcon, PauseIcon, PlayIcon, PlusIcon, ShieldCheckIcon, SkipForwardIcon, TargetIcon, UploadSimpleIcon, WarningCircleIcon, WifiHighIcon, XIcon } from "@phosphor-icons/react";
import { barsFromEvents, eventCategory, eventNames, MAX_LOCAL_ROWS, observations, parseJournal } from "@/lib/events";
import { asNumber, object, type Dataset, type EventRow, type RunInfo } from "@/lib/types";

const MarketChart = dynamic(() => import("./market-chart"), { ssr: false, loading: () => <div className="chart-skeleton"><div className="skeleton" /><span>در حال آماده‌سازی چارت…</span></div> });
type Status = { storageConfigured: boolean; viewerConfigured: boolean; authenticated: boolean; ingestConfigured: boolean };
const tabs = [{ id: "overview", name: "اتاق کنترل", Icon: ActivityIcon }, { id: "setups", name: "ستاپ‌ها", Icon: TargetIcon }, { id: "journal", name: "دفتر رویدادها", Icon: ListBulletsIcon }, { id: "analytics", name: "تحلیل اجرا", Icon: ChartLineUpIcon }];
const money = (n: number | null) => n === null ? "—" : `${n < 0 ? "−" : n > 0 ? "+" : ""}${Math.abs(n).toFixed(2)}`;
const price = (value: unknown) => asNumber(value)?.toFixed(2) ?? "—";
function clock(value: string | null | undefined, zone = "Asia/Tehran") {
  if (!value) return "زمان نامشخص";
  return new Intl.DateTimeFormat("en-GB", { timeZone: zone, hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date(value));
}
function download(name: string, content: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "application/x-ndjson;charset=utf-8" }));
  const link = document.createElement("a"); link.href = url; link.download = name; link.click(); URL.revokeObjectURL(url);
}
async function getJson(url: string, options?: RequestInit) {
  const response = await fetch(url, { cache: "no-store", ...options });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `خطای اتصال ${response.status}`);
  return body;
}

export default function Dashboard({ fixture }: { fixture: Dataset }) {
  const [dataset, setDataset] = useState<Dataset>(fixture);
  const [mode, setMode] = useState("sample");
  const [tab, setTab] = useState("overview");
  const [cursor, setCursor] = useState(fixture.events.length);
  const [playing, setPlaying] = useState(false);
  const [follow, setFollow] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [frame, setFrame] = useState("M1");
  const [zone, setZone] = useState("Asia/Tehran");
  const [levels, setLevels] = useState(true);
  const [reset, setReset] = useState(0);
  const [selected, setSelected] = useState<EventRow | null>(null);
  const [category, setCategory] = useState("all");
  const [query, setQuery] = useState("");
  const search = useDeferredValue(query);
  const [settings, setSettings] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [runId, setRunId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [password, setPassword] = useState("");
  const [now, setNow] = useState(0);
  const [pollTime, setPollTime] = useState<string | null>(null);
  const importer = useRef<HTMLInputElement>(null);
  const liveEvents = useRef<EventRow[]>([]);

  useEffect(() => {
    if (!selected && !settings) return;
    const prior = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    const focusable = () => Array.from(dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input, select, a[href], [tabindex="0"]') ?? []);
    focusable()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setSelected(null); setSettings(false); }
      if (event.key !== "Tab") return;
      const list = focusable(), first = list[0], last = list.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", keydown);
    return () => { document.removeEventListener("keydown", keydown); document.body.style.overflow = overflow; prior?.focus(); };
  }, [selected, settings]);

  useEffect(() => { getJson("/api/status").then(setStatus).catch(() => setError("وضعیت اتصال دریافت نشد.")); const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  useEffect(() => { if (follow && mode === "live") setCursor(dataset.events.length); }, [dataset.events.length, follow, mode]);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => setCursor(value => {
      if (value >= dataset.events.length) { setPlaying(false); return value; }
      return value + 1;
    }), 1000 / speed);
    return () => clearInterval(timer);
  }, [playing, speed, dataset.events.length]);

  useEffect(() => {
    if (mode !== "live" || !status?.authenticated) return;
    let active = true;
    let timeout: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    async function poll() {
      if (!active) return;
      if (document.hidden) { timeout = setTimeout(poll, 3000); return; }
      try {
        const result = await getJson("/api/runs", { signal: controller.signal });
        if (!active) return;
        setRuns(result.runs);
        if (!runId && result.runs.length) { setRunId(result.runs[0].id); return; }
        if (runId && liveEvents.current.length < MAX_LOCAL_ROWS) {
          let more = true;
          while (more && active && liveEvents.current.length < MAX_LOCAL_ROWS) {
            const after = liveEvents.current.at(-1)?.seq ?? 0;
            const page = await getJson(`/api/events?run=${encodeURIComponent(runId)}&after=${after}`, { signal: controller.signal });
            if (!active) return;
            if (!Array.isArray(page.events)) throw new Error("پاسخ رویداد معتبر نیست.");
            liveEvents.current = [...liveEvents.current, ...page.events].slice(0, MAX_LOCAL_ROWS);
            more = page.hasMore;
          }
          const run = (result.runs as RunInfo[]).find(r => r.id === runId);
          setDataset({ id: runId, label: run?.label ?? runId, source: run?.source ?? "native", events: liveEvents.current,
            warnings: liveEvents.current.length >= MAX_LOCAL_ROWS ? ["سقف نمایش ۲۰٬۰۰۰ رویداد پر شده؛ این نما کل تاریخچه را پوشش نمی‌دهد. داده‌های بیشتر در دیتابیس محفوظ‌اند."] : [] });
        }
        setPollTime(new Date().toISOString()); setError("");
      } catch (e) { if (active && !controller.signal.aborted) setError(e instanceof Error ? e.message : "اتصال ناموفق بود."); }
      if (active) timeout = setTimeout(poll, 3000);
    }
    poll();
    return () => { active = false; controller.abort(); clearTimeout(timeout); };
  }, [mode, status?.authenticated, runId]);

  const visible = useMemo(() => dataset.events.slice(0, cursor), [dataset.events, cursor]);
  const stats = useMemo(() => observations(visible), [visible]);
  const chartBars = useMemo(() => {
    if (dataset.bars) { const time = visible.at(-1)?.time; return dataset.bars.filter(b => b.timeframe === frame && time && Date.parse(b.availableAt) <= Date.parse(time)); }
    return barsFromEvents(visible, frame);
  }, [dataset, visible, frame]);
  const filtered = useMemo(() => visible.filter(e => (category === "all" || eventCategory(e) === category) && (!search || JSON.stringify(e).toLowerCase().includes(search.toLowerCase()))), [visible, category, search]);
  const activeRun = runs.find(r => r.id === runId);
  const publisherAge = activeRun && now ? Math.max(0, (now - Date.parse(activeRun.last_ingest_at)) / 1000) : null;
  const connected = mode === "live" && status?.authenticated && publisherAge !== null && publisherAge < 20 && !error;
  const isPaper = dataset.source !== "native" && visible.some(e => /PAPER_|CORE_PLAN/.test(e.event));
  const setups = visible.filter(e => e.event === "SETUP_ANNOTATED");
  const latest = visible.at(-1);
  const lastPlan = object([...visible].reverse().find(e => e.event === "CORE_PLAN")?.plan);
  const currentPnl = isPaper ? stats.pnl : null;

  function changeSource(value: string) {
    setPlaying(false); setSelected(null); setError(""); setMode(value); setPollTime(null);
    if (value === "sample") { setDataset(fixture); setCursor(fixture.events.length); setReset(v => v + 1); }
    if (value === "live") { liveEvents.current = []; setDataset({ id: runId || "waiting", source: "native", label: "در انتظار اتصال", events: [], warnings: [] }); setCursor(0); if (!status?.authenticated) setSettings(true); }
    if (value === "import") importer.current?.click();
  }
  async function importFile(file: File) {
    setBusy(true); setPlaying(false); setError("");
    try {
      if (file.size > 15_000_000) throw new Error("سقف فایل محلی ۱۵ مگابایت است.");
      const imported = parseJournal(await file.text(), file.name);
      setMode("import"); setDataset(imported); setCursor(imported.events.length); setSelected(null); setReset(v => v + 1);
    } catch (e) { setError(e instanceof Error ? e.message : "فایل خوانده نشد."); }
    finally { setBusy(false); }
  }
  async function login(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try { await getJson("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password }) }); setPassword(""); setStatus(await getJson("/api/status")); changeSource("live"); setSettings(false); }
    catch (e) { setError(e instanceof Error ? e.message : "ورود ناموفق بود."); }
    finally { setBusy(false); }
  }
  async function logout() {
    try { await getJson("/api/session", { method: "DELETE" }); setStatus(s => s ? { ...s, authenticated: false } : s); setRuns([]); setRunId(""); liveEvents.current = []; changeSource("sample"); }
    catch { setError("خروج انجام نشد؛ دوباره تلاش کن."); }
  }
  function rowView(e: EventRow) {
    return <button className={`event-row ${selected?.seq === e.seq ? "selected" : ""}`} key={e.seq} onClick={() => setSelected(e)}>
      <span className={`event-dot ${eventCategory(e)}`} /><span className="event-main"><strong>{eventNames[e.event] ?? e.event}</strong><small>{String(e.setup_id ?? e.rule)}{e.reason ? ` · ${String(e.reason)}` : ""}</small></span>
      <span className="event-tail"><time className="mono">{clock(e.time, zone)}</time><small className="mono">#{e.seq}</small></span>
    </button>;
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" dir="ltr"><span className="brand-mark"><ActivityIcon size={23} weight="bold" /></span>TraderLab<span className="brand-version">01</span></a>
      <div className="workspace"><span className="workspace-avatar">TL</span><div><strong>اتاق کنترل استراتژی</strong><small>XAUUSD · نسخهٔ ۰.۱</small></div><span className="tag outline">OBSERVE</span></div>
      <div className="nav-caption">فضای کاری</div>
      <nav aria-label="بخش‌های داشبورد">{tabs.map(({ id, name, Icon }) => <button key={id} className={`nav-item ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}><Icon size={20} /><span>{name}</span>{id === "journal" ? <b className="nav-count mono">{visible.length}</b> : null}</button>)}</nav>
      <div className="nav-caption second">داده و اتصال</div>
      <button className="nav-item" onClick={() => setSettings(true)}><WifiHighIcon size={20} /><span>اتصال به بات</span><span className={`small-dot ${connected ? "green" : ""}`} /></button>
      <button className="nav-item" onClick={() => importer.current?.click()}><UploadSimpleIcon size={20} /><span>ورود فایل لاگ</span></button>
      <a className="nav-item" href="/guide"><FileTextIcon size={20} /><span>راهنمای راه‌اندازی</span><ArrowSquareOutIcon size={15} /></a>
      <div className="sidebar-bottom"><ShieldCheckIcon size={20} /><div><strong>فقط مشاهده</strong><p>این داشبورد سفارش معاملاتی ارسال نمی‌کند.</p></div></div>
      <div className="sidebar-footer mono">TRADERLAB / OBSERVABILITY</div>
    </aside>

    <main className="main">
      <header className="topbar"><div className="breadcrumb">فضای کاری <span>/</span><strong>{tabs.find(t => t.id === tab)?.name}</strong></div><div className="top-actions"><span className={`connection ${connected ? "online" : ""}`}><span className="small-dot" />{mode === "live" ? connected ? "ناشر متصل" : "در انتظار داده / قطع اتصال" : "اتصال زنده فعال نیست"}</span><button className="icon-button" aria-label="تنظیمات اتصال" onClick={() => setSettings(true)}><GearSixIcon size={20} /></button><span className="avatar">M</span></div></header>
      <div className="content">
        <div className="page-heading"><div><div className="eyebrow mono">STRATEGY OBSERVATORY / XAUUSD</div><h1>{tabs.find(t => t.id === tab)?.name}</h1><p>هر تشخیص، هر تصمیم، با دلیل و زمان مشخص.</p></div><div className="heading-actions"><button className="button" disabled={!dataset.events.length} onClick={() => download(`${dataset.id}.jsonl`, dataset.events.map(e => JSON.stringify(e)).join("\n") + "\n")}><DownloadSimpleIcon size={17} />دریافت لاگ</button><button className="button accent" onClick={() => setSettings(true)}><PlusIcon size={17} />اتصال بات</button></div></div>
        <div className="source-strip"><span className={`tag ${dataset.source === "synthetic" ? "amber" : "mint"}`}>{dataset.source === "synthetic" ? "نمونهٔ ساختگی" : dataset.source === "imported" ? "فایل محلی · منشأ تأییدنشده" : dataset.source === "native" ? "لاگ MT5 · تشخیص" : "شبیه‌سازی ثبت‌شده"}</span><span className="source-description">{dataset.source === "synthetic" ? "مثال مرجع استراتژی · قیمت‌های چارت صرفاً برای نمایش ساخته شده‌اند" : dataset.label}</span><label className="source-picker">منبع <select value={mode} onChange={e => changeSource(e.target.value)}><option value="sample">مثال سند</option><option value="live">اتصال زنده</option><option value="import">فایل محلی</option></select></label></div>
        {error ? <div className="notice danger" role="alert"><WarningCircleIcon size={20} /><span>{error}</span><button className="icon-button" aria-label="بستن پیام" onClick={() => setError("")}><XIcon size={17} /></button></div> : null}
        {dataset.warnings.filter(w => !w.startsWith("فایل محلی")).map(w => <div key={w} className="notice"><InfoIcon size={18} /><span>{w}</span></div>)}
        {mode === "live" ? <div className="live-strip"><span><WifiHighIcon size={18} />ناشر: {connected ? "متصل" : "دادهٔ تازه دریافت نشده"}</span><span>آخرین رویداد دریافتی: <b className="mono">{clock(activeRun?.last_event_received_at, zone)}</b></span><span>آخرین بررسی: <b className="mono">{clock(pollTime, zone)}</b></span>{runs.length ? <select aria-label="انتخاب اجرای بات" value={runId} onChange={e => { liveEvents.current = []; setRunId(e.target.value); setDataset({ id: e.target.value, label: "در انتظار داده", source: "native", events: [], warnings: [] }); setCursor(0); setSelected(null); }} >{runs.map(run => <option key={run.id} value={run.id}>{run.label} · {run.source}</option>)}</select> : <button className="text-button" onClick={() => setSettings(true)}>راهنمای اتصال</button>}</div> : null}

        <section className="metrics" aria-label="خلاصهٔ اجرا">
          <div className="metric"><div className="metric-title">سود بسته‌شدهٔ مشاهده‌شده <ChartLineUpIcon size={18} /></div><div className={`metric-value mono ${currentPnl !== null && currentPnl >= 0 ? "positive" : ""}`}>{money(currentPnl)}<span>USD</span></div><small>{isPaper ? "معاملات شبیه‌سازی‌شده در بازهٔ نمایش" : "EA فعلی فقط تشخیص و ثبت می‌کند"}</small></div>
          <div className="metric"><div className="metric-title">ورودهای شبیه‌سازی‌شده <ArrowUpIcon size={18} /></div><div className="metric-value mono">{isPaper ? stats.entries.length.toString().padStart(2, "0") : "—"}<span>ENTRY</span></div><small>{isPaper ? `${stats.exits.length} خروج جزئی ثبت‌شده` : "ورود معاملاتی از این منبع گزارش نشده"}</small></div>
          <div className="metric"><div className="metric-title">استاپ روز معاملاتی <ShieldCheckIcon size={18} /></div><div className="metric-value mono">{stats.stopped ?? "—"}<span>/ 2 SETUPS</span></div><small>{stats.halted === true ? "ورود جدید متوقف است" : stats.halted === false ? "توقف روزانه گزارش نشده" : "وضعیت روزانه در لاگ موجود نیست"}</small></div>
          <div className="metric"><div className="metric-title">موارد مسدود / نامشخص <WarningCircleIcon size={18} /></div><div className="metric-value mono">{stats.blocks.length.toString().padStart(2, "0")}<span>EVENTS</span></div><small>{stats.blocks.length ? "دلیل هر مورد در دفتر رویدادها" : "در بازهٔ نمایش موردی گزارش نشده"}</small></div>
        </section>

        {tab === "overview" ? <>
          <div className="monitor-grid"><section className="panel market-panel"><div className="panel-header"><div className="instrument"><span className="instrument-icon">Au</span><div><h2 dir="ltr">XAU / USD <span>GOLD</span></h2><small>کندل بسته‌شده · زمان چارت UTC</small></div></div><div className="quote mono">{price(stats.lastQuote?.bid ?? chartBars.at(-1)?.close)}<small>{stats.lastQuote ? `ASK ${price(stats.lastQuote.ask)}` : "CLOSED BAR"}</small></div></div><div className="chart-toolbar"><div className="segmented" dir="ltr">{["M1", "M5", "M15", "H1", "H4"].map(f => <button key={f} className={frame === f ? "active" : ""} onClick={() => { setFrame(f); setReset(v => v + 1); }}>{f}</button>)}</div><div className="chart-tools"><label className="checkbox"><input type="checkbox" checked={levels} onChange={e => setLevels(e.target.checked)} />ناحیه‌ها و سطوح</label><button className="icon-button" title="نمایش تمام کندل‌ها" aria-label="نمایش تمام کندل‌ها" onClick={() => setReset(v => v + 1)}><ArrowClockwiseIcon size={17} /></button></div></div><MarketChart bars={chartBars} events={visible} levels={levels} reset={reset} /><div className="chart-footer"><span><i className="legend-dot mint" />FVG</span><span><i className="legend-dot amber" />BOS / OB</span><span><i className="legend-dot rose" />SL</span><span className="chart-credit"><a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">Charts by TradingView</a></span></div></section>
          <section className="panel decisions-panel"><div className="panel-header"><h2><ActivityIcon size={19} />جریان تصمیم‌ها</h2><span className="tag outline mono">{visible.length} EVENTS</span></div><div className="decision-feed">{visible.filter(e => e.kind !== "bar" && e.kind !== "tick").slice(-8).reverse().map(rowView)}{!visible.length ? <Empty title="منتظر اولین رویداد" text="پس از اتصال ناشر، تشخیص‌ها و تصمیم‌ها اینجا نمایش داده می‌شوند." /> : null}</div><button className="panel-link" onClick={() => setTab("journal")}>مشاهدهٔ دفتر کامل <ArrowSquareOutIcon size={16} /></button></section></div>
          <ReplayBar cursor={cursor} total={dataset.events.length} playing={playing} speed={speed} latest={latest} zone={zone} live={mode === "live"} follow={follow} setFollow={setFollow} setZone={setZone} setSpeed={setSpeed} setCursor={v => { setFollow(false); setPlaying(false); setCursor(v); }} toggle={() => { setFollow(false); if (cursor >= dataset.events.length) setCursor(0); setPlaying(v => !v); }} />
          <div className="lower-grid"><section className="panel"><div className="panel-header"><h2><TargetIcon size={19} />ستاپ جاری</h2><span className="tag outline">{setups.at(-1)?.side ? String(setups.at(-1)?.side) : "بدون ستاپ"}</span></div><SetupSummary setup={setups.at(-1)} plan={lastPlan} events={visible} /></section><section className="panel"><div className="panel-header"><h2><ShieldCheckIcon size={19} />وضعیت قواعد</h2><span className="mono muted">SPEC 0.1</span></div><RuleStatus events={visible} /></section></div>
        </> : null}

        {tab === "journal" ? <section className="panel journal"><div className="panel-header"><h2>دفتر رویدادها <span className="tag outline mono">{filtered.length}</span></h2><input className="search" placeholder="جست‌وجو در قانون، ستاپ یا دلیل…" aria-label="جست‌وجوی رویدادها" value={query} onChange={e => setQuery(e.target.value)} /></div><div className="journal-tabs">{[["all", "همه"], ["detection", "تشخیص"], ["trade", "معامله"], ["blocked", "مسدود / نامشخص"], ["system", "سیستم"]].map(([id, label]) => <button className={category === id ? "active" : ""} key={id} onClick={() => setCategory(id)}>{label}</button>)}<span className="muted">نمایش آخرین ۵۰۰ مورد · {zone === "UTC" ? "UTC" : "تهران"}</span></div><div className="journal-list">{filtered.slice(-500).reverse().map(rowView)}{!filtered.length ? <Empty title="رویدادی با این فیلتر وجود ندارد" text="فیلتر یا متن جست‌وجو را تغییر بده." /> : null}</div></section> : null}
        {tab === "setups" ? <div className="setup-grid">{setups.map(setup => <section className="panel" key={setup.seq}><div className="panel-header"><h2>{String(setup.setup_id)}</h2><span className="tag mint">{String(setup.side)}</span></div><SetupSummary setup={setup} plan={object(visible.find(e => e.event === "CORE_PLAN" && e.setup_id === setup.setup_id)?.plan)} events={visible.filter(e => e.setup_id === setup.setup_id)} /><button className="panel-link" onClick={() => { setSelected(setup); }}>مشاهدهٔ منبع و جزئیات <ArrowSquareOutIcon size={16} /></button></section>)}{!setups.length ? <section className="panel"><Empty title="ستاپی با مرزهای مشخص ثبت نشده" text="کاندید BOS به‌تنهایی ستاپ قابل‌معامله نیست. این بخش فقط ستاپ‌های دارای منبع را نمایش می‌دهد." /></section> : null}</div> : null}
        {tab === "analytics" ? <Analytics stats={stats} paper={isPaper} /> : null}
        <footer className="page-footer"><span><LockSimpleIcon size={14} />مشاهده و تحلیل؛ بدون کنترل سفارش</span><span>دادهٔ نمایشی یا شبیه‌سازی‌شده، مدرک سودآوری بازار نیست.</span><span className="mono">RULES → EVENTS → EVIDENCE</span></footer>
      </div>
    </main>

    <input ref={importer} type="file" accept=".jsonl,.ndjson,.txt" hidden onChange={e => { const file = e.target.files?.[0]; if (file) importFile(file); e.target.value = ""; }} />
    {selected ? <div className="modal-backdrop" onClick={() => setSelected(null)}><section role="dialog" aria-modal="true" aria-labelledby="detail-title" className="drawer" onClick={e => e.stopPropagation()}><div className="panel-header"><h2 id="detail-title">جزئیات رویداد</h2><button className="icon-button" aria-label="بستن جزئیات" onClick={() => setSelected(null)}><XIcon size={22} /></button></div><div className="drawer-body"><span className={`tag ${eventCategory(selected) === "blocked" ? "amber" : "mint"}`}>{eventNames[selected.event] ?? selected.event}</span><h3 dir="ltr" className="mono">{selected.event}</h3><div className="detail-facts"><span>شماره <b className="mono">#{selected.seq}</b></span><span>قانون <b className="mono">{selected.rule}</b></span><span>زمان UTC <b className="mono">{selected.time ?? "نامشخص"}</b></span></div>{selected.reason ? <div className="notice"><WarningCircleIcon size={20} /><span dir="ltr" className="mono">{String(selected.reason)}</span></div> : null}<h4>اطلاعات ثبت‌شده در لاگ</h4><pre className="json-view" dir="ltr">{JSON.stringify(selected, null, 2)}</pre><p className="muted">نمایش دادهٔ اصلی؛ داشبورد قانون یا سیگنال تازه‌ای تولید نمی‌کند.</p></div></section></div> : null}
    {settings ? <div className="modal-backdrop" onClick={() => setSettings(false)}><section role="dialog" aria-modal="true" aria-labelledby="connection-title" className="connection-dialog" onClick={e => e.stopPropagation()}><div className="panel-header"><h2 id="connection-title"><WifiHighIcon size={21} />اتصال خصوصی به بات</h2><button className="icon-button" aria-label="بستن اتصال" onClick={() => setSettings(false)}><XIcon size={22} /></button></div><div className="connection-body"><p>لاگ MT5 از کامپیوتر اجرای بات به این داشبورد ارسال می‌شود. صرفاً بازبودن سایت به معنی اجرای بات نیست.</p><div className="connection-steps">{[{ title: "دیتابیس رویدادها", text: "Neon / PostgreSQL", ready: status?.storageConfigured }, { title: "دسترسی خصوصی", text: "رمز مشاهده و نشست امن", ready: status?.viewerConfigured }, { title: "مسیر ارسال لاگ", text: "کلید اختصاصی ناشر", ready: status?.ingestConfigured }].map(step => <div key={step.title}><span className={`step-icon ${step.ready ? "ready" : ""}`}>{step.ready ? <CheckIcon size={18} /> : <ClockIcon size={18} />}</span><div><strong>{step.title}</strong><small>{step.text}</small></div><span className={`tag ${step.ready ? "mint" : "outline"}`}>{step.ready ? "تنظیم شده" : "نیاز به راه‌اندازی"}</span></div>)}</div>{status?.authenticated ? <div className="notice success"><ShieldCheckIcon size={20} /><span>نشست خصوصی فعال است.</span><button className="text-button" onClick={logout}>خروج</button></div> : status?.viewerConfigured && status?.storageConfigured ? <form className="login-form" onSubmit={login}><label htmlFor="viewer-password">رمز مشاهدهٔ داشبورد</label><input id="viewer-password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required /><button className="button accent" disabled={busy}>{busy ? "در حال ورود…" : "ورود و مشاهدهٔ اجراها"}</button></form> : <div className="notice"><InfoIcon size={20} /><span>داده‌های زنده تا تکمیل راه‌اندازی خصوصی نمایش داده نمی‌شوند. نمونه و فایل محلی قابل‌استفاده‌اند.</span></div>}{error ? <p className="error-text" role="alert">{error}</p> : null}<a className="button" href="/guide"><FileTextIcon size={18} />راهنمای Vercel، دیتابیس و ناشر <ArrowSquareOutIcon size={16} /></a></div></section></div> : null}
  </div>;
}

function Empty({ title, text }: { title: string; text: string }) { return <div className="empty"><DatabaseIcon size={30} /><h3>{title}</h3><p>{text}</p></div>; }

function ReplayBar(p: { cursor: number; total: number; playing: boolean; speed: number; latest?: EventRow; zone: string; live: boolean; follow: boolean; setFollow: (v: boolean) => void; setZone: (v: string) => void; setSpeed: (v: number) => void; setCursor: (v: number) => void; toggle: () => void }) {
  return <section className="replay"><div className="replay-heading"><strong><ClockIcon size={18} />بازپخش تصمیم‌ها</strong><span>رویداد <b className="mono">{p.cursor} / {p.total}</b></span><select aria-label="منطقهٔ زمانی رویدادها" value={p.zone} onChange={e => p.setZone(e.target.value)}><option value="Asia/Tehran">زمان تهران</option><option value="UTC">زمان UTC</option></select>{p.live ? <label className="checkbox"><input type="checkbox" checked={p.follow} onChange={e => p.setFollow(e.target.checked)} />دنبال‌کردن رویدادهای تازه</label> : <span className="muted">بدون جلو بردن زمانِ تأیید قواعد</span>}</div><div className="replay-controls"><button className="play-button" disabled={!p.total} aria-label={p.playing ? "توقف بازپخش" : "شروع بازپخش"} onClick={p.toggle}>{p.playing ? <PauseIcon weight="fill" size={20} /> : <PlayIcon weight="fill" size={20} />}</button><button className="icon-button" disabled={p.cursor >= p.total} aria-label="رویداد بعدی" onClick={() => p.setCursor(p.cursor + 1)}><SkipForwardIcon size={21} /></button><span className="mono replay-time">{clock(p.latest?.time, p.zone)}</span><input aria-label="شمارهٔ رویداد در بازپخش" type="range" min="0" max={p.total || 1} value={p.cursor} onChange={e => p.setCursor(Number(e.target.value))} /><select aria-label="سرعت بازپخش" value={p.speed} onChange={e => p.setSpeed(Number(e.target.value))}><option value="1">۱ رویداد / ثانیه</option><option value="2">۲ رویداد / ثانیه</option><option value="4">۴ رویداد / ثانیه</option></select><button className="button small" disabled={!p.total} onClick={() => p.setCursor(p.total)}>آخرین رویداد</button></div></section>;
}

function SetupSummary({ setup, plan, events }: { setup?: EventRow; plan: Record<string, unknown>; events: EventRow[] }) {
  if (!setup) return <Empty title="هنوز ستاپی ثبت نشده" text="تشخیص‌های مستقل در جریان رویدادها نمایش داده می‌شوند؛ مرزهای نامشخص حدس زده نمی‌شوند." />;
  const entries = Array.isArray(plan.entries) ? plan.entries : [];
  const has = (name: string) => events.some(e => e.setup_id === setup.setup_id && e.event === name);
  return <div className="setup-summary"><div className="setup-name"><strong>{String(setup.setup_id)}</strong><span className="tag amber">مرزهای دارای منبع دستی</span></div><div className="setup-progress">{[{ name: "ثبت ستاپ", yes: true }, { name: "برنامهٔ ورود", yes: has("CORE_PLAN") }, { name: "ورود", yes: has("PAPER_ENTRY") }, { name: "خروج", yes: has("PAPER_EXIT") }].map((step, i) => <div key={step.name} className={step.yes ? "complete" : ""}><span>{step.yes ? <CheckIcon size={13} weight="bold" /> : i + 1}</span><small>{step.name}</small></div>)}</div><div className="levels-grid"><div><small>ورودهای انتخاب‌شده</small><b className="mono">{entries.length ? entries.map(e => price(object(e).entry)).join(" / ") : "—"}</b></div><div><small>استاپ مشترک</small><b className="mono rose-text">{price(plan.stop)}</b></div><div><small>هدف اول</small><b className="mono positive">{price(plan.target1)}</b></div><div><small>هدف دوم</small><b className="mono positive">{price(plan.target2)}</b></div></div><p className="setup-source"><FileTextIcon size={14} /><span>{String(setup.source ?? "منبع اعلام نشده")}</span></p></div>;
}

function RuleStatus({ events }: { events: EventRow[] }) {
  const ny = [...events].reverse().find(e => /NY_CONTEXT|NY_RANGE/.test(e.event));
  const blocked = events.filter(e => /BLOCKED|UNRESOLVED/.test(e.event));
  return <div className="rule-status"><div><span><ShieldCheckIcon size={17} />قواعد نامشخص</span><b className={`tag ${blocked.length ? "amber" : "outline"}`}>{blocked.length ? `${blocked.length} مورد در این بازه` : "موردی گزارش نشده"}</b></div><div><span><ClockIcon size={17} />بایاس نیویورک</span><b className="tag outline">{ny ? String(ny.bias ?? ny.context ?? "مشاهده ثبت شده") : "گزارش نشده"}</b></div><div><span><InfoIcon size={17} />اخبار اقتصادی</span><b className="tag outline">{blocked.some(e => /news/i.test(String(e.reason))) ? "محدودیت ثبت‌شده" : "وضعیت مستقل گزارش نشده"}</b></div><div><span><LockSimpleIcon size={17} />سفارش از داشبورد</span><b className="tag mint">غیرفعال</b></div><p>این نما فقط وضعیت ثبت‌شده در لاگ را می‌خواند.</p></div>;
}

function Analytics({ stats, paper }: { stats: ReturnType<typeof observations>; paper: boolean }) {
  const max = Math.max(1, ...stats.equity.map(e => Math.abs(e.value)));
  const points = stats.equity.map((e, i) => `${30 + i / Math.max(1, stats.equity.length - 1) * 940},${140 - e.value / max * 105}`).join(" ");
  const reasons = new Map<string, number>(); for (const e of stats.blocks) { const reason = String(e.reason ?? e.todo ?? e.event); reasons.set(reason, (reasons.get(reason) ?? 0) + 1); }
  return <div className="analytics-grid"><section className="panel"><div className="panel-header"><h2>روند سود بسته‌شده</h2><span className="tag outline">فقط دادهٔ مشاهده‌شده</span></div>{paper ? <><div className="analytics-total mono positive">{money(stats.pnl)} <small>USD</small></div><svg className="equity-chart" viewBox="0 0 1000 280" role="img" aria-label="روند سود و زیان شبیه‌سازی‌شده"><path d="M30 140H970 M30 35H970 M30 245H970" fill="none" stroke="#26363b" strokeDasharray="4 6" /><polyline points={points} fill="none" stroke="#80d4b8" strokeWidth="3" /><text x="30" y="274" fill="#91a5ac" fontSize="14">START</text><text x="870" y="274" fill="#91a5ac" fontSize="14">LAST EVENT</text></svg><div className="table-scroll"><table><thead><tr><th>پوزیشن</th><th>خروج</th><th>سود خالص USD</th></tr></thead><tbody>{stats.exits.map(e => <tr key={e.seq}><td className="mono">{String(e.position_id)}</td><td className="mono">{String(e.exit_reason)}</td><td className={`mono ${(asNumber(e.pnl_usd) ?? 0) >= 0 ? "positive" : "rose-text"}`}>{money(asNumber(e.pnl_usd))}</td></tr>)}</tbody></table></div></> : <Empty title="معاملهٔ شبیه‌سازی‌شده گزارش نشده" text="از لاگ تشخیص، نرخ برد یا سود معاملاتی محاسبه نمی‌شود." />}</section><section className="panel"><div className="panel-header"><h2>دلایل ورود نکردن</h2><span className="tag amber">{stats.blocks.length}</span></div>{reasons.size ? <div className="reason-list">{[...reasons].map(([reason, count]) => <div key={reason}><code>{reason}</code><span className="tag outline mono">{count}</span></div>)}</div> : <Empty title="محدودیتی در این بازه ثبت نشده" text="این نتیجه فقط رویدادهای قابل مشاهده را پوشش می‌دهد." />}</section></div>;
}
