import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# =====================================================
# 📁 أسماء ملفات JSON
# =====================================================
DB_USERS = 'users_data.json'
DB_KEYS = 'keys_store.json'
DB_REDEEM = 'redeem_codes.json'
DB_PRICES = 'prices_config.json'
DB_CONFIG = 'bot_config.json'

# =====================================================
# 🔧 دوال JSON
# =====================================================
def load_json(filename):
    """تحميل ملف JSON بأمان"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطأ في تحميل {filename}: {e}")
            return {}
    return {}

def save_json(filename, data):
    """حفظ ملف JSON بأمان"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ خطأ في حفظ {filename}: {e}")

# =====================================================
# 📦 تحميل البيانات
# =====================================================
users = load_json(DB_USERS)
keys_store = load_json(DB_KEYS)
redeem_codes = load_json(DB_REDEEM)
prices_config = load_json(DB_PRICES)
bot_config = load_json(DB_CONFIG)

# =====================================================
# ⚙️ الإعدادات الافتراضية (كل الميزات)
# =====================================================
default_config = {
    # 💰 الاقتصاد
    "daily_gift": 10,
    "invite_reward": 20,
    "discount": 0,
    
    # 🛠️ حالة البوت
    "maintenance": False,
    
    # 📊 الإحصائيات
    "total_sales": 0,
    "total_earnings": 0,
    "total_visits": 0,
    "sales_log": [],
    
    # 🎫 التذاكر والطلبات
    "tickets": {},
    "product_requests": {},
    "temp_req": {},
    "temp_ticket_cat": {},
    
    # 🎮 الألعاب
    "lootbox_price": 50,
    "lootbox_chance": 25,
    "wheel_price": 40,
    "wheel_chance": 5,
    
    # 🔥 المهام
    "quests": {
        "invite": {"target": 5, "reward": 100},
        "buy": {"target": 3, "reward": 150},
        "points": {"target": 1000, "reward": 200}
    },
    
    # 🏆 الإنجازات
    "achievements": {},
    
    # 👑 VIP
    "vip_users": [],
    
    # ⚡ العروض الخاطفة
    "flash_sales": {"current": None, "history": []},
    
    # 📊 لوحة المتصدرين
    "leaderboard_enabled": True,
    
    # 🎨 الثيمات
    "default_theme": "dark",
    
    # 🔔 الإشعارات
    "notifications_enabled": True,
    
    # 💎 معلومات البوت
    "bot_version": "3.0",
    "bot_launch_date": datetime.now().isoformat()
}

# دمج الإعدادات الافتراضية مع الحالية
for key, val in default_config.items():
    if key not in bot_config:
        bot_config[key] = val

save_json(DB_CONFIG, bot_config)

# =====================================================
# 🔌 الاتصال بقاعدة البيانات PostgreSQL
# =====================================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("⚠️ WARNING: DATABASE_URL not set!")

engine = create_engine(DATABASE_URL)

# =====================================================
# 🗄️ إنشاء الجداول
# =====================================================
def init_db():
    """إنشاء جدول المستخدمين مع كل الأعمدة اللازمة"""
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
                join_date TEXT DEFAULT NULL,
                theme TEXT DEFAULT 'dark',
                last_active TEXT DEFAULT NULL,
                purchases_count INTEGER DEFAULT 0,
                referral_earnings INTEGER DEFAULT 0
            )
        """))
        
        # إضافة الأعمدة الناقصة إن لم تكن موجودة
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
            ("join_date", "TEXT DEFAULT NULL"),
            ("theme", "TEXT DEFAULT 'dark'"),
            ("last_active", "TEXT DEFAULT NULL"),
            ("purchases_count", "INTEGER DEFAULT 0"),
            ("referral_earnings", "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_def in missing_columns:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
            except Exception as e:
                print(f"عمود {col_name}: {e}")
        
        conn.commit()
    print("✅ قاعدة البيانات جاهزة - كل الأعمدة موجودة")

# =====================================================
# 👤 تسجيل مستخدم جديد
# =====================================================
def register_user(user):
    """تسجيل مستخدم جديد (يتجاهل إذا موجود)"""
    uid = str(user.id)
    username = user.username or user.first_name or "User"
    now = datetime.now().isoformat()
    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT uid FROM users WHERE uid = :uid"),
            {"uid": uid}
        ).fetchone()
        
        if not result:
            conn.execute(text("""
                INSERT INTO users (
                    uid, username, points, accumulated_points, lang, rank,
                    rank_discount, invite_count, completed_quests, banned,
                    is_admin, verified, lang_selected, vip, total_spent,
                    streak_days, notifications_on, join_date, theme, last_active
                )
                VALUES (
                    :uid, :username, 0, 0, 'ar', 'عضو عادي 🔹',
                    0.0, 0, '', FALSE,
                    FALSE, FALSE, FALSE, FALSE, 0,
                    0, TRUE, :jd, 'dark', :la
                )
            """), {"uid": uid, "username": username, "jd": now, "la": now})
            conn.commit()
            
            # زيادة عداد الزيارات الكلي
            bot_config["total_visits"] = bot_config.get("total_visits", 0) + 1
            save_json(DB_CONFIG, bot_config)
        else:
            # تحديث آخر نشاط
            try:
                conn.execute(
                    text("UPDATE users SET last_active = :la WHERE uid = :uid"),
                    {"uid": uid, "la": now}
                )
                conn.commit()
            except: pass

# =====================================================
# 🔍 جلب بيانات مستخدم
# =====================================================
def get_user(uid):
    """جلب كل بيانات المستخدم"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE uid = :uid"),
            {"uid": str(uid)}
        ).fetchone()
        if result:
            return dict(result._mapping)
        return None

