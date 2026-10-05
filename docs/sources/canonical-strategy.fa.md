بله. این را به‌عنوان **Canonical Strategy Specification برای تحویل به Codex** می‌نویسم؛ طوری که بدون دیدن این چت قابل استفاده باشد.

یک نکته درباره منبع‌ها: من به پیام‌های موجود در همین گفتگو، سه PDF مرجع و تصاویر ارسالی دسترسی دارم. **متن خام RAR اکسپورت تلگرام را در این لحظه نمی‌توانم دوباره مستقیماً استخراج کنم**؛ بنابراین هر قاعده‌ای که فقط از تحلیل اولیه آن Export آمده و بعداً دوباره صریحاً تأیید نشده، با برچسب «منبع قدیمی» مشخص شده است. قواعد جدیدتر بر قواعد قبلی مقدم‌اند.

برای خواندن سند:

- **[صریح]** = مستقیماً توسط شما/برادرتان گفته و تأیید شده.
- **[مرجع]** = از PDFهای آموزشی.
- **[فرمال‌سازی]** = تبدیل حرف صریح به فرمول ماشینی، بدون افزودن قانون جدید.
- **[نامشخص]** = در منابع موجود تعریف قطعی ندارد و Codex نباید حدس بزند.

---

# Strategy Specification — XAUUSD MT5 EA

## 1. بازار و واحد Pip

**Symbol:** `XAUUSD`

تعریف Pip در این استراتژی:

**هر 1.0 دلار حرکت قیمت XAUUSD = 10 pip**

بنابراین:

| حرکت قیمت | Pip |
|---|---:|
| 4150 → 4151 | 10 |
| 4150 → 4153 | 30 |
| 4150 → 4156 | 60 |
| 4150 → 4160 | 100 |

**منبع [صریح]:** پاسخ شماره 13 برادرتان: «هر یک دلار حرکت قیمت مساوی است با ۱۰ پیپ». :chatgpt-content-reference{index="0"}

برای EA بهتر است تمام محاسبات Strategy بر اساس همین تعریف انجام شوند و به `_Point` یا تعداد Digits بروکر وابسته فرض نشوند.

---

# 2. اولویت قواعد در صورت تعارض

در صورت تعارض، ترتیب زیر معتبر است:

1. آخرین توضیحات صریح شما/برادرتان در همین گفتگو
2. PDF پاسخ به 18 سؤال
3. PDF روش تشخیص BOS
4. PDF آموزش Order Block استاد هادی
5. قواعد استخراج‌شده از Export قدیمی تلگرام

مثلاً در ابتدا بحث ورود بعد از حرکت 10 pip مطرح شده بود، اما بعداً صریحاً گفتید:

> «سوال اول میگه A»

یعنی قانون نهایی:

**Touch BOS → Entry مستقیم**

و قانون انتظار 10 pip برای Core Entry کنار گذاشته می‌شود.

---

# 3. Timeframeها

تقسیم وظایف اصلی:

| Timeframe | وظیفه |
|---|---|
| H4 | پیدا کردن Big Candle و Order Block |
| H1 | بررسی Structure |
| M15 | پیدا کردن BOS |
| M5 | پیدا کردن BOS و Entry |
| M1 | پیدا کردن BOS و Entry |

این تقسیم مستقیماً در پاسخ‌ها آمده است. :chatgpt-content-reference{index="1"}

بعداً درباره Big Candle سؤال شد که قانون عددی آن فقط برای M5/M15 است یا همه تایم‌ها؛ پاسخ نهایی شما:

> «برای همش لحاظ شه»

بنابراین قانون Big Candle بخش بعد، روی **تمام Timeframeهای مورد استفاده** اعمال می‌شود.

### [نامشخص]

عبارت «بررسی Structure در H1» وجود دارد، ولی **الگوریتم عددی مستقلی برای Structure H1 تعریف نشده است**. H1 نباید با یک تعریف دلخواه مثل EMA/HH-HL جایگزین شود.

---

# 4. Big Candle / Momentum Candle

## 4.1 معیار اندازه

ملاک:

**Body کندل**

نه کل High-Low.

فرمول:

`BodySize = abs(Close - Open)`

## 4.2 مقایسه

کندل موردنظر با:

- 10 کندل قبل
- 10 کندل بعد

مقایسه می‌شود.

شرط حداقلی:

**Body کندل FVG / Big Candle باید حداقل دو برابر میانگین Body آن 20 کندل باشد.**

یعنی:

`BigCandle = Body(candidate) >= 2 × AverageBody(10 before + 10 after)`

در پاسخ اولیه نوشته شده که معیار «قانون کاملاً قطعی دیگری ندارد»، ولی همین حداقل 2× صریحاً تعیین شده است. :chatgpt-content-reference{index="2"}

## 4.3 Momentum Candle

بعداً پرسیدیم آیا Momentum Candle همان Big Candle است و پاسخ:

