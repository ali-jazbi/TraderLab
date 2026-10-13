#ifndef TRADERLAB_DEMO_GATEWAY_MQH
#define TRADERLAB_DEMO_GATEWAY_MQH
// §52 preparation only. Changing this lock requires a separate reviewed milestone.
const bool TL_DEMO_DISPATCH_REVIEWED=false;

bool TLDemoAccount(const long mode) { return mode==ACCOUNT_TRADE_MODE_DEMO; }
bool TLDemoReturnQuote(const MqlTick &quote,const long first_return_msc,const double first_return_bid,const double first_return_ask)
{
   return first_return_msc>0 && quote.time_msc==first_return_msc &&
          quote.bid==first_return_bid && quote.ask==first_return_ask;
}
// Broker execution budget, not an alternate signal or permission to retry a return.
bool TLDemoPairQuote(const MqlTick &q,const long signal_msc,const double signal_bid,const double signal_ask,
                     const bool buy,const ulong elapsed,const int max_ms,const double max_spread,
                     const int max_slippage_points,const double point)
{
   return signal_msc>0 && signal_bid>0 && signal_ask>=signal_bid &&
          max_ms>0 && max_spread>0 && max_slippage_points>=0 && point>0 &&
          elapsed<=(ulong)max_ms && q.time_msc>=signal_msc && q.bid>0 && q.ask>=q.bid &&
          q.ask-q.bid<=max_spread+1e-8 &&
          MathAbs((buy?q.ask:q.bid)-(buy?signal_ask:signal_bid))<=max_slippage_points*point+1e-8;
}
bool TLDemoUnfilledHistory(const MqlTick &ticks[],const bool buy,const double low,const double high)
{
   if(ArraySize(ticks)==0 || low<=0 || high<=low) return false;
   long previous=0;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      if(ticks[i].time_msc<=0 || ticks[i].time_msc<previous || ticks[i].bid<=0 || (buy?ticks[i].bid<high:ticks[i].bid>low)) return false;
      previous=ticks[i].time_msc;
   }
   return true;
}
bool TLDemoVolume(const double value,const double low,const double high,const double step)
{
   return step>0 && low>0 && high>=low && value>=low && value<=high &&
          MathAbs((value-low)/step-MathRound((value-low)/step))<1e-8;
}
bool TLDemoGrid(const double value,const double step)
{ return step>0 && MathIsValidNumber(value) && MathAbs(value/step-MathRound(value/step))<1e-7; }
bool TLDemoNewsEntryBlocked(const datetime now,const datetime event_utc)
{ return event_utc>0 && now>=event_utc-900 && now<=event_utc+900; }
// OrderCheck's documented successful retcode is 0; it is not an OrderSend fill.
bool TLDemoCheckPassed(const bool called,const uint retcode)
{ return called && (retcode==0 || retcode==TRADE_RETCODE_DONE); }
string TLDemoResponseState(const bool sent,const uint retcode,const ulong order,const ulong deal)
{
   if(order==0 && deal==0 && (retcode==TRADE_RETCODE_REJECT || retcode==TRADE_RETCODE_INVALID ||
      retcode==TRADE_RETCODE_NO_MONEY || retcode==TRADE_RETCODE_INVALID_VOLUME || retcode==TRADE_RETCODE_INVALID_STOPS)) return "REJECTED";
   return sent && (retcode==TRADE_RETCODE_DONE || retcode==TRADE_RETCODE_PLACED)?"ACK":"UNKNOWN";
}
bool TLDemoNewsCloseDue(const datetime now,const datetime event_utc,const int lead,const bool carried,const bool has_positions)
{
   if(event_utc<=0 || lead<=0 || !has_positions || now<event_utc-180-lead) return false;
   // Also close a position opened late inside the restriction window; do not excuse the breach.
   return carried || now<=event_utc+900;
}
bool TLDemoId(const string id)
{
   if(StringLen(id)<1 || StringLen(id)>20) return false;
   for(int i=0;i<StringLen(id);i++)
   { ushort c=StringGetCharacter(id,i); if(!((c>=48 && c<=57)||(c>=65 && c<=90)||(c>=97 && c<=122))) return false; }
   return true;
}
struct TLDemoIntent
{
   string id,opportunity,symbol,state;
   double volume,sl,tp;
   bool buy,single;
   datetime claimed;
};

