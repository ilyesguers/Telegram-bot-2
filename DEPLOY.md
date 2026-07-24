# 🚀 النشر على Railway — Deploying to Railway

دليل مختصر لتشغيل البوت على Railway بشكل صحيح ودائم.

---

## 1️⃣ إنشاء المشروع

1. افتح [railway.app](https://railway.app) → **New Project**
2. اختر **Deploy from GitHub repo** → اختر `Telegram-bot-2`
3. Railway سيكتشف Python تلقائياً عبر Nixpacks

---

## 2️⃣ إضافة قاعدة البيانات (مهم جداً ⚠️)

داخل نفس المشروع:

**+ New** → **Database** → **Add PostgreSQL**

Railway يضيف متغير `DATABASE_URL` تلقائياً ويربطه بخدمة البوت.

> **لماذا هذا ضروري؟**
> قرص Railway مؤقت (ephemeral): أي ملف `.json` يُحذف عند كل إعادة نشر.
> ملف `bot5.py` يحفظ **المنتجات والمفاتيح والأكواد والإعدادات** داخل
> PostgreSQL كل 4 ثوانٍ ويسترجعها عند الإقلاع — بدون قاعدة بيانات
> **ستفقد كل بيانات المتجر عند كل deploy**.

---

## 3️⃣ ضبط المتغيرات (Variables)

في خدمة البوت → تبويب **Variables**:

| المتغير | القيمة | إلزامي |
|---|---|---|
| `API_TOKEN` | التوكن من [@BotFather](https://t.me/BotFather) | ✅ نعم |
| `DATABASE_URL` | يُضاف تلقائياً مع Postgres | ✅ نعم |

إذا نسيت `API_TOKEN` سيتوقف البوت برسالة واضحة تشرح الحل بدل خطأ غامض.

---

## 4️⃣ التشغيل

النشر يبدأ تلقائياً. راقب **Deploy Logs** — يجب أن ترى:

```
✅ قاعدة البيانات جاهزة - كل الأعمدة موجودة
✅ bot5.py — جسر حماية البيانات جاهز ويعمل!
🤖 Bot is now RUNNING!
```

---

## ⚠️ نقطة حرجة: نسخة واحدة فقط

تيليجرام يسمح لجلسة **polling واحدة** فقط لكل توكن. إذا شغّلت نسختين
(مثلاً Railway + جهازك) ستحصل على خطأ `409 Conflict` والبوت يتعطّل.

- أبقِ **Replicas = 1** (مضبوط في `railway.json`)
- أوقف البوت محلياً قبل النشر

---

## 📁 ملفات النشر

| الملف | الوظيفة |
|---|---|
| `Procfile` | `worker: python bot.py` — بوت polling وليس خادم ويب |
| `railway.json` | إعادة تشغيل تلقائية عند الفشل + نسخة واحدة |
| `runtime.txt` | Python 3.11 |
| `requirements.txt` | إصدارات مثبّتة لبناء متكرر وآمن |

> **لماذا `worker` وليس `web`؟**
> البوت لا يفتح منفذ HTTP. لو عُرِّف كـ `web` سينتظر Railway منفذاً
> ولن يصل أبداً، فيعتبر النشر فاشلاً.

---

## 🔧 حل المشاكل

| العَرَض | السبب والحل |
|---|---|
| `API_TOKEN is missing` | أضف `API_TOKEN` في Variables |
| `DATABASE_URL not set` | أضف خدمة PostgreSQL واربطها |
| `409 Conflict` | نسخة أخرى تعمل بنفس التوكن — أوقفها |
| المتجر فارغ بعد النشر | تأكد أن PostgreSQL مربوطة (راجع خطوة 2) |
| البوت لا يرد | راجع Deploy Logs، وتأكد أن `remove_webhook` نجح |

---

## 💻 التشغيل محلياً

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export API_TOKEN="123456:ABC..."
export DATABASE_URL="postgresql://..."   # اختياري: بدونه يستخدم SQLite محلي

python bot.py
```

## 🧪 الاختبارات

```bash
python -m unittest tests.test_shop_ui tests.test_channel_broadcasting
```
