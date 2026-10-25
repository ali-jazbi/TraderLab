#property strict
void OnStart()
{
 ulong end=GetTickCount64()+90000;while(!TerminalInfoInteger(TERMINAL_CONNECTED) && GetTickCount64()<end)Sleep(250);
 if(!TerminalInfoInteger(TERMINAL_CONNECTED) || AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)return;
 int f=FileOpen("ServerHistoryMetadata.jsonl",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_SHARE_READ,0,CP_UTF8);if(f==INVALID_HANDLE)return;
 MqlTick tick;SymbolInfoTick("XAUUSD_o",tick);
 FileWriteString(f,"{\"event\":\"CURRENT_SERVER\",\"quote_time_msc\":"+(string)tick.time_msc+",\"time_current\":"+(string)TimeCurrent()+",\"time_trade_server\":"+(string)TimeTradeServer()+",\"terminal_build\":"+(string)TerminalInfoInteger(TERMINAL_BUILD)+",\"demo\":true,\"strategy_orders\":0}\r\n");FileFlush(f);
 ENUM_TIMEFRAMES frames[]={PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_H1,PERIOD_H4};
 for(int i=0;i<5;i++)
 {ResetLastError();long first=SeriesInfoInteger("XAUUSD_o",frames[i],SERIES_SERVER_FIRSTDATE);int e=GetLastError();FileWriteString(f,"{\"event\":\"SERVER_BAR_HISTORY_METADATA\",\"timeframe\":\""+EnumToString(frames[i])+"\",\"first_bar_epoch\":"+(string)first+",\"error\":"+(string)e+",\"not_tick_history_start\":true}\r\n");FileFlush(f);}
 FileWriteString(f,"{\"event\":\"COMPLETE\"}\r\n");FileClose(f);
}
