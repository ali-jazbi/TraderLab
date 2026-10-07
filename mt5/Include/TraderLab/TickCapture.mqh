#ifndef TRADERLAB_TICK_CAPTURE_MQH
#define TRADERLAB_TICK_CAPTURE_MQH
#include "EventLog.mqh"

const int TL_CAPTURE_TIMER_SECONDS=1;

bool TLSameTick(const MqlTick &a,const MqlTick &b)
{
   return a.time==b.time && a.time_msc==b.time_msc && a.bid==b.bid && a.ask==b.ask &&
          a.last==b.last && a.volume==b.volume && a.flags==b.flags && a.volume_real==b.volume_real;
}

// Pure, deterministic cursor: retain the entire ordered boundary millisecond,
// including repeated identical records. No hash, price-only dedupe or callback ID.
class TLTickCursor
{
private:
   MqlTick boundary[];
   long cursor_msc;
   bool ready;
   bool ValidBatch(const MqlTick &ticks[],string &reason)
   {
      if(ArraySize(ticks)==0) { reason="empty_history"; return false; }
      for(int i=0;i<ArraySize(ticks);i++)
      {
         if(ticks[i].time_msc<=0 || (long)ticks[i].time!=ticks[i].time_msc/1000 ||
            !MathIsValidNumber(ticks[i].bid) || !MathIsValidNumber(ticks[i].ask) ||
            !MathIsValidNumber(ticks[i].last) || !MathIsValidNumber(ticks[i].volume_real))
         { reason="invalid_raw_tick"; return false; }
         if(i>0 && ticks[i].time_msc<ticks[i-1].time_msc)
         { reason="history_not_chronological"; return false; }
      }
      return true;
   }
   bool SaveBoundary(const MqlTick &ticks[],string &reason)
   {
      int end=ArraySize(ticks)-1, first=end;
      while(first>0 && ticks[first-1].time_msc==ticks[end].time_msc) first--;
      MqlTick next[];
      if(ArrayResize(next,end-first+1)!=end-first+1)
      { reason="cursor_allocation_failed"; return false; }
      for(int i=first;i<=end;i++) next[i-first]=ticks[i];
      if(!ArraySwap(boundary,next)) { reason="cursor_swap_failed"; return false; }
      cursor_msc=ticks[end].time_msc;
      ready=true;
      return true;
   }
public:
   TLTickCursor() { cursor_msc=0; ready=false; }
   long Millisecond() { return cursor_msc; }
   int BoundaryCount() { return ArraySize(boundary); }
   bool Initialize(const MqlTick &baseline[],string &reason)
   {
      reason="";
      if(!ValidBatch(baseline,reason)) return false;
      if(baseline[0].time_msc!=baseline[ArraySize(baseline)-1].time_msc)
      { reason="startup_baseline_spans_milliseconds"; return false; }
      return SaveBoundary(baseline,reason);
   }
   bool Consume(const MqlTick &ticks[],int &skip,string &reason)
   {
      skip=0; reason="";
      if(!ready) { reason="cursor_not_initialized"; return false; }
      if(!ValidBatch(ticks,reason)) return false;
      if(ticks[0].time_msc!=cursor_msc || ArraySize(ticks)<ArraySize(boundary))
      { reason="boundary_prefix_missing"; return false; }
      for(int i=0;i<ArraySize(boundary);i++)
         if(!TLSameTick(ticks[i],boundary[i]))
         { reason="boundary_prefix_changed"; return false; }
      int known=ArraySize(boundary);
      // Advance only after validating the WHOLE drain. On failure, emit nothing.
      if(!SaveBoundary(ticks,reason)) return false;
      skip=known;
      return true;
   }
};

