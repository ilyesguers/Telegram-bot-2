"""
=====================================================
 bot9.py — نظام النجوم المتكامل + إصلاح عجلة الحظ
=====================================================
⭐ تحكم كامل بالنجوم للأدمن
🎡 إصلاح عجلة الحظ
💳 نظام الدفع الكامل

📌 الأوامر:
   /stars - لوحة تحكم النجوم (للأدمن فقط)

📌 طريقة التركيب:
   في bot.py، أضف: import bot9
=====================================================
"""

import random
import time
from datetime import datetime, timedelta
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID
from database import (bot_config, save_json, DB_CONFIG, get_user, 
                       update_user_data, update_user_rank_and_quests)

# =====================================================
# 🔧 إصلاح allowed_updates
# =====================================================
_original_infinity_polling = bot.infinity_polling

def _patched_infinity_polling(*args, **kwargs):
    kwargs.setdefault("allowed_updates", [
        "message", "edited_message", "callback_query",
        "pre_checkout_query", "shipping_query",
        "message_reaction", "message_reaction_count", "chat_member"
    ])
    print("✅ bot9: allowed_updates patched!")
    return _original_infinity_polling(*args, **kwargs)

bot.infinity_polling = _patched_infinity_polling

_original_polling = bot.polling

def _patched_polling(*args, **kwargs):
    kwargs.setdefault("allowed_updates", [
        "message", "edited_message", "callback_query",
        "pre_checkout_query", "shipping_query",
        "message_reaction", "message_reaction_count", "chat_member"
    ])
    return _original_polling(*args, **kwargs)

bot.polling = _patched_polling


# =====================================================
# 📊 تهيئة إحصائيات النجوم
# =====================================================
def init_stars_config():
    defaults = {
        "stars_stats": {
            "total_received": 0,
            "total_sent": 0,
            "total_gifts": 0,
            "total_conversions": 0,
            "transactions": []
        },
        "stars_gifts_history": [],
        "stars_settings": {
            "conversion_rate": 2,
            "vip_price": 100,
            "min_gift": 1,
            "max_gift": 1000,
            "gift_enabled": True,
            "conversion_enabled": True
        }
    }
    changed = False
    for k, v in defaults.items():
        if k not in bot_config:
            bot_config[k] = v
            changed = True
    if changed:
        save_json(DB_CONFIG, bot_config)

init_stars_config()


# =====================================================
# 🔐 التحقق من الأدمن
# =====================================================
def is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except:
        pass
    u = get_user(str(uid)) or {}
    return u.get("is_admin", False)


# =====================================================
# 📝 تسجيل المعاملات
# =====================================================
def log_transaction(tx_type, uid, amount, details=""):
    tx = {
        "type": tx_type,
        "uid": str(uid),
        "amount": amount,
        "details": details,
        "time": datetime.now().isoformat()
    }
    if "stars_stats" not in bot_config:
        bot_config["stars_stats"] = {"transactions": []}
    if "transactions" not in bot_config["stars_stats"]:
        bot_config["stars_stats"]["transactions"] = []
    
    bot_config["stars_stats"]["transactions"].append(tx)
    # احتفظ بآخر 500 معاملة فقط
    bot_config["stars_stats"]["transactions"] = bot_config["stars_stats"]["transactions"][-500:]
    save_json(DB_CONFIG, bot_config)


# =====================================================
# ⭐ أمر /stars - لوحة تحكم النجوم
# =====================================================
@bot.message_handler(commands=['stars'])
def stars_admin_command(message):
    uid = str(message.from_user.id)
    
    if not is_admin(uid):
        bot.reply_to(message, "❌ هذا الأمر للأدمن فقط!")
        return
    
    show_stars_admin_panel(message.chat.id)


