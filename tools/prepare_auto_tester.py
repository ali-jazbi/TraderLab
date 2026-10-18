"""Build explicit EXPERIMENTAL tester calendar/config; no terminal or broker execution."""
import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import json

def prepare(root, start, end, experiment, run):
    # Oct18 review: existing source packet covers Oct16 NY close. Extend ONLY
    # the explicit historical study bound for the prespecified Oct14-16 holdout.
    if not date(2026,9,21) <= start < end <= date(2026,10,17):
        raise ValueError("This source-reviewed packet only covers 2026-09-21 through 2026-10-16")
    if experiment not in (1,2,3) or not run or Path(run).name != run or any(c in run for c in '/\\:'):
        raise ValueError("Explicit experimental policy and plain output basename required")
    root = Path(root)
    source = json.loads((root / "configs/core-calendar.sources-20261013.json").read_text())
    sydney_hour,sydney_minute=map(int,source['session_profile']['sydney_open'].split(':'))
    ny_hour,ny_minute=map(int,source['session_profile']['new_york_close'].split(':'))
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            opening = datetime.combine(d, datetime.min.time()).replace(hour=sydney_hour, minute=sydney_minute, tzinfo=ZoneInfo("Australia/Sydney")).astimezone(timezone.utc)
            closing = datetime.combine(d, datetime.min.time()).replace(hour=ny_hour, minute=ny_minute, tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)
            days.append({"id": d.isoformat(), "start": opening, "end": closing})
        d += timedelta(days=1)
    # Explicit TESTER-ONLY hypothesis; never publish this allocation as an owner rule.
    for a,b in zip(days,days[1:]):
        a["end"] = min(a["end"], b["start"])
    known = datetime(2026,1,1,tzinfo=timezone.utc)  # EX_POST schedule assumption, not asserted publication evidence.
    epoch = lambda x: int(x.timestamp())
    name = "EXPERIMENTAL_TESTER_ONLY:overlap_clipped_at_next_sydney_open:EX_POST_NEWS"
    rows = [f"SYDNEY_NY_NEWS|{name}|{epoch(days[0]['start'])}|{epoch(days[-1]['end'])}"]
    for v in days:
        rows.append(f"DAY|{v['id']}|{epoch(v['start'])}|{epoch(v['end'])}|{epoch(known)}")
    news = []
    for v in source["events"]:
        hh,mm = map(int,v["local_time"].split(":"))
        t = datetime.fromisoformat(v["date"]).replace(hour=hh,minute=mm,tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)
        if days[0]["start"] <= t <= days[-1]["end"]:
            rows.append(f"NEWS|{v['name']}|{epoch(t)}|0|{epoch(known)}")
            news.append({"name":v["name"],"scheduled_at":t.isoformat(),"available_at":known.isoformat(),"source":v["source"]})
    target = root / "work/auto-core"
    target.mkdir(parents=True,exist_ok=True)
    calendar = target / f"{run}.calendar.csv"
    calendar.write_text("\n".join(rows)+"\n",encoding="utf-8")
    inputs = {
        "InpBrokerSymbol":"XAUUSD_o","InpLogFile":f"{run}.jsonl",
        "InpServerUtcOffsetSeconds":10800,"InpTehranUtcOffsetSeconds":12600,
        "InpCoreMagic":2026101401,"InpCoreCalendarFile":"TraderLab-auto-tester-calendar.csv",
        "InpNewsClosureLeadSeconds":120,"InpCoreOperatorPackages":"",
        "InpCorePanel":"false","InpRequestCoreDemoExecution":"false",
        "InpCorePairMaxMilliseconds":1000,"InpCoreMaxSpreadPrice":0.22,
        "InpCoreMaxSlippagePoints":0,"InpExperimentalAutoCoreTester":experiment,
        "InpTesterStress":"false"
    }
    preset = target / f"{run}.set"
    preset.write_text("".join(f"{k}={v}\n" for k,v in inputs.items()),encoding="utf-16")
    ini = target / f"{run}.ini"
    ini.write_text("[Experts]\nAllowLiveTrading=0\n[Tester]\nExpert=TraderLab\\TraderLabAutoTester.ex5\n"
                   f"ExpertParameters={preset.name}\nSymbol=XAUUSD_o\nPeriod=M1\nModel=4\nExecutionMode=0\n"
                   f"FromDate={start:%Y.%m.%d}\nToDate={end:%Y.%m.%d}\nOptimization=0\n"
                   f"Report={target / (run+'.html')}\nReplaceReport=0\nShutdownTerminal=1\n"
                   "Deposit=1000\nCurrency=USD\nLeverage=1:200\nUseLocal=1\nUseRemote=0\nUseCloud=0\nVisual=0\n",encoding="utf-16")
    manifest={"mode":"EXPERIMENTAL_TESTER_ONLY","run":run,"start":str(start),"end_exclusive":str(end),
              "grouping":("same_frame_at_confirmed_availability", "all_frames_at_confirmed_availability",
                          "same_frame_earliest_qualified_equal_level_v1")[experiment-1],
              "day_overlap":"EXPERIMENTAL clipped at next Sydney opening; owner allocation unresolved",
              "news_availability":"EX_POST schedule assumed preknown; NOT historical as-of availability proof",
              "news":news,"source_urls":source["source_urls"]+['https://www.bls.gov/schedule/2026/09_sched.htm','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'],
              "days":[{**d,"start":d["start"].isoformat(),"end":d["end"].isoformat(),"available_at":known.isoformat()} for d in days],
              "automatic_demo_approved":False,"real_broker_orders_enabled":False,"tick_model":4,
              "execution_delay_model_ms":0,"limits_are_trial_caps_not_broker_guarantees":True}
    (target / f"{run}.manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {"calendar":str(calendar),"preset":str(preset),"ini":str(ini)}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start",type=date.fromisoformat,required=True)
    p.add_argument("--end",type=date.fromisoformat,required=True)
    p.add_argument("--experiment",type=int,choices=(1,2,3),required=True)
    p.add_argument("--run",required=True)
    a=p.parse_args()
    print(json.dumps(prepare(Path(__file__).resolve().parents[1],a.start,a.end,a.experiment,a.run),indent=2))
