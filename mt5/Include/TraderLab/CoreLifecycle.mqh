#ifndef TRADERLAB_CORE_LIFECYCLE_MQH
#define TRADERLAB_CORE_LIFECYCLE_MQH
#include "DemoGateway.mqh"
#include "Rules.mqh"

// Pure reducers accept evidence; no quote interpolation, clock defaults or broker calls.
struct TLCoreGuards
{
   bool group_confirmed,group_final,calendar,news,daily,restart,live_tick;
   bool startup_history,single_be_defined;
};
string TLCoreEntryBlock(const TLCoreGuards &g,const int fill,const bool single,const bool exact)
{
   if(!exact) return "MISSED_EXACT_SIGNAL_QUOTE_NO_FILL";
   if(fill<0 || fill>2) return "FVG_STATE_UNVERIFIED";
   if(fill==2) return "FVG_FULL_FILL_INVALID";
   if(fill==1) return "TODO_STRATEGY_UNRESOLVED:partial_fill_policy";
   if(g.startup_history) return "STARTUP_HISTORY_NOT_EXECUTION_PROOF";
   if(!g.group_confirmed || !g.group_final) return "TODO_STRATEGY_UNRESOLVED:package_grouping";
   if(single && !g.single_be_defined) return "TODO_STRATEGY_UNRESOLVED:single_be_anchor";
   if(!g.calendar || !g.news) return "SESSION_NEWS_CALENDAR_UNAVAILABLE";
   if(!g.daily) return "DAILY_NEW_ENTRIES_HALTED";
   if(!g.restart) return "RESTART_RECONCILIATION_REQUIRED";
   if(!g.live_tick) return "HISTORICAL_OR_DELAYED_QUOTE_NOT_EXECUTABLE";
   return "";
}
struct TLCoreLeg
{
   ulong entry_deal,exit_deal,position;
   bool open;
   double fill,stop,target,entry_cost,net;
};
bool TLCoreFill(TLCoreLeg &leg,const int side,const bool single,const double shared_stop,const double target,
                const ulong deal,const ulong position,const double volume,const double fill,const double cost)
{
   if(leg.entry_deal>0) return leg.entry_deal==deal && leg.position==position && leg.fill==fill &&
                              leg.entry_cost==cost && leg.target==target && volume==TL_LEG_LOTS;
   double stop=single?TLSingleFillStop(side,fill):shared_stop;
   if((side!=1 && side!=-1) || deal==0 || position==0 || volume!=TL_LEG_LOTS || fill<=0 ||
      !MathIsValidNumber(fill) || !MathIsValidNumber(cost) || !MathIsValidNumber(stop) ||
      !MathIsValidNumber(target) || (side==1?(stop>=fill || target<=fill):(stop<=fill || target>=fill))) return false;
   leg.entry_deal=deal; leg.position=position; leg.open=true; leg.fill=fill; leg.entry_cost=cost;
   leg.stop=single?TLSingleFillStop(side,fill):shared_stop; leg.target=target; return true;
}
bool TLCoreExit(TLCoreLeg &leg,const ulong deal,const ulong position,const double volume,const double net_exit)
{
   if(leg.exit_deal>0) return leg.exit_deal==deal && leg.position==position && volume==TL_LEG_LOTS &&
                             leg.net==net_exit+leg.entry_cost;
   if(!leg.open || position!=leg.position || deal==0 || volume!=TL_LEG_LOTS || !MathIsValidNumber(net_exit)) return false;
   leg.exit_deal=deal; leg.open=false; leg.net=net_exit+leg.entry_cost; return true;
}
bool TLCoreBreakEven(const int side,const bool single,const bool single_anchor_known,const bool actual_anchor,
                     const double shared_reference,const double planned_entry,const TLCoreLeg &leg,double &stop)
{
   if((side!=1 && side!=-1) || !leg.open || (single && !single_anchor_known)) return false;
   double anchor=single?(actual_anchor?leg.fill:planned_entry):shared_reference;
   stop=TLBreakEven(side,anchor); return true;
}
bool TLCoreTickOrder(const long last_index,const long last_msc,const long index,const long msc)
{ return index==last_index+1 && msc>=last_msc; }
bool TLCoreBeforeAvailability(const long return_msc,const long return_index,const long available_msc,const long before_tick_index)
{ return return_msc<available_msc || (return_msc==available_msc && return_index<before_tick_index); }

