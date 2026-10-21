#ifndef TRADERLAB_CORE_ELIGIBILITY_MQH
#define TRADERLAB_CORE_ELIGIBILITY_MQH
// Owner §55. Permission is independent of detection, grouping and first returns.
struct TLEligibilityBos
{
   string id;
   datetime opened;
   long qualified_msc;
   int side;
   double level;
};
struct TLCoreEligibility
{
   bool eligible;
   double body_pips;
   string witnesses,reasons,reason;
};
void TLEligibilityReason(TLCoreEligibility &r,const string reason)
{
   if(r.reason=="") r.reason=reason;
   r.reasons+=(r.reasons==""?"":",")+"\""+reason+"\"";
}
TLCoreEligibility TLCheckCoreEligibility(const TLDetectedGap &gap,const TLEligibilityBos &bos[],const long cutoff)
{
   TLCoreEligibility r; ZeroMemory(r); r.reason=""; r.reasons=""; r.witnesses="";
   // OHLC is recorded to eight decimals. Remove binary subtraction noise
   // at exponent boundaries; 7.99999999 still fails, exactly 8.00000000 passes.
   double body_price=NormalizeDouble(MathAbs(gap.c2_close-gap.c2_open),8);
   r.body_pips=body_price/TL_PIP;
   if(gap.c2_open<=0 || gap.c2_close<=0) TLEligibilityReason(r,"C2_OHLC_UNAVAILABLE");
   else if(body_price<80*TL_PIP) TLEligibilityReason(r,"C2_BODY_BELOW_80_PIPS");
   int prior=0;
   for(int i=0;i<ArraySize(bos);i++)
   {
      TLEligibilityBos b=bos[i];
      if(b.side!=gap.side || b.opened>=gap.candidate || b.opened<=0 || b.qualified_msc<=0 ||
         b.qualified_msc>cutoff) continue;
      prior++;
      if(b.level>=gap.low && b.level<=gap.high) r.witnesses+=(r.witnesses==""?"":";")+b.id;
   }
   if(prior==0) TLEligibilityReason(r,"NO_VALID_PREFVG_BOS");
   else if(r.witnesses=="") TLEligibilityReason(r,"BOS_OUTSIDE_FVG");
   r.eligible=r.reason=="";
   return r;
}
#endif
