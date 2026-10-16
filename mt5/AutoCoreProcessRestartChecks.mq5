// Four genuine terminal processes. Only the injected EXTERNAL synthetic broker
// is snapshotted here; Core state must recover from its own production journals.
#define OnStart TLUnusedIntegrationSuite
#include "AutoCoreIntegrationChecks.mq5"
#undef OnStart

string backend_path="SYNTHETIC-EXTERNAL-BROKER.txt";
void SaveBroker()
{
   int f=FileOpen(backend_path,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   FileWriteString(f,"SYNTHETIC_BROKER_V1|"+(string)(long)fake_now+"|"+(string)fake_sends+"|"+(string)fake_opens+"|"+(string)fake_total_sends+"\r\n");
   MqlRates empty={}; FileWriteString(f,"Q|"+TLRecoveryInput("T",-1,1,1,fake_quote,empty)+"\r\n");
   for(int i=0;i<ArraySize(fake_positions);i++)
   {
      TLFakePosition p=fake_positions[i];
      FileWriteString(f,"P|"+(string)p.ticket+"|"+(string)p.magic+"|"+(string)(int)p.open+"|"+(string)(int)p.buy+"|"+
         TLRecoveryDouble(p.volume)+"|"+TLRecoveryDouble(p.price)+"|"+TLRecoveryDouble(p.sl)+"|"+TLRecoveryDouble(p.tp)+"|"+p.comment+"|"+(string)(long)p.at+"\r\n");
   }
   for(int i=0;i<ArraySize(fake_deals);i++)
   {
      TLFakeDeal d=fake_deals[i];
      FileWriteString(f,"D|"+(string)d.ticket+"|"+(string)d.position+"|"+(string)d.magic+"|"+(string)d.entry+"|"+(string)d.reason+"|"+
         TLRecoveryDouble(d.volume)+"|"+TLRecoveryDouble(d.price)+"|"+TLRecoveryDouble(d.profit)+"|"+TLRecoveryDouble(d.commission)+"|"+d.comment+"|"+(string)(long)d.at+"\r\n");
   }
   FileFlush(f); FileClose(f);
}
bool LoadBroker()
{
   FakeReset(); int file=FileOpen(backend_path,FILE_READ|FILE_TXT|FILE_ANSI,0,CP_UTF8); if(file==INVALID_HANDLE) return false;
   string f[],line=FileReadString(file);
   if(StringSplit(line,'|',f)!=5 || f[0]!="SYNTHETIC_BROKER_V1") { FileClose(file); return false; }
   fake_now=(datetime)StringToInteger(f[1]); fake_sends=(int)StringToInteger(f[2]); fake_opens=(int)StringToInteger(f[3]); fake_total_sends=(int)StringToInteger(f[4]);
   while(!FileIsEnding(file))
   {
      line=FileReadString(file); if(line=="") continue;
      int n=StringSplit(line,'|',f);
      if(f[0]=="Q")
      { string kind; int frame,ordinal; long index; MqlRates empty;
        if(!TLRecoveryParse(StringSubstr(line,2),kind,frame,index,ordinal,fake_quote,empty)) { FileClose(file); return false; } }
      else if(f[0]=="P" && n==11)
      {
         int p=ArraySize(fake_positions); ArrayResize(fake_positions,p+1);
         fake_positions[p].ticket=(ulong)StringToInteger(f[1]); fake_positions[p].magic=(ulong)StringToInteger(f[2]);
         fake_positions[p].open=StringToInteger(f[3])!=0; fake_positions[p].buy=StringToInteger(f[4])!=0;
         fake_positions[p].volume=StringToDouble(f[5]); fake_positions[p].price=StringToDouble(f[6]);
         fake_positions[p].sl=StringToDouble(f[7]); fake_positions[p].tp=StringToDouble(f[8]);
         fake_positions[p].comment=f[9]; fake_positions[p].at=(datetime)StringToInteger(f[10]);
      }
      else if(f[0]=="D" && n==12)
      {
         int d=ArraySize(fake_deals); ArrayResize(fake_deals,d+1);
         fake_deals[d].ticket=(ulong)StringToInteger(f[1]); fake_deals[d].position=(ulong)StringToInteger(f[2]); fake_deals[d].magic=(ulong)StringToInteger(f[3]);
         fake_deals[d].entry=StringToInteger(f[4]); fake_deals[d].reason=StringToInteger(f[5]);
         fake_deals[d].volume=StringToDouble(f[6]); fake_deals[d].price=StringToDouble(f[7]); fake_deals[d].profit=StringToDouble(f[8]);
         fake_deals[d].commission=StringToDouble(f[9]); fake_deals[d].comment=f[10]; fake_deals[d].at=(datetime)StringToInteger(f[11]);
      }
      else { FileClose(file); return false; }
   }
   FileClose(file); return true;
}
void ProcessPhase(const int phase)
{
   if(phase==1) { RecoveryPipeline(true); return; }
   Check(LoadBroker(),"external synthetic broker survives terminal VM teardown");
   TLAutoCoreNamespace("XAUUSD_o",fake_magic,0,run_token+"detector-restart");
   TLNativeRetestStream stream; TLTickCapture capture; TLEventLog silent;
   stream.Configure("XAUUSD_o",0); stream.ConfigureCore(fake_magic,fixture_calendar_path,120,"",false,3);
   stream.CoreExecutionLimits(1000,.22,0); stream.CoreTrialRiskLimits(30,1);
   Check(stream.OpenRecovery(capture,silent) && stream.CheckGroups()==1 && stream.CheckPending()==0,
         "fresh terminal process rebuilds frozen group and consumed return without a replayed order");
   Check(fake_opens==2,"no duplicate opening requests across physical process restart");
   if(phase==2)
   {
      Check(FakePositionsTotal()==2,"both authoritative external positions restored");
      long index=stream.CheckIndex(); MqlTick tick=fake_quote;
      FeedTick(stream,tick,index,2); stream.CoreFinishDrain(tick,tick,true,silent);
      Check(fake_opens==2,"same-ms occurrence after process restart cannot duplicate entry");
      FakeClose(0,DEAL_REASON_TP,5006.5); tick=fake_quote; FeedTick(stream,tick,index);
      stream.CoreService();
      Check(FakePositionsTotal()==1 && Near(fake_positions[1].sl,5001) && fake_sends==3,"TP1 and BE+5 complete after actual terminal relaunch");
   }
   if(phase==3)
   {
      stream.CoreService();
      Check(FakePositionsTotal()==1 && Near(fake_positions[1].sl,5001) && fake_sends==3,
            "another terminal process restores BE without another modification request");
      FakeClose(1,DEAL_REASON_TP,5010.5); long index=stream.CheckIndex(); MqlTick tick=fake_quote;
      FeedTick(stream,tick,index); stream.CoreService();
      Check(FakePositionsTotal()==0 && fake_opens==2,"TP2 exit after second physical restart leaves no exposure");
   }
   if(phase==4)
   {
      Check(FakePositionsTotal()==0 && fake_sends==3,"closed positions remain closed after physical restart");
      long index=stream.CheckIndex(); MqlTick tick=fake_quote; tick.time_msc++; tick.bid=5000.5; tick.ask=5000.6;
      FeedTick(stream,tick,index); stream.CoreFinishDrain(tick,tick,true,silent);
      Check(fake_opens==2 && FakePositionsTotal()==0 && fake_sends==3,"consumed setup cannot be resurrected in the fourth terminal process");
   }
}
void OnStart()
{
   run_token="PROCESS"; fixture_calendar_path="synthetic-calendar-PROCESS.csv";
   int phase=1;
   if(FileIsExist("SYNTHETIC-PROCESS-PHASE.txt"))
   { int f=FileOpen("SYNTHETIC-PROCESS-PHASE.txt",FILE_READ|FILE_TXT|FILE_ANSI); phase=(int)StringToInteger(FileReadString(f)); FileClose(f); }
   if(phase<1 || phase>4) Check(false,"invalid physical test phase"); else ProcessPhase(phase);
   if(failures==0)
   { SaveBroker(); int f=FileOpen("SYNTHETIC-PROCESS-PHASE.txt",FILE_WRITE|FILE_TXT|FILE_ANSI); FileWriteString(f,(string)(phase+1)); FileFlush(f); FileClose(f); }
   string result="{\"mode\":\"SYNTHETIC_PHYSICAL_TERMINAL_RESTART_NOT_HISTORICAL\",\"phase\":"+(string)phase+
      ",\"checks\":"+(string)checks+",\"failures\":"+(string)failures+",\"opening_requests_cumulative\":"+(string)fake_opens+
      ",\"synthetic_transport_requests_cumulative\":"+(string)fake_total_sends+",\"real_broker_orders\":0,\"failed_checks\":["+failed_names+"]}";
   int f=FileOpen("AutoCoreProcessRestartChecks-phase"+(string)phase+".json",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   FileWriteString(f,result+"\n"); FileFlush(f); FileClose(f); Print(result);
   if(StringFind(TerminalInfoString(TERMINAL_PATH),"offline-native")>=0) TerminalClose(failures==0?0:1);
}
