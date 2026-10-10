#property strict
#property version "0.10"
#property description "Canonical XAUUSD detection/logging. No broker orders."

#include "Include/TraderLab/Detection.mqh"
#include "Include/TraderLab/TickCapture.mqh"
#include "Include/TraderLab/TesterStress.mqh"

input string InpBrokerSymbol="XAUUSD";
input string InpLogFile="TraderLab-run01.jsonl";
input int InpServerUtcOffsetSeconds=INT_MAX; // TODO: explicit offset for this capture; no broker timezone guess.
input bool InpTesterStress=false; // Ignored outside MQL_TESTER.
input int InpTesterStressSkipCallbacks=8; // Skip N, drain one; first callback always drains.
input int InpTehranUtcOffsetSeconds=INT_MAX; // TODO: explicit strategy-time offset for this capture.

TLEventLog event_log;
TLBarDetector detectors[5];
ENUM_TIMEFRAMES frames[5]={PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_H1,PERIOD_H4};
string frame_names[5]={"M1","M5","M15","H1","H4"};
TLTickCapture tick_capture;
long last_detection_msc=0;
bool tester_start_pending=false;
TLTesterStress tester_stress;

bool TLSupportsVolume(const double volume,const double minimum,const double maximum,const double step)
{
   if(minimum<=0 || maximum<minimum || step<=0 || volume<minimum-1e-8 || volume>maximum+1e-8) return false;
   double increments=(volume-minimum)/step;
   return MathAbs(increments-MathRound(increments))<1e-8;
}

double TLExistingDirectionalVolume(const string symbol,const bool buy)
{
   double total=0;
   for(int i=0;i<PositionsTotal();i++)
   {
      if(PositionGetTicket(i)==0 || PositionGetString(POSITION_SYMBOL)!=symbol) continue;
      bool position_buy=(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY);
      if(position_buy==buy) total+=PositionGetDouble(POSITION_VOLUME);
   }
   for(int i=0;i<OrdersTotal();i++)
   {
      if(OrderGetTicket(i)==0 || OrderGetString(ORDER_SYMBOL)!=symbol) continue;
      long type=OrderGetInteger(ORDER_TYPE);
      bool buy_order=(type==ORDER_TYPE_BUY_LIMIT || type==ORDER_TYPE_BUY_STOP || type==ORDER_TYPE_BUY_STOP_LIMIT);
      bool sell_order=(type==ORDER_TYPE_SELL_LIMIT || type==ORDER_TYPE_SELL_STOP || type==ORDER_TYPE_SELL_STOP_LIMIT);
      if((buy && buy_order) || (!buy && sell_order)) total+=OrderGetDouble(ORDER_VOLUME_CURRENT);
   }
   return total;
}

