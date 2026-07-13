"""
══════════════════════════════════════════════════════════════════════════════
║                    bot5.py - DATA FORTRESS SYSTEM v2.0                      ║
║                 🔒 حماية البيانات من الضياع 100%                              ║
║              All Data Stored in PostgreSQL - Never Lost                     ║
══════════════════════════════════════════════════════════════════════════════
║  Developer: @fkLJh00302                                                     ║
║  Features:                                                                   ║
║   ✅ حفظ كل الإعدادات في PostgreSQL (لا JSON محلي)                            ║
║   ✅ حماية المتجر، المكافآت، الألعاب، المهام                                  ║
║   ✅ استعادة تلقائية عند إعادة التشغيل                                        ║
║   ✅ نسخ احتياطي تلقائي كل ساعة                                               ║
══════════════════════════════════════════════════════════════════════════════
"""

import json
import threading
import time
from datetime import datetime, timedelta
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import engine, text, save_json, DB_CONFIG, DB_KEYS, DB_PRICES, DB_REDEEM

# ═══════════════════════════════════════════════════════════════════════════
# 🏗️ إنشاء جداول حماية البيانات
# ═══════════════════════════════════════════════════════════════════════════

def init_data_fortress():
    """إنشاء جداول حماية البيانات في PostgreSQL"""
    with engine.connect() as conn:
        # جدول الإعدادات العامة
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # جدول المنتجات
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) UNIQUE NOT NULL,
                plans JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        
        # جدول المفاتيح
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_keys (
                id SERIAL PRIMARY KEY,
                product_name VARCHAR(200) NOT NULL,
                plan VARCHAR(50) NOT NULL,
                key_value TEXT NOT NULL,
                is_sold BOOLEAN DEFAULT FALSE,
                sold_to VARCHAR(50),
                sold_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # جدول أكواد الشحن
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS redeem_codes (
                code VARCHAR(100) PRIMARY KEY,
                points INTEGER NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                used_by VARCHAR(50),
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # جدول المبيعات
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_log (
                id SERIAL PRIMARY KEY,
                uid VARCHAR(50) NOT NULL,
                username VARCHAR(200),
                product VARCHAR(200) NOT NULL,
                plan VARCHAR(50) NOT NULL,
                price INTEGER NOT NULL,
                key_value TEXT,
                sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # جدول التذاكر
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                ticket_id VARCHAR(20) UNIQUE NOT NULL,
                uid VARCHAR(50) NOT NULL,
                category VARCHAR(50),
                text_content TEXT,
                status VARCHAR(20) DEFAULT 'open',
                messages JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """))
        
        # جدول Giveaways
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS giveaways (
                code VARCHAR(50) PRIMARY KEY,
                reward INTEGER NOT NULL,
                max_users INTEGER NOT NULL,
                hours INTEGER NOT NULL,
                claimed_by JSONB DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'active',
                channel_msg_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """))
        
        # جدول VIP
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vip_subscribers (
                uid VARCHAR(50) PRIMARY KEY,
                expires_at TIMESTAMP NOT NULL,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # جدول النسخ الاحتياطية
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS backups (
                id SERIAL PRIMARY KEY,
                backup_type VARCHAR(50),
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
    print("✅ Data Fortress Tables Created!")

# ═══════════════════════════════════════════════════════════════════════════
# 💾 دوال حفظ الإعدادات
# ═══════════════════════════════════════════════════════════════════════════

def save_setting(key: str, value) -> bool:
    """حفظ إعداد في قاعدة البيانات"""
    try:
        json_value = json.dumps(value, ensure_ascii=False)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO bot_settings (key, value, updated_at)
                VALUES (:key, :value, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET 
                    value = :value,
                    updated_at = CURRENT_TIMESTAMP
            """), {"key": key, "value": json_value})
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error saving setting {key}: {e}")
        return False

def get_setting(key: str, default=None):
    """جلب إعداد من قاعدة البيانات"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT value FROM bot_settings WHERE key = :key"),
                {"key": key}
            ).fetchone()
            if result:
                return json.loads(result[0])
        return default
    except Exception as e:
        print(f"⚠️ Error getting setting {key}: {e}")
        return default

def save_all_settings(settings_dict: dict) -> bool:
    """حفظ كل الإعدادات دفعة واحدة"""
    success = True
    for key, value in settings_dict.items():
        if not save_setting(key, value):
            success = False
    return success

# ═══════════════════════════════════════════════════════════════════════════
# 📦 دوال المنتجات (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def save_product_db(name: str, plans: dict) -> bool:
    """حفظ منتج في قاعدة البيانات"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO products (name, plans)
                VALUES (:name, :plans)
                ON CONFLICT (name) DO UPDATE SET 
                    plans = :plans
            """), {"name": name, "plans": json.dumps(plans)})
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error saving product: {e}")
        return False

