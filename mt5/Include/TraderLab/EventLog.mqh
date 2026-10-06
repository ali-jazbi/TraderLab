#ifndef TRADERLAB_EVENTLOG_MQH
#define TRADERLAB_EVENTLOG_MQH

string TLQuote(string value)
{
   StringReplace(value,"\\","\\\\");
   StringReplace(value,"\"","\\\"");
   StringReplace(value,"\r","\\r");
   StringReplace(value,"\n","\\n");
   StringReplace(value,"\t","\\t");
   return "\""+value+"\"";
}

string TLIso(const datetime server_time,const int offset,const int millis=0)
{
   if(offset==INT_MAX) return "null";
   string text=TimeToString(server_time-offset,TIME_DATE|TIME_SECONDS);
   StringReplace(text,".","-"); StringReplace(text," ","T");
   return TLQuote(text+StringFormat(".%03dZ",millis));
}

string TLServerIso(const datetime server_time,const int millis=0)
{
   string text=TimeToString(server_time,TIME_DATE|TIME_SECONDS);
   StringReplace(text,".","-"); StringReplace(text," ","T");
   return TLQuote(text+StringFormat(".%03d",millis));
}

string TLZonedIso(const datetime server_time,const int server_offset,const int zone_offset,const int millis=0)
{
   if(server_offset==INT_MAX || zone_offset==INT_MAX) return "null";
   string text=TimeToString(server_time-server_offset+zone_offset,TIME_DATE|TIME_SECONDS);
   StringReplace(text,".","-"); StringReplace(text," ","T");
   int absolute_offset=zone_offset<0 ? -zone_offset : zone_offset;
   string sign=zone_offset<0 ? "-" : "+";
   int hours=absolute_offset/3600;
   int minutes=(absolute_offset%3600)/60;
   int seconds=absolute_offset%60;
   string suffix=sign+StringFormat("%02d:%02d",hours,minutes);
   if(seconds>0) suffix+=StringFormat(":%02d",seconds);
   return TLQuote(text+StringFormat(".%03d",millis)+suffix);
}

class TLEventLog
{
private:
   int handle;
   long sequence;
   int offset;
   int tehran_offset;
public:
   TLEventLog() { handle=INVALID_HANDLE; sequence=0; offset=INT_MAX; tehran_offset=INT_MAX; }
   bool Open(const string name,const int server_offset,const int strategy_offset)
   {
      // Refuse overwriting an earlier capture. Caller supplies a new run file.
      if(FileIsExist(name)) { Print("TraderLab log already exists. Supply a new InpLogFile: ",name); return false; }
      // A read-only local publisher may tail this capture while the EA writes.
      handle=FileOpen(name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_SHARE_READ|FILE_SHARE_WRITE,0,CP_UTF8);
      offset=server_offset;
      tehran_offset=strategy_offset;
      return handle!=INVALID_HANDLE;
   }
   void Write(const string name,const string rule,const string details,const datetime server_time,const int millis=0)
   {
      if(handle==INVALID_HANDLE) return;
      sequence++;
      string strategy_time="null";
      if(offset!=INT_MAX && tehran_offset!=INT_MAX) strategy_time=TLZonedIso(server_time,offset,tehran_offset,millis);
      string row="{\"seq\":"+(string)sequence+",\"time\":"+TLIso(server_time,offset,millis)+
                 ",\"server_time\":"+TLServerIso(server_time,millis)+
                 ",\"server_utc_offset_seconds\":"+(offset==INT_MAX?"null":(string)offset)+
                 ",\"strategy_time\":"+strategy_time+
                 ",\"tehran_utc_offset_seconds\":"+(tehran_offset==INT_MAX?"null":(string)tehran_offset)+
                 ",\"spec_version\":\"0.1\",\"event\":"+TLQuote(name)+",\"rule\":"+TLQuote(rule);
      if(details!="") row+=","+details;
      row+="}\n";
      FileWriteString(handle,row); FileFlush(handle);
   }
   void Close() { if(handle!=INVALID_HANDLE) { FileClose(handle); handle=INVALID_HANDLE; } }
};

#endif
