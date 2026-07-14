"""
=====================================================
 bot9.py — نظام النجوم المتكامل v3.0
=====================================================
⭐ تحكم كامل بالنجوم للأدمن
🎡 إصلاح عجلة الحظ
💳 نظام الدفع الكامل
💫 إدارة نجوم تيليجرام الحقيقية

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
            "total_refunded": 0,
            "transactions": [],
            "payments_log": []  # سجل الدفعات للـ refund
        },
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
    
    # تأكد من وجود payments_log
    if "payments_log" not in bot_config.get("stars_stats", {}):
        if "stars_stats" not in bot_config:
            bot_config["stars_stats"] = {}
        bot_config["stars_stats"]["payments_log"] = []
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
def log_transaction(tx_type, uid, amount, details="", charge_id=None):
    tx = {
        "type": tx_type,
        "uid": str(uid),
        "amount": amount,
        "details": details,
        "charge_id": charge_id,
        "time": datetime.now().isoformat(),
        "refunded": False
    }
    if "stars_stats" not in bot_config:
        bot_config["stars_stats"] = {"transactions": [], "payments_log": []}
    if "transactions" not in bot_config["stars_stats"]:
        bot_config["stars_stats"]["transactions"] = []
    
    bot_config["stars_stats"]["transactions"].append(tx)
    bot_config["stars_stats"]["transactions"] = bot_config["stars_stats"]["transactions"][-500:]
    
    # حفظ في سجل الدفعات للـ refund
    if charge_id and tx_type in ["vip", "convert"]:
        if "payments_log" not in bot_config["stars_stats"]:
            bot_config["stars_stats"]["payments_log"] = []
        bot_config["stars_stats"]["payments_log"].append({
            "uid": str(uid),
            "amount": amount,
            "charge_id": charge_id,
            "type": tx_type,
            "time": datetime.now().isoformat(),
            "refunded": False
        })
        bot_config["stars_stats"]["payments_log"] = bot_config["stars_stats"]["payments_log"][-200:]
    
    save_json(DB_CONFIG, bot_config)


# =====================================================
# 💫 دوال نجوم تيليجرام الحقيقية
# =====================================================
def get_telegram_star_transactions(limit=100):
    """جلب معاملات النجوم من تيليجرام"""
    try:
        result = bot.get_star_transactions(limit=limit)
        return result.transactions if result else []
    except Exception as e:
        print(f"⚠️ Error getting star transactions: {e}")
        return None


def get_telegram_star_balance():
    """حساب رصيد النجوم من المعاملات"""
    try:
        transactions = get_telegram_star_transactions(limit=200)
        if transactions is None:
            return None, None
        
        incoming = 0
        outgoing = 0
        
        for tx in transactions:
            amount = tx.amount
            if amount > 0:
                incoming += amount
            else:
                outgoing += abs(amount)
        
        balance = incoming - outgoing
        return balance, {"incoming": incoming, "outgoing": outgoing, "count": len(transactions)}
    except Exception as e:
        print(f"⚠️ Error calculating balance: {e}")
        return None, None


def refund_star_payment(user_id, charge_id):
    """إرجاع النجوم للمستخدم"""
    try:
        bot.refund_star_payment(user_id=int(user_id), telegram_payment_charge_id=charge_id)
        return True, "تم الإرجاع بنجاح"
    except Exception as e:
        error_msg = str(e)
        if "CHARGE_ALREADY_REFUNDED" in error_msg:
            return False, "تم إرجاع هذه الدفعة مسبقاً"
        elif "CHARGE_NOT_FOUND" in error_msg:
            return False, "الدفعة غير موجودة"
        else:
            return False, f"خطأ: {error_msg[:50]}"


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
    
    # إحصائيات محلية
    total_received = stats.get("total_received", 0)
    total_refunded = stats.get("total_refunded", 0)
    
    # محاولة جلب رصيد تيليجرام الحقيقي
    tg_balance, tg_stats = get_telegram_star_balance()
    
    if tg_balance is not None:
        balance_text = (
            f"💫 رصيد النجوم الحقيقي:\n"
            f"├── ⭐ الرصيد: {tg_balance}\n"
            f"├── 📥 المستلمة: {tg_stats['incoming']}\n"
            f"├── 📤 المرجعة: {tg_stats['outgoing']}\n"
            f"└── 📊 المعاملات: {tg_stats['count']}"
        )
    else:
        balance_text = (
            f"📊 الإحصائيات المحلية:\n"
            f"├── ⭐ المستلمة: {total_received}\n"
            f"└── 🔄 المرجعة: {total_refunded}"
        )
    
    rate = settings.get("conversion_rate", 2)
    vip_price = settings.get("vip_price", 100)
    
    # عدد الدفعات القابلة للإرجاع
    payments = stats.get("payments_log", [])
    refundable = sum(1 for p in payments if not p.get("refunded", False))
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ ⭐ لوحة تحكم النجوم ⭐ ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"{balance_text}\n\n"
        f"⚙️ الإعدادات:\n"
        f"├── 💱 سعر التحويل: 1⭐ = {rate}💎\n"
        f"└── 👑 سعر VIP: {vip_price}⭐\n\n"
        f"📋 دفعات قابلة للإرجاع: {refundable}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # صف 1: النجوم الحقيقية
    m.add(
        types.InlineKeyboardButton("💫 معاملات تيليجرام", callback_data="stradm_tg_transactions"),
        types.InlineKeyboardButton("🔄 إرجاع نجوم (Refund)", callback_data="stradm_refund")
    )
    
    # صف 2: الهدايا والنقاط
    m.add(
        types.InlineKeyboardButton("🎁 إرسال هدية نقاط", callback_data="stradm_gift"),
        types.InlineKeyboardButton("💎 منح نقاط", callback_data="stradm_give_points")
    )
    
    # صف 3: VIP
    m.add(
        types.InlineKeyboardButton("👑 منح VIP مجاني", callback_data="stradm_free_vip"),
        types.InlineKeyboardButton("📢 إذاعة للجميع", callback_data="stradm_broadcast")
    )
    
    # صف 4: الإعدادات
    m.add(
        types.InlineKeyboardButton("💱 سعر التحويل", callback_data="stradm_rate"),
        types.InlineKeyboardButton("👑 سعر VIP", callback_data="stradm_vip_price")
    )
    
    # صف 5: الإحصائيات
    m.add(
        types.InlineKeyboardButton("📊 إحصائيات مفصلة", callback_data="stradm_detailed_stats"),
        types.InlineKeyboardButton("📜 سجل المعاملات", callback_data="stradm_all_tx")
    )
    
    # صف 6: الألعاب والعروض
    m.add(
        types.InlineKeyboardButton("🎰 إعدادات الألعاب", callback_data="stradm_games"),
        types.InlineKeyboardButton("⚡ عرض خاطف", callback_data="stradm_flash")
    )
    
    # صف 7: تحديث
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="stradm_refresh"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


# =====================================================
# 💫 معاملات تيليجرام الحقيقية
# =====================================================
def show_telegram_transactions(chat_id, msg_id=None):
    """عرض معاملات النجوم من تيليجرام"""
    transactions = get_telegram_star_transactions(limit=20)
    
    if transactions is None:
        msg = (
            "❌ لم نتمكن من جلب المعاملات\n\n"
            "💡 تأكد أن البوت استلم نجوم من قبل"
        )
    elif len(transactions) == 0:
        msg = "📭 لا توجد معاملات نجوم بعد"
    else:
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ 💫 معاملات النجوم الحقيقية 💫 ║\n"
            "╚═══════════════════════════════╝\n\n"
        )
        
        for i, tx in enumerate(transactions[:15], 1):
            amount = tx.amount
            date = datetime.fromtimestamp(tx.date).strftime("%m/%d %H:%M")
            
            if amount > 0:
                # دفعة واردة
                source = tx.source
                if hasattr(source, 'user') and source.user:
                    user_info = f"@{source.user.username}" if source.user.username else f"ID:{source.user.id}"
                else:
                    user_info = "مستخدم"
                msg += f"📥 +{amount}⭐ من {user_info} | {date}\n"
            else:
                # إرجاع
                msg += f"📤 {amount}⭐ (إرجاع) | {date}\n"
        
        if len(transactions) > 15:
            msg += f"\n... و {len(transactions) - 15} معاملة أخرى"
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="stradm_tg_transactions"))
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


# =====================================================
# 🔄 نظام إرجاع النجوم (Refund)
# =====================================================
def show_refund_menu(chat_id, msg_id=None):
    """عرض قائمة الدفعات القابلة للإرجاع"""
    payments = bot_config.get("stars_stats", {}).get("payments_log", [])
    
    # فلترة الدفعات غير المرجعة
    refundable = [p for p in payments if not p.get("refunded", False)]
    
    if not refundable:
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ 🔄 إرجاع النجوم (Refund) 🔄 ║\n"
            "╚═══════════════════════════════╝\n\n"
            "📭 لا توجد دفعات قابلة للإرجاع\n\n"
            "💡 الدفعات تظهر هنا بعد أن يدفع\n"
            "   مستخدم عبر VIP أو تحويل النجوم"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    else:
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ 🔄 إرجاع النجوم (Refund) 🔄 ║\n"
            "╚═══════════════════════════════╝\n\n"
            f"📋 الدفعات القابلة للإرجاع: {len(refundable)}\n\n"
            "⚠️ عند الإرجاع:\n"
            "├── النجوم ترجع للمستخدم الأصلي\n"
            "├── لا يمكن التراجع عن الإرجاع\n"
            "└── يجب إزالة VIP/النقاط يدوياً\n\n"
            "👇 اختر الدفعة للإرجاع:"
        )
        
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(refundable[-10:]):  # آخر 10
            u = get_user(p["uid"]) or {}
            username = u.get("username", "N/A")[:10]
            amount = p.get("amount", 0)
            tx_type = "👑" if p.get("type") == "vip" else "🔄"
            date = p.get("time", "")[:10]
            
            btn_text = f"{tx_type} {amount}⭐ @{username} ({date})"
            m.add(types.InlineKeyboardButton(btn_text, callback_data=f"strrefund_{i}"))
        
        m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="stradm_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("strrefund_"))
def handle_refund_selection(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    try:
        idx = int(call.data.split("_")[1])
        payments = bot_config.get("stars_stats", {}).get("payments_log", [])
        refundable = [p for p in payments if not p.get("refunded", False)]
        
        if idx >= len(refundable):
            bot.answer_callback_query(call.id, "❌ الدفعة غير موجودة", show_alert=True)
            return
        
        payment = refundable[idx]
        
        # عرض تأكيد
        u = get_user(payment["uid"]) or {}
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ ⚠️ تأكيد الإرجاع ⚠️ ║\n"
            "╚═══════════════════════════════╝\n\n"
            f"👤 المستخدم: @{u.get('username', 'N/A')}\n"
            f"🆔 ID: {payment['uid']}\n"
            f"⭐ المبلغ: {payment['amount']} نجمة\n"
            f"📝 النوع: {'VIP' if payment.get('type') == 'vip' else 'تحويل'}\n"
            f"📅 التاريخ: {payment.get('time', '')[:16]}\n\n"
            "⚠️ هل أنت متأكد من الإرجاع؟\n"
            "النجوم سترجع للمستخدم فوراً!"
        )
        
        m = types.InlineKeyboardMarkup()
        m.add(
            types.InlineKeyboardButton("✅ نعم، أرجع", callback_data=f"strrefundconfirm_{idx}"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="stradm_refund")
        )
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, 
                              reply_markup=m, parse_mode="HTML")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)[:30]}", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("strrefundconfirm_"))
def handle_refund_confirm(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    try:
        idx = int(call.data.split("_")[1])
        payments = bot_config.get("stars_stats", {}).get("payments_log", [])
        refundable = [p for p in payments if not p.get("refunded", False)]
        
        if idx >= len(refundable):
            bot.answer_callback_query(call.id, "❌ الدفعة غير موجودة", show_alert=True)
            return
        
        payment = refundable[idx]
        charge_id = payment.get("charge_id")
        
        if not charge_id:
            bot.answer_callback_query(call.id, "❌ معرف الدفعة غير موجود", show_alert=True)
            return
        
        # تنفيذ الإرجاع
        success, message = refund_star_payment(payment["uid"], charge_id)
        
        if success:
            # تحديث السجل
            for p in payments:
                if p.get("charge_id") == charge_id:
                    p["refunded"] = True
                    p["refund_time"] = datetime.now().isoformat()
                    p["refund_by"] = uid
            
            bot_config["stars_stats"]["total_refunded"] = bot_config["stars_stats"].get("total_refunded", 0) + payment["amount"]
            save_json(DB_CONFIG, bot_config)
            
            # إشعار المستخدم
            try:
                bot.send_message(int(payment["uid"]),
                    f"╔═══════════════════════════╗\n"
                    f"║ 🔄 تم إرجاع النجوم! 🔄 ║\n"
                    f"╚═══════════════════════════╝\n\n"
                    f"⭐ المبلغ: {payment['amount']} نجمة\n"
                    f"💫 تم إرجاعها لحسابك\n\n"
                    f"✨ شكراً لتفهمك!", parse_mode="HTML")
            except:
                pass
            
            bot.answer_callback_query(call.id, "✅ تم الإرجاع بنجاح!", show_alert=True)
            
            # إشعار الأدمن
            u = get_user(payment["uid"]) or {}
            bot.edit_message_text(
                f"✅ تم إرجاع {payment['amount']}⭐ لـ @{u.get('username', 'N/A')}",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, f"❌ {message}", show_alert=True)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)[:30]}", show_alert=True)


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
    
    if data == "stradm_back":
        show_stars_admin_panel(chat_id, msg_id)
        return
    
    if data == "stradm_tg_transactions":
        bot.answer_callback_query(call.id, "⏳ جاري الجلب...")
        show_telegram_transactions(chat_id, msg_id)
        return
    
    if data == "stradm_refund":
        show_refund_menu(chat_id, msg_id)
        return
    
    if data == "stradm_gift":
        temp_admin_action[uid] = {"action": "gift", "step": "user"}
        msg = bot.send_message(chat_id, 
            "🎁 إرسال هدية نقاط\n\n"
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


# =====================================================
# 🎁 معالجة الهدايا والنقاط
# =====================================================
def process_gift_user(message):
    uid = str(message.from_user.id)
    target = message.text.strip().replace("@", "")
    
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
        
        update_user_data(target, points=amount, accumulated_points=amount)
        update_user_rank_and_quests(target)
        
        log_transaction("gift", target, amount, f"من الأدمن {uid}")
        
        u = get_user(target) or {}
        
        try:
            bot.send_message(int(target),
                f"╔═══════════════════════════╗\n"
                f"║ 🎁 هدية من الإدارة! 🎁 ║\n"
                f"╚═══════════════════════════╝\n\n"
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
                f"╔═══════════════════════════╗\n"
                f"║ 👑 VIP مجاني! 👑 ║\n"
                f"╚═══════════════════════════╝\n\n"
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
        bot_config["star_to_points_rate"] = rate
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
        bot_config["vip_price_stars"] = price
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
    
    today = datetime.now().date().isoformat()
    transactions = stats.get("transactions", [])
    
    today_tx = [tx for tx in transactions if tx.get("time", "").startswith(today)]
    today_vip = sum(1 for tx in today_tx if tx.get("type") == "vip")
    today_convert = sum(1 for tx in today_tx if tx.get("type") == "convert")
    today_gift = sum(1 for tx in today_tx if tx.get("type") == "gift")
    today_stars = sum(tx.get("amount", 0) for tx in today_tx if tx.get("type") in ["vip", "convert"])
    
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    week_tx = [tx for tx in transactions if tx.get("time", "") >= week_ago]
    week_stars = sum(tx.get("amount", 0) for tx in week_tx if tx.get("type") in ["vip", "convert"])
    
    vip_users = bot_config.get("vip_subscribers", {})
    active_vip = 0
    for v in vip_users.values():
        try:
            if datetime.now() < datetime.fromisoformat(v.get("expires", "2000-01-01")):
                active_vip += 1
        except:
            pass
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ 📊 إحصائيات مفصلة 📊 ║\n"
        f"╚═══════════════════════════════╝\n\n"
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
        f"└── 👑 VIP: {settings.get('vip_price', 100)}⭐"
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
    transactions = stats.get("transactions", [])[-20:]
    
    if not transactions:
        msg = "📭 لا توجد معاملات"
    else:
        msg = "╔═══════════════════════════════╗\n"
        msg += "║ 📜 آخر المعاملات 📜 ║\n"
        msg += "╚═══════════════════════════════╝\n\n"
        
        for tx in reversed(transactions):
            tx_type = tx.get("type", "?")
            amount = tx.get("amount", 0)
            tx_time = tx.get("time", "")[:10]
            refunded = "🔄" if tx.get("refunded") else ""
            
            icons = {"vip": "👑", "convert": "🔄", "gift": "🎁", "wheel": "🎡", "lootbox": "🎰"}
            icon = icons.get(tx_type, "📝")
            
            msg += f"{icon} {amount} | {tx_time} {refunded}\n"
    
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
        f"╔═══════════════════════════════╗\n"
        f"║ 🎰 إعدادات الألعاب 🎰 ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"🎡 عجلة الحظ:\n"
        f"├── 💰 السعر: {wheel_price}💎\n"
        f"└── 📊 نسبة الكبرى: {wheel_chance}%\n\n"
        f"🎰 صندوق الحظ:\n"
        f"├── 💰 السعر: {lootbox_price}💎\n"
        f"└── 📊 نسبة الفوز: {lootbox_chance}%"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎡 سعر ➕", callback_data="strgame_wheel_price_up"),
        types.InlineKeyboardButton("🎡 سعر ➖", callback_data="strgame_wheel_price_down")
    )
    m.add(
        types.InlineKeyboardButton("📊 نسبة ➕", callback_data="strgame_wheel_chance_up"),
        types.InlineKeyboardButton("📊 نسبة ➖", callback_data="strgame_wheel_chance_down")
    )
    m.add(
        types.InlineKeyboardButton("🎰 سعر ➕", callback_data="strgame_box_price_up"),
        types.InlineKeyboardButton("🎰 سعر ➖", callback_data="strgame_box_price_down")
    )
    m.add(
        types.InlineKeyboardButton("📊 نسبة ➕", callback_data="strgame_box_chance_up"),
        types.InlineKeyboardButton("📊 نسبة ➖", callback_data="strgame_box_chance_down")
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
        f"╔═══════════════════════════════╗\n"
        f"║ ⚡ العروض الخاطفة ⚡ ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"{status}"
    )
    
    m = types.InlineKeyboardMarkup()
    if not fs:
        m.add(types.InlineKeyboardButton("⚡ إنشاء عرض", callback_data="strflash_create"))
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
    
    from utils import create_flash_sale, publish_flash_sale_to_channel
    expires = create_flash_sale(prod, discount, hours)
    publish_flash_sale_to_channel(prod, discount, hours)
    
    bot.answer_callback_query(call.id, f"✅ تم إنشاء العرض!", show_alert=True)
    
    bot.edit_message_text(
        f"╔═══════════════════════════════╗\n"
        f"║ ⚡ تم إنشاء العرض! ⚡ ║\n"
        f"╚═══════════════════════════════╝\n\n"
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
    
    wheel_price = bot_config.get("wheel_price", 40)
    user_points = u.get("points", 0)
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ 🎡 عجلة الحظ 🎡 ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"💰 رصيدك: {user_points}💎\n"
        f"🎫 سعر الدورة: {wheel_price}💎\n\n"
        f"🎁 الجوائز:\n"
        f"├── 💎 5-20 (35%)\n"
        f"├── 🎁 25-50 (25%)\n"
        f"├── ⭐ 60-100 (15%)\n"
        f"├── 👑 120-200 (10%)\n"
        f"├── 🏆 300-500 (5%)\n"
        f"└── 💀 لا شيء (10%)"
    )
    
    m = types.InlineKeyboardMarkup()
    if user_points >= wheel_price:
        m.add(types.InlineKeyboardButton(f"🎡 دوّر ({wheel_price}💎)", callback_data="wheel_spin"))
    else:
        m.add(types.InlineKeyboardButton("❌ رصيد غير كافٍ", callback_data="wheel_no"))
    
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
    
    update_user_data(uid, points=-wheel_price)
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    frames = ["🎡 ⬆️", "🎡 ➡️", "🎡 ⬇️", "🎡 ⬅️"]
    
    for i in range(8):
        try:
            bot.edit_message_text(f"🎡 جاري الدوران...\n\n{frames[i % 4]}",
                                  chat_id, msg_id, parse_mode="HTML")
            time.sleep(0.3)
        except:
            pass
    
    roll = random.randint(1, 100)
    cumulative = 0
    prize = WHEEL_PRIZES[-1]
    
    for p in WHEEL_PRIZES:
        cumulative += p["chance"]
        if roll <= cumulative:
            prize = p
            break
    
    if prize["max"] > 0:
        winnings = random.randint(prize["min"], prize["max"])
        update_user_data(uid, points=winnings, accumulated_points=winnings)
        update_user_rank_and_quests(uid)
        log_transaction("wheel", uid, winnings, prize["name"])
        
        u_new = get_user(uid) or {}
        result = (
            f"🎊 مبروك!\n\n"
            f"{prize['emoji']} {prize['name']}\n"
            f"💎 +{winnings}\n"
            f"💰 رصيدك: {u_new.get('points', 0)}"
        )
    else:
        u_new = get_user(uid) or {}
        result = (
            f"😢 للأسف!\n\n"
            f"{prize['emoji']} {prize['name']}\n"
            f"💰 رصيدك: {u_new.get('points', 0)}"
        )
    
    m = types.InlineKeyboardMarkup()
    if u_new.get("points", 0) >= wheel_price:
        m.add(types.InlineKeyboardButton("🎡 مرة أخرى", callback_data="wheel_spin"))
    
    try:
        bot.edit_message_text(result, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(chat_id, result, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "wheel_no")
def handle_wheel_no(call):
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
    
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    points = u.get("points", 0)
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ 🎰 صندوق الحظ 🎰 ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"💰 رصيدك: {points}💎\n"
        f"🎫 السعر: {price}💎\n"
        f"📊 نسبة الفوز: {chance}%"
    )
    
    m = types.InlineKeyboardMarkup()
    if points >= price:
        m.add(types.InlineKeyboardButton(f"🎰 افتح ({price}💎)", callback_data="lootbox_open"))
    else:
        m.add(types.InlineKeyboardButton("❌ رصيد غير كافٍ", callback_data="lootbox_no"))
    
    try:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(call.message.chat.id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "lootbox_open")
def handle_lootbox_open(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    points = u.get("points", 0)
    
    if points < price:
        bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ!", show_alert=True)
        return
    
    update_user_data(uid, points=-price)
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    for frame in ["📦", "📦✨", "📦💫", "🎁"]:
        try:
            bot.edit_message_text(f"🎰 جاري الفتح...\n\n{frame}", chat_id, msg_id)
            time.sleep(0.4)
        except:
            pass
    
    won = random.randint(1, 100) <= chance
    
    if won:
        item = random.choice(LOOTBOX_ITEMS)
        winnings = random.randint(item["min"], item["max"])
        update_user_data(uid, points=winnings, accumulated_points=winnings)
        update_user_rank_and_quests(uid)
        log_transaction("lootbox", uid, winnings, item["name"])
        
        u_new = get_user(uid) or {}
        result = (
            f"🎊 فزت!\n\n"
            f"{item['emoji']} {item['name']}\n"
            f"💎 +{winnings}\n"
            f"💰 رصيدك: {u_new.get('points', 0)}"
        )
    else:
        u_new = get_user(uid) or {}
        result = (
            f"📦 فارغ!\n\n"
            f"😢 للأسف\n"
            f"💰 رصيدك: {u_new.get('points', 0)}"
        )
    
    m = types.InlineKeyboardMarkup()
    if u_new.get("points", 0) >= price:
        m.add(types.InlineKeyboardButton("🎰 مرة أخرى", callback_data="lootbox_open"))
    
    try:
        bot.edit_message_text(result, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(chat_id, result, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "lootbox_no")
def handle_lootbox_no(call):
    bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)


# =====================================================
# ✅ PRE-CHECKOUT HANDLER
# =====================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def bot9_handle_pre_checkout(pre_checkout_query):
    try:
        uid = str(pre_checkout_query.from_user.id)
        payload = pre_checkout_query.invoice_payload
        
        print(f"🔔 bot9: Pre-checkout from {uid}")
        
        valid = payload.startswith("vip_purchase_") or payload.startswith("stars_convert_")
        
        if valid:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            print(f"✅ bot9: Approved")
        else:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, 
                                          error_message="❌ طلب غير صالح")
    except Exception as e:
        print(f"⚠️ bot9: Error: {e}")
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
        charge_id = payment.telegram_payment_charge_id
        
        print(f"💰 bot9: Payment from {uid}, amount={total_amount}, charge={charge_id}")
        
        if "stars_stats" not in bot_config:
            bot_config["stars_stats"] = {}
        bot_config["stars_stats"]["total_received"] = bot_config["stars_stats"].get("total_received", 0) + total_amount
        
        if payload.startswith("vip_purchase_"):
            expires = datetime.now() + timedelta(days=30)
            if "vip_subscribers" not in bot_config:
                bot_config["vip_subscribers"] = {}
            bot_config["vip_subscribers"][uid] = {
                "activated": datetime.now().isoformat(),
                "expires": expires.isoformat(),
                "days": 30
            }
            save_json(DB_CONFIG, bot_config)
            
            log_transaction("vip", uid, total_amount, "VIP 30 days", charge_id)
            
            bot.send_message(message.chat.id,
                f"╔═══════════════════════════╗\n"
                f"║ 🎊 VIP مفعّل! 🎊 ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"👑 أهلاً بك!\n"
                f"⏰ حتى: {expires.strftime('%Y-%m-%d')}", parse_mode="HTML")
            
            try:
                u = get_user(uid) or {}
                bot.send_message(ADMIN_PRIMARY,
                    f"💰 VIP جديد!\n@{u.get('username', 'N/A')}\n{total_amount}⭐", parse_mode="HTML")
            except:
                pass
                
        elif payload.startswith("stars_convert_"):
            parts = payload.split("_")
            stars = int(parts[2])
            points = int(parts[3])
            
            update_user_data(uid, points=points, accumulated_points=points)
            update_user_rank_and_quests(uid)
            
            log_transaction("convert", uid, stars, f"{stars}⭐→{points}💎", charge_id)
            
            u_new = get_user(uid) or {}
            bot.send_message(message.chat.id,
                f"✅ تم!\n⭐ {stars} → 💎 {points}\n💰 رصيدك: {u_new.get('points', 0)}", parse_mode="HTML")
            
            try:
                bot.send_message(ADMIN_PRIMARY, f"⭐ تحويل: {stars}→{points}💎", parse_mode="HTML")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ bot9: Payment error: {e}")


# =====================================================
# 🚀 تأكيد التحميل
# =====================================================
print("=" * 55)
print("✅ bot9.py v3.0 — نظام النجوم المتكامل")
print("⭐ لوحة التحكم: /stars")
print("💫 معاملات تيليجرام: Active")
print("🔄 نظام Refund: Active")
print("🎡 عجلة الحظ: Fixed")
print("🎰 صندوق الحظ: Fixed")
print("=" * 55)
