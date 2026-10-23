#property strict
// Read-only data availability probe. No strategy, gateway or order transport.
void Save(const string body)
{
   int f=FileOpen("FinalDataInventory-result.json",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(f!=INVALID_HANDLE) { FileWriteString(f,body); FileClose(f); }
}
void OnStart()
{
   ulong deadline=GetTickCount64()+90000;
   while(!TerminalInfoInteger(TERMINAL_CONNECTED) && GetTickCount64()<deadline) Sleep(250);
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
   { Save("{\"status\":\"NOT_CONNECTED\",\"strategy_orders\":0}"); return; }
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
   { Save("{\"status\":\"REJECTED_NON_DEMO\",\"strategy_orders\":0}"); return; }
   string symbol="XAUUSD_o";
   if(!SymbolSelect(symbol,true))
   { Save("{\"status\":\"SYMBOL_UNAVAILABLE\",\"strategy_orders\":0}"); return; }
#ifdef TL_PROBE_GAP_DAY
   string days[]={"2026.10.16"};
#else
   string days[]={"2026.10.19","2026.10.20","2026.10.21","2026.10.22"};
#endif
   string rows="";
   for(int i=0;i<ArraySize(days);i++)
   {
      ulong start=(ulong)StringToTime(days[i]+" 00:00:00")*1000;
      ulong end=start+86400000-1;
      MqlTick ticks[];
      ResetLastError();
      int count=CopyTicksRange(symbol,ticks,COPY_TICKS_ALL,start,end);
      int error=GetLastError();
      long first=0,last=0;
      if(count>0) { first=ticks[0].time_msc; last=ticks[count-1].time_msc; }
      rows+=(rows==""?"":",")+"{\"server_day\":\""+days[i]+"\",\"requested_from_msc\":"+(string)start+
            ",\"requested_until_msc\":"+(string)end+",\"returned_ticks\":"+(string)count+
            ",\"error\":"+(string)error+",\"first_time_msc\":"+(string)first+",\"last_time_msc\":"+(string)last+"}";
      ArrayFree(ticks);
   }
   Save("{\"status\":\"PROBE_COMPLETE\",\"symbol\":\"XAUUSD_o\",\"demo_account\":true,\"strategy_orders\":0,"
        "\"scope\":\"History availability only; not a completed real-tick backtest or proof of complete coverage\",\"days\":["+rows+"]}");
}
