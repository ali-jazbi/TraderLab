#ifndef TRADERLAB_FIRST_TOUCH_POLICY_MQH
#define TRADERLAB_FIRST_TOUCH_POLICY_MQH
// Authorized historical comparison only; this cannot enable Demo submission.
int TL_TESTER_FVG_POLICY=0; // 0 STRICT_ORIGINAL, 1 EXPERIMENTAL_FIRST_TOUCH
int TL_TESTER_SECOND_EXTREME=0; // 0 strict, 1 same-group second while non-FULL
int TL_TESTER_POLICY_MASK=0; // Independent study bits: crossing=1, non-FULL=2, per-BOS=4.
int TL_TESTER_DISCOVERY=0; // 0 unchanged; 1 FRESH_CONFIRMED; 2 IMPULSE_GLOBAL; 3 IMPULSE_ARMED.
int TL_TESTER_M1_MAX_AGE_MINUTES=0; // 0 unchanged; 60/120 are separate TESTER-only studies, not owner cutoffs.
bool TLStudyBosAgeAllowed(const bool tester,const int frame,const datetime opened,const long observed_msc,const int minutes)
{
   if(minutes==0) return true;
   if(!tester || (minutes!=60 && minutes!=120)) return false;
   if(frame!=0) return true; // M1 only; no expiry invented for M5/M15/H1/H4.
   long age=observed_msc-(long)opened*1000;
   return opened>0 && age>=0 && age<=(long)minutes*60000;
}
bool TLTesterBosAgeAllowed(const int frame,const datetime opened,const long observed_msc)
{ return TLStudyBosAgeAllowed((bool)MQLInfoInteger(MQL_TESTER),frame,opened,observed_msc,TL_TESTER_M1_MAX_AGE_MINUTES); }
bool TLDiscoveryStudy() { return MQLInfoInteger(MQL_TESTER) && TL_TESTER_DISCOVERY>0; }
string TLDiscoveryName()
{ return !TLDiscoveryStudy()?"UNCHANGED":TL_TESTER_DISCOVERY==1?"FRESH_CONFIRMED":TL_TESTER_DISCOVERY==2?"IMPULSE_GLOBAL":"IMPULSE_ARMED"; }
datetime TL_TESTER_EXECUTION_FROM=0; // Study warm-up consumes returns but never submits them.
bool TLStudyPolicy(const int bit) { return MQLInfoInteger(MQL_TESTER) && (TL_TESTER_POLICY_MASK & bit)!=0; }
bool TLStudyCrossing(const bool buy,const double reference,const double bid,const double ask,const double slip=0)
{
   return TLStudyPolicy(1) && reference>0 && bid>0 && ask>=bid && slip>=0 &&
      (buy?bid<reference:bid>reference) && MathAbs((buy?ask:bid)-reference)+slip<=0.5+1e-8 &&
      MathAbs(bid-reference)<=0.5+1e-8;
}
bool TLStudyMemberAvailable(const bool consumed) { return !consumed || TLStudyPolicy(4); }
bool TLFirstTouchEnabled() { return MQLInfoInteger(MQL_TESTER) && TL_TESTER_FVG_POLICY==1; }
bool TLExperimentalFvgPermission(const int proof)
{ return (proof==3 && TLStudyPolicy(2)) || (TLFirstTouchEnabled() && (proof==1 || (proof==2 && TL_TESTER_SECOND_EXTREME==1))); }
string TLFvgPermissionName(const int proof)
{ return proof==3?"EXPERIMENTAL_NON_FULL_FVG":proof==1?"EXPERIMENTAL_FIRST_TOUCH":proof==2?"EXPERIMENTAL_SAME_GROUP_SECOND":"UNFILLED"; }
#endif
