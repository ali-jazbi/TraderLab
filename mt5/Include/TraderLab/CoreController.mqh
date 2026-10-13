#ifndef TRADERLAB_CORE_CONTROLLER_MQH
#define TRADERLAB_CORE_CONTROLLER_MQH
#include "Detection.mqh"
#include "CoreLifecycle.mqh"

string TLCoreFillName(const int value) { return value==2?"FULL":value==1?"PARTIAL":"UNFILLED"; }
bool TLCoreField(const string value)
{ return value!="" && StringFind(value,"|")<0 && StringFind(value,"\n")<0 && StringFind(value,"\r")<0; }

// A truncated/unavailable journal blocks execution; touch is never reset.
class TLCoreConsumption
{
private:
   int file;
   bool ready;
   string ids[];
   bool Load(const string path,const string scope,const bool common)
   {
      if(file!=INVALID_HANDLE) return false;
      file=FileOpen(path,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|(common?FILE_COMMON:0),'|',CP_UTF8);
      if(file==INVALID_HANDLE) return false;
      if(FileSize(file)==0)
      { ResetLastError(); uint n=FileWrite(file,"SCOPE",scope); FileFlush(file); if(n==0 || GetLastError()!=0) return false; }
      else
      {
         if(FileReadString(file)!="SCOPE" || FileReadString(file)!=scope) return false;
         while(!FileIsEnding(file))
         {
            string kind=FileReadString(file); if(kind=="" && FileIsEnding(file)) break;
            string id=FileReadString(file); long msc=StringToInteger(FileReadString(file));
            if(kind!="RETURN" || !TLCoreField(id) || msc<=0) return false;
            if(!Seen(id)) { int n=ArraySize(ids); ArrayResize(ids,n+1); ids[n]=id; }
         }
      }
      ready=FileSeek(file,0,SEEK_END); return ready;
   }
public:
   TLCoreConsumption() { file=INVALID_HANDLE; ready=false; }
   ~TLCoreConsumption() { if(file!=INVALID_HANDLE) FileClose(file); }
   bool Seen(const string id) { for(int i=0;i<ArraySize(ids);i++) if(ids[i]==id) return true; return false; }
   bool Open(const string symbol,const ulong magic)
   {
      if(MQLInfoInteger(MQL_TESTER) || magic==0 || !TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE))) return false;
      string server=AccountInfoString(ACCOUNT_SERVER),safe=server;
      for(int c=0;c<StringLen(safe);c++) { ushort v=StringGetCharacter(safe,c); if(!((v>=48&&v<=57)||(v>=65&&v<=90)||(v>=97&&v<=122))) StringSetCharacter(safe,c,'_'); }
      return Load("TraderLab-core-consumed-"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+"-"+safe+".csv",
                  (string)AccountInfoInteger(ACCOUNT_LOGIN)+":"+server+":"+symbol+":"+(string)magic,true);
   }
#ifdef TRADERLAB_CORE_CHECKS
   // Available only in the reducer-check script; never uses production FILE_COMMON.
   bool OpenFixture(const string path,const string scope) { return Load(path,scope,false); }
#endif
   bool Consume(const string id,const long msc)
   {
      if(!ready || file==INVALID_HANDLE || !TLCoreField(id) || msc<=0) return false;
      if(Seen(id)) return true;
      ResetLastError(); uint written=FileWrite(file,"RETURN",id,msc); FileFlush(file);
      if(written==0 || GetLastError()!=0) return false;
      int n=ArraySize(ids); ArrayResize(ids,n+1); ids[n]=id; return true;
   }
};
struct TLCoreBos
{
   string id;
   int frame,tracker_id;
   bool startup;
   TLBosHistory history;
};
struct TLCoreGap { string id; int frame; long before_tick_index; TLDetectedGap value; };
struct TLCorePair { int bos,gap; bool return_reported; };

