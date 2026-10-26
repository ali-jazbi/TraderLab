#ifndef TRADERLAB_RULES_MQH
#define TRADERLAB_RULES_MQH

// Canonical §§1,15,17–24,36. Unknown branches return a TODO, never a trading default.
const double TL_PIP = 0.1;
const double TL_LEG_LOTS = 0.01;

// Owner §52 (2026-10-12): SL uses actual executed fill; dual BE reuses TP reference.
double TLCoreEntryReference(const int side,const double bos_level) { return bos_level+side*5*TL_PIP; }
// First-directional-return reading: crossing is evidence, never an invented fill.
bool TLDirectionalReturn(const int side,const double reference,const double previous,const double current)
{
   if(side!=1 && side!=-1) return false;
   return side*(previous-reference)>0 && side*(current-reference)<=0;
}
double TLBosLevel(const MqlRates &bar,const int side) { return side==1?bar.high:bar.low; }
// Owner §54: directional shadow AND the existing qualification, no minimum size.
// step=0 keeps exact source-price comparison for pure fixtures without metadata.
bool TLHasBosWick(const MqlRates &bar,const int side,const double step=0)
{
   if((side!=1 && side!=-1) || !MathIsValidNumber(step) || step<0) return false;
   double wick=side==1?bar.high:bar.low;
   double body=side==1?MathMax(bar.open,bar.close):MathMin(bar.open,bar.close);
   if(step>0) { wick=MathRound(wick/step); body=MathRound(body/step); }
   return side==1?wick>body:wick<body;
}
void TLOrderBlockBounds(const MqlRates &bar,double &low,double &high) { low=bar.low; high=bar.high; }

struct TLPlan
{
   int count;
   double entry1;
   double entry2;
   double stop;
   double tp1;
   double tp2;
   double reference;
};

bool TLCorePlan(const int side, const double &prices[], const double single_sl_pips,
                TLPlan &plan, string &todo)
{
   ZeroMemory(plan);
   todo="";
   int size=ArraySize(prices);
   if((side!=1 && side!=-1) || size<1) { todo="INVALID_ANNOTATION"; return false; }
   double lowest=prices[0], highest=prices[0];
   for(int i=1;i<size;i++) { lowest=MathMin(lowest,prices[i]); highest=MathMax(highest,prices[i]); }
   double distance=(highest-lowest)/TL_PIP;
   // Floating tolerance is representation error, not a wider strategy threshold.
   if(size>1 && distance<10.0-1e-8) { todo="TODO_STRATEGY_UNRESOLVED:bos_distance_lt10"; return false; }
   if(size>1 && distance>40.0+1e-8) { todo="TODO_STRATEGY_UNRESOLVED:bos_distance_gt40"; return false; }
   plan.count=(size>1 && distance>20.0+1e-8)?2:1;
   plan.reference=(side==1)?highest:lowest;
   plan.entry1=plan.reference;
   plan.entry2=(side==1)?lowest:highest;
   if(plan.count==1)
   {
      if(single_sl_pips>0 && MathAbs(single_sl_pips-40)>1e-8) { todo="SINGLE_SL_DISTANCE_MUST_BE_40"; return false; }
      // A planned-anchor numeric preview only; no native paper or broker execution.
      plan.stop=plan.entry1-side*40*TL_PIP;
   }
   else plan.stop=(side==1)?lowest-30*TL_PIP:highest+30*TL_PIP;
   plan.tp1=plan.reference+side*60*TL_PIP;
   plan.tp2=plan.reference+side*100*TL_PIP;
   return true;
}

double TLSingleFillStop(const int side,const double executed_fill) { return executed_fill-side*40*TL_PIP; }
bool TLCoreLevelPlan(const int side,const double &levels[],TLPlan &plan,string &todo)
{
   if(!TLCorePlan(side,levels,40,plan,todo)) return false;
   // Selection and dual stop use raw wick levels; targets use offset entry references.
   double shift=side*5*TL_PIP;
   plan.entry1+=shift; plan.entry2+=shift; plan.reference+=shift; plan.tp1+=shift; plan.tp2+=shift;
   if(plan.count==1) plan.stop=plan.entry1-side*40*TL_PIP;
   return true;
}
double TLDualBreakEven(const int side,const TLPlan &plan) { return plan.reference+side*5*TL_PIP; }
double TLBreakEven(const int side, const double entry) { return entry+side*5*TL_PIP; }
bool TLOBroken(const int original_side,const double low,const double high,const double observed)
{
   return (original_side==1)?observed<=low-10*TL_PIP:observed>=high+10*TL_PIP;
}

bool TLBearishOBMomentum(const double low,const double high,const MqlRates &bar,const bool confirmed_big)
{
   // §52.4: crosses OB and closes beyond; no bullish/two-bar sequence inferred.
   return confirmed_big && bar.close<bar.open && bar.high>=low &&
          TLOBroken(1,low,high,bar.low) && bar.close<low;
}
bool TLReversePlan(const int side,const double original_entry,TLPlan &plan)
{
   ZeroMemory(plan);
   if((side!=1 && side!=-1) || !MathIsValidNumber(original_entry) || original_entry<=0) return false;
   // §§39,51–52: original planned Core entry; never apply a second BOS offset.
   plan.count=1; plan.entry1=original_entry; plan.reference=original_entry;
   plan.stop=TLSingleFillStop(side,original_entry); // Preview; SL reanchors to actual fill.
   plan.tp1=original_entry+side*60*TL_PIP; plan.tp2=original_entry+side*100*TL_PIP;
   return true;
}
string TLBreakerBlock(const int original_side,const bool executed,const bool stopped,const int entries,
                      const bool bos_broken,const bool ob_broken,const bool ifvg,const bool momentum)
{
   if(original_side!=1 && original_side!=-1) return "INVALID_DIRECTION";
   if(!executed) return "CORE_EXECUTION_REQUIRED";
   if(!stopped) return "CORE_ACTUAL_SL_REQUIRED";
   if(entries!=1) return "TODO_STRATEGY_UNRESOLVED:breaker_dual_parent";
   if(original_side!=1) return "TODO_STRATEGY_UNRESOLVED:reverse_buy_momentum";
   if(!bos_broken) return "REVERSE_BOS_BREAK_REQUIRED";
   if(!ob_broken) return "REVERSE_OB_10_PIP_BREAK_REQUIRED";
   if(!momentum) return "REVERSE_CONFIRMED_MOMENTUM_OB_BREAK_CLOSE_REQUIRED";
   if(!ifvg) return "REVERSE_IFVG_REQUIRED";
   return "TODO_STRATEGY_UNRESOLVED:reverse_ifvg_association_sequence_and_daily_count";
}

class TLDailyGuard
{
private:
   string stopped_ids[];
public:
   double closed_profit;
   bool profit_reached;
   bool halted;
   void Reset()
   {
      ArrayResize(stopped_ids,0);
      closed_profit=0; profit_reached=false; halted=false;
   }
   int StoppedCount() { return ArraySize(stopped_ids); }
   void Close(const string setup_id,const double pnl,const bool stopped)
   {
      bool prior=profit_reached;
      closed_profit+=pnl;
      if(stopped)
      {
         bool exists=false;
         for(int i=0;i<ArraySize(stopped_ids);i++) if(stopped_ids[i]==setup_id) exists=true;
         if(!exists) { int n=ArraySize(stopped_ids); ArrayResize(stopped_ids,n+1); stopped_ids[n]=setup_id; }
         halted=halted || prior || StoppedCount()>=2;
      }
      profit_reached=profit_reached || closed_profit>=100.0;
   }
};

#endif