> «درسته همون قانون بیگ کندل»

پس:

**Momentum Candle = Big Candle**

تعریف جداگانه ندارد.

### نکته اجرایی [فرمال‌سازی، نه قانون جدید]

چون تعریف صریح شامل **10 کندل بعد** است، EA در Live نمی‌تواند در لحظه بسته‌شدن Candidate بداند Big Candle تأیید شده؛ باید 10 کندل بعد نیز تشکیل شوند.

بنابراین در Backtest استفاده از Big Candle قبل از تشکیل آن 10 کندل آینده، **Look-Ahead Bias** ایجاد می‌کند.

Codex نباید برای بهترشدن Backtest این محدودیت را نادیده بگیرد.

---

# 5. FVG

مرجع آموزشی ساختار را سه‌کندلی تعریف می‌کند:

- Candle 1
- Candle 2 = کندل بزرگ / Impulse
- Candle 3

اگر Wickهای Candle 1 و Candle 3 به یکدیگر نرسند، Gap ایجاد شده همان FVG است. :chatgpt-content-reference{index="3"}

## 5.1 فرمال‌سازی هندسی FVG

**[فرمال‌سازی از تعریف Wick-to-Wick]**

برای Bullish Gap:

`Low(C3) > High(C1)`

FVG:

`[High(C1), Low(C3)]`

برای Bearish Gap:

`High(C3) < Low(C1)`

FVG:

`[High(C3), Low(C1)]`

این فرمول صرفاً تبدیل مستقیم تعریف «فاصله بین Wickهای کندل اول و سوم» به منطق کد است.

---

# 6. حداقل اندازه FVG

FVG باید حداقل:

**20 pip**

باشد.

- `< 20 pip` → نامعتبر
- `>= 20 pip` → از نظر اندازه معتبر

**منبع [صریح]:**

> «حداقل اندازه ۲۰ پیپ باشد؛ کمتر از ۲۰ پیپ نامعتبر» :chatgpt-content-reference{index="4"}

با تعریف XAUUSD این Strategy:

**20 pip = 2.0 دلار فاصله قیمتی**

---

# 7. Fill شدن FVG

صریحاً گفته شده:

> «اگر کامل پر شود نامعتبر است.» :chatgpt-content-reference{index="5"}

پس:

**Full Fill → FVG Invalid**

### [نامشخص]

در پاسخ اصلی صراحتاً نوشته نشده که **Partial Fill تا چه درصدی** مجاز است.

در بحث‌های قبلی من Partial Fill را معتبر تلقی کرده بودم، اما چون شما الآن خواسته‌اید برداشت از گفته صریح جدا باشد:

**قاعده دقیق Partial Fill = نامشخص**

Codex نباید درصدی مثل 50% یا 75% از خودش بسازد.

---

# 8. Order Block

در فایل آموزشی:

1. ابتدا H4 بررسی می‌شود.
2. Big Candle نسبت به اطراف پیدا می‌شود.
3. Candle قبل و بعد از آن بررسی می‌شوند.
4. اگر بعد از حذف ذهنی Candle وسط، Wickهای Candle 1 و Candle 3 به هم نرسند، ساختار FVG/Order Block معتبر در نظر گرفته می‌شود. :chatgpt-content-reference{index="6"}

برای Zone:

- در حالت **Sell**، ناحیه Order Block حول **Candle 1**
- در حالت **Buy**، ناحیه حول **Candle 3**

رسم می‌شود. :chatgpt-content-reference{index="7"}

### [نامشخص — مهم برای پیاده‌سازی]

در متن مرجع گفته شده «ناحیه/محیط کندل»، ولی دقیقاً مشخص نشده که مرز OB:

- High/Low کامل کندل است؟
- فقط Body است؟
- Open/Close است؟
- یا Rule دیگری دارد؟

در مثال Breaker، Zone به‌صورت عددی داده شده، مثلاً:

**OB = 4141 تا 4143**

اما یک فرمول عمومی برای استخراج این دو مرز از OHLC صریحاً ارائه نشده است.

**Codex نباید تعریف ICT/SMC عمومی را جایگزین این قسمت کند.**

---

# 9. BOS — تعریف اعتبار

PDF اختصاصی BOS این بخش را مشخص می‌کند.

برای یک **سقف / Bullish BOS candidate**، قبل از اینکه آن سقف شکسته شود باید حداقل یک Candle بعدی **پایین‌تر از کل Candle BOS، شامل Wick آن، Close کرده باشد**. :chatgpt-content-reference{index="8"}

در مثال‌های نزولی نیز قاعده به‌صورت Mirror بررسی شده: اگر هیچ Candle بالاتر از کل Candle نزولی موردنظر Close نکرده باشد، آن Candidate به‌عنوان BOS معتبر پذیرفته نمی‌شود. :chatgpt-content-reference{index="9"}

