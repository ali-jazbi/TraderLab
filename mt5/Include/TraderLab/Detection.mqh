#ifndef TRADERLAB_DETECTION_MQH
#define TRADERLAB_DETECTION_MQH
#include "Rules.mqh"
#include "EventLog.mqh"
#include "Retests.mqh"

struct TLBosCandidate { datetime time; double high; double low; int side; bool qualified; };
struct TLDetectedGap
{
   datetime candidate,anchor;
   long available_msc,formation_msc,impulse_end_msc;
   int side,fill; // 0 UNFILLED, 1 PARTIAL, 2 FULL
   double low,high,ob_low,ob_high;
   double c2_open,c2_high,c2_low,c2_close;
};

string TLCandidateEpoch(const datetime value)
{
   // datetime -> string formats a date; cast through long for a JSON number.
   return "\"candidate_server_epoch\":"+(string)(long)value;
}

class TLBarDetector
{
private:
   MqlRates history[];
   TLBosCandidate candidates[];
   long availability[];
   TLDetectedGap detected;
   bool new_gap,emit_bars;
   string prefix;
   string Event(const string name) { return prefix+name; }
public:
   datetime last_open;
   TLBarDetector() { last_open=0; new_gap=false; emit_bars=true; prefix=""; }
   void ConfigureCore() { prefix="CORE_"; emit_bars=false; }
   bool Gap(TLDetectedGap &value) { value=detected; return new_gap; }
   void Process(const MqlRates &bar,const string symbol,const string tf,const datetime captured,const int millis,
                const int server_offset,TLEventLog &log)
   {
      new_gap=false;
      if(bar.time<=last_open) return;
      last_open=bar.time;
      if(emit_bars) log.Write("CLOSED_BAR","TF-01","\"kind\":\"bar\",\"symbol\":"+TLQuote(symbol)+",\"timeframe\":"+TLQuote(tf)+
                ",\"opened_at\":"+TLIso(bar.time,server_offset)+",\"open\":"+TLQuote(DoubleToString(bar.open,8))+
                ",\"high\":"+TLQuote(DoubleToString(bar.high,8))+",\"low\":"+TLQuote(DoubleToString(bar.low,8))+
                ",\"close\":"+TLQuote(DoubleToString(bar.close,8)),captured,millis);
      int retained=0;
      for(int i=0;i<ArraySize(candidates);i++)
      {
         TLBosCandidate c=candidates[i];
         bool crossed=(c.side==1)?bar.high>c.high:bar.low<c.low;
         bool qualifies=(c.side==1)?bar.close<c.low:bar.close>c.high;
         string details="\"timeframe\":"+TLQuote(tf)+","+TLCandidateEpoch(c.time)+
                        ",\"bos_id\":"+TLQuote(TLBosIdentity(tf,c.side,c.time,server_offset))+
                        ",\"side\":"+TLQuote(c.side==1?"BUY":"SELL")+
                        ",\"level\":"+TLQuote(DoubleToString(c.side==1?c.high:c.low,8))+",\"tradable_zone\":null";
         if(crossed)
         {
            log.Write(Event("BOS_CANDIDATE_BREAK"),"BOS-01",details+
                      ",\"qualified_before_break\":"+(c.qualified?"true":"false")+
                      ",\"same_bar_order_ambiguous\":"+((qualifies && !c.qualified)?"true":"false"),captured,millis);
            log.Write(Event(c.qualified?"BOS_CONFIRMED":"BOS_REJECTED"),"BOS-01/BOS-02",details+
                      ",\"confirmation_source\":\"closed_bar_wick\",\"intrabar_break_at\":null"+
                      ",\"reason\":"+TLQuote(c.qualified?"qualified_before_break":qualifies?
                      "same_bar_order_ambiguous":"break_before_qualification"),captured,millis);
         }
         else
         {
            if(qualifies && !c.qualified)
            {
               c.qualified=true;
               log.Write(Event("BOS_CANDIDATE_QUALIFIED"),"BOS-01",details,captured,millis);
            }
            candidates[retained++]=c;
         }
      }
      ArrayResize(candidates,retained+2);
      double price_step=SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_SIZE);
      for(int j=0;j<2;j++)
      {
         int side=j==0?1:-1;
         if(!TLHasBosWick(bar,side,price_step))
         {
            log.Write(Event("BOS_REJECTED"),"BOS-WICK-01/OWNER-54",
               "\"timeframe\":"+TLQuote(tf)+","+TLCandidateEpoch(bar.time)+
               ",\"bos_id\":"+TLQuote(TLBosIdentity(tf,side,bar.time,server_offset))+
               ",\"side\":"+TLQuote(side==1?"BUY":"SELL")+
               ",\"level\":"+TLQuote(DoubleToString(TLBosLevel(bar,side),8))+
               ",\"reason\":\"directional_wick_missing\"",captured,millis);
            continue;
         }
         candidates[retained].time=bar.time;
         candidates[retained].high=bar.high; candidates[retained].low=bar.low;
         candidates[retained].side=side; candidates[retained].qualified=false; retained++;
      }
      ArrayResize(candidates,retained);
      int n=ArraySize(history);
      if(n==21) { for(int i=0;i<20;i++) { history[i]=history[i+1]; availability[i]=availability[i+1]; } n=20; }
      ArrayResize(history,n+1); ArrayResize(availability,n+1); history[n]=bar; availability[n]=(long)captured*1000+millis;
      if(ArraySize(history)!=21) return;
      double sum=0;
      for(int i=0;i<21;i++) if(i!=10) sum+=MathAbs(history[i].close-history[i].open);
      double body=MathAbs(history[10].close-history[10].open);
      string details="\"timeframe\":"+TLQuote(tf)+","+TLCandidateEpoch(history[10].time)+
                     ",\"candidate_at\":"+TLIso(history[10].time,server_offset)+",\"body\":"+TLQuote(DoubleToString(body,8));
      if(body+1e-10<2.0*sum/20.0)
      {
         log.Write(Event("BIG_CANDLE_REJECTED"),"BIG-01",details+",\"reason\":\"body_below_two_times_average\"",captured,millis);
         return;
      }
      log.Write(Event("BIG_CANDLE_CONFIRMED"),"BIG-01",details,captured,millis);
      double low=0, high=0; int side=0;
      if(history[11].low>history[9].high) { low=history[9].high; high=history[11].low; side=1; }
      else if(history[11].high<history[9].low) { low=history[11].high; high=history[9].low; side=-1; }
      if(side==0 || high-low<20*TL_PIP-1e-8)
      {
         log.Write(Event("FVG_REJECTED"),"FVG-01/FVG-02",details+
                   ",\"reason\":\"no_wick_gap_or_gap_below_20_pips\"",captured,millis);
         return;
      }
      bool full=false,partial=false;
      for(int i=12;i<21;i++)
      {
         if(side==1) { full=full || history[i].low<=low; partial=partial || history[i].low<high; }
         else { full=full || history[i].high>=high; partial=partial || history[i].high>low; }
      }
      log.Write(Event("FVG_CONFIRMED"),"FVG-01",details+",\"side\":"+TLQuote(side==1?"BUY":"SELL")+
                ",\"c2_ohlc\":{\"open\":"+TLQuote(DoubleToString(history[10].open,8))+
                ",\"high\":"+TLQuote(DoubleToString(history[10].high,8))+",\"low\":"+TLQuote(DoubleToString(history[10].low,8))+
                ",\"close\":"+TLQuote(DoubleToString(history[10].close,8))+"}"+
                ",\"zone\":["+TLQuote(DoubleToString(low,8))+","+TLQuote(DoubleToString(high,8))+
                "],\"fill_state\":"+TLQuote(full?"FULL":partial?"PARTIAL":"UNFILLED")+
                ",\"tradable_setup\":false,\"todo\":\"Q-ASSOCIATION\"",captured,millis);
         int anchor=(side==1)?11:9;
         double ob_low,ob_high; TLOrderBlockBounds(history[anchor],ob_low,ob_high);
         new_gap=true; detected.candidate=history[10].time; detected.anchor=history[anchor].time;
         detected.available_msc=availability[20]; detected.formation_msc=availability[11];
         detected.impulse_end_msc=(long)history[11].time*1000; // C3 open bounds actual C2 break evidence, no lookback/expiry.
         detected.side=side; detected.fill=full?2:partial?1:0; detected.low=low; detected.high=high;
         detected.c2_open=history[10].open; detected.c2_high=history[10].high;
         detected.c2_low=history[10].low; detected.c2_close=history[10].close;
         detected.ob_low=ob_low; detected.ob_high=ob_high;
         log.Write(Event("OB_CONFIRMED"),"OB-01",details+",\"side\":"+TLQuote(side==1?"BUY":"SELL")+
                   ",\"anchor_candle\":"+TLQuote(side==1?"C3":"C1")+",\"anchor_at\":"+
                   TLIso(history[anchor].time,server_offset)+",\"zone\":["+TLQuote(DoubleToString(ob_low,8))+","+
                   TLQuote(DoubleToString(ob_high,8))+"],\"tradable_setup\":false",captured,millis);
   }
};

#endif
