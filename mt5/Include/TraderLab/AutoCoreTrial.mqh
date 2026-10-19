#ifndef TRADERLAB_AUTO_CORE_TRIAL_MQH
#define TRADERLAB_AUTO_CORE_TRIAL_MQH
#include "RecoveryJournal.mqh"
string TL_AUTO_CORE_NAMESPACE="";
string TL_AUTO_CORE_SCOPE="";
ulong TL_AUTO_CORE_MAGIC=0;
string TLAutoCoreJournalPath(const string kind)
{ return "AUTO_CORE_DEMO-"+kind+"-"+TL_AUTO_CORE_NAMESPACE+".dat"; }
string TLAutoCoreLegacyJournalPath(const string kind,const ulong magic)
{
   string safe=AccountInfoString(ACCOUNT_SERVER);
   for(int c=0;c<StringLen(safe);c++) { ushort v=StringGetCharacter(safe,c);
      if(!((v>=48&&v<=57)||(v>=65&&v<=90)||(v>=97&&v<=122))) StringSetCharacter(safe,c,'_'); }
   return "AUTO_CORE_DEMO-"+kind+"-"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+"-"+safe+"-"+(string)magic+".csv";
}
int TLAutoCoreRecoverySet()
{
   string kinds[]={"consumed","plans","gateway","plans-wal","intents-wal","inputs"}; int found=0;
   int common=MQLInfoInteger(MQL_TESTER)?0:FILE_COMMON;
   for(int i=0;i<ArraySize(kinds);i++) if(FileIsExist(TLAutoCoreJournalPath(kinds[i]),common))
   {
      int f=FileOpen(TLAutoCoreJournalPath(kinds[i]),FILE_READ|FILE_BIN|common);
      if(f==INVALID_HANDLE) return -1;
      bool empty=FileSize(f)==0; FileClose(f);
      if(empty) return -1;
      found++;
   }
   // An old candidate ledger has no input WAL/as-of membership. Never reset or
   // silently migrate it into a new empty trial budget, even when currently flat.
   if(TL_AUTO_CORE_SCOPE=="" || TL_AUTO_CORE_MAGIC==0) return -1;
   if(FileIsExist(TLAutoCoreLegacyJournalPath("plans",TL_AUTO_CORE_MAGIC),common) ||
      FileIsExist(TLAutoCoreLegacyJournalPath("gateway",TL_AUTO_CORE_MAGIC),common)) return -1;
   return found==0?0:found==ArraySize(kinds)?1:-1;
}
void TLAutoCoreNamespace(const string symbol,const ulong magic,const int offset,const string tester_run)
{
   string scope=(string)AccountInfoInteger(ACCOUNT_LOGIN)+":"+AccountInfoString(ACCOUNT_SERVER)+":"+symbol+":"+
      (string)magic+":"+(string)offset+":equal_level_v1:recovery_v1";
   if(MQLInfoInteger(MQL_TESTER))
      scope+=":touch"+(string)TL_TESTER_FVG_POLICY+":second"+(string)TL_TESTER_SECOND_EXTREME+":mask"+(string)TL_TESTER_POLICY_MASK+
         ":from"+(string)(long)TL_TESTER_EXECUTION_FROM+
         (TLDiscoveryStudy()?":discovery"+(string)TL_TESTER_DISCOVERY:"")+
         (TL_TESTER_M1_MAX_AGE_MINUTES>0?":m1age"+(string)TL_TESTER_M1_MAX_AGE_MINUTES:"")+":TESTER:"+tester_run;
   TL_AUTO_CORE_SCOPE=scope;
   TL_AUTO_CORE_MAGIC=magic;
   TL_AUTO_CORE_NAMESPACE=(string)AccountInfoInteger(ACCOUNT_LOGIN)+"-"+(string)magic+"-"+(string)TLRecoveryHash(scope);
}
// Operational trial restrictions, never selection/SL/TP strategy rules.
bool TLAutoCoreTrialDayAllowed(const string reserved,const string requested)
{ return requested!="" && (TLDiscoveryStudy() || reserved=="" || reserved==requested); }
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
      if(sl<=0 || !MathIsValidNumber(sl) || !MathIsValidNumber(volume) || volume<=0 ||
         !OrderCalcProfit(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?ORDER_TYPE_BUY:ORDER_TYPE_SELL,
            symbol,volume,PositionGetDouble(POSITION_PRICE_OPEN),sl,loss) || !MathIsValidNumber(loss)) return "AUTO_TRIAL_OPEN_RISK_UNAVAILABLE";
      lots+=volume; risk+=MathMax(0,-loss);
   }
   if(!TLAutoCoreTrialLotsAllowed(lots,reserve)) return "AUTO_TRIAL_TOTAL_CORE_VOLUME_EXCEEDS_004";
   double new_profit;
   if(stop<=0 || price<=0 || !MathIsValidNumber(stop) || !MathIsValidNumber(price) ||
      !OrderCalcProfit(buy?ORDER_TYPE_BUY:ORDER_TYPE_SELL,symbol,reserve,price,stop,new_profit) || !MathIsValidNumber(new_profit))
      return "AUTO_TRIAL_NEW_RISK_UNAVAILABLE";
   risk+=MathMax(0,-new_profit)+cost_reserve;
   if(risk>risk_cap+1e-8) return "AUTO_TRIAL_OPEN_RISK_CAP_EXCEEDED";
   // Stop risk is an estimate, not a promise about gaps/slippage or future fees.
   return "";
}
#endif