def show_stars_admin_panel(chat_id, msg_id=None):
    stats = bot_config.get("stars_stats", {})
    settings = bot_config.get("stars_settings", {})
    
    total_received = stats.get("total_received", 0)
    total_sent = stats.get("total_sent", 0)
    total_gifts = stats.get("total_gifts", 0)
    total_conversions = stats.get("total_conversions", 0)
    
    rate = settings.get("conversion_rate", 2)
    vip_price = settings.get("vip_price", 100)
    
    # آخر 5 معاملات
    transactions = stats.get("transactions", [])[-5:]
    tx_text = ""
    if transactions:
        for tx in reversed(transactions):
            tx_type = tx.get("type", "?")
            amount = tx.get("amount", 0)
            tx_time = tx.get("time", "")[:16]
            if tx_type == "vip":
                tx_text += f"👑 VIP: {amount}⭐ @ {tx_time}\n"
            elif tx_type == "convert":
                tx_text += f"🔄 تحويل: {amount}⭐ @ {tx_time}\n"
            elif tx_type == "gift":
                tx_text += f"🎁 هدية: {amount}⭐ @ {tx_time}\n"
    else:
        tx_text = "📭 لا توجد معاملات بعد"
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ ⭐ لوحة تحكم النجوم ⭐ ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"📊 الإحصائيات الكلية:\n"
        f"├── ⭐ المستلمة: {total_received}\n"
        f"├── 📤 المرسلة: {total_sent}\n"
        f"├── 🎁 الهدايا: {total_gifts}\n"
        f"└── 🔄 التحويلات: {total_conversions}\n\n"
        f"⚙️ الإعدادات:\n"
        f"├── 💱 سعر التحويل: 1⭐ = {rate}💎\n"
        f"└── 👑 سعر VIP: {vip_price}⭐\n\n"
        f"📜 آخر المعاملات:\n{tx_text}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎁 إرسال هدية نجوم", callback_data="stradm_gift"),
        types.InlineKeyboardButton("💎 منح نقاط", callback_data="stradm_give_points")
    )
    m.add(
        types.InlineKeyboardButton("👑 منح VIP مجاني", callback_data="stradm_free_vip"),
        types.InlineKeyboardButton("📢 إعلان للجميع", callback_data="stradm_broadcast")
    )
    m.add(
        types.InlineKeyboardButton("💱 تغيير سعر التحويل", callback_data="stradm_rate"),
        types.InlineKeyboardButton("👑 تغيير سعر VIP", callback_data="stradm_vip_price")
    )
    m.add(
        types.InlineKeyboardButton("📊 إحصائيات مفصلة", callback_data="stradm_detailed_stats"),
        types.InlineKeyboardButton("📜 كل المعاملات", callback_data="stradm_all_tx")
    )
    m.add(
        types.InlineKeyboardButton("🎰 إعدادات الألعاب", callback_data="stradm_games"),
        types.InlineKeyboardButton("⚡ عرض خاطف", callback_data="stradm_flash")
    )
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="stradm_refresh"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


# =====================================================
# 🎮 معالجات الكولباك
# =====================================================
temp_admin_action = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("stradm_"))
def handle_stars_admin_callbacks(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "❌ للأدمن فقط!", show_alert=True)
        return
    
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "stradm_refresh":
        show_stars_admin_panel(chat_id, msg_id)
        bot.answer_callback_query(call.id, "✅ تم التحديث")
        return
    
    if data == "stradm_gift":
        temp_admin_action[uid] = {"action": "gift", "step": "user"}
        msg = bot.send_message(chat_id, 
            "🎁 إرسال هدية نجوم\n\n"
            "📝 أرسل معرف المستخدم (ID أو @username):")
        bot.register_next_step_handler(msg, process_gift_user)
        return
    
    if data == "stradm_give_points":
        temp_admin_action[uid] = {"action": "points", "step": "user"}
        msg = bot.send_message(chat_id,
            "💎 منح نقاط\n\n"
            "📝 أرسل: ID المبلغ\n"
            "مثال: 123456789 500")
        bot.register_next_step_handler(msg, process_give_points)
        return
    
    if data == "stradm_free_vip":
        temp_admin_action[uid] = {"action": "vip", "step": "user"}
        msg = bot.send_message(chat_id,
            "👑 منح VIP مجاني\n\n"
            "📝 أرسل: ID الأيام\n"
            "مثال: 123456789 30")
        bot.register_next_step_handler(msg, process_free_vip)
        return
    
    if data == "stradm_rate":
        msg = bot.send_message(chat_id,
            f"💱 سعر التحويل الحالي: 1⭐ = {bot_config.get('stars_settings', {}).get('conversion_rate', 2)}💎\n\n"
            "📝 أرسل السعر الجديد:")
        bot.register_next_step_handler(msg, process_new_rate)
        return
    
    if data == "stradm_vip_price":
        msg = bot.send_message(chat_id,
            f"👑 سعر VIP الحالي: {bot_config.get('stars_settings', {}).get('vip_price', 100)}⭐\n\n"
            "📝 أرسل السعر الجديد:")
        bot.register_next_step_handler(msg, process_new_vip_price)
        return
    
    if data == "stradm_broadcast":
        msg = bot.send_message(chat_id,
            "📢 إذاعة للجميع\n\n"
            "📝 أرسل نص الرسالة:")
        bot.register_next_step_handler(msg, process_broadcast)
        return
    
    if data == "stradm_detailed_stats":
        show_detailed_stats(chat_id, msg_id)
        return
    
    if data == "stradm_all_tx":
        show_all_transactions(chat_id, msg_id)
        return
    
    if data == "stradm_games":
        show_games_settings(chat_id, msg_id)
        return
    
    if data == "stradm_flash":
        show_flash_sale_menu(chat_id, msg_id)
        return
    
    if data == "stradm_back":
        show_stars_admin_panel(chat_id, msg_id)
        return


# =====================================================
# 🎁 معالجة الهدايا
# =====================================================
def process_gift_user(message):
    uid = str(message.from_user.id)
    target = message.text.strip().replace("@", "")
    
    # البحث عن المستخدم
    from database import search_user
    u = None
    if target.isdigit():
        u = get_user(target)
    else:
        u = search_user(target)
    
    if not u:
        bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
        return
    
    temp_admin_action[uid] = {"action": "gift", "step": "amount", "target": str(u.get("uid"))}
    msg = bot.send_message(message.chat.id,
        f"✅ تم العثور على: @{u.get('username', 'N/A')}\n"
        f"🆔 ID: {u.get('uid')}\n\n"
        f"💎 أرسل عدد النقاط للهدية:")
    bot.register_next_step_handler(msg, process_gift_amount)


