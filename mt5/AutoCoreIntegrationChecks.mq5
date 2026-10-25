#property strict
#property version "1.000"
// SYNTHETIC INTEGRATION ONLY. Every broker API below is compile-time injected.
// Never attach this harness to a trading account; use the isolated local runner.
#include "Checks/OfflineBroker.mqh"
#define TRADERLAB_DEMO_FORWARD_RELEASE
#define TRADERLAB_AUTO_CORE_CANDIDATE
#define TRADERLAB_CORE_CHECKS
#include "Include/TraderLab/NativeRetestStream.mqh"
int checks=0,failures=0;
string failed_names="",run_token,fixture_calendar_path;
void Check(const bool ok,const string name)
{ checks++; if(!ok) { failures++; failed_names+=(failed_names==""?"":",")+TLQuote(name); Print("FAIL ",name); } }
bool Near(const double a,const double b) { return MathAbs(a-b)<1e-7; }
TLCoreGuards AllGuards()
{
   TLCoreGuards g; ZeroMemory(g); g.group_confirmed=true; g.group_final=true; g.calendar=true; g.news=true;
   g.daily=true; g.restart=true; g.live_tick=true; g.single_be_defined=true; return g;
}
void Calendar(const bool news=false)
{
   int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   FileWriteString(f,"SYDNEY_NY_NEWS_V2|SYNTHETIC_TEST_ONLY|100|10000|900|3500\r\nDAY|A|100|9000|900\r\n");
   if(news) FileWriteString(f,"NEWS|CPI|2000|0|900\r\n");
   FileClose(f);
}
void Scenario(const string name)
{ TL_FORWARD_DEMO=false; TL_DEMO_DAY_BALANCE=0; TL_DEMO_DAY_STOP=false; FakeReset(); TLAutoCoreNamespace("XAUUSD_o",fake_magic,0,run_token+name); Calendar(); }
bool Configure(TLCoreTradeBook &book)
{
   bool ok=book.Configure("XAUUSD_o",fake_magic,0,fixture_calendar_path,120,false,true);
   book.ExecutionLimits(1000,.22,0); book.TrialRiskLimits(30,1); return ok;
}
TLCoreTrade Trade(const string setup="S",const string prefix="T")
{
   TLCoreTrade t; ZeroMemory(t); t.setup=setup; t.side=1; t.be_known=true;
   t.reference=5000.5; t.planned=5000.5; t.shared_stop=4994; t.id1=prefix+"1"; t.id2=prefix+"2"; return t;
}
bool Enter(TLCoreTradeBook &book,const TLCoreTrade &trade)
{ TLCoreGuards g=AllGuards(); return book.Begin(trade,g,0,true,fake_quote,trade.side==1?4996:5000.5,trade.side==1?5000.5:5005); }
void QuotePreflight()
{
   Scenario("quote-preflight");
   {
      TLCoreConsumption consumed; Check(consumed.Open("XAUUSD_o",fake_magic) && consumed.Consume("BOS-wide",1000000),"first return is durably consumed before preflight");
      TLCoreTradeBook book; Check(Configure(book),"quote regression book configured");
      fake_quote.ask=fake_quote.bid+.51;
      Check(!Enter(book,Trade("wide","W")) && book.EntryError()=="PAIR_QUOTE_TIME_SPREAD_OR_SLIPPAGE_GUARD","observed .51 spread still rejects against .22 cap");
      Check(fake_sends==0 && !book.HasPlans() && book.Ready(),"no send or persisted plan and no permanent emergency on preflight miss");
      Check(consumed.Seen("BOS-wide"),"spread rejection does not rearm consumed BOS");
   }
   {
      TLCoreTradeBook restored; fake_quote.ask=fake_quote.bid+.1;
      Check(Configure(restored) && restored.Ready(),"restart after zero-dispatch quote rejection stays reconciled");
      Check(Enter(restored,Trade("fresh","F")) && fake_opens==2 && FakePositionsTotal()==2,"later independent valid setup enters exactly two positions");
   }
   Scenario("quote-after-first"); fake_second_fault=1;
   { TLCoreTradeBook book; Configure(book);
     Check(!Enter(book,Trade()) && !book.Ready() && FakePositionsTotal()==0,"post-first-send failure still halts and compensates exposure"); }
}
void Lifecycle()
{
   Scenario("lifecycle"); TLCoreTrade trade=Trade();
   {
      TLCoreTradeBook book; Check(Configure(book),"configure synthetic Core book");
      Check(Enter(book,trade) && FakePositionsTotal()==2 && fake_opens==2,"one signal produces exactly two broker-model positions");
      Check(Near(fake_positions[0].volume,.01) && Near(fake_positions[1].volume,.01),"both legs .01");
      Check(Near(fake_positions[0].sl,4994) && Near(fake_positions[1].sl,4994) &&
            Near(fake_positions[0].tp,5006.5) && Near(fake_positions[1].tp,5010.5),"canonical shared SL and TP60/100");
      FakeClose(0,DEAL_REASON_TP,5006.5); book.DealsChanged();
      Check(FakePositionsTotal()==1 && Near(fake_positions[1].sl,5001) && fake_sends==3,"TP1 moves remaining SL to shared reference plus five pips");
      Check(Near(book.CheckNetClosed(),5.8),"synthetic NET reducer includes paid entry and exit commission; not a performance result");
      Check(!Enter(book,trade) && fake_sends==3,"same opportunity cannot send twice");
   }
   {
      TLCoreTradeBook restored; Check(Configure(restored) && restored.Ready(),"restart restores plans positions costs and BE");
      restored.Service(); Check(fake_sends==3 && Near(fake_positions[1].sl,5001),"restart cannot repeat BE or reset SL");
      Check(Near(restored.CheckNetClosed(),5.8),"history reconciliation does not double-count net costs or closed result");
      FakeClose(1,DEAL_REASON_TP,5010.5); restored.DealsChanged();
      Check(FakePositionsTotal()==0 && restored.Ready(),"TP2 closes genuine modeled remaining position");
      Check(!Enter(restored,Trade("OTHER","U")) && fake_opens==2 && restored.EntryError()=="AUTO_TRIAL_ONE_NEW_SETUP_PER_DAY",
            "one daily setup remains reserved after all exits with exact blocking reason");
   }
   { TLCoreTradeBook restored; Check(Configure(restored) && !Enter(restored,trade) && fake_opens==2,"closed setup is not rearmed by another restart"); }
}
void DefinitiveFirstLegRejection()
{
   Check(TLDemoResponseState(false,TRADE_RETCODE_MARKET_CLOSED,0,0)=="REJECTED","market closed zero IDs is definitive rejection");
   Check(TLDemoResponseState(false,TRADE_RETCODE_MARKET_CLOSED,17,0)=="UNKNOWN","market closed with an order ID stays unknown");
   Check(TLDemoResponseState(false,TRADE_RETCODE_TIMEOUT,0,0)=="UNKNOWN","timeout absence never proves rejection");
   for(int code=0;code<4;code++)
   {
      Scenario("first-reject"+(string)code);
      if(code<2) fake_first_retcode=code==0?TRADE_RETCODE_MARKET_CLOSED:TRADE_RETCODE_REJECT;
      else { fake_first_check_retcode=TRADE_RETCODE_MARKET_CLOSED; fake_reject_check_number=code==2?1:2; }
      int rejected_sends=code<2?1:0;
      {
         TLCoreConsumption consumed; Check(consumed.Open("XAUUSD_o",fake_magic) && consumed.Consume("BOS-rejected",1000000),"rejected return is durably consumed");
         TLCoreTradeBook book; Check(Configure(book),"rejection regression configured");
         Check(!Enter(book,Trade("rejected","R")) && book.Ready() && fake_sends==rejected_sends && FakePositionsTotal()==0,
               "definitive first-leg rejection reconciles without global emergency");
         Check(book.EntryError()=="DEFINITIVE_FIRST_LEG_REJECTION_RECONCILED_NO_RETRY","rejection reports exact recoverable outcome");
         Check(!Enter(book,Trade("rejected","R")) && fake_sends==rejected_sends,"same rejected setup is never resubmitted");
         Check(consumed.Seen("BOS-rejected"),"rejection never rearms First Touch");
      }
      {
         TLCoreConsumption consumed; Check(consumed.Open("XAUUSD_o",fake_magic) && consumed.Seen("BOS-rejected"),"consumption survives rejection restart");
         TLCoreTradeBook restored; Check(Configure(restored) && restored.Ready(),"rejected intent remains reconciled across restart");
         Check(!Enter(restored,Trade("rejected","R")) && fake_sends==rejected_sends,"restart never retries rejected setup");
         // Keep the existing one-setup daily fixture budget: advance its canonical
         // day instead of weakening a risk guard to make this regression pass.
         fake_now=9000; fake_quote.time=fake_now; fake_quote.time_msc=(long)fake_now*1000;
         int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
         FileWriteString(f,"SYDNEY_NY_NEWS_V2|SYNTHETIC_TEST_ONLY|8000|18000|9000|12000\r\nDAY|B|9000|18000|9000\r\n"); FileClose(f);
         restored.Service();
         fake_first_check_retcode=0;
         Check(Enter(restored,Trade("fresh","N")) && fake_sends==rejected_sends+2 && FakePositionsTotal()==2,
               "after reopening fresh independent setup can dispatch exactly two legs");
      }
   }
   for(int mode=0;mode<=4;mode++)
   {
      Scenario("first-uncertain"+(string)mode);
      fake_first_retcode=mode==0?TRADE_RETCODE_TIMEOUT:TRADE_RETCODE_MARKET_CLOSED; fake_reject_evidence=mode;
      { TLCoreTradeBook book; Configure(book);
        Check(!Enter(book,Trade()) && !book.Ready(),"unknown or contradictory/unavailable broker evidence remains blocked");
        int sent=fake_sends; fake_history_ok=true; book.Service();
        Check(!Enter(book,Trade("later","L")) && fake_sends==sent,"uncertain first order is never automatically repeated or unlocked"); }
   }
}
void SellLifecycle()
{
   Scenario("sell-lifecycle"); TLCoreTrade trade=Trade(); trade.side=-1; trade.shared_stop=5007;
   { TLCoreTradeBook book; Configure(book);
     Check(Enter(book,trade) && !fake_positions[0].buy && !fake_positions[1].buy,"Sell Core enters two .01 positions at observed Bid");
     Check(Near(fake_positions[0].price,5000.5) && Near(fake_positions[0].sl,5007) &&
           Near(fake_positions[0].tp,4994.5) && Near(fake_positions[1].tp,4990.5),"Sell canonical SL and TP60/100");
     FakeClose(0,DEAL_REASON_TP,4994.5); book.DealsChanged();
     Check(Near(fake_positions[1].sl,5000) && fake_sends==3,"Sell TP1 moves SL to shared reference minus five pips"); }
   { TLCoreTradeBook restored; Check(Configure(restored) && restored.Ready(),"Sell lifecycle survives restart with BE intact");
     FakeClose(1,DEAL_REASON_TP,4990.5); restored.DealsChanged();
     Check(FakePositionsTotal()==0 && !Enter(restored,trade) && fake_opens==2,"Sell TP2 exits and consumed setup never reenters"); }
}
void Faults()
{
   for(int mode=1;mode<=3;mode++)
   {
      Scenario("second"+(string)mode); fake_second_fault=mode;
      { TLCoreTradeBook book; Check(Configure(book),"fault book configured"); Check(!Enter(book,Trade()) && !book.Ready(),"second reject timeout or partial latches emergency");
        Check(FakePositionsTotal()==0,"incomplete pair compensates observed exposure"); }
      { TLCoreTradeBook restored; Configure(restored); int attempts=fake_opens; Check(!Enter(restored,Trade()) && attempts==fake_opens,"restart never retries failed or unknown entry"); }
   }
   Scenario("stop");
   { TLCoreTradeBook book; Configure(book); Check(Enter(book,Trade()),"stop setup entered");
     FakeClose(0,DEAL_REASON_SL,4994); FakeClose(1,DEAL_REASON_SL,4994); book.DealsChanged();
     Check(FakePositionsTotal()==0 && book.CheckStoppedSetups()==1,"both stop deals reconcile and count one stopped setup"); }
   Scenario("margin-after-first");
   { TLCoreTradeBook book; Configure(book); fake_margin_after_first=.5;
     Check(!Enter(book,Trade()) && fake_opens==1 && FakePositionsTotal()==0 && !book.Ready(),
           "margin loss after first fill blocks second order and compensates actual first position"); }
   Scenario("be-stop");
   { TLCoreTradeBook book; Configure(book); Enter(book,Trade()); FakeClose(0,DEAL_REASON_TP,5006.5); book.DealsChanged();
     FakeClose(1,DEAL_REASON_SL,5001); book.DealsChanged();
     Check(!book.Ready(),"unresolved profitable BE stop counting blocks further entries without changing owner rule"); }
   Scenario("lost-history");
   { TLCoreTradeBook book; Configure(book); Enter(book,Trade()); fake_history_ok=false; book.Service();
     Check(!book.Ready() && FakePositionsTotal()==0,"history outage retains emergency closure ability"); }
   Scenario("close-rejected");
   { TLCoreTradeBook book; Configure(book); Enter(book,Trade()); fake_close_rejected=true; book.Emergency("SYNTHETIC_TEST_STOP");
     Check(FakePositionsTotal()==2,"definitive close rejection is not invented liquidation");
     fake_close_rejected=false; book.Service();
     Check(FakePositionsTotal()==0 && !book.Ready(),"emergency retries definitive rejected closes while entries remain latched off"); }
   Scenario("close-unknown");
   { TLCoreTradeBook book; Configure(book); Enter(book,Trade()); fake_close_unknown=true; book.Emergency("SYNTHETIC_TEST_STOP");
     int sent=fake_sends; fake_close_unknown=false; book.Service();
     Check(FakePositionsTotal()==2 && fake_sends==sent && !book.Ready(),"unknown close cannot be retried or reported as flat without broker evidence"); }
}
void Controls()
{
   for(int mode=0;mode<2;mode++)
   {
      Scenario("forbidden-account"+(string)mode); fake_account_mode=mode==0?ACCOUNT_TRADE_MODE_REAL:ACCOUNT_TRADE_MODE_CONTEST;
      TLCoreTradeBook book; Check(!Configure(book) && !Enter(book,Trade()) && fake_opens==0,"Real and Contest rejected by actual Core gateway account check");
   }
   for(int mode=0;mode<6;mode++)
   {
      Scenario("guard"+(string)mode); TLCoreTradeBook book; Configure(book);
      if(mode==0) book.TrialRiskLimits(0,1);
      if(mode==1) book.TrialRiskLimits(30,-1);
      if(mode==2) book.TrialRiskLimits(10,1);
      if(mode==3) fake_margin_free=1;
      if(mode==4) fake_quote.ask=fake_quote.bid+.5;
      if(mode==5) fake_pending=1;
      Check(!Enter(book,Trade()) && fake_opens==0,"unknown risk cost budget risk cap margin spread or foreign order blocks without sending");
   }
   for(int foreign=0;foreign<2;foreign++)
   {
      Scenario("exposure"+(string)foreign); TLCoreTradeBook book; Configure(book);
      ArrayResize(fake_positions,1); ZeroMemory(fake_positions[0]); fake_positions[0].open=true; fake_positions[0].ticket=999;
      fake_positions[0].magic=foreign?999:fake_magic; fake_positions[0].volume=.03; fake_positions[0].price=5000;
      fake_positions[0].sl=4994; fake_positions[0].buy=true;
      Check(!Enter(book,Trade()) && fake_opens==0,"total .04 cap and manual/other-robot exclusion");
   }
   Scenario("foreign-at-send-boundary");
   { TLCoreTradeBook book; Configure(book); fake_foreign_on_check=2;
     Check(!Enter(book,Trade()) && fake_opens==0,"foreign position appearing during OrderCheck blocks at final send boundary");
     Check(FakePositionsTotal()==1 && fake_positions[0].magic==999 && fake_sends==0,
           "entry veto and Core emergency do not liquidate a foreign position outside NEWS-01"); }
   Check(TLAutoCoreTrialDayAllowed("S","S") && !TLAutoCoreTrialDayAllowed("S","T"),"same setup second stage allowed; new setup rejected");
   Check(TLAutoCoreTrialLotsAllowed(.02,.02) && TLAutoCoreTrialLotsAllowed(.03,.01) &&
         !TLAutoCoreTrialLotsAllowed(.04,.01),"hard .04 aggregate volume cap is inclusive without lot rounding");
}
void DayChanges()
{
   for(int overlap=0;overlap<2;overlap++)
   {
      Scenario("day"+(string)overlap);
      { TLCoreTradeBook book; Configure(book); Enter(book,Trade());
        FakeClose(0,DEAL_REASON_TP,5006.5); FakeClose(1,DEAL_REASON_TP,5010.5); book.DealsChanged();
        int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
        FileWriteString(f,"SYDNEY_NY_NEWS_V2|SYNTHETIC_TEST_ONLY|8000|18000|9000|12000\r\nDAY|B|"+
                          (overlap?"8000":"9000")+"|18000|9000\r\n"); FileClose(f);
        fake_now=9000; fake_quote.time=9000; fake_quote.time_msc=9000000;
        fake_quote.bid=5000.5; fake_quote.ask=5000.6; book.Service();
        bool entered=Enter(book,Trade("NEXTDAY","N"));
        Check(overlap?!entered:entered,"safe day transition allows only nonoverlap; no invented daily clipping");
      }
      { TLCoreTradeBook restored; Configure(restored); int attempts=fake_opens;
        Check(!Enter(restored,Trade("ANOTHER","Z")) && fake_opens==attempts,"day reservation or emergency survives rollover restart"); }
   }
}
void TornDiagnostics()
{
   Scenario("csv-not-authoritative");
   { TLCoreTradeBook book; Configure(book); Check(Enter(book,Trade()),"WAL scenario starts with two receipts"); }
   string kinds[]={"plans","gateway"};
   for(int i=0;i<2;i++)
   {
      int f=FileOpen(TLAutoCoreJournalPath(kinds[i]),FILE_READ|FILE_WRITE|FILE_BIN); FileSeek(f,0,SEEK_END);
      FileWriteInteger(f,'X',CHAR_VALUE); FileFlush(f); FileClose(f);
   }
   { TLCoreTradeBook restored; Check(Configure(restored) && restored.Ready() && !Enter(restored,Trade()) && fake_opens==2,
       "torn diagnostic CSV does not discard authoritative checksummed plans or duplicate positions"); }
   string path=TLAutoCoreJournalPath("plans-wal");
   int f=FileOpen(path,FILE_READ|FILE_WRITE|FILE_BIN); FileSeek(f,0,SEEK_END); FileWriteInteger(f,1,CHAR_VALUE); FileFlush(f); FileClose(f);
   { TLCoreTradeBook restored; Check(!Configure(restored) && !Enter(restored,Trade()) && fake_opens==2,
       "corrupt authoritative plan WAL fails closed without inventing flat positions"); }
}
void NewsAndExpiry()
{
   for(int mode=0;mode<4;mode++)
   {
      Scenario("calendar"+(string)mode); if(mode<2) Calendar(true);
      TLCoreTradeBook book; Configure(book); Check(Enter(book,Trade()),"calendar scenario starts with a valid pair");
      fake_now=mode==0?1700:mode==1?1820:3500;
      fake_quote.time=fake_now; fake_quote.time_msc=(long)fake_now*1000;
      if(mode==3) { int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI); FileWriteString(f,"INVALID|OUTAGE\n"); FileClose(f); }
      book.Service();
      Check(FakePositionsTotal()==0,"news lead deadline source outage or exact TTL expiry closes all observed positions");
      if(mode>0) Check(!book.Ready(),"breach expiry and provider outage latch emergency");
   }
   Scenario("ttl"); TLCoreCalendar cal; Check(cal.Load(fixture_calendar_path),"V2 loaded"); string day; bool blocked;
   Check(cal.Day(3499,day) && !cal.Day(3500,day) && !cal.News(3500,blocked),"TTL exclusive on entries and news validation");
   Check(cal.EntryUntil(1000)==3500,"pair cannot cross source freshness deadline");
}
void Geometry()
{
   TLCoreGuards g=AllGuards();
   for(int side=-1;side<=1;side+=2)
   {
      double low=4996,high=5000.5,reference=side==1?5000:4997;
      TLFirstReturn r; ZeroMemory(r); MqlTick t=fake_quote; t.bid=reference+side; TLAdvanceReturn(r,side,reference,t.bid,t,1,1);
      t.time_msc++; t.bid=reference; bool consumed=TLAdvanceReturn(r,side,reference,t.bid,t,2,1);
      int post=side==1?(t.bid<=low?2:t.bid<high?1:0):(t.bid>=high?2:t.bid>low?1:0);
      Check(consumed && r.exact && post==1 && TLCoreEntryBlock(g,post,false,true)!="","exact interior first return becomes PARTIAL before eligibility; no rule relaxed");
      Check(!TLAdvanceReturn(r,side,reference,t.bid,t,3,1),"blocked first touch cannot be rearmed");
   }
}
void Journals()
{
   string path="synthetic-wal-"+run_token+".dat",scope="SYNTHETIC_RECOVERY_V1";
   MqlTick tick=fake_quote; MqlRates bar={}; string encoded=TLRecoveryInput("T",-1,1,1,tick,bar),row;
   { TLRecoveryJournal journal; Check(journal.Open(path,scope) && journal.Next(row)==0 && journal.Append(encoded),"durable journal append and flush"); }
   { TLRecoveryJournal journal; Check(journal.Open(path,scope) && journal.Next(row)==1 && row==encoded && journal.Next(row)==0,"journal restart preserves exact tick occurrence"); }
   { TLRecoveryJournal journal; Check(!journal.Open(path,"OTHER_SCOPE"),"journal scope conflict blocks"); }
   int f=FileOpen(path,FILE_READ|FILE_WRITE|FILE_BIN); FileSeek(f,0,SEEK_END); FileWriteInteger(f,1,CHAR_VALUE); FileFlush(f); FileClose(f);
   { TLRecoveryJournal journal; Check(journal.Open(path,scope) && journal.Next(row)==1 && journal.Next(row)==-1,"torn tail blocks rather than silently dropping consumed history"); }
   string kind; int frame,ordinal; long index; MqlTick decoded; MqlRates rates;
   Check(TLRecoveryParse(encoded,kind,frame,index,ordinal,decoded,rates) && TLSameTick(tick,decoded),"17-digit tick round trip preserves duplicate identity");
}
void FeedTick(TLNativeRetestStream &stream,MqlTick &tick,long &index,const int ordinal=1)
{
   TLEventLog silent; fake_quote=tick; fake_now=tick.time;
   stream.AfterTick(tick,++index,ordinal,silent);
}
void RecoveryPipeline(const bool stop_after_dispatch=false)
{
   Scenario("detector-restart"); TLEventLog silent; string frozen; long index=0; MqlTick tick=fake_quote;
   {
      TLNativeRetestStream stream; TLTickCapture capture;
      stream.Configure("XAUUSD_o",0); stream.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
      stream.CoreExecutionLimits(1000,.22,0); stream.CoreTrialRiskLimits(30,1);
      Check(stream.OpenRecovery(capture,silent),"fresh autonomous recovery journal opens");
      MqlTick baseline[1]; baseline[0]=tick; capture.Resume("XAUUSD_o",baseline,0);
      Check(stream.SeedRecovery(capture),"complete excluded baseline durably committed");
      for(int i=0;i<21;i++)
      {
         MqlRates bar; ZeroMemory(bar); bar.time=1000+i*60;
         bar.open=4989.3; bar.close=4989.5; bar.high=4994; bar.low=4988;
         if(i==0) { bar.open=4995; bar.close=4995.2; bar.high=5000; bar.low=4994; }
         if(i==1) { bar.open=4992; bar.close=4992.2; bar.high=4997; bar.low=4990; }
         if(i==9) { bar.open=4993; bar.close=4993.2; bar.high=4996; bar.low=4991; }
         if(i==10)
         {
            bar.open=4993; bar.close=5005; bar.high=5006; bar.low=4992;
            // Intrabar wick break is observed BEFORE the impulse closes.
            tick.time=bar.time+30; tick.time_msc=(long)tick.time*1000; tick.bid=5005.8; tick.ask=5005.9;
            FeedTick(stream,tick,index);
         }
         if(i>=11) { bar.open=5006; bar.close=5006.2; bar.high=5008; bar.low=i==11?5000.5:5004; }
         tick.time=bar.time+60; tick.time_msc=(long)tick.time*1000;
         tick.bid=i>=10?5006.2:bar.close; tick.ask=tick.bid+.1;
         Check(stream.FixtureBar(0,bar,tick,index+1),"as-of fixture candle durably recorded before detector");
         FeedTick(stream,tick,index);
         if(i<20) Check(stream.CheckGroups()==0,"ten subsequent closes cannot be bypassed");
      }
      Check(stream.CheckGroups()==1 && fake_opens==0,"detectors autonomously freeze genuine fixture BOS/FVG/OB membership without approval");
      frozen=stream.CheckState();
   }
   {
      TLNativeRetestStream restored; TLTickCapture capture;
      restored.Configure("XAUUSD_o",0); restored.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
      restored.CoreExecutionLimits(1000,.22,0); restored.CoreTrialRiskLimits(30,1);
      Check(restored.OpenRecovery(capture,silent) && restored.CheckState()==frozen && fake_opens==0,
            "restart rebuilds exact membership plan outbound history availability and consumed flags without sends");
      tick.time_msc++; tick.bid=5000.5; tick.ask=5000.6; FeedTick(restored,tick,index);
      Check(restored.CheckPending()==1,"first valid post-confirmation boundary return selects frozen Core plan");
      restored.CoreFinishDrain(tick,tick,true,silent);
      Check(fake_opens==2 && FakePositionsTotal()==2,"restored automatic signal traverses original Core and paired gateway transport");
   }
   if(stop_after_dispatch) return; // Physical-process harness persists only its external fake broker here.
   {
      TLNativeRetestStream restored; TLTickCapture capture;
      restored.Configure("XAUUSD_o",0); restored.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
      restored.CoreExecutionLimits(1000,.22,0); restored.CoreTrialRiskLimits(30,1);
      Check(restored.OpenRecovery(capture,silent) && restored.CheckPending()==0 && fake_opens==2,
            "restart after dispatch restores broker positions but never replays consumed pending orders");
      // Identical raw occurrence in the same millisecond must still be journaled.
      FeedTick(restored,tick,index,2); restored.CoreFinishDrain(tick,tick,true,silent);
      Check(fake_opens==2,"same-ms duplicate occurrence does not duplicate a trade");
      tick.time_msc++; tick.bid=4997.5; tick.ask=4997.6; FeedTick(restored,tick,index);
      restored.CoreFinishDrain(tick,tick,true,silent);
      Check(fake_opens==2 && restored.CheckPending()==0,"second extreme inside FVG becomes PARTIAL and remains blocked");
      frozen=restored.CheckState();
   }
   {
      TLNativeRetestStream restored; TLTickCapture capture;
      restored.Configure("XAUUSD_o",0); restored.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
      Check(restored.OpenRecovery(capture,silent) && restored.CheckState()==frozen && fake_opens==2,
            "another restart preserves PARTIAL and both consumed extremes without rearming");
   }
   string path=TLAutoCoreJournalPath("inputs");
   int f=FileOpen(path,FILE_READ|FILE_WRITE|FILE_BIN); FileSeek(f,0,SEEK_END); FileWriteInteger(f,1,CHAR_VALUE); FileFlush(f); FileClose(f);
   { TLNativeRetestStream restored; TLTickCapture capture;
     restored.Configure("XAUUSD_o",0); restored.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
     Check(!restored.OpenRecovery(capture,silent) && fake_opens==2 && FakePositionsTotal()==0,
           "corrupt discovery WAL stops entry while valid broker plan journals retain emergency closure"); }
   Check(FileMove(path,0,path+".retained",0),"retain corrupt fixture journal without deleting it");
   { TLNativeRetestStream restored; TLTickCapture capture;
     restored.Configure("XAUUSD_o",0); restored.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
     Check(!restored.OpenRecovery(capture,silent) && !FileIsExist(path) && fake_opens==2,
           "missing member of recovery set is not silently treated as a new trading session"); }
}
void ForwardDeploymentControls()
{
   Scenario("live-calendar"); fake_is_tester=false;
   {
      TLCoreCalendar cal;
      Check(!cal.Load(fixture_calendar_path) && cal.error=="VERIFIED_FORWARD_CALENDAR_PROVIDER_REQUIRED",
            "live calendar rejects synthetic V2 even with fresh timestamps");
      int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
      FileWriteString(f,"SYDNEY_NY_NEWS_V2|PRIMARY_BLS_FED_FORWARD_V1|100|9000|900|3500\r\nDAY|A|100|9000|900\r\nNEWS|CPI|2000|0|900\r\n"); FileClose(f);
      bool blocked; string day;
      Check(cal.Load(fixture_calendar_path) && cal.Day(1000,day) && cal.News(1000,blocked),"fresh primary forward packet can be observed without unlocking execution");
      Check(!cal.Fresh(3500) && !cal.Fresh(899),"live packet expires and future observation never becomes present evidence");
      f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
      FileWriteString(f,"SYDNEY_NY_NEWS_V2|PRIMARY_BLS_FED_FORWARD_V1|100|9000|900|3500\r\nDAY|A|100|9000|900\r\nNEWS|CPI|2000|0|1500\r\n"); FileClose(f);
      Check(!cal.Load(fixture_calendar_path) && cal.error=="FORWARD_CALENDAR_OBSERVATION_MISMATCH","future-known news cannot masquerade as a verified forward snapshot");
      Check(!TLCoreCalendarSourceAllowed(false,false,"PRIMARY_BLS_FED_FORWARD_V1") &&
            !TLCoreCalendarSourceAllowed(false,true,"EXPERIMENTAL_TESTER_ONLY:historical") &&
            TLCoreCalendarSourceAllowed(true,false,"SYNTHETIC_TEST_ONLY"),"legacy historical packets remain tester only");
   }
   Scenario("disconnect");
   {
      TLDemoGateway gateway;
      Check(gateway.Start(true,"XAUUSD_o",fake_magic,TLAutoCoreJournalPath("gateway"),0,true) && gateway.CheckReconciled(),"initial tester snapshot reconciles");
      gateway.CheckTransportEnvironment(false); fake_is_tester=false; fake_connected=false;
      Check(!gateway.Reconcile() && !gateway.CheckReconciled() && gateway.Error()=="BROKER_DISCONNECTED_RECONCILIATION_REQUIRED",
            "disconnected terminal cannot reconcile from cached history");
      fake_connected=true; fake_history_ok=false;
      Check(!gateway.Reconcile() && !gateway.CheckReconciled(),"reconnect with missing broker history stays blocked");
      fake_history_ok=true;
      Check(gateway.Reconcile() && gateway.CheckReconciled() && !gateway.CanDispatch() && fake_sends==0,
            "fresh broker proof returns but live compile lock remains closed");
   }
   Scenario("preflight-snapshot");
   {
      TLDemoGateway gateway; gateway.Start(true,"XAUUSD_o",fake_magic,TLAutoCoreJournalPath("gateway"),0,true);
      gateway.ExecutionLimits(1000,.22,0); fake_history_ok=false;
      Check(!gateway.CoreQuotePreflight(true,fake_quote) && !gateway.CheckReconciled() && fake_sends==0,
            "unchanged executable quote cannot bypass a fresh broker history failure");
   }
   Scenario("deal-audit"); string path="synthetic-deals-"+run_token+".jsonl";
   TLEventLog audit;
   Check(audit.Open(path,0,0) && audit.Healthy(),"execution audit opens unique scoped file");
   {
      TLCoreTradeBook book; book.BindAudit(GetPointer(audit)); Configure(book);
      Check(Enter(book,Trade()) && book.CheckAuditedDeals()==2,"both actual entry receipts are logged");
      FakeClose(0,DEAL_REASON_TP,5006.5); fake_deals[ArraySize(fake_deals)-1].magic=0; book.DealsChanged(); book.Service();
      Check(book.CheckAuditedDeals()==3 && Near(fake_positions[1].sl,5001),"TP receipt and actual BE survive repeated reconciliation without duplicate deal audit");
   }
   audit.Close(); Check(audit.Open(path+".restart",0,0),"restart keeps prior raw and opens a new audit shard");
   {
      TLCoreTradeBook restored; restored.BindAudit(GetPointer(audit)); Configure(restored);
      Check(restored.CheckAuditedDeals()==3 && restored.Ready(),"broker history reconstructs all receipts including missed callbacks after restart");
      FakeClose(1,DEAL_REASON_CLIENT,5010.5); fake_deals[ArraySize(fake_deals)-1].magic=0; restored.DealsChanged();
      Check(restored.CheckAuditedDeals()==4,"last exit is logged with actual broker reason and costs");
   }
   audit.Close();
   Scenario("audit-compensation"); Check(audit.Open(path+".partial",0,0),"compensation audit opens without replacing prior raw");
   {
      TLCoreTradeBook book; book.BindAudit(GetPointer(audit)); Configure(book); fake_second_fault=3;
      Check(!Enter(book,Trade()) && FakePositionsTotal()==0,"unsupported partial pair still compensates and stays halted");
      for(int i=0;i<ArraySize(fake_deals);i++) if(fake_deals[i].entry==DEAL_ENTRY_OUT) fake_deals[i].magic=0;
      book.Service();
      Check(book.CheckAuditedDeals()==ArraySize(fake_deals) && book.CheckAuditedDeals()>0 && !book.Ready(),
            "all partial and compensation receipts remain auditable without accepting an invalid pair");
   }
   audit.Close();
   Scenario("audit-outage");
   {
      TLCoreTradeBook book; book.BindAudit(GetPointer(audit)); Configure(book);
      Check(!Enter(book,Trade()) && fake_sends==0 && book.EntryError()=="CORE_TRADE_AUDIT_UNAVAILABLE","closed audit sink blocks entries without fabricating a successful trade");
   }
}
#include "Checks/DemoForwardFixtures.mqh"
void OnStart()
{
   run_token=(string)GetMicrosecondCount(); fixture_calendar_path="synthetic-calendar-"+run_token+".csv";
   if(FileIsExist("CoreQuotePreflightOnly.flag")) QuotePreflight();
   else {
   Lifecycle(); SellLifecycle(); Faults(); Controls(); DayChanges(); TornDiagnostics(); NewsAndExpiry(); Geometry(); Journals(); RecoveryPipeline(); QuotePreflight(); DefinitiveFirstLegRejection(); ForwardDeploymentControls(); DemoForwardControls();
   Scenario("legacy-ledger");
   string legacy=TLAutoCoreLegacyJournalPath("plans",fake_magic);
   int old=FileOpen(legacy,FILE_WRITE|FILE_TXT|FILE_ANSI); FileWriteString(old,"SYNTHETIC_OLD_LAYOUT"); FileFlush(old); FileClose(old);
   Check(TLAutoCoreRecoverySet()==-1,"legacy candidate ledger cannot silently become a fresh day budget");
   }
   string result="{\"mode\":\"SYNTHETIC_NATIVE_INTEGRATION_NOT_HISTORICAL\",\"checks\":"+(string)checks+
      ",\"failures\":"+(string)failures+",\"synthetic_transport_requests\":"+(string)fake_total_sends+
      ",\"real_broker_orders\":0,\"historical_backtest\":false,\"failed_checks\":["+failed_names+"]}";
   int f=FileOpen("AutoCoreIntegrationChecks-result.json",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   FileWriteString(f,result+"\n"); FileFlush(f); FileClose(f); Print(result);
   if(StringFind(TerminalInfoString(TERMINAL_PATH),"offline-native")>=0) TerminalClose(failures==0?0:1);
}
