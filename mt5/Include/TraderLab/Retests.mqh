#ifndef TRADERLAB_RETESTS_MQH
#define TRADERLAB_RETESTS_MQH
#include "Rules.mqh"
#include "EventLog.mqh"
#include "FirstTouchPolicy.mqh"

// Current reading of prior owner examples, NOT a new direct confirmation.
enum TLBosState { TL_CANDIDATE, TL_QUALIFIED, TL_BROKEN, TL_OUTBOUND, TL_CONSUMED, TL_BLOCKED };

string TLBosIdentity(const string tf,const int side,const datetime opened,const int offset)
{
   string at="server_epoch:"+(string)(long)opened;
   if(offset!=INT_MAX)
   {
      at=TimeToString(opened-offset,TIME_DATE|TIME_SECONDS);
      StringReplace(at,".","-"); StringReplace(at," ","T"); at+="+00:00";
   }
   return tf+":"+(side==1?"BUY":"SELL")+":"+at;
}

string TLMscIso(const long msc,const int offset)
{
   return msc==0?"null":TLIso((datetime)(msc/1000),offset,(int)(msc%1000));
}

struct TLFirstReturn
{
   bool have_previous,consumed,exact;
   double previous,previous_return,observed;
   long outbound_msc,return_msc,return_index;
   int return_ordinal;
};

bool TLAdvanceReturn(TLFirstReturn &r,const int side,const double reference,const double price,
                     const MqlTick &tick,const long index,const int ordinal)
{
   if(r.consumed) return false;
   if(side*(price-reference)>0 && r.outbound_msc==0) r.outbound_msc=tick.time_msc;
   if(r.have_previous && r.outbound_msc>0 && TLDirectionalReturn(side,reference,r.previous,price))
   {
      r.consumed=true; r.exact=(price==reference); r.previous_return=r.previous; r.observed=price;
      r.return_msc=tick.time_msc; r.return_index=index; r.return_ordinal=ordinal;
      return true;
   }
   r.have_previous=true; r.previous=price;
   return false;
}

struct TLBosLane
{
   TLBosState state;
   long break_msc;
   string reason;
   TLFirstReturn returns[2]; // Bid and Ask return evidence; no executable choice.
};

struct TLBosHistory
{
   datetime opened;
   double high,low;
   int side;
   long qualified_msc;
   bool closed_pending;
   TLBosLane lanes[2]; // Separate Bid and Ask wick-break observations.
};

