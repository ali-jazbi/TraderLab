#property strict
#property script_show_inputs
#include "Include/TraderLab/DemoGateway.mqh"
void OnStart()
{
   int failures=0;
   if(TL_DEMO_DISPATCH_REVIEWED) failures++;
   if(!TLDemoAccount(ACCOUNT_TRADE_MODE_DEMO) || TLDemoAccount(ACCOUNT_TRADE_MODE_REAL) || TLDemoAccount(ACCOUNT_TRADE_MODE_CONTEST)) failures++;
   if(!TLDemoVolume(0.01,0.01,100,0.01) || TLDemoVolume(0.01,0.02,100,0.01)) failures++;
   if(!TLDemoGrid(4142.32,0.01) || TLDemoGrid(4142.321,0.01)) failures++;
   if(!TLDemoId("BUY1") || TLDemoId("x|x") || TLDemoId("")) failures++;
   if(!TLDemoCheckPassed(true,0) || !TLDemoCheckPassed(true,TRADE_RETCODE_DONE) ||
      TLDemoCheckPassed(false,0) || TLDemoCheckPassed(true,TRADE_RETCODE_INVALID_STOPS)) failures++;
   if(!TLDemoNewsEntryBlocked(1000,1900) || TLDemoNewsEntryBlocked(999,1900) || !TLDemoNewsEntryBlocked(2800,1900) || TLDemoNewsEntryBlocked(2801,1900)) failures++;
   if(TLDemoNewsCloseDue(1709,1900,10,true,true) || !TLDemoNewsCloseDue(1710,1900,10,true,true) ||
      !TLDemoNewsCloseDue(1800,1900,10,false,true) || !TLDemoNewsCloseDue(2801,1900,10,true,true) ||
      TLDemoNewsCloseDue(2801,1900,10,false,true) || TLDemoNewsCloseDue(1800,1900,10,true,false)) failures++;
   TLDemoGateway gateway;
   if(gateway.CanDispatch()) failures++;
   Print("TraderLab read-only runtime: mode=",AccountInfoInteger(ACCOUNT_TRADE_MODE),
         " margin_mode=",AccountInfoInteger(ACCOUNT_MARGIN_MODE)," currency=",AccountInfoString(ACCOUNT_CURRENCY),
         " symbol=",_Symbol," chart_mode=",SymbolInfoInteger(_Symbol,SYMBOL_CHART_MODE),
         " tick_size=",SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE),
         " volume_min=",SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN)," volume_step=",SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),
         " filling=",SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE)," free_margin=",AccountInfoDouble(ACCOUNT_MARGIN_FREE));
   Print("TraderLab DEMO gateway checks failures=",failures," dispatch_locked=",!TL_DEMO_DISPATCH_REVIEWED);
}