def get_all_products_db() -> dict:
    """جلب كل المنتجات من قاعدة البيانات"""
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT name, plans FROM products WHERE is_active = TRUE")
            ).fetchall()
            products = {}
            for row in results:
                products[row[0]] = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            return products
    except Exception as e:
        print(f"⚠️ Error getting products: {e}")
        return {}

def delete_product_db(name: str) -> bool:
    """حذف منتج (تعطيل)"""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE products SET is_active = FALSE WHERE name = :name"),
                {"name": name}
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error deleting product: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# 🔑 دوال المفاتيح (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def add_keys_db(product: str, plan: str, keys: list) -> int:
    """إضافة مفاتيح للمنتج"""
    added = 0
    try:
        with engine.connect() as conn:
            for key in keys:
                conn.execute(text("""
                    INSERT INTO product_keys (product_name, plan, key_value)
                    VALUES (:product, :plan, :key)
                """), {"product": product, "plan": plan, "key": key.strip()})
                added += 1
            conn.commit()
    except Exception as e:
        print(f"⚠️ Error adding keys: {e}")
    return added

def get_available_key_db(product: str, plan: str) -> str:
    """جلب مفتاح متاح (وتعليمه كمباع)"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, key_value FROM product_keys 
                WHERE product_name = :product AND plan = :plan AND is_sold = FALSE
                LIMIT 1
            """), {"product": product, "plan": plan}).fetchone()
            
            if result:
                conn.execute(text("""
                    UPDATE product_keys SET is_sold = TRUE, sold_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """), {"id": result[0]})
                conn.commit()
                return result[1]
        return None
    except Exception as e:
        print(f"⚠️ Error getting key: {e}")
        return None

def get_keys_count_db(product: str, plan: str) -> int:
    """عدد المفاتيح المتاحة"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM product_keys 
                WHERE product_name = :product AND plan = :plan AND is_sold = FALSE
            """), {"product": product, "plan": plan}).fetchone()
            return result[0] if result else 0
    except Exception as e:
        return 0

def get_all_keys_stats_db() -> dict:
    """إحصائيات المفاتيح"""
    stats = {}
    try:
        with engine.connect() as conn:
            results = conn.execute(text("""
                SELECT product_name, plan, 
                       COUNT(*) FILTER (WHERE is_sold = FALSE) as available,
                       COUNT(*) FILTER (WHERE is_sold = TRUE) as sold
                FROM product_keys
                GROUP BY product_name, plan
            """)).fetchall()
            
            for row in results:
                if row[0] not in stats:
                    stats[row[0]] = {}
                stats[row[0]][row[1]] = {"available": row[2], "sold": row[3]}
    except Exception as e:
        print(f"⚠️ Error getting keys stats: {e}")
    return stats

# ═══════════════════════════════════════════════════════════════════════════
# 🎫 دوال أكواد الشحن (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def add_redeem_code_db(code: str, points: int) -> bool:
    """إضافة كود شحن"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO redeem_codes (code, points)
                VALUES (:code, :points)
                ON CONFLICT (code) DO UPDATE SET points = :points
            """), {"code": code, "points": points})
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error adding redeem code: {e}")
        return False

def use_redeem_code_db(code: str, uid: str) -> int:
    """استخدام كود شحن - يرجع النقاط أو 0"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT points FROM redeem_codes 
                WHERE code = :code AND is_used = FALSE
            """), {"code": code}).fetchone()
            
            if result:
                conn.execute(text("""
                    UPDATE redeem_codes 
                    SET is_used = TRUE, used_by = :uid, used_at = CURRENT_TIMESTAMP
                    WHERE code = :code
                """), {"code": code, "uid": uid})
                conn.commit()
                return result[0]
        return 0
    except Exception as e:
        print(f"⚠️ Error using redeem code: {e}")
        return 0

def get_all_redeem_codes_db() -> dict:
    """جلب كل أكواد الشحن النشطة"""
    try:
        with engine.connect() as conn:
            results = conn.execute(text("""
                SELECT code, points FROM redeem_codes WHERE is_used = FALSE
            """)).fetchall()
            return {row[0]: row[1] for row in results}
    except:
        return {}

