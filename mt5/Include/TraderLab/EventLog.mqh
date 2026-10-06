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
      if(offset!=INT_MAX && tehran_offset!=INT_MAX) strategy_time=TLIso(server_time,offset-tehran_offset,millis);
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
