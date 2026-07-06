import os
import json
from sqlalchemy import create_engine, text

# --- تعريف أسماء ملفات JSON ---
DB_USERS = 'users_data.json'
DB_KEYS = 'keys_store.json'
DB_REDEEM = 'redeem_codes.json'
DB_PRICES = 'prices_config.json'
DB_CONFIG = 'bot.json' 

# --- دوال التعامل مع JSON (تم تعريفها مرة واحدة فقط) ---
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- تحميل البيانات لتكون جاهزة للاستيراد في bot.py ---
users = load_json(DB_USERS)
keys_store = load_json(DB_KEYS)
redeem_codes = load_json(DB_REDEEM)
prices_config = load_json(DB_PRICES)
bot_config = load_json(DB_CONFIG)

# --- هنا يبدأ كود الاتصال بقاعدة البيانات (engine, init_db, إلخ...) ---


# 1. الاتصال بقاعدة البيانات...
# (باقي الكود الخاص بك كما هو...)

# 1. الاتصال بقاعدة البيانات من متغيرات Railway
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# 2. دالة لإنشاء الجداول في المرة الأولى (استدعها في بداية main.py)
def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                uid VARCHAR(50) PRIMARY KEY,
                username TEXT,
                points INTEGER DEFAULT 0,
                accumulated_points INTEGER DEFAULT 0,
                lang VARCHAR(5) DEFAULT 'ar',
                rank TEXT DEFAULT 'عضو عادي 🔹',
                invite_count INTEGER DEFAULT 0,
                completed_quests TEXT DEFAULT ''
            )
        """))
        conn.commit()

# 3. تسجيل مستخدم جديد
def register_user(user):
    uid = str(user.id)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT uid FROM users WHERE uid = :uid"), {"uid": uid}).fetchone()
        if not result:
            conn.execute(text("""
                INSERT INTO users (uid, username, points, accumulated_points, lang, rank, invite_count, completed_quests)
                VALUES (:uid, :username, 0, 0, 'ar', 'عضو عادي 🔹', 0, '')
            """), {"uid": uid, "username": user.username})
            conn.commit()

# 4. جلب بيانات مستخدم
def get_user(uid):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE uid = :uid"), {"uid": str(uid)}).fetchone()
        return result._asdict() if result else None

# 5. تحديث بيانات (نقاط، رتبة، إلخ)
def update_user_data(uid, points=None, acc_points=None, invite_count=None, rank=None, completed_quests=None):
    with engine.connect() as conn:
        query = "UPDATE users SET "
        updates = []
        params = {"uid": str(uid)}
        
        if points is not None: updates.append("points = points + :points"); params["points"] = points
        if acc_points is not None: updates.append("accumulated_points = accumulated_points + :acc_points"); params["acc_points"] = acc_points
        if invite_count is not None: updates.append("invite_count = invite_count + :invite_count"); params["invite_count"] = invite_count
        if rank is not None: updates.append("rank = :rank"); params["rank"] = rank
        if completed_quests is not None: updates.append("completed_quests = :completed_quests"); params["completed_quests"] = completed_quests
        
        query += ", ".join(updates) + " WHERE uid = :uid"
        conn.execute(text(query), params)
        conn.commit()

# 6. دالة نقل البيانات القديمة (تستخدمها لمرة واحدة)
def insert_old_data(uid, username, points, acc_points, lang, rank, invite_count):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO users (uid, username, points, accumulated_points, lang, rank, invite_count)
            VALUES (:uid, :username, :points, :acc_points, :lang, :rank, :invite_count)
            ON CONFLICT (uid) DO NOTHING
        """), {
            "uid": str(uid), "username": username, "points": points, 
            "acc_points": acc_points, "lang": lang, "rank": rank, "invite_count": invite_count
        })
        conn.commit()
# أضف هذا في نهاية ملف database.py

def update_user_rank_and_quests(uid):
    # هنا يجب أن تضع الكود البرمجي الخاص بالدالة
    # هذا مجرد مثال على شكل الدالة:
    with engine.connect() as conn:
        # ضع هنا المنطق الخاص بتحديث الرتبة والمهام
        # ...
        conn.commit()
