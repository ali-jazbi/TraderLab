"use client";

import { useEffect, useRef, useState } from "react";
import { CandlestickSeries, ColorType, createChart, createSeriesMarkers, type IChartApi, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";
import { asNumber, object, type Bar, type EventRow } from "@/lib/types";

export default function MarketChart({ bars, events, levels, reset }: { bars: Bar[]; events: EventRow[]; levels: boolean; reset: number }) {
  const host = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [hover, setHover] = useState<Bar | null>(null);
  const [zones, setZones] = useState<{ label: string; top: number; bottom: number; color: string }[]>([]);
  const latest = useRef({ bars, events, levels });
  const redraw = useRef<() => void>(() => {});
  latest.current = { bars, events, levels };

  useEffect(() => {
    if (!host.current) return;
    const api = createChart(host.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "#101719" }, textColor: "#91a5ac", fontFamily: "IBM Plex Mono", fontSize: 11, attributionLogo: true },
      grid: { vertLines: { color: "#1a2428" }, horzLines: { color: "#1a2428" } },
      rightPriceScale: { borderColor: "#243137", scaleMargins: { top: .1, bottom: .12 } },
      timeScale: { borderColor: "#243137", timeVisible: true, secondsVisible: true, rightOffset: 6 },
      crosshair: { vertLine: { color: "#719094", labelBackgroundColor: "#27393e" }, horzLine: { color: "#719094", labelBackgroundColor: "#27393e" } },
    });
    const candles = api.addSeries(CandlestickSeries, {
      upColor: "#80d4b8", downColor: "#e19489", borderVisible: false, wickUpColor: "#80d4b8", wickDownColor: "#e19489", priceFormat: { type: "price", precision: 2, minMove: .01 },
    });
    chart.current = api; series.current = candles;
    api.subscribeCrosshairMove(p => {
      const data = p.seriesData.get(candles);
      if (data && "open" in data) setHover({ ...data, availableAt: "", timeframe: "", time: Number(data.time) });
      else setHover(null);
    });
    function drawZones() {
      if (!latest.current.levels) { setZones([]); return; }
      const setup = [...latest.current.events].reverse().find(e => e.event === "SETUP_ANNOTATED");
      const displayedFrame = latest.current.bars.at(-1)?.timeframe;
      const detected = [...latest.current.events].reverse().find(e => e.event === "FVG_CONFIRMED" && e.fill_state !== "FULL" && e.timeframe === displayedFrame);
      const zone = Array.isArray(detected?.zone) ? detected.zone : [];
      const fvg = object(setup?.fvg), ob = object(setup?.ob);
      const definitions = [{ label: setup ? "FVG · منبع دستی" : "FVG · تشخیص تأییدشده", low: setup ? fvg.low : zone[0], high: setup ? fvg.high : zone[1], color: "mint" }, { label: "OB · منبع دستی", low: ob.low, high: ob.high, color: "amber" }];
      setZones(definitions.flatMap(z => {
        const low = asNumber(z.low), high = asNumber(z.high);
        if (low === null || high === null) return [];
        const a = candles.priceToCoordinate(high), b = candles.priceToCoordinate(low);
        return a !== null && b !== null ? [{ label: z.label, top: a, bottom: b, color: z.color }] : [];
      }));
    }
    redraw.current = drawZones;
    api.timeScale().subscribeVisibleLogicalRangeChange(drawZones);
    const observer = new ResizeObserver(drawZones);
    observer.observe(host.current);
    const element = host.current;
    element.addEventListener("pointerup", drawZones);
    element.addEventListener("wheel", drawZones, { passive: true });
    return () => { observer.disconnect(); element.removeEventListener("pointerup", drawZones); element.removeEventListener("wheel", drawZones); api.remove(); chart.current = null; series.current = null; };
  }, []);

  useEffect(() => {
    const candles = series.current;
    if (!candles) return;
    candles.setData(bars.map(bar => ({ time: bar.time as UTCTimestamp, open: bar.open, high: bar.high, low: bar.low, close: bar.close })));
    const markers = events.flatMap(e => {
      if (!e.time || !["PAPER_ENTRY", "PAPER_EXIT", "BIG_CANDLE_CONFIRMED"].includes(e.event)) return [];
      const t = Date.parse(e.event === "BIG_CANDLE_CONFIRMED" && typeof e.candidate_at === "string" ? e.candidate_at : e.time) / 1000;
      const bar = [...bars].reverse().find(b => b.time <= t);
      if (!bar) return [];
      const entry = e.event === "PAPER_ENTRY", bullish = e.side !== "SELL";
      return [{ time: bar.time as UTCTimestamp, position: entry ? (bullish ? "belowBar" as const : "aboveBar" as const) : "aboveBar" as const,
        color: entry ? "#80d4b8" : "#b7c4c7", shape: entry ? (bullish ? "arrowUp" as const : "arrowDown" as const) : "circle" as const,
        text: entry ? String(e.side) : String(e.exit_reason ?? "BIG"), size: .6 }];
    }).sort((a, b) => Number(a.time) - Number(b.time));
    const markerApi = createSeriesMarkers(candles, markers);
    const lines: ReturnType<typeof candles.createPriceLine>[] = [];
    if (levels) {
      const plan = object([...events].reverse().find(e => e.event === "CORE_PLAN")?.plan);
      for (const [key, title, color] of [["stop", "SL", "#e19489"], ["target1", "TP1", "#80d4b8"], ["target2", "TP2", "#80d4b8"]]) {
        const price = asNumber(plan[key]);
        if (price !== null) lines.push(candles.createPriceLine({ price, color, lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title }));
      }
      if (Array.isArray(plan.entries)) for (const value of plan.entries) {
        const price = asNumber(object(value).entry);
        if (price !== null) lines.push(candles.createPriceLine({ price, color: "#dab879", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: "BOS · دستی" }));
      }
    }
    const refresh = requestAnimationFrame(() => redraw.current());
    return () => { cancelAnimationFrame(refresh); markerApi.detach(); for (const line of lines) candles.removePriceLine(line); };
  }, [bars, events, levels]);

  useEffect(() => { chart.current?.timeScale().fitContent(); }, [reset]);
  const candle = hover ?? bars.at(-1);
  return <div className="chart-surface" dir="ltr">
    <div className="ohlc">{candle ? <>{["open", "high", "low", "close"].map(key => <span key={key}><i>{key[0].toUpperCase()}</i>{candle[key as keyof Bar] && Number(candle[key as keyof Bar]).toFixed(2)}</span>)}</> : <span>دادهٔ کندل بسته‌شده در این بازه موجود نیست</span>}</div>
    <div ref={host} className="chart-canvas" />
    <div className="chart-zones" aria-hidden="true">{zones.map(z => <div key={z.label} className={`chart-zone ${z.color}`} style={{ top: Math.max(0, z.top), height: Math.max(1, z.bottom - z.top) }}><span>{z.label}</span></div>)}</div>
    {!bars.length && <div className="chart-empty">چارت با دریافت کندل‌های بسته‌شده نمایش داده می‌شود.</div>}
  </div>;
}