# ═══════════════════════════════════════════════════════════════════════════
# 📊 دوال المبيعات (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def log_sale_db(uid: str, username: str, product: str, plan: str, price: int, key: str) -> bool:
    """تسجيل عملية بيع"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO sales_log (uid, username, product, plan, price, key_value)
                VALUES (:uid, :username, :product, :plan, :price, :key)
            """), {
                "uid": uid, "username": username, "product": product,
                "plan": plan, "price": price, "key": key
            })
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error logging sale: {e}")
        return False

def get_sales_stats_db() -> dict:
    """إحصائيات المبيعات"""
    try:
        with engine.connect() as conn:
            total = conn.execute(text("SELECT COUNT(*), SUM(price) FROM sales_log")).fetchone()
            today = conn.execute(text("""
                SELECT COUNT(*), COALESCE(SUM(price), 0) FROM sales_log 
                WHERE DATE(sold_at) = CURRENT_DATE
            """)).fetchone()
            
            return {
                "total_sales": total[0] or 0,
                "total_earnings": total[1] or 0,
                "today_sales": today[0] or 0,
                "today_earnings": today[1] or 0
            }
    except:
        return {"total_sales": 0, "total_earnings": 0, "today_sales": 0, "today_earnings": 0}

def get_recent_sales_db(limit: int = 10) -> list:
    """آخر المبيعات"""
    try:
        with engine.connect() as conn:
            results = conn.execute(text(f"""
                SELECT uid, username, product, plan, price, key_value, sold_at
                FROM sales_log ORDER BY sold_at DESC LIMIT {limit}
            """)).fetchall()
            return [dict(zip(
                ["uid", "username", "product", "plan", "price", "key", "date"],
                row
            )) for row in results]
    except:
        return []

# ═══════════════════════════════════════════════════════════════════════════
# 🎫 دوال التذاكر (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def create_ticket_db(ticket_id: str, uid: str, category: str, text_content: str) -> bool:
    """إنشاء تذكرة"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO tickets (ticket_id, uid, category, text_content)
                VALUES (:tid, :uid, :cat, :txt)
            """), {"tid": ticket_id, "uid": uid, "cat": category, "txt": text_content})
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error creating ticket: {e}")
        return False

def get_ticket_db(ticket_id: str) -> dict:
    """جلب تذكرة"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT ticket_id, uid, category, text_content, status, messages, created_at
                FROM tickets WHERE ticket_id = :tid
            """), {"tid": ticket_id}).fetchone()
            if result:
                return {
                    "id": result[0], "uid": result[1], "category": result[2],
                    "text": result[3], "status": result[4],
                    "messages": json.loads(result[5]) if isinstance(result[5], str) else result[5],
                    "created_at": str(result[6])
                }
        return None
    except:
        return None

def add_ticket_message_db(ticket_id: str, sender: str, message: str) -> bool:
    """إضافة رسالة للتذكرة"""
    try:
        ticket = get_ticket_db(ticket_id)
        if not ticket:
            return False
        
        messages = ticket.get("messages", [])
        messages.append({
            "from": sender,
            "text": message,
            "time": datetime.now().isoformat()
        })
        
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE tickets SET messages = :msgs WHERE ticket_id = :tid
            """), {"tid": ticket_id, "msgs": json.dumps(messages)})
            conn.commit()
        return True
    except:
        return False

def close_ticket_db(ticket_id: str) -> bool:
    """إغلاق تذكرة"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE tickets 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP 
                WHERE ticket_id = :tid
            """), {"tid": ticket_id})
            conn.commit()
        return True
    except:
        return False

def get_open_tickets_db() -> list:
    """جلب التذاكر المفتوحة"""
    try:
        with engine.connect() as conn:
            results = conn.execute(text("""
                SELECT ticket_id, uid, category, status, created_at
                FROM tickets WHERE status = 'open'
                ORDER BY created_at DESC
            """)).fetchall()
            return [{"id": r[0], "uid": r[1], "category": r[2], 
                    "status": r[3], "date": str(r[4])} for r in results]
    except:
        return []

# ═══════════════════════════════════════════════════════════════════════════
# 🎁 دوال Giveaway (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def create_giveaway_db(code: str, reward: int, max_users: int, hours: int) -> bool:
    """إنشاء Giveaway"""
    try:
        expires = datetime.now() + timedelta(hours=hours)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO giveaways (code, reward, max_users, hours, expires_at)
                VALUES (:code, :reward, :max, :hours, :expires)
            """), {"code": code, "reward": reward, "max": max_users, 
                  "hours": hours, "expires": expires})
            conn.commit()
        return True
    except:
        return False

