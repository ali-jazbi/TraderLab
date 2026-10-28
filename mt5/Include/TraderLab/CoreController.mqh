#ifndef TRADERLAB_CORE_CONTROLLER_MQH
#define TRADERLAB_CORE_CONTROLLER_MQH
#include "Detection.mqh"
#include "CoreEligibility.mqh"
#include "CoreLifecycle.mqh"
#include "CorePackages.mqh"
#include "RecoveryJournal.mqh"

string TLCoreFillName(const int value) { return value==2?"FULL":value==1?"PARTIAL":"UNFILLED"; }
bool TLCoreField(const string value)
{ return value!="" && StringFind(value,"|")<0 && StringFind(value,"\n")<0 && StringFind(value,"\r")<0; }

// A truncated/unavailable journal blocks execution; touch is never reset.
class TLCoreConsumption
{
private:
   int file;
   bool ready,stopped;
   string ids[];
   string package_ids[],package_payloads[];
   bool Load(const string path,const string scope,const bool common)
   {
      bool technical_only=false;
      if(file!=INVALID_HANDLE) return false;
      file=FileOpen(path,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|(common?FILE_COMMON:0),'|',CP_UTF8);
      if(file==INVALID_HANDLE) return false;
      if(FileSize(file)==0)
      { ResetLastError(); uint n=FileWrite(file,"SCOPE",scope); FileFlush(file); if(n==0 || GetLastError()!=0) return false; }
      else
      {
         if(FileReadString(file)!="SCOPE" || FileReadString(file)!=scope) return false;
         while(!FileIsEnding(file))
         {
            string kind=FileReadString(file); if(kind=="" && FileIsEnding(file)) break;
            string id=FileReadString(file),value=FileReadString(file);
            if(!TLCoreField(id)) return false;
            if(kind=="RETURN")
            {
               if(StringToInteger(value)<=0) return false;
               if(!Seen(id)) { int n=ArraySize(ids); ArrayResize(ids,n+1); ids[n]=id; }
            }
            else if(kind=="PACKAGE")
            {
               if(!TLCoreField(value)) return false;
               for(int i=0;i<ArraySize(package_ids);i++) if(package_ids[i]==id && package_payloads[i]!=value) return false;
               int n=ArraySize(package_ids); ArrayResize(package_ids,n+1); ArrayResize(package_payloads,n+1);
               package_ids[n]=id; package_payloads[n]=value;
            }
            else if(kind=="HALT")
            { if(!TLCoreEpoch(value)) return false;
              technical_only=(!stopped || technical_only) && id=="invalid_asof_closed_bar"; stopped=true; }
            else if(kind=="RESUME")
            {
               if(!stopped || !technical_only || !TLRecoveryTechnicalResume(id,value)) return false;
               stopped=false; technical_only=false;
            }
            else return false;
         }
      }
      ready=FileSeek(file,0,SEEK_END); return ready;
   }
public:
   TLCoreConsumption() { file=INVALID_HANDLE; ready=false; stopped=false; }
   ~TLCoreConsumption() { if(file!=INVALID_HANDLE) FileClose(file); }
   bool Seen(const string id) { for(int i=0;i<ArraySize(ids);i++) if(ids[i]==id) return true; return false; }
   bool Open(const string symbol,const ulong magic)
   {
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      if(magic==0 || !TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE))) return false;
      return Load(TLAutoCoreJournalPath("consumed"),TL_AUTO_CORE_SCOPE,!MQLInfoInteger(MQL_TESTER));
#else
      if(MQLInfoInteger(MQL_TESTER) || magic==0 || !TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE))) return false;
      string server=AccountInfoString(ACCOUNT_SERVER),safe=server;
      for(int c=0;c<StringLen(safe);c++) { ushort v=StringGetCharacter(safe,c); if(!((v>=48&&v<=57)||(v>=65&&v<=90)||(v>=97&&v<=122))) StringSetCharacter(safe,c,'_'); }
      return Load("TraderLab-core-consumed-"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+"-"+safe+".csv",
                  (string)AccountInfoInteger(ACCOUNT_LOGIN)+":"+server+":"+symbol+":"+(string)magic,true);
#endif
   }
#ifdef TRADERLAB_CORE_CHECKS
   // Available only in the reducer-check script; never uses production FILE_COMMON.
   bool OpenFixture(const string path,const string scope) { return Load(path,scope,false); }
#endif
   bool Consume(const string id,const long msc)
   {
      if(!ready || file==INVALID_HANDLE || !TLCoreField(id) || msc<=0) return false;
      if(Seen(id)) return true;
      ResetLastError(); uint written=FileWrite(file,"RETURN",id,msc); FileFlush(file);
      if(written==0 || GetLastError()!=0) return false;
      int n=ArraySize(ids); ArrayResize(ids,n+1); ids[n]=id; return true;
   }
   bool FreezePackage(const string id,const string payload)
   {
      if(!ready || !TLCoreField(id) || !TLCoreField(payload)) return false;
      for(int i=0;i<ArraySize(package_ids);i++) if(package_ids[i]==id) return package_payloads[i]==payload;
      ResetLastError(); uint n=FileWrite(file,"PACKAGE",id,payload); FileFlush(file);
      if(n==0 || GetLastError()!=0) return false;
      int size=ArraySize(package_ids); ArrayResize(package_ids,size+1); ArrayResize(package_payloads,size+1);
      package_ids[size]=id; package_payloads[size]=payload; return true;
   }
   bool Halted() { return stopped; }
   bool Stop(const string reason,const datetime now)
   {
      if(!ready || !TLCoreField(reason) || now<=0) return false;
      if(stopped) return true;
      ResetLastError(); uint n=FileWrite(file,"HALT",reason,(long)now); FileFlush(file);
      if(n==0 || GetLastError()!=0) { ready=false; return false; }
      stopped=true; return true;
   }
};
struct TLCoreBos
{
   string id;
   int frame,tracker_id;
   bool startup;
   TLBosHistory history;
   TLFirstReturn study_return; // Independent experiment, never resets canonical lanes.
   bool study_armed;
   long study_arm_msc;
};
struct TLCoreGap { string id; int frame,fill_before_tick; long before_tick_index,fill_tick_index; TLDetectedGap value; };
struct TLCorePair { int bos,gap; bool return_reported; };
struct TLCorePending { TLCoreTrade trade; int bos,gap,fvg_permission; long index; bool persisted; };
struct TLExperimentalGroup { int gap; string members; TLPlan plan; long index,msc; };

