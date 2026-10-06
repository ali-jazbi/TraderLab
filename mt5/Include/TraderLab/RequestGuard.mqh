#ifndef TRADERLAB_REQUEST_GUARD_MQH
#define TRADERLAB_REQUEST_GUARD_MQH

// Safety reference only. No send function lives here and the diagnostic EA does not call it.
// A future execution gateway must call RecordBeforeSend immediately before its single send site.
class TLRequestGuard
{
private:
   ulong dispatch_times[];
   string action_ids[];
   string intent_hashes[];
   string action_states[];
   int action_attempts[];

   int FindAction(const string action_id)
   {
      for(int i=0;i<ArraySize(action_ids);i++) if(action_ids[i]==action_id) return i;
      return -1;
   }
   int CountWindow(const ulong now_msc,const ulong width_msc)
   {
      int count=0;
      for(int i=0;i<ArraySize(dispatch_times);i++)
         if(now_msc>=dispatch_times[i] && now_msc-dispatch_times[i]<width_msc) count++;
      return count;
   }
   void Prune(const ulong now_msc)
   {
      int keep=0;
      for(int i=0;i<ArraySize(dispatch_times);i++)
         if(now_msc<dispatch_times[i] || now_msc-dispatch_times[i]<3600000)
            dispatch_times[keep++]=dispatch_times[i];
      ArrayResize(dispatch_times,keep);
   }
public:
   bool RecordBeforeSend(const string action_id,const string intent_hash,const ulong now_msc,
                         const bool explicit_retry,string &attempt_id,string &request_state,
                         string &rate_state)
   {
      attempt_id=""; request_state="REQUEST_ALLOWED"; rate_state="REQUEST_ALLOWED";
      if(action_id=="" || intent_hash=="")
      {
         request_state="REQUEST_REJECTED"; rate_state="INVALID_ACTION_IDENTITY"; return false;
      }
      Prune(now_msc);
      int existing=FindAction(action_id);
      if(existing>=0)
      {
         if(intent_hashes[existing]!=intent_hash)
         {
            request_state="REQUEST_REJECTED"; rate_state="REQUEST_ID_PAYLOAD_CONFLICT"; return false;
         }
         if(!explicit_retry || (action_states[existing]!="REQUEST_TIMEOUT" &&
                                action_states[existing]!="REQUEST_REJECTED" &&
                                action_states[existing]!="REQUEST_RATE_BLOCKED"))
         {
            request_state=action_states[existing]; rate_state="DUPLICATE_ACTION_SUPPRESSED"; return false;
         }
      }
      int short_count=CountWindow(now_msc,300000);
      int hour_count=CountWindow(now_msc,3600000);
      if(short_count>=1000 || hour_count>=10000)
      {
         request_state="REQUEST_RATE_BLOCKED"; rate_state=request_state;
         if(existing<0)
         {
            int n=ArraySize(action_ids);
            ArrayResize(action_ids,n+1); ArrayResize(intent_hashes,n+1);
            ArrayResize(action_states,n+1); ArrayResize(action_attempts,n+1);
            action_ids[n]=action_id; intent_hashes[n]=intent_hash; action_states[n]=request_state; action_attempts[n]=0;
         }
         else action_states[existing]=request_state;
         return false;
      }
      int index=existing;
      if(index<0)
      {
         index=ArraySize(action_ids);
         ArrayResize(action_ids,index+1); ArrayResize(intent_hashes,index+1);
         ArrayResize(action_states,index+1); ArrayResize(action_attempts,index+1);
         action_ids[index]=action_id; intent_hashes[index]=intent_hash;
         action_states[index]="REQUEST_PENDING"; action_attempts[index]=0;
      }
      int attempt=action_attempts[index]+1;
      action_attempts[index]=attempt; action_states[index]="REQUEST_PENDING";
      int n=ArraySize(dispatch_times); ArrayResize(dispatch_times,n+1); dispatch_times[n]=now_msc;
      attempt_id=action_id+":attempt:"+(string)attempt;
      if(short_count+1>=1000 || hour_count+1>=10000) rate_state="REQUEST_RATE_WARNING";
      request_state="REQUEST_PENDING";
      return true;
   }

   bool Reconcile(const string action_id,const string next_state,const string evidence)
   {
      int i=FindAction(action_id);
      if(i<0 || (action_states[i]!="REQUEST_PENDING" && action_states[i]!="REQUEST_ACCEPTED"))
         return false;
      if(next_state!="REQUEST_ACCEPTED" && next_state!="REQUEST_REJECTED" &&
         next_state!="REQUEST_TIMEOUT" && next_state!="REQUEST_RECONCILED") return false;
      if(evidence=="") return false;
      action_states[i]=next_state;
      return true;
   }
};

#endif