خلاصه Rule مرجع:

### Bullish BOS candidate

قبل از Break شدن High آن:

حداقل یک Candle بعدی باید:

`Close < Low(BOS candle)`

داشته باشد.

### Bearish BOS candidate

Mirror:

قبل از Break شدن Low آن:

حداقل یک Candle بعدی باید:

`Close > High(BOS candle)`

داشته باشد.

این همان شرطی است که PDF برای جلوگیری از Fake BOS آموزش می‌دهد. :chatgpt-content-reference{index="10"}

---

# 10. محدوده دقیق BOS

BOS در مثال‌های شما بعضاً **Zone** است، نه یک Price تک‌خطی.

مثلاً در Breaker Example:

**BOS Zone = 4145.5 تا 4146.5**

### [نامشخص — مهم]

منابع فعلی فرمول عمومی و قطعی برای تبدیل BOS Candle به:

`BOS_zone_low`
و
`BOS_zone_high`

نداده‌اند.

Rule اعتبار Candle BOS مشخص است، اما **فرمول مرز Zone** از متن موجود قابل استخراج قطعی نیست.

این یکی از معدود بخش‌هایی است که اگر Indicator/Reference Code وجود نداشته باشد باید قبل از Final EA دقیق شود.

---

# 11. First Touch

هر BOS:

**فقط در اولین Touch قابل معامله است.**

بعد از اولین Touch، آن BOS دیگر برای Entry مجدد استفاده نمی‌شود.

**منبع [صریح]:**

> «هر BOS فقط برای اولین تاچ معتبر است.» :chatgpt-content-reference{index="11"}

State پیشنهادی:

`UNTOUCHED → TOUCHED/CONSUMED`

---

# 12. Core Entry

قانون نهایی:

**First Touch BOS → Entry مستقیم**

هیچ Candle Confirmation برای Entry Core لازم نیست.

**منبع اولیه:**

> «به محض تاچ شدن BOS وارد می‌شویم و نیازی به Confirmation نداریم.» :chatgpt-content-reference{index="12"}

بعداً نیز هنگام رفع تناقض، پاسخ نهایی شما:

> «سوال اول میگه A»

یعنی گزینه:

**Touch BOS → همان لحظه Entry**

---

# 13. Spread / Touch Allowance

در پاسخ BOS گفته شده رسیدن به سطح با درنظرگرفتن حدود:

**5 pip برای Spread و نوسانات**

کافی است و Candle Close لازم نیست. :chatgpt-content-reference{index="13"}

### [نامشخص]

دقیقاً تعریف نشده 5 pip در MT5 چگونه روی Bid/Ask اعمال شود:

- ±5 pip به Zone؟
- فقط Spread Allowance؟
- Ask برای Buy و Bid برای Sell؟

پس عدد **5 pip صریح است**، اما Execution semantics آن باید Config/Implementation TODO باشد، نه حدس.

---

# 14. تعداد BOSها و انتخاب Extremeها

اگر 3 یا 4 BOS وجود داشته باشند، با مثال زیر پرسیده شد:

4200  
4195  
4190  
4185

پاسخ نهایی:

> «در بای 4200 و 4185 و در سل هم همینطور»

یعنی در مجموعه چند BOS:

**Highest BOS + Lowest BOS**

به‌عنوان دو Candidate اصلی انتخاب می‌شوند.

---

# 15. فاصله دو BOS — قانون نهایی

این بخش با توضیحات آخر کاملاً اصلاح شد.

## 15.1 فاصله 10 تا 20 pip

اگر:

`10 <= distance <= 20 pip`

فقط **یک Entry** انجام می‌شود.

برای Buy:

**بالاترین BOS**

برای Sell:

**پایین‌ترین BOS**

پاسخ آخر:

> «فاصله خود عدد ۲۰ پیپ هم همون یک ورود فقط لحاظ می‌شود»

پس **20 دقیقاً متعلق به حالت یک Entry است**.

---

## 15.2 فاصله بیشتر از 20 تا 40 pip

اگر:

`20 < distance <= 40 pip`

هر دو Entry گرفته می‌شوند.

برای Buy:

SL هر دو = **30 pip پایین‌تر از پایین‌ترین BOS**

برای Sell:

SL هر دو = **30 pip بالاتر از بالاترین BOS**

**منبع [صریح]:**

> «اگر فاصله دوتا BOS بین ۲۰ تا ۴۰ پیپ بود هر دوتاش گرفته می‌شود...»

---

## 15.3 فاصله کمتر از 10 pip

**[نامشخص]**

هیچ قانون قطعی برای:

`distance < 10 pip`

در منابع موجود ندارم.

---

## 15.4 فاصله بیشتر از 40 pip

در جمع‌بندی اولیه من از Export تلگرام آمده بود:

**اگر فاصله >40 pip باشد، هر BOS SL مستقل 30 pip دارد.**

