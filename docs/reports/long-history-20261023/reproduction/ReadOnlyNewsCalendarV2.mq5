#property strict
void OnStart()
{
 ulong end=GetTickCount64()+90000;while(!TerminalInfoInteger(TERMINAL_CONNECTED) && GetTickCount64()<end)Sleep(250);
 if(!TerminalInfoInteger(TERMINAL_CONNECTED) || AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)return;
 int f=FileOpen("ReadOnlyNewsCalendar-v2.jsonl",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_SHARE_READ,0,CP_UTF8);if(f==INVALID_HANDLE)return;
 FileWriteString(f,"{\"event\":\"CALENDAR_REQUEST\",\"from\":\"2025.10.01\",\"until_exclusive\":\"2026.10.24\",\"historical_asof_proven\":false,\"strategy_orders\":0}\r\n");FileFlush(f);
 MqlCalendarValue values[];ResetLastError();int n=CalendarValueHistory(values,D'2025.10.01',D'2026.10.24',"US","USD");int e=GetLastError();
 FileWriteString(f,"{\"event\":\"CALENDAR_RESPONSE\",\"count\":"+(string)n+",\"error\":"+(string)e+"}\r\n");FileFlush(f);
 for(int i=0;i<n;i++)
 {MqlCalendarEvent ev;if(!CalendarEventById(values[i].event_id,ev))continue;string name=ev.name;StringReplace(name,"\"","'");FileWriteString(f,"{\"event\":\"CALENDAR_VALUE\",\"event_id\":"+(string)values[i].event_id+",\"name\":\""+name+"\",\"event_code\":\""+ev.event_code+"\",\"server_time\":\""+TimeToString(values[i].time,TIME_DATE|TIME_MINUTES)+"\"}\r\n");FileFlush(f);}
 FileWriteString(f,"{\"event\":\"COMPLETE\",\"scope\":\"Raw historical metadata only. No strategy calendar constructed or approved.\"}\r\n");FileClose(f);
}
