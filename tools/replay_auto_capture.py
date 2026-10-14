"""Stream real native tester evidence through Python EXPERIMENTAL Core; never annotate trades."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traderlab.experimental import ExperimentalEngine
from traderlab.backtest import Equity, results
from traderlab.replay import encode, json_line
from traderlab.broker import validate_capture_timestamp
from traderlab.detection import instant

def replay(capture, manifest_path, out, replay_python=True):
    manifest=json.loads(manifest_path.read_text())
    base=json.loads((Path(__file__).resolve().parents[1]/"configs/production.template.json").read_text())
    base.update(backtest_only=True,experimental_grouping=manifest["grouping"],
                config_status="EXPERIMENTAL_REAL_DATA_BACKTEST_NOT_STRATEGY_APPROVAL",
                partial_fill_policy=None,be_entry_anchor=None,be_stop_counts_as_stop=None,
                account_currency="USD",contract_size=None,commission_usd_per_lot_per_side="0",
                slippage_pips="0",tp_fill_policy="target",server_utc_offset_seconds=10800,
                tehran_utc_offset_seconds=12600,max_spread_price="0.22",news_closure_lead_seconds=120,
                news_calendar={"source":"EXPERIMENTAL_EX_POST_PRIMARY_SCHEDULE",
                               "coverage_start":manifest["days"][0]["start"],
                               "coverage_end":manifest["days"][-1]["end"],"events":manifest["news"]},
                trading_day_calendar={"source":"EXPERIMENTAL_OVERLAP_CLIPPING",
                   "session_definition":"Sydney_open_to_New_York_close",
                   "coverage_start":manifest["days"][0]["start"],"coverage_end":manifest["days"][-1]["end"],
                   "sessions":[{"id":d["id"],"sydney_open":d["start"],"new_york_close":d["end"],
                                "available_at":d["available_at"]} for d in manifest["days"]]})
    engine=None; equity=Equity(); counts=Counter(); group_reasons=Counter(); entry_reasons=Counter()
    native_groups=[]; native_metrics=None; native_summary=None; capture_summary=None; deals=[]
    accepted_groups=[]; return_reasons=Counter(); followups=[]; config_evidence=None; last_tick_row=None
    previous_seq=0; previous_tick=0; previous_msc=0; total_bars=0; first=last=None; digest=hashlib.sha256()
    with capture.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            if not raw.strip(): continue
            r=json.loads(raw); event=r["event"]; counts[event]+=1
            if r["seq"]<=previous_seq: raise ValueError("Native event sequence regressed")
            previous_seq=r["seq"]
            if event in ("TICK_CAPTURE_ERROR","TICK_CAPTURE_AMBIGUITY","CORE_CONTROLLER_HALTED","BOS_TRACKER_HALTED"):
                raise ValueError("Invalid historical evidence: "+event)
            if event=="BROKER_CAPABILITY_SNAPSHOT":
                base["contract_size"]=r["contract_size"]
                base["runtime_capabilities"]={"volume_min":r["volume_min"],"volume_max":r["volume_max"],
                   "volume_step":r["volume_step"],"volume_limit":r["volume_limit"],"tick_size":r["tick_size"],
                   "chart_mode":"BID" if r.get("chart_mode",0)==0 else "UNSUPPORTED"}
                # Older capture has no chart field; BID was independently verified in this terminal.
                if replay_python: engine=ExperimentalEngine(base)
            if event=="EXPERIMENTAL_GROUP_FINALIZED":
                group_reasons[r["reason"] or "ACCEPTED"]+=1
                native_groups.append({k:r[k] for k in ("time","fvg_id","members","policy","accepted","reason")})
                if r["accepted"]: accepted_groups.append(r)
            elif event=="EXPERIMENTAL_TESTER_CONFIG": config_evidence=r
            elif event=="EXPERIMENTAL_FIRST_RETURN":
                return_reasons[r["reason"]]+=1
                related=[g for g in accepted_groups if r["bos_id"] in g["members"].split(";")]
                if related and len(followups)<30:
                    followups.append({**r,"observed_tick":last_tick_row if last_tick_row and last_tick_row["time"]==r["time"] else None})
            elif event=="CORE_FVG_VALIDITY_CHANGED" and any(g["fvg_id"]==r["fvg_id"] for g in accepted_groups):
                if len(followups)<30: followups.append(r)
            elif event=="CORE_TESTER_DISPATCH_RESULT": entry_reasons[r["reason"] or "SUBMITTED"]+=1
            elif event=="TESTER_CORE_METRICS": native_metrics=r
            elif event=="CORE_CONTROLLER_SUMMARY": native_summary=r
            elif event=="TICK_CAPTURE_SUMMARY": capture_summary=r
            elif event=="TESTER_CORE_DEAL": deals.append(r)
            if event not in ("TICK","BOS_TRACKER_CLOSED_BAR"): continue
            if r.get("server_utc_offset_seconds")!=10800: raise ValueError("Unverified offset in this September/October run")
            validate_capture_timestamp(r["server_time"],r["time"],10800)
            if event=="TICK":
                if r["tick_index"]!=previous_tick+1 or r["time_msc"]<previous_msc:
                    raise ValueError("Missing/reordered tick; same-ms multiplicity must stay intact")
                previous_tick=r["tick_index"]; previous_msc=r["time_msc"]
                first=first or r["time"]; last=r["time"]
                last_tick_row={k:r[k] for k in ("time","server_time","tick_index","bid","ask")}
                row=r
            else:
                seconds={"M1":60,"M5":300,"M15":900,"H1":3600,"H4":14400}[r["timeframe"]]
                if (instant(r["time"])-instant(r["opened_at"])).total_seconds()<seconds:
                    raise ValueError("Future/forming candle was exposed")
                row={**r,"kind":"bar","symbol":"XAUUSD_o"}; total_bars+=1
            if replay_python:
                if engine is None: raise ValueError("Runtime broker metadata missing")
                engine.accept(row)
                if event=="TICK": equity.observe(engine,row)
    if not capture_summary or capture_summary["capture_halted"] or not capture_summary["terminal_cursor_evidence_valid"] or capture_summary["emitted_ticks"]!=previous_tick:
        raise ValueError("Incomplete/rejected native capture")
    if not native_summary or native_summary["controller_halted"] or native_summary["processed_ticks"]!=previous_tick:
        raise ValueError("Incomplete/rejected Core controller")
    if native_metrics is None: raise ValueError("No completed Strategy Tester metrics")
    report={"mode":"EXPERIMENTAL_REAL_TICK_CORE_BACKTEST","manifest":manifest,"raw_capture":str(capture),
            "raw_sha256":digest.hexdigest(),"ticks":previous_tick,"bars":total_bars,"first_utc":first,"last_utc":last,
            "canonical_approved_setups":0,"native_groups":native_summary["experimental_groups"],
            "native_rejected_groups":native_summary["experimental_rejected_groups"],
            "native_group_reasons":dict(group_reasons),"native_entry_reasons":dict(entry_reasons),
            "native_metrics":native_metrics,"native_deals":deals,"native_group_examples":native_groups[:30],
            "native_accepted_group_examples":accepted_groups,"accepted_group_followups":followups,
            "native_return_reasons":dict(return_reasons),"native_configuration":config_evidence,
            "trade_run_validity":"VERIFIED_CONFIGURATION" if config_evidence and all(v in config_evidence["status"] for v in ("JOURNAL OK","PAIR LIMITS OK","CALENDAR_OK")) and config_evidence.get("simulated_transport_only") is True and config_evidence.get("real_and_demo_auto_submission") is False else
               "DETECTION_COMPARISON_ONLY_CONFIGURATION_NOT_VERIFIED",
            "automatic_demo_ready":False,"cost_limitations":"Zero commission/slippage Python hypothesis; MT5 uses its own modeled costs, neither proves historical live costs",
            "agent_original_raw_archive_incident":"MT5 cleared previous agent sandbox files; original October7 normalized inputs remain, old raw file is unavailable"}
    if engine:
        report["python"]={**results(engine,equity),"groups":engine.accepted_groups,
                          "group_reasons":dict(engine.group_rejections)}
        report["parity"]={"same_real_ticks":True,"native_fvgs":native_summary["fvgs"],
                         "python_fvgs":len(engine.automatic.gaps),
                         "native_groups":native_summary["experimental_groups"],"python_groups":engine.accepted_groups,
                         "fully_verified":False,"limitations":["Python paired legs atomic at observed quote vs MT5 two simulated orders",
                            "Python forces stop/TP model from quotes; MT5 broker simulator supplies deal ordering/costs",
                            "Execution and partial-FVG policies remain fail-closed; grouped discovery is a hypothesis"]}
    if out.exists(): raise ValueError("Choose a fresh output directory")
    out.mkdir(parents=True)
    (out/"report.json").write_text(json.dumps(encode(report),indent=2)+"\n",encoding="utf-8")
    if engine:
        (out/"python-events.jsonl").write_text("".join(json_line(e) for e in engine.events),encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--capture",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    p.add_argument("--native-only",action="store_true");a=p.parse_args()
    r=replay(a.capture,a.manifest,a.out,not a.native_only)
    print(json.dumps(encode({k:r[k] for k in ("ticks","first_utc","last_utc","native_groups","native_group_reasons","native_metrics","automatic_demo_ready")}),indent=2))