// Explicit UTC epochs, source and coverage. No fixed Sydney/NY hours or guessed news.
struct TLCoreSession { string id; datetime start,end,known; };
struct TLCoreNews { string name; datetime scheduled,known; };
bool TLCoreEpoch(const string s,const bool zero=false)
{
   if(s=="") return false;
   for(int i=0;i<StringLen(s);i++) if(StringGetCharacter(s,i)<48 || StringGetCharacter(s,i)>57) return false;
   long v=StringToInteger(s); return v>0 || (zero && s=="0");
}
class TLCoreCalendar
{
private:
   TLCoreSession days[];
   TLCoreNews events[];
   datetime coverage_start,coverage_end;
   bool ready;
public:
   string source;
   string error;
   TLCoreCalendar() { ready=false; }
   bool Load(const string path)
   {
      ready=false; source=""; error="CALENDAR_MISSING_OR_MALFORMED"; ArrayResize(days,0); ArrayResize(events,0);
      if(path=="") return false;
      int f=FileOpen(path,FILE_READ|FILE_TXT|FILE_ANSI,0,CP_UTF8); if(f==INVALID_HANDLE) return false;
      string fields[],line=FileReadString(f);
      if(StringLen(line)>0 && StringGetCharacter(line,0)==65279) line=StringSubstr(line,1);
      if(StringSplit(line,'|',fields)!=4 || fields[0]!="SYDNEY_NY_NEWS" || fields[1]=="" ||
         !TLCoreEpoch(fields[2]) || !TLCoreEpoch(fields[3])) { FileClose(f); return false; }
      source=fields[1]; coverage_start=(datetime)StringToInteger(fields[2]); coverage_end=(datetime)StringToInteger(fields[3]);
      if(coverage_end<=coverage_start) { FileClose(f); return false; }
      while(!FileIsEnding(f))
      {
         line=FileReadString(f); if(line=="") continue;
         if(StringSplit(line,'|',fields)!=5 || !TLCoreEpoch(fields[2]) || !TLCoreEpoch(fields[3],true) ||
            !TLCoreEpoch(fields[4])) { FileClose(f); return false; }
         string kind=fields[0],id=fields[1]; datetime start=(datetime)StringToInteger(fields[2]);
         datetime end=(datetime)StringToInteger(fields[3]),known=(datetime)StringToInteger(fields[4]);
         if(kind=="DAY")
         {
            int n=ArraySize(days);
            if(id=="" || start<coverage_start || end>coverage_end || start>=end || known<=0 ||
               (n>0 && start<days[n-1].end)) { FileClose(f); return false; }
            for(int i=0;i<n;i++) if(days[i].id==id) { FileClose(f); return false; }
            ArrayResize(days,n+1); days[n].id=id; days[n].start=start; days[n].end=end; days[n].known=known;
         }
         else if(kind=="NEWS" && end==0 && (id=="CPI" || id=="NFP" || id=="FOMC") && start>=coverage_start && start<=coverage_end && known>0)
         {
            int n=ArraySize(events);
            for(int i=0;i<n;i++) if(events[i].name==id && events[i].scheduled==start) { FileClose(f); return false; }
            ArrayResize(events,n+1); events[n].name=id; events[n].scheduled=start; events[n].known=known;
         }
         else { FileClose(f); return false; }
      }
      FileClose(f); ready=ArraySize(days)>0; if(ready) error=""; return ready;
   }
   bool Day(const datetime now,string &id)
   {
      id=""; if(!ready || now<coverage_start || now>coverage_end) return false;
      for(int i=0;i<ArraySize(days);i++) if(now>=days[i].start && now<days[i].end && days[i].known<=now) { id=days[i].id; return true; }
      return false;
   }
   bool News(const datetime now,bool &blocked)
   {
      blocked=false; if(!ready || now<coverage_start || now>coverage_end) return false;
      for(int i=0;i<ArraySize(events);i++)
         if(TLDemoNewsEntryBlocked(now,events[i].scheduled))
         { if(events[i].known>now) return false; blocked=true; }
      return true;
   }
   bool CloseNews(TLDemoGateway &gateway,const datetime now,const int lead)
   {
      bool blocked; if(!News(now,blocked)) return gateway.GuardNews("",0,0,false,lead);
      for(int i=0;i<ArraySize(events);i++)
         if(events[i].known<=now && !gateway.GuardNews(events[i].name,events[i].scheduled,events[i].known,true,lead)) return false;
      return true;
   }
   datetime EntryUntil(const datetime now)
   {
      string id; bool blocked;
      if(!Day(now,id) || !News(now,blocked) || blocked) return 0;
      datetime limit=coverage_end;
      for(int i=0;i<ArraySize(days);i++) if(days[i].id==id) limit=(datetime)MathMin(limit,days[i].end);
      for(int i=0;i<ArraySize(events);i++) if(events[i].scheduled>now)
         limit=(datetime)MathMin(limit,events[i].scheduled-900);
      return limit;
   }
   string Status(const datetime now)
   {
      string id; bool blocked;
      if(!ready) return error;
      if(!Day(now,id)) return "SESSION_OR_COVERAGE_UNAVAILABLE";
      if(!News(now,blocked)) return "NEWS_COVERAGE_UNAVAILABLE";
      return (blocked?"NEWS_RESTRICTED":"CALENDAR_OK")+" | "+source+" | day "+id+
             " | coverage ends "+TimeToString(coverage_end,TIME_DATE|TIME_SECONDS)+" UTC";
   }
};

