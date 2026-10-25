#ifndef TRADERLAB_NATIVE_RETEST_STREAM_MQH
#define TRADERLAB_NATIVE_RETEST_STREAM_MQH
#include "TickCapture.mqh"
#include "Retests.mqh"
#include "CoreController.mqh"

// A separate as-of closed-bar stream leaves timer-driven legacy diagnostics intact.
class TLNativeRetestStream : public TLTickObserver
{
private:
   TLBosTracker trackers[5];
   ENUM_TIMEFRAMES frames[5];
   string names[5],symbol;
   datetime checked_bucket[5],last_open[5];
   int offset;
   bool halted;
   long last_msc,last_index,bars_seen,rate_calls;
   ulong elapsed_us;
   TLCoreController core;
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
   TLRecoveryJournal recovery;
   bool recovery_seeded,recovery_open,recovery_set_valid;
#endif
   void Halt(const string reason,const string tf,const MqlTick &tick,TLEventLog &log)
   {
      halted=true;
      core.FailClosed(reason);
      log.Write("BOS_TRACKER_HALTED","BOS-01/TOUCH-01","\"reason\":"+TLQuote(reason)+
                ",\"timeframe\":"+TLQuote(tf)+",\"detection_halted\":true,\"tick_capture_unchanged\":true",
                tick.time,(int)(tick.time_msc%1000));
   }
public:
   TLNativeRetestStream()
   {
      frames[0]=PERIOD_M1; frames[1]=PERIOD_M5; frames[2]=PERIOD_M15; frames[3]=PERIOD_H1; frames[4]=PERIOD_H4;
      names[0]="M1"; names[1]="M5"; names[2]="M15"; names[3]="H1"; names[4]="H4";
      ArrayInitialize(checked_bucket,0); ArrayInitialize(last_open,0);
      halted=false; last_msc=0; last_index=0; bars_seen=0; rate_calls=0; elapsed_us=0;
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      recovery_seeded=false; recovery_open=false; recovery_set_valid=true;
#endif
   }
   void Configure(const string broker_symbol,const int server_offset)
   {
      symbol=broker_symbol; offset=server_offset;
      for(int i=0;i<5;i++) trackers[i].Configure(names[i],offset,SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_SIZE));
   }
   void ConfigureCore(const ulong magic,const string calendar_path,const int lead,const string packages="",const bool request_execution=false,const int tester_experiment=0,TLEventLog *audit=NULL)
   {
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      recovery_set_valid=TLAutoCoreRecoverySet()>=0; // BEFORE any missing files can be created.
#endif
      core.Configure(symbol,offset,magic,calendar_path,lead,packages,request_execution,tester_experiment,audit);
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      if(!recovery_set_valid) core.FailClosed("AUTO_CORE_INCOMPLETE_RECOVERY_SET_NO_RESET");
#endif
   }
   void CoreRefreshPackages() { core.RefreshPackages(); }
   void CoreFinishDrain(const MqlTick &before,const MqlTick &tail,const bool active,TLEventLog &log)
   { core.FinishLiveDrain(before,tail,active,log); }
   void CoreService() { core.Service(); }
   void CoreBrokerOffset(const int seconds) { core.BrokerOffset(seconds); }
   bool CoreDispatchReady() { return !halted && core.DispatchReady(); }
   string CoreStatus() { return core.Status(); }
   void CoreExecutionLimits(const int ms,const double spread,const int slippage) { core.ExecutionLimits(ms,spread,slippage); }
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
   void CoreTrialRiskLimits(const double risk_cap,const double cost_reserve) { core.TrialRiskLimits(risk_cap,cost_reserve); }