class TLBosTracker
{
private:
   TLBosHistory history[];
   int active[];
   int changed[];
   string timeframe;
   int offset;
   double price_step;
   datetime last_open;
   long break_events,return_events,tick_visits,inspections;
   string Details(const TLBosHistory &h)
   {
      return "\"bos_id\":"+TLQuote(TLBosIdentity(timeframe,h.side,h.opened,offset))+
             ",\"timeframe\":"+TLQuote(timeframe)+",\"side\":"+TLQuote(h.side==1?"BUY":"SELL")+
             ",\"candidate_at\":"+TLIso(h.opened,offset)+
             ",\"candidate_server_epoch\":"+(string)(long)h.opened+
             ",\"diagnostic_only\":true,\"tradable_setup\":false";
   }
public:
   TLBosTracker() { offset=INT_MAX; price_step=0; last_open=0; break_events=0; return_events=0; tick_visits=0; inspections=0; }
   void Configure(const string tf,const int server_offset,const double step=0)
   { timeframe=tf; offset=server_offset; price_step=step; }
   long Breaks() { return break_events; }
   long Returns() { return return_events; }
   long Visits() { return tick_visits; }
   long Inspections() { return inspections; }
   int Count() { return ArraySize(history); }
   int ActiveCount() { return ArraySize(active); }
   int ChangedCount() { return ArraySize(changed); }
   bool Changed(const int i,int &id,TLBosHistory &value)
   { if(i<0 || i>=ArraySize(changed)) return false; id=changed[i]; value=history[id]; return true; }
   bool Read(const datetime opened,const int side,TLBosHistory &value)
   {
      for(int i=ArraySize(history)-1;i>=0;i--)
         if(history[i].opened==opened && history[i].side==side) { value=history[i]; return true; }
      return false;
   }
   void ProcessBar(const MqlRates &bar,const long available_msc)
   {
      if(bar.time<=last_open) return; // Duplicate closed bars cannot rearm history.
      ArrayResize(changed,0);
      last_open=bar.time;
      for(int i=0;i<ArraySize(history);i++)
      {
         if(!history[i].closed_pending) continue;
         bool crossed=history[i].side==1?bar.high>history[i].high:bar.low<history[i].low;
         bool qualifies=history[i].side==1?bar.close<history[i].low:bar.close>history[i].high;
         if(!crossed && qualifies && history[i].qualified_msc==0)
         {
            history[i].qualified_msc=available_msc;
            int c=ArraySize(changed); ArrayResize(changed,c+1); changed[c]=i;
            for(int q=0;q<2;q++)
               if(history[i].lanes[q].state==TL_CANDIDATE) history[i].lanes[q].state=TL_QUALIFIED;
         }
         if(crossed)
         {
            if(history[i].qualified_msc>0) { int c=ArraySize(changed); ArrayResize(changed,c+1); changed[c]=i; }
            history[i].closed_pending=false;
            for(int q=0;q<2;q++)
               if(history[i].lanes[q].state==TL_CANDIDATE || history[i].lanes[q].state==TL_QUALIFIED)
               {
                  history[i].lanes[q].state=TL_BLOCKED;
                  history[i].lanes[q].reason="intrabar_break_unobserved";
               }
         }
      }
      int n=ArraySize(history),a=ArraySize(active);
      ArrayResize(history,n+2,256); ArrayResize(active,a+2,256);
      for(int s=0;s<2;s++)
      {
         ZeroMemory(history[n+s]); history[n+s].opened=bar.time;
         history[n+s].side=s==0?1:-1; history[n+s].high=bar.high; history[n+s].low=bar.low;
         bool wick=TLHasBosWick(bar,history[n+s].side,price_step);
         history[n+s].closed_pending=wick;
         if(wick) active[a++]=n+s;
         else for(int q=0;q<2;q++)
         { history[n+s].lanes[q].state=TL_BLOCKED; history[n+s].lanes[q].reason="directional_wick_missing"; }
      }
      ArrayResize(active,a,256);
   }
   void ProcessTick(const MqlTick &tick,const long index,const int ordinal,TLEventLog &log)
   {
      tick_visits++;
      ArrayResize(changed,0);
      double prices[2]; prices[0]=tick.bid; prices[1]=tick.ask;
      string quotes[2]={"bid","ask"}; int retained=0;
      for(int i=0;i<ArraySize(active);i++)
      {
         int id=active[i]; inspections++;
         TLBosHistory h=history[id]; double level=h.side==1?h.high:h.low;
         bool updated=false;
         double reference=TLCoreEntryReference(h.side,level);
         for(int q=0;q<2;q++)
         {
            if(h.lanes[q].state==TL_BLOCKED || h.lanes[q].state==TL_CONSUMED) continue;
            if(h.lanes[q].break_msc==0)
            {
               if(h.side*(prices[q]-level)<=0) continue;
               if(h.qualified_msc==0)
               {
                  h.lanes[q].state=TL_BLOCKED; h.lanes[q].reason="tick_break_before_qualification";
                  continue;
               }
               h.lanes[q].state=TL_BROKEN; h.lanes[q].break_msc=tick.time_msc; break_events++;
               updated=true;
               log.Write("BOS_INTRABAR_BREAK","BOS-01/BOS-02",Details(h)+
                         ",\"break_quote\":"+TLQuote(quotes[q])+",\"break_at\":"+TLMscIso(tick.time_msc,offset)+
                         ",\"qualified_at\":"+TLMscIso(h.qualified_msc,offset)+
                         ",\"level\":"+TLQuote(DoubleToString(level,8))+
                         ",\"observed_quote\":"+TLQuote(DoubleToString(prices[q],8))+
                         ",\"tick_index\":"+(string)index+",\"millisecond_ordinal\":"+(string)ordinal,
                         tick.time,(int)(tick.time_msc%1000));
            }
            for(int r=0;r<2;r++)
            {
               bool returned=TLAdvanceReturn(h.lanes[q].returns[r],h.side,reference,prices[r],tick,index,ordinal);
               TLFirstReturn evidence=h.lanes[q].returns[r];
               if(evidence.outbound_msc>0) h.lanes[q].state=TL_OUTBOUND;
               if(!returned) continue;
               updated=true;
               return_events++;
               log.Write("BOS_FIRST_DIRECTIONAL_RETURN","TOUCH-01",Details(h)+
                         ",\"break_quote\":"+TLQuote(quotes[q])+",\"retest_quote\":"+TLQuote(quotes[r])+
                         ",\"entry_reference\":"+TLQuote(DoubleToString(reference,8))+
                         ",\"break_at\":"+TLMscIso(h.lanes[q].break_msc,offset)+
                         ",\"outbound_at\":"+TLMscIso(evidence.outbound_msc,offset)+
                         ",\"first_return_at\":"+TLMscIso(evidence.return_msc,offset)+
                         ",\"tick_index\":"+(string)index+",\"millisecond_ordinal\":"+(string)ordinal+
                         ",\"previous_quote\":"+TLQuote(DoubleToString(evidence.previous_return,8))+
                         ",\"observed_quote\":"+TLQuote(DoubleToString(evidence.observed,8))+
                         ",\"exact_quote\":"+(evidence.exact?"true":"false")+
                         ",\"consumed\":true,\"reason\":\"TODO_STRATEGY_UNRESOLVED:association_and_activation\"",
                         tick.time,(int)(tick.time_msc%1000));
            }
            if(h.lanes[q].returns[0].consumed && h.lanes[q].returns[1].consumed) h.lanes[q].state=TL_CONSUMED;
         }
         history[id]=h;
         if(updated) { int c=ArraySize(changed); ArrayResize(changed,c+1); changed[c]=id; }
         bool terminal=true;
         for(int q=0;q<2;q++) if(h.lanes[q].state!=TL_BLOCKED && h.lanes[q].state!=TL_CONSUMED) terminal=false;
         if(!terminal) active[retained++]=id;
      }
      ArrayResize(active,retained,256); // Archive retained, no expiry or history reset.
   }
};
#endif
