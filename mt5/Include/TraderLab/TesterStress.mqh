#ifndef TRADERLAB_TESTER_STRESS_MQH
#define TRADERLAB_TESTER_STRESS_MQH
// Pure scheduling policy. Never creates ticks or advances the history cursor.
class TLTesterStress
{
private:
   bool enabled, holding;
   int skip_limit;
   long callbacks, skipped, held_timers;
public:
   TLTesterStress() { enabled=false; holding=false; skip_limit=0; callbacks=0; skipped=0; held_timers=0; }
   bool Configure(const bool tester,const bool requested,const int skip_callbacks)
   {
      enabled=tester && requested;
      if(enabled && skip_callbacks<1) return false;
      skip_limit=skip_callbacks;
      return true;
   }
   bool Enabled() { return enabled; }
   long Callbacks() { return callbacks; }
   long Skipped() { return skipped; }
   long HeldTimers() { return held_timers; }
   bool SkipCallback()
   {
      callbacks++;
      // First callback always establishes/drains the same baseline as normal.
      if(!enabled || callbacks==1) { holding=false; return false; }
      holding=(callbacks-2)%((long)skip_limit+1)<skip_limit;
      if(holding) skipped++;
      return holding;
   }
   bool SkipTimer()
   {
      if(!enabled || !holding) return false;
      held_timers++;
      return true;
   }
};
#endif