void LogBrokerCapabilities()
{
   int digits=(int)SymbolInfoInteger(InpBrokerSymbol,SYMBOL_DIGITS);
   double point=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_POINT);
   double tick_size=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_TRADE_TICK_SIZE);
   double tick_profit=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_TRADE_TICK_VALUE_PROFIT);
   double tick_loss=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_TRADE_TICK_VALUE_LOSS);
   double contract=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_TRADE_CONTRACT_SIZE);
   double volume_min=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_VOLUME_MIN);
   double volume_max=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_VOLUME_MAX);
   double volume_step=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_VOLUME_STEP);
   double volume_limit=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_VOLUME_LIMIT);
   long stops=SymbolInfoInteger(InpBrokerSymbol,SYMBOL_TRADE_STOPS_LEVEL);
   long freeze=SymbolInfoInteger(InpBrokerSymbol,SYMBOL_TRADE_FREEZE_LEVEL);
   long trade_mode=SymbolInfoInteger(InpBrokerSymbol,SYMBOL_TRADE_MODE);
   long order_mode=SymbolInfoInteger(InpBrokerSymbol,SYMBOL_ORDER_MODE);
   long filling_mode=SymbolInfoInteger(InpBrokerSymbol,SYMBOL_FILLING_MODE);
   long margin_mode=AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   long leverage=AccountInfoInteger(ACCOUNT_LEVERAGE);
   double swap_long=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_SWAP_LONG);
   double swap_short=SymbolInfoDouble(InpBrokerSymbol,SYMBOL_SWAP_SHORT);
   double existing_buy=TLExistingDirectionalVolume(InpBrokerSymbol,true);
   double existing_sell=TLExistingDirectionalVolume(InpBrokerSymbol,false);
   string offset=(InpServerUtcOffsetSeconds==INT_MAX)?"null":(string)InpServerUtcOffsetSeconds;
   string details="\"broker_symbol\":"+TLQuote(InpBrokerSymbol)+
      ",\"strategy_pip\":\"0.1\",\"digits\":"+(string)digits+
      ",\"point\":"+DoubleToString(point,10)+",\"tick_size\":"+DoubleToString(tick_size,10)+
      ",\"tick_value_profit\":"+DoubleToString(tick_profit,10)+
      ",\"tick_value_loss\":"+DoubleToString(tick_loss,10)+
      ",\"contract_size\":"+DoubleToString(contract,10)+
      ",\"volume_min\":"+DoubleToString(volume_min,8)+
      ",\"volume_max\":"+DoubleToString(volume_max,8)+
      ",\"volume_step\":"+DoubleToString(volume_step,8)+
      ",\"volume_limit\":"+DoubleToString(volume_limit,8)+
      ",\"stops_level\":"+(string)stops+",\"freeze_level\":"+(string)freeze+
      ",\"trade_mode\":"+(string)trade_mode+",\"order_mode\":"+(string)order_mode+
      ",\"filling_mode\":"+(string)filling_mode+
      ",\"account_currency\":"+TLQuote(AccountInfoString(ACCOUNT_CURRENCY))+
      ",\"account_margin_mode\":"+(string)margin_mode+
      ",\"account_leverage\":"+(string)leverage+
      ",\"account_trade_mode\":"+(string)AccountInfoInteger(ACCOUNT_TRADE_MODE)+
      ",\"account_trade_allowed\":"+(AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)?"true":"false")+
      ",\"account_trade_expert\":"+(AccountInfoInteger(ACCOUNT_TRADE_EXPERT)?"true":"false")+
      ",\"account_hedge_allowed\":"+(AccountInfoInteger(ACCOUNT_HEDGE_ALLOWED)?"true":"false")+
      ",\"swap_long\":"+DoubleToString(swap_long,10)+
      ",\"swap_short\":"+DoubleToString(swap_short,10)+
      ",\"existing_buy_directional_volume\":"+DoubleToString(existing_buy,8)+
      ",\"existing_sell_directional_volume\":"+DoubleToString(existing_sell,8)+
      ",\"broker_margin_news_window_minutes\":30"+
      ",\"server_utc_offset_seconds\":"+offset+
      ",\"tehran_utc_offset_seconds\":"+(InpTehranUtcOffsetSeconds==INT_MAX?"null":(string)InpTehranUtcOffsetSeconds)+
      ",\"offset_validation\":"+TLQuote(InpServerUtcOffsetSeconds==INT_MAX?
         "UNRESOLVED":"EXPLICIT_CONFIGURED_UNVERIFIED");
   event_log.Write("BROKER_CAPABILITY_SNAPSHOT","UNIT-01",details,TimeCurrent());
   if(!TLSupportsVolume(TL_LEG_LOTS,volume_min,volume_max,volume_step))
      event_log.Write("BROKER_CONFIG_BLOCKED","UNIT-01",
         "\"reason\":\"canonical_0.01_lot_unrepresentable\",\"volume_min\":"+
         DoubleToString(volume_min,8)+",\"volume_max\":"+DoubleToString(volume_max,8)+
         ",\"volume_step\":"+DoubleToString(volume_step,8)+",\"volume_limit\":"+
         DoubleToString(volume_limit,8),TimeCurrent());
   if(volume_limit>0 && existing_buy+2*TL_LEG_LOTS>volume_limit)
      event_log.Write("BROKER_CONFIG_BLOCKED","UNIT-01",
         "\"reason\":\"canonical_entry_exceeds_directional_volume_limit\",\"side\":\"BUY\",\"current_directional_volume\":"+
         DoubleToString(existing_buy,8)+",\"requested_directional_volume\":"+DoubleToString(2*TL_LEG_LOTS,8)+
         ",\"volume_limit\":"+DoubleToString(volume_limit,8),TimeCurrent());
   if(volume_limit>0 && existing_sell+2*TL_LEG_LOTS>volume_limit)
      event_log.Write("BROKER_CONFIG_BLOCKED","UNIT-01",
         "\"reason\":\"canonical_entry_exceeds_directional_volume_limit\",\"side\":\"SELL\",\"current_directional_volume\":"+
         DoubleToString(existing_sell,8)+",\"requested_directional_volume\":"+DoubleToString(2*TL_LEG_LOTS,8)+
         ",\"volume_limit\":"+DoubleToString(volume_limit,8),TimeCurrent());
}

