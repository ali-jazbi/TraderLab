#ifndef TRADERLAB_RECOVERY_JOURNAL_MQH
#define TRADERLAB_RECOVERY_JOURNAL_MQH
// Append-only write-ahead input journal. Not a historical-performance dataset.
// Every frame is length + chained FNV checksum + UTF8 payload + commit marker.
// Torn frames, changed scope and a second writer fail closed; nothing is deleted.
uint TLRecoveryHash(const string text,uint hash=2166136261)
{
   uchar bytes[]; int n=StringToCharArray(text,bytes,0,WHOLE_ARRAY,CP_UTF8);
   for(int i=0;i<n-1;i++) { hash^=bytes[i]; hash*=16777619; }
   return hash;
}
// Narrow, operator-run repair receipt for the reproduced restart defect only.
// This is never an emergency-stop reset button or permission to retry an order.
bool TLRecoveryTechnicalResume(const string reason,const string revision)
{
   if(reason!="invalid_asof_closed_bar" || StringLen(revision)!=64) return false;
   for(int i=0;i<64;i++) { ushort c=StringGetCharacter(revision,i);
      if(!((c>=48 && c<=57) || (c>=97 && c<=102))) return false; }
   return true;
}
string TLRecoveryDouble(const double n) { return StringFormat("%.17g",n); }
string TLRecoveryInput(const string kind,const int frame,const long index,const int ordinal,
                       const MqlTick &tick,const MqlRates &bar)
{
   return kind+"|"+(string)frame+"|"+(string)index+"|"+(string)ordinal+"|"+(string)tick.time_msc+
      "|"+TLRecoveryDouble(tick.bid)+"|"+TLRecoveryDouble(tick.ask)+"|"+TLRecoveryDouble(tick.last)+
      "|"+(string)tick.volume+"|"+(string)tick.flags+"|"+TLRecoveryDouble(tick.volume_real)+
      "|"+(string)(long)bar.time+"|"+TLRecoveryDouble(bar.open)+"|"+TLRecoveryDouble(bar.high)+
      "|"+TLRecoveryDouble(bar.low)+"|"+TLRecoveryDouble(bar.close)+"|"+(string)bar.tick_volume+
      "|"+(string)bar.spread+"|"+(string)bar.real_volume;
}
bool TLRecoveryParse(const string row,string &kind,int &frame,long &index,int &ordinal,MqlTick &tick,MqlRates &bar)
{
   string f[]; if(StringSplit(row,'|',f)!=19) return false;
   kind=f[0]; frame=(int)StringToInteger(f[1]); index=StringToInteger(f[2]); ordinal=(int)StringToInteger(f[3]);
   ZeroMemory(tick); ZeroMemory(bar);
   tick.time_msc=StringToInteger(f[4]); tick.time=(datetime)(tick.time_msc/1000);
   tick.bid=StringToDouble(f[5]); tick.ask=StringToDouble(f[6]); tick.last=StringToDouble(f[7]);
   tick.volume=(ulong)StringToInteger(f[8]); tick.flags=(uint)StringToInteger(f[9]); tick.volume_real=StringToDouble(f[10]);
   bar.time=(datetime)StringToInteger(f[11]); bar.open=StringToDouble(f[12]); bar.high=StringToDouble(f[13]);
   bar.low=StringToDouble(f[14]); bar.close=StringToDouble(f[15]); bar.tick_volume=StringToInteger(f[16]);
   bar.spread=(int)StringToInteger(f[17]); bar.real_volume=StringToInteger(f[18]);
   if((kind!="Z" && kind!="T" && kind!="B") || tick.time_msc<=0 || tick.bid<=0 || tick.ask<tick.bid ||
      !MathIsValidNumber(tick.bid) || !MathIsValidNumber(tick.ask) || !MathIsValidNumber(tick.last) ||
      !MathIsValidNumber(tick.volume_real) || index<0 || (kind=="T" && (index==0 || ordinal<1)) ||
      (kind=="Z" && index!=0) || (kind=="B" && (frame<0 || frame>4 || bar.time<=0))) return false;
   return TLRecoveryInput(kind,frame,index,ordinal,tick,bar)==row; // reject numeric suffixes/NaN/overflow
}
class TLRecoveryJournal
{
private:
   int file;
   uint chain;
   bool writable,failed;
   string revision;
public:
   string error;
   string Revision() { return revision; }
   uint Chain() { return chain; }
   TLRecoveryJournal() { file=INVALID_HANDLE; chain=2166136261; writable=false; failed=false; error=""; revision=""; }
   ~TLRecoveryJournal() { Close(); }
   void Close() { if(file!=INVALID_HANDLE) FileClose(file); file=INVALID_HANDLE; writable=false; }
   bool Append(const string payload)
   {
      if(file==INVALID_HANDLE || !writable || failed) return false;
      uchar bytes[]; int count=StringToCharArray(payload,bytes,0,WHOLE_ARRAY,CP_UTF8)-1;
      if(count<1 || count>16384) return false;
      uint next=TLRecoveryHash(payload,chain);
      ResetLastError();
      bool ok=FileWriteInteger(file,count,INT_VALUE)==4 && FileWriteInteger(file,(int)next,INT_VALUE)==4 &&
         FileWriteArray(file,bytes,0,count)==(uint)count && FileWriteInteger(file,0x41434A31,INT_VALUE)==4;
      FileFlush(file);
      if(!ok || GetLastError()!=0) { failed=true; error="RECOVERY_JOURNAL_WRITE_FAILED"; return false; }
      chain=next; return true;
   }
   // 1 record, 0 validated EOF, -1 malformed/torn/read error.
   int Next(string &payload)
   {
      if(file==INVALID_HANDLE || failed) return -1;
      long left=(long)(FileSize(file)-FileTell(file));
      if(left==0) { writable=true; return 0; }
      if(left<12) { failed=true; error="RECOVERY_TORN_FRAME"; return -1; }
      ResetLastError(); int count=FileReadInteger(file,INT_VALUE); uint expected=(uint)FileReadInteger(file,INT_VALUE);
      if(count<1 || count>16384 || left<12+count) { failed=true; error="RECOVERY_INVALID_FRAME_LENGTH"; return -1; }
      uchar bytes[]; ArrayResize(bytes,count);
      if(FileReadArray(file,bytes,0,count)!=(uint)count || FileReadInteger(file,INT_VALUE)!=0x41434A31 || GetLastError()!=0)
      { failed=true; error="RECOVERY_TORN_COMMIT"; return -1; }
      payload=CharArrayToString(bytes,0,count,CP_UTF8);
      uint actual=TLRecoveryHash(payload,chain);
      if(actual!=expected) { failed=true; error="RECOVERY_CHECKSUM_OR_ORDER_MISMATCH"; return -1; }
      chain=actual; return 1;
   }
   // Explicit offline repair retains the original frames. Validate the WHOLE
   // chain before choosing a committed authoritative-history replay revision.
   // Incomplete revisions never fall back to the old state or move a cursor.
   bool SelectReplay()
   {
      long start=(long)FileTell(file),selected=start; uint initial=chain,selected_chain=chain;
      string row,pending=""; int result;
      revision="";
      while((result=Next(row))==1)
      {
         if(StringFind(row,"HISTORY_REBUILD_BEGIN|")==0)
         {
            string id=StringSubstr(row,22);
            if(pending!="" || StringLen(id)!=64) { error="RECOVERY_INVALID_REBUILD_BEGIN"; return false; }
            pending=id; selected=(long)FileTell(file); selected_chain=chain;
         }
         else if(StringFind(row,"HISTORY_REBUILD_COMMIT|")==0)
         {
            if(pending=="" || StringSubstr(row,23)!=pending) { error="RECOVERY_INVALID_REBUILD_COMMIT"; return false; }
            revision=pending; pending="";
         }
      }
      if(result<0) return false;
      if(pending!="") { failed=true; error="RECOVERY_UNCOMMITTED_HISTORY_REBUILD"; return false; }
      if(revision=="") { selected=start; selected_chain=initial; }
      writable=false; chain=selected_chain;
      return FileSeek(file,selected,SEEK_SET);
   }
   bool Open(const string path,const string scope,const bool common=false)
   {
      if(file!=INVALID_HANDLE || scope=="" || StringFind(scope,"\n")>=0 || StringFind(scope,"\r")>=0) return false;
      file=FileOpen(path,FILE_READ|FILE_WRITE|FILE_BIN|(common?FILE_COMMON:0));
      if(file==INVALID_HANDLE) { error="RECOVERY_JOURNAL_LOCKED_OR_UNAVAILABLE"; return false; }
      string header="AUTO_CORE_INPUT_V1|"+scope;
      if(FileSize(file)==0) { writable=true; if(!Append(header)) return false; }
      FileSeek(file,0,SEEK_SET); chain=2166136261; writable=false;
      string stored; if(Next(stored)!=1 || stored!=header) { failed=true; error="RECOVERY_SCOPE_OR_VERSION_MISMATCH"; return false; }
      return true;
   }
};
#endif