def process_gift_amount(message):
    uid = str(message.from_user.id)
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
        
        target = temp_admin_action[uid]["target"]
        
        # إضافة النقاط
        update_user_data(target, points=amount, accumulated_points=amount)
        update_user_rank_and_quests(target)
        
        # تسجيل المعاملة
        log_transaction("gift", target, amount, f"من الأدمن {uid}")
        bot_config["stars_stats"]["total_gifts"] = bot_config["stars_stats"].get("total_gifts", 0) + 1
        save_json(DB_CONFIG, bot_config)
        
        u = get_user(target) or {}
        
        # إشعار المستخدم
        try:
            bot.send_message(int(target),
                f"╔═══════════════════════╗\n"
                f"║ 🎁 هدية من الإدارة! 🎁 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"🎊 مبروك!\n\n"
                f"💎 حصلت على: +{amount} نقطة\n"
                f"💰 رصيدك الجديد: {u.get('points', 0)}\n\n"
                f"✨ استمتع!", parse_mode="HTML")
        except:
            pass
        
        bot.send_message(message.chat.id,
            f"✅ تم إرسال الهدية!\n\n"
            f"👤 المستلم: @{u.get('username', 'N/A')}\n"
            f"💎 المبلغ: {amount} نقطة")
        
        del temp_admin_action[uid]
        
    except:
        bot.send_message(message.chat.id, "❌ أرسل رقماً صحيحاً!")


def process_give_points(message):
    try:
        parts = message.text.strip().split()
        target = parts[0]
        amount = int(parts[1])
        
        if amount <= 0:
            raise ValueError
        
        u = get_user(target)
        if not u:
            bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
            return
        
        update_user_data(target, points=amount, accumulated_points=amount)
        update_user_rank_and_quests(target)
        
        log_transaction("points", target, amount, "منح من الأدمن")
        
        u_new = get_user(target) or {}
        
        try:
            bot.send_message(int(target),
                f"🎁 حصلت على +{amount}💎 من الإدارة!\n"
                f"💰 رصيدك: {u_new.get('points', 0)}", parse_mode="HTML")
        except:
            pass
        
        bot.send_message(message.chat.id,
            f"✅ تم منح {amount}💎 لـ {target}")
        
    except:
        bot.send_message(message.chat.id, "❌ الصيغة: ID المبلغ")


def process_free_vip(message):
    try:
        parts = message.text.strip().split()
        target = parts[0]
        days = int(parts[1])
        
        if days <= 0:
            raise ValueError
        
        u = get_user(target)
        if not u:
            bot.send_message(message.chat.id, "❌ المستخدم غير موجود!")
            return
        
        # تفعيل VIP
        expires = datetime.now() + timedelta(days=days)
        if "vip_subscribers" not in bot_config:
            bot_config["vip_subscribers"] = {}
        bot_config["vip_subscribers"][target] = {
            "activated": datetime.now().isoformat(),
            "expires": expires.isoformat(),
            "days": days,
            "free": True
        }
        save_json(DB_CONFIG, bot_config)
        
        log_transaction("free_vip", target, days, "VIP مجاني")
        
        try:
            bot.send_message(int(target),
                f"╔═══════════════════════╗\n"
                f"║ 👑 VIP مجاني! 👑 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"🎊 مبروك!\n\n"
                f"⏰ المدة: {days} يوم\n"
                f"📅 حتى: {expires.strftime('%Y-%m-%d')}\n\n"
                f"✨ استمتع بالمزايا!", parse_mode="HTML")
        except:
            pass
        
        bot.send_message(message.chat.id,
            f"✅ تم منح VIP لـ {target} لمدة {days} يوم")
        
    except:
        bot.send_message(message.chat.id, "❌ الصيغة: ID الأيام")


def process_new_rate(message):
    try:
        rate = int(message.text.strip())
        if rate <= 0:
            raise ValueError
        
        if "stars_settings" not in bot_config:
            bot_config["stars_settings"] = {}
        bot_config["stars_settings"]["conversion_rate"] = rate
        bot_config["star_to_points_rate"] = rate  # للتوافق مع bot2
        save_json(DB_CONFIG, bot_config)
        
        bot.send_message(message.chat.id,
            f"✅ تم تحديث سعر التحويل!\n\n"
            f"💱 الجديد: 1⭐ = {rate}💎")
        
    except:
        bot.send_message(message.chat.id, "❌ أرسل رقماً صحيحاً!")


def process_new_vip_price(message):
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
        
        if "stars_settings" not in bot_config:
            bot_config["stars_settings"] = {}
        bot_config["stars_settings"]["vip_price"] = price
        bot_config["vip_price_stars"] = price  # للتوافق مع bot2
        save_json(DB_CONFIG, bot_config)
        
        bot.send_message(message.chat.id,
            f"✅ تم تحديث سعر VIP!\n\n"
            f"👑 الجديد: {price}⭐")
        
    except:
        bot.send_message(message.chat.id, "❌ أرسل رقماً صحيحاً!")


