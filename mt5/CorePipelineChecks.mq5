#property strict
#property script_show_inputs
#define TRADERLAB_CORE_CHECKS
#include "Include/TraderLab/CoreController.mqh"
int failures=0,checks=0;
void Check(const bool ok,const string name) { checks++; if(!ok) { failures++; Print("Core check failed: ",name); } }
bool Near(const double a,const double b) { return MathAbs(a-b)<1e-8; }
void SourcedCalendarChecks()
{
   TLCoreCalendar current,next; string day; bool blocked;
   Check(current.Load("TraderLab-core-calendar-20261013.csv"),"reviewed current calendar packet present");
   Check(current.Day(1791887580,day) && day=="2026-10-13","actual sourced day available at verification epoch");
   Check(current.Day(1791925199,day) && !current.Day(1791925200,day),"actual NY close boundary respected");
   Check(current.News(1791980100,blocked) && blocked,"actual CPI restriction starts Oct14 12:15 UTC");
   Check(current.News(1791980099,blocked) && !blocked,"actual CPI pre-window remains unrestricted");
   Check(current.EntryUntil(1791887580)==1791925200,"one-day entry permission expires before later CPI");
   Check(next.Load("TraderLab-core-calendar-20261014.csv"),"separate next-day packet present");
   Check(next.EntryUntil(1791979200)==1791980100,"next-day pair deadline cannot cross actual CPI window");
   // These are real calendar facts, not an executed trade or an approved closure lead.
}
void LifecycleScenarios()
{
   // Synthetic broker receipts exercise the SAME reducers used by ObserveDeal.
   // No request is submitted; these are not historical strategy trades.
   for(int side=-1;side<=1;side+=2)
   {
      double levels[]={4146,4143}; TLPlan plan; string todo;
      Check(TLCoreLevelPlan(side,levels,plan,todo),"scenario canonical dual plan");
      TLCoreTrade t; ZeroMemory(t);
      t.setup="SYNTHETIC CHECK ONLY"; t.side=side; t.reference=plan.reference;
      t.planned=plan.entry1; t.shared_stop=plan.stop; t.be_known=true;
      TLCoreTrade base=t; double price=t.planned+(side==1?.22:0);
      Check(!TLCorePairedEvidence(t),"no receipt is not two positions");
      Check(TLCoreTradeFill(t,0,1001,2001,.01,price,-.05),"first full receipt");
      Check(!TLCorePairedEvidence(t),"missing second receipt blocks pair completion");
      Check(!TLCoreTradeFill(t,1,1002,2002,.005,price,-.05) && t.legs[1].entry_deal==0,
            "partial second leg never promoted");
      Check(TLCoreTradeFill(t,1,1002,2002,.01,price,-.05) && TLCorePairedEvidence(t),
            "distinct .01 positions fully evidenced");
      Check(Near(t.legs[0].target,plan.tp1) && Near(t.legs[1].target,plan.tp2) &&
            Near(t.legs[0].stop,plan.stop) && Near(t.legs[1].stop,plan.stop),"two targets and canonical shared SL");
      TLCoreTrade duplicate_position=base;
      TLCoreTradeFill(duplicate_position,0,1001,2001,.01,price,0);
      TLCoreTradeFill(duplicate_position,1,1002,2001,.01,price,0);
      Check(!TLCorePairedEvidence(duplicate_position),"one position identifier is not a hedged pair");
      bool duplicate,unknown; double be;
      Check(!TLCoreTradeExit(t,0,DEAL_REASON_TP,3001,999,.01,5.75,duplicate,unknown),
            "unrelated position cannot claim TP1");
      Check(TLCoreTradeExit(t,0,DEAL_REASON_CLIENT,3001,2001,.01,5.75,duplicate,unknown) && !t.tp1_closed,
            "manual/emergency close is not TP1");
      t=base; TLCoreTradeFill(t,0,1001,2001,.01,price,-.05); TLCoreTradeFill(t,1,1002,2002,.01,price,-.05);
      Check(TLCoreTradeExit(t,0,DEAL_REASON_TP,3001,2001,.01,5.75,duplicate,unknown) &&
            !duplicate && !unknown && t.tp1_closed && !t.legs[0].open && t.legs[1].open,"TP1 retains second position");
      Check(TLCoreBreakEven(side,false,true,false,t.reference,t.planned,t.legs[1],be) &&
            Near(be,TLDualBreakEven(side,plan)),"shared BE after TP1");
      Check(TLCoreTradeExit(t,0,DEAL_REASON_TP,3001,2001,.01,5.75,duplicate,unknown) && duplicate,
            "repeated TP receipt idempotent");
      TLCoreTrade restarted=base;
      TLCoreTradeFill(restarted,0,1001,2001,.01,price,-.05);
      TLCoreTradeFill(restarted,1,1002,2002,.01,price,-.05);
      TLCoreTradeExit(restarted,0,DEAL_REASON_TP,3001,2001,.01,5.75,duplicate,unknown);
      double restored_be;
      Check(restarted.tp1_closed && restarted.legs[1].open &&
            TLCoreBreakEven(side,false,true,false,restarted.reference,restarted.planned,restarted.legs[1],restored_be) &&
            Near(restored_be,be),"restart reconstructs pending BE from broker history");
      restarted.be_sent=true;
      Check(TLCoreTradeExit(restarted,1,DEAL_REASON_SL,3002,2002,.01,.2,duplicate,unknown) && unknown,
            "actual BE stop consumes exit but blocks unknown daily count");
      Check(Near(restarted.legs[1].net,.15),"BE exit retains actual net costs");
      t.be_sent=true;
      Check(TLCoreTradeExit(t,1,DEAL_REASON_TP,3002,2002,.01,9.75,duplicate,unknown) &&
            !unknown && !t.legs[1].open && Near(t.legs[1].net,9.7),"TP2 after BE completes actual receipts");
      TLCoreTrade emergency=base;
      TLCoreTradeFill(emergency,0,1001,2001,.01,price,0); TLCoreTradeFill(emergency,1,1002,2002,.01,price,0);
      Check(TLCoreTradeExit(emergency,0,DEAL_REASON_EXPERT,3001,2001,.01,-.2,duplicate,unknown) &&
            TLCoreTradeExit(emergency,1,DEAL_REASON_EXPERT,3002,2002,.01,-.3,duplicate,unknown) &&
            !emergency.legs[0].open && !emergency.legs[1].open && !emergency.tp1_closed,
            "authoritative emergency exits close both without inventing TP/BE");
   }
}
void OnStart()
{
   // Synthetic reducer/calendar cases. No broker transport, orders or synthetic market capture.
   Check(!TL_DEMO_DISPATCH_REVIEWED,"dispatch locked");
   Check(TLDemoIntentDealEntry("PACKAGE:leg1",DEAL_ENTRY_IN) &&
         !TLDemoIntentDealEntry("PACKAGE:leg1",DEAL_ENTRY_OUT),"TP/SL comment cannot masquerade as opening fill");
   Check(TLDemoIntentDealEntry("emergency:77",DEAL_ENTRY_OUT) &&
         !TLDemoIntentDealEntry("emergency:77",DEAL_ENTRY_IN),"entry cannot masquerade as emergency closure");
   Check(!TLDemoIntentDealEntry("MOD:77:Leg",DEAL_ENTRY_OUT),"BE reconciliation requires protective-level evidence");
   LifecycleScenarios();
   SourcedCalendarChecks();
   MqlTick observed={}; observed.time_msc=12345; observed.bid=4146.5; observed.ask=4146.7;
   Check(TLDemoReturnQuote(observed,12345,4146.5,4146.7),"genuine first-return execution quote");
   Check(!TLDemoReturnQuote(observed,12344,4146.5,4146.7),"later same-price return cannot substitute");
   Check(!TLDemoReturnQuote(observed,12345,4146.5,4146.8),"same-ms ask substitution rejected");
   observed.time_msc=12445; observed.bid=4146.51; observed.ask=4146.71;
   Check(TLDemoPairQuote(observed,12345,4146.5,4146.7,true,100,500,.3,2,.01),
         "second leg uses observed quote inside explicit execution budget, not a new retest");
   Check(!TLDemoPairQuote(observed,12345,4146.5,4146.7,true,501,500,.3,2,.01),"pair deadline enforced");
   Check(!TLDemoPairQuote(observed,12345,4146.5,4146.7,true,100,500,.1,2,.01),"pair spread enforced");
   Check(!TLDemoPairQuote(observed,12345,4146.5,4146.7,true,100,500,.3,0,.01),"pair slippage enforced");
   Check(!TLDemoPairQuote(observed,12446,4146.5,4146.7,true,100,500,.3,2,.01),"stale second quote rejected");
   Check(!TLDemoPairQuote(observed,12345,4146.5,4146.7,true,100,0,.3,2,.01),"unset pair budget blocked");
   observed.bid=4146.49; observed.ask=4146.69;
   Check(TLDemoPairQuote(observed,12345,4146.5,4146.7,false,100,500,.3,2,.01),"sell execution budget mirrors broker side");
   MqlTick between[]; ArrayResize(between,3);
   for(int i=0;i<3;i++) { between[i]=observed; between[i].time_msc=12345+i; between[i].bid=4146.5; }
   Check(TLDemoUnfilledHistory(between,true,4142,4146),"same-ms multiplicity/identical quotes allowed in execution guard");
   between[1].bid=4145.99;
   Check(!TLDemoUnfilledHistory(between,true,4142,4146),"hidden intermediate partial fill blocks second leg");
   between[1].bid=4146.5; between[1].time_msc=12344;
   Check(!TLDemoUnfilledHistory(between,true,4142,4146),"reordered terminal history blocks second leg");
   between[1].time_msc=12345;
   Check(TLDemoUnfilledHistory(between,false,4147,4150),"sell unfilled history checked symmetrically");
   TLCorePackage approved;
   Check(TLCorePackageRow("PACKAGE|Example|UnitCheck|Canonical16|1000|F|F:C3|B1;B2",approved),"explicit labeled package");
   Check(!TLCorePackageRow("PACKAGE|Example|UnitCheck|Canonical16|1000|F|F:C3|B1;B1",approved),"duplicate BOS membership rejected");
   Check(!TLCorePackageRow("PACKAGE|Example|UnitCheck|Canonical16|1000x|F|F:C3|B1;B2",approved),"strict approval epoch");
   TLCorePackageRow("PACKAGE|Example|UnitCheck|Canonical16|1000|F|F:C3|B1;B2",approved); approved.loaded=1100;
   Check(!TLCorePackageAvailable(approved,1100999) && TLCorePackageAvailable(approved,1101000),"coarse operator receipt never backdated");
   double owner_levels[]={4146,4143}; TLPlan reviewed; string block;
   Check(TLCorePackageGeometry(1,owner_levels,4142,4147,0,reviewed,block) &&
         reviewed.count==2 && Near(reviewed.stop,4140) && Near(reviewed.reference,4146.5),"canonical owner16/51 reviewed dual plan");
   Check(!TLCorePackageGeometry(1,owner_levels,4142,4147,1,reviewed,block),"operator cannot approve PARTIAL");
   Check(!TLCorePackageGeometry(1,owner_levels,4142,4147,2,reviewed,block),"operator cannot approve FULL");
   Check(!TLCorePackageGeometry(1,owner_levels,4144,4147,0,reviewed,block),"operator cannot move BOS/FVG bounds");
   string approval_path="TraderLab-CorePipelineChecks-approvals.csv"; FileDelete(approval_path);
   TLCorePackages package_file;
   Check(package_file.Load("", "XAUUSD_o",1100) && package_file.Append(approval_path,"XAUUSD_o",approved,1100),
         "chart approval creates scoped file from actual membership");
   Check(!package_file.Append(approval_path,"XAUUSD_o",approved,1100),"chart approval duplicate never overwrites");
   TLCorePackages restarted_packages; TLCorePackage restored_package;
   Check(restarted_packages.Load(approval_path,"XAUUSD_o",1200) && restarted_packages.Read(0,restored_package) &&
         restored_package.members=="B1;B2" && restored_package.loaded==1200,"approval restart receipt not backdated");
   Check(!restarted_packages.Load(approval_path,"XAUUSD",1200),"chart approval wrong symbol blocked");
   FileDelete(approval_path);
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
      Check(first.FreezePackage("TESTPACKAGE","immutable payload"),"durable operator membership");
      Check(first.Stop("TEST ONLY",1000) && first.Halted(),"operator emergency persisted with Algo OFF");
   }
   {
      TLCoreConsumption restarted;
      Check(restarted.OpenFixture(journal,"TEST ONLY") && restarted.Seen("TEST:BOS"),"restart retains consumed BOS");
      Check(restarted.Halted(),"restart never clears operator emergency");
      Check(restarted.FreezePackage("TESTPACKAGE","immutable payload") &&
            !restarted.FreezePackage("TESTPACKAGE","changed payload"),"restart cannot mutate approved package");
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
      Check(cal.EntryUntil(1001)==3100 && cal.EntryUntil(3999)==0 && cal.EntryUntil(6001)==10000,
            "two-leg execution cannot cross session/news/coverage entry deadline");
      FileDelete(path); // Only this script's synthetic fixture.
   }
   Check(TLCoreEpoch("1000") && !TLCoreEpoch("1000junk") && !TLCoreEpoch("-1") &&
         !TLCoreEpoch("0") && TLCoreEpoch("0",true),"calendar strict epochs");
   Check(TLCoreDayWindow("",0,0,"A",1000,5000) && TLCoreDayWindow("A",1000,5000,"A",1000,5000),
         "initial and restart calendar window immutable");
   Check(!TLCoreDayWindow("A",1000,5000,"B",4000,8000),"separate files cannot bypass unresolved overlapping daily reset");
   Check(!TLCoreDayWindow("A",1000,5000,"A",1000,6000),"same day definition cannot change after restart");
   Check(TLCoreDayWindow("A",1000,5000,"B",5000,9000),"non-overlapping sourced day advance allowed");
   f=FileOpen(path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(f!=INVALID_HANDLE)
   {
      FileWriteString(f,"SYDNEY_NY_NEWS|SYNTHETIC|1000|10000\r\nDAY|A|1000|10000|900\r\nNEWS|CPI|4000x|0|900\r\n");
      FileClose(f); TLCoreCalendar bad_cal;
      Check(!bad_cal.Load(path),"malformed news timestamp blocks even with valid session");
      FileDelete(path);
   }
   else Check(false,"calendar fault fixture");
   Print("TraderLab Core pipeline checks failures=",failures," checks=",checks," dispatch_locked=",!TL_DEMO_DISPATCH_REVIEWED,
         " broker_orders_sent=0; reducer tests only, transport/runtime approval pending");
}