class TLCoreController
{
private:
   TLBarDetector detectors[5];
   string names[5],symbol;
   TLCoreBos bos[];
   TLCoreGap gaps[];
   TLCorePair pairs[];
   TLCoreTradeBook book;
   TLCoreConsumption consumption;
   TLCorePackages packages;
   TLCorePending pending[];
   string package_file,approved_ids[],last_package_error;
   long operator_returns;
   int offset;
   bool halted,durable,recovering;
   int experiment,next_group_gap;
   long experimental_rejected;
   TLExperimentalGroup experimental_groups[];
   int study_active[];
   long last_index,last_msc;
   int panel_gap,panel_bos;
   string panel_members,panel_message,panel_preview;
   bool panel_enabled;
   TLCoreEligibility Eligibility(const int g,const long cutoff,const string scope="")
   {
      TLEligibilityBos evidence[];
      for(int b=0;b<ArraySize(bos);b++)
      {
         if(scope!="" && StringFind(";"+scope+";",";"+bos[b].id+";")<0) continue;
         if(scope=="" && experiment!=2 && bos[b].frame!=gaps[g].frame) continue;
         TLBosHistory h=bos[b].history;
         int n=ArraySize(evidence); ArrayResize(evidence,n+1);
         evidence[n].id=bos[b].id; evidence[n].opened=h.opened; evidence[n].side=h.side;
         evidence[n].qualified_msc=h.qualified_msc; evidence[n].level=h.side==1?h.high:h.low;
      }
      return TLCheckCoreEligibility(gaps[g].value,evidence,cutoff);
   }
   void ExperimentalFinalize(const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(experiment==0 || !TLPolicyActive()) return;
      while(next_group_gap<ArraySize(gaps))
      {
         int g=next_group_gap++; TLDetectedGap v=gaps[g].value;
         TLCoreEligibility eligibility=Eligibility(g,v.available_msc);
         double levels[]; int members[]; string ids="",aliases="",reason=""; TLPlan plan; ZeroMemory(plan);
         for(int b=0;b<ArraySize(bos);b++)
         {
            TLBosHistory h=bos[b].history; double level=h.side==1?h.high:h.low;
            if(h.side!=v.side || h.qualified_msc<=0 || h.qualified_msc>v.available_msc ||
               level<v.low || level>v.high || (experiment!=2 && bos[b].frame!=gaps[g].frame)) continue;
            if(TLDiscoveryStudy())
            {
               if(TL_TESTER_DISCOVERY!=3 && h.lanes[0].returns[0].consumed) continue;
               if(TL_TESTER_DISCOVERY>=2 && (h.lanes[0].break_msc<(long)v.candidate*1000 ||
                  h.lanes[0].break_msc>=v.impulse_end_msc)) continue;
               if(TL_TESTER_DISCOVERY==3 && bos[b].study_return.consumed) continue;
            }
            aliases+=(aliases==""?"":";")+bos[b].id;
            int duplicate=-1;
            if(experiment==3) for(int j=0;j<ArraySize(levels);j++) if(levels[j]==level) { duplicate=j; break; }
            if(duplicate>=0)
            {
               int old=members[duplicate]; TLBosHistory prior=bos[old].history;
               if(h.qualified_msc<prior.qualified_msc || (h.qualified_msc==prior.qualified_msc &&
                  (h.opened<prior.opened || (h.opened==prior.opened && StringCompare(bos[b].id,bos[old].id)<0))))
                  members[duplicate]=b;
               continue;
            }
            int n=ArraySize(levels); ArrayResize(levels,n+1); ArrayResize(members,n+1);
            levels[n]=level; members[n]=b;
         }
         string selected="",consumed_ids=""; int fresh_selected=0;
         for(int i=0;i<ArraySize(members);i++) ids+=(ids==""?"":";")+bos[members[i]].id;
         if(!eligibility.eligible) reason=eligibility.reason;
         else if(ArraySize(levels)==0) reason="NO_QUALIFIED_CONTAINED_BOS_AT_CONFIRMATION";
         else if(!TLCorePackageGeometry(v.side,levels,v.low,v.high,(v.fill==1 && TLStudyPolicy(2))?0:v.fill,plan,reason)) {}
         else if(plan.count==1 && !TLDiscoveryStudy()) reason="SINGLE_BE_ANCHOR_UNRESOLVED";
         else for(int i=0;i<ArraySize(members);i++)
         {
            int b=members[i]; double entry=TLCoreEntryReference(v.side,levels[i]);
            if(entry!=plan.entry1 && (plan.count!=2 || entry!=plan.entry2)) continue;
            selected+=(selected==""?"":";")+bos[b].id;
            if(bos[b].history.lanes[0].returns[0].consumed) consumed_ids+=(consumed_ids==""?"":";")+bos[b].id;
            if(!bos[b].history.lanes[0].returns[0].consumed || (TLDiscoveryStudy() && TL_TESTER_DISCOVERY==3)) fresh_selected++;
            if(bos[b].startup) reason="STARTUP_HISTORY_NOT_EXECUTION_PROOF";
            else if(!TLStudyMemberAvailable(bos[b].history.lanes[0].returns[0].consumed)) reason="FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION";
         }
         if(reason=="" && fresh_selected==0) reason="ALL_SELECTED_BOS_ALREADY_CONSUMED";
         bool accepted=reason=="";
         if(accepted)
         { int n=ArraySize(experimental_groups); ArrayResize(experimental_groups,n+1);
           experimental_groups[n].gap=g; experimental_groups[n].members=ids;
           experimental_groups[n].plan=plan; experimental_groups[n].index=index; experimental_groups[n].msc=tick.time_msc; }
         else experimental_rejected++;
         if(accepted && TLDiscoveryStudy() && TL_TESTER_DISCOVERY==3) for(int i=0;i<ArraySize(members);i++)
         {
            int b=members[i]; double entry=TLCoreEntryReference(v.side,levels[i]);
            if(entry!=plan.entry1 && (plan.count!=2 || entry!=plan.entry2)) continue;
            if(!bos[b].study_armed)
            { ZeroMemory(bos[b].study_return); bos[b].study_armed=true; bos[b].study_arm_msc=tick.time_msc;
              int a=ArraySize(study_active); ArrayResize(study_active,a+1); study_active[a]=b; }
         }
         log.Write("EXPERIMENTAL_GROUP_FINALIZED","EXPERIMENTAL_NOT_OWNER_CONFIRMED",
                   "\"fvg_id\":"+TLQuote(gaps[g].id)+",\"ob_id\":"+TLQuote(gaps[g].id+(v.side==1?":C3":":C1"))+
                   ",\"members\":"+TLQuote(ids)+",\"all_geometric_members\":"+TLQuote(aliases)+
                   ",\"selected_bos_ids\":"+TLQuote(selected)+",\"frozen_at\":"+TLMscIso(v.available_msc,offset)+
                   ",\"consumed_selected_ids\":"+TLQuote(consumed_ids)+",\"fresh_selected_count\":"+(string)fresh_selected+
                   ",\"entry1\":"+DoubleToString(plan.entry1,8)+",\"entry2\":"+DoubleToString(plan.entry2,8)+
                   ",\"entry1_outside_fvg_interior\":"+(plan.count>0 && (v.side==1?plan.entry1>=v.high:plan.entry1<=v.low)?"true":"false")+
                   ",\"entry2_outside_fvg_interior\":"+(plan.count==2 && (v.side==1?plan.entry2>=v.high:plan.entry2<=v.low)?"true":"false")+
                   ",\"policy\":"+TLQuote(experiment==3?"same_frame_earliest_qualified_equal_level_v1":experiment==1?"same_frame_at_confirmed_availability":"all_frames_at_confirmed_availability")+
                   ",\"policy_mask\":"+(string)TL_TESTER_POLICY_MASK+",\"fill_at_confirmation\":"+TLQuote(TLCoreFillName(v.fill))+
                   ",\"accepted\":"+(accepted?"true":"false")+",\"reason\":"+TLQuote(reason)+
                   ",\"discovery_policy\":"+TLQuote(TLDiscoveryName())+",\"state\":"+TLQuote(accepted?"STRUCTURAL_VALID":"BLOCKED")+
                   ",\"tick_index\":"+(string)index+",\"demo_execution_approved\":false",tick.time,(int)(tick.time_msc%1000));
      }
   }
   void ExperimentalReturn(const int b,const MqlTick &tick,const long index,TLEventLog &log,const bool armed=false)
   {
      if(recovering || experiment==0 || !TLPolicyActive()) return;
      TLFirstReturn r=bos[b].history.lanes[0].returns[0];
      if(armed) r=bos[b].study_return;
      bool age_allowed=TLTesterBosAgeAllowed(bos[b].frame,bos[b].history.opened,tick.time_msc);
      double entry=TLCoreEntryReference(bos[b].history.side,bos[b].history.side==1?bos[b].history.high:bos[b].history.low);
      int chosen=-1,matches=0,selected_groups=0,blocked_fill=-1,permission=0; string related="",reason="NO_ACTIVE_EXPERIMENTAL_GROUP";
      for(int i=0;i<ArraySize(experimental_groups);i++)
      {
         TLExperimentalGroup p=experimental_groups[i]; string ids[]; StringSplit(p.members,';',ids);
         bool member=false; for(int j=0;j<ArraySize(ids);j++) if(ids[j]==bos[b].id) member=true;
         if(member && (entry==p.plan.entry1 || (p.plan.count==2 && entry==p.plan.entry2)))
         {
            selected_groups++; related+=(related==""?"":";")+gaps[p.gap].id;
            blocked_fill=(int)MathMax(blocked_fill,gaps[p.gap].value.fill);
            TLCoreGap gap=gaps[p.gap]; int proof=0;
            if(gap.value.fill==1 && TLStudyPolicy(2)) proof=3;
            if(TLFirstTouchEnabled() && gap.value.fill==1 && gap.fill_tick_index==index)
            {
               if(gap.fill_before_tick==0) proof=1;
               else if(TL_TESTER_SECOND_EXTREME==1 && gap.fill_before_tick==1 &&
                       book.HasExecutedSetup("EXPERIMENTAL:"+gap.id)) proof=2;
            }
            if(gap.value.fill==0 || TLExperimentalFvgPermission(proof)) { chosen=i; matches++; permission=proof; }
         }
      }
      if(matches==0 && selected_groups>0) reason=blocked_fill==2?"FVG_FULL_AT_FIRST_RETURN":"PARTIAL_NOT_APPROVED_AT_FIRST_RETURN";
      if(matches>1) reason="AMBIGUOUS_MULTIPLE_FVG_PACKAGES_NO_ARBITRARY_SELECTION";
      else if(matches==1)
      {
         TLExperimentalGroup p=experimental_groups[chosen];
         if(!r.exact && !TLStudyCrossing(bos[b].history.side==1,entry,tick.bid,tick.ask)) reason="MISSED_EXACT_FIRST_RETURN_OR_CROSSING_OVER_5_PIPS";
         else if(tick.time<TL_TESTER_EXECUTION_FROM) reason="TESTER_WARMUP_RETURN_CONSUMED_NO_ORDER";
         else if(TLCoreBeforeAvailability(r.return_msc,r.return_index,p.msc,p.index)) reason="RETURN_BEFORE_GROUP_AVAILABILITY";
         else if(!age_allowed) reason="EXPERIMENTAL_M1_BOS_AGE_AT_FIRST_RETURN";
         else
         {
            TLCorePending v; ZeroMemory(v); v.bos=b; v.gap=p.gap; v.index=index; v.persisted=true;
            v.fvg_permission=permission;
            int rank=entry==p.plan.entry1?0:1;
            v.trade.setup="EXPERIMENTAL:"+gaps[p.gap].id; v.trade.side=bos[b].history.side;
            v.trade.single=p.plan.count==1; v.trade.be_known=true; v.trade.be_actual=TLDiscoveryStudy(); v.trade.reference=p.plan.reference;
            v.trade.planned=entry; v.trade.shared_stop=p.plan.stop;
            v.trade.id1="EX"+(string)p.gap+(string)rank+"1"; v.trade.id2="EX"+(string)p.gap+(string)rank+"2";
            int n=ArraySize(pending); ArrayResize(pending,n+1); pending[n]=v;
            reason="AWAIT_CURRENT_TESTER_QUOTE_AND_STRATEGY_GUARDS";
         }
      }
      log.Write("EXPERIMENTAL_FIRST_RETURN","EXPERIMENTAL_NOT_OWNER_CONFIRMED",
                "\"bos_id\":"+TLQuote(bos[b].id)+",\"matches\":"+(string)matches+
                ",\"m1_max_age_minutes\":"+(string)TL_TESTER_M1_MAX_AGE_MINUTES+
                ",\"bos_age_ms\":"+(string)(tick.time_msc-(long)bos[b].history.opened*1000)+
                ",\"age_allowed\":"+(age_allowed?"true":"false")+
                ",\"selected_groups\":"+(string)selected_groups+",\"related_fvg_ids\":"+TLQuote(related)+
                ",\"fill_after_tick\":"+TLQuote(blocked_fill<0?"NO_SELECTED_GROUP":TLCoreFillName(blocked_fill))+
                ",\"policy_mask\":"+(string)TL_TESTER_POLICY_MASK+
                ",\"exact_quote\":"+(r.exact?"true":"false")+",\"reason\":"+TLQuote(reason)+
                ",\"discovery_policy\":"+TLQuote(TLDiscoveryName())+",\"signal_ready\":"+(reason=="AWAIT_CURRENT_TESTER_QUOTE_AND_STRATEGY_GUARDS"?"true":"false")+
                ",\"fvg_policy\":"+TLQuote(TLFirstTouchEnabled()?"EXPERIMENTAL_FIRST_TOUCH":"STRICT_ORIGINAL")+
                ",\"permission\":"+TLQuote(TLFvgPermissionName(permission))+",\"second_extreme_policy\":"+(string)TL_TESTER_SECOND_EXTREME+
                ",\"tick_index\":"+(string)index+",\"demo_execution_approved\":false",tick.time,(int)(tick.time_msc%1000));
   }
   void PanelControl(const string id,const string caption,const int x,const int y,const int width,const bool edit=false)
   {
      string name="TLCore."+id;
      if(ObjectFind(0,name)>=0) return;
      ObjectCreate(0,name,edit?OBJ_EDIT:OBJ_BUTTON,0,0,0);
      ObjectSetInteger(0,name,OBJPROP_XDISTANCE,x); ObjectSetInteger(0,name,OBJPROP_YDISTANCE,y);
      ObjectSetInteger(0,name,OBJPROP_XSIZE,width); ObjectSetInteger(0,name,OBJPROP_YSIZE,24);
      ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_LOWER);
      ObjectSetInteger(0,name,OBJPROP_FONTSIZE,9);
      ObjectSetInteger(0,name,OBJPROP_COLOR,clrBlack); ObjectSetInteger(0,name,OBJPROP_BGCOLOR,clrWhiteSmoke);
      ObjectSetString(0,name,OBJPROP_TEXT,caption);
   }
   int PanelBosCount(int &members[])
   {
      ArrayResize(members,0);
      for(int i=0;i<ArraySize(pairs);i++) if(pairs[i].gap==panel_gap)
      { int n=ArraySize(members); ArrayResize(members,n+1); members[n]=pairs[i].bos; }
      return ArraySize(members);
   }
   bool PanelDraft(TLCorePackage &p,TLPlan &plan,string &reason)
   {
      if(panel_gap<0 || panel_gap>=ArraySize(gaps) || panel_members=="") { reason="Select FVG and complete BOS membership"; return false; }
      if(offset==INT_MAX || MQLInfoInteger(MQL_TESTER) || !TLDemoAccount(AccountInfoInteger(ACCOUNT_TRADE_MODE)))
      { reason="Live DEMO and explicit UTC offset required"; return false; }
      p.id=(string)(long)TimeGMT()+StringFormat("%c%c",65+packages.Count()/26,65+packages.Count()%26);
      p.operator_name=ObjectGetString(0,"TLCore.operator",OBJPROP_TEXT);
      p.evidence=ObjectGetString(0,"TLCore.evidence",OBJPROP_TEXT);
      p.approved=TimeGMT(); p.loaded=p.approved; p.fvg=gaps[panel_gap].id;
      p.ob=p.fvg+(gaps[panel_gap].value.side==1?":C3":":C1"); p.members=panel_members;
      if(!TLCorePackageField(p.operator_name) || !TLCorePackageField(p.evidence) || StringLen(p.id)>12)
      { reason="Enter operator name and chart review evidence"; return false; }
      int gap;
      if(!Resolve(p,plan,gap,reason)) return false;
      if(plan.count==1) { reason="Single BE anchor unresolved; approve a canonical dual package"; return false; }
      string ids[]; StringSplit(p.members,';',ids);
      for(int i=0;i<ArraySize(ids);i++) if(consumption.Seen(ids[i]))
      { reason="BOS already consumed in durable journal"; return false; }
      reason=""; return true;
   }
   int BosIndex(const string id) { for(int i=0;i<ArraySize(bos);i++) if(bos[i].id==id) return i; return -1; }
   int GapIndex(const string id) { for(int i=0;i<ArraySize(gaps);i++) if(gaps[i].id==id) return i; return -1; }
   bool Resolve(const TLCorePackage &p,TLPlan &plan,int &gap,string &reason)
   {
      gap=GapIndex(p.fvg); reason="OPERATOR_IDS_NOT_OBSERVED";
      if(gap<0) return false;
      TLDetectedGap v=gaps[gap].value;
      if(p.ob!=p.fvg+(v.side==1?":C3":":C1")) { reason="OB_NOT_CONFIRMED_C3_C1"; return false; }
      if(v.available_msc-(long)offset*1000>(long)p.approved*1000) { reason="APPROVAL_PRECEDES_CONFIRMED_FVG"; return false; }
      TLCoreEligibility eligibility=Eligibility(gap,(long)p.approved*1000+(long)offset*1000,p.members);
      if(!eligibility.eligible) { reason=eligibility.reason; return false; }
      string ids[]; int count=StringSplit(p.members,';',ids); double levels[]; ArrayResize(levels,count);
      for(int i=0;i<count;i++)
      {
         int b=BosIndex(ids[i]); if(b<0) return false;
         TLBosHistory h=bos[b].history;
         if(h.side!=v.side || h.qualified_msc==0 || h.qualified_msc-(long)offset*1000>(long)p.approved*1000)
         { reason="BOS_NOT_QUALIFIED_AT_APPROVAL"; return false; }
         if(bos[b].startup) { reason="STARTUP_HISTORY_NOT_EXECUTION_PROOF"; return false; }
         levels[i]=h.side==1?h.high:h.low;
      }
      if(!TLCorePackageGeometry(v.side,levels,v.low,v.high,v.fill,plan,reason)) return false;
      for(int i=0;i<count;i++)
      {
         int b=BosIndex(ids[i]); double entry=TLCoreEntryReference(v.side,levels[i]);
         if(entry!=plan.entry1 && (plan.count!=2 || entry!=plan.entry2)) continue;
         TLFirstReturn r=bos[b].history.lanes[0].returns[0];
         if(r.consumed && !TLCorePackageAvailable(p,r.return_msc-(long)offset*1000))
         { reason="FIRST_RETURN_CONSUMED_BEFORE_OPERATOR_APPROVAL"; return false; }
      }
      return true;
   }
   void OperatorReturn(const int b,const bool persisted,const MqlTick &tick,const long index,TLEventLog &log)
   {
      TLFirstReturn r=bos[b].history.lanes[0].returns[0];
      for(int i=0;i<packages.Count();i++)
      {
         TLCorePackage p; packages.Read(i,p); string ids[]; StringSplit(p.members,';',ids);
         bool member=false; for(int j=0;j<ArraySize(ids);j++) if(ids[j]==bos[b].id) member=true;
         if(!member) continue;
         TLPlan plan; int gap; string reason;
         if(offset==INT_MAX || !TLCorePackageAvailable(p,tick.time_msc-(long)offset*1000)) reason="OPERATOR_APPROVAL_NOT_AVAILABLE_AT_RETURN";
         else if(!Resolve(p,plan,gap,reason)) {}
         else
         {
            double entry=TLCoreEntryReference(bos[b].history.side,bos[b].history.side==1?bos[b].history.high:bos[b].history.low);
            int rank=entry==plan.entry1?0:(plan.count==2 && entry==plan.entry2?1:-1);
            if(rank<0) reason="BOS_NOT_CANONICALLY_SELECTED";
            else if(!r.exact) reason="MISSED_EXACT_SIGNAL_QUOTE_NO_FILL";
            else if(TLCoreBeforeAvailability(r.return_msc,r.return_index,gaps[gap].value.available_msc,gaps[gap].before_tick_index))
               reason="FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION";
            else if(plan.count==1) reason="TODO_STRATEGY_UNRESOLVED:single_be_anchor";
            else
            {
               TLCorePending v; ZeroMemory(v); v.bos=b; v.gap=gap; v.index=index;
               v.persisted=persisted && consumption.FreezePackage(p.id,TLCorePackageFingerprint(p));
               v.trade.setup="OPERATOR:"+p.id; v.trade.side=bos[b].history.side; v.trade.single=false;
               v.trade.be_known=true; v.trade.reference=plan.reference; v.trade.planned=entry; v.trade.shared_stop=plan.stop;
               v.trade.id1="OP"+p.id+(string)rank+"1"; v.trade.id2="OP"+p.id+(string)rank+"2";
               int n=ArraySize(pending); ArrayResize(pending,n+1); pending[n]=v;
               operator_returns++; reason="AWAIT_CURRENT_LIVE_DRAIN_AND_EXECUTION_GUARDS";
            }
         }
         log.Write("CORE_OPERATOR_FIRST_RETURN","OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY",
                   "\"package_id\":"+TLQuote(p.id)+",\"operator\":"+TLQuote(p.operator_name)+",\"evidence\":"+TLQuote(p.evidence)+
                   ",\"bos_id\":"+TLQuote(bos[b].id)+",\"tick_index\":"+(string)index+",\"reason\":"+TLQuote(reason)+
                   ",\"automatic_discovery\":false",tick.time,(int)(tick.time_msc%1000));
      }
   }
   string GapId(const int frame,const TLDetectedGap &g)
   { return TLBosIdentity(names[frame],g.side,g.candidate,offset); }
   string Evidence(const int b,const int g)
   {
      TLCoreBos c=bos[b]; TLCoreGap f=gaps[g]; TLDetectedGap v=f.value;
      double level=c.history.side==1?c.history.high:c.history.low;
      TLFirstReturn r=c.history.lanes[0].returns[0];
      return "\"candidate_id\":"+TLQuote(c.id+"~"+f.id)+",\"bos_id\":"+TLQuote(c.id)+",\"fvg_id\":"+TLQuote(f.id)+
             ",\"ob_id\":"+TLQuote(f.id+(v.side==1?":C3":":C1"))+",\"bos_timeframe\":"+TLQuote(names[c.frame])+
             ",\"fvg_timeframe\":"+TLQuote(names[f.frame])+",\"side\":"+TLQuote(v.side==1?"BUY":"SELL")+
             ",\"candidate_at\":"+TLIso(c.history.opened,offset)+",\"qualified_at\":"+TLMscIso(c.history.qualified_msc,offset)+
             ",\"fvg_candidate_at\":"+TLIso(v.candidate,offset)+",\"fvg_available_at\":"+TLMscIso(v.available_msc,offset)+
             ",\"formation_at\":"+TLMscIso(v.formation_msc,offset)+",\"ob_anchor_at\":"+TLIso(v.anchor,offset)+
             ",\"bos_level\":"+TLQuote(DoubleToString(level,8))+",\"entry_reference\":"+TLQuote(DoubleToString(TLCoreEntryReference(v.side,level),8))+
             ",\"fvg\":["+TLQuote(DoubleToString(v.low,8))+","+TLQuote(DoubleToString(v.high,8))+"]"+
             ",\"ob\":["+TLQuote(DoubleToString(v.ob_low,8))+","+TLQuote(DoubleToString(v.ob_high,8))+"]"+
             ",\"fill_state\":"+TLQuote(TLCoreFillName(v.fill))+",\"break_at\":"+TLMscIso(c.history.lanes[0].break_msc,offset)+
             ",\"first_return_at\":"+TLMscIso(r.return_msc,offset)+",\"first_return_consumed\":"+(r.consumed?"true":"false")+
             ",\"exact_quote\":"+(r.exact?"true":"false")+",\"previous_quote\":"+TLQuote(DoubleToString(r.previous_return,8))+
             ",\"observed_quote\":"+TLQuote(DoubleToString(r.observed,8))+",\"startup_history\":"+(c.startup?"true":"false")+
             ",\"signal_quote\":\"bid\",\"tradable_setup\":false,\"broker_orders_enabled\":false";
   }
   string Reasons(const int b,const int g)
   {
      TLDetectedGap v=gaps[g].value; TLFirstReturn r=bos[b].history.lanes[0].returns[0];
      string reasons="[\"TODO_STRATEGY_UNRESOLVED:package_grouping\"";
      if(bos[b].frame!=gaps[g].frame) reasons+=",\"TODO_STRATEGY_UNRESOLVED:cross_timeframe_association\"";
      if(v.fill==2) reasons+=",\"FVG_FULL_FILL_INVALID\"";
      if(v.fill==1) reasons+=",\"TODO_STRATEGY_UNRESOLVED:partial_fill_policy\"";
      if(bos[b].startup) reasons+=",\"STARTUP_HISTORY_NOT_EXECUTION_PROOF\"";
      if(bos[b].history.lanes[0].state==TL_BLOCKED) reasons+=",\"INTRABAR_BREAK_UNOBSERVED_NOT_EXECUTABLE\"";
      if(r.consumed && TLCoreBeforeAvailability(r.return_msc,r.return_index,v.available_msc,gaps[g].before_tick_index))
         reasons+=",\"FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION\"";
      if(r.consumed && !r.exact) reasons+=",\"MISSED_EXACT_SIGNAL_QUOTE_NO_FILL\"";
      if(!durable) reasons+=",\"CORE_CONSUMPTION_JOURNAL_UNAVAILABLE\"";
      return reasons+"]";
   }
   void Report(const int b,const int g,const string event,const MqlTick &tick,const long index,TLEventLog &log)
   {
      log.Write(event,"BOS-02/FVG-03/OWNER-51/OWNER-52",Evidence(b,g)+",\"reasons\":"+Reasons(b,g)+
                ",\"tick_index\":"+(string)index+
                ",\"minimal_evidence\":[\"Owner package candle/timeframe mapping, complete BOS member IDs and group finalization time\","+
                "\"Explicit PARTIAL permission if applicable; consumed returns cannot be retroactively approved\","+
                "\"Sourced session/news calendar, costs and reviewed lifecycle guards before a new live opportunity\"]",
                tick.time,(int)(tick.time_msc%1000));
   }
   void PairNew(const int only_bos,const int only_gap,const MqlTick &tick,const long index,TLEventLog &log)
   {
      for(int b=0;b<ArraySize(bos);b++) for(int g=0;g<ArraySize(gaps);g++)
      {
         if(only_bos>=0 && b!=only_bos) continue;
         if(only_gap>=0 && g!=only_gap) continue;
         TLDetectedGap v=gaps[g].value; double level=bos[b].history.side==1?bos[b].history.high:bos[b].history.low;
         if(bos[b].history.side!=v.side || level<v.low || level>v.high) continue;
         bool seen=false; for(int p=0;p<ArraySize(pairs);p++) if(pairs[p].bos==b && pairs[p].gap==g) { seen=true; break; }
         if(seen) continue;
         int n=ArraySize(pairs); ArrayResize(pairs,n+1,256); pairs[n].bos=b; pairs[n].gap=g;
         pairs[n].return_reported=bos[b].history.lanes[0].returns[0].consumed;
         Report(b,g,"CORE_SETUP_CANDIDATE",tick,index,log);
      }
   }
