// SYNTHETIC in-process transport. Included ONLY by AutoCoreIntegrationChecks.mq5.
// No terminal/account connection, broker OrderSend, or historical prices are used.
struct TLFakePosition { ulong ticket,magic; bool open,buy; double volume,price,sl,tp; string comment; datetime at; };
struct TLFakeDeal { ulong ticket,position,magic; long entry,reason,type; double volume,price,profit,commission; string comment; datetime at; };
TLFakePosition fake_positions[]; TLFakeDeal fake_deals[];
int fake_selected=-1,fake_sends=0,fake_total_sends=0,fake_opens=0,fake_second_fault=0,fake_pending=0;
bool fake_history_ok=true,fake_close_rejected=false,fake_close_unknown=false;
uint fake_first_retcode=0;
uint fake_first_check_retcode=0;
int fake_reject_check_number=1;
int fake_reject_evidence=0;
string fake_rejected_comment="";
double fake_margin_free=1000;
double fake_margin_after_first=-1;
datetime fake_now=1000;
MqlTick fake_quote;
ulong fake_magic=2026101603;
long fake_account_mode=ACCOUNT_TRADE_MODE_DEMO;
int fake_checks=0,fake_foreign_on_check=0;
void FakeReset()
{
   ArrayResize(fake_positions,0); ArrayResize(fake_deals,0);
   fake_selected=-1; fake_sends=0; fake_opens=0; fake_second_fault=0; fake_pending=0;
   fake_history_ok=true; fake_close_rejected=false; fake_close_unknown=false; fake_margin_free=1000; fake_now=1000;
   fake_margin_after_first=-1;
   fake_account_mode=ACCOUNT_TRADE_MODE_DEMO;
   fake_checks=0; fake_foreign_on_check=0;
   fake_first_retcode=0; fake_reject_evidence=0; fake_rejected_comment="";
   fake_first_check_retcode=0; fake_reject_check_number=1;
   ZeroMemory(fake_quote); fake_quote.time=fake_now; fake_quote.time_msc=(long)fake_now*1000;
   fake_quote.bid=5000.5; fake_quote.ask=5000.6;
}
long FakeMQLInfoInteger(const ENUM_MQL_INFO_INTEGER key)
{ return key==MQL_TESTER || key==MQL_TRADE_ALLOWED; }
long FakeAccountInfoInteger(const ENUM_ACCOUNT_INFO_INTEGER key)
{
   if(key==ACCOUNT_LOGIN) return 123456;
   if(key==ACCOUNT_TRADE_MODE) return fake_account_mode;
   if(key==ACCOUNT_MARGIN_MODE) return ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;
   return 1;
}
string FakeAccountInfoString(const ENUM_ACCOUNT_INFO_STRING key)
{ return key==ACCOUNT_CURRENCY?"USD":"LiteFinance-MT5-Demo"; }
double FakeAccountInfoDouble(const ENUM_ACCOUNT_INFO_DOUBLE key)
{ return key==ACCOUNT_MARGIN_FREE?fake_margin_free:1000; }
datetime FakeTimeCurrent() { return fake_now; }
datetime FakeTimeGMT() { return fake_now; }
bool FakeSymbolInfoTick(const string name,MqlTick &quote) { quote=fake_quote; return true; }
double FakeSymbolInfoDouble(const string name,const ENUM_SYMBOL_INFO_DOUBLE key)
{
   if(key==SYMBOL_VOLUME_MAX) return 100;
   if(key==SYMBOL_VOLUME_LIMIT) return 0;
   if(key==SYMBOL_TRADE_CONTRACT_SIZE) return 100;
   return .01;
}
long FakeSymbolInfoInteger(const string name,const ENUM_SYMBOL_INFO_INTEGER key)
{
   if(key==SYMBOL_TRADE_MODE) return SYMBOL_TRADE_MODE_FULL;
   if(key==SYMBOL_FILLING_MODE) return SYMBOL_FILLING_FOK;
   return 0;
}
bool FakeOrderCalcProfit(const ENUM_ORDER_TYPE type,const string name,const double volume,
                        const double opening,const double closing,double &profit)
{ profit=(type==ORDER_TYPE_BUY?1:-1)*(closing-opening)*volume*100; return true; }
bool FakeOrderCalcMargin(const ENUM_ORDER_TYPE type,const string name,const double volume,const double price,double &margin)
{ margin=volume*1000; return true; }
int FakePositionsTotal() { int n=0; for(int i=0;i<ArraySize(fake_positions);i++) if(fake_positions[i].open) n++; return n; }
ulong FakePositionGetTicket(const int index)
{
   int n=0; for(int i=0;i<ArraySize(fake_positions);i++) if(fake_positions[i].open && n++==index)
   { fake_selected=i; return fake_positions[i].ticket; } return 0;
}
bool FakePositionSelectByTicket(const ulong ticket)
{
   for(int i=0;i<ArraySize(fake_positions);i++) if(fake_positions[i].open && fake_positions[i].ticket==ticket)
   { fake_selected=i; return true; } return false;
}
long FakePositionGetInteger(const ENUM_POSITION_PROPERTY_INTEGER key)
{
   if(fake_selected<0) return 0;
   if(key==POSITION_MAGIC) return (long)fake_positions[fake_selected].magic;
   if(key==POSITION_IDENTIFIER) return (long)fake_positions[fake_selected].ticket;
   if(key==POSITION_TYPE) return fake_positions[fake_selected].buy?POSITION_TYPE_BUY:POSITION_TYPE_SELL;
   return (long)fake_positions[fake_selected].at;
}
double FakePositionGetDouble(const ENUM_POSITION_PROPERTY_DOUBLE key)
{
   if(fake_selected<0) return 0;
   if(key==POSITION_VOLUME) return fake_positions[fake_selected].volume;
   if(key==POSITION_PRICE_OPEN) return fake_positions[fake_selected].price;
   if(key==POSITION_SL) return fake_positions[fake_selected].sl;
   if(key==POSITION_TP) return fake_positions[fake_selected].tp;
   return 0;
}
string FakePositionGetString(const ENUM_POSITION_PROPERTY_STRING key)
{ return key==POSITION_SYMBOL?"XAUUSD_o":fake_positions[fake_selected].comment; }
int FakeOrdersTotal() { return fake_pending; }
ulong FakeOrderGetTicket(const int i) { return 900000+i; }
long FakeOrderGetInteger(const ENUM_ORDER_PROPERTY_INTEGER key) { return key==ORDER_MAGIC?(fake_reject_evidence==2?(long)fake_magic:999):ORDER_TYPE_BUY_LIMIT; }
double FakeOrderGetDouble(const ENUM_ORDER_PROPERTY_DOUBLE key) { return .01; }
string FakeOrderGetString(const ENUM_ORDER_PROPERTY_STRING key) { return key==ORDER_SYMBOL?"XAUUSD_o":fake_reject_evidence==2?fake_rejected_comment:"OTHER"; }
int FakeHistoryOrdersTotal() { return fake_reject_evidence==3?1:0; }
ulong FakeHistoryOrderGetTicket(const int index) { return index==0?900001:0; }
long FakeHistoryOrderGetInteger(const ulong ticket,const ENUM_ORDER_PROPERTY_INTEGER key) { return key==ORDER_MAGIC?(long)fake_magic:0; }
string FakeHistoryOrderGetString(const ulong ticket,const ENUM_ORDER_PROPERTY_STRING key) { return key==ORDER_SYMBOL?"XAUUSD_o":fake_rejected_comment; }
bool FakeHistorySelect(const datetime from,const datetime to) { return fake_history_ok; }
bool FakeHistoryDealSelect(const ulong ticket) { return ticket>0 && ticket<=(ulong)ArraySize(fake_deals) && fake_history_ok; }
int FakeHistoryDealsTotal() { return ArraySize(fake_deals); }
ulong FakeHistoryDealGetTicket(const int index) { return index>=0 && index<ArraySize(fake_deals)?fake_deals[index].ticket:0; }
long FakeHistoryDealGetInteger(const ulong ticket,const ENUM_DEAL_PROPERTY_INTEGER key)
{
   int i=(int)ticket-1; if(i<0 || i>=ArraySize(fake_deals)) return 0;
   if(key==DEAL_MAGIC) return (long)fake_deals[i].magic;
   if(key==DEAL_POSITION_ID) return (long)fake_deals[i].position;
   if(key==DEAL_ENTRY) return fake_deals[i].entry;
   if(key==DEAL_TYPE) return fake_deals[i].type;
   if(key==DEAL_REASON) return fake_deals[i].reason;
   if(key==DEAL_TIME_MSC) return (long)fake_deals[i].at*1000;
   return (long)fake_deals[i].at;
}
double FakeHistoryDealGetDouble(const ulong ticket,const ENUM_DEAL_PROPERTY_DOUBLE key)
{
   int i=(int)ticket-1; if(i<0 || i>=ArraySize(fake_deals)) return 0;
   if(key==DEAL_VOLUME) return fake_deals[i].volume;
   if(key==DEAL_PRICE) return fake_deals[i].price;
   if(key==DEAL_PROFIT) return fake_deals[i].profit;
   if(key==DEAL_COMMISSION) return fake_deals[i].commission;
   return 0;
}
string FakeHistoryDealGetString(const ulong ticket,const ENUM_DEAL_PROPERTY_STRING key)
{ return key==DEAL_SYMBOL?"XAUUSD_o":fake_deals[(int)ticket-1].comment; }
ulong FakeDeal(const int position,const long entry,const long reason,const double price,const string comment)
{
   int n=ArraySize(fake_deals); ArrayResize(fake_deals,n+1);
   fake_deals[n].ticket=n+1; fake_deals[n].position=fake_positions[position].ticket;
   fake_deals[n].at=fake_now;
   fake_deals[n].magic=fake_positions[position].magic; fake_deals[n].entry=entry; fake_deals[n].reason=reason;
   bool deal_buy=entry==DEAL_ENTRY_IN?fake_positions[position].buy:!fake_positions[position].buy;
   fake_deals[n].type=deal_buy?DEAL_TYPE_BUY:DEAL_TYPE_SELL;
   fake_deals[n].price=price; fake_deals[n].volume=fake_positions[position].volume;
   fake_deals[n].comment=comment; fake_deals[n].commission=-.05;
   fake_deals[n].profit=entry==DEAL_ENTRY_IN?0:(fake_positions[position].buy?1:-1)*
      (price-fake_positions[position].price)*fake_positions[position].volume*100;
   return n+1;
}
void FakeClose(const int p,const long reason,const double price)
{
   FakeDeal(p,DEAL_ENTRY_OUT,reason,price,"SYNTHETIC_EXIT"); fake_positions[p].open=false;
   fake_quote.bid=fake_positions[p].buy?price:price-.1;
   fake_quote.ask=fake_positions[p].buy?price+.1:price;
   fake_quote.time=fake_now; fake_quote.time_msc++;
}
bool FakeOrderCheck(const MqlTradeRequest &request,MqlTradeCheckResult &result)
{
   fake_checks++;
   if(fake_foreign_on_check>0 && fake_checks==fake_foreign_on_check)
   {
      int n=ArraySize(fake_positions); ArrayResize(fake_positions,n+1); ZeroMemory(fake_positions[n]);
      fake_positions[n].ticket=999; fake_positions[n].magic=999; fake_positions[n].open=true;
      fake_positions[n].buy=true; fake_positions[n].volume=.01; fake_positions[n].price=5000;
      fake_positions[n].sl=4994; fake_positions[n].comment="OTHER_ROBOT"; fake_positions[n].at=fake_now;
   }
   ZeroMemory(result);
   if(fake_first_check_retcode!=0 && fake_checks==fake_reject_check_number)
   { result.retcode=fake_first_check_retcode; return false; }
   if(request.action==TRADE_ACTION_SLTP && FakePositionSelectByTicket(request.position))
   {
      bool buy=fake_positions[fake_selected].buy;
      if(buy?(request.sl>=fake_quote.bid || request.tp<=fake_quote.bid):(request.sl<=fake_quote.ask || request.tp>=fake_quote.ask))
      { result.retcode=TRADE_RETCODE_INVALID_STOPS; return false; }
   }
   result.retcode=0; return true;
}
bool FakeOrderSend(const MqlTradeRequest &request,MqlTradeResult &result)
{
   fake_sends++; fake_total_sends++; ZeroMemory(result);
   if(request.action==TRADE_ACTION_SLTP)
   {
      if(!FakePositionSelectByTicket(request.position)) { result.retcode=TRADE_RETCODE_REJECT; return false; }
      fake_positions[fake_selected].sl=request.sl; fake_positions[fake_selected].tp=request.tp;
      result.retcode=TRADE_RETCODE_DONE; return true;
   }
   if(request.position>0)
   {
      if(fake_close_unknown) { result.retcode=TRADE_RETCODE_TIMEOUT; return false; }
      if(fake_close_rejected || !FakePositionSelectByTicket(request.position)) { result.retcode=TRADE_RETCODE_REJECT; return false; }
      int p=fake_selected; ulong d=FakeDeal(p,DEAL_ENTRY_OUT,DEAL_REASON_EXPERT,request.price,request.comment);
      fake_positions[p].open=false; result.deal=d; result.order=d+1000; result.price=request.price; result.retcode=TRADE_RETCODE_DONE; return true;
   }
   fake_opens++;
   if(fake_opens==1 && fake_first_retcode!=0)
   {
      fake_rejected_comment=request.comment;
      result.retcode=fake_first_retcode;
      if(fake_reject_evidence==1) fake_history_ok=false;
      if(fake_reject_evidence==2) fake_pending=1;
      if(fake_reject_evidence==4)
      {
         int p=ArraySize(fake_positions); ArrayResize(fake_positions,p+1); ZeroMemory(fake_positions[p]);
         fake_positions[p].ticket=10001+p; fake_positions[p].magic=request.magic; fake_positions[p].open=true;
         fake_positions[p].buy=true; fake_positions[p].volume=request.volume; fake_positions[p].price=request.price;
         fake_positions[p].comment=request.comment; fake_positions[p].at=fake_now;
         FakeDeal(p,DEAL_ENTRY_IN,DEAL_REASON_EXPERT,request.price,request.comment);
         // History still proves a fill even if the position has already closed.
         fake_positions[p].open=false;
      }
      return false;
   }
   if(fake_opens==2 && (fake_second_fault==1 || fake_second_fault==2))
   { result.retcode=fake_second_fault==1?TRADE_RETCODE_REJECT:TRADE_RETCODE_TIMEOUT; return false; }
   int p=ArraySize(fake_positions); ArrayResize(fake_positions,p+1); ZeroMemory(fake_positions[p]);
   fake_positions[p].ticket=10001+p; fake_positions[p].magic=request.magic; fake_positions[p].open=true;
   fake_positions[p].at=fake_now;
   fake_positions[p].buy=request.type==ORDER_TYPE_BUY; fake_positions[p].volume=(fake_opens==2 && fake_second_fault==3)?.005:request.volume;
   fake_positions[p].price=request.price; fake_positions[p].sl=request.sl; fake_positions[p].tp=request.tp; fake_positions[p].comment=request.comment;
   ulong d=FakeDeal(p,DEAL_ENTRY_IN,DEAL_REASON_EXPERT,request.price,request.comment);
   result.deal=d; result.order=d+1000; result.price=request.price;
   if(fake_opens==1 && fake_margin_after_first>=0) fake_margin_free=fake_margin_after_first;
   result.retcode=(fake_positions[p].volume==request.volume)?TRADE_RETCODE_DONE:TRADE_RETCODE_DONE_PARTIAL; return true;
}
int FakeCopyTicksRange(const string name,MqlTick &ticks[],const uint flags,const ulong from,const ulong to)
{ ArrayResize(ticks,1); ticks[0]=fake_quote; return 1; }