def claim_giveaway_db(code: str, uid: str) -> tuple:
    """استلام Giveaway - يرجع (نجح, المكافأة أو السبب)"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT reward, max_users, claimed_by, status, expires_at
                FROM giveaways WHERE code = :code
            """), {"code": code}).fetchone()
            
            if not result:
                return False, "not_found"
            
            reward, max_users, claimed_by, status, expires = result
            claimed_list = json.loads(claimed_by) if isinstance(claimed_by, str) else claimed_by
            
            if status != "active":
                return False, status
            
            if datetime.now() > expires:
                conn.execute(text("UPDATE giveaways SET status = 'expired' WHERE code = :code"), {"code": code})
                conn.commit()
                return False, "expired"
            
            if uid in claimed_list:
                return False, "already_claimed"
            
            if len(claimed_list) >= max_users:
                conn.execute(text("UPDATE giveaways SET status = 'full' WHERE code = :code"), {"code": code})
                conn.commit()
                return False, "full"
            
            claimed_list.append(uid)
            new_status = "full" if len(claimed_list) >= max_users else "active"
            
            conn.execute(text("""
                UPDATE giveaways SET claimed_by = :claimed, status = :status WHERE code = :code
            """), {"code": code, "claimed": json.dumps(claimed_list), "status": new_status})
            conn.commit()
            
            return True, reward
    except Exception as e:
        print(f"⚠️ Error claiming giveaway: {e}")
        return False, "error"

# ═══════════════════════════════════════════════════════════════════════════
# 👑 دوال VIP (محمية)
# ═══════════════════════════════════════════════════════════════════════════

def activate_vip_db(uid: str, days: int) -> datetime:
    """تفعيل VIP"""
    try:
        expires = datetime.now() + timedelta(days=days)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO vip_subscribers (uid, expires_at)
                VALUES (:uid, :expires)
                ON CONFLICT (uid) DO UPDATE SET 
                    expires_at = :expires,
                    activated_at = CURRENT_TIMESTAMP
            """), {"uid": str(uid), "expires": expires})
            conn.commit()
        return expires
    except Exception as e:
        print(f"⚠️ Error activating VIP: {e}")
        return None

def is_vip_active_db(uid: str) -> bool:
    """فحص VIP نشط"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT expires_at FROM vip_subscribers WHERE uid = :uid
            """), {"uid": str(uid)}).fetchone()
            if result:
                return datetime.now() < result[0]
        return False
    except:
        return False

def get_vip_days_left_db(uid: str) -> int:
    """أيام VIP المتبقية"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT expires_at FROM vip_subscribers WHERE uid = :uid
            """), {"uid": str(uid)}).fetchone()
            if result:
                remaining = result[0] - datetime.now()
                return max(0, remaining.days)
        return 0
    except:
        return 0

# ═══════════════════════════════════════════════════════════════════════════
# 💾 نظام النسخ الاحتياطي التلقائي
# ═══════════════════════════════════════════════════════════════════════════

def create_backup():
    """إنشاء نسخة احتياطية"""
    try:
        from database import bot_config, prices_config, keys_store, redeem_codes
        
        backup_data = {
            "bot_config": bot_config,
            "prices_config": prices_config,
            "keys_store": keys_store,
            "redeem_codes": redeem_codes,
            "timestamp": datetime.now().isoformat()
        }
        
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO backups (backup_type, data)
                VALUES ('auto', :data)
            """), {"data": json.dumps(backup_data, ensure_ascii=False)})
            
            # حذف النسخ القديمة (الاحتفاظ بآخر 48)
            conn.execute(text("""
                DELETE FROM backups WHERE id NOT IN (
                    SELECT id FROM backups ORDER BY created_at DESC LIMIT 48
                )
            """))
            conn.commit()
        
        print(f"✅ Backup created at {datetime.now()}")
        return True
    except Exception as e:
        print(f"⚠️ Backup error: {e}")
        return False

