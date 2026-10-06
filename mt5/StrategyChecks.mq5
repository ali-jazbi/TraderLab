#property strict
#property script_show_inputs
#include "Include/TraderLab/Rules.mqh"
#include "Include/TraderLab/RequestGuard.mqh"

int failures=0;
void Check(bool condition,string name) { if(!condition) { Print("FAIL: ",name); failures++; } }
bool Equal(double a,double b) { return MathAbs(a-b)<1e-8; }

void OnStart()
{
   TLPlan p; string todo;
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
   Check(dedupe.Reconcile("CORE:S1:B1","REQUEST_TIMEOUT","explicit timeout") &&
         dedupe.RecordBeforeSend("CORE:S1:B1","same-intent",3,true,attempt,state,rate) &&
         attempt=="CORE:S1:B1:attempt:2","explicit retry is counted");
   Print("TraderLab native checks failures=",failures);
}
