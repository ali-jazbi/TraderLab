#property strict
#property version "0.10"
#property description "Canonical XAUUSD detection/logging. No broker orders."

#include "Include/TraderLab/Detection.mqh"

input string InpBrokerSymbol="XAUUSD";
input string InpLogFile="TraderLab-run01.jsonl";
input int InpServerUtcOffsetSeconds=INT_MAX; // TODO: explicit offset for this capture; no broker timezone guess.

TLEventLog event_log;
TLBarDetector detectors[5];
ENUM_TIMEFRAMES frames[5]={PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_H1,PERIOD_H4};
string frame_names[5]={"M1","M5","M15","H1","H4"};
long tick_index=0;

int OnInit()
{
   if(_Symbol!=InpBrokerSymbol)
   {
      Print("Attach to the configured broker symbol chart: ",InpBrokerSymbol);
      return INIT_PARAMETERS_INCORRECT;
   }
   if(!event_log.Open(InpLogFile,InpServerUtcOffsetSeconds)) return INIT_FAILED;
   event_log.Write("EA_INIT","UNIT-01/SCOPE-01","\"mode\":\"detection_only\",\"broker_orders_enabled\":false,"+
                   "\"broker_symbol\":"+TLQuote(InpBrokerSymbol)+",\"strategy_pip\":\"0.1\",\"digits\":"+
                   (string)SymbolInfoInteger(InpBrokerSymbol,SYMBOL_DIGITS)+",\"point\":"+
                   TLQuote(DoubleToString(SymbolInfoDouble(InpBrokerSymbol,SYMBOL_POINT),8))+
                   ",\"tick_size\":"+TLQuote(DoubleToString(SymbolInfoDouble(InpBrokerSymbol,SYMBOL_TRADE_TICK_SIZE),8)),TimeCurrent());
   if(InpServerUtcOffsetSeconds==INT_MAX)
      event_log.Write("CONFIG_UNRESOLVED","TF-01","\"todo\":\"broker_server_utc_offset\",\"replayable\":false",TimeCurrent());
   Print("TraderLab detection capture active. Native order execution is not implemented in this milestone.");
   return INIT_SUCCEEDED;
}

void OnTick()
{
   MqlTick tick;
   if(!SymbolInfoTick(InpBrokerSymbol,tick)) return;
   int millis=(int)(tick.time_msc%1000);
   for(int tf=0;tf<5;tf++)
   {
      MqlRates bars[];
      ArraySetAsSeries(bars,false);
      int count=CopyRates(InpBrokerSymbol,frames[tf],1,21,bars); // Only CLOSED bars; oldest first.
      if(count<1) continue;
      for(int i=0;i<count;i++)
         detectors[tf].Process(bars[i],frame_names[tf],tick.time,millis,InpServerUtcOffsetSeconds,event_log);
   }
   tick_index++;
   event_log.Write("TICK","TOUCH-01","\"kind\":\"tick\",\"symbol\":\"XAUUSD\",\"tick_index\":"+(string)tick_index+
                   ",\"bid\":"+TLQuote(DoubleToString(tick.bid,8))+",\"ask\":"+TLQuote(DoubleToString(tick.ask,8))+
                   ",\"spread_price\":"+TLQuote(DoubleToString(tick.ask-tick.bid,8)),tick.time,millis);
}

void OnDeinit(const int reason)
{
   event_log.Write("EA_DEINIT","SCOPE-01","\"reason\":"+(string)reason,TimeCurrent());
   event_log.Close();
}
