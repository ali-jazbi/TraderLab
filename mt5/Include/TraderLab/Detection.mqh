#ifndef TRADERLAB_DETECTION_MQH
#define TRADERLAB_DETECTION_MQH
#include "Rules.mqh"
#include "EventLog.mqh"

struct TLBosCandidate { datetime time; double high; double low; int side; bool qualified; };

class TLBarDetector
{
private:
   MqlRates history[];
   TLBosCandidate candidates[];
public:
   datetime last_open;
   TLBarDetector() { last_open=0; }
   void Process(const MqlRates &bar,const string symbol,const string tf,const datetime captured,const int millis,
                const int server_offset,TLEventLog &log)
   {
      if(bar.time<=last_open) return;
      last_open=bar.time;
      log.Write("CLOSED_BAR","TF-01","\"kind\":\"bar\",\"symbol\":"+TLQuote(symbol)+",\"timeframe\":"+TLQuote(tf)+
                ",\"opened_at\":"+TLIso(bar.time,server_offset)+",\"open\":"+TLQuote(DoubleToString(bar.open,8))+
                ",\"high\":"+TLQuote(DoubleToString(bar.high,8))+",\"low\":"+TLQuote(DoubleToString(bar.low,8))+
                ",\"close\":"+TLQuote(DoubleToString(bar.close,8)),captured,millis);
      int retained=0;
      for(int i=0;i<ArraySize(candidates);i++)
      {
         TLBosCandidate c=candidates[i];
         bool crossed=(c.side==1)?bar.high>c.high:bar.low<c.low;
         bool qualifies=(c.side==1)?bar.close<c.low:bar.close>c.high;
         string details="\"timeframe\":"+TLQuote(tf)+",\"candidate_server_epoch\":"+(string)c.time+
                        ",\"side\":"+TLQuote(c.side==1?"BUY":"SELL")+",\"tradable_zone\":null";
         if(crossed)
         {
            log.Write("BOS_CANDIDATE_BREAK","BOS-01",details+
                      ",\"qualified_before_break\":"+(c.qualified?"true":"false")+
                      ",\"same_bar_order_ambiguous\":"+((qualifies && !c.qualified)?"true":"false"),captured,millis);
         }
         else
         {
            if(qualifies && !c.qualified)
            {
               c.qualified=true;
               log.Write("BOS_CANDIDATE_QUALIFIED","BOS-01",details,captured,millis);
            }
            candidates[retained++]=c;
         }
      }
      ArrayResize(candidates,retained+2);
      for(int j=0;j<2;j++)
      {
         candidates[retained+j].time=bar.time;
         candidates[retained+j].high=bar.high; candidates[retained+j].low=bar.low;
         candidates[retained+j].side=(j==0)?1:-1; candidates[retained+j].qualified=false;
      }
      int n=ArraySize(history);
      if(n==21) { for(int i=0;i<20;i++) history[i]=history[i+1]; n=20; }
      ArrayResize(history,n+1); history[n]=bar;
      if(ArraySize(history)!=21) return;
      double sum=0;
      for(int i=0;i<21;i++) if(i!=10) sum+=MathAbs(history[i].close-history[i].open);
      double body=MathAbs(history[10].close-history[10].open);
      if(body+1e-10<2.0*sum/20.0) return;
      string details="\"timeframe\":"+TLQuote(tf)+",\"candidate_server_epoch\":"+(string)history[10].time+
                     ",\"candidate_at\":"+TLIso(history[10].time,server_offset)+",\"body\":"+TLQuote(DoubleToString(body,8));
      log.Write("BIG_CANDLE_CONFIRMED","BIG-01",details,captured,millis);
      double low=0, high=0; int side=0;
      if(history[11].low>history[9].high) { low=history[9].high; high=history[11].low; side=1; }
      else if(history[11].high<history[9].low) { low=history[11].high; high=history[9].low; side=-1; }
      if(side==0 || high-low<20*TL_PIP-1e-8) return;
      bool full=false,partial=false;
      for(int i=12;i<21;i++)
      {
         if(side==1) { full=full || history[i].low<=low; partial=partial || history[i].low<high; }
         else { full=full || history[i].high>=high; partial=partial || history[i].high>low; }
      }
      log.Write("FVG_CONFIRMED","FVG-01",details+",\"side\":"+TLQuote(side==1?"BUY":"SELL")+
                ",\"zone\":["+TLQuote(DoubleToString(low,8))+","+TLQuote(DoubleToString(high,8))+
                "],\"fill_state\":"+TLQuote(full?"FULL":partial?"PARTIAL":"UNFILLED")+
                ",\"tradable_setup\":false,\"todo\":\"Q-OB-BOUNDS/Q-BOS-BOUNDS\"",captured,millis);
      if(tf=="H4")
      {
         int anchor=(side==1)?11:9;
         log.Write("OB_ANCHOR_OBSERVATION","OB-01","\"side\":"+TLQuote(side==1?"BUY":"SELL")+
                   ",\"anchor_candle\":"+TLQuote(side==1?"C3":"C1")+",\"anchor_at\":"+
                   TLIso(history[anchor].time,server_offset)+",\"zone\":null,\"todo\":\"Q-OB-BOUNDS\"",captured,millis);
      }
   }
};

#endif
