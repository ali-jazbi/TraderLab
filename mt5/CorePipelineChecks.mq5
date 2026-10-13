#property strict
#property script_show_inputs
#define TRADERLAB_CORE_CHECKS
#include "Include/TraderLab/CoreController.mqh"
int failures=0,checks=0;
void Check(const bool ok,const string name) { checks++; if(!ok) { failures++; Print("Core check failed: ",name); } }
bool Near(const double a,const double b) { return MathAbs(a-b)<1e-8; }
void OnStart()
{
   // Synthetic reducer/calendar cases. No broker transport, orders or synthetic market capture.
   Check(!TL_DEMO_DISPATCH_REVIEWED,"dispatch locked");
   TLDemoGateway gateway; Check(!gateway.CanDispatch(),"default disabled");
   TLCoreGuards g; ZeroMemory(g);
   g.group_confirmed=true; g.group_final=true; g.calendar=true; g.news=true; g.daily=true;
   g.restart=true; g.live_tick=true; g.single_be_defined=true;
   Check(TLCoreEntryBlock(g,0,true,true)=="","complete synthetic guards");
   g.group_final=false; Check(StringFind(TLCoreEntryBlock(g,0,true,true),"package_grouping")>=0,"unfinalized group"); g.group_final=true;
   g.startup_history=true; Check(TLCoreEntryBlock(g,0,true,true)=="STARTUP_HISTORY_NOT_EXECUTION_PROOF","warmup not executable"); g.startup_history=false;
   g.live_tick=false; Check(TLCoreEntryBlock(g,0,true,true)=="HISTORICAL_OR_DELAYED_QUOTE_NOT_EXECUTABLE","delayed quote"); g.live_tick=true;
   g.restart=false; Check(TLCoreEntryBlock(g,0,true,true)=="RESTART_RECONCILIATION_REQUIRED","restart guard"); g.restart=true;
   g.news=false; Check(TLCoreEntryBlock(g,0,true,true)=="SESSION_NEWS_CALENDAR_UNAVAILABLE","news coverage"); g.news=true;
   Check(TLCoreEntryBlock(g,1,true,true)=="TODO_STRATEGY_UNRESOLVED:partial_fill_policy","partial blocked");
   Check(TLCoreEntryBlock(g,2,true,true)=="FVG_FULL_FILL_INVALID","full invalid");
   Check(TLCoreEntryBlock(g,0,true,false)=="MISSED_EXACT_SIGNAL_QUOTE_NO_FILL","missed no fill");
   g.single_be_defined=false; Check(TLCoreEntryBlock(g,0,true,true)=="TODO_STRATEGY_UNRESOLVED:single_be_anchor","single BE unknown");
   Check(TLCoreEntryBlock(g,0,false,true)=="","dual shared BE answered");
   double levels[]={4146,4143}; TLPlan p; string todo;
   Check(TLCoreLevelPlan(1,levels,p,todo) && p.count==2 && Near(p.entry1,4146.5) && Near(p.entry2,4143.5) &&
         Near(p.stop,4140) && Near(p.tp1,4152.5) && Near(p.tp2,4156.5) && Near(TLDualBreakEven(1,p),4147),"buy raw-wick plan");
   Check(TLCoreLevelPlan(-1,levels,p,todo) && p.count==2 && Near(p.reference,4142.5) && Near(p.stop,4149) &&
         Near(p.tp1,4136.5) && Near(TLDualBreakEven(-1,p),4142),"sell mirrored plan");
   levels[1]=4144; Check(TLCoreLevelPlan(1,levels,p,todo) && p.count==1,"20 pip one BOS");
   TLCoreTrade a,b; ZeroMemory(a); ZeroMemory(b);
   a.setup="SYNTHETIC PAIR"; a.side=1; a.reference=4146.5; a.planned=4146.5; a.shared_stop=4140;
   b=a; b.planned=4143.5;
   Check(TLCoreCompatiblePair(a,b),"two selected BOS entries share canonical group and stop identity");
   b.planned=4144.5; Check(!TLCoreCompatiblePair(a,b),"20 pip cannot be two entries");
   b.planned=4143.5; b.reference=4143.5; Check(!TLCoreCompatiblePair(a,b),"shared TP/BE reference immutable");
   TLCoreLeg l; ZeroMemory(l);
   Check(!TLCoreFill(l,1,true,0,4148,1,7,.005,4142.52,-.05),"partial fill rejected");
   Check(l.entry_deal==0,"failed fill leaves reducer unchanged");
   Check(TLCoreFill(l,1,true,0,4148,1,7,.01,4142.52,-.05) && Near(l.stop,4138.52),"actual broker fill SL");
   Check(TLCoreFill(l,1,true,0,4148,1,7,.01,4142.52,-.05),"duplicate/restart fill idempotent");
   Check(!TLCoreFill(l,1,true,0,4148,1,7,.01,4142.52,-.06),"conflicting broker cost");
   double stop;
   Check(!TLCoreBreakEven(1,true,false,false,4142.32,4142.32,l,stop),"unknown single anchor");
   Check(TLCoreBreakEven(1,false,false,false,4142.32,4142.32,l,stop) && Near(stop,4142.82),"dual shared anchor");
   Check(!TLCoreExit(l,2,8,.01,5),"wrong position identifier");
   Check(!TLCoreExit(l,2,7,.005,5),"partial exit rejected");
   Check(TLCoreExit(l,2,7,.01,5) && Near(l.net,4.95),"actual net deal costs");
   Check(TLCoreExit(l,2,7,.01,5) && !TLCoreExit(l,2,7,.01,6),"restart exit exact evidence");
   Check(TLDemoResponseState(false,TRADE_RETCODE_REJECT,0,0)=="REJECTED","definitive rejection");
   Check(TLDemoResponseState(false,TRADE_RETCODE_REJECT,5,0)=="UNKNOWN","reject with order is not no-execution proof");
   Check(TLDemoResponseState(false,TRADE_RETCODE_TIMEOUT,0,0)=="UNKNOWN","timeout unknown no retry");
   Check(TLDemoResponseState(true,TRADE_RETCODE_DONE_PARTIAL,5,7)=="UNKNOWN","partial emergency state");
   Check(TLDemoResponseState(true,TRADE_RETCODE_DONE,5,7)=="ACK","ACK never actual fill");
   Check(TLCoreTickOrder(1,1000,2,1000) && !TLCoreTickOrder(1,1000,3,1001) && !TLCoreTickOrder(1,1000,2,999),"same-ms/missing/reorder");
   Check(TLCoreBeforeAvailability(1000,1,1000,2),"earlier same-ms occurrence consumed before availability");
   Check(!TLCoreBeforeAvailability(1000,2,1000,2),"as-of bars precede their same-ms dispatch tick");
   for(int side=-1;side<=1;side+=2)
   {
      TLFirstReturn r; ZeroMemory(r); MqlTick tick={}; tick.time_msc=1000;
      double ref=4142;
      Check(!TLAdvanceReturn(r,side,ref,ref,tick,1,1),"outbound touch not consumed");
      tick.time_msc=1001; Check(!TLAdvanceReturn(r,side,ref,ref+side*.02,tick,2,1),"outbound movement");
      tick.time_msc=1002; Check(TLAdvanceReturn(r,side,ref,ref-side*.01,tick,3,1) && r.consumed && !r.exact,"missed first return consumed");
      tick.time_msc=1003; Check(!TLAdvanceReturn(r,side,ref,ref,tick,4,1) && r.return_msc==1002,"late FVG cannot reset return");
   }
   Check(TLDemoNewsEntryBlocked(1000,1900) && !TLDemoNewsEntryBlocked(999,1900),"news boundary");
   Check(!TLDemoNewsCloseDue(1709,1900,10,true,true) && TLDemoNewsCloseDue(1710,1900,10,true,true) &&
         TLDemoNewsCloseDue(2801,1900,10,true,true),"close deadline and quote gap");
   TLDailyGuard daily; daily.Reset(); daily.Close("PAIR",-.1,true); daily.Close("PAIR",-.2,true);
   Check(daily.StoppedCount()==1 && !daily.halted,"paired stop once");
   daily.Close("NEXT",-.1,true); Check(daily.halted,"two stopped setups");
   string journal="TraderLab-CorePipelineChecks-consumed.csv";
   FileDelete(journal); // This named synthetic fixture only.
   {
      TLCoreConsumption first;
      Check(first.OpenFixture(journal,"TEST ONLY") && first.Consume("TEST:BOS",1234),"persist first return before execution");
      Check(first.Consume("TEST:BOS",9999),"repeat never resets first return");
   }
   {
      TLCoreConsumption restarted;
      Check(restarted.OpenFixture(journal,"TEST ONLY") && restarted.Seen("TEST:BOS"),"restart retains consumed BOS");
   }
   {
      TLCoreConsumption wrong_scope;
      Check(!wrong_scope.OpenFixture(journal,"OTHER") && !wrong_scope.Consume("OTHER:BOS",10000),"scope failure cannot write");
   }
   int broken=FileOpen(journal,FILE_WRITE|FILE_CSV|FILE_ANSI,'|',CP_UTF8);
   if(broken!=INVALID_HANDLE)
   {
      FileWrite(broken,"SCOPE","TEST ONLY"); FileWrite(broken,"RETURN","TEST:BOS"); FileClose(broken);
      TLCoreConsumption truncated;
      Check(!truncated.OpenFixture(journal,"TEST ONLY") && !truncated.Consume("TEST:OTHER",2000),"truncated journal fail closed");
   }
   else Check(false,"fault fixture write");
   FileDelete(journal);
   string path="TraderLab-CorePipelineChecks-synthetic.csv";
   int f=FileOpen(path,FILE_WRITE|FILE_CSV|FILE_ANSI,'|',CP_UTF8);
   if(f==INVALID_HANDLE) Check(false,"test calendar file");
   else
   {
      FileWrite(f,"SYDNEY_NY_NEWS","SYNTHETIC TEST ONLY",1000,10000);
      FileWrite(f,"DAY","A",1000,5000,900); FileWrite(f,"DAY","B",6000,10000,900);
      FileWrite(f,"NEWS","CPI",4000,0,900); FileClose(f);
      TLCoreCalendar cal; string day; bool blocked;
      Check(cal.Load(path) && cal.Day(4999,day) && day=="A","explicit UTC calendar");
      Check(!cal.Day(5500,day) && cal.Day(6000,day) && day=="B","DST-varying gap not guessed");
      Check(cal.News(3999,blocked) && blocked && !cal.News(10001,blocked),"known news/coverage");
      FileDelete(path); // Only this script's synthetic fixture.
   }
   Print("TraderLab Core pipeline checks failures=",failures," checks=",checks," dispatch_locked=",!TL_DEMO_DISPATCH_REVIEWED,
         " broker_orders_sent=0; reducer tests only, transport/runtime approval pending");
}
