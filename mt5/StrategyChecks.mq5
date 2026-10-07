#property strict
#property script_show_inputs
#include "Include/TraderLab/Rules.mqh"
#include "Include/TraderLab/RequestGuard.mqh"
#include "Include/TraderLab/EventLog.mqh"
#include "Include/TraderLab/Detection.mqh"
#include "Include/TraderLab/TickCapture.mqh"

int failures=0;
void Check(bool condition,string name) { if(!condition) { Print("FAIL: ",name); failures++; } }
bool Equal(double a,double b) { return MathAbs(a-b)<1e-8; }

MqlTick TestTick(const long millis,const double bid,const uint flags=6)
{
   MqlTick tick;
   ZeroMemory(tick);
   tick.time=(datetime)(millis/1000); tick.time_msc=millis;
   tick.bid=bid; tick.ask=bid+0.2; tick.flags=flags;
   return tick;
}

void TickCursorChecks()
{
   const long start=1791360000123;
   MqlTick baseline[1]; baseline[0]=TestTick(start,4146);
   TLTickCursor cursor; string reason; int skip;
   Check(cursor.Initialize(baseline,reason),"cursor starts at explicit snapshot, emits no baseline history");
   MqlTick normal[2]; normal[0]=baseline[0]; normal[1]=TestTick(start+1,4147);
   Check(cursor.Consume(normal,skip,reason) && skip==1 && ArraySize(normal)-skip==1,
         "one normal tick after startup");
   Check(cursor.Millisecond()==start+1,"exact millisecond retained");
   MqlTick precision=TestTick((long)D'2026.10.07 08:54:41'*1000+864,4133.97);
   Check(TLIso(precision.time,10800,(int)(precision.time_msc%1000))=="\"2026-10-07T05:54:41.864Z\"",
         "recovered raw tick preserves exact UTC milliseconds");
   MqlTick raw_change=baseline[0]; raw_change.volume_real=1;
   Check(!TLSameTick(raw_change,baseline[0]),"dedupe compares real volume as well as quotes and flags");
   MqlTick overlap[1]; overlap[0]=normal[1];
   Check(cursor.Consume(overlap,skip,reason) && skip==1,"overlap emits zero duplicate ticks");
   MqlTick delayed[4]; delayed[0]=overlap[0];
   delayed[1]=TestTick(start+2,4148); delayed[2]=TestTick(start+3,4149); delayed[3]=TestTick(start+4,4150);
   Check(cursor.Consume(delayed,skip,reason) && skip==1 && ArraySize(delayed)-skip==3,
         "delayed callback drains three terminal-history ticks in chronological order");
   MqlTick same_ms[3]; same_ms[0]=delayed[3];
   same_ms[1]=TestTick(start+4,4151); same_ms[2]=same_ms[1];
   Check(cursor.Consume(same_ms,skip,reason) && skip==1 && cursor.BoundaryCount()==3,
         "same millisecond keeps distinct and repeated identical tick occurrences");
   Check(cursor.Consume(same_ms,skip,reason) && skip==3,
         "whole ordered same-ms prefix is skipped on next drain");
   MqlTick appended[4];
   for(int i=0;i<3;i++) appended[i]=same_ms[i];
   appended[3]=TestTick(start+4,4151,2);
   Check(cursor.Consume(appended,skip,reason) && skip==3 && cursor.BoundaryCount()==4,
         "raw flags distinguish a new same-ms tick even when quotes match");
   MqlTick missing[1]; missing[0]=TestTick(start+5,4152);
   Check(!cursor.Consume(missing,skip,reason) && reason=="boundary_prefix_missing" &&
         cursor.Millisecond()==start+4,"missing overlap fails closed without advancing cursor");
   Check(!cursor.Consume(same_ms,skip,reason) && reason=="boundary_prefix_missing",
         "truncated boundary cannot prove prior tick multiplicity");
   appended[0].volume=1;
   Check(!cursor.Consume(appended,skip,reason) && reason=="boundary_prefix_changed",
         "mutated raw prefix produces explicit ambiguity");
   appended[0]=same_ms[0]; appended[1]=same_ms[2]; appended[2]=same_ms[0];
   Check(!cursor.Consume(appended,skip,reason) && reason=="boundary_prefix_changed",
         "reordered same-ms prefix is ambiguous");
   for(int i=0;i<3;i++) appended[i]=same_ms[i];
   appended[3]=TestTick(start+4,4151,2);
   MqlTick regressed[5];
   for(int i=0;i<4;i++) regressed[i]=appended[i];
   regressed[4]=TestTick(start+3,4152);
   Check(!cursor.Consume(regressed,skip,reason) && reason=="history_not_chronological",
         "whole batch checked before any suffix can be emitted");
   MqlTick before_start[2]; before_start[0]=TestTick(start-1,4145); before_start[1]=baseline[0];
   TLTickCursor startup; Check(startup.Initialize(baseline,reason),"fresh test cursor");
   Check(!startup.Consume(before_start,skip,reason) && reason=="boundary_prefix_missing",
         "historical ticks before capture startup are not emitted");
   MqlTick empty[];
   Check(!startup.Consume(empty,skip,reason) && reason=="empty_history","empty history is ambiguous");
   normal[1].time=(datetime)((start+1)/1000+1);
   Check(!startup.Consume(normal,skip,reason) && reason=="invalid_raw_tick",
         "raw seconds and milliseconds must agree, never synthesized");
}

