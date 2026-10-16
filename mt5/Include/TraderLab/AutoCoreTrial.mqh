#ifndef TRADERLAB_AUTO_CORE_TRIAL_MQH
#define TRADERLAB_AUTO_CORE_TRIAL_MQH
// Operational trial restrictions, never selection/SL/TP strategy rules.
bool TLAutoCoreTrialDayAllowed(const string reserved,const string requested)
{ return requested!="" && (reserved=="" || reserved==requested); }
bool TLAutoCoreTrialLotsAllowed(const double current,const double reserve)
{ return MathIsValidNumber(current) && MathIsValidNumber(reserve) && current>=0 && reserve>0 && current+reserve<=0.04+1e-8; }
string TLAutoCoreTrialRiskBlock(const string symbol,const ulong magic,const bool buy,const double price,
                              const double stop,const double reserve,const double risk_cap,const double cost_reserve)
{
   if(AccountInfoString(ACCOUNT_CURRENCY)!="USD") return "AUTO_TRIAL_USD_ACCOUNT_REQUIRED";
   if(!MathIsValidNumber(risk_cap) || !MathIsValidNumber(cost_reserve) || risk_cap<=0 || cost_reserve<0)
      return "AUTO_TRIAL_EXPLICIT_RISK_AND_COST_BUDGET_REQUIRED";
   if(OrdersTotal()!=0) return "AUTO_TRIAL_PENDING_ORDER_OR_OTHER_ROBOT";
   double lots=0,risk=0;
   for(int i=0;i<PositionsTotal();i++)
   {
      if(PositionGetTicket(i)==0) return "AUTO_TRIAL_POSITION_SNAPSHOT_FAILED";
      if(PositionGetString(POSITION_SYMBOL)!=symbol || (ulong)PositionGetInteger(POSITION_MAGIC)!=magic)
         return "AUTO_TRIAL_MANUAL_OR_OTHER_ROBOT_POSITION";
      double volume=PositionGetDouble(POSITION_VOLUME),sl=PositionGetDouble(POSITION_SL),loss;
      if(sl<=0 || !OrderCalcProfit(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?ORDER_TYPE_BUY:ORDER_TYPE_SELL,
            symbol,volume,PositionGetDouble(POSITION_PRICE_OPEN),sl,loss)) return "AUTO_TRIAL_OPEN_RISK_UNAVAILABLE";
      lots+=volume; risk+=MathMax(0,-loss);
   }
   if(!TLAutoCoreTrialLotsAllowed(lots,reserve)) return "AUTO_TRIAL_TOTAL_CORE_VOLUME_EXCEEDS_004";
   double new_profit;
   if(stop<=0 || price<=0 || !OrderCalcProfit(buy?ORDER_TYPE_BUY:ORDER_TYPE_SELL,symbol,reserve,price,stop,new_profit))
      return "AUTO_TRIAL_NEW_RISK_UNAVAILABLE";
   risk+=MathMax(0,-new_profit)+cost_reserve;
   if(risk>risk_cap+1e-8) return "AUTO_TRIAL_OPEN_RISK_CAP_EXCEEDED";
   // Stop risk is an estimate, not a promise about gaps/slippage or future fees.
   return "";
}
#endif
