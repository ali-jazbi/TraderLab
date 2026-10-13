#ifndef TRADERLAB_CORE_PACKAGES_MQH
#define TRADERLAB_CORE_PACKAGES_MQH
#include "Rules.mqh"
#include "DemoGateway.mqh"

// Explicit operator package membership; never automatic strategy discovery.
struct TLCorePackage
{
   string id,operator_name,evidence,fvg,ob,members;
   datetime approved,loaded;
};
bool TLCorePackageField(const string s)
{ return s!="" && StringFind(s,"|")<0 && StringFind(s,"\n")<0 && StringFind(s,"\r")<0; }
bool TLCorePackageRow(const string line,TLCorePackage &p)
{
   string f[]; if(StringSplit(line,'|',f)!=8 || f[0]!="PACKAGE") return false;
   for(int i=1;i<8;i++) if(!TLCorePackageField(f[i])) return false;
   p.id=f[1]; p.operator_name=f[2]; p.evidence=f[3]; p.approved=(datetime)StringToInteger(f[4]);
   p.fvg=f[5]; p.ob=f[6]; p.members=f[7]; p.loaded=0;
   if(!TLDemoId(p.id) || StringLen(p.id)>12 || p.approved<=0) return false;
   for(int i=0;i<StringLen(f[4]);i++) if(StringGetCharacter(f[4],i)<48 || StringGetCharacter(f[4],i)>57) return false;
   string ids[]; int n=StringSplit(p.members,';',ids); if(n<1) return false;
   for(int i=0;i<n;i++)
   { if(ids[i]=="") return false; for(int j=0;j<i;j++) if(ids[i]==ids[j]) return false; }
   return true;
}
bool TLCorePackageSame(const TLCorePackage &a,const TLCorePackage &b)
{
   return a.id==b.id && a.operator_name==b.operator_name && a.evidence==b.evidence &&
          a.approved==b.approved && a.fvg==b.fvg && a.ob==b.ob && a.members==b.members;
}
string TLCorePackageFingerprint(const TLCorePackage &p)
{
   string f[]={p.id,p.operator_name,p.evidence,(string)(long)p.approved,p.fvg,p.ob,p.members};
   string value=""; for(int i=0;i<7;i++) value+=(string)StringLen(f[i])+":"+f[i];
   return value;
}
bool TLCorePackageAvailable(const TLCorePackage &p,const long utc_msc)
{
   // Operator/file availability has second precision. No precise timestamp is invented.
   return utc_msc>((long)MathMax(p.approved,p.loaded)*1000+999);
}
bool TLCorePackageGeometry(const int side,const double &levels[],const double low,const double high,
                          const int fill,TLPlan &plan,string &reason)
{
   if(fill!=0) { reason=fill==1?"PARTIAL_NOT_APPROVED":"FULL_OR_UNKNOWN_FVG_INVALID"; return false; }
   if(high-low<20*TL_PIP-1e-8) { reason="FVG_BELOW_20_PIPS"; return false; }
   for(int i=0;i<ArraySize(levels);i++) if(levels[i]<low || levels[i]>high)
   { reason="BOS_WICK_OUTSIDE_FVG"; return false; }
   for(int i=0;i<ArraySize(levels);i++) for(int j=0;j<i;j++) if(levels[i]==levels[j])
   { reason="AMBIGUOUS_EQUAL_BOS_LEVELS"; return false; }
   return TLCoreLevelPlan(side,levels,plan,reason);
}
class TLCorePackages
{
private:
   TLCorePackage rows[],known[];
public:
   string error;
   int Count() { return ArraySize(rows); }
   bool Read(const int i,TLCorePackage &p) { if(i<0 || i>=Count()) return false; p=rows[i]; return true; }
   bool Load(const string path,const string symbol,const datetime now_utc)
   {
      ArrayResize(rows,0); error="";
      if(path=="") return true;
      int file=FileOpen(path,FILE_READ|FILE_TXT|FILE_ANSI,0,CP_UTF8);
      if(file==INVALID_HANDLE) { error="OPERATOR_PACKAGE_FILE_UNAVAILABLE"; return false; }
      string header=FileReadString(file);
      if(StringLen(header)>0 && StringGetCharacter(header,0)==65279) header=StringSubstr(header,1);
      if(header!="CORE_OPERATOR_PACKAGES_V1|"+symbol) { FileClose(file); error="OPERATOR_PACKAGE_SCOPE"; return false; }
      TLCorePackage next[];
      while(!FileIsEnding(file))
      {
         string line=FileReadString(file); if(line=="") continue;
         TLCorePackage p;
         if(!TLCorePackageRow(line,p)) { FileClose(file); error="OPERATOR_PACKAGE_MALFORMED"; return false; }
         p.loaded=now_utc;
         for(int i=0;i<ArraySize(known);i++) if(known[i].id==p.id)
         {
            if(!TLCorePackageSame(known[i],p)) { FileClose(file); error="OPERATOR_PACKAGE_MUTATED"; return false; }
            p.loaded=known[i].loaded;
         }
         string ids[]; StringSplit(p.members,';',ids);
         for(int i=0;i<ArraySize(next);i++)
         {
            if(next[i].id==p.id) { FileClose(file); error="OPERATOR_PACKAGE_DUPLICATE"; return false; }
            string other[]; StringSplit(next[i].members,';',other);
            for(int a=0;a<ArraySize(ids);a++) for(int b=0;b<ArraySize(other);b++) if(ids[a]==other[b])
            { FileClose(file); error="OPERATOR_BOS_MULTIPLE_PACKAGES"; return false; }
         }
         int n=ArraySize(next); ArrayResize(next,n+1); next[n]=p;
      }
      FileClose(file);
      ArrayResize(rows,ArraySize(next)); for(int i=0;i<ArraySize(next);i++) rows[i]=next[i];
      for(int i=0;i<Count();i++)
      {
         bool seen=false; for(int j=0;j<ArraySize(known);j++) if(known[j].id==rows[i].id) seen=true;
         if(!seen) { int n=ArraySize(known); ArrayResize(known,n+1); known[n]=rows[i]; }
      }
      return true;
   }
};
#endif
