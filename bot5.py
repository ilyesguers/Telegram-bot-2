"""
=====================================================================
 bot5.py — جسر حماية البيانات (Database Persistence Bridge)
=====================================================================
🎯 المشكلة التي يحلها:
   ملفات bot_config.json / keys_store.json / prices_config.json /
   redeem_codes.json تُخزَّن محلياً على قرص Railway، وهذا القرص
   "مؤقت" (Ephemeral) — أي تحديث/إعادة نشر (Redeploy) من GitHub
   يمسحها بالكامل ← فقدان: المتجر، المفاتيح، الأكواد، الـ VIP،
   الـ Giveaways، العروض الخاطفة، التذاكر، المهام...

   (ملاحظة: نقاط/بيانات المستخدمين نفسها آمنة أصلاً لأنها في
   PostgreSQL منذ البداية — المشكلة فقط في هذه الملفات الأربعة)

✅ الحل: هذا الملف ينسخ محتوى هذه القواميس تلقائياً كل 4 ثوانٍ إلى
   نفس قاعدة بيانات PostgreSQL المستخدمة أصلاً، وعند كل إقلاع جديد
   للبوت يستعيدها تلقائياً قبل أن يبدأ أي شيء آخر بالعمل.

📌 طريقة التركيب (لا تلمس أي شيء آخر):
   افتح bot.py وأضف هذا السطر فقط بعد سطر "import bot4":

        import bot5

   هذا كل شيء. لا حذف، لا تعديل، فقط سطر واحد جديد.
=====================================================================
"""

import json
import time
import threading
import signal
import sys
import atexit
import hashlib

import database
from database import engine, text, DB_CONFIG, DB_KEYS, DB_PRICES, DB_REDEEM

# =====================================================================
# 🗂️ القواميس المتتبعة: اسم -> (الموديول، اسم المتغير بداخله، اسم ملف الـ JSON)
# =====================================================================
TRACKED_STORES = {
    "bot_config": (database, "bot_config", DB_CONFIG),
    "keys_store": (database, "keys_store", DB_KEYS),
    "prices_config": (database, "prices_config", DB_PRICES),
    "redeem_codes": (database, "redeem_codes", DB_REDEEM),
}

_TABLE = "bot5_json_backup"
_last_hash = {}
_lock = threading.Lock()


def _ensure_table():
    with engine.connect() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {_TABLE} (
                store_key VARCHAR(50) PRIMARY KEY,
                data_json TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()


def _load_backup(store_key):
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(f"SELECT data_json FROM {_TABLE} WHERE store_key = :k"),
                {"k": store_key}
            ).fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception as e:
        print(f"⚠️ bot5: خطأ تحميل نسخة '{store_key}': {e}")
    return None


def _save_backup(store_key, data):
    try:
        payload = json.dumps(data, ensure_ascii=False, default=str)
        h = hashlib.md5(payload.encode("utf-8")).hexdigest()
        if _last_hash.get(store_key) == h:
            return  # لا تغيير منذ آخر حفظ، تجاهل لتوفير الموارد
        with engine.connect() as conn:
            conn.execute(text(f"""
                INSERT INTO {_TABLE} (store_key, data_json, updated_at)
                VALUES (:k, :d, NOW())
                ON CONFLICT (store_key)
                DO UPDATE SET data_json = :d, updated_at = NOW()
            """), {"k": store_key, "d": payload})
            conn.commit()
        _last_hash[store_key] = h
    except Exception as e:
        print(f"⚠️ bot5: خطأ حفظ نسخة '{store_key}': {e}")


def _restore_all():
    for store_key, (mod, attr, _f) in TRACKED_STORES.items():
        backup = _load_backup(store_key)
        if backup:
            live_dict = getattr(mod, attr)
            live_dict.update(backup)  # يدمج فوق القيم الافتراضية بدون حذف مفاتيح جديدة أضافها تحديث لاحق للكود
            print(f"✅ bot5: تم استرجاع '{store_key}' من PostgreSQL ({len(backup)} عنصر رئيسي)")
        else:
            print(f"ℹ️ bot5: لا توجد نسخة سابقة لـ '{store_key}' — أول تشغيل، سيتم إنشاؤها تلقائياً")


def _save_all(force=False):
    with _lock:
        for store_key, (mod, attr, _f) in TRACKED_STORES.items():
            live_dict = getattr(mod, attr)
            if force:
                _last_hash.pop(store_key, None)
            _save_backup(store_key, dict(live_dict))


def _autosave_worker():
    while True:
        try:
            _save_all()
        except Exception as e:
            print(f"⚠️ bot5 autosave error: {e}")
        time.sleep(4)  # كل 4 ثوانٍ — سريع بما يكفي لتقليل خطر فقدان البيانات


def _signal_handler(signum, frame):
    print("🛑 bot5: تم استلام إشارة إيقاف (Redeploy/Restart) — حفظ نهائي فوري...")
    try:
        _save_all(force=True)
        print("✅ bot5: تم الحفظ النهائي بنجاح.")
    except Exception as e:
        print(f"⚠️ bot5: فشل الحفظ النهائي: {e}")
    sys.exit(0)


def _atexit_save():
    try:
        _save_all(force=True)
    except Exception:
        pass


# =====================================================================
# 🚀 التشغيل الفعلي (يعمل تلقائياً بمجرد "import bot5")
# =====================================================================
try:
    _ensure_table()
    _restore_all()

    _worker_thread = threading.Thread(target=_autosave_worker, daemon=True)
    _worker_thread.start()

    atexit.register(_atexit_save)
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
    except Exception:
        pass  # بعض البيئات لا تسمح بتسجيل signal خارج الـ main thread

    print("=" * 55)
    print("✅ bot5.py — جسر حماية البيانات جاهز ويعمل!")
    print("💾 المتجر / المفاتيح / الأكواد / الإعدادات محمية الآن")
    print("⏱️ نسخ احتياطي تلقائي كل 4 ثوانٍ + حفظ فوري عند إعادة النشر")
    print("=" * 55)
except Exception as e:
    print(f"❌ bot5: فشل التهيئة الكاملة: {e}")
