#ifndef TRADERLAB_RULES_MQH
#define TRADERLAB_RULES_MQH

// Canonical §§1,15,17–24,36. Unknown branches return a TODO, never a trading default.
const double TL_PIP = 0.1;
const double TL_LEG_LOTS = 0.01;

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
      if(single_sl_pips<=0) { todo="TODO_STRATEGY_UNRESOLVED:single_core_sl_pips"; return false; }
      plan.stop=plan.entry1-side*single_sl_pips*TL_PIP;
   }
   else plan.stop=(side==1)?lowest-30*TL_PIP:highest+30*TL_PIP;
   plan.tp1=plan.reference+side*60*TL_PIP;
   plan.tp2=plan.reference+side*100*TL_PIP;
   return true;
}

double TLBreakEven(const int side, const double entry) { return entry+side*5*TL_PIP; }
bool TLOBroken(const int original_side,const double low,const double high,const double observed)
{
   return (original_side==1)?observed<=low-10*TL_PIP:observed>=high+10*TL_PIP;
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
