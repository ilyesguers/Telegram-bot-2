import os
import json
from sqlalchemy import create_engine, text

# --- أسماء ملفات JSON ---
DB_USERS = 'users_data.json'
DB_KEYS = 'keys_store.json'
DB_REDEEM = 'redeem_codes.json'
DB_PRICES = 'prices_config.json'
DB_CONFIG = 'bot_config.json' 

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ خطأ في حفظ {filename}: {e}")

# --- تحميل البيانات ---
users = load_json(DB_USERS)
keys_store = load_json(DB_KEYS)
redeem_codes = load_json(DB_REDEEM)
prices_config = load_json(DB_PRICES)
bot_config = load_json(DB_CONFIG)

# --- الإعدادات الافتراضية ---
default_config = {
    "daily_gift": 10,
    "invite_reward": 20,
    "discount": 0,
    "maintenance": False,
    "total_sales": 0,
    "total_earnings": 0,
    "sales_log": [],
    "tickets": {},
    "product_requests": {},
    "temp_req": {},
    "lootbox_price": 50,
    "lootbox_chance": 25,
    "wheel_price": 40,
    "wheel_chance": 5,
    "quests": {
        "invite": {"target": 5, "reward": 100},
        "buy": {"target": 3, "reward": 150},
        "points": {"target": 1000, "reward": 200}
    },
    "achievements": {},
    "vip_users": [],
    "flash_sales": {},
    "leaderboard_enabled": True
}
for key, val in default_config.items():
    if key not in bot_config:
        bot_config[key] = val
save_json(DB_CONFIG, bot_config)

# --- الاتصال بقاعدة البيانات ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def init_db():
    """إنشاء الجداول"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                uid VARCHAR(50) PRIMARY KEY,
                username TEXT DEFAULT '',
                points INTEGER DEFAULT 0,
                accumulated_points INTEGER DEFAULT 0,
                lang VARCHAR(5) DEFAULT 'ar',
                rank TEXT DEFAULT 'عضو عادي 🔹',
                rank_discount REAL DEFAULT 0.0,
                invite_count INTEGER DEFAULT 0,
                completed_quests TEXT DEFAULT '',
                invited_by TEXT DEFAULT NULL,
                last_claim TEXT DEFAULT NULL,
                banned BOOLEAN DEFAULT FALSE,
                banned_until TEXT DEFAULT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                verified BOOLEAN DEFAULT FALSE,
                lang_selected BOOLEAN DEFAULT FALSE,
                vip BOOLEAN DEFAULT FALSE,
                total_spent INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                last_streak_date TEXT DEFAULT NULL,
                notifications_on BOOLEAN DEFAULT TRUE,
                join_date TEXT DEFAULT NULL
            )
        """))
        
        missing_columns = [
            ("rank_discount", "REAL DEFAULT 0.0"),
            ("invited_by", "TEXT DEFAULT NULL"),
            ("last_claim", "TEXT DEFAULT NULL"),
            ("banned", "BOOLEAN DEFAULT FALSE"),
            ("banned_until", "TEXT DEFAULT NULL"),
            ("is_admin", "BOOLEAN DEFAULT FALSE"),
            ("verified", "BOOLEAN DEFAULT FALSE"),
            ("lang_selected", "BOOLEAN DEFAULT FALSE"),
            ("vip", "BOOLEAN DEFAULT FALSE"),
            ("total_spent", "INTEGER DEFAULT 0"),
            ("streak_days", "INTEGER DEFAULT 0"),
            ("last_streak_date", "TEXT DEFAULT NULL"),
            ("notifications_on", "BOOLEAN DEFAULT TRUE"),
            ("join_date", "TEXT DEFAULT NULL")
        ]
        for col_name, col_def in missing_columns:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
            except Exception as e:
                print(f"عمود {col_name}: {e}")
        
        conn.commit()
    print("✅ قاعدة البيانات جاهزة.")

def register_user(user):
    from datetime import datetime
    uid = str(user.id)
    username = user.username or user.first_name or ""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT uid FROM users WHERE uid = :uid"), {"uid": uid}).fetchone()
        if not result:
            conn.execute(text("""
                INSERT INTO users (uid, username, points, accumulated_points, lang, rank, rank_discount, invite_count, completed_quests, banned, is_admin, verified, lang_selected, vip, total_spent, streak_days, notifications_on, join_date)
                VALUES (:uid, :username, 0, 0, 'ar', 'عضو عادي 🔹', 0.0, 0, '', FALSE, FALSE, FALSE, FALSE, FALSE, 0, 0, TRUE, :jd)
            """), {"uid": uid, "username": username, "jd": datetime.now().isoformat()})
            conn.commit()