public:
   TLCoreController()
   {
      names[0]="M1"; names[1]="M5"; names[2]="M15"; names[3]="H1"; names[4]="H4";
      for(int i=0;i<5;i++) detectors[i].ConfigureCore();
      halted=false; durable=false; recovering=false; last_index=0; last_msc=0; offset=INT_MAX;
      experiment=0; next_group_gap=0; experimental_rejected=0;
      operator_returns=0; package_file="";
      panel_gap=-1; panel_bos=0; panel_members=""; panel_preview=""; panel_enabled=false;
   }
   void Configure(const string name,const int server_offset,const ulong magic,const string calendar_path,const int lead,
                  const string operator_file="",const bool request_execution=false,const int tester_experiment=0,TLEventLog *audit=NULL)
   {
      symbol=name; offset=server_offset;
      experiment=TLPolicyActive()?tester_experiment:0;
      durable=experiment>0 || consumption.Open(name,magic);
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      durable=consumption.Open(name,magic);
      if(!durable) halted=true;
#endif
      if(consumption.Halted()) halted=true;
      package_file=operator_file;
      book.BindAudit(audit);
      book.Configure(name,magic,server_offset,calendar_path,lead,request_execution,MQLInfoInteger(MQL_TESTER) && experiment>0);
      if(experiment>0) Print("EXPERIMENTAL_TESTER_GUARDS ",book.Status());
      if(consumption.Halted()) book.Emergency("RESTORED_OPERATOR_EMERGENCY_STOP");
      RefreshPackages();
   }
   void ClosedBar(const int frame,const MqlRates &bar,TLBosTracker &tracker,const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(halted) return;
      for(int i=0;i<ArraySize(gaps);i++) if(gaps[i].frame==frame)
      {
         TLDetectedGap v=gaps[i].value;
         bool full=v.side==1?bar.low<=v.low:bar.high>=v.high;
         bool partial=v.side==1?bar.low<v.high:bar.high>v.low;
         int next=full?2:partial?(int)MathMax(v.fill,1):v.fill;
         if(next!=v.fill)
         {
            gaps[i].value.fill=next;
            log.Write("CORE_FVG_VALIDITY_CHANGED","FVG-03","\"fvg_id\":"+TLQuote(gaps[i].id)+
                      ",\"fill_state\":"+TLQuote(TLCoreFillName(next))+",\"tick_index\":"+(string)index,tick.time,(int)(tick.time_msc%1000));
         }
      }
      Sync(frame,tracker,tick,index,log,true);
      detectors[frame].Process(bar,symbol,names[frame],tick.time,(int)(tick.time_msc%1000),offset,log);
      MqlRates momentum;
      if(detectors[frame].Momentum(momentum)) for(int g=0;g<ArraySize(gaps);g++)
      {
         TLDetectedGap v=gaps[g].value;
         if(v.side!=1 || !TLBearishOBMomentum(v.ob_low,v.ob_high,momentum,true)) continue;
         // Evidence only: no inferred candle/OB association, inversion, or Reverse order.
         log.Write("REVERSAL_MOMENTUM_CLOSE_DIAGNOSTIC","REV-01/OWNER-52.4",
                   "\"fvg_id\":"+TLQuote(gaps[g].id)+",\"timeframe\":"+TLQuote(names[frame])+
                   ",\"candidate_at\":"+TLIso(momentum.time,offset)+
                   ",\"close\":"+TLQuote(DoubleToString(momentum.close,8))+
                   ",\"confirmation_at\":"+TLMscIso(tick.time_msc,offset)+
                   ",\"block_reason\":"+TLQuote(book.ReverseBlock("EXPERIMENTAL:"+gaps[g].id,false,
                                           TLOBroken(1,v.ob_low,v.ob_high,momentum.low),false,true))+
                   ",\"ob\":["+TLQuote(DoubleToString(v.ob_low,8))+","+TLQuote(DoubleToString(v.ob_high,8))+
                   "],\"momentum_count\":1,\"diagnostic_only\":true,\"association_confirmed\":false,\"tradable_reverse\":false",
                   tick.time,(int)(tick.time_msc%1000));
      }
      TLDetectedGap value;
      if(detectors[frame].Gap(value))
      {
         int n=ArraySize(gaps); ArrayResize(gaps,n+1); gaps[n].id=GapId(frame,value); gaps[n].frame=frame;
         gaps[n].before_tick_index=index; gaps[n].value=value;
         TLCoreEligibility eligibility=Eligibility(n,value.available_msc);
         log.Write("CORE_SETUP_ELIGIBILITY","OWNER-55","\"fvg_id\":"+TLQuote(gaps[n].id)+
                   ",\"eligible\":"+(eligibility.eligible?"true":"false")+
                   ",\"body_pips\":"+DoubleToString(eligibility.body_pips,8)+
                   ",\"witness_ids\":"+TLQuote(eligibility.witnesses)+",\"reasons\":["+eligibility.reasons+"]",
                   tick.time,(int)(tick.time_msc%1000));
         PairNew(-1,n,tick,index,log);
      }
   }
   void Sync(const int frame,TLBosTracker &tracker,const MqlTick &tick,const long index,TLEventLog &log,const bool from_bar=false)
   {
      if(halted) return;
      for(int i=0;i<tracker.ChangedCount();i++)
      {
         TLBosHistory h; int id; if(!tracker.Changed(i,id,h) || h.qualified_msc==0) continue;
         int b=-1; for(int j=0;j<ArraySize(bos);j++) if(bos[j].frame==frame && bos[j].tracker_id==id) { b=j; break; }
         bool added=b<0;
         if(added)
         {
            b=ArraySize(bos); ArrayResize(bos,b+1,256); bos[b].id=TLBosIdentity(names[frame],h.side,h.opened,offset);
            bos[b].frame=frame; bos[b].tracker_id=id; bos[b].startup=index==1;
            ZeroMemory(bos[b].study_return); bos[b].study_armed=false; bos[b].study_arm_msc=0;
         }
         bool prior=!added && bos[b].history.lanes[0].returns[0].consumed;
         bos[b].history=h;
         TLFirstReturn r=h.lanes[0].returns[0];
         bool was_seen=consumption.Seen(bos[b].id);
         if(r.consumed && !prior)
         {
            bool persisted=experiment>0 || consumption.Consume(bos[b].id,r.return_msc);
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
            persisted=consumption.Consume(bos[b].id,r.return_msc);
#endif
            if(!persisted) durable=false;
            log.Write("CORE_BOS_CONSUMED","TOUCH-01","\"bos_id\":"+TLQuote(bos[b].id)+
                      ",\"first_return_at\":"+TLMscIso(r.return_msc,offset)+",\"exact_quote\":"+(r.exact?"true":"false")+
                      ",\"tick_index\":"+(string)index+",\"durable\":"+(persisted?"true":"false")+
                      ",\"execution_context\":"+TLQuote(MQLInfoInteger(MQL_TESTER)?"tester_history":"accepted_history_not_live_execution_proof"),
                      tick.time,(int)(tick.time_msc%1000));
            if(experiment>0) { if(persisted && !was_seen && !(TLDiscoveryStudy() && TL_TESTER_DISCOVERY==3)) ExperimentalReturn(b,tick,index,log); }
            else OperatorReturn(b,persisted && !was_seen,tick,index,log);
         }
         if(added) PairNew(b,-1,tick,index,log);
         if(r.consumed && !prior) for(int p=0;p<ArraySize(pairs);p++) if(pairs[p].bos==b && !pairs[p].return_reported)
         {
            pairs[p].return_reported=true; int g=pairs[p].gap;
            Report(b,g,"CORE_FIRST_RETURN_BLOCKED",tick,index,log);
            // Automatic membership remains unresolved; only explicit operator
            // packages may produce a pending canonical plan.
         }
      }
   }
   void TickComplete(const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(!TLCoreTickOrder(last_index,last_msc,index,tick.time_msc))
      {
         halted=true; book.Emergency("CORE_MISSED_OR_REORDERED_TICK");
         log.Write("CORE_CONTROLLER_HALTED","TOUCH-01","\"reason\":\"nonchronological_tick_dispatch\",\"capture_unchanged\":true",tick.time,(int)(tick.time_msc%1000));
      }
      last_index=index; last_msc=tick.time_msc;
   }
   void Prices(const MqlTick &tick,const long index,TLEventLog &log)
   {
      if(halted) return;
      ExperimentalFinalize(tick,index,log);
      for(int i=0;i<ArraySize(gaps);i++)
      {
         TLDetectedGap v=gaps[i].value;
         gaps[i].fill_before_tick=v.fill; gaps[i].fill_tick_index=index;
         bool full=v.side==1?tick.bid<=v.low:tick.bid>=v.high;
         bool partial=v.side==1?tick.bid<v.high:tick.bid>v.low;
         int next=full?2:partial?(int)MathMax(v.fill,1):v.fill;
         if(next!=v.fill)
         {
            gaps[i].value.fill=next;
            log.Write("CORE_FVG_VALIDITY_CHANGED","FVG-03","\"fvg_id\":"+TLQuote(gaps[i].id)+
                      ",\"fill_before_tick\":"+TLQuote(TLCoreFillName(v.fill))+
                      ",\"fill_state\":"+TLQuote(TLCoreFillName(next))+",\"observed_bid\":"+DoubleToString(tick.bid,8)+
                      ",\"source\":\"observed_bid\",\"tick_index\":"+
                      (string)index,tick.time,(int)(tick.time_msc%1000));
         }
      }
      if(TLDiscoveryStudy() && TL_TESTER_DISCOVERY==3)
      {
         int keep=0;
         for(int a=0;a<ArraySize(study_active);a++)
         {
            int b=study_active[a];
            double entry=TLCoreEntryReference(bos[b].history.side,bos[b].history.side==1?bos[b].history.high:bos[b].history.low);
            if(TLAdvanceReturn(bos[b].study_return,bos[b].history.side,entry,tick.bid,tick,index,0))
            {
               string key="ARMED:"+bos[b].id; bool seen=consumption.Seen(key);
               bool saved=recovering || consumption.Consume(key,tick.time_msc);
               if(!saved) { FailClosed("STUDY_ARMED_CONSUMPTION_WRITE_FAILED"); continue; }
               log.Write("EXPERIMENTAL_ARMED_FIRST_RETURN","NOT_OWNER_CONFIRMED",
                  "\"bos_id\":"+TLQuote(bos[b].id)+",\"entry_reference\":"+DoubleToString(entry,8)+
                  ",\"arm_at\":"+TLMscIso(bos[b].study_arm_msc,offset)+",\"previous_quote\":"+DoubleToString(bos[b].study_return.previous_return,8)+
                  ",\"observed_quote\":"+DoubleToString(tick.bid,8)+",\"tick_index\":"+(string)index+
                  ",\"canonical_consumption_preserved\":true",tick.time,(int)(tick.time_msc%1000));
               if(!recovering && !seen) ExperimentalReturn(b,tick,index,log,true);
            }
            if(!bos[b].study_return.consumed) study_active[keep++]=b;
         }
         ArrayResize(study_active,keep);
      }
      for(int i=0;i<packages.Count();i++)
      {
         TLCorePackage p; packages.Read(i,p); TLPlan plan; int gap; string reason;
         if(offset==INT_MAX || !TLCorePackageAvailable(p,tick.time_msc-(long)offset*1000) || !Resolve(p,plan,gap,reason)) continue;
         bool seen=false; for(int j=0;j<ArraySize(approved_ids);j++) if(approved_ids[j]==p.id) seen=true;
         if(seen) continue;
         int n=ArraySize(approved_ids); ArrayResize(approved_ids,n+1); approved_ids[n]=p.id;
         log.Write("CORE_OPERATOR_PLAN_READY","OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY",
                   "\"package_id\":"+TLQuote(p.id)+",\"fvg_id\":"+TLQuote(p.fvg)+",\"ob_id\":"+TLQuote(p.ob)+
                   ",\"bos_members\":"+TLQuote(p.members)+",\"operator\":"+TLQuote(p.operator_name)+",\"evidence\":"+TLQuote(p.evidence)+
                   ",\"selected_entries\":"+(string)plan.count+",\"reference\":"+TLQuote(DoubleToString(plan.reference,8))+
                   ",\"automatic_discovery\":false",tick.time,(int)(tick.time_msc%1000));
      }
   }
   void Recovering(const bool value) { recovering=value; if(value) ArrayResize(pending,0); }
   bool HasPlans() { return book.HasPlans(); }
