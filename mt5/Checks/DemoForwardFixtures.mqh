// Synthetic account-bound forward transport checks. Never in a production include tree.
void ForwardScenario(const string name)
{
   Scenario(name); fake_is_tester=false; fake_login=91496222;
   fake_magic=(ulong)TLRecoveryHash(run_token+name)+2026102501;
   TL_FORWARD_DEMO=true; TL_TESTER_POLICY_MASK=7; TL_TESTER_DISCOVERY=1; TL_TESTER_M1_MAX_AGE_MINUTES=120;
   TLAutoCoreNamespace("XAUUSD_o",fake_magic,0,run_token+name);
   int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   FileWriteString(f,"SYDNEY_NY_NEWS_V2|MT5_USD_PRIMARY_FORWARD_V1|100|10000|900|3500\nDAY|A|100|9000|900\n"); FileClose(f);
}
bool ForwardBook(TLCoreTradeBook &book)
{
   bool ok=book.Configure("XAUUSD_o",fake_magic,0,fixture_calendar_path,120,true,false);
   book.ExecutionLimits(1500,.22,2); book.TrialRiskLimits(10,1); book.Service(); return ok;
}
TLCoreTrade ForwardTrade(const string setup="DS",const string prefix="D")
{
   TLCoreTrade t=Trade(setup,prefix); t.single=true; t.be_actual=true; t.shared_stop=t.reference-4; return t;
}
string ForwardDetectorState(const bool live)
{
   if(live) ForwardScenario("parity-live");
   else { Scenario("parity-tester"); TL_TESTER_POLICY_MASK=7; TL_TESTER_DISCOVERY=1; TL_TESTER_M1_MAX_AGE_MINUTES=120; }
   TLEventLog silent; TLNativeRetestStream stream; TLTickCapture capture; MqlTick tick=fake_quote; long index=0;
   stream.Configure("XAUUSD_o",0); stream.ConfigureCore(fake_magic,fixture_calendar_path,120,"",live,3);
   stream.CoreExecutionLimits(1500,.22,2); stream.CoreTrialRiskLimits(10,1);
   Check(stream.OpenRecovery(capture,silent),"parity WAL opens in genuine configured environment");
   MqlTick baseline[1]; baseline[0]=tick; capture.Resume("XAUUSD_o",baseline,0); stream.SeedRecovery(capture);
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
         tick.time=bar.time+30; tick.time_msc=(long)tick.time*1000; tick.bid=5005.8; tick.ask=5005.9; FeedTick(stream,tick,index);
      }
      if(i>=11) { bar.open=5006; bar.close=5006.2; bar.high=5008; bar.low=i==11?5000.5:5004; }
      tick.time=bar.time+60; tick.time_msc=(long)tick.time*1000; tick.bid=i>=10?5006.2:bar.close; tick.ask=tick.bid+.1;
      stream.FixtureBar(0,bar,tick,index+1); FeedTick(stream,tick,index);
      if(i<20) Check(stream.CheckGroups()==0,"Demo and Tester both require ten subsequent closed bars");
   }
   tick.time_msc++; tick.bid=5000.5; tick.ask=5000.6; FeedTick(stream,tick,index);
   Check(stream.CheckGroups()==1 && stream.CheckPending()==1,"Body80 AGE120 mask7 genuine first return becomes pending without approval");
   Check(fake_sends==0,"detector parity never fabricates a broker execution");
   return stream.CheckState();
}
void DemoForwardControls()
{
   string tester=ForwardDetectorState(false),demo=ForwardDetectorState(true);
   Check(tester==demo,"Tester and actual non-Tester Demo policy produce identical complete detection state");
   ForwardScenario("identity");
   Check(TLDemoForwardReviewed(),"account-bound explicit release accepts authorized Demo");
   fake_account_mode=ACCOUNT_TRADE_MODE_REAL; Check(!TLDemoForwardReviewed() && !TLPolicyActive(),"Real cannot enable shared forward policy or dispatch");
   fake_account_mode=ACCOUNT_TRADE_MODE_CONTEST; Check(!TLDemoForwardReviewed(),"Contest cannot enable dispatch");
   fake_account_mode=ACCOUNT_TRADE_MODE_DEMO; fake_login=123456; Check(!TLDemoForwardReviewed(),"other Demo identity is not authorized");
   ForwardScenario("daily-risk");
   {
      TLCoreTradeBook book; Check(ForwardBook(book) && Near(TL_DEMO_DAY_BALANCE,1000),"Demo daily balance baseline durably established");
      fake_equity=980; book.Service();
      Check(TL_DEMO_DAY_STOP && !Enter(book,ForwardTrade()) && fake_sends==0,"two percent equity loss blocks new entries without changing stops or size");
   }
   TL_DEMO_DAY_BALANCE=0; TL_DEMO_DAY_STOP=false; fake_equity=1000;
   { TLCoreTradeBook restored; Check(ForwardBook(restored) && TL_DEMO_DAY_STOP && !Enter(restored,ForwardTrade()),"restart cannot reset daily loss latch even after equity recovers"); }
   ForwardScenario("risk-cap");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"Demo risk book configured");
      Check(!Enter(book,Trade()) && fake_sends==0 && book.EntryError()=="AUTO_TRIAL_OPEN_RISK_CAP_EXCEEDED","unchanged original stop over one percent equity is rejected, never resized");
      Check(Enter(book,ForwardTrade()) && fake_opens==2,"valid canonical single pair passes actual forward path at .01 each");
      Check(!Enter(book,ForwardTrade()) && fake_opens==2,"Demo duplicate opportunity cannot dispatch twice");
      FakeClose(0,DEAL_REASON_TP,5006.5); book.DealsChanged();
      Check(FakePositionsTotal()==1 && Near(fake_positions[1].sl,5001.1) && fake_sends==3,"forward TP1 automatically moves the second single leg to actual fill plus canonical five pips");
   }
   { TLCoreTradeBook restored; Check(ForwardBook(restored) && fake_opens==2 && !Enter(restored,ForwardTrade()),"Demo broker reconciliation restores positions without replaying an order"); }
   ForwardScenario("calendar-recovery");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"calendar recovery book configured");
      int f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI); FileWriteString(f,"INVALID\n"); FileClose(f); book.Service();
      Check(book.Ready() && !Enter(book,ForwardTrade()) && fake_sends==0,"calendar outage blocks entry without permanent halt");
      f=FileOpen(fixture_calendar_path,FILE_WRITE|FILE_TXT|FILE_ANSI); FileWriteString(f,"SYDNEY_NY_NEWS_V2|MT5_USD_PRIMARY_FORWARD_V1|100|10000|900|3500\nDAY|A|100|9000|900\n"); FileClose(f); book.Service();
      fake_first_retcode=TRADE_RETCODE_MARKET_CLOSED;
      Check(!Enter(book,ForwardTrade("closed","C")) && book.Ready(),"actual forward Market closed rejection does not poison new opportunities");
      fake_first_retcode=0;
      Check(Enter(book,ForwardTrade("new","N")) && fake_opens==3 && FakePositionsTotal()==2,"after calendar and broker recovery an independent opportunity can enter");
   }
   ForwardScenario("unknown-forward");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"unknown forward book configured"); fake_first_retcode=TRADE_RETCODE_TIMEOUT;
      Check(!Enter(book,ForwardTrade()) && !book.Ready() && fake_sends==1,"Demo timeout is unknown and never automatically retried");
      fake_first_retcode=0; book.Service();
      Check(!Enter(book,ForwardTrade("fresh","Z")) && fake_sends==1,"unresolved broker intent blocks even a different opportunity");
   }
   ForwardScenario("reconnect-forward");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"forward reconnect book configured"); fake_connected=false; book.Service();
      Check(!Enter(book,ForwardTrade()) && fake_sends==0,"offline forward account never dispatches cached evidence");
      fake_connected=true; book.Service();
      Check(Enter(book,ForwardTrade("reconnected","R")) && fake_opens==2,"fresh reconciliation after reconnect restores autonomous dispatch");
   }
   ForwardScenario("investor-forward");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"investor guard book configured before permission revocation");
      fake_trade_allowed=false;
      Check(!Enter(book,ForwardTrade()) && !book.DispatchReady() && fake_sends==0,"Investor login cannot dispatch even with terminal Algo enabled and correct Demo identity");
   }
   ForwardScenario("stale-forward");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"stale quote forward book configured"); fake_now+=3;
      Check(!Enter(book,ForwardTrade()) && fake_sends==0 && book.Ready(),"stale real quote blocks entry without a permanent emergency");
   }
   ForwardScenario("margin-forward");
   {
      TLCoreTradeBook book; Check(ForwardBook(book),"margin forward book configured"); fake_margin_per_lot=20000;
      Check(!Enter(book,ForwardTrade()) && fake_sends==0 && book.Ready(),"margin utilization cap rejects unchanged pair before dispatch");
      fake_margin_per_lot=1000;
      Check(Enter(book,ForwardTrade("margin-new","M")) && fake_opens==2,"reconciled known non-submission permits another independent opportunity without retrying the rejected plan");
   }
   TL_FORWARD_DEMO=false; TL_DEMO_DAY_BALANCE=0; TL_DEMO_DAY_STOP=false;
   TL_TESTER_POLICY_MASK=0; TL_TESTER_DISCOVERY=0; TL_TESTER_M1_MAX_AGE_MINUTES=0; fake_magic=2026101603;
}