class TLCoreController
{
private:
   TLBarDetector detectors[5];
   string names[5],symbol;
   TLCoreBos bos[];
   TLCoreGap gaps[];
   TLCorePair pairs[];
   TLCoreTradeBook book;
   TLCoreConsumption consumption;
   int offset;
   bool halted,durable;
   long last_index,last_msc;
   string GapId(const int frame,const TLDetectedGap &g)
   { return TLBosIdentity(names[frame],g.side,g.candidate,offset); }
   string Evidence(const int b,const int g)
   {
      TLCoreBos c=bos[b]; TLCoreGap f=gaps[g]; TLDetectedGap v=f.value;
      double level=c.history.side==1?c.history.high:c.history.low;
      TLFirstReturn r=c.history.lanes[0].returns[0];
      return "\"candidate_id\":"+TLQuote(c.id+"~"+f.id)+",\"bos_id\":"+TLQuote(c.id)+",\"fvg_id\":"+TLQuote(f.id)+
             ",\"ob_id\":"+TLQuote(f.id+(v.side==1?":C3":":C1"))+",\"bos_timeframe\":"+TLQuote(names[c.frame])+
             ",\"fvg_timeframe\":"+TLQuote(names[f.frame])+",\"side\":"+TLQuote(v.side==1?"BUY":"SELL")+
             ",\"candidate_at\":"+TLIso(c.history.opened,offset)+",\"qualified_at\":"+TLMscIso(c.history.qualified_msc,offset)+
             ",\"fvg_candidate_at\":"+TLIso(v.candidate,offset)+",\"fvg_available_at\":"+TLMscIso(v.available_msc,offset)+
             ",\"formation_at\":"+TLMscIso(v.formation_msc,offset)+",\"ob_anchor_at\":"+TLIso(v.anchor,offset)+
             ",\"bos_level\":"+TLQuote(DoubleToString(level,8))+",\"entry_reference\":"+TLQuote(DoubleToString(TLCoreEntryReference(v.side,level),8))+
             ",\"fvg\":["+TLQuote(DoubleToString(v.low,8))+","+TLQuote(DoubleToString(v.high,8))+"]"+
             ",\"ob\":["+TLQuote(DoubleToString(v.ob_low,8))+","+TLQuote(DoubleToString(v.ob_high,8))+"]"+
             ",\"fill_state\":"+TLQuote(TLCoreFillName(v.fill))+",\"break_at\":"+TLMscIso(c.history.lanes[0].break_msc,offset)+
             ",\"first_return_at\":"+TLMscIso(r.return_msc,offset)+",\"first_return_consumed\":"+(r.consumed?"true":"false")+
             ",\"exact_quote\":"+(r.exact?"true":"false")+",\"previous_quote\":"+TLQuote(DoubleToString(r.previous_return,8))+
             ",\"observed_quote\":"+TLQuote(DoubleToString(r.observed,8))+",\"startup_history\":"+(c.startup?"true":"false")+
             ",\"signal_quote\":\"bid\",\"tradable_setup\":false,\"broker_orders_enabled\":false";
   }
   string Reasons(const int b,const int g)
   {
      TLDetectedGap v=gaps[g].value; TLFirstReturn r=bos[b].history.lanes[0].returns[0];
      string reasons="[\"TODO_STRATEGY_UNRESOLVED:package_grouping\"";
      if(bos[b].frame!=gaps[g].frame) reasons+=",\"TODO_STRATEGY_UNRESOLVED:cross_timeframe_association\"";
      if(v.fill==2) reasons+=",\"FVG_FULL_FILL_INVALID\"";
      if(v.fill==1) reasons+=",\"TODO_STRATEGY_UNRESOLVED:partial_fill_policy\"";
      if(bos[b].startup) reasons+=",\"STARTUP_HISTORY_NOT_EXECUTION_PROOF\"";
      if(bos[b].history.lanes[0].state==TL_BLOCKED) reasons+=",\"INTRABAR_BREAK_UNOBSERVED_NOT_EXECUTABLE\"";
      if(r.consumed && TLCoreBeforeAvailability(r.return_msc,r.return_index,v.available_msc,gaps[g].before_tick_index))
         reasons+=",\"FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION\"";
      if(r.consumed && !r.exact) reasons+=",\"MISSED_EXACT_SIGNAL_QUOTE_NO_FILL\"";
      if(!durable) reasons+=",\"CORE_CONSUMPTION_JOURNAL_UNAVAILABLE\"";
      return reasons+"]";
   }
   void Report(const int b,const int g,const string event,const MqlTick &tick,const long index,TLEventLog &log)
   {
      log.Write(event,"BOS-02/FVG-03/OWNER-51/OWNER-52",Evidence(b,g)+",\"reasons\":"+Reasons(b,g)+
                ",\"tick_index\":"+(string)index+
                ",\"minimal_evidence\":[\"Owner package candle/timeframe mapping, complete BOS member IDs and group finalization time\","+
                "\"Explicit PARTIAL permission if applicable; consumed returns cannot be retroactively approved\","+
                "\"Sourced session/news calendar, costs and reviewed lifecycle guards before a new live opportunity\"]",
                tick.time,(int)(tick.time_msc%1000));
   }
   void PairNew(const int only_bos,const int only_gap,const MqlTick &tick,const long index,TLEventLog &log)
   {
      for(int b=0;b<ArraySize(bos);b++) for(int g=0;g<ArraySize(gaps);g++)
      {
         if(only_bos>=0 && b!=only_bos) continue;
         if(only_gap>=0 && g!=only_gap) continue;
         TLDetectedGap v=gaps[g].value; double level=bos[b].history.side==1?bos[b].history.high:bos[b].history.low;
         if(bos[b].history.side!=v.side || level<v.low || level>v.high) continue;
         bool seen=false; for(int p=0;p<ArraySize(pairs);p++) if(pairs[p].bos==b && pairs[p].gap==g) { seen=true; break; }
         if(seen) continue;
         int n=ArraySize(pairs); ArrayResize(pairs,n+1,256); pairs[n].bos=b; pairs[n].gap=g;
         pairs[n].return_reported=bos[b].history.lanes[0].returns[0].consumed;
         Report(b,g,"CORE_SETUP_CANDIDATE",tick,index,log);
      }
   }
public:
   TLCoreController()
   {
      names[0]="M1"; names[1]="M5"; names[2]="M15"; names[3]="H1"; names[4]="H4";
      for(int i=0;i<5;i++) detectors[i].ConfigureCore();
      halted=false; durable=false; last_index=0; last_msc=0; offset=INT_MAX;
   }
   void Configure(const string name,const int server_offset,const ulong magic,const string calendar_path,const int lead)
   {
      symbol=name; offset=server_offset;
      durable=consumption.Open(name,magic);
      book.Configure(name,magic,server_offset,calendar_path,lead);
   }
   void ClosedBar(const int frame,const MqlRates &bar,TLBosTracker &tracker,const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(halted) return;
      for(int i=0;i<ArraySize(gaps);i++) if(gaps[i].frame==frame)
      {
         TLDetectedGap v=gaps[i].value;
         bool full=v.side==1?bar.low<=v.low:bar.high>=v.high;
         bool partial=v.side==1?bar.low<v.high:bar.high>v.low;
         int next=full?2:partial?(int)MathMax(v.fill,1):v.fill;
         if(next!=v.fill)
         {
            gaps[i].value.fill=next;
            log.Write("CORE_FVG_VALIDITY_CHANGED","FVG-03","\"fvg_id\":"+TLQuote(gaps[i].id)+
                      ",\"fill_state\":"+TLQuote(TLCoreFillName(next))+",\"tick_index\":"+(string)index,tick.time,(int)(tick.time_msc%1000));
         }
      }
      Sync(frame,tracker,tick,index,log,true);
      detectors[frame].Process(bar,symbol,names[frame],tick.time,(int)(tick.time_msc%1000),offset,log);
      TLDetectedGap value;
      if(detectors[frame].Gap(value))
      {
         int n=ArraySize(gaps); ArrayResize(gaps,n+1); gaps[n].id=GapId(frame,value); gaps[n].frame=frame;
         gaps[n].before_tick_index=index; gaps[n].value=value;
         PairNew(-1,n,tick,index,log);
      }
   }
   void Sync(const int frame,TLBosTracker &tracker,const MqlTick &tick,const long index,TLEventLog &log,const bool from_bar=false)
   {
      if(halted) return;
      for(int i=0;i<tracker.ChangedCount();i++)
      {
         TLBosHistory h; int id; if(!tracker.Changed(i,id,h) || h.qualified_msc==0) continue;
         int b=-1; for(int j=0;j<ArraySize(bos);j++) if(bos[j].frame==frame && bos[j].tracker_id==id) { b=j; break; }
         bool added=b<0;
         if(added)
         {
            b=ArraySize(bos); ArrayResize(bos,b+1,256); bos[b].id=TLBosIdentity(names[frame],h.side,h.opened,offset);
            bos[b].frame=frame; bos[b].tracker_id=id; bos[b].startup=index==1;
         }
         bool prior=!added && bos[b].history.lanes[0].returns[0].consumed;
         bos[b].history=h;
         TLFirstReturn r=h.lanes[0].returns[0];
         bool was_seen=consumption.Seen(bos[b].id);
         if(r.consumed && !prior)
         {
            bool persisted=consumption.Consume(bos[b].id,r.return_msc);
            if(!persisted) durable=false;
            log.Write("CORE_BOS_CONSUMED","TOUCH-01","\"bos_id\":"+TLQuote(bos[b].id)+
                      ",\"first_return_at\":"+TLMscIso(r.return_msc,offset)+",\"exact_quote\":"+(r.exact?"true":"false")+
                      ",\"tick_index\":"+(string)index+",\"durable\":"+(persisted?"true":"false")+
                      ",\"execution_context\":"+TLQuote(MQLInfoInteger(MQL_TESTER)?"tester_history":"accepted_history_not_live_execution_proof"),
                      tick.time,(int)(tick.time_msc%1000));
         }
         if(added) PairNew(b,-1,tick,index,log);
         if(r.consumed && !prior) for(int p=0;p<ArraySize(pairs);p++) if(pairs[p].bos==b && !pairs[p].return_reported)
         {
            pairs[p].return_reported=true; int g=pairs[p].gap;
            Report(b,g,"CORE_FIRST_RETURN_BLOCKED",tick,index,log);
            TLCoreGuards guards; ZeroMemory(guards); guards.startup_history=bos[b].startup;
            // The owner has not supplied group finalization; never manufacture it.
            guards.group_confirmed=false; guards.group_final=false; guards.restart=durable && !was_seen;
            TLCoreTrade trade; ZeroMemory(trade); trade.setup=bos[b].id+"~"+gaps[g].id; trade.side=h.side;
            trade.single=true; trade.planned=TLCoreEntryReference(h.side,h.side==1?h.high:h.low); trade.reference=trade.planned;
            book.Begin(trade,guards,gaps[g].value.fill,r.exact);
         }
      }
   }
   void TickComplete(const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(!TLCoreTickOrder(last_index,last_msc,index,tick.time_msc))
      {
         halted=true; book.Emergency("CORE_MISSED_OR_REORDERED_TICK");
         log.Write("CORE_CONTROLLER_HALTED","TOUCH-01","\"reason\":\"nonchronological_tick_dispatch\",\"capture_unchanged\":true",tick.time,(int)(tick.time_msc%1000));
      }
      last_index=index; last_msc=tick.time_msc;
   }
   void Prices(const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(halted) return;
      for(int i=0;i<ArraySize(gaps);i++)
      {
         TLDetectedGap v=gaps[i].value;
         bool full=v.side==1?tick.bid<=v.low:tick.bid>=v.high;
         bool partial=v.side==1?tick.bid<v.high:tick.bid>v.low;
         int next=full?2:partial?(int)MathMax(v.fill,1):v.fill;
         if(next!=v.fill)
         {
            gaps[i].value.fill=next;
            log.Write("CORE_FVG_VALIDITY_CHANGED","FVG-03","\"fvg_id\":"+TLQuote(gaps[i].id)+
                      ",\"fill_state\":"+TLQuote(TLCoreFillName(next))+",\"source\":\"observed_bid\",\"tick_index\":"+
                      (string)index,tick.time,(int)(tick.time_msc%1000));
         }
      }
   }
   void FailClosed(const string reason) { halted=true; book.Emergency(reason); }
   void Service() { book.Service(); }
   void Transaction(const MqlTradeTransaction &trans)
   { if(trans.type==TRADE_TRANSACTION_DEAL_ADD && trans.deal>0) book.ObserveDeal(trans.deal); book.Service(); }
   void Summary(TLEventLog &log)
   {
      log.Write("CORE_CONTROLLER_SUMMARY","OWNER-51/OWNER-52","\"candidates\":"+(string)ArraySize(pairs)+
                ",\"qualified_bos\":"+(string)ArraySize(bos)+",\"fvgs\":"+(string)ArraySize(gaps)+
                ",\"processed_ticks\":"+(string)last_index+",\"controller_halted\":"+(halted?"true":"false")+
                ",\"approved_setups\":0,\"broker_orders_enabled\":false,\"dispatch_locked\":true",TimeCurrent());
   }
};
#endif