# =====================================================
# ✏️ تحديث بيانات مستخدم (ذكي ومرن)
# =====================================================
def update_user_data(uid, **kwargs):
    """
    تحديث بيانات المستخدم:
    - الحقول العددية: تُجمع (points += value)
    - الحقول النصية والمنطقية: تُستبدل
    """
    if not kwargs:
        return
    
    increment_fields = {
        "points", "accumulated_points", "invite_count",
        "total_spent", "streak_days", "purchases_count", "referral_earnings"
    }
    
    replace_fields = {
        "username", "lang", "rank", "rank_discount", "completed_quests",
        "invited_by", "last_claim", "banned", "banned_until", "is_admin",
        "verified", "lang_selected", "vip", "last_streak_date",
        "notifications_on", "join_date", "theme", "last_active"
    }
    
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

# =====================================================
# 🏆 تحديث الرتبة والمهام تلقائياً
# =====================================================
def update_user_rank_and_quests(uid):
    """
    فحص وتحديث:
    - الرتبة (تلقائي حسب النقاط)
    - المهام المكتملة
    - إرسال إشعارات
    """
    from config import RANKS
    
    u = get_user(uid)
    if not u:
        return
    
    acc_pts = u.get("accumulated_points", 0) or 0
    current_rank = u.get("rank", "عضو عادي 🔹")
    current_discount = u.get("rank_discount", 0.0) or 0.0
    lang = u.get("lang", "ar")
    
    # ═══════════════════════════════
    # 🏆 فحص الرتبة الجديدة
    # ═══════════════════════════════
    new_rank = "عضو عادي 🔹"
    new_discount = 0.0
    new_rank_key = None
    
    for rank_key in ["silver", "gold", "diamond", "hero", "master", "legend"]:
        rank_info = RANKS[rank_key]
        if acc_pts >= rank_info["points_needed"]:
            new_rank = rank_info.get(f"name_{lang}", rank_info.get("name_en", ""))
            new_discount = rank_info["discount"]
            new_rank_key = rank_key
    
    # ترقية!
    if new_rank != current_rank or abs(new_discount - current_discount) > 0.001:
        update_user_data(uid, rank=new_rank, rank_discount=new_discount)
        
        # 🎉 إشعار جميل بالترقية
        try:
            from config import bot
            promotion_msg = (
                f"╔═══════════════════╗\n"
                f"║  🎊 <b>RANK UP!</b> 🎊   ║\n"
                f"╚═══════════════════╝\n\n"
                f"🎉 <b>Congratulations!</b>\n\n"
                f"🎖️ <b>New Rank:</b> {new_rank}\n"
                f"💎 <b>Discount:</b> {int(new_discount*100)}%\n"
                f"📊 <b>Points:</b> {acc_pts}\n\n"
                f"✨ <i>Keep going for higher ranks!</i>"
            )
            bot.send_message(int(uid), promotion_msg, parse_mode="HTML")
        except: pass
    
    # ═══════════════════════════════
    # 🔥 فحص المهام المكتملة
    # ═══════════════════════════════
    completed = u.get("completed_quests", "") or ""
    quests = bot_config.get("quests", {})
    
    # مهمة الدعوات
    if "quest_invite" not in completed:
        invite_cnt = u.get("invite_count", 0) or 0
        target = quests.get("invite", {}).get("target", 5)
        reward = quests.get("invite", {}).get("reward", 100)
        if invite_cnt >= target:
            new_completed = (completed + ",quest_invite").strip(",")
            update_user_data(uid, completed_quests=new_completed, points=reward, accumulated_points=reward)
            try:
                from config import bot
                bot.send_message(int(uid),
                    f"🎉 <b>━━ Quest Completed! ━━</b>\n\n"
                    f"👥 <b>Invitations Master!</b>\n"
                    f"🎁 Reward: <b>+{reward}</b> 💎\n\n"
                    f"✨ <i>You're on fire!</i>",
                    parse_mode="HTML")
            except: pass
    
    # مهمة المبيعات
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
                bot.send_message(int(uid),
                    f"🎉 <b>━━ Quest Completed! ━━</b>\n\n"
                    f"🛒 <b>Shopping Expert!</b>\n"
                    f"🎁 Reward: <b>+{reward}</b> 💎\n\n"
                    f"✨ <i>Great customer!</i>",
                    parse_mode="HTML")
            except: pass
    
    # مهمة النقاط التراكمية
    if "quest_points" not in completed:
        target = quests.get("points", {}).get("target", 1000)
        reward = quests.get("points", {}).get("reward", 200)
        if acc_pts >= target:
            u_now = get_user(uid)
            new_completed = ((u_now.get("completed_quests", "") or "") + ",quest_points").strip(",")
            update_user_data(uid, completed_quests=new_completed, points=reward, accumulated_points=reward)
            try:
                from config import bot
                bot.send_message(int(uid),
                    f"🎉 <b>━━ Quest Completed! ━━</b>\n\n"
                    f"💎 <b>Points Collector!</b>\n"
                    f"🎁 Reward: <b>+{reward}</b> 💎\n\n"
                    f"✨ <i>You're unstoppable!</i>",
                    parse_mode="HTML")
            except: pass

