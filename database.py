import os
import json
import tempfile
import threading
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from config import CHANNEL_ID, CHANNEL_LINK

# PostgreSQL is the durable source of truth for the legacy JSON-shaped stores.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. Configure PostgreSQL before starting the bot."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)

_STATE_TABLE = "bot_state"
_state_lock = threading.RLock()
_state_table_ready = False
_file_locks = {}
_file_locks_guard = threading.Lock()


def _ensure_state_table():
    """Create the generic state table once, safely across concurrent callers."""
    global _state_table_ready
    if _state_table_ready:
        return
    with _state_lock:
        if _state_table_ready:
            return
        with engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {_STATE_TABLE} (
                    store_key VARCHAR(100) PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
        _state_table_ready = True


def _file_lock(filename):
    with _file_locks_guard:
        return _file_locks.setdefault(filename, threading.RLock())


def _write_legacy_mirror(filename, data):
    """Write a best-effort atomic local mirror for migration/older tooling."""
    directory = os.path.dirname(os.path.abspath(filename))
    temp_path = None
    try:
        with _file_lock(filename):
            fd, temp_path = tempfile.mkstemp(
                prefix=".bot-state-", suffix=".tmp", dir=directory
            )
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=4, ensure_ascii=False, default=str)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, filename)
            temp_path = None
    except Exception as exc:
        # PostgreSQL already committed; mirror failure must not misreport DB failure.
        print(f"⚠️ تعذر تحديث النسخة المحلية الاختيارية {filename}: {exc}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

# =====================================================
# 📁 أسماء ملفات JSON
# =====================================================
DB_USERS = 'users_data.json'
DB_KEYS = 'keys_store.json'
DB_REDEEM = 'redeem_codes.json'
DB_PRICES = 'prices_config.json'
DB_CONFIG = 'bot_config.json'

# =====================================================
# 🔧 توافق JSON مع تخزين دائم وفوري في PostgreSQL
# =====================================================
def load_json(filename):
    """
    Load a store from PostgreSQL. If this is the first migration, import its
    legacy JSON file into PostgreSQL once. The local file is only a mirror.
    """
    _ensure_state_table()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT data_json FROM {_STATE_TABLE} WHERE store_key = :k"),
            {"k": filename},
        ).fetchone()

    if row and row[0] is not None:
        try:
            return json.loads(row[0])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Stored state for {filename} is invalid JSON; refusing silent reset."
            ) from exc

    legacy_data = {}
    if os.path.exists(filename):
        try:
            with _file_lock(filename), open(filename, "r", encoding="utf-8") as stream:
                legacy_data = json.load(stream)
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"Could not read legacy state file {filename}: {exc}") from exc

    # Import legacy data (including an empty object) so future reads are DB-backed.
    payload = json.dumps(legacy_data, ensure_ascii=False, default=str)
    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO {_STATE_TABLE} (store_key, data_json, updated_at)
            VALUES (:k, :d, CURRENT_TIMESTAMP)
            ON CONFLICT (store_key)
            DO NOTHING
        """), {"k": filename, "d": payload})

    # Another process may have won the first-write race; read its committed row.
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT data_json FROM {_STATE_TABLE} WHERE store_key = :k"),
            {"k": filename},
        ).fetchone()
    if not row or row[0] is None:
        raise RuntimeError(f"Failed to initialize persistent state for {filename}")
    return json.loads(row[0])


def save_json(filename, data):
    """
    Persist the complete store to PostgreSQL before returning.
    Local JSON is retained only as an atomic compatibility/migration mirror.
    Database errors are raised rather than swallowed so callers cannot mistake
    a failed durable write for a successful save.
    """
    _ensure_state_table()
    with _state_lock:
        payload = json.dumps(data, ensure_ascii=False, default=str)
        with engine.begin() as conn:
            conn.execute(text(f"""
                INSERT INTO {_STATE_TABLE} (store_key, data_json, updated_at)
                VALUES (:k, :d, CURRENT_TIMESTAMP)
                ON CONFLICT (store_key)
                DO UPDATE SET data_json = EXCLUDED.data_json,
                              updated_at = CURRENT_TIMESTAMP
            """), {"k": filename, "d": payload})
        _write_legacy_mirror(filename, data)


def get_json_state_updated_at(filename):
    """Return the last PostgreSQL commit timestamp for a persisted store."""
    _ensure_state_table()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT updated_at FROM {_STATE_TABLE} WHERE store_key = :k"),
            {"k": filename},
        ).fetchone()
    return row[0] if row else None


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
    "bot_launch_date": datetime.now().isoformat(),

    # Subscription and administrator-managed publishing
    "force_sub_channels": [],
    "managed_channels": [],

    # Bounded payment IDs used to prevent duplicate channel announcements when
    # more than one Telegram payment handler receives the same update.
    "channel_payment_announcements": []
}

# دمج الإعدادات الافتراضية مع الحالية
for key, val in default_config.items():
    if key not in bot_config:
        bot_config[key] = val

# Seed the legacy channel once, while retaining administrator customisation.
if not bot_config.get("force_sub_channels") and CHANNEL_ID:
    bot_config["force_sub_channels"] = [{"id": int(CHANNEL_ID), "label": "القناة", "url": CHANNEL_LINK}]
save_json(DB_CONFIG, bot_config)

# =====================================================
# 🔌 اتصال PostgreSQL مهيأ في أعلى الملف
# =====================================================

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
        with engine.begin() as conn:
            result = conn.execute(text(query), params)
        return result.rowcount > 0
    except Exception as e:
        print(f"❌ خطأ update_user_data للمستخدم {uid}: {e}")
        raise RuntimeError(f"Failed to update user {uid}") from e


# =====================================================
# 🛒 شراء ذري: خصم الرصيد وسحب المخزون وتسجيل البيع معاً
# =====================================================
def purchase_key_atomic(uid, product, plan, price, username=""):
    """
    Atomically reserve one key, deduct points and record the sale.
    PostgreSQL row locks prevent two concurrent purchases from taking the same
    key or spending the same balance. Raises ValueError with a stable reason.
    """
    uid = str(uid)
    price = int(price)
    if price < 0:
        raise ValueError("invalid_price")

    _ensure_state_table()
    with _state_lock:
        with engine.begin() as conn:
            user_row = conn.execute(
                text("SELECT points FROM users WHERE uid = :uid FOR UPDATE"),
                {"uid": uid},
            ).fetchone()
            if not user_row:
                raise ValueError("user_not_found")
            current_points = int(user_row[0] or 0)
            if current_points < price:
                raise ValueError("insufficient_balance")

            keys_row = conn.execute(
                text(f"SELECT data_json FROM {_STATE_TABLE} WHERE store_key = :k FOR UPDATE"),
                {"k": DB_KEYS},
            ).fetchone()
            config_row = conn.execute(
                text(f"SELECT data_json FROM {_STATE_TABLE} WHERE store_key = :k FOR UPDATE"),
                {"k": DB_CONFIG},
            ).fetchone()
            if not keys_row or not config_row:
                raise RuntimeError("Persistent store is missing keys or bot configuration")

            stored_keys = json.loads(keys_row[0])
            stored_config = json.loads(config_row[0])
            product_data = stored_keys.get(product, {})
            stock = product_data.get(plan, []) if isinstance(product_data, dict) else []
            if not isinstance(stock, list) or not stock:
                raise ValueError("out_of_stock")

            key = stock.pop(0)
            product_data[plan] = stock
            stored_keys[product] = product_data

            stored_config["total_sales"] = int(stored_config.get("total_sales", 0) or 0) + 1
            stored_config["total_earnings"] = int(stored_config.get("total_earnings", 0) or 0) + price
            sales_log = stored_config.setdefault("sales_log", [])
            if not isinstance(sales_log, list):
                raise RuntimeError("Invalid sales_log data in persistent store")
            sales_log.append({
                "uid": uid,
                "username": username or "",
                "product": product,
                "plan": plan,
                "price": price,
                "key": key,
                "date": datetime.now().isoformat(),
            })

            remaining = conn.execute(
                text("""
                    UPDATE users
                    SET points = COALESCE(points, 0) - :price,
                        total_spent = COALESCE(total_spent, 0) + :price,
                        purchases_count = COALESCE(purchases_count, 0) + 1
                    WHERE uid = :uid AND COALESCE(points, 0) >= :price
                    RETURNING points
                """),
                {"uid": uid, "price": price},
            ).fetchone()
            if not remaining:
                raise ValueError("insufficient_balance")

            conn.execute(text(f"""
                UPDATE {_STATE_TABLE}
                SET data_json = :data, updated_at = CURRENT_TIMESTAMP
                WHERE store_key = :k
            """), {
                "data": json.dumps(stored_keys, ensure_ascii=False, default=str),
                "k": DB_KEYS,
            })
            conn.execute(text(f"""
                UPDATE {_STATE_TABLE}
                SET data_json = :data, updated_at = CURRENT_TIMESTAMP
                WHERE store_key = :k
            """), {
                "data": json.dumps(stored_config, ensure_ascii=False, default=str),
                "k": DB_CONFIG,
            })

        # Reflect only committed values in the in-memory compatibility stores.
        keys_store.clear()
        keys_store.update(stored_keys)
        bot_config.clear()
        bot_config.update(stored_config)
        _write_legacy_mirror(DB_KEYS, keys_store)
        _write_legacy_mirror(DB_CONFIG, bot_config)

    return key, len(stock), int(remaining[0] or 0)


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


# =====================================================
# 📦 تصدير/استيراد نسخة كاملة قابلة للنقل بين قواعد Railway
# =====================================================
BACKUP_VERSION = 1


def export_full_backup():
    """Export canonical JSON stores and relational user records to a portable JSON object."""
    _ensure_state_table()
    # Flush the current in-memory stores before taking the export snapshot.
    # This also captures settings that a feature updated just before /backup.
    for filename, data in (
        (DB_USERS, users),
        (DB_KEYS, keys_store),
        (DB_REDEEM, redeem_codes),
        (DB_PRICES, prices_config),
        (DB_CONFIG, bot_config),
    ):
        save_json(filename, data)

    with _state_lock, engine.begin() as conn:
        state_rows = conn.execute(text(
            f"SELECT store_key, data_json FROM {_STATE_TABLE} ORDER BY store_key"
        )).fetchall()
        user_rows = conn.execute(text("SELECT * FROM users ORDER BY uid")).fetchall()
        user_columns = list(conn.execute(text(
            "SELECT * FROM users LIMIT 0"
        )).keys())

    return {
        "format": "telegram_bot_full_backup",
        "version": BACKUP_VERSION,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "state": [{"key": row[0], "data_json": row[1]} for row in state_rows],
        "users_table": {
            "columns": user_columns,
            "rows": [dict(row._mapping) for row in user_rows],
        },
    }


def restore_full_backup(backup):
    """
    Restore a portable backup into an EMPTY users table.
    Refuses non-empty destinations to avoid accidental data loss.
    """
    if not isinstance(backup, dict) or backup.get("format") != "telegram_bot_full_backup":
        raise ValueError("invalid_backup_format")
    if backup.get("version") != BACKUP_VERSION:
        raise ValueError("unsupported_backup_version")
    state_rows = backup.get("state")
    user_table = backup.get("users_table")
    if not isinstance(state_rows, list) or not isinstance(user_table, dict):
        raise ValueError("invalid_backup_structure")
    user_columns = user_table.get("columns")
    user_rows = user_table.get("rows")
    if not isinstance(user_columns, list) or not isinstance(user_rows, list):
        raise ValueError("invalid_users_section")
    if any(not isinstance(row, dict) for row in user_rows):
        raise ValueError("invalid_users_rows")
    allowed_user_columns = set(user_columns)
    if not allowed_user_columns or "uid" not in allowed_user_columns:
        raise ValueError("invalid_users_columns")
    for row in user_rows:
        if set(row) - allowed_user_columns:
            raise ValueError("unexpected_user_columns")

    seen_keys = set()
    for row in state_rows:
        if not isinstance(row, dict) or not isinstance(row.get("key"), str) or not isinstance(row.get("data_json"), str):
            raise ValueError("invalid_state_row")
        if row["key"] in seen_keys:
            raise ValueError("duplicate_state_key")
        seen_keys.add(row["key"])
        # Refuse malformed state rather than importing a broken backup.
        json.loads(row["data_json"])

    _ensure_state_table()
    with _state_lock, engine.begin() as conn:
        existing_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
        if existing_users:
            raise ValueError("destination_not_empty")

        live_columns = set(conn.execute(text("SELECT * FROM users LIMIT 0")).keys())
        if not allowed_user_columns.issubset(live_columns):
            raise ValueError("users_schema_mismatch")

        # This function is intended for a fresh destination database only.
        conn.execute(text(f"DELETE FROM {_STATE_TABLE}"))
        conn.execute(text("DELETE FROM users"))

        for row in state_rows:
            conn.execute(text(f"""
                INSERT INTO {_STATE_TABLE} (store_key, data_json, updated_at)
                VALUES (:k, :d, CURRENT_TIMESTAMP)
            """), {"k": row["key"], "d": row["data_json"]})

        if user_rows:
            columns_sql = ", ".join(f'"{name}"' for name in user_columns)
            values_sql = ", ".join(f":{name}" for name in user_columns)
            insert_sql = text(f"INSERT INTO users ({columns_sql}) VALUES ({values_sql})")
            for row in user_rows:
                conn.execute(insert_sql, row)

    # Refresh shared dictionaries in-place so modules importing them see restored data.
    global_state_map = {
        DB_USERS: "users",
        DB_KEYS: "keys_store",
        DB_REDEEM: "redeem_codes",
        DB_PRICES: "prices_config",
        DB_CONFIG: "bot_config",
    }
    for store_key, attr in global_state_map.items():
        match = next((item for item in state_rows if item["key"] == store_key), None)
        if match:
            restored_value = json.loads(match["data_json"])
            current_value = globals().get(attr)
            if isinstance(current_value, dict) and isinstance(restored_value, dict):
                current_value.clear()
                current_value.update(restored_value)
            elif isinstance(current_value, list) and isinstance(restored_value, list):
                current_value[:] = restored_value
    return {"state_stores": len(state_rows), "users": len(user_rows)}