class TLDemoGateway
{
private:
   int file;
   bool enabled,halted,reconciled,pair_in_progress;
   long login;
   int broker_offset;
   string server,symbol;
   ulong magic;
   TLDemoIntent intents[];
   string last_error;
   MqlTradeRequest vetted;
   bool vetted_ready,vetted_single; int vetted_leg;
   double vetted_bid,vetted_ask; long vetted_msc;
   int pair_max_ms,slippage_points;
   double spread_limit,pair_signal_bid,pair_signal_ask;
   long pair_signal_msc;
   ulong pair_started;
   datetime pair_guard_until;
   double pair_fvg_low,pair_fvg_high;
   bool pair_first_filled;
   bool Fail(const string reason) { last_error=reason; Print("TraderLab DEMO gate: ",reason); return false; }
   bool Account()
   {
      return !MQLInfoInteger(MQL_TESTER) && TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE)) &&
             AccountInfoInteger(ACCOUNT_LOGIN)==login && AccountInfoString(ACCOUNT_SERVER)==server;
   }
   bool Permissions()
   {
      return Account() && TerminalInfoInteger(TERMINAL_CONNECTED) && TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) &&
             MQLInfoInteger(MQL_TRADE_ALLOWED) && AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) && AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
   }
   int Find(const string id)
   { for(int i=0;i<ArraySize(intents);i++) if(intents[i].id==id) return i; return -1; }
   bool Save(const TLDemoIntent &v)
   {
      if(file==INVALID_HANDLE || !Account()) return Fail("LEDGER_UNAVAILABLE_OR_ACCOUNT_CHANGED");
      ResetLastError();
      uint written=FileWrite(file,v.id,v.opportunity,v.symbol,v.state,v.volume,v.sl,v.tp,(int)v.buy,(int)v.single,(long)v.claimed);
      FileFlush(file);
      if(written==0 || GetLastError()!=0) { halted=true; return Fail("LEDGER_WRITE_FAILED_NO_DISPATCH"); }
      return true;
   }
   bool Claim(TLDemoIntent &v)
   {
      if(Find(v.id)>=0) return Fail("DUPLICATE_INTENT_NO_RETRY");
      int short_count=0,long_count=0; datetime now=TimeGMT();
      for(int i=0;i<ArraySize(intents);i++)
      {
         if(intents[i].opportunity==v.opportunity) return Fail("DUPLICATE_OPPORTUNITY_NO_RETRY");
         if(intents[i].claimed>now) return Fail("LEDGER_CLOCK_REGRESSION");
         if(StringFind(intents[i].opportunity,"ANCHOR:")==0) continue;
         if(now-intents[i].claimed<=300) short_count++;
         if(now-intents[i].claimed<=3600) long_count++;
      }
      if(short_count>=1000 || long_count>=10000) return Fail("DURABLE_REQUEST_RATE_BLOCKED");
      v.claimed=now; v.state="INTENT";
      if(!Save(v)) return false;
      int n=ArraySize(intents); ArrayResize(intents,n+1); intents[n]=v;
      return true;
   }
   bool Dispatch(MqlTradeRequest &request,TLDemoIntent &intent)
   {
      // ONLY send site. The Core integration cannot unlock dispatch.
      if(!enabled || !TL_DEMO_DISPATCH_REVIEWED) return Fail("DISABLED_OR_UNREVIEWED");
      if(!Permissions() || (!reconciled && request.position==0)) return Fail("ACCOUNT_OR_RECONCILIATION_GUARD");
      if(request.action==TRADE_ACTION_DEAL && request.position==0 && halted) return Fail("PERSISTENT_EMERGENCY_STOP");
      MqlTradeCheckResult check={};
      bool checked=OrderCheck(request,check);
      if(!TLDemoCheckPassed(checked,check.retcode)) return Fail("ORDER_CHECK_REJECTED:"+(string)check.retcode);
      if(!Claim(intent)) return false; // flush intent before network boundary
      MqlTradeResult result={}; ResetLastError();
      bool sent=OrderSend(request,result);
      // Even true/DONE is not a position. Never automatically retry an unknown/rejected intent.
      intent.state=TLDemoResponseState(sent,result.retcode,result.order,result.deal);
      if(result.retcode==TRADE_RETCODE_DONE_PARTIAL) { intent.state="UNKNOWN"; EmergencyStop("PARTIAL_FILL"); }
      // No-execution rejection only when result has no order/deal and a definitive rejection code.
      if(!Save(intent)) return false; intents[Find(intent.id)]=intent; reconciled=false;
      Print("TraderLab DEMO response ",intent.id," retcode=",result.retcode," order=",result.order," deal=",result.deal," state=",intent.state);
      if(intent.state=="REJECTED") return Fail("DEFINITIVE_ORDER_REJECTION_NO_RETRY");
      return Reconcile();
   }
   bool Quote(const string name,MqlTick &tick)
   { return SymbolInfoTick(name,tick) && tick.bid>0 && tick.ask>=tick.bid && tick.time>0; }
   bool PairHistory(const MqlTick &quote,const bool buy)
   {
      // Read-only guard between network legs: callback quotes cannot hide an intervening FVG fill.
      // TickCapture still owns emission and ordered-prefix validation; no cursor advances here.
      MqlTick ticks[]; ResetLastError();
      int n=CopyTicksRange(symbol,ticks,COPY_TICKS_ALL,(ulong)pair_signal_msc,(ulong)quote.time_msc);
      if(n<=0 || n!=ArraySize(ticks) || GetLastError()!=0 ||
         ticks[0].time_msc!=pair_signal_msc || ticks[n-1].time_msc!=quote.time_msc ||
         !TLDemoUnfilledHistory(ticks,buy,pair_fvg_low,pair_fvg_high))
         return Fail("PAIR_HISTORY_LAG_ERROR_OR_FVG_FILL");
      // No SymbolInfoTick raw-payload identity requirement.
      return true;
   }
