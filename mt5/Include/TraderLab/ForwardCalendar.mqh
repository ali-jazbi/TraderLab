#ifndef TRADERLAB_FORWARD_CALENDAR_MQH
#define TRADERLAB_FORWARD_CALENDAR_MQH
// Native calendar transport. Python publisher validates source, time and IANA sessions.
// No HTTP scraper, synthetic dates, or historical availability claims.
bool TLForwardClock(int &offset)
{
   if(!TLDemoForwardIdentity() || !TerminalInfoInteger(TERMINAL_CONNECTED)) return false;
   long measured=(long)TimeTradeServer()-(long)TimeGMT();
   int rounded=(int)(MathRound((double)measured/900)*900);
   if(MathAbs(measured-rounded)>2 || MathAbs(rounded)>14*3600) return false;
   offset=rounded; return true;
}
void TLForwardCalendarRefresh()
{
   if(!TL_FORWARD_DEMO) return;
   static datetime last=0;
   datetime now=TimeGMT(); if(now-last<60) return; last=now;
   int offset=0; bool valid=TLForwardClock(offset);
   MqlCalendarValue values[]; int n=-1,error=0;
   if(valid) { ResetLastError(); n=CalendarValueHistory(values,now+offset-86400,now+offset+40*86400,"US","USD"); error=GetLastError(); }
   valid=valid && n>0 && error==0;
   string data="{\"observed_utc\":"+(string)(long)now+",\"server_offset\":"+(string)offset+
      ",\"valid\":"+(valid?"true":"false")+",\"error\":"+(string)error+",\"events\":[";
   int kept=0;
   for(int i=0;i<n;i++)
   {
      MqlCalendarEvent e; if(!CalendarEventById(values[i].event_id,e)) { valid=false; break; }
      string c=e.event_code;
      if(StringFind(c,"consumer-price-index")!=0 && c!="nonfarm-payrolls" && c!="fed-interest-rate-decision" &&
         c!="fomc-minutes" && c!="fomc-press-conference") continue;
      if(kept++>0) data+=",";
      data+="{\"code\":"+TLQuote(c)+",\"source\":"+TLQuote(e.source_url)+",\"server_time\":"+
         (string)(long)values[i].time+",\"time_mode\":"+(string)e.time_mode+"}";
   }
   data+="]}";
   if(!valid) data="{\"observed_utc\":"+(string)(long)now+",\"valid\":false,\"error\":"+(string)error+"}";
   int f=FileOpen("TraderLab-forward-native.tmp",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(f==INVALID_HANDLE) return;
   FileWriteString(f,data); FileFlush(f); FileClose(f);
   FileMove("TraderLab-forward-native.tmp",0,"TraderLab-forward-native.json",FILE_REWRITE);
}
#endif