اما متن خام آن پیام فعلاً برای نقل قول مستقیم در دسترس من نیست و این مورد بعداً دوباره صریحاً از برادرتان تأیید نشد.

بنابراین وضعیت:

**[منبع قدیمی، تأیید نهایی مجدد ندارد]**

Codex اگر کاملاً strict پیاده‌سازی می‌کند بهتر است این Rule را Config/TODO نگه دارد تا تأیید نهایی شود.

---

# 16. مثال دو Entry

مثال نهایی خود برادرتان:

**Buy BOS 1 = 4146**  
**Buy BOS 2 = 4143**

فاصله:

3 دلار = **30 pip**

پس هر دو Entry فعال‌اند.

Shared SL:

**4140**

زیرا 30 pip پایین‌تر از BOS پایین‌تر `4143` است.

TPها بر اساس **بالاترین Entry Buy یعنی 4146** محاسبه می‌شوند:

**TP1 = 4152**  
**TP2 = 4156**

نقل قول:

> «تی پی یکصدم اول بای اول و دوم میشه ۴۱۵۲ و ... دوم ... ۴۱۵۶.»

---

# 17. Position Size

برای هر Entry:

**0.02 lot**

که به:

- `0.01 lot` برای TP1
- `0.01 lot` برای TP2

تقسیم می‌شود.

این قاعده در جمع‌بندی Export اولیه آمده بود و مثال نهایی سود/ضرر نیز آن را تأیید می‌کند؛ برادرتان صراحتاً از «یک‌صدم اول» و «یک‌صدم دوم» برای هر دو معامله صحبت می‌کند.

پس برای دو Entry:

**Total volume = 0.04 lot**

در چهار Position با حجم 0.01.

---

# 18. Take Profit

قانون نهایی Fixed است:

**TP1 = 60 pip**

**TP2 = 100 pip**

:chatgpt-content-reference{index="14"}

BOSهای مقابل TP را جابه‌جا نمی‌کنند؛ این مورد نسبت به آموزش عمومی Order Block یک **تغییر شخصی Strategy** است.

---

# 19. TP Reference در دو Entry

برای Buy:

همه TPها از **بالاترین Entry** محاسبه می‌شوند.

برای Sell:

همه TPها از **پایین‌ترین Entry** محاسبه می‌شوند.

مثال Buy:

Entry 1 = 4146  
Entry 2 = 4143

هر دو:

TP1 = 4146 + 60 pip = **4152**

TP2 = 4146 + 100 pip = **4156**

---

# 20. مثال Risk/Reward واقعی

همان Example:

Buy1 = 4146 × 0.02  
Buy2 = 4143 × 0.02  
SL = 4140

زیان:

- معامله 4146 → 4140 = 60 pip روی 0.02 ≈ $12
- معامله 4143 → 4140 = 30 pip روی 0.02 ≈ $6

**Total SL ≈ $18**

Full TP:

برای دو نیمه Entry 4146:

- 0.01 تا 4152 ≈ $6
- 0.01 تا 4156 ≈ $10

برای دو نیمه Entry 4143:

- 0.01 تا 4152 ≈ $9
- 0.01 تا 4156 ≈ $13

Total:

**$38**

این دقیقاً همان عددی است که برادرتان داده:

> «اگر هر دو ورود استاپ شود ... ۱۸ دلار و اگر فول تیپی شود مجموعاً ۳۸ دلار سود.»

---

# 21. Stop Loss Core — موارد قطعی

برای **دو Entry با فاصله >20 و <=40 pip**:

قاعده SL کاملاً مشخص است:

Buy:

`SL = LowestBOS - 30 pip`

Sell:

`SL = HighestBOS + 30 pip`

### [نامشخص مهم]

برای حالت **یک Entry** در فاصله `10–20 pip`، آخرین توضیحات مقدار SL را دوباره مشخص نکرد.

در Context قدیمی عدد 30 pip برای Single BOS وجود داشت، ولی در Breaker Example برادرتان از **Stop 40 pip معامله اولیه** حرف زده است.

پس در نسخه Strict:

**Single-entry Core SL = نامشخص / تعارض 30 و 40 pip**

نباید خودسرانه 30 یا 40 Hard-code شود.

---

# 22. Break Even

پس از رسیدن TP1:

برای Buy:

**SL نیمه دوم = Entry + 5 pip**

برای Sell:

**SL نیمه دوم = Entry - 5 pip**

پاسخ PDF جابه‌جایی 5 pip بعد از TP1 را مشخص کرده است. :chatgpt-content-reference{index="15"}

و بعداً شما مثال Buy/Sell را تأیید کردید:

> «سوال بعد هم تاییده مثالت درسته»

### [نامشخص جزئی]

در Setup دو Entry، صریحاً گفته نشده Offset پنج pip برای هر Position دوم از **Entry خودش** محاسبه شود یا از Reference Entry مشترک.