public:
   TLDemoGateway() { file=INVALID_HANDLE; vetted_ready=false; enabled=false; pair_in_progress=false; pair_first_filled=false;
                    halted=false; reconciled=false; login=0; magic=0; broker_offset=INT_MAX;
                    pair_max_ms=0; spread_limit=0; slippage_points=-1; pair_guard_until=0; }
   ~TLDemoGateway() { if(file!=INVALID_HANDLE) FileClose(file); }
   string Error() { return last_error; }
   bool CanDispatch() { return enabled && TL_DEMO_DISPATCH_REVIEWED && !halted && reconciled && Permissions(); }
   bool CanManage() { return enabled && TL_DEMO_DISPATCH_REVIEWED && Permissions(); }
   bool ExecutionLimitsReady() { return pair_max_ms>0 && spread_limit>0 && slippage_points>=0 && MathIsValidNumber(spread_limit); }
   void ExecutionLimits(const int max_ms,const double max_spread,const int max_slippage)
   { pair_max_ms=max_ms; spread_limit=max_spread; slippage_points=max_slippage; }
   bool Start(const bool enable,const string name,const ulong owner_magic,const string journal,const int server_utc_offset_seconds=INT_MAX)
   {
      if(file!=INVALID_HANDLE) return Fail("ALREADY_INITIALIZED");
      enabled=enable; symbol=name; magic=owner_magic; broker_offset=server_utc_offset_seconds;
      login=AccountInfoInteger(ACCOUNT_LOGIN); server=AccountInfoString(ACCOUNT_SERVER);
      if(!TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE)) || login<=0 || server=="" || magic==0) return Fail("DEMO_IDENTITY_REQUIRED");
      // Exclusive handle: another process/EA cannot use the same journal concurrently.
      string safe_server=server;
      for(int c=0;c<StringLen(safe_server);c++)
      { ushort value=StringGetCharacter(safe_server,c); if(!((value>=48 && value<=57)||(value>=65 && value<=90)||(value>=97 && value<=122))) StringSetCharacter(safe_server,c,'_'); }
      string canonical="TraderLab-demo-"+(string)login+"-"+safe_server+".csv";
      if(journal!=canonical) return Fail("CANONICAL_ACCOUNT_LEDGER_REQUIRED:"+canonical);
      file=FileOpen(journal,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,'|',CP_UTF8);
      if(file==INVALID_HANDLE) return Fail("LEDGER_LOCK_OR_OPEN_FAILED");
      if(FileSize(file)==0)
      { FileWrite(file,"SCOPE",login,server,symbol,magic); FileFlush(file); }
      else
      {
         string tag=FileReadString(file); long stored_login=(long)StringToInteger(FileReadString(file));
         string stored_server=FileReadString(file),stored_symbol=FileReadString(file); ulong stored_magic=(ulong)StringToInteger(FileReadString(file));
         if(tag!="SCOPE" || stored_login!=login || stored_server!=server || stored_symbol!=symbol || stored_magic!=magic) return Fail("LEDGER_SCOPE_MISMATCH");
         while(!FileIsEnding(file))
         {
            TLDemoIntent v; v.id=FileReadString(file); if(v.id=="" && FileIsEnding(file)) break;
            v.opportunity=FileReadString(file); v.symbol=FileReadString(file); v.state=FileReadString(file);
            v.volume=StringToDouble(FileReadString(file)); v.sl=StringToDouble(FileReadString(file)); v.tp=StringToDouble(FileReadString(file));
            v.buy=StringToInteger(FileReadString(file))!=0; v.single=StringToInteger(FileReadString(file))!=0; v.claimed=(datetime)StringToInteger(FileReadString(file));
            if(v.id=="EMERGENCY") { halted=true; continue; }
            if(!TLDemoId(v.id) || v.opportunity=="" || v.symbol=="" || v.claimed<=0 ||
               !MathIsValidNumber(v.volume) || (v.volume<=0 && StringFind(v.opportunity,"MOD:")!=0 && StringFind(v.opportunity,"ANCHOR:")!=0) || !MathIsValidNumber(v.sl) || !MathIsValidNumber(v.tp) ||
               (v.state!="INTENT" && v.state!="ACK" && v.state!="UNKNOWN" && v.state!="REJECTED" && v.state!="RECONCILED"))
               return Fail("CORRUPT_LEDGER_FAIL_CLOSED");
            int n=Find(v.id);
            if(n>=0 && (intents[n].opportunity!=v.opportunity || intents[n].symbol!=v.symbol || intents[n].volume!=v.volume ||
               intents[n].sl!=v.sl || intents[n].tp!=v.tp || intents[n].buy!=v.buy || intents[n].single!=v.single))
               return Fail("LEDGER_INTENT_PAYLOAD_CONFLICT");
            if(n<0) { n=ArraySize(intents); ArrayResize(intents,n+1); } intents[n]=v;
         }
      }
      FileSeek(file,0,SEEK_END);
      return Reconcile();
   }
   bool Reconcile()
   {
      reconciled=false;
      if(file==INVALID_HANDLE || !Account() || !HistorySelect(0,TimeCurrent())) return Fail("BROKER_HISTORY_UNAVAILABLE");
      // Unlinked owned positions/orders are never ignored after restart.
      for(int i=0;i<PositionsTotal();i++)
      {
         if(PositionGetTicket(i)==0) return Fail("POSITION_SNAPSHOT_FAILED");
         if((ulong)PositionGetInteger(POSITION_MAGIC)!=magic) continue;
         string comment=PositionGetString(POSITION_COMMENT);
         int n=Find(StringSubstr(comment,3));
         if(StringFind(comment,"TL:")!=0 || n<0 || PositionGetString(POSITION_SYMBOL)!=intents[n].symbol) return Fail("UNLINKED_POSITION");
         if(PositionGetDouble(POSITION_VOLUME)!=intents[n].volume) { EmergencyStop("PARTIAL_OR_MIXED_FILL"); return Fail("UNSUPPORTED_FILL_VOLUME"); }
      }
      for(int i=0;i<OrdersTotal();i++)
      {
         if(OrderGetTicket(i)==0) return Fail("ORDER_SNAPSHOT_FAILED");
         if((ulong)OrderGetInteger(ORDER_MAGIC)!=magic) continue;
         string comment=OrderGetString(ORDER_COMMENT);
         if(StringFind(comment,"TL:")!=0 || Find(StringSubstr(comment,3))<0) return Fail("UNLINKED_ORDER");
      }
      for(int i=0;i<ArraySize(intents);i++)
      {
         if(intents[i].state=="REJECTED" || intents[i].state=="RECONCILED") continue;
         bool found=false;
         if(StringFind(intents[i].opportunity,"MOD:")==0)
         {
            string parts[];
            if(StringSplit(intents[i].opportunity,':',parts)!=3) return Fail("CORRUPT_MODIFICATION_ID");
            ulong position=(ulong)StringToInteger(parts[1]);
            if(PositionSelectByTicket(position) && MathAbs(PositionGetDouble(POSITION_SL)-intents[i].sl)<1e-8 &&
               MathAbs(PositionGetDouble(POSITION_TP)-intents[i].tp)<1e-8) found=true;
            if(!found) return Fail("MODIFICATION_NOT_RECONCILED");
         }
         double executed_volume=0;
         for(int d=0;d<HistoryDealsTotal();d++)
         {
            ulong ticket=HistoryDealGetTicket(d); if(ticket==0) return Fail("DEAL_HISTORY_READ_FAILED");
            if((ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC)==magic && HistoryDealGetString(ticket,DEAL_COMMENT)=="TL:"+intents[i].id)
            { found=true; executed_volume+=HistoryDealGetDouble(ticket,DEAL_VOLUME); }
         }
         if(!found) return Fail("UNKNOWN_DISPATCH_NO_AUTOMATIC_RETRY");
         if(StringFind(intents[i].opportunity,"MOD:")!=0 && MathAbs(executed_volume-intents[i].volume)>1e-8)
         { EmergencyStop("INCOMPLETE_DEAL_VOLUME"); return Fail("DEAL_VOLUME_NOT_RECONCILED"); }
         intents[i].state="RECONCILED"; if(!Save(intents[i])) return false;
      }
      if(!pair_in_progress)
      {
         for(int i=0;i<ArraySize(intents);i++)
         {
            string op=intents[i].opportunity; int len=StringLen(op);
            if(len<5 || (StringSubstr(op,len-5)!=":leg1" && StringSubstr(op,len-5)!=":leg2")) continue;
            if(intents[i].state=="REJECTED") continue;
            string partner=StringSubstr(op,0,len-1)+(StringSubstr(op,len-1)=="1"?"2":"1"); bool found=false;
            for(int j=0;j<ArraySize(intents);j++) if(intents[j].opportunity==partner && intents[j].state=="RECONCILED") found=true;
            if(!found) { EmergencyStop("INCOMPLETE_CANONICAL_PAIR_ON_RESTART"); return Fail("INCOMPLETE_PAIR_REQUIRES_OPERATOR"); }
         }
      }
      reconciled=true; return true;
   }
   void EmergencyStop(const string reason)
   {
      halted=true;
      TLDemoIntent v; v.id="EMERGENCY"; v.opportunity=reason; v.symbol=symbol; v.state="HALT";
      v.volume=0; v.sl=0; v.tp=0; v.buy=false; v.single=false; v.claimed=TimeGMT(); Save(v);
   }
   bool PrepareCore(const bool buy,const bool single,const double reference,const double shared_stop,const double entry_touch_reference,
                    const int leg,const string fvg_fill_state,const bool strategy_guards_passed,const bool session_calendar_valid,
                    const bool news_calendar_valid,const datetime news_deadline,MqlTradeRequest &request,
                    const long first_return_msc=0,const double first_return_ask=0)
   {
      vetted_ready=false;
      if(broker_offset==INT_MAX || MathAbs(broker_offset)>14*3600) return Fail("EXPLICIT_BROKER_UTC_OFFSET_REQUIRED");
      if(!Permissions() || !reconciled || halted) return Fail("ACCOUNT_RECONCILIATION_OR_EMERGENCY_GUARD");
      if(fvg_fill_state!="UNFILLED") return Fail("PARTIAL_OR_FULL_FVG_UNSUPPORTED");
      if(!strategy_guards_passed || !session_calendar_valid || !news_calendar_valid) return Fail("STRATEGY_SESSION_NEWS_UNAPPROVED");
      // Caller must prove UNFILLED eligibility, first observed touch and consumed history.
      if(news_deadline>0 && TLDemoNewsEntryBlocked(TimeGMT(),news_deadline+180)) return Fail("NEWS_RESTRICTION");
      if(AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING || AccountInfoString(ACCOUNT_CURRENCY)!="USD") return Fail("ONLY_USD_HEDGING_SUPPORTED");
      if(leg!=1 && leg!=2) return Fail("CANONICAL_LEG_REQUIRED");
      MqlTick tick; if(!Quote(symbol,tick)) return Fail("QUOTE_UNAVAILABLE");
      if(!pair_in_progress || !ExecutionLimitsReady() || TimeGMT()>=pair_guard_until ||
         !TLDemoPairQuote(tick,pair_signal_msc,pair_signal_bid,pair_signal_ask,buy,GetTickCount64()-pair_started,
                         pair_max_ms,spread_limit,slippage_points,SymbolInfoDouble(symbol,SYMBOL_POINT)))
         return Fail("PAIR_QUOTE_TIME_SPREAD_OR_SLIPPAGE_GUARD");
      if(leg==1 && !TLDemoReturnQuote(tick,first_return_msc,entry_touch_reference,first_return_ask))
         return Fail("FIRST_RETURN_QUOTE_CHANGED_NO_REARM");
      if(leg==2 && !pair_first_filled) return Fail("SECOND_LEG_REQUIRES_RECONCILED_FIRST");
      if(buy?tick.bid<pair_fvg_high:tick.bid>pair_fvg_low) return Fail("PAIR_FVG_NO_LONGER_UNFILLED");
      if(SymbolInfoInteger(symbol,SYMBOL_CHART_MODE)!=SYMBOL_CHART_MODE_BID || (leg==1 && tick.bid!=entry_touch_reference))
         return Fail("EXACT_BID_CHART_TOUCH_REQUIRED");
      double volume=0.01,low=SymbolInfoDouble(symbol,SYMBOL_VOLUME_MIN),high=SymbolInfoDouble(symbol,SYMBOL_VOLUME_MAX),step=SymbolInfoDouble(symbol,SYMBOL_VOLUME_STEP);
      if(!TLDemoVolume(volume,low,high,step)) return Fail("CANONICAL_VOLUME_UNREPRESENTABLE");
      double reserve=(pair_in_progress && leg==2)?0.01:0.02;
      double directional=0,limit=SymbolInfoDouble(symbol,SYMBOL_VOLUME_LIMIT);
      for(int i=0;i<PositionsTotal();i++)
      {
         if(PositionGetTicket(i)==0) return Fail("EXPOSURE_UNAVAILABLE");
         if(PositionGetString(POSITION_SYMBOL)==symbol && (PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)==buy) directional+=PositionGetDouble(POSITION_VOLUME);
      }
      for(int i=0;i<OrdersTotal();i++)
      {
         if(OrderGetTicket(i)==0) return Fail("PENDING_EXPOSURE_UNAVAILABLE");
         if(OrderGetString(ORDER_SYMBOL)!=symbol) continue;
         long type=OrderGetInteger(ORDER_TYPE);
         bool is_buy=type==ORDER_TYPE_BUY_LIMIT || type==ORDER_TYPE_BUY_STOP || type==ORDER_TYPE_BUY_STOP_LIMIT;
         if(is_buy==buy) directional+=OrderGetDouble(ORDER_VOLUME_CURRENT);
      }
      if(limit>0 && directional+reserve>limit+1e-8) return Fail("DIRECTIONAL_LIMIT");
      int sign=buy?1:-1; double price=buy?tick.ask:tick.bid;
      request.action=TRADE_ACTION_DEAL; request.symbol=symbol; request.magic=magic; request.volume=volume;
      request.type=buy?ORDER_TYPE_BUY:ORDER_TYPE_SELL; request.price=price;
      request.sl=single?price-sign*4.0:shared_stop; request.tp=reference+sign*(leg==1?6.0:10.0);
      double grid=SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_SIZE);
      if(!TLDemoGrid(request.sl,grid)||!TLDemoGrid(request.tp,grid)||!TLDemoGrid(price,grid)) return Fail("CANONICAL_PRICE_UNREPRESENTABLE");
      double min_distance=MathMax(SymbolInfoInteger(symbol,SYMBOL_TRADE_STOPS_LEVEL),SymbolInfoInteger(symbol,SYMBOL_TRADE_FREEZE_LEVEL))*SymbolInfoDouble(symbol,SYMBOL_POINT);
      double exit_quote=buy?tick.bid:tick.ask;
      if(sign*(exit_quote-request.sl)<min_distance || sign*(request.tp-exit_quote)<min_distance) return Fail("STOP_FREEZE_GEOMETRY");
      double margin=0;
      if(!OrderCalcMargin(request.type,symbol,reserve,price,margin) || margin<0 || margin>AccountInfoDouble(ACCOUNT_MARGIN_FREE)) return Fail("MARGIN_CHECK_FAILED");
      if((SymbolInfoInteger(symbol,SYMBOL_FILLING_MODE)&SYMBOL_FILLING_FOK)==0) return Fail("FOK_REQUIRED_NO_PARTIAL_POLICY");
      request.type_filling=ORDER_FILLING_FOK;
      request.deviation=(ulong)slippage_points;
      MqlTradeCheckResult check={};
      bool checked=OrderCheck(request,check);
      if(!TLDemoCheckPassed(checked,check.retcode)) return Fail("PREFLIGHT_ORDER_REJECTED:"+(string)check.retcode);
      vetted=request; vetted_single=single; vetted_leg=leg; vetted_bid=tick.bid; vetted_ask=tick.ask; vetted_msc=tick.time_msc; vetted_ready=true; return true;
   }
