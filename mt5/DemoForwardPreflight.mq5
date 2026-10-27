#property strict
#property version "1.000"
// Read-only account/calendar/capability probe. No trade API invocation.
#include "Include/TraderLab/EventLog.mqh"
#include "Include/TraderLab/FirstTouchPolicy.mqh"
#include "Include/TraderLab/ForwardCalendar.mqh"
void OnStart()
{
   ulong deadline=GetTickCount64()+30000;
   while(!TerminalInfoInteger(TERMINAL_CONNECTED) && GetTickCount64()<deadline) Sleep(100);
   SymbolSelect("XAUUSD_o",true); int offset=0; bool clock=TLForwardClock(offset);
   bool identity=TLDemoForwardIdentity() && TerminalInfoInteger(TERMINAL_CONNECTED);
   TL_FORWARD_DEMO=identity; TLForwardCalendarRefresh();
   ENUM_TIMEFRAMES frames[]={PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_H1,PERIOD_H4}; bool bars_ok=true;
   // A fresh dedicated terminal can legitimately fetch its first history asynchronously.
   do
   {
      bars_ok=true;
      for(int i=0;i<5;i++) { MqlRates bars[]; if(CopyRates("XAUUSD_o",frames[i],1,21,bars)!=21) bars_ok=false; }
      if(!bars_ok) Sleep(100);
   } while(!bars_ok && GetTickCount64()<deadline);
   int f=FileOpen("TraderLab-forward-preflight.json",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(f!=INVALID_HANDLE)
   {
      FileWriteString(f,"{\"utc\":"+(string)(long)TimeGMT()+",\"demo_verified\":"+(identity?"true":"false")+
         ",\"login\":"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+",\"server\":"+TLQuote(AccountInfoString(ACCOUNT_SERVER))+
         ",\"clock_verified\":"+(clock?"true":"false")+",\"server_offset\":"+(string)offset+
         ",\"currency\":"+TLQuote(AccountInfoString(ACCOUNT_CURRENCY))+",\"hedging\":"+(AccountInfoInteger(ACCOUNT_MARGIN_MODE)==ACCOUNT_MARGIN_MODE_RETAIL_HEDGING?"true":"false")+
         ",\"equity\":"+DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY),2)+",\"balance\":"+DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE),2)+
         ",\"positions\":"+(string)PositionsTotal()+",\"orders\":"+(string)OrdersTotal()+",\"five_frames_history\":"+(bars_ok?"true":"false")+
         ",\"trade_allowed\":"+(AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)?"true":"false")+
         ",\"expert_allowed\":"+(AccountInfoInteger(ACCOUNT_TRADE_EXPERT)?"true":"false")+
         ",\"connected\":"+(TerminalInfoInteger(TERMINAL_CONNECTED)?"true":"false")+
         ",\"terminal_path\":"+TLQuote(TerminalInfoString(TERMINAL_PATH))+
         ",\"tick_size\":"+DoubleToString(SymbolInfoDouble("XAUUSD_o",SYMBOL_TRADE_TICK_SIZE),8)+
         ",\"volume_min\":"+DoubleToString(SymbolInfoDouble("XAUUSD_o",SYMBOL_VOLUME_MIN),8)+
         ",\"volume_step\":"+DoubleToString(SymbolInfoDouble("XAUUSD_o",SYMBOL_VOLUME_STEP),8)+
         ",\"contract_size\":"+DoubleToString(SymbolInfoDouble("XAUUSD_o",SYMBOL_TRADE_CONTRACT_SIZE),2)+
         ",\"algo\":"+(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)?"true":"false")+"}"); FileClose(f);
   }
   if(StringFind(TerminalInfoString(TERMINAL_PATH),"TraderLabDemoForward")>=0) TerminalClose(0);
}