void HistoryAuthorityChecks()
{
   const long start=1791360000123;
   MqlTick baseline[3]; baseline[0]=TestTick(start-1,4145);
   baseline[1]=TestTick(start,4146); baseline[2]=baseline[1];
   TLTickCursor cursor; string reason; int skip,direct;
   Check(cursor.Initialize(baseline,reason) && cursor.BoundaryCount()==2,
         "startup history snapshot excludes all earlier milliseconds and identical baseline records");
   MqlTick history[4]; history[0]=baseline[1]; history[1]=baseline[2];
   history[2]=TestTick(start,4147); history[3]=history[2];
   MqlTick quote=history[3]; quote.flags=2; quote.volume=9; quote.volume_real=9;
   quote.last=4148; quote.bid=4148; quote.ask=4149;
   Check(TLConsumeHistory(cursor,history,quote,true,skip,direct,reason) && skip==2 && direct==-1,
         "run04 same time_msc differing raw SymbolInfoTick fields does not halt history capture");
   long emitted=ArraySize(history)-skip, matches=(direct>=skip && direct>=0)?1:0;
   long recovered=emitted-matches;
   Check(emitted==2 && recovered==2 && matches==0 && cursor.BoundaryCount()==4,
         "unmatched callback counters reconcile and preserve identical same-ms suffix ticks");
   quote=TestTick(start+100,4150);
   Check(TLConsumeHistory(cursor,history,quote,true,skip,direct,reason) && skip==4 && direct==-1,
         "history lagging current quote snapshot is valid overlap with no synthetic emission");
   MqlTick caught_up[5]; for(int i=0;i<4;i++) caught_up[i]=history[i];
   caught_up[4]=TestTick(start+1,4149);
   Check(TLConsumeHistory(cursor,caught_up,quote,true,skip,direct,reason) && skip==4 && direct==-1,
         "lagging history later emits every unseen occurrence without requiring quote identity");
   quote=TestTick(start-100,4140);
   MqlTick newer_history[2]; newer_history[0]=caught_up[4]; newer_history[1]=TestTick(start+2,4150);
   Check(TLConsumeHistory(cursor,newer_history,quote,true,skip,direct,reason) && skip==1,
         "older quote snapshot never limits authoritative history");
   TLTickCursor mutated; Check(mutated.Initialize(baseline,reason),"mutation test baseline");
   history[0].flags=2;
   Check(!TLConsumeHistory(mutated,history,quote,true,skip,direct,reason) &&
         reason=="boundary_prefix_changed" && mutated.Millisecond()==start,
         "history boundary mutation still fails closed regardless of snapshot");
   history[0]=baseline[1]; history[1]=history[2]; history[2]=baseline[2];
   Check(!TLConsumeHistory(mutated,history,quote,true,skip,direct,reason) && reason=="boundary_prefix_changed",
         "history boundary reordering still fails closed regardless of snapshot");
}