private:
   bool SubmitReviewedCore(MqlTradeRequest &request,const string id,const string opportunity,const bool single)
   {
      if(!vetted_ready || single!=vetted_single || request.type_filling!=vetted.type_filling || request.symbol!=vetted.symbol || request.type!=vetted.type || request.price!=vetted.price ||
         request.sl!=vetted.sl || request.tp!=vetted.tp || request.volume!=vetted.volume) return Fail("PREPARED_REQUEST_REQUIRED");
      vetted_ready=false;
      // Recheck quote: do not silently replace a stale request price.
      MqlTick latest; if(!Quote(symbol,latest) || (request.type==ORDER_TYPE_BUY?latest.ask:latest.bid)!=request.price || latest.bid!=vetted_bid || latest.ask!=vetted_ask || latest.time_msc!=vetted_msc) return Fail("QUOTE_CHANGED_NO_FILL");
      if(TimeGMT()>=pair_guard_until ||
         !TLDemoPairQuote(latest,pair_signal_msc,pair_signal_bid,pair_signal_ask,request.type==ORDER_TYPE_BUY,
                         GetTickCount64()-pair_started,pair_max_ms,spread_limit,slippage_points,SymbolInfoDouble(symbol,SYMBOL_POINT)))
         return Fail("PAIR_EXECUTION_BUDGET_EXPIRED");
      if(vetted_leg==2 && !PairHistory(latest,request.type==ORDER_TYPE_BUY)) return false;
      // The read may take time: refresh timing/quote proof before entering the sole dispatch path.
      MqlTick after_history;
      if(!Quote(symbol,after_history) || !TLDemoReturnQuote(after_history,latest.time_msc,latest.bid,latest.ask) ||
         TimeGMT()>=pair_guard_until || GetTickCount64()-pair_started>(ulong)pair_max_ms)
         return Fail("PAIR_QUOTE_CHANGED_AFTER_HISTORY_GUARD");
      if(!TLDemoId(id) || StringLen(id)>18 || opportunity=="" || request.action!=TRADE_ACTION_DEAL || request.position!=0 ||
         request.symbol!=symbol || request.magic!=magic || request.volume!=0.01 ||
         (request.type!=ORDER_TYPE_BUY && request.type!=ORDER_TYPE_SELL)) return Fail("UNSUPPORTED_CORE_REQUEST");
      // No public automatic caller, no input can unlock the compile-time review flag.
      TLDemoIntent v; v.id=id; v.opportunity=opportunity+":leg"+(string)vetted_leg; v.symbol=symbol; v.state="";
      v.volume=request.volume; v.sl=request.sl; v.tp=request.tp; v.buy=request.type==ORDER_TYPE_BUY; v.single=single; v.claimed=0;
      request.comment="TL:"+id;
      if(!Dispatch(request,v)) return false;
      // Market execution may ignore deviation. Inspect real deals, never call a requested price a fill.
      double expected=v.buy?pair_signal_ask:pair_signal_bid;
      for(int d=0;d<HistoryDealsTotal();d++)
      {
         ulong deal=HistoryDealGetTicket(d);
         if((ulong)HistoryDealGetInteger(deal,DEAL_MAGIC)!=magic || HistoryDealGetString(deal,DEAL_COMMENT)!="TL:"+id) continue;
         if(MathAbs(HistoryDealGetDouble(deal,DEAL_PRICE)-expected)>
            slippage_points*SymbolInfoDouble(symbol,SYMBOL_POINT)+1e-8) return Fail("ACTUAL_FILL_EXCEEDS_REVIEWED_SLIPPAGE");
      }
      return RepairActualFillStops();
   }
