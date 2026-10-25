#property strict
// Isolated Tester-only DATA audit. Never a strategy/performance backtest.
long counts[13];datetime first[13],last[13],bounds[14];int bucket=0;
int OnInit()
{
 if(!MQLInfoInteger(MQL_TESTER))return INIT_FAILED;
 ArrayInitialize(counts,0);ArrayInitialize(first,0);ArrayInitialize(last,0);
 for(int k=0;k<14;k++){int yr=2025+(9+k)/12,mo=(9+k)%12+1;bounds[k]=StringToTime(StringFormat("%04d.%02d.01",yr,mo));}
 ENUM_TIMEFRAMES frames[]={PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_H1,PERIOD_H4};
 for(int i=0;i<5;i++){MqlRates bars[];ResetLastError();int n=CopyRates(_Symbol,frames[i],0,25,bars);Print("DATA_AUDIT_TIMEFRAME ",EnumToString(frames[i])," bars=",n," error=",GetLastError());}
 Print("DATA_AUDIT_ONLY no trading strategy, no orders, no calendar assumptions, no profitability claim");return INIT_SUCCEEDED;
}
void OnTick()
{
 datetime t=TimeCurrent();while(bucket<12 && t>=bounds[bucket+1])bucket++;
 if(t<bounds[0] || t>=bounds[13])return;
 if(counts[bucket]==0)first[bucket]=t;last[bucket]=t;counts[bucket]++;
}
double OnTester()
{
 for(int k=0;k<13;k++)Print("DATA_AUDIT_MONTH {\"month\":\"",TimeToString(bounds[k],TIME_DATE),"\",\"callbacks\":",counts[k],",\"first_server\":\"",TimeToString(first[k],TIME_DATE|TIME_SECONDS),"\",\"last_server\":\"",TimeToString(last[k],TIME_DATE|TIME_SECONDS),"\"}");
 Print("DATA_AUDIT_COMPLETE strategy_orders=0; callbacks may include generated fallback: consult Agent warnings");return 0;
}