طبیعی‌ترین برداشت «Entry خودش» است، ولی چون خواسته‌اید چیزی حدس نزنیم:

**Multi-entry BE reference = نامشخص**

---

# 23. Daily Stop

Daily Stop بر اساس **Setup** شمرده می‌شود، نه تعداد Positionهای داخل Setup.

اگر دو Entry یک Setup هر دو SL شوند:

**فقط یک Stop Setup ثبت می‌شود.**

:chatgpt-content-reference{index="16"}

اگر یکی SL شود و دیگری TP:

برای Daily Stop:

**یک Stop لحاظ می‌شود.**

:chatgpt-content-reference{index="17"}

قانون اصلی:

**2 stopped setups در یک روز → Trading برای آن روز متوقف شود.**

---

# 24. Daily Profit Rule

مبنای سود:

**Closed Profit**

نه Floating Equity.

وقتی:

`Closed Daily Profit >= $100`

می‌شود، EA **همان لحظه متوقف نمی‌شود**.

Trading ادامه دارد؛ حتی اگر چند معامله بعدی Full TP شوند.

اما:

**اولین Stop بعد از رسیدن Closed Profit به $100 یا بیشتر → Trading آن روز تمام شود.**

پاسخ PDF صریحاً همین رفتار را توضیح می‌دهد. :chatgpt-content-reference{index="18"}

بنابراین دو Stop Condition مستقل داریم:

1. `Daily stopped setups >= 2`
2. اگر `profit_100_reached == true`، اولین Stop بعدی

هرکدام زودتر رخ دهد → Disable New Trades for the day.

### [نامشخص]

ساعت Reset روز معاملاتی صریحاً تعیین نشده است.

با اینکه همه ساعت‌های Strategy بر اساس ایران هستند، **00:00 ایران به‌عنوان Daily Reset صریحاً تأیید نشده**.

---

# 25. Trend Filter

H4 Trend شرط اجباری نیست.

صریحاً گفته شده:

> «اگر ستاپ معتبر باشد حتی خلاف جهت ۴ ساعته هم معامله می‌کنیم.» :chatgpt-content-reference{index="19"}

پس EA نباید:

- EMA filter
- Higher timeframe direction filter
- RSI trend filter
- MACD

از خودش اضافه کند.

---

# 26. News Filter

برای سه خبر:

- CPI
- NFP
- FOMC

از:

**15 دقیقه قبل**

تا:

**15 دقیقه بعد**

معامله نمی‌کنیم. :chatgpt-content-reference{index="20"}

### [نامشخص]

«معامله نمی‌کنیم» از متن برای **Entry جدید** روشن است، اما مشخص نشده:

- Position باز قبل از News بسته شود؟
- SL/TP آن باقی بماند؟
- Breaker Entry در News Window هم ممنوع است؟

نباید بدون تأیید Position باز را Force Close کرد.

News data source نیز مشخص نشده.

---

# 27. New York Session Bias

این بخش بعداً به Strategy افزوده شد و **برای کمک به پوزیشن‌های نیویورک** است، نه Strategy مستقل.

برادرتان:

> «این ستاپ قطعی نیست ولی در بیشتر موارد قابل اتکا هست برای تشخیص روند»

و بعد:

> «ترکیب کنه به اون موارد قبلی خیلی میتونه کمک کنه برای پوزیشن‌های تایم نیویورک»

بنابراین این یک **Bias/Confirmation Layer** است.

---

# 28. Timezone تمام ساعت‌ها

پاسخ شما:

> «هر ساعتی میگیم به تایم ایرانه همیشه»

پس تمام ساعت‌های Specification:

**Tehran / Iran Time**

هستند.

---

# 29. Tokyo–London Shared Range

Timeframe:

**M15**

بازه:

**10:30 تا 12:30 به وقت ایران**

در این Window باید ثبت شود:

`SharedHigh = Highest High`

`SharedLow = Lowest Low`

---

# 30. NY Bias Break

بعد از Shared Window، در بخش بعدی London Session بررسی می‌شود کدام سمت Range شکسته می‌شود.

Break معتبر:

**حداقل 30 pip عبور از مرز**

Close لازم نیست.

Wick / Shadow کافی است.

پاسخ صریح:

> «حداقل ۳۰ پیپ ناحیه سقف یا کف ... رد کند ... نیازی به کلوز نیست، حتی شدو هم تایید است ... M15»

بنابراین:

اگر:

`Low <= SharedLow - 30 pip`

→ **New York Bias = SELL**

اگر:

`High >= SharedHigh + 30 pip`

→ **New York Bias = BUY**

---

# 31. نحوه استفاده از NY Bias

NY Bias به‌تنهایی Entry نیست.

مثلاً:

Shared Low شکسته شد  
→ `NY Bias = SELL`