#endif
   void CorePanelEnable(const bool enabled) { core.PanelEnable(enabled); }
   void CorePanelDraw() { core.PanelDraw(); }
   void CorePanelEvent(const int event,const string name,TLEventLog &log) { core.PanelEvent(event,name,log); }
   void CorePanelClose() { core.PanelClose(); }
   void CoreTransaction(const MqlTradeTransaction &trans) { core.Transaction(trans); }
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
   bool OpenRecovery(TLTickCapture &capture,TLEventLog &log)
   {
      if(!recovery_set_valid) { core.FailClosed("AUTO_CORE_INCOMPLETE_RECOVERY_SET_NO_RESET"); return false; }
      if(!recovery.Open(TLAutoCoreJournalPath("inputs"),TL_AUTO_CORE_SCOPE,!MQLInfoInteger(MQL_TESTER)))
      { core.FailClosed(recovery.error); return false; }
      TLEventLog silent; core.Recovering(true);
      string row; int result; MqlTick boundary[]; bool have_seed_rows=false;
      while((result=recovery.Next(row))==1)
      {
         if(row=="BASE_COMMIT")
         { if(!have_seed_rows || recovery_seeded) { result=-1; break; } recovery_seeded=true; continue; }
         string kind; int frame,ordinal; long index; MqlTick tick; MqlRates bar;
         if(!TLRecoveryParse(row,kind,frame,index,ordinal,tick,bar)) { result=-1; break; }
         if(kind=="Z")
         {
            if(recovery_seeded || (ArraySize(boundary)>0 && tick.time_msc!=boundary[0].time_msc)) { result=-1; break; }
            int n=ArraySize(boundary); ArrayResize(boundary,n+1); boundary[n]=tick; have_seed_rows=true; continue;
         }
         if(!recovery_seeded || index!=last_index+1 || tick.time_msc<last_msc) { result=-1; break; }
         if(kind=="B")
         {
            int seconds=PeriodSeconds(frames[frame]);
            if(bar.time<=last_open[frame] || bar.time+seconds>tick.time) { result=-1; break; }
            trackers[frame].ProcessBar(bar,tick.time_msc); core.ClosedBar(frame,bar,trackers[frame],tick,index,silent);
            last_open[frame]=bar.time; bars_seen++;
         }
         else
         {
            core.Prices(tick,index,silent);
            for(int i=0;i<5;i++) { trackers[i].ProcessTick(tick,index,ordinal,silent); core.Sync(i,trackers[i],tick,index,silent); }
            core.TickComplete(tick,index,silent); last_index=index; last_msc=tick.time_msc;
            if(ArraySize(boundary)>0 && boundary[0].time_msc!=tick.time_msc) ArrayResize(boundary,0);
            int n=ArraySize(boundary); ArrayResize(boundary,n+1); boundary[n]=tick;
         }
      }
      core.Recovering(false);
      if(result<0 || (have_seed_rows && !recovery_seeded) || (!recovery_seeded && core.HasPlans()) ||
         (recovery_seeded && !capture.Resume(symbol,boundary,last_index)))
      { core.FailClosed("AUTO_CORE_RECOVERY_CORRUPT_OR_INCOMPLETE:"+recovery.error); return false; }
      recovery_open=true;
      log.Write("AUTO_CORE_RECOVERY","EXPERIMENTAL_RECOVERY_V1","\"recovered_ticks\":"+(string)last_index+
         ",\"replayed_orders\":0,\"recovery_chain\":"+(string)recovery.Chain()+
         ",\"standalone_full_capture\":"+(last_index==0?"true":"false")+
         ",\"memberships_and_retests_rebuilt\":true,\"dispatch_locked\":true",TimeCurrent());
      return true;
   }
   bool SeedRecovery(TLTickCapture &capture)
   {
      if(!recovery_open) return false;
      if(recovery_seeded) return true;
      MqlTick boundary[]; capture.ExportBoundary(boundary); MqlRates empty={};
      if(ArraySize(boundary)==0) return false;
      for(int i=0;i<ArraySize(boundary);i++) if(!recovery.Append(TLRecoveryInput("Z",-1,0,0,boundary[i],empty))) return false;
      recovery_seeded=recovery.Append("BASE_COMMIT"); return recovery_seeded;
   }
   bool Recovered() { return recovery_seeded; }
#ifdef TRADERLAB_CORE_CHECKS
   bool FixtureBar(const int frame,const MqlRates &bar,const MqlTick &tick,const long index)
   {
      TLEventLog silent;
      if(!recovery.Append(TLRecoveryInput("B",frame,index,1,tick,bar))) return false;
      trackers[frame].ProcessBar(bar,tick.time_msc); core.ClosedBar(frame,bar,trackers[frame],tick,index,silent);
      last_open[frame]=bar.time; bars_seen++; return true;
   }
   string CheckState() { return core.CheckState(); }
   long CheckIndex() { return last_index; }
   int CheckGroups() { return core.CheckGroups(); }
   int CheckPending() { return core.CheckPending(); }