void OnStart()
{
   TickCursorChecks();
   HistoryAuthorityChecks();
   TLPlan p; string todo;
   Check("{"+TLCandidateEpoch(D'2026.10.07 08:23:00')+"}"==
         "{\"candidate_server_epoch\":1791361380}","candidate epoch generates numeric JSON");
   Check("{"+TLCandidateEpoch((datetime)0)+"}"==
         "{\"candidate_server_epoch\":0}","zero candidate epoch generates numeric JSON");
   Check(TLZonedIso(D'2026.07.01 12:00:00',10800,12600,123)=="\"2026-07-01T12:30:00.123+03:30\"",
         "GMT+3 server becomes explicit Tehran offset, not UTC");
   Check(TLZonedIso(D'2026.01.15 11:00:00',7200,12600,123)=="\"2026-01-15T12:30:00.123+03:30\"",
         "GMT+2 server keeps Tehran strategy time");
   double dual[2]={4146,4143};
   Check(TLCorePlan(1,dual,0,p,todo),"canonical-A valid");
   Check(p.count==2 && Equal(p.stop,4140) && Equal(p.tp1,4152) && Equal(p.tp2,4156),"canonical-A levels");
   double boundary[2]={4146,4144};
   Check(!TLCorePlan(1,boundary,0,p,todo) && todo=="TODO_STRATEGY_UNRESOLVED:single_core_sl_pips","20 pip needs single SL");
   Check(TLCorePlan(1,boundary,40,p,todo) && p.count==1 && Equal(p.entry1,4146),"20 pip Buy only highest");
   Check(TLCorePlan(-1,boundary,40,p,todo) && p.count==1 && Equal(p.entry1,4144),"20 pip Sell only lowest");
   double forty[2]={4146,4142};
   Check(TLCorePlan(1,forty,0,p,todo) && p.count==2,"40 inclusive");
   double tiny[2]={4146,4145.5};
   Check(!TLCorePlan(1,tiny,40,p,todo),"sub10 unresolved");
   Check(TLOBroken(1,4141,4143,4140) && !TLOBroken(1,4141,4143,4140.1),"canonical-C OB10 wick");
   Check(Equal(TLBreakEven(1,4146),4146.5) && Equal(TLBreakEven(-1,4146),4145.5),"BE mirrors");
   TLDailyGuard day; day.Reset();
   day.Close("same",-12,true); day.Close("same",-6,true);
   Check(day.StoppedCount()==1 && !day.halted,"dual stops count once");
   day.Close("second",-4,true); Check(day.halted,"two stopped setups");
   day.Reset(); day.Close("profit",100,false); Check(!day.halted && day.profit_reached,"100 continues");
   day.Close("profit2",10,false); Check(!day.halted,"continued TP");
   day.Close("next-stop",-4,true); Check(day.halted,"first subsequent stop halts");
   TLRequestGuard guard; string attempt,state,rate;
   for(int i=0;i<1000;i++)
   {
      bool allowed=guard.RecordBeforeSend("A"+(string)i,"H"+(string)i,1000,true,attempt,state,rate);
      Check(allowed,"request limit attempt "+(string)i);
   }
   Check(!guard.RecordBeforeSend("A1000","H1000",1000,true,attempt,state,rate) &&
         rate=="REQUEST_RATE_BLOCKED","short request cap blocks next");
   Check(guard.RecordBeforeSend("AFTER","HAFTER",301000,true,attempt,state,rate) &&
         state=="REQUEST_PENDING","short window expires");
   TLRequestGuard dedupe;
   Check(dedupe.RecordBeforeSend("CORE:S1:B1","same-intent",1,false,attempt,state,rate),"first action dispatch");
   Check(!dedupe.RecordBeforeSend("CORE:S1:B1","same-intent",2,false,attempt,state,rate) &&
         rate=="DUPLICATE_ACTION_SUPPRESSED","duplicate action suppressed");
   Check(!dedupe.RecordBeforeSend("CORE:S1:B1","different-intent",3,true,attempt,state,rate) &&
         rate=="REQUEST_ID_PAYLOAD_CONFLICT","same action ID rejects a different payload");
   Check(dedupe.Reconcile("CORE:S1:B1","REQUEST_TIMEOUT","transport-timeout",false,false),
         "timeout is recorded as unknown");
   Check(!dedupe.RecordBeforeSend("CORE:S1:B1","same-intent",4,true,attempt,state,rate) &&
         state=="REQUEST_TIMEOUT","unknown timeout cannot be resent");
   Check(dedupe.Reconcile("CORE:S1:B1","REQUEST_RECONCILED","order:O1",true,false),
         "broker order evidence reconciles timeout");
   Check(!dedupe.RecordBeforeSend("CORE:S1:B1","same-intent",5,true,attempt,state,rate),
         "reconciled order suppresses duplicate action");
   TLRequestGuard rejected;
   Check(rejected.RecordBeforeSend("CORE:S2:B1","intent-2",1,false,attempt,state,rate),"second action dispatch");
   Check(rejected.Reconcile("CORE:S2:B1","REQUEST_TIMEOUT","transport-timeout",false,false),"second action timeout");
   Check(!rejected.Reconcile("CORE:S2:B1","REQUEST_REJECTED","history:H1",false,false),
         "rejection without no-execution evidence is refused");
   Check(rejected.Reconcile("CORE:S2:B1","REQUEST_REJECTED","history:H1",false,true),
         "authoritative no-execution result reconciles");
   Check(rejected.RecordBeforeSend("CORE:S2:B1","intent-2",2,true,attempt,state,rate) &&
         attempt=="CORE:S2:B1:attempt:2","controlled retry after no-execution proof");
   Print("TraderLab native checks failures=",failures);
}