سپس همچنان باید:

**Order Block + BOS + Core Entry rules**

برقرار باشند.

در توضیح برادر:

> «با تاییدیه‌های اوردربلاک و BOS میتونیم وارد معامله سل بشیم»

پس:

`Session Bias != Entry Trigger`

---

# 32. NY Bias Hard Filter نیست

چون خود Strategy آن را «قطعی» ندانسته، از اطلاعات فعلی نمی‌توان نتیجه گرفت:

`NY Bias SELL => reject all BUY setups`

بهتر است در نسخه اولیه ثبت شود:

- `ALIGNED`
- `COUNTER_BIAS`
- `NO_BIAS`

تا Backtest جداگانه انجام شود.

### [نامشخص]

اگر Shared High و Shared Low هر دو در همان روز حداقل 30 pip شکسته شوند:

**Bias نهایی تعریف نشده است.**

همچنین زمان دقیق پایان Window «London-only» و شروع New York به‌صورت Rule جداگانه صریح نشده.

در Screenshot Session Indicator اعداد London/New York دیده می‌شوند، اما برای Hard-code کردن به‌اندازه Shared Window تأیید صریح ندارند.

---

# 33. Breaker Block / iFVG Reversal

این Layer بعداً اضافه شد.

هدف:

اگر Core Setup شکست خورد و ساختار واقعاً به سمت مخالف Invalidate شد، پس از تشکیل Breaker/iFVG امکان معامله Reverse وجود دارد.

این **Reverse صرفاً به‌خاطر SL خوردن نیست**.

---

# 34. مثال مرجع Breaker

مثال صریح:

**FVG = 4143 تا 4147**

**BOS = 4145.5 تا 4146.5**

**Order Block = 4141 تا 4143**

Core Setup:

BUY از BOS.

در Chart:

1. BOS به سمت پایین شکسته شده.
2. Candle بعدی با Shadow ناحیه OB را نیز شکسته.
3. FVG تبدیل به iFVG شده.
4. ساختار Breaker Block تشکیل شده.
5. جهت Reverse = SELL.

---

# 35. شرط شکست BOS و OB

بعداً مستقیم پرسیدیم آیا هر دو باید شکسته شوند و پاسخ:

> «بله»

پس برای Breaker Strategy:

**شکستن BOS به‌تنهایی کافی نیست.**

هم:

**BOS**

و هم:

**Order Block**

باید Invalid شوند.

---

# 36. شرط شکست Order Block

برای شکسته‌شدن OB:

قیمت باید حداقل:

**10 pip آن‌طرف مرز Order Block**

برود.

Candle Close لازم نیست.

Wick/Shadow کافی است.

پاسخ صریح:

> «لازمه شکست اوردر بلاک حداقل ۱۰ پیپ بالاتر یا پایین‌تر از اوردر بلاک هست»

مثال:

OB = 4141 تا 4143

در Break نزولی:

اگر Shadow برسد به:

**4140**

یعنی 10 pip پایین‌تر از 4141:

**OB Broken**

---

# 37. iFVG

توضیح صریح:

> «شکست zone و تبدیل FVG به iFVG منوط به رد کردن ... ناحیه FVG و Order Block هستش.»

در Example:

FVG 4143–4147 بوده و پس از Break ساختار نقش آن معکوس شده.

### [نامشخص]

یک Threshold مستقل مثل:

«FVG باید دقیقاً X pip از لبه خودش رد شود»

برای iFVG تعریف نشده است.

عدد 10 pip **برای Order Block Break** صریح است، نه لزوماً برای خود FVG.

---

# 38. Breaker فقط بعد از Core Trade

این موضوع در آخر قطعی شد.

برادرتان:

> «بر اساس ستاپی که تعریف کردیم بات باید معامله اول بای را گرفته باشد»

و:

> «ممکن است استاپ شود ولی بریکر بلاک و iFVG تشکیل نشود و ... معامله معکوس نباشد»

پس Sequence:

1. Core Setup معتبر
2. First Touch
3. Core Trade واقعاً اجرا می‌شود
4. Core Trade SL می‌خورد
5. سپس اگر Breaker + iFVG تشکیل شد → Reverse Trade Candidate
6. اگر فقط SL خورد ولی iFVG/Breaker شکل نگرفت → **No Reverse**

یعنی:

**SL ≠ Automatic Reverse**

---

# 39. Reverse Entry Price

این بخش نیز کاملاً قطعی شده.

Reverse Entry دقیقاً:

**همان Entry Price معامله Core قبلی**

است.

نقل قول:

> «دقیقاً همون نقطه ورود ما برای بای، حالا برای سل گذاشته می‌شود»

مثال:

Original BUY Entry = **4146.5**

بعد از Breaker/iFVG:

صبر می‌شود قیمت دوباره به:

**4146.5**

برگردد.

سپس:

**SELL @ 4146.5**