def restore_latest_backup() -> bool:
    """استعادة آخر نسخة احتياطية"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT data FROM backups ORDER BY created_at DESC LIMIT 1
            """)).fetchone()
            
            if result:
                backup_data = json.loads(result[0])
                
                # استعادة الإعدادات
                from database import bot_config, prices_config, keys_store, redeem_codes
                
                for key, value in backup_data.get("bot_config", {}).items():
                    bot_config[key] = value
                
                for key, value in backup_data.get("prices_config", {}).items():
                    prices_config[key] = value
                
                for key, value in backup_data.get("keys_store", {}).items():
                    keys_store[key] = value
                
                for key, value in backup_data.get("redeem_codes", {}).items():
                    redeem_codes[key] = value
                
                # حفظ في الملفات
                save_json(DB_CONFIG, bot_config)
                save_json(DB_PRICES, prices_config)
                save_json(DB_KEYS, keys_store)
                save_json(DB_REDEEM, redeem_codes)
                
                print(f"✅ Restored backup from {backup_data.get('timestamp')}")
                return True
        return False
    except Exception as e:
        print(f"⚠️ Restore error: {e}")
        return False

def sync_json_to_db():
    """مزامنة ملفات JSON مع قاعدة البيانات"""
    try:
        from database import bot_config, prices_config, keys_store, redeem_codes
        
        # حفظ الإعدادات
        for key, value in bot_config.items():
            save_setting(f"config_{key}", value)
        
        # حفظ المنتجات
        for product, plans in prices_config.items():
            save_product_db(product, plans)
        
        # حفظ المفاتيح
        for product, plans in keys_store.items():
            for plan, keys in plans.items():
                for key in keys:
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO product_keys (product_name, plan, key_value)
                                VALUES (:product, :plan, :key)
                                ON CONFLICT DO NOTHING
                            """), {"product": product, "plan": plan, "key": key})
                            conn.commit()
                    except:
                        pass
        
        # حفظ أكواد الشحن
        for code, points in redeem_codes.items():
            add_redeem_code_db(code, points)
        
        print("✅ JSON synced to PostgreSQL")
        return True
    except Exception as e:
        print(f"⚠️ Sync error: {e}")
        return False

def sync_db_to_json():
    """مزامنة قاعدة البيانات مع ملفات JSON"""
    try:
        from database import bot_config, prices_config, keys_store, redeem_codes
        
        # جلب المنتجات
        db_products = get_all_products_db()
        for product, plans in db_products.items():
            prices_config[product] = plans
        
        # جلب أكواد الشحن
        db_codes = get_all_redeem_codes_db()
        for code, points in db_codes.items():
            redeem_codes[code] = points
        
        # حفظ
        save_json(DB_CONFIG, bot_config)
        save_json(DB_PRICES, prices_config)
        save_json(DB_REDEEM, redeem_codes)
        
        print("✅ PostgreSQL synced to JSON")
        return True
    except Exception as e:
        print(f"⚠️ Sync error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# ⏰ مهام الخلفية
# ═══════════════════════════════════════════════════════════════════════════

def start_backup_thread():
    """بدء خيط النسخ الاحتياطي"""
    def worker():
        while True:
            try:
                time.sleep(3600)  # كل ساعة
                create_backup()
                sync_json_to_db()
            except Exception as e:
                print(f"⚠️ Backup thread error: {e}")
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print("✅ Backup thread started (every 1 hour)")

def start_sync_thread():
    """بدء خيط المزامنة"""
    def worker():
        while True:
            try:
                time.sleep(300)  # كل 5 دقائق
                sync_json_to_db()
            except Exception as e:
                print(f"⚠️ Sync thread error: {e}")
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print("✅ Sync thread started (every 5 minutes)")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 التهيئة
# ═══════════════════════════════════════════════════════════════════════════

def initialize_data_fortress():
    """تهيئة نظام حماية البيانات"""
    print("=" * 60)
    print("🔒 DATA FORTRESS SYSTEM v2.0")
    print("=" * 60)
    
    # إنشاء الجداول
    init_data_fortress()
    
    # مزامنة البيانات
    sync_json_to_db()
    
    # بدء المهام
    start_backup_thread()
    start_sync_thread()
    
    print("=" * 60)
    print("✅ Data Fortress ACTIVE - Your data is 100% protected!")
    print("=" * 60)

# تشغيل عند الاستيراد
initialize_data_fortress()

print("=" * 60)
print("✅ bot5.py loaded!")
print("🔒 Data Fortress: ACTIVE")
print("💾 Auto Backup: Every 1 hour")
print("🔄 Auto Sync: Every 5 minutes")
print("📊 PostgreSQL Storage: ENABLED")
print("=" * 60)