// Compile-time injection exists only in this test translation unit.
#define MQLInfoInteger FakeMQLInfoInteger
#define AccountInfoInteger FakeAccountInfoInteger
#define AccountInfoString FakeAccountInfoString
#define AccountInfoDouble FakeAccountInfoDouble
#define TimeCurrent FakeTimeCurrent
#define TimeGMT FakeTimeGMT
#define SymbolInfoTick FakeSymbolInfoTick
#define SymbolInfoDouble FakeSymbolInfoDouble
#define SymbolInfoInteger FakeSymbolInfoInteger
#define OrderCalcProfit FakeOrderCalcProfit
#define OrderCalcMargin FakeOrderCalcMargin
#define PositionsTotal FakePositionsTotal
#define PositionGetTicket FakePositionGetTicket
#define PositionSelectByTicket FakePositionSelectByTicket
#define PositionGetInteger FakePositionGetInteger
#define PositionGetDouble FakePositionGetDouble
#define PositionGetString FakePositionGetString
#define OrdersTotal FakeOrdersTotal
#define OrderGetTicket FakeOrderGetTicket
#define OrderGetInteger FakeOrderGetInteger
#define OrderGetDouble FakeOrderGetDouble
#define OrderGetString FakeOrderGetString
#define HistorySelect FakeHistorySelect
#define HistoryOrdersTotal FakeHistoryOrdersTotal
#define HistoryOrderGetTicket FakeHistoryOrderGetTicket
#define HistoryOrderGetInteger FakeHistoryOrderGetInteger
#define HistoryOrderGetString FakeHistoryOrderGetString
#define HistoryDealSelect FakeHistoryDealSelect
#define HistoryDealsTotal FakeHistoryDealsTotal
#define HistoryDealGetTicket FakeHistoryDealGetTicket
#define HistoryDealGetInteger FakeHistoryDealGetInteger
#define HistoryDealGetDouble FakeHistoryDealGetDouble
#define HistoryDealGetString FakeHistoryDealGetString
#define OrderCheck FakeOrderCheck
#define OrderSend FakeOrderSend
#define CopyTicksRange FakeCopyTicksRange