struct TLCoreTrade
{
   string setup,id1,id2;
   int side;
   bool single,be_known,be_actual,be_sent,tp1_closed;
   double reference,planned,shared_stop;
   TLCoreLeg legs[2];
};
bool TLCoreCompatiblePair(const TLCoreTrade &a,const TLCoreTrade &b)
{
   if(a.setup!=b.setup || a.single || b.single || a.side!=b.side || a.planned==b.planned ||
      a.reference!=b.reference || a.shared_stop!=b.shared_stop || a.be_known!=b.be_known ||
      a.be_actual!=b.be_actual) return false;
   double levels[2]; levels[0]=a.planned-a.side*5*TL_PIP; levels[1]=b.planned-b.side*5*TL_PIP;
   TLPlan p; string todo;
   return TLCoreLevelPlan(a.side,levels,p,todo) && p.count==2 &&
          MathAbs(p.reference-a.reference)<1e-8 && MathAbs(p.stop-a.shared_stop)<1e-8;
}

// Locked native lifecycle connects only reviewed, guard-complete requests. No new send site.
class TLCoreTradeBook
{
private:
   TLDemoGateway gateway;
   TLCoreTrade trades[];
   TLCoreCalendar calendar;
   TLDailyGuard daily;
   string day_key,symbol,calendar_file;
   int offset,news_lead;
   bool ready,halted;
   bool restoring;
   int plan_file;
   ulong magic;
   bool ReconcileDeals()
   {
      if(!ready || !HistorySelect(0,TimeCurrent())) return false;
      ulong tickets[]; int total=HistoryDealsTotal(); ArrayResize(tickets,total);
      // Deal callbacks may arrive out of order. Snapshot authoritative history before
      // HistoryDealSelect changes the selection; process entries/exits in history order.
      for(int i=0;i<total;i++) tickets[i]=HistoryDealGetTicket(i);
      restoring=true;
      for(int i=0;i<total;i++) if(tickets[i]>0) ObserveDeal(tickets[i]);
      restoring=false; return true;
   }
   bool MoveBE(const int i)
   {
      if(!trades[i].tp1_closed || !trades[i].legs[1].open || trades[i].be_sent) return true;
      double stop; ulong ticket=0;
      for(int p=0;p<PositionsTotal();p++)
      {
         ulong candidate=PositionGetTicket(p);
         if(candidate>0 && (ulong)PositionGetInteger(POSITION_IDENTIFIER)==trades[i].legs[1].position &&
            (ulong)PositionGetInteger(POSITION_MAGIC)==magic && PositionGetString(POSITION_SYMBOL)==symbol) ticket=candidate;
      }
      if(ticket==0 || !TLCoreBreakEven(trades[i].side,trades[i].single,trades[i].be_known,trades[i].be_actual,
                         trades[i].reference,trades[i].planned,trades[i].legs[1],stop) ||
         !gateway.MoveBreakEven(trades[i].id2,ticket,stop,trades[i].legs[1].target)) return false;
      trades[i].be_sent=true; return true;
   }
public:
   TLCoreTradeBook() { ready=false; halted=false; restoring=false; plan_file=INVALID_HANDLE; news_lead=0; offset=INT_MAX; magic=0; daily.Reset(); }
   ~TLCoreTradeBook() { if(plan_file!=INVALID_HANDLE) FileClose(plan_file); }
   bool Configure(const string name,const ulong owner_magic,const int server_offset,const string calendar_path,const int closure_lead,const bool request_execution=false)
   {
      symbol=name; magic=owner_magic; offset=server_offset; news_lead=closure_lead;
      calendar_file=calendar_path; calendar.Load(calendar_file);
      if(MQLInfoInteger(MQL_TESTER) || owner_magic==0 || server_offset==INT_MAX || !TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE))) return false;
      // Both explicit operator opt-in and the existing compiled review lock are required.
      string server=AccountInfoString(ACCOUNT_SERVER);
      for(int c=0;c<StringLen(server);c++) { ushort v=StringGetCharacter(server,c); if(!((v>=48&&v<=57)||(v>=65&&v<=90)||(v>=97&&v<=122))) StringSetCharacter(server,c,'_'); }
      string scope=(string)AccountInfoInteger(ACCOUNT_LOGIN)+":"+AccountInfoString(ACCOUNT_SERVER)+":"+name+":"+(string)owner_magic;
      plan_file=FileOpen("TraderLab-core-plans-"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+"-"+server+".csv",
                         FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,'|',CP_UTF8);
      if(plan_file==INVALID_HANDLE) return false;
      if(FileSize(plan_file)==0)
      { ResetLastError(); uint n=FileWrite(plan_file,"SCOPE",scope); FileFlush(plan_file); if(n==0 || GetLastError()!=0) return false; }
      else
      {
         if(FileReadString(plan_file)!="SCOPE" || FileReadString(plan_file)!=scope) return false;
         while(!FileIsEnding(plan_file))
         {
            string kind=FileReadString(plan_file); if(kind=="" && FileIsEnding(plan_file)) break;
            TLCoreTrade t; ZeroMemory(t); t.setup=FileReadString(plan_file); t.id1=FileReadString(plan_file); t.id2=FileReadString(plan_file);
            t.side=(int)StringToInteger(FileReadString(plan_file)); t.single=StringToInteger(FileReadString(plan_file))!=0;
            t.be_known=StringToInteger(FileReadString(plan_file))!=0; t.be_actual=StringToInteger(FileReadString(plan_file))!=0;
            t.reference=StringToDouble(FileReadString(plan_file)); t.planned=StringToDouble(FileReadString(plan_file));
            t.shared_stop=StringToDouble(FileReadString(plan_file));
            if(kind!="PLAN" || t.setup=="" || !TLDemoId(t.id1) || !TLDemoId(t.id2) || t.id1==t.id2 ||
               (t.side!=1 && t.side!=-1) || t.reference<=0 || t.planned<=0 || t.shared_stop<0 ||
               !MathIsValidNumber(t.reference) || !MathIsValidNumber(t.planned) || !MathIsValidNumber(t.shared_stop)) return false;
            int same_group=0;
            for(int i=0;i<ArraySize(trades);i++)
            {
               if(trades[i].id1==t.id1 || trades[i].id2==t.id2 || trades[i].id1==t.id2 || trades[i].id2==t.id1) return false;
               if(trades[i].setup==t.setup && (!TLCoreCompatiblePair(trades[i],t) || ++same_group>1)) return false;
            }
            int n=ArraySize(trades); ArrayResize(trades,n+1); trades[n]=t;
         }
      }
      FileSeek(plan_file,0,SEEK_END);
      ready=gateway.Start(request_execution && TL_DEMO_DISPATCH_REVIEWED,name,owner_magic,"TraderLab-demo-"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+"-"+server+".csv",server_offset);
      calendar.Day(TimeGMT(),day_key);
      if(ready && HistorySelect(0,TimeCurrent()))
      {
         ulong tickets[]; int total=HistoryDealsTotal(); ArrayResize(tickets,total);
         for(int i=0;i<total;i++) tickets[i]=HistoryDealGetTicket(i);
         restoring=true;
         for(int i=0;i<total;i++) if(tickets[i]>0) ObserveDeal(tickets[i]);
         restoring=false;
      }
      else halted=true;
      // Restored leg evidence must match authoritative open position identifiers.
      for(int p=0;p<PositionsTotal();p++) if(PositionGetTicket(p)>0 && (ulong)PositionGetInteger(POSITION_MAGIC)==magic)
      {
         bool linked=false; ulong id=(ulong)PositionGetInteger(POSITION_IDENTIFIER);
         for(int i=0;i<ArraySize(trades);i++) for(int l=0;l<2;l++)
            if(trades[i].legs[l].open && trades[i].legs[l].position==id && PositionGetDouble(POSITION_VOLUME)==TL_LEG_LOTS) linked=true;
         if(!linked) halted=true;
      }
      for(int i=0;i<ArraySize(trades);i++) for(int l=0;l<2;l++) if(trades[i].legs[l].open)
      {
         bool present=false;
         for(int p=0;p<PositionsTotal();p++)
         {
            if(PositionGetTicket(p)==0 || (ulong)PositionGetInteger(POSITION_MAGIC)!=magic ||
               (ulong)PositionGetInteger(POSITION_IDENTIFIER)!=trades[i].legs[l].position ||
               PositionGetString(POSITION_SYMBOL)!=symbol) continue;
            double actual_stop=PositionGetDouble(POSITION_SL),be_stop;
            bool is_be=l==1 && trades[i].tp1_closed &&
               TLCoreBreakEven(trades[i].side,trades[i].single,trades[i].be_known,trades[i].be_actual,
                               trades[i].reference,trades[i].planned,trades[i].legs[l],be_stop) &&
               MathAbs(actual_stop-be_stop)<1e-8;
            present=PositionGetDouble(POSITION_VOLUME)==TL_LEG_LOTS &&
                    MathAbs(PositionGetDouble(POSITION_TP)-trades[i].legs[l].target)<1e-8 &&
                    (MathAbs(actual_stop-trades[i].legs[l].stop)<1e-8 || is_be);
            if(is_be) trades[i].be_sent=true;
         }
         if(!present) halted=true; // Absence is never invented liquidation.
      }
      return ready && !halted;
   }
   bool Begin(const TLCoreTrade &trade,const TLCoreGuards &guards,const int fill,const bool exact,const MqlTick &observed,
              const double fvg_low,const double fvg_high)
   {
      if(TLCoreEntryBlock(guards,fill,trade.single,exact)!="" || !ready || halted) return false;
      // This milestone never enables the gateway, even if an injected/reviewed
      // package is supplied. No successful submission or position is fabricated.
      if(!gateway.CanDispatch()) return false;
      string current_day; bool news_blocked;
      datetime now=TimeGMT();
      if(!calendar.Day(now,current_day) || current_day!=day_key || !calendar.News(now,news_blocked) ||
         news_blocked || daily.halted || news_lead<=0) return false;
      if(trade.setup=="" || StringFind(trade.setup,"|")>=0 || StringFind(trade.setup,"\n")>=0 ||
         StringFind(trade.setup,"\r")>=0 || !TLDemoId(trade.id1) || !TLDemoId(trade.id2) || trade.id1==trade.id2 ||
         trade.be_sent || trade.legs[0].entry_deal>0 || trade.legs[1].entry_deal>0) return false;
      int same_group=0;
      for(int i=0;i<ArraySize(trades);i++)
      {
         if(trades[i].id1==trade.id1 || trades[i].id2==trade.id2 || trades[i].id1==trade.id2 || trades[i].id2==trade.id1) return false;
         if(trades[i].setup==trade.setup && (!TLCoreCompatiblePair(trades[i],trade) || ++same_group>1)) return false;
      }
      if(plan_file==INVALID_HANDLE) return false;
      ResetLastError();
      uint written=FileWrite(plan_file,"PLAN",trade.setup,trade.id1,trade.id2,trade.side,(int)trade.single,
                             (int)trade.be_known,(int)trade.be_actual,trade.reference,trade.planned,trade.shared_stop);
      FileFlush(plan_file); // Persist approved plan BEFORE gateway's durable order intent.
      if(written==0 || GetLastError()!=0) { Emergency("CORE_PLAN_WRITE_FAILED"); return false; }
      int n=ArraySize(trades); ArrayResize(trades,n+1); trades[n]=trade;
      bool submitted=gateway.SubmitReviewedCorePair(trade.side==1,trade.single,trade.reference,trade.shared_stop,trade.planned,
                "UNFILLED",true,guards.calendar,guards.news,0,trade.id1,trade.id2,
                trade.setup+":"+DoubleToString(trade.planned,8),observed.time_msc,observed.ask,calendar.EntryUntil(now),fvg_low,fvg_high);
      if(!submitted) Emergency("CORE_PAIR_FAILED_NO_RETRY");
      else if(!ReconcileDeals()) Emergency("CORE_DEAL_HISTORY_UNAVAILABLE");
      return submitted;
   }
   void Emergency(const string reason)
   { halted=true; if(ready) { gateway.EmergencyStop(reason); gateway.CloseAllDemoPositions(reason); } }
   void Service()
   {
      calendar.Load(calendar_file); // Calendar updates do not require an EA restart.
      if(!ready || !gateway.CanManage()) return; // Algo OFF / lock: no broker requests.
      if(halted) { gateway.ObserveTradeTransaction(); gateway.CloseAllDemoPositions("core-persistent-emergency"); return; }
      datetime now=TimeGMT(); string day; bool blocked;
      if(!calendar.Day(now,day) || !calendar.News(now,blocked)) { Emergency("CORE_CALENDAR_UNAVAILABLE"); return; }
      if(day_key!=day) { daily.Reset(); day_key=day; }
      if(!calendar.CloseNews(gateway,now,news_lead)) halted=true;
      if(!gateway.ObserveTradeTransaction()) halted=true;
      if(!ReconcileDeals()) { Emergency("CORE_DEAL_HISTORY_UNAVAILABLE"); return; }
      if(!halted) for(int i=0;i<ArraySize(trades);i++)
         if(!MoveBE(i)) { Emergency("CORE_BE_FAILED_OR_UNRESOLVED"); return; }
   }
   bool ObserveDeal(const ulong ticket)
   {
      if(!ready || !HistoryDealSelect(ticket)) return false;
      if((ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC)!=magic || HistoryDealGetString(ticket,DEAL_SYMBOL)!=symbol) return false;
      string current_day;
      if(calendar.Day(TimeGMT(),current_day) && current_day!=day_key) { daily.Reset(); day_key=current_day; }
      ulong position=(ulong)HistoryDealGetInteger(ticket,DEAL_POSITION_ID);
      string comment=HistoryDealGetString(ticket,DEAL_COMMENT);
      long entry=HistoryDealGetInteger(ticket,DEAL_ENTRY),reason=HistoryDealGetInteger(ticket,DEAL_REASON);
      double volume=HistoryDealGetDouble(ticket,DEAL_VOLUME),price=HistoryDealGetDouble(ticket,DEAL_PRICE);
      double net=HistoryDealGetDouble(ticket,DEAL_PROFIT)+HistoryDealGetDouble(ticket,DEAL_COMMISSION)+
                 HistoryDealGetDouble(ticket,DEAL_SWAP)+HistoryDealGetDouble(ticket,DEAL_FEE);
      for(int i=0;i<ArraySize(trades);i++) for(int leg=0;leg<2;leg++)
      {
         string id=leg==0?trades[i].id1:trades[i].id2;
         if(entry==DEAL_ENTRY_IN && comment=="TL:"+id)
         {
            if(!TLCoreFill(trades[i].legs[leg],trades[i].side,trades[i].single,trades[i].shared_stop,
                          trades[i].reference+trades[i].side*(leg==0?6.0:10.0),ticket,position,volume,price,net)) Emergency("CORE_PARTIAL_OR_CONFLICTING_FILL");
            return !halted;
         }
         if(entry==DEAL_ENTRY_OUT && trades[i].legs[leg].position==position)
         {
            if(trades[i].legs[leg].exit_deal>0)
            {
               if(TLCoreExit(trades[i].legs[leg],ticket,position,volume,net)) return true;
               Emergency("CORE_CONFLICTING_DUPLICATE_EXIT"); return false;
            }
            if(!TLCoreExit(trades[i].legs[leg],ticket,position,volume,net)) { Emergency("CORE_PARTIAL_OR_CONFLICTING_EXIT"); return false; }
            // Exact broker reasons, never guess TP/SL from a quote.
            bool stopped=reason==DEAL_REASON_SL;
            bool unknown_be_stop=stopped && leg==1 && (trades[i].be_sent || trades[i].tp1_closed);
            string exit_day;
            datetime closed_utc=(datetime)(HistoryDealGetInteger(ticket,DEAL_TIME)-offset);
            if(calendar.Day(closed_utc,exit_day) && exit_day==day_key)
               daily.Close(trades[i].setup,trades[i].legs[leg].net,stopped && !unknown_be_stop);
            // Actual closed NET profit must be recorded even while the stop-count policy blocks entries.
            if(unknown_be_stop) { Emergency("CORE_BE_STOP_COUNT_UNRESOLVED"); return false; }
            if(leg==0 && reason==DEAL_REASON_TP) trades[i].tp1_closed=true;
            if(!restoring && !MoveBE(i)) { Emergency("CORE_BE_FAILED_OR_UNRESOLVED"); return false; }
            return true;
         }
      }
      Emergency("CORE_UNRESTORED_DEAL_PLAN"); return false;
   }
   bool Ready() { return ready && !halted && !daily.halted; }
   void Guards(TLCoreGuards &g)
   {
      string day; bool blocked=false; datetime now=TimeGMT();
      g.calendar=calendar.Day(now,day) && day==day_key;
      g.news=calendar.News(now,blocked) && !blocked && news_lead>0;
      g.daily=!daily.halted; g.restart=g.restart && ready && !halted;
   }
   string ExecutionBlock()
   { return !gateway.ExecutionLimitsReady()?"EXPLICIT_PAIR_TIME_SPREAD_SLIPPAGE_LIMITS_REQUIRED":gateway.CanDispatch()?"":"DEMO_DISPATCH_DISABLED_OR_UNREVIEWED"; }
   bool DispatchReady() { return gateway.CanDispatch(); }
   void ExecutionLimits(const int ms,const double spread,const int slippage) { gateway.ExecutionLimits(ms,spread,slippage); }
   void DealsChanged()
   { if(ready && !ReconcileDeals()) Emergency("CORE_DEAL_HISTORY_UNAVAILABLE"); Service(); }
   string Status()
   {
      return (TL_DEMO_DISPATCH_REVIEWED?"REVIEWED":"COMPILE LOCKED")+
             string(ready?(halted?" | HALTED":" | JOURNAL OK"):" | JOURNAL/RESTART NOT READY")+
             (gateway.ExecutionLimitsReady()?" | PAIR LIMITS OK":" | PAIR LIMITS UNSET")+
             " | "+calendar.Status(TimeGMT());
   }
};
#endif