public:
   bool SubmitReviewedCorePair(const bool buy,const bool single,const double reference,const double shared_stop,
                               const double entry_touch_reference,const string fvg_fill_state,const bool strategy_guards_passed,
                               const bool session_calendar_valid,const bool news_calendar_valid,const datetime news_deadline,
                               const string id1,const string id2,const string opportunity,
                               const long first_return_msc=0,const double first_return_ask=0,const datetime guard_until=0,
                               const double fvg_low=0,const double fvg_high=0)
   {
      if(!enabled || !TL_DEMO_DISPATCH_REVIEWED) return Fail("PAIR_DISPATCH_DISABLED_OR_UNREVIEWED");
      if(id1==id2 || !TLDemoId(id1) || !TLDemoId(id2) || StringLen(id1)>18 || StringLen(id2)>18 || opportunity=="")
         return Fail("PAIR_IDENTITIES_REQUIRED");
      if(!ExecutionLimitsReady() || guard_until<=TimeGMT() || fvg_low<=0 || fvg_high<=fvg_low)
         return Fail("REVIEWED_PAIR_LIMITS_FVG_AND_CALENDAR_DEADLINE_REQUIRED");
      pair_in_progress=true;
      pair_first_filled=false; pair_signal_msc=first_return_msc; pair_signal_bid=entry_touch_reference;
      pair_signal_ask=first_return_ask; pair_started=GetTickCount64(); pair_guard_until=guard_until;
      pair_fvg_low=fvg_low; pair_fvg_high=fvg_high;
      MqlTradeRequest first={};
      if(!PrepareCore(buy,single,reference,shared_stop,entry_touch_reference,1,fvg_fill_state,strategy_guards_passed,
                      session_calendar_valid,news_calendar_valid,news_deadline,first,first_return_msc,first_return_ask)) { pair_in_progress=false; return false; }
      if(!SubmitReviewedCore(first,id1,opportunity,single))
      { pair_in_progress=false; EmergencyStop("FIRST_LEG_UNKNOWN_OR_FAILED"); CloseAllDemoPositions("failed-pair:"+opportunity); return false; }
      pair_first_filled=true;
      MqlTradeRequest second={};
      if(!PrepareCore(buy,single,reference,shared_stop,entry_touch_reference,2,fvg_fill_state,strategy_guards_passed,
                      session_calendar_valid,news_calendar_valid,news_deadline,second,first_return_msc,first_return_ask) ||
         !SubmitReviewedCore(second,id2,opportunity,single))
      {
         // Two market legs are not atomic. Compensate observed exposure; never invent the missing half.
         pair_in_progress=false; EmergencyStop("INCOMPLETE_CANONICAL_PAIR"); CloseAllDemoPositions("failed-pair:"+opportunity); return false;
      }
      pair_in_progress=false; return Reconcile();
   }
   bool RepairActualFillStops()
   {
      if(!enabled || !TL_DEMO_DISPATCH_REVIEWED || !Permissions()) return Fail("STOP_REPAIR_DISABLED");
      if(!Reconcile()) return false;
      for(int i=0;i<PositionsTotal();i++)
      {
         ulong ticket=PositionGetTicket(i); if(ticket==0) return Fail("STOP_POSITION_READ_FAILED");
         if((ulong)PositionGetInteger(POSITION_MAGIC)!=magic) continue;
         string id=StringSubstr(PositionGetString(POSITION_COMMENT),3); int n=Find(id);
         if(n<0) return Fail("UNLINKED_STOP_POSITION");
         if(!intents[n].single) continue;
         if(PositionGetDouble(POSITION_VOLUME)!=intents[n].volume) { EmergencyStop("PARTIAL_OR_MIXED_FILL"); return false; }
         string mod_id="M"+id;
         // Completed anchor record persists across restart; later reviewed BE cannot be reset.
         if(Find(mod_id)>=0) continue;
         int sign=intents[n].buy?1:-1;
         double actual_stop=PositionGetDouble(POSITION_PRICE_OPEN)-sign*4.0;
         double grid=SymbolInfoDouble(intents[n].symbol,SYMBOL_TRADE_TICK_SIZE);
         if(!TLDemoGrid(actual_stop,grid)) { EmergencyStop("ACTUAL_FILL_SL_UNREPRESENTABLE"); return false; }
         TLDemoIntent v; v.id=mod_id; v.opportunity="MOD:"+(string)ticket+":"+id; v.symbol=intents[n].symbol;
         v.volume=0; v.sl=actual_stop; v.tp=intents[n].tp; v.buy=intents[n].buy; v.single=false; v.claimed=TimeGMT();
         if(MathAbs(PositionGetDouble(POSITION_SL)-actual_stop)<1e-8 && MathAbs(PositionGetDouble(POSITION_TP)-v.tp)<1e-8)
         {
            // Authoritative position already has the exact actual-fill anchor; no request fabricated.
            v.opportunity="ANCHOR:"+(string)ticket+":"+id; v.state="RECONCILED"; if(!Save(v)) return false;
            int count=ArraySize(intents); ArrayResize(intents,count+1); intents[count]=v; continue;
         }
         MqlTradeRequest r={}; r.action=TRADE_ACTION_SLTP; r.position=ticket; r.symbol=v.symbol; r.magic=magic;
         r.sl=actual_stop; r.tp=v.tp; r.comment="TL:"+mod_id;
         if(!Dispatch(r,v)) { EmergencyStop("ACTUAL_FILL_SL_REPAIR_FAILED"); return false; }
      }
      return true;
   }
   bool CloseAllDemoPositions(const string episode)
   {
      if(!enabled || !TL_DEMO_DISPATCH_REVIEWED || !Permissions()) return Fail("CLOSURE_DISABLED_OR_UNREVIEWED");
      // Closing an authoritative current position is allowed while an entry is unresolved.
      // It never retries that entry. Stable close intent still suppresses duplicate closes.
      Reconcile();
      // Account-wide scope implements owner 'every open position'; DEMO identity checked per dispatch.
      bool all_closed=true;
      for(int i=PositionsTotal()-1;i>=0;i--)
      {
         ulong ticket=PositionGetTicket(i); if(ticket==0) return Fail("POSITION_READ_FAILED");
         string name=PositionGetString(POSITION_SYMBOL); bool buy=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY;
         double volume=PositionGetDouble(POSITION_VOLUME); MqlTick tick; if(!Quote(name,tick)) { Fail("CLOSE_QUOTE_UNAVAILABLE"); all_closed=false; continue; }
         MqlTradeRequest r={}; r.action=TRADE_ACTION_DEAL; r.position=ticket; r.symbol=name; r.magic=magic; r.volume=volume;
         r.type=buy?ORDER_TYPE_SELL:ORDER_TYPE_BUY; r.price=buy?tick.bid:tick.ask;
         if((SymbolInfoInteger(name,SYMBOL_FILLING_MODE)&SYMBOL_FILLING_FOK)==0) { Fail("CLOSE_FOK_UNAVAILABLE"); all_closed=false; continue; }
         r.type_filling=ORDER_FILLING_FOK;
         TLDemoIntent v; v.id="C"+(string)ticket; v.opportunity=episode+":"+(string)ticket; v.symbol=name; v.state="";
         v.volume=volume; v.sl=0; v.tp=0; v.buy=!buy; v.single=false; v.claimed=0; r.comment="TL:"+v.id;
         if(!Dispatch(r,v)) all_closed=false;
      }
      return all_closed && PositionsTotal()==0;
   }
   bool ObserveTradeTransaction()
   {
      if(!enabled || !TL_DEMO_DISPATCH_REVIEWED) return Fail("TRANSACTION_OBSERVER_DISABLED");
      Reconcile();
      if(halted) return CloseAllDemoPositions("persistent-emergency");
      return RepairActualFillStops();
   }
   bool MoveBreakEven(const string entry_id,const ulong position,const double stop,const double target)
   {
      if(!enabled || !TL_DEMO_DISPATCH_REVIEWED || !Permissions() || halted) return Fail("BE_DISABLED_OR_UNREVIEWED");
      if(!Reconcile() || !PositionSelectByTicket(position)) return Fail("BE_POSITION_UNRECONCILED");
      int n=Find(entry_id);
      if(n<0 || (ulong)PositionGetInteger(POSITION_MAGIC)!=magic || PositionGetString(POSITION_COMMENT)!="TL:"+entry_id ||
         PositionGetString(POSITION_SYMBOL)!=intents[n].symbol || PositionGetDouble(POSITION_VOLUME)!=0.01)
         return Fail("BE_AUTHORITATIVE_POSITION_REQUIRED");
      if(!TLDemoGrid(stop,SymbolInfoDouble(intents[n].symbol,SYMBOL_TRADE_TICK_SIZE)) || target!=intents[n].tp)
         return Fail("BE_CANONICAL_GRID_OR_TARGET");
      string id="B"+entry_id;
      int prior=Find(id);
      if(prior>=0)
      {
         if(intents[prior].state=="RECONCILED" && intents[prior].sl==stop && intents[prior].tp==target &&
            PositionGetDouble(POSITION_SL)==stop && PositionGetDouble(POSITION_TP)==target) return true;
         return Fail("DUPLICATE_BE_NO_RETRY");
      }
      TLDemoIntent v; v.id=id; v.opportunity="MOD:"+(string)position+":"+entry_id; v.symbol=intents[n].symbol;
      v.volume=0; v.sl=stop; v.tp=target; v.buy=intents[n].buy; v.single=false; v.claimed=0;
      MqlTradeRequest r={}; r.action=TRADE_ACTION_SLTP; r.position=position; r.symbol=v.symbol; r.magic=magic;
      r.sl=stop; r.tp=target; r.comment="TL:"+id;
      return Dispatch(r,v);
   }
   bool GuardNews(const string event_name,const datetime event_utc,const datetime available_utc,const bool coverage_valid,const int safety_lead_seconds)
   {
      datetime now=TimeGMT();
      if(event_utc>0 && event_name!="CPI" && event_name!="NFP" && event_name!="FOMC") return Fail("UNSUPPORTED_NEWS_NAME");
      if(!coverage_valid || available_utc>now) { EmergencyStop("NEWS_CALENDAR_UNAVAILABLE"); return CloseAllDemoPositions("calendar-unavailable"); }
      if(event_utc>0 && safety_lead_seconds<=0) { EmergencyStop("NEWS_CLOSURE_LEAD_UNRESOLVED"); return false; }
      if(event_utc<=0) return true; // Explicit verified coverage, genuinely no restricted event.
      bool carried=false;
      if(PositionsTotal()>0 && (broker_offset==INT_MAX || MathAbs(broker_offset)>14*3600))
      { EmergencyStop("POSITION_CLOCK_UNVERIFIED"); CloseAllDemoPositions("position-clock-unverified"); return false; }
      for(int p=0;p<PositionsTotal();p++)
      {
         if(PositionGetTicket(p)==0) return Fail("NEWS_POSITION_READ_FAILED");
         if((datetime)(PositionGetInteger(POSITION_TIME)-broker_offset)<=event_utc-180) carried=true;
      }
      if(TLDemoNewsCloseDue(now,event_utc,safety_lead_seconds,carried,PositionsTotal()>0))
      {
         bool closed=CloseAllDemoPositions("news:"+(string)event_utc);
         // Coarse TimeGMT cannot certify an exact deadline-second fill; conservative breach.
         if(!closed || TimeGMT()>=event_utc-180) { EmergencyStop("NEWS_DEADLINE_MISSED_OR_UNVERIFIED"); return false; }
         return true;
      }
      return true;
   }
};
#endif