def process_broadcast(message):
    from database import engine, text
    
    txt = message.text
    sent = 0
    failed = 0
    
    bot.send_message(message.chat.id, "📤 جاري الإرسال...")
    
    try:
        with engine.connect() as conn:
            users = conn.execute(text("SELECT uid FROM users")).fetchall()
            
        for row in users:
            try:
                u_info = get_user(str(row[0])) or {}
                if u_info.get("notifications_on", True):
                    bot.send_message(int(row[0]), txt, parse_mode="HTML")
                    sent += 1
                    time.sleep(0.05)
            except:
                failed += 1
                
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {e}")
        return
    
    bot.send_message(message.chat.id,
        f"✅ تم الإرسال!\n\n"
        f"📤 نجح: {sent}\n"
        f"❌ فشل: {failed}")


# =====================================================
# 📊 الإحصائيات المفصلة
# =====================================================
def show_detailed_stats(chat_id, msg_id=None):
    stats = bot_config.get("stars_stats", {})
    settings = bot_config.get("stars_settings", {})
    
    # إحصائيات اليوم
    today = datetime.now().date().isoformat()
    transactions = stats.get("transactions", [])
    
    today_tx = [tx for tx in transactions if tx.get("time", "").startswith(today)]
    today_vip = sum(1 for tx in today_tx if tx.get("type") == "vip")
    today_convert = sum(1 for tx in today_tx if tx.get("type") == "convert")
    today_gift = sum(1 for tx in today_tx if tx.get("type") == "gift")
    today_stars = sum(tx.get("amount", 0) for tx in today_tx if tx.get("type") in ["vip", "convert"])
    
    # إحصائيات الأسبوع
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    week_tx = [tx for tx in transactions if tx.get("time", "") >= week_ago]
    week_stars = sum(tx.get("amount", 0) for tx in week_tx if tx.get("type") in ["vip", "convert"])
    
    # عدد VIP النشطين
    vip_users = bot_config.get("vip_subscribers", {})
    active_vip = sum(1 for v in vip_users.values() 
                     if datetime.now() < datetime.fromisoformat(v.get("expires", "2000-01-01")))
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ 📊 إحصائيات مفصلة 📊 ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"📅 إحصائيات اليوم:\n"
        f"├── ⭐ النجوم: {today_stars}\n"
        f"├── 👑 VIP: {today_vip}\n"
        f"├── 🔄 تحويلات: {today_convert}\n"
        f"└── 🎁 هدايا: {today_gift}\n\n"
        f"📆 إحصائيات الأسبوع:\n"
        f"├── ⭐ النجوم: {week_stars}\n"
        f"└── 📝 المعاملات: {len(week_tx)}\n\n"
        f"👑 VIP:\n"
        f"├── 🟢 نشط: {active_vip}\n"
        f"└── 📊 الكل: {len(vip_users)}\n\n"
        f"⚙️ الإعدادات:\n"
        f"├── 💱 التحويل: 1⭐ = {settings.get('conversion_rate', 2)}💎\n"
        f"├── 👑 VIP: {settings.get('vip_price', 100)}⭐\n"
        f"├── 🎁 الهدايا: {'✅' if settings.get('gift_enabled', True) else '❌'}\n"
        f"└── 🔄 التحويل: {'✅' if settings.get('conversion_enabled', True) else '❌'}"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


def show_all_transactions(chat_id, msg_id=None):
    stats = bot_config.get("stars_stats", {})
    transactions = stats.get("transactions", [])[-20:]  # آخر 20
    
    if not transactions:
        msg = "📭 لا توجد معاملات"
    else:
        msg = "╔═══════════════════════════╗\n"
        msg += "║ 📜 آخر المعاملات 📜 ║\n"
        msg += "╚═══════════════════════════╝\n\n"
        
        for tx in reversed(transactions):
            tx_type = tx.get("type", "?")
            amount = tx.get("amount", 0)
            uid = tx.get("uid", "?")
            tx_time = tx.get("time", "")[:16]
            
            if tx_type == "vip":
                msg += f"👑 VIP | {amount}⭐ | {uid[:8]}.. | {tx_time}\n"
            elif tx_type == "convert":
                msg += f"🔄 تحويل | {amount}⭐ | {uid[:8]}.. | {tx_time}\n"
            elif tx_type == "gift":
                msg += f"🎁 هدية | {amount}💎 | {uid[:8]}.. | {tx_time}\n"
            elif tx_type == "wheel":
                msg += f"🎡 عجلة | {amount}💎 | {uid[:8]}.. | {tx_time}\n"
            elif tx_type == "lootbox":
                msg += f"🎰 صندوق | {amount}💎 | {uid[:8]}.. | {tx_time}\n"
            else:
                msg += f"📝 {tx_type} | {amount} | {uid[:8]}.. | {tx_time}\n"
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


# =====================================================
# 🎰 إعدادات الألعاب
# =====================================================
def show_games_settings(chat_id, msg_id=None):
    wheel_price = bot_config.get("wheel_price", 40)
    wheel_chance = bot_config.get("wheel_chance", 5)
    lootbox_price = bot_config.get("lootbox_price", 50)
    lootbox_chance = bot_config.get("lootbox_chance", 25)
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ 🎰 إعدادات الألعاب 🎰 ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"🎡 عجلة الحظ:\n"
        f"├── 💰 السعر: {wheel_price}💎\n"
        f"└── 📊 نسبة الجائزة الكبرى: {wheel_chance}%\n\n"
        f"🎰 صندوق الحظ:\n"
        f"├── 💰 السعر: {lootbox_price}💎\n"
        f"└── 📊 نسبة الفوز: {lootbox_chance}%"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎡 سعر العجلة ➕", callback_data="strgame_wheel_price_up"),
        types.InlineKeyboardButton("🎡 سعر العجلة ➖", callback_data="strgame_wheel_price_down")
    )
    m.add(
        types.InlineKeyboardButton("📊 نسبة العجلة ➕", callback_data="strgame_wheel_chance_up"),
        types.InlineKeyboardButton("📊 نسبة العجلة ➖", callback_data="strgame_wheel_chance_down")
    )
    m.add(
        types.InlineKeyboardButton("🎰 سعر الصندوق ➕", callback_data="strgame_box_price_up"),
        types.InlineKeyboardButton("🎰 سعر الصندوق ➖", callback_data="strgame_box_price_down")
    )
    m.add(
        types.InlineKeyboardButton("📊 نسبة الصندوق ➕", callback_data="strgame_box_chance_up"),
        types.InlineKeyboardButton("📊 نسبة الصندوق ➖", callback_data="strgame_box_chance_down")
    )
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("strgame_"))
def handle_games_settings(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    data = call.data
    
    if "wheel_price_up" in data:
        bot_config["wheel_price"] = bot_config.get("wheel_price", 40) + 5
    elif "wheel_price_down" in data:
        bot_config["wheel_price"] = max(5, bot_config.get("wheel_price", 40) - 5)
    elif "wheel_chance_up" in data:
        bot_config["wheel_chance"] = min(50, bot_config.get("wheel_chance", 5) + 1)
    elif "wheel_chance_down" in data:
        bot_config["wheel_chance"] = max(1, bot_config.get("wheel_chance", 5) - 1)
    elif "box_price_up" in data:
        bot_config["lootbox_price"] = bot_config.get("lootbox_price", 50) + 5
    elif "box_price_down" in data:
        bot_config["lootbox_price"] = max(5, bot_config.get("lootbox_price", 50) - 5)
    elif "box_chance_up" in data:
        bot_config["lootbox_chance"] = min(100, bot_config.get("lootbox_chance", 25) + 5)
    elif "box_chance_down" in data:
        bot_config["lootbox_chance"] = max(1, bot_config.get("lootbox_chance", 25) - 5)
    
    save_json(DB_CONFIG, bot_config)
    bot.answer_callback_query(call.id, "✅")
    show_games_settings(call.message.chat.id, call.message.message_id)


# =====================================================
# ⚡ العروض الخاطفة
# =====================================================
def show_flash_sale_menu(chat_id, msg_id=None):
    from utils import get_active_flash_sale, format_time_remaining
    
    fs = get_active_flash_sale()
    
    if fs:
        remaining = format_time_remaining(fs["expires"])
        status = (
            f"⚡ عرض نشط!\n"
            f"├── 📦 المنتج: {fs['product']}\n"
            f"├── 🔥 الخصم: {fs['discount']}%\n"
            f"└── ⏰ ينتهي: {remaining}"
        )
    else:
        status = "😴 لا يوجد عرض نشط"
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ ⚡ العروض الخاطفة ⚡ ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"{status}"
    )
    
    m = types.InlineKeyboardMarkup()
    if not fs:
        m.add(types.InlineKeyboardButton("⚡ إنشاء عرض جديد", callback_data="strflash_create"))
    else:
        m.add(types.InlineKeyboardButton("❌ إلغاء العرض", callback_data="strflash_cancel"))
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("strflash_"))
def handle_flash_callbacks(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    data = call.data
    chat_id = call.message.chat.id
    
    if data == "strflash_create":
        from database import prices_config
        if not prices_config:
            bot.answer_callback_query(call.id, "❌ لا توجد منتجات!", show_alert=True)
            return
        
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"strflashp_{p}"))
        m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_flash"))
        
        bot.edit_message_text("📦 اختر المنتج:", chat_id, call.message.message_id, reply_markup=m)
        return
    
    if data == "strflash_cancel":
        if "flash_sales" in bot_config:
            bot_config["flash_sales"]["current"] = None
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ تم إلغاء العرض", show_alert=True)
        show_flash_sale_menu(chat_id, call.message.message_id)
        return


@bot.callback_query_handler(func=lambda call: call.data.startswith("strflashp_"))
def handle_flash_product(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    prod = call.data.split("_", 1)[1]
    
    m = types.InlineKeyboardMarkup(row_width=3)
    for disc in [20, 30, 40, 50, 60, 70]:
        m.add(types.InlineKeyboardButton(f"{disc}%", callback_data=f"strflashd_{prod}|{disc}"))
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="strflash_create"))
    
    bot.edit_message_text(f"📦 {prod}\n\n🔥 اختر نسبة الخصم:", 
                          call.message.chat.id, call.message.message_id, reply_markup=m)


@bot.callback_query_handler(func=lambda call: call.data.startswith("strflashd_"))
def handle_flash_discount(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    parts = call.data.split("_", 1)[1].split("|")
    prod = parts[0]
    discount = int(parts[1])
    
    m = types.InlineKeyboardMarkup(row_width=3)
    for hours in [1, 3, 6, 12, 24, 48]:
        m.add(types.InlineKeyboardButton(f"{hours}h", callback_data=f"strflashh_{prod}|{discount}|{hours}"))
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"strflashp_{prod}"))
    
    bot.edit_message_text(f"📦 {prod} | 🔥 {discount}%\n\n⏰ اختر المدة:", 
                          call.message.chat.id, call.message.message_id, reply_markup=m)


@bot.callback_query_handler(func=lambda call: call.data.startswith("strflashh_"))
def handle_flash_hours(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    parts = call.data.split("_", 1)[1].split("|")
    prod = parts[0]
    discount = int(parts[1])
    hours = int(parts[2])
    
    # إنشاء العرض
    from utils import create_flash_sale, publish_flash_sale_to_channel
    expires = create_flash_sale(prod, discount, hours)
    publish_flash_sale_to_channel(prod, discount, hours)
    
    bot.answer_callback_query(call.id, f"✅ تم إنشاء العرض!", show_alert=True)
    
    bot.edit_message_text(
        f"╔═══════════════════════════╗\n"
        f"║ ⚡ تم إنشاء العرض! ⚡ ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"📦 المنتج: {prod}\n"
        f"🔥 الخصم: {discount}%\n"
        f"⏰ المدة: {hours} ساعة\n"
        f"📅 ينتهي: {expires.strftime('%Y-%m-%d %H:%M')}",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")


# =====================================================
# 🎡 إصلاح عجلة الحظ
# =====================================================
WHEEL_PRIZES = [
    {"emoji": "💎", "name": "جائزة صغيرة", "min": 5, "max": 20, "chance": 35},
    {"emoji": "🎁", "name": "جائزة متوسطة", "min": 25, "max": 50, "chance": 25},
    {"emoji": "⭐", "name": "جائزة كبيرة", "min": 60, "max": 100, "chance": 15},
    {"emoji": "👑", "name": "جائزة ملكية", "min": 120, "max": 200, "chance": 10},
    {"emoji": "🏆", "name": "الجائزة الكبرى", "min": 300, "max": 500, "chance": 5},
    {"emoji": "💀", "name": "لا شيء", "min": 0, "max": 0, "chance": 10},
]

@bot.callback_query_handler(func=lambda call: call.data == "menu_wheel")
def handle_wheel_menu(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    wheel_price = bot_config.get("wheel_price", 40)
    user_points = u.get("points", 0)
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ 🎡 عجلة الحظ 🎡 ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"💰 رصيدك: {user_points}💎\n"
        f"🎫 سعر الدورة: {wheel_price}💎\n\n"
        f"🎁 الجوائز الممكنة:\n"
        f"├── 💎 5-20 نقطة (35%)\n"
        f"├── 🎁 25-50 نقطة (25%)\n"
        f"├── ⭐ 60-100 نقطة (15%)\n"
        f"├── 👑 120-200 نقطة (10%)\n"
        f"├── 🏆 300-500 نقطة (5%)\n"
        f"└── 💀 لا شيء (10%)\n\n"
        f"🍀 جرّب حظك!"
    )
    
    m = types.InlineKeyboardMarkup()
    if user_points >= wheel_price:
        m.add(types.InlineKeyboardButton(f"🎡 دوّر العجلة ({wheel_price}💎)", callback_data="wheel_spin"))
    else:
        m.add(types.InlineKeyboardButton("❌ رصيد غير كافٍ", callback_data="wheel_no_balance"))
    
    try:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, 
                              reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(call.message.chat.id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "wheel_spin")
def handle_wheel_spin(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    wheel_price = bot_config.get("wheel_price", 40)
    user_points = u.get("points", 0)
    
    if user_points < wheel_price:
        bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ!", show_alert=True)
        return
    
    # خصم السعر
    update_user_data(uid, points=-wheel_price)
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # أنيميشن الدوران
    spin_frames = ["🎡 ⬆️", "🎡 ↗️", "🎡 ➡️", "🎡 ↘️", "🎡 ⬇️", "🎡 ↙️", "🎡 ⬅️", "🎡 ↖️"]
    
    for i in range(12):
        try:
            bot.edit_message_text(
                f"╔═══════════════════════════╗\n"
                f"║ 🎡 العجلة تدور... 🎡 ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"{spin_frames[i % len(spin_frames)]} جاري الدوران...\n\n"
                f"{'🔵' * (i % 4)}{'⚪' * (4 - i % 4)}",
                chat_id, msg_id, parse_mode="HTML")
            time.sleep(0.25)
        except:
            pass
    
    # اختيار الجائزة
    roll = random.randint(1, 100)
    cumulative = 0
    prize = None
    
    for p in WHEEL_PRIZES:
        cumulative += p["chance"]
        if roll <= cumulative:
            prize = p
            break
    
    if not prize:
        prize = WHEEL_PRIZES[-1]
    
    # حساب المكسب
    if prize["max"] > 0:
        winnings = random.randint(prize["min"], prize["max"])
        update_user_data(uid, points=winnings, accumulated_points=winnings)
        update_user_rank_and_quests(uid)
        log_transaction("wheel", uid, winnings, prize["name"])
        
        result_msg = (
            f"╔═══════════════════════════╗\n"
            f"║ 🎊 مبروك! 🎊 ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"{prize['emoji']} {prize['name']}!\n\n"
            f"💎 ربحت: +{winnings} نقطة\n"
            f"💰 رصيدك الجديد: {u.get('points', 0) - wheel_price + winnings}"
        )
    else:
        result_msg = (
            f"╔═══════════════════════════╗\n"
            f"║ 😢 للأسف! 😢 ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"{prize['emoji']} {prize['name']}\n\n"
            f"💔 لم تربح هذه المرة\n"
            f"💰 رصيدك: {u.get('points', 0) - wheel_price}\n\n"
            f"🍀 حظاً أوفر المرة القادمة!"
        )
    
    m = types.InlineKeyboardMarkup()
    u_new = get_user(uid) or {}
    if u_new.get("points", 0) >= wheel_price:
        m.add(types.InlineKeyboardButton("🎡 دوّر مرة أخرى", callback_data="wheel_spin"))
    
    try:
        bot.edit_message_text(result_msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(chat_id, result_msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "wheel_no_balance")
def handle_wheel_no_balance(call):
    bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)


# =====================================================
# 🎰 إصلاح صندوق الحظ
# =====================================================
LOOTBOX_ITEMS = [
    {"emoji": "💎", "name": "ألماسات", "min": 10, "max": 30},
    {"emoji": "⭐", "name": "نجوم", "min": 20, "max": 50},
    {"emoji": "🎁", "name": "هدية", "min": 30, "max": 70},
    {"emoji": "👑", "name": "تاج", "min": 50, "max": 100},
    {"emoji": "🏆", "name": "كأس", "min": 80, "max": 150},
]

@bot.callback_query_handler(func=lambda call: call.data == "menu_lootbox")
def handle_lootbox_menu(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    lootbox_price = bot_config.get("lootbox_price", 50)
    lootbox_chance = bot_config.get("lootbox_chance", 25)
    user_points = u.get("points", 0)
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ 🎰 صندوق الحظ 🎰 ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"💰 رصيدك: {user_points}💎\n"
        f"🎫 سعر الصندوق: {lootbox_price}💎\n"
        f"📊 نسبة الفوز: {lootbox_chance}%\n\n"
        f"🎁 المحتويات الممكنة:\n"
        f"├── 💎 10-30 ألماسة\n"
        f"├── ⭐ 20-50 نجمة\n"
        f"├── 🎁 30-70 هدية\n"
        f"├── 👑 50-100 تاج\n"
        f"└── 🏆 80-150 كأس\n\n"
        f"🍀 افتح الصندوق!"
    )
    
    m = types.InlineKeyboardMarkup()
    if user_points >= lootbox_price:
        m.add(types.InlineKeyboardButton(f"🎰 افتح الصندوق ({lootbox_price}💎)", callback_data="lootbox_open"))
    else:
        m.add(types.InlineKeyboardButton("❌ رصيد غير كافٍ", callback_data="lootbox_no_balance"))
    
    try:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(call.message.chat.id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "lootbox_open")
def handle_lootbox_open(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    lootbox_price = bot_config.get("lootbox_price", 50)
    lootbox_chance = bot_config.get("lootbox_chance", 25)
    user_points = u.get("points", 0)
    
    if user_points < lootbox_price:
        bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ!", show_alert=True)
        return
    
    # خصم السعر
    update_user_data(uid, points=-lootbox_price)
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # أنيميشن الفتح
    open_frames = ["🎰 📦", "🎰 📦✨", "🎰 📦💫", "🎰 🎁"]
    
    for frame in open_frames:
        try:
            bot.edit_message_text(
                f"╔═══════════════════════════╗\n"
                f"║ 🎰 جاري الفتح... 🎰 ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"{frame}",
                chat_id, msg_id, parse_mode="HTML")
            time.sleep(0.4)
        except:
            pass
    
    # تحديد الفوز
    won = random.randint(1, 100) <= lootbox_chance
    
    if won:
        item = random.choice(LOOTBOX_ITEMS)
        winnings = random.randint(item["min"], item["max"])
        update_user_data(uid, points=winnings, accumulated_points=winnings)
        update_user_rank_and_quests(uid)
        log_transaction("lootbox", uid, winnings, item["name"])
        
        result_msg = (
            f"╔═══════════════════════════╗\n"
            f"║ 🎊 فزت! 🎊 ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"🎁 فتحت الصندوق ووجدت:\n\n"
            f"{item['emoji']} {item['name']}\n"
            f"💎 +{winnings} نقطة!\n\n"
            f"💰 رصيدك الجديد: {u.get('points', 0) - lootbox_price + winnings}"
        )
    else:
        result_msg = (
            f"╔═══════════════════════════╗\n"
            f"║ 📦 الصندوق فارغ! 📦 ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"😢 للأسف الصندوق كان فارغاً!\n\n"
            f"💰 رصيدك: {u.get('points', 0) - lootbox_price}\n\n"
            f"🍀 حظاً أوفر المرة القادمة!"
        )
    
    m = types.InlineKeyboardMarkup()
    u_new = get_user(uid) or {}
    if u_new.get("points", 0) >= lootbox_price:
        m.add(types.InlineKeyboardButton("🎰 افتح صندوق آخر", callback_data="lootbox_open"))
    
    try:
        bot.edit_message_text(result_msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(chat_id, result_msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "lootbox_no_balance")
def handle_lootbox_no_balance(call):
    bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)


# =====================================================
# ✅ PRE-CHECKOUT HANDLER
# =====================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def bot9_handle_pre_checkout(pre_checkout_query):
    try:
        uid = str(pre_checkout_query.from_user.id)
        payload = pre_checkout_query.invoice_payload
        
        print(f"🔔 bot9: Pre-checkout from {uid}, payload={payload}")
        
        valid_prefixes = ["vip_purchase_", "stars_convert_"]
        is_valid = any(payload.startswith(prefix) for prefix in valid_prefixes)
        
        if is_valid:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            print(f"✅ bot9: Pre-checkout APPROVED")
        else:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, 
                                          error_message="❌ طلب غير صالح")
            print(f"❌ bot9: Pre-checkout REJECTED")
            
    except Exception as e:
        print(f"⚠️ bot9: Pre-checkout error: {e}")
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except:
            pass


# =====================================================
# ✅ SUCCESSFUL PAYMENT HANDLER
# =====================================================
@bot.message_handler(content_types=['successful_payment'])
def bot9_handle_successful_payment(message):
    try:
        uid = str(message.from_user.id)
        payment = message.successful_payment
        payload = payment.invoice_payload
        total_amount = payment.total_amount
        
        print(f"💰 bot9: Payment from {uid}, amount={total_amount}")
        
        # تحديث الإحصائيات
        if "stars_stats" not in bot_config:
            bot_config["stars_stats"] = {}
        bot_config["stars_stats"]["total_received"] = bot_config["stars_stats"].get("total_received", 0) + total_amount
        
        if payload.startswith("vip_purchase_"):
            # تفعيل VIP
            expires = datetime.now() + timedelta(days=30)
            if "vip_subscribers" not in bot_config:
                bot_config["vip_subscribers"] = {}
            bot_config["vip_subscribers"][uid] = {
                "activated": datetime.now().isoformat(),
                "expires": expires.isoformat(),
                "days": 30
            }
            save_json(DB_CONFIG, bot_config)
            
            log_transaction("vip", uid, total_amount, "VIP 30 days")
            
            bot.send_message(message.chat.id,
                f"╔═══════════════════════════╗\n"
                f"║ 🎊 VIP مفعّل! 🎊 ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"👑 أهلاً بك في نادي VIP!\n\n"
                f"⏰ صالح حتى: {expires.strftime('%Y-%m-%d')}\n"
                f"💎 كل المزايا مفعّلة\n\n"
                f"✨ استمتع!", parse_mode="HTML")
            
            # إشعار الأدمن
            try:
                u = get_user(uid) or {}
                bot.send_message(ADMIN_PRIMARY,
                    f"💰 VIP جديد!\n\n"
                    f"👤 @{u.get('username', 'N/A')}\n"
                    f"🆔 {uid}\n"
                    f"⭐ دفع: {total_amount}", parse_mode="HTML")
            except:
                pass
                
        elif payload.startswith("stars_convert_"):
            parts = payload.split("_")
            stars = int(parts[2])
            points = int(parts[3])
            
            update_user_data(uid, points=points, accumulated_points=points)
            update_user_rank_and_quests(uid)
            
            log_transaction("convert", uid, stars, f"{stars}⭐ → {points}💎")
            bot_config["stars_stats"]["total_conversions"] = bot_config["stars_stats"].get("total_conversions", 0) + 1
            save_json(DB_CONFIG, bot_config)
            
            u_new = get_user(uid) or {}
            bot.send_message(message.chat.id,
                f"╔═══════════════════════════╗\n"
                f"║ 🎉 تم التحويل! 🎉 ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"⭐ النجوم: {stars}\n"
                f"💎 النقاط: +{points}\n"
                f"💰 الرصيد: {u_new.get('points', 0)}", parse_mode="HTML")
            
            # إشعار الأدمن
            try:
                u = get_user(uid) or {}
                bot.send_message(ADMIN_PRIMARY,
                    f"⭐ تحويل!\n"
                    f"@{u.get('username', 'N/A')}\n"
                    f"⭐{stars} → 💎{points}", parse_mode="HTML")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ bot9: Payment error: {e}")


# =====================================================
# 🚀 تأكيد التحميل
# =====================================================
print("=" * 55)
print("✅ bot9.py v2.0 — نظام النجوم المتكامل")
print("⭐ لوحة تحكم النجوم: /stars")
print("💳 نظام الدفع: Active")
print("🎡 عجلة الحظ: Fixed")
print("🎰 صندوق الحظ: Fixed")
print("📊 الإحصائيات: Active")
print("=" * 55)