class TLTickCapture
{
private:
   TLTickCursor cursor;
   string symbol;
   bool halted, have_latest;
   MqlTick latest;
   long callbacks, drains, copy_calls, emitted, recovered, direct_matches, overlap_skips;
   long ambiguities, copy_errors, snapshot_errors, timer_errors;
   void Diagnostic(TLEventLog &log,const string name,const string details)
   {
      if(have_latest) log.Write(name,"SCOPE-01/TOUCH-01",details,latest.time,(int)(latest.time_msc%1000));
      else log.Write(name,"SCOPE-01/TOUCH-01",details,TimeCurrent());
   }
   void Ambiguous(TLEventLog &log,const string reason,const string source)
   {
      ambiguities++; halted=true;
      Diagnostic(log,"TICK_CAPTURE_AMBIGUITY","\"reason\":"+TLQuote(reason)+
                 ",\"source\":"+TLQuote(source)+",\"cursor_time_msc\":"+(string)cursor.Millisecond()+
                 ",\"capture_halted\":true");
   }
   bool ReadHead(MqlTick &head,TLEventLog &log,const string source)
   {
      ResetLastError();
      if(SymbolInfoTick(symbol,head) && head.time_msc>0) return true;
      int error=GetLastError(); snapshot_errors++;
      Diagnostic(log,"TICK_CAPTURE_ERROR","\"operation\":\"SymbolInfoTick\",\"error_code\":"+
                 (string)error+",\"source\":"+TLQuote(source)+",\"cursor_advanced\":false");
      return false;
   }
   bool ReadRange(const long from_msc,const long to_msc,MqlTick &ticks[],TLEventLog &log,const string source)
   {
      copy_calls++; ResetLastError();
      int count=CopyTicksRange(symbol,ticks,COPY_TICKS_ALL,(ulong)from_msc,(ulong)to_msc);
      int error=GetLastError();
      if(count>=0 && error==0 && count==ArraySize(ticks)) return true;
      // A positive partial result with ERR_HISTORY_TIMEOUT is not accepted.
      copy_errors++;
      Diagnostic(log,"TICK_CAPTURE_ERROR","\"operation\":\"CopyTicksRange\",\"error_code\":"+
                 (string)error+",\"returned_ticks\":"+(string)count+",\"source\":"+TLQuote(source)+
                 ",\"from_msc\":"+(string)from_msc+",\"to_msc\":"+(string)to_msc+
                 ",\"cursor_advanced\":false");
      return false;
   }
   bool ContainsHead(const MqlTick &ticks[],const MqlTick &head)
   {
      for(int i=ArraySize(ticks)-1;i>=0 && ticks[i].time_msc>=head.time_msc;i--)
         if(TLSameTick(ticks[i],head)) return true;
      return false;
   }
public:
   TLTickCapture()
   {
      halted=true; have_latest=false;
      callbacks=0; drains=0; copy_calls=0; emitted=0; recovered=0; direct_matches=0; overlap_skips=0;
      ambiguities=0; copy_errors=0; snapshot_errors=0; timer_errors=0;
   }
   bool Active() { return !halted; }
   bool StartTimer(TLEventLog &log)
   {
      ResetLastError();
      if(EventSetTimer(TL_CAPTURE_TIMER_SECONDS)) return true;
      int error=GetLastError(); timer_errors++; halted=true;
      Diagnostic(log,"TICK_CAPTURE_ERROR","\"operation\":\"EventSetTimer\",\"error_code\":"+
                 (string)error+",\"capture_halted\":true");
      return false;
   }
   bool Latest(MqlTick &tick) { if(!have_latest) return false; tick=latest; return true; }
   bool Start(const string configured_symbol,TLEventLog &log)
   {
      symbol=configured_symbol;
      MqlTick head, baseline[]; string reason;
      if(!ReadHead(head,log,"startup")) return false;
      if(!ReadRange(head.time_msc,head.time_msc,baseline,log,"startup")) return false;
      if(!ContainsHead(baseline,head)) { Ambiguous(log,"startup_head_missing","startup"); return false; }
      if(!cursor.Initialize(baseline,reason)) { Ambiguous(log,reason,"startup"); return false; }
      halted=false;
      log.Write("TICK_CAPTURE_START","SCOPE-01/TOUCH-01",
                "\"capture_version\":\"loss_aware_v1\",\"cursor_time_msc\":"+(string)cursor.Millisecond()+
                ",\"cursor_boundary_count\":"+(string)cursor.BoundaryCount()+
                ",\"startup_policy\":\"exclude_baseline_and_earlier_ticks\""+
                ",\"same_millisecond_policy\":\"ordered_full_prefix\",\"timer_interval_ms\":"+
                (string)(TL_CAPTURE_TIMER_SECONDS*1000)+",\"broker_feed_complete\":null",TimeCurrent());
      return true;
   }
   void OnCallback(TLEventLog &log) { callbacks++; Drain("ontick",log); }
   void Drain(const string source,TLEventLog &log)
   {
      drains++;
      if(halted) return;
      MqlTick head, ticks[];
      if(!ReadHead(head,log,source)) return;
      if(head.time_msc<cursor.Millisecond()) { Ambiguous(log,"head_before_cursor",source); return; }
      if(!ReadRange(cursor.Millisecond(),head.time_msc,ticks,log,source)) return;
      if(ArraySize(ticks)>0 && ticks[ArraySize(ticks)-1].time_msc>head.time_msc)
      { Ambiguous(log,"history_outside_requested_range",source); return; }
      if(!ContainsHead(ticks,head)) { Ambiguous(log,"snapshot_head_missing",source); return; }
      int skip; string reason;
      if(!cursor.Consume(ticks,skip,reason)) { Ambiguous(log,reason,source); return; }
      overlap_skips+=skip;
      int direct=-1;
      if(source=="ontick")
         for(int i=ArraySize(ticks)-1;i>=skip;i--)
            if(TLSameTick(ticks[i],head)) { direct=i; break; }
      int ordinal=0; long first_index=emitted+1, recovered_here=0;
      for(int i=0;i<ArraySize(ticks);i++)
      {
         ordinal=(i>0 && ticks[i].time_msc==ticks[i-1].time_msc)?ordinal+1:1;
         if(i<skip) continue;
         emitted++;
         if(i==direct) direct_matches++; else { recovered++; recovered_here++; }
         MqlTick tick=ticks[i];
         log.Write("TICK","TOUCH-01","\"kind\":\"tick\",\"symbol\":"+TLQuote(symbol)+
                   ",\"tick_index\":"+(string)emitted+",\"time_msc\":"+(string)tick.time_msc+
                   ",\"broker_time_seconds\":"+(string)(long)tick.time+
                   ",\"millisecond_ordinal\":"+(string)ordinal+",\"flags\":"+(string)tick.flags+
                   ",\"last\":"+TLQuote(DoubleToString(tick.last,16))+",\"volume\":"+(string)tick.volume+
                   ",\"volume_real\":"+TLQuote(DoubleToString(tick.volume_real,16))+
                   ",\"bid\":"+TLQuote(DoubleToString(tick.bid,8))+",\"ask\":"+TLQuote(DoubleToString(tick.ask,8))+
                   ",\"spread_price\":"+TLQuote(DoubleToString(tick.ask-tick.bid,8)),tick.time,(int)(tick.time_msc%1000));
         latest=tick; have_latest=true;
      }
      if(recovered_here>0)
         Diagnostic(log,"TICK_CAPTURE_RECOVERY","\"source\":"+TLQuote(source)+
                    ",\"first_tick_index\":"+(string)first_index+",\"last_tick_index\":"+(string)emitted+
                    ",\"recovered_ticks\":"+(string)recovered_here);
   }
   void Summary(TLEventLog &log)
   {
      bool valid=!halted && ambiguities==0 && copy_errors==0 && snapshot_errors==0 && timer_errors==0;
      log.Write("TICK_CAPTURE_SUMMARY","SCOPE-01/TOUCH-01",
                "\"capture_version\":\"loss_aware_v1\",\"ontick_callbacks\":"+(string)callbacks+
                ",\"drain_calls\":"+(string)drains+",\"copyticks_calls\":"+(string)copy_calls+
                ",\"emitted_ticks\":"+(string)emitted+",\"callback_snapshot_matches\":"+(string)direct_matches+
                ",\"recovered_ticks\":"+(string)recovered+",\"duplicate_overlap_skips\":"+(string)overlap_skips+
                ",\"cursor_ambiguities\":"+(string)ambiguities+",\"copyticks_errors\":"+(string)copy_errors+
                ",\"snapshot_errors\":"+(string)snapshot_errors+",\"timer_errors\":"+(string)timer_errors+
                ",\"capture_halted\":"+(halted?"true":"false")+
                ",\"terminal_cursor_evidence_valid\":"+(valid?"true":"false")+
                ",\"broker_feed_complete\":null,\"cursor_time_msc\":"+(string)cursor.Millisecond()+
                ",\"cursor_boundary_count\":"+(string)cursor.BoundaryCount(),TimeCurrent());
   }
};
#endif