#ifdef TRADERLAB_CORE_CHECKS
   int CheckGroups() { return ArraySize(experimental_groups); }
   int CheckPending() { return ArraySize(pending); }
   string CheckState()
   {
      string s=(string)last_index+":"+(string)last_msc+":"+(string)next_group_gap;
      for(int i=0;i<ArraySize(gaps);i++) s+="|G:"+gaps[i].id+":"+(string)gaps[i].value.fill;
      for(int i=0;i<ArraySize(experimental_groups);i++) s+="|P:"+experimental_groups[i].members+":"+
         TLRecoveryDouble(experimental_groups[i].plan.entry1)+":"+TLRecoveryDouble(experimental_groups[i].plan.entry2);
      for(int b=0;b<ArraySize(bos);b++)
      {
         s+="|B:"+bos[b].id+":"+(string)bos[b].history.qualified_msc;
         for(int q=0;q<2;q++) for(int r=0;r<2;r++)
         {
            TLFirstReturn ret=bos[b].history.lanes[q].returns[r];
            s+=":"+(string)bos[b].history.lanes[q].break_msc+":"+(string)ret.consumed+":"+(string)ret.outbound_msc+
               ":"+TLRecoveryDouble(ret.previous)+":"+(string)ret.return_msc+":"+(string)ret.return_index;
         }
      }
      return s;
   }