نه Midpoint iFVG و نه لبه دیگری.

---

# 40. Confirmation در Reverse Entry

روش کلی Breaker در Reference نیز می‌گوید Breaker Block به Confirmation اضافی نیاز ندارد. :chatgpt-content-reference{index="21"}

همچنین توضیح جدید می‌گوید فقط منتظر برگشت به Entry قبلی می‌مانیم.

پس:

**Retest original entry → Reverse Entry مستقیم**

Candle confirmation جدید تعریف نشده است.

---

# 41. جهت Reverse

Original BUY شکست بخورد:

→ Reverse = **SELL**

Original SELL شکست بخورد:

→ Reverse = **BUY**

---

# 42. Breaker SL

در اولین توضیح Breaker گفته شد:

> «با استاپ ۴۰ پیپ سل میزنیم»

و همچنین گفته شد:

> «با همون استاپ و تی پی ستاپ اصلی»

ولی Core SL نهایی در همه حالت‌ها 40 pip نیست و برای دو BOS فاصله 20–40 صریحاً 30 pip پشت Extreme تعریف شده.

بنابراین:

### [نامشخص / تعارض]

**قاعده عمومی Breaker SL هنوز قطعی نیست.**

چیزی که قطعی داریم:

در مثال 4146.5:

**Reverse SELL example uses 40 pip SL**

اما نمی‌توان از این مثال نتیجه گرفت:

`All Breaker SL = 40 pip`

بدون تأیید بیشتر.

---

# 43. Breaker TP

برادرتان گفته:

> «با همون استاپ و تی پی ستاپ اصلی»

در مورد TP تعارضی با Rule جدید نداریم.

بنابراین قابل‌اتکاترین Rule:

**Breaker TP1 = 60 pip**

**Breaker TP2 = 100 pip**

و Position split مشابه Core.

این بخش صریح‌تر از Breaker SL است.

---

# 44. Breaker و چند Entry

Example Breaker مربوط به حالتی است که دو BOS فقط حدود 10 pip فاصله داشتند و طبق Rule جدید فقط یک Core Entry انتخاب شده:

**Buy entry = BOS بالایی = 4146.5**

بنابراین Reverse هم فقط:

**4146.5**

بوده است.

### [نامشخص]

اگر Core Setup به‌دلیل فاصله `>20 و <=40` دارای **دو Entry واقعی** باشد و هر دو SL شوند:

مشخص نشده Breaker:

- دو Reverse Entry بگیرد؟
- فقط Reference Entry را بگیرد؟
- یا فقط یکی از BOSها؟

Codex نباید این حالت را حدس بزند.

---

# 45. Breaker و Daily Stop

### [نامشخص]

مشخص نشده اگر:

Core Trade → SL  
Breaker Reverse → SL

این‌ها برای Daily Stop:

- دو Setup Stop
- یا یک Package/Setup Stop

محسوب شوند.

قاعده عمومی Daily Stop می‌گوید Stop بر اساس Setup شمرده می‌شود، اما رابطه Breaker با Parent Setup صریحاً تعیین نشده.

---

# 46. Core Setup Workflow نهایی

برای Codex، Workflow بدون قسمت‌های نامشخص باید به این ترتیب باشد:

**A. Detection**
- XAUUSD
- Find valid Big Candle
- Detect 3-candle FVG
- FVG size >=20 pip
- Find related Order Block
- Detect valid BOS according to BOS-reference rule

**B. BOS selection**
- Consume only first touch
- Multiple BOS → extreme high + extreme low Candidates
- Distance 10–20 inclusive → one Entry
- Distance >20–40 → both Entries
- <10 → unresolved
- >40 → old-context rule only

**C. Entry**
- Direct first touch
- No candle confirmation
- 5 pip spread/volatility allowance exists

**D. Position**
- 0.02 per Entry
- 0.01 TP1
- 0.01 TP2

**E. TP**
- TP1 +60 pip
- TP2 +100 pip
- For multi-entry Buy: Reference = highest Entry
- For multi-entry Sell: Reference = lowest Entry

**F. SL**
- Multi-entry >20–40: shared 30 pip beyond extreme
- Single Entry: unresolved conflict

**G. BE**
- After TP1:
  - Buy +5 pip
  - Sell -5 pip

**H. Daily guards**
- Two stopped setups → stop day
- Closed Profit >=$100 → continue
- first subsequent Stop → stop day

**I. News**
- No new trades ±15 min CPI/NFP/FOMC

**J. NY Bias**
- M15
- Iran 10:30–12:30 Shared Tokyo/London
- Break >=30 pip
- Wick sufficient
- Low break = Sell Bias
- High break = Buy Bias
- Bias is supporting confirmation, not standalone Entry

