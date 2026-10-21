#property strict
#include "Include/TraderLab/Detection.mqh"
#include "Include/TraderLab/CoreEligibility.mqh"
// Synthetic arithmetic checks only. No gateway, account login or OrderSend.
int failures=0,checks=0;
string results="";
void Case(const string name,const TLDetectedGap &g,const TLEligibilityBos &bos[],const bool expected,const string reason="")
{
   TLCoreEligibility r=TLCheckCoreEligibility(g,bos,g.available_msc);
   checks++;
   if(r.eligible!=expected || (reason!="" && StringFind(r.reasons,reason)<0)) { failures++; Print("FAIL ",name); }
   results+=(results==""?"":",")+"{\"case\":\""+name+"\",\"eligible\":"+(r.eligible?"true":"false")+
            ",\"body_pips\":"+DoubleToString(r.body_pips,8)+",\"reasons\":["+r.reasons+"]}";
}
void OnStart()
{
   TLDetectedGap g; ZeroMemory(g); g.candidate=D'2026.10.01 12:00';g.available_msc=(long)(g.candidate+11*60)*1000;
   g.side=1;g.low=4146;g.high=4150;g.c2_open=4146;g.c2_close=4154;g.c2_high=4160;g.c2_low=4130;
   TLEligibilityBos b[];ArrayResize(b,1);b[0].id="B";b[0].opened=g.candidate-180;
   b[0].qualified_msc=(long)g.candidate*1000;b[0].side=1;b[0].level=4148;
   g.c2_close=4153.99;Case("79.9",g,b,false,"C2_BODY_BELOW_80_PIPS");
   g.c2_close=4154;Case("80",g,b,true);
   g.c2_close=4156;Case("100",g,b,true);
   g.c2_close=4154;TLEligibilityBos empty[];Case("no_bos",g,empty,false,"NO_VALID_PREFVG_BOS");
   Case("prior_inside",g,b,true);
   b[0].opened=g.candidate+1;Case("after_c2",g,b,false,"NO_VALID_PREFVG_BOS");
   b[0].opened=g.candidate;Case("same_c2",g,b,false,"NO_VALID_PREFVG_BOS");
   b[0].opened=g.candidate-180;g.c2_close=4147;Case("small_body_large_wicks",g,b,false,"C2_BODY_BELOW_80_PIPS");
   g.c2_close=4154;b[0].level=4150.01;Case("outside",g,b,false,"BOS_OUTSIDE_FVG");
   b[0].level=4146;Case("lower_edge",g,b,true);b[0].level=4150;Case("upper_edge",g,b,true);
   b[0].qualified_msc=0;Case("unqualified",g,b,false,"NO_VALID_PREFVG_BOS");
   b[0].qualified_msc=g.available_msc+1;Case("future_qualification",g,b,false,"NO_VALID_PREFVG_BOS");
   b[0].qualified_msc=(long)g.candidate*1000+1;Case("qualification_after_c2",g,b,true);
   g.side=-1;b[0].side=-1;g.c2_close=4138;b[0].opened=g.candidate-300*86400;Case("sell_no_lookback",g,b,true);
   g.c2_open=4146.13;g.c2_close=4138.13;Case("decimal_exact_80",g,b,true);
   for(int i=0;i<100;i++)
   {
      g.side=1;b[0].side=1;g.c2_open=4092.0+i/100.0;g.c2_close=4100.0+i/100.0;
      Case("binary_buy_"+(string)i,g,b,true);
      g.side=-1;b[0].side=-1;g.c2_open=4100.0+i/100.0;g.c2_close=4092.0+i/100.0;
      Case("binary_sell_"+(string)i,g,b,true);
   }
   g.side=1;b[0].side=1;g.c2_open=4092.03;g.c2_close=4100.02999999;
   Case("one_decimal_unit_below_80",g,b,false,"C2_BODY_BELOW_80_PIPS");
   g.c2_close=4100.03000001;Case("one_decimal_unit_above_80",g,b,true);
   g.c2_open=0;Case("missing_c2",g,b,false,"C2_OHLC_UNAVAILABLE");
   int f=FileOpen("CoreEligibilityChecks-result.json",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(f!=INVALID_HANDLE) { FileWriteString(f,"{\"checks\":"+(string)checks+",\"failures\":"+(string)failures+",\"cases\":["+results+"]}");FileClose(f); }
   Print("Core eligibility checks=",checks," failures=",failures);
}