#endif
   void FailClosed(const string reason)
   {
      halted=true;
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
      consumption.Stop(reason,MQLInfoInteger(MQL_TESTER)?TimeCurrent()-offset:TimeGMT());
#endif
      book.Emergency(reason);
   }
   void RefreshPackages()
   {
      // Operator approvals are a live administrative path, not historical signals.
      if(offset==INT_MAX || MQLInfoInteger(MQL_TESTER) || TL_FORWARD_DEMO) return;
      datetime now=MQLInfoInteger(MQL_TESTER)?TimeCurrent()-offset:TimeGMT();
      packages.Load(package_file,symbol,now);
      if(packages.error!=last_package_error)
      { Print("TraderLab operator packages: ",packages.error==""?"loaded":packages.error); last_package_error=packages.error; }
   }
   void FinishLiveDrain(const MqlTick &before,const MqlTick &tail,const bool capture_active,TLEventLog &log)
   {
      MqlTick current; bool latest=(!MQLInfoInteger(MQL_TESTER) || experiment>0) && capture_active && SymbolInfoTick(symbol,current) &&
         current.time_msc==tail.time_msc && before.time_msc==tail.time_msc &&
         current.bid==tail.bid && current.ask==tail.ask && before.bid==tail.bid && before.ask==tail.ask;
      for(int i=0;i<ArraySize(pending);i++)
      {
         TLCorePending p=pending[i]; TLCoreGuards g; ZeroMemory(g);
         g.group_confirmed=true; g.group_final=true; g.single_be_defined=true;
         g.fvg_permission=p.fvg_permission;
         bool exact=bos[p.bos].history.lanes[0].returns[0].exact;
         if(TLDiscoveryStudy() && TL_TESTER_DISCOVERY==3) exact=bos[p.bos].study_return.exact;
         g.crossing=!exact && TLStudyCrossing(p.trade.side==1,p.trade.planned,tail.bid,tail.ask);
         g.startup_history=bos[p.bos].startup; g.restart=p.persisted;
         g.live_tick=latest && p.index==last_index && !halted;
         book.Guards(g);
         string reason=TLCoreEntryBlock(g,gaps[p.gap].value.fill,p.trade.single,exact);
         if(reason=="" && !TLTesterBosAgeAllowed(bos[p.bos].frame,bos[p.bos].history.opened,tail.time_msc))
            reason="EXPERIMENTAL_M1_BOS_AGE_BEFORE_DISPATCH";
         if(reason=="") reason=book.ExecutionBlock();
         bool sent=false; if(reason=="") { sent=book.Begin(p.trade,g,gaps[p.gap].value.fill,exact,tail,
                                                         gaps[p.gap].value.low,gaps[p.gap].value.high);
                                         if(!sent) reason=book.EntryError()==""?"CORE_BROKER_LIFECYCLE_FAILED_NO_RETRY":book.EntryError(); }
         log.Write(TL_FORWARD_DEMO?"CORE_DEMO_DISPATCH_RESULT":experiment>0?"CORE_TESTER_DISPATCH_RESULT":"CORE_OPERATOR_DISPATCH_RESULT",experiment>0?"EXPERIMENTAL_NOT_OWNER_CONFIRMED":"OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY",
                   "\"setup_id\":"+TLQuote(p.trade.setup)+",\"reason\":"+TLQuote(reason)+",\"submitted\":"+(sent?"true":"false")+
                   ",\"bos_id\":"+TLQuote(bos[p.bos].id)+",\"m1_max_age_minutes\":"+(string)TL_TESTER_M1_MAX_AGE_MINUTES+
                   ",\"bos_age_ms\":"+(string)(tail.time_msc-(long)bos[p.bos].history.opened*1000)+
                   ",\"discovery_policy\":"+TLQuote(TLDiscoveryName())+",\"state\":"+TLQuote(sent?"EXECUTION_READY":"SIGNAL_BLOCKED_AT_EXECUTION")+
                   ",\"automatic_discovery\":"+(experiment>0?"true":"false")+",\"tick_index\":"+(string)p.index,tail.time,(int)(tail.time_msc%1000));
      }
      ArrayResize(pending,0);
   }
   void Service() { book.Service(); }
   void BrokerOffset(const int seconds) { book.BrokerOffset(seconds); }
   bool DispatchReady() { return !halted && durable && book.DispatchReady(); }
   string Status() { return book.Status(); }
   void ExecutionLimits(const int ms,const double spread,const int slippage) { book.ExecutionLimits(ms,spread,slippage); }