int OnInit()
{
   if(_Symbol!=InpBrokerSymbol)
   {
      Print("Attach to the configured broker symbol chart: ",InpBrokerSymbol);
      return INIT_PARAMETERS_INCORRECT;
   }
   if(!event_log.Open(InpLogFile,InpServerUtcOffsetSeconds,InpTehranUtcOffsetSeconds)) return INIT_FAILED;
   event_log.Write("EA_INIT","UNIT-01/SCOPE-01","\"mode\":\"detection_only\",\"broker_orders_enabled\":false,"+
                   "\"broker_symbol\":"+TLQuote(InpBrokerSymbol),TimeCurrent());
   LogBrokerCapabilities();
   if(InpServerUtcOffsetSeconds==INT_MAX)
      event_log.Write("CONFIG_UNRESOLVED","TF-01","\"todo\":\"broker_server_utc_offset\",\"replayable\":false",TimeCurrent());
   else
      event_log.Write("BROKER_TIME_OFFSET","TF-01","\"configured_seconds\":"+
                      (string)InpServerUtcOffsetSeconds+",\"status\":\"EXPLICIT_CONFIGURED_UNVERIFIED\"",TimeCurrent());
   if(InpTehranUtcOffsetSeconds==INT_MAX)
      event_log.Write("CONFIG_UNRESOLVED","NY-01","\"todo\":\"tehran_utc_offset\",\"strategy_time_available\":false",TimeCurrent());
   // Tester history may not be usable before the first simulated NewTick.
   // Live Demo startup remains synchronous, with its original failure returns.
   if(MQLInfoInteger(MQL_TESTER))
   {
      if(!tester_stress.Configure(true,InpTesterStress,InpTesterStressSkipCallbacks))
      {
         event_log.Write("CONFIG_UNRESOLVED","SCOPE-01",
                         "\"todo\":\"tester_stress_skip_callbacks_must_be_positive\",\"replayable\":false",TimeCurrent());
         return INIT_PARAMETERS_INCORRECT;
      }
      event_log.Write("TESTER_STRESS_CONFIG","SCOPE-01",
                      "\"environment\":\"strategy_tester\",\"enabled\":"+(tester_stress.Enabled()?"true":"false")+
                      ",\"skip_callbacks\":"+(string)InpTesterStressSkipCallbacks+
                      ",\"policy\":\"skip_n_drain_one_after_baseline\",\"timer_policy\":\"hold_during_skips\"",TimeCurrent());
      tester_start_pending=true;
      event_log.Write("TICK_CAPTURE_START_DEFERRED","SCOPE-01/TOUCH-01",
                      "\"environment\":\"strategy_tester\",\"until\":\"first_ontick\","+
                      "\"startup_policy\":\"exclude_baseline_and_earlier_ticks\","+
                      "\"first_callback_history_is_baseline\":true",TimeCurrent());
      Print("TraderLab tester capture waiting for first OnTick; no tick history requested in OnInit.");
      return INIT_SUCCEEDED;
   }
   if(!tick_capture.Start(InpBrokerSymbol,event_log)) return INIT_FAILED;
   if(!tick_capture.StartTimer(event_log)) return INIT_FAILED;
   Print("TraderLab detection capture active. Native order execution is not implemented in this milestone.");
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(tester_start_pending)
   {
      // Clear BEFORE attempting startup: errors must never move the baseline
      // forward on a later callback and silently erase the failed interval.
      tester_start_pending=false;
      if(!tick_capture.Start(InpBrokerSymbol,event_log) || !tick_capture.StartTimer(event_log))
      {
         tick_capture.OnCallback(event_log); // Count the real callback; halted drain emits nothing.
         Print("TraderLab tester capture startup failed on first OnTick; stopping test.");
         ExpertRemove();
         return;
      }
   }
   bool skip=tester_stress.SkipCallback();
   tick_capture.OnCallback(event_log,!skip);
}

void ProcessClosedBars()
{
   MqlTick tick;
   if(!tick_capture.Active() || !tick_capture.Latest(tick) || tick.time_msc<=last_detection_msc) return;
   last_detection_msc=tick.time_msc;
   int millis=(int)(tick.time_msc%1000);
   for(int tf=0;tf<5;tf++)
   {
      MqlRates bars[];
      ArraySetAsSeries(bars,false);
      int count=CopyRates(InpBrokerSymbol,frames[tf],1,21,bars); // Only CLOSED bars; oldest first.
      if(count<1) continue;
      for(int i=0;i<count;i++)
         detectors[tf].Process(bars[i],InpBrokerSymbol,frame_names[tf],tick.time,millis,InpServerUtcOffsetSeconds,event_log);
   }
}

void OnTimer()
{
   if(tester_start_pending || tester_stress.SkipTimer()) return;
   // MT5 serializes this EA's events. Both handlers use the same cursor.
   tick_capture.Drain("timer",event_log);
   ProcessClosedBars();
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   if(tester_start_pending)
      event_log.Write("TICK_CAPTURE_ERROR","SCOPE-01/TOUCH-01",
                      "\"operation\":\"tester_startup\",\"reason\":\"tester_no_first_tick\","+
                      "\"capture_halted\":true,\"cursor_advanced\":false",TimeCurrent());
   tick_capture.Drain("deinit",event_log);
   ProcessClosedBars();
   if(MQLInfoInteger(MQL_TESTER))
      event_log.Write("TESTER_STRESS_SUMMARY","SCOPE-01",
                      "\"environment\":\"strategy_tester\",\"enabled\":"+(tester_stress.Enabled()?"true":"false")+
                      ",\"callbacks_seen\":"+(string)tester_stress.Callbacks()+
                      ",\"skipped_callbacks\":"+(string)tester_stress.Skipped()+
                      ",\"deferred_timer_calls\":"+(string)tester_stress.HeldTimers(),TimeCurrent());
   tick_capture.Summary(event_log);
   event_log.Write("EA_DEINIT","SCOPE-01","\"reason\":"+(string)reason,TimeCurrent());
   event_log.Close();
}