def get_user(uid):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE uid = :uid"), {"uid": str(uid)}).fetchone()
        if result:
            return dict(result._mapping)
        return None

def update_user_data(uid, **kwargs):
    if not kwargs:
        return
    
    increment_fields = {"points", "accumulated_points", "invite_count", "total_spent", "streak_days"}
    replace_fields = {"username", "lang", "rank", "rank_discount", "completed_quests",
                      "invited_by", "last_claim", "banned", "banned_until", "is_admin", 
                      "verified", "lang_selected", "vip", "last_streak_date", "notifications_on", "join_date"}
    
    updates = []
    params = {"uid": str(uid)}
    
    for key, value in kwargs.items():
        if key in increment_fields and value is not None:
            updates.append(f"{key} = COALESCE({key}, 0) + :{key}")
            params[key] = value
        elif key in replace_fields:
            updates.append(f"{key} = :{key}")
            params[key] = value
    
    if not updates:
        return
    
    query = f"UPDATE users SET {', '.join(updates)} WHERE uid = :uid"
    
    try:
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
    except Exception as e:
        print(f"⚠️ خطأ update_user_data: {e}")

def update_user_rank_and_quests(uid):
    from config import RANKS
    
    u = get_user(uid)
    if not u:
        return
    
    acc_pts = u.get("accumulated_points", 0) or 0
    current_rank = u.get("rank", "عضو عادي 🔹")
    current_discount = u.get("rank_discount", 0.0) or 0.0
    
    new_rank = "عضو عادي 🔹"
    new_discount = 0.0
    
    for rank_key in ["silver", "gold", "diamond", "hero", "master", "legend"]:
        rank_info = RANKS[rank_key]
        if acc_pts >= rank_info["points_needed"]:
            new_rank = rank_info.get("name_ar", rank_info.get("name", ""))
            new_discount = rank_info["discount"]
    
    if new_rank != current_rank or abs(new_discount - current_discount) > 0.001:
        update_user_data(uid, rank=new_rank, rank_discount=new_discount)
        try:
            from config import bot
            bot.send_message(int(uid), 
                f"🎊 <b>ترقية جديدة!</b>\n\nرتبتك الجديدة: <b>{new_rank}</b>\n💎 خصم دائم: <b>{int(new_discount*100)}%</b>", 
                parse_mode="HTML")
        except: pass
    
    completed = u.get("completed_quests", "") or ""
    quests = bot_config.get("quests", {})
    
    if "quest_invite" not in completed:
        invite_cnt = u.get("invite_count", 0) or 0
        target = quests.get("invite", {}).get("target", 5)
        reward = quests.get("invite", {}).get("reward", 100)
        if invite_cnt >= target:
            new_completed = (completed + ",quest_invite").strip(",")
            update_user_data(uid, completed_quests=new_completed, points=reward, accumulated_points=reward)
            try:
                from config import bot
                bot.send_message(int(uid), f"🎉 <b>أكملت مهمة الدعوات!</b>\n🎁 +<b>{reward}</b> نقطة", parse_mode="HTML")
            except: pass
    
    if "quest_buy" not in completed:
        user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == str(uid))
        target = quests.get("buy", {}).get("target", 3)
        reward = quests.get("buy", {}).get("reward", 150)
        if user_buys >= target:
            u_now = get_user(uid)
            new_completed = ((u_now.get("completed_quests", "") or "") + ",quest_buy").strip(",")
            update_user_data(uid, completed_quests=new_completed, points=reward, accumulated_points=reward)
            try:
                from config import bot
                bot.send_message(int(uid), f"🎉 <b>أكملت مهمة المبيعات!</b>\n🎁 +<b>{reward}</b> نقطة", parse_mode="HTML")
            except: pass
    
    if "quest_points" not in completed:
        target = quests.get("points", {}).get("target", 1000)
        reward = quests.get("points", {}).get("reward", 200)
        if acc_pts >= target:
            u_now = get_user(uid)
            new_completed = ((u_now.get("completed_quests", "") or "") + ",quest_points").strip(",")
            update_user_data(uid, completed_quests=new_completed, points=reward, accumulated_points=reward)
            try:
                from config import bot
                bot.send_message(int(uid), f"🎉 <b>أكملت مهمة النقاط!</b>\n🎁 +<b>{reward}</b> نقطة", parse_mode="HTML")
            except: pass
