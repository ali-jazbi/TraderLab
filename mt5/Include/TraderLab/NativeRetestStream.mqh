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
   }
   void Configure(const string broker_symbol,const int server_offset)
   {
      symbol=broker_symbol; offset=server_offset;
      for(int i=0;i<5;i++) trackers[i].Configure(names[i],offset);
   }
   void ConfigureCore(const ulong magic,const string calendar_path,const int lead,const string packages="",const bool request_execution=false,const int tester_experiment=0)
   { core.Configure(symbol,offset,magic,calendar_path,lead,packages,request_execution,tester_experiment); }
   void CoreRefreshPackages() { core.RefreshPackages(); }
   void CoreFinishDrain(const MqlTick &before,const MqlTick &tail,const bool active,TLEventLog &log)
   { core.FinishLiveDrain(before,tail,active,log); }
   void CoreService() { core.Service(); }
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