**K. Breaker**
- Core Trade must have existed and stopped
- BOS breaks
- OB breaks >=10 pip beyond edge; wick sufficient
- FVG becomes iFVG
- Wait for same original Core Entry Price
- Reverse direction
- Direct Entry
- TP 60/100
- General SL unresolved

---

# 47. مواردی که Codex نباید اضافه کند

در هیچ‌یک از منابع فعلی اجازه‌ای برای موارد زیر وجود ندارد:

- EMA Filter
- RSI Filter
- MACD
- ATR-based Stop
- Dynamic TP
- Trailing Stop اضافی
- Martingale
- Grid
- افزایش Lot بعد از Loss
- Recovery صرفاً به دلیل Stop
- Session Filter اجباری غیر از Rules ذکرشده
- H4 Trend Hard Filter
- ورود مجدد روی BOS مصرف‌شده
- Confirmation Candle برای Core Entry

---

# 48. موارد واقعاً نامشخص که باید در کد TODO/Config بمانند

این‌ها را Codex **نباید پر کند**:

| مورد | وضعیت |
|---|---|
| فرمول دقیق مرز Order Block از OHLC | نامشخص |
| فرمول دقیق Low/High ناحیه BOS | نامشخص |
| FVG Partial Fill limit | نامشخص |
| Single-entry Core SL | تعارض 30/40، نامشخص |
| فاصله BOS کمتر از 10 pip | نامشخص |
| فاصله BOS بیشتر از 40 pip | فقط قاعده قدیمی، تأیید نهایی ندارد |
| Multi-entry BE reference | نامشخص |
| Daily Reset hour | نامشخص |
| News data source | نامشخص |
| رفتار Position باز هنگام News | نامشخص |
| NY Bias وقتی هر دو سمت Range می‌شکنند | نامشخص |
| NY Bias به‌عنوان Hard Reject خلاف جهت | تعریف نشده؛ فعلاً Soft Bias |
| Generic numeric FVG-break threshold برای iFVG | نامشخص |
| Breaker SL عمومی | نامشخص؛ Example = 40 pip |
| Breaker با Parent دارای دو Entry | نامشخص |
| Breaker SL در Daily Stop count | نامشخص |
| Bid/Ask semantics برای 5-pip Touch allowance | نامشخص |

---

# 49. سه مثال Canonical برای تست Codex

## Test A — Multi-entry Buy

BOS:

4146  
4143

Distance:

30 pip

Expected:

- BUY 0.02 @4146
- BUY 0.02 @4143
- Shared SL = 4140
- TP1 for both = 4152
- TP2 for both = 4156
- Full SL ≈ -$18
- Full TP ≈ +$38

---

## Test B — Close BOS pair

دو BOS با فاصله:

**20 pip دقیقاً**

Expected:

- فقط یک Entry
- Buy → Highest BOS
- Sell → Lowest BOS

**20 pip نباید وارد branch دو Entry شود.**

---

## Test C — Breaker/iFVG

Initial:

FVG = 4143–4147  
BOS = 4145.5–4146.5  
OB = 4141–4143

Core:

BUY Entry = 4146.5

بعد:

- Core BUY stops
- BOS breaks down
- OB must be penetrated at least 10 pip
- Shadow to 4140 qualifies for OB ending at 4141
- Breaker/iFVG confirmed
- Do not immediately Sell at bottom
- Wait for price to return to **4146.5**
- Reverse SELL @4146.5

Expected Reverse TP:

- TP1 = 60 pip below
- TP2 = 100 pip below

**SL عمومی Breaker هنوز نباید از Example به‌صورت Global Hard-code شود.**

---

# 50. ادعای Win Rate

برادرتان گفته:

> «اگه بتونه اینو هم پیاده‌سازی کنه وین ریت مون بالای ۹۰٪ میشه قطعی»

این **جزء Strategy Rule نیست** و فعلاً یک ادعای تجربی است.

EA/Backtest نباید 90% را به‌عنوان Acceptance Criterion تضمین‌شده در نظر بگیرد.

برای سنجش واقعی باید حداقل:

- Backtest بدون Look-Ahead
- Out-of-sample
- Forward Demo

انجام شود.

---

## جمع‌بندی برای Codex

هسته Strategy برای شروع توسعه **به‌اندازه کافی مشخص است که Detection Engine، State Machine، Logging و Backtest Skeleton ساخته شود**؛ اما هنوز چند قسمت برای اجرای 100٪ خودکار Live تعریف ریاضی قطعی ندارند، مهم‌ترینشان **مرز دقیق BOS/OB، Single-entry SL و Breaker SL عمومی** است.

بنابراین Codex باید هر بخش نامشخص را با `TODO_STRATEGY_UNRESOLVED` یا Config بدون مقدار نهایی نگه دارد و **هیچ Rule متداول ICT/SMC را از دانش خودش وارد نکند**.

این سند باید مرجع اصلی Implementation باشد؛ هرجا کد با این سند تعارض داشت، **این Specification مقدم است**.