#ifndef TRADERLAB_FIRST_TOUCH_POLICY_MQH
#define TRADERLAB_FIRST_TOUCH_POLICY_MQH
// Authorized historical comparison only; this cannot enable Demo submission.
int TL_TESTER_FVG_POLICY=0; // 0 STRICT_ORIGINAL, 1 EXPERIMENTAL_FIRST_TOUCH
int TL_TESTER_SECOND_EXTREME=0; // 0 strict, 1 same-group second while non-FULL
bool TLFirstTouchEnabled() { return MQLInfoInteger(MQL_TESTER) && TL_TESTER_FVG_POLICY==1; }
bool TLExperimentalFvgPermission(const int proof)
{ return TLFirstTouchEnabled() && (proof==1 || (proof==2 && TL_TESTER_SECOND_EXTREME==1)); }
string TLFvgPermissionName(const int proof)
{ return proof==1?"EXPERIMENTAL_FIRST_TOUCH":proof==2?"EXPERIMENTAL_SAME_GROUP_SECOND":"UNFILLED"; }
#endif