#ifdef TRADERLAB_AUTO_CORE_CANDIDATE
   void TrialRiskLimits(const double risk_cap,const double cost_reserve) { book.TrialRiskLimits(risk_cap,cost_reserve); }
#endif
   void PanelEnable(const bool enable) { panel_enabled=enable && !MQLInfoInteger(MQL_TESTER); }
   void PanelDraw()
   {
      if(!panel_enabled) return;
      PanelControl("prevF","< FVG",10,36,70); PanelControl("nextF","FVG >",85,36,70);
      PanelControl("prevB","< BOS",160,36,70); PanelControl("nextB","BOS >",235,36,70);
      PanelControl("member","Add / remove BOS",310,36,135);
      PanelControl("approve","Review / approve",450,36,135);
      PanelControl("stop","EMERGENCY STOP",590,36,140);
      PanelControl("operator","",10,66,180,true); PanelControl("evidence","",195,66,390,true);
      if(panel_gap<0 && ArraySize(gaps)>0) panel_gap=ArraySize(gaps)-1;
      string s="TraderLab | OPERATOR_APPROVED_CORE | "+symbol+"\n"+
               "Automatic grouping BLOCKED. Approvals declare complete membership; no order is sent by a button.\n"+
               "Execution: "+book.Status()+"\nOperator name (left box), chart-review evidence (right box).\n";
      if(panel_gap<0) s+="Waiting for genuine confirmed FVGs (10 following closed bars required).\n";
      else
      {
         TLCoreGap f=gaps[panel_gap]; TLDetectedGap v=f.value;
         s+="FVG "+(string)(panel_gap+1)+"/"+(string)ArraySize(gaps)+"  "+f.id+"\n"+
            "Broker candle "+TimeToString(v.candidate,TIME_DATE|TIME_MINUTES)+" | "+TLCoreFillName(v.fill)+
            " | "+DoubleToString(v.low,2)+" .. "+DoubleToString(v.high,2)+"\n"+
            "OB "+f.id+(v.side==1?":C3":":C1")+" | "+DoubleToString(v.ob_low,2)+" .. "+DoubleToString(v.ob_high,2)+"\n";
         int members[]; int count=PanelBosCount(members);
         if(count>0)
         {
            panel_bos=(panel_bos%count+count)%count;
            TLCoreBos b=bos[members[panel_bos]];
            double level=b.history.side==1?b.history.high:b.history.low;
            s+="BOS "+(string)(panel_bos+1)+"/"+(string)count+"  "+b.id+"\n"+
               "Broker candle "+TimeToString(b.history.opened,TIME_DATE|TIME_MINUTES)+
               " | wick "+DoubleToString(level,2)+" | entry "+DoubleToString(TLCoreEntryReference(b.history.side,level),2)+
               " | "+(b.startup?"STARTUP":b.history.lanes[0].returns[0].consumed || consumption.Seen(b.id)?"CONSUMED":"WAITING FIRST RETURN")+"\n";
         }
         else s+="No qualified BOS wick contained in this FVG.\n";
      }
      s+="Selected COMPLETE membership: "+panel_members+"\n";
      for(int i=0;i<packages.Count();i++)
      {
         TLCorePackage p; packages.Read(i,p); TLPlan plan; int g; string reason;
         bool valid=offset!=INT_MAX && Resolve(p,plan,g,reason);
         s+="Approval "+p.id+" | "+(valid?"VALID - waiting eligible fresh return":reason)+"\n";
      }
      s+=panel_message;
      Comment(s);
   }
   void PanelEvent(const int event,const string object,TLEventLog &log)
   {
      if(!panel_enabled || StringFind(object,"TLCore.")!=0) return;
      if(event==CHARTEVENT_OBJECT_ENDEDIT) { panel_preview=""; PanelDraw(); return; }
      if(event!=CHARTEVENT_OBJECT_CLICK) return;
      ObjectSetInteger(0,object,OBJPROP_STATE,false);
      if(object=="TLCore.stop")
      {
         bool saved=consumption.Stop("OPERATOR_EMERGENCY_STOP",TimeGMT());
         FailClosed("OPERATOR_EMERGENCY_STOP");
         log.Write("CORE_OPERATOR_EMERGENCY","SCOPE-01","\"broker_closure_requires_reviewed_demo_permissions\":true",TimeCurrent());
         panel_message=(saved?"EMERGENCY STOP persisted":"EMERGENCY STOP active; journal unavailable")+
                       string("; no further entries. Verify any open positions in Trade tab.");
      }
      else if(object=="TLCore.prevF" || object=="TLCore.nextF")
      {
         int n=ArraySize(gaps);
         if(n>0) panel_gap=(panel_gap+(object=="TLCore.nextF"?1:-1)+n)%n;
         panel_bos=0; panel_members=""; panel_preview="";
      }
      else if(object=="TLCore.prevB" || object=="TLCore.nextB")
      { panel_bos+=(object=="TLCore.nextB"?1:-1); panel_preview=""; }
      else if(object=="TLCore.member")
      {
         int members[]; int n=PanelBosCount(members);
         if(n>0)
         {
            panel_bos=(panel_bos%n+n)%n; string id=bos[members[panel_bos]].id,ids[];
            StringSplit(panel_members,';',ids); bool found=false; string next="";
            for(int i=0;i<ArraySize(ids);i++) { if(ids[i]==id) { found=true; continue; } if(ids[i]!="") next+=(next==""?"":";")+ids[i]; }
            if(!found) next+=(next==""?"":";")+id;
            panel_members=next; panel_preview="";
         }
      }
      else if(object=="TLCore.approve")
      {
         RefreshPackages(); TLCorePackage p; TLPlan plan; string reason;
         if(halted || !durable) panel_message="Approval blocked: controller/journal unavailable";
         else if(!PanelDraft(p,plan,reason)) panel_message="Approval blocked: "+reason;
         else
         {
            // Confirmation compares membership/operator/evidence, not a time-varying generated ID.
            string key=p.fvg+"|"+p.members+"|"+p.operator_name+"|"+p.evidence;
            if(panel_preview!=key)
            {
               panel_preview=key;
               panel_message="Confirm COMPLETE grouping: click Review / approve again.\n"+
                  "Entries "+DoubleToString(plan.entry1,2)+" / "+DoubleToString(plan.entry2,2)+
                  " | SL "+DoubleToString(plan.stop,2)+" | TP1 "+DoubleToString(plan.tp1,2)+
                  " | TP2 "+DoubleToString(plan.tp2,2)+" | BE "+DoubleToString(TLDualBreakEven(gaps[panel_gap].value.side,plan),2);
            }
            else
            {
               bool frozen=consumption.FreezePackage(p.id,TLCorePackageFingerprint(p));
               bool saved=frozen && packages.Append(package_file,symbol,p,TimeGMT());
               panel_message=saved?"Approval saved: "+p.id+". Fresh first return and all execution guards still required.":
                                   "Approval failed: "+(frozen?packages.error:"durable package identity conflict or journal write failure");
               panel_preview="";
               log.Write("CORE_OPERATOR_APPROVAL","OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY",
                         "\"package_id\":"+TLQuote(p.id)+",\"saved\":"+(saved?"true":"false")+
                         ",\"operator\":"+TLQuote(p.operator_name)+",\"evidence\":"+TLQuote(p.evidence)+
                         ",\"fvg_id\":"+TLQuote(p.fvg)+",\"ob_id\":"+TLQuote(p.ob)+
                         ",\"bos_members\":"+TLQuote(p.members)+",\"automatic_discovery\":false",TimeCurrent());
            }
         }
      }
      PanelDraw(); ChartRedraw();
   }
   void PanelClose()
   { if(panel_enabled) { ObjectsDeleteAll(0,"TLCore."); Comment(""); } }
   void Transaction(const MqlTradeTransaction &trans)
   { if(trans.type==TRADE_TRANSACTION_DEAL_ADD && trans.deal>0) book.DealsChanged(); else book.Service(); }
   void Summary(TLEventLog &log)
   {
      log.Write("CORE_CONTROLLER_SUMMARY","OWNER-51/OWNER-52","\"candidates\":"+(string)ArraySize(pairs)+
                ",\"experimental_groups\":"+(string)ArraySize(experimental_groups)+",\"experimental_rejected_groups\":"+(string)experimental_rejected+
                ",\"tester_experiment\":"+(string)experiment+
                ",\"qualified_bos\":"+(string)ArraySize(bos)+",\"fvgs\":"+(string)ArraySize(gaps)+
                ",\"processed_ticks\":"+(string)last_index+",\"controller_halted\":"+(halted?"true":"false")+
                ",\"approved_setups\":0,\"broker_orders_enabled\":"+(!MQLInfoInteger(MQL_TESTER) && book.DispatchReady()?"true":"false")+
                ",\"simulated_orders_enabled\":"+(MQLInfoInteger(MQL_TESTER) && experiment>0 && book.DispatchReady()?"true":"false")+
                ",\"dispatch_locked\":"+((TL_DEMO_DISPATCH_REVIEWED || TLDemoForwardReviewed())?"false":"true"),TimeCurrent());
      log.Write("CORE_OPERATOR_SUMMARY","OPERATOR_REVIEW_NOT_AUTOMATIC_DISCOVERY",
                "\"operator_plans\":"+(string)ArraySize(approved_ids)+",\"eligible_returns\":"+(string)operator_returns+
                ",\"automatic_discovery\":false,\"dispatch_locked\":"+((TL_DEMO_DISPATCH_REVIEWED || TLDemoForwardReviewed())?"false":"true"),TimeCurrent());
   }
};
#endif