#endif
#endif
   virtual void BeforeTick(const MqlTick &tick,const long index,const int ordinal,TLEventLog &log)
   {
      if(halted) return;
      if(index!=last_index+1 || tick.time_msc<last_msc)
      { Halt("nonchronological_tick_dispatch","ALL",tick,log); return; }
      ulong started=GetMicrosecondCount();
      for(int tf=0;tf<5;tf++)
      {
         int seconds=PeriodSeconds(frames[tf]);
         datetime bucket=(datetime)(((long)tick.time/seconds)*seconds);
         if(bucket==checked_bucket[tf]) continue;
         // cutoff excludes the current forming candle even in a recovered batch.
         datetime cutoff=bucket-1;
         MqlRates bars[]; ArraySetAsSeries(bars,false);
         ResetLastError(); rate_calls++;
         int count=last_open[tf]==0?CopyRates(symbol,frames[tf],cutoff,21,bars):
                   CopyRates(symbol,frames[tf],last_open[tf]+seconds,cutoff,bars);
         int error=GetLastError();
         if(count<0 || error!=0 || count!=ArraySize(bars) || (last_open[tf]==0 && count==0))
         { Halt("closed_history_unavailable:"+(string)error,names[tf],tick,log); break; }
         for(int i=0;i<count;i++)
         {
            if(bars[i].time<=last_open[tf] || bars[i].time+seconds>tick.time ||
               !MathIsValidNumber(bars[i].high) || !MathIsValidNumber(bars[i].low) ||
               !MathIsValidNumber(bars[i].open) || !MathIsValidNumber(bars[i].close) ||
               bars[i].low<=0 || bars[i].low>MathMin(bars[i].open,bars[i].close) ||
               bars[i].high<MathMax(bars[i].open,bars[i].close) || bars[i].low>bars[i].high)
            { Halt("invalid_asof_closed_bar",names[tf],tick,log); break; }
            // Warm-up history is available NOW, not retroactively at its open.
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
            if(!recovery_seeded || !recovery.Append(TLRecoveryInput("B",tf,index,ordinal,tick,bars[i])))
            { Halt("recovery_bar_write_failed",names[tf],tick,log); break; }
#endif
            trackers[tf].ProcessBar(bars[i],tick.time_msc);
            core.ClosedBar(tf,bars[i],trackers[tf],tick,index,log);
            log.Write("BOS_TRACKER_CLOSED_BAR","TF-01/BOS-01",
                      "\"symbol\":"+TLQuote(symbol)+",\"timeframe\":"+TLQuote(names[tf])+
                      ",\"opened_at\":"+TLIso(bars[i].time,offset)+
                      ",\"open\":"+TLQuote(DoubleToString(bars[i].open,8))+
                      ",\"high\":"+TLQuote(DoubleToString(bars[i].high,8))+
                      ",\"low\":"+TLQuote(DoubleToString(bars[i].low,8))+
                      ",\"close\":"+TLQuote(DoubleToString(bars[i].close,8))+
                      ",\"before_tick_index\":"+(string)index+",\"diagnostic_only\":true",
                      tick.time,(int)(tick.time_msc%1000));
            last_open[tf]=bars[i].time; bars_seen++;
         }
         if(halted) break;
         checked_bucket[tf]=bucket;
      }
      elapsed_us+=GetMicrosecondCount()-started;
   }
   virtual void AfterTick(const MqlTick &tick,const long index,const int ordinal,TLEventLog &log)
   {
      if(halted) return;
      ulong started=GetMicrosecondCount();
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      MqlRates empty={};
      if(!recovery_seeded || !recovery.Append(TLRecoveryInput("T",-1,index,ordinal,tick,empty)))
      { Halt("recovery_tick_write_failed","ALL",tick,log); return; }
#endif
      core.Prices(tick,index,log);
      for(int i=0;i<5;i++) { trackers[i].ProcessTick(tick,index,ordinal,log); core.Sync(i,trackers[i],tick,index,log); }
      core.TickComplete(tick,index,log);
      last_index=index; last_msc=tick.time_msc;
      elapsed_us+=GetMicrosecondCount()-started;
   }
   void Summary(TLEventLog &log)
   {
      core.Summary(log);
      long breaks=0,returns=0,inspections=0; int stored=0,active=0;
      for(int i=0;i<5;i++)
      {
         breaks+=trackers[i].Breaks(); returns+=trackers[i].Returns(); inspections+=trackers[i].Inspections();
         stored+=trackers[i].Count(); active+=trackers[i].ActiveCount();
      }
      // Real measured runtime and active/archive sizes, never an expiry heuristic.
      log.Write("BOS_TRACKER_SUMMARY","BOS-01/TOUCH-01",
                "\"detection_halted\":"+(halted?"true":"false")+",\"processed_ticks\":"+(string)last_index+
                ",\"closed_bars\":"+(string)bars_seen+",\"copyrates_calls\":"+(string)rate_calls+
                ",\"intrabar_breaks\":"+(string)breaks+",\"first_returns\":"+(string)returns+
                ",\"stored_bos\":"+(string)stored+",\"active_bos\":"+(string)active+
                ",\"candidate_inspections\":"+(string)inspections+",\"processing_us\":"+(string)elapsed_us+
                ",\"automatic_setups\":0,\"execution_policy\":\"UNRESOLVED\"",TimeCurrent());
   }
};
#endif