# =====================================================
# 📊 دوال إحصائية مساعدة
# =====================================================
def get_total_users():
    """عدد المستخدمين الكلي"""
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()
            return r[0] if r else 0
    except:
        return 0

def get_active_users_today():
    """المستخدمون النشطون اليوم"""
    try:
        today = datetime.now().date().isoformat()
        with engine.connect() as conn:
            r = conn.execute(
                text("SELECT COUNT(*) FROM users WHERE last_active LIKE :today"),
                {"today": f"{today}%"}
            ).fetchone()
            return r[0] if r else 0
    except:
        return 0

def get_top_users_by_points(limit=10):
    """أعلى المستخدمين نقاطاً (للمتصدرين)"""
    try:
        with engine.connect() as conn:
            results = conn.execute(text(
                f"SELECT uid, username, accumulated_points FROM users "
                f"ORDER BY accumulated_points DESC LIMIT {limit}"
            )).fetchall()
            return [dict(r._mapping) for r in results]
    except:
        return []

def get_top_users_by_invites(limit=10):
    """أعلى المستخدمين دعوات"""
    try:
        with engine.connect() as conn:
            results = conn.execute(text(
                f"SELECT uid, username, invite_count FROM users "
                f"WHERE invite_count > 0 ORDER BY invite_count DESC LIMIT {limit}"
            )).fetchall()
            return [dict(r._mapping) for r in results]
    except:
        return []

def get_bot_stats():
    """إحصائيات شاملة عن البوت"""
    return {
        "total_users": get_total_users(),
        "active_today": get_active_users_today(),
        "total_sales": bot_config.get("total_sales", 0),
        "total_earnings": bot_config.get("total_earnings", 0),
        "total_products": len(prices_config),
        "total_codes": len(redeem_codes),
        "total_tickets": len(bot_config.get("tickets", {})),
        "open_tickets": len([t for t in bot_config.get("tickets", {}).values() if t.get("status", "open") == "open"]),
        "total_requests": len(bot_config.get("product_requests", {})),
        "bot_version": bot_config.get("bot_version", "3.0"),
        "maintenance": bot_config.get("maintenance", False)
    }

# =====================================================
# 🎨 دوال البحث والفلترة
# =====================================================
def search_user(query):
    """بحث عن مستخدم بالـ ID أو اليوزرنيم"""
    try:
        with engine.connect() as conn:
            # بحث بالـ ID
            if query.isdigit():
                r = conn.execute(
                    text("SELECT * FROM users WHERE uid = :q"),
                    {"q": query}
                ).fetchone()
                if r: return dict(r._mapping)
            
            # بحث باليوزرنيم
            q = query.replace("@", "")
            r = conn.execute(
                text("SELECT * FROM users WHERE LOWER(username) LIKE :q"),
                {"q": f"%{q.lower()}%"}
            ).fetchone()
            if r: return dict(r._mapping)
    except: pass
    return None

def get_all_admins():
    """جلب كل المشرفين"""
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT uid, username FROM users WHERE is_admin = TRUE")).fetchall()
            return [dict(row._mapping) for row in r]
    except:
        return []

# =====================================================
# 🛡️ دوال الحماية والأمان
# =====================================================
def ban_user(uid, permanent=True, hours=24):
    """حظر مستخدم"""
    if permanent:
        update_user_data(uid, banned=True)
    else:
        until = (datetime.now() + timedelta(hours=hours)).isoformat()
        update_user_data(uid, banned_until=until)

def unban_user(uid):
    """فك الحظر"""
    update_user_data(uid, banned=False, banned_until=None)

# =====================================================
# 🎯 تصدير كل الدوال المطلوبة
# =====================================================
__all__ = [
    'engine', 'text', 'init_db', 'get_user', 'update_user_data',
    'register_user', 'users', 'keys_store', 'redeem_codes',
    'prices_config', 'bot_config', 'save_json', 'load_json',
    'DB_USERS', 'DB_KEYS', 'DB_REDEEM', 'DB_PRICES', 'DB_CONFIG',
    'update_user_rank_and_quests', 'get_total_users', 'get_active_users_today',
    'get_top_users_by_points', 'get_top_users_by_invites', 'get_bot_stats',
    'search_user', 'get_all_admins', 'ban_user', 'unban_user'
]
