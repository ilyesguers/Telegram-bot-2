"""
==============================================
🎁 bot2.py - نظام الميزات المتقدمة
==============================================
- نظام Giveaway الكامل
- إرسال/حذف رسائل القناة
- إشعارات ذكية
==============================================
"""

import random
import time
from datetime import datetime, timedelta
from telebot import types
from config import bot, ADMIN_PRIMARY, CHANNEL_ID, CHANNEL_LINK, t
from database import (bot_config, save_json, DB_CONFIG, get_user, 
                      update_user_data, update_user_rank_and_quests)
from utils import generate_captcha

# =====================================================
# 🎁 نظام الـ GIVEAWAY الكامل
# =====================================================

def init_giveaway_config():
    """تهيئة إعدادات الـ Giveaway"""
    if "giveaways" not in bot_config:
        bot_config["giveaways"] = {}
    if "giveaway_captchas" not in bot_config:
        bot_config["giveaway_captchas"] = {}
    save_json(DB_CONFIG, bot_config)

def generate_giveaway_code():
    """توليد كود giveaway فريد"""
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

def create_giveaway(reward, max_users, hours):
    """
    إنشاء giveaway جديد
    reward: قيمة الجائزة بالنقاط
    max_users: عدد المستخدمين المسموح
    hours: مدة صلاحية الرابط
    """
    init_giveaway_config()
    
    code = generate_giveaway_code()
    expires = datetime.now() + timedelta(hours=hours)
    
    bot_config["giveaways"][code] = {
        "code": code,
        "reward": reward,
        "max_users": max_users,
        "hours": hours,
        "expires": expires.isoformat(),
        "created": datetime.now().isoformat(),
        "claimed_by": [],
        "status": "active"
    }
    save_json(DB_CONFIG, bot_config)
    return code

def get_giveaway(code):
    """جلب بيانات giveaway"""
    init_giveaway_config()
    return bot_config.get("giveaways", {}).get(code)

def is_giveaway_valid(code):
    """
    فحص صلاحية الـ giveaway
    يرجع: (bool, reason)
    """
    gw = get_giveaway(code)
    if not gw:
        return False, "not_found"
    if gw.get("status") != "active":
        return False, "inactive"
    
    # فحص الانتهاء
    try:
        if datetime.now() > datetime.fromisoformat(gw["expires"]):
            gw["status"] = "expired"
            save_json(DB_CONFIG, bot_config)
            return False, "expired"
    except:
        return False, "expired"
    
    # فحص العدد الأقصى
    if len(gw.get("claimed_by", [])) >= gw.get("max_users", 0):
        gw["status"] = "full"
        save_json(DB_CONFIG, bot_config)
        return False, "full"
    
    return True, "valid"

def has_user_claimed_giveaway(code, uid):
    """فحص إذا استلم المستخدم الجائزة من قبل"""
    gw = get_giveaway(code)
    if not gw:
        return False
    return str(uid) in gw.get("claimed_by", [])

def claim_giveaway(code, uid):
    """
    تسجيل استلام الجائزة
    """
    gw = get_giveaway(code)
    if not gw:
        return False
    
    if "claimed_by" not in gw:
        gw["claimed_by"] = []
    
    gw["claimed_by"].append(str(uid))
    
    # فحص إذا امتلأ
    if len(gw["claimed_by"]) >= gw["max_users"]:
        gw["status"] = "full"
    
    save_json(DB_CONFIG, bot_config)
    return True

def publish_giveaway_to_channel(code):
    """نشر إعلان الـ Giveaway في القناة (بالإنجليزية)"""
    gw = get_giveaway(code)
    if not gw:
        return None
    
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    giveaway_link = f"https://t.me/{bot_user}?start=gw_{code}"
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  🎁 <b>GIVEAWAY!</b> 🎁    ║\n"
        f"╚═══════════════════════╝\n\n"
        f"🎊 <b>FREE PRIZE FOR EVERYONE!</b> 🎊\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Prize:</b> {gw['reward']} points\n"
        f"👥 <b>Winners:</b> {gw['max_users']} lucky users\n"
        f"⏰ <b>Duration:</b> {gw['hours']} hours\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>How to claim:</b>\n"
        f"1️⃣ Click the button below\n"
        f"2️⃣ Complete the security check\n"
        f"3️⃣ Get your reward instantly! 🎉\n\n"
        f"⚡ <b>First come, first served!</b>\n"
        f"💨 <i>Hurry before it's gone!</i>"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🎁 CLAIM YOUR PRIZE NOW", url=giveaway_link))
    
    try:
        sent = bot.send_message(CHANNEL_ID, msg, reply_markup=m, parse_mode="HTML")
        # حفظ message_id للنشر
        gw["channel_msg_id"] = sent.message_id
        save_json(DB_CONFIG, bot_config)
        return sent.message_id
    except Exception as e:
        print(f"❌ Error publishing giveaway: {e}")
        return None

def start_giveaway_captcha(uid, code):
    """بدء كابتشا الـ giveaway للمستخدم"""
    init_giveaway_config()
    
    u = get_user(str(uid)) or {}
    lang = u.get("lang", "en")
    
    emoji, name, opts = generate_captcha(lang)
    
    bot_config["giveaway_captchas"][str(uid)] = {
        "code": code,
        "answer": emoji,
        "attempts": 0,
        "expires": (datetime.now() + timedelta(minutes=5)).isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    
    m = types.InlineKeyboardMarkup(row_width=2)
    random.shuffle(opts)
    m.add(*[types.InlineKeyboardButton(o, callback_data=f"gwcap_{o}") for o in opts])
    
    gw = get_giveaway(code)
    reward = gw["reward"] if gw else 0
    
    try:
        bot.send_message(int(uid),
            f"╔═══════════════════════╗\n"
            f"║  🎁 <b>GIVEAWAY CLAIM</b>  ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🎊 <b>You're one step away!</b>\n\n"
            f"💎 <b>Prize:</b> {reward} points\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ <b>Security Check</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ Press on: <b>{name}</b> {emoji}\n\n"
            f"💡 <i>Only real users can claim!</i>",
            reply_markup=m, parse_mode="HTML")
    except Exception as e:
        print(f"❌ Error sending giveaway captcha: {e}")

def verify_giveaway_captcha(uid, answer):
    """
    التحقق من كابتشا الـ giveaway
    يرجع: ('correct'|'wrong'|'expired'|'no_session', code_or_None)
    """
    init_giveaway_config()
    uid = str(uid)
    
    sessions = bot_config.get("giveaway_captchas", {})
    if uid not in sessions:
        return "no_session", None
    
    session = sessions[uid]
    
    # فحص الانتهاء
    try:
        if datetime.now() > datetime.fromisoformat(session["expires"]):
            del sessions[uid]
            save_json(DB_CONFIG, bot_config)
            return "expired", None
    except:
        pass
    
    # فحص الإجابة
    if str(answer) == session["answer"]:
        code = session["code"]
        del sessions[uid]
        save_json(DB_CONFIG, bot_config)
        return "correct", code
    
    # إجابة خاطئة
    session["attempts"] = session.get("attempts", 0) + 1
    if session["attempts"] >= 3:
        del sessions[uid]
        save_json(DB_CONFIG, bot_config)
        return "banned", None
    
    save_json(DB_CONFIG, bot_config)
    return "wrong", None

def process_giveaway_claim(uid, code):
    """
    معالجة استلام الجائزة النهائية
    """
    valid, reason = is_giveaway_valid(code)
    if not valid:
        return False, reason
    
    if has_user_claimed_giveaway(code, uid):
        return False, "already_claimed"
    
    gw = get_giveaway(code)
    reward = gw["reward"]
    
    # إضافة النقاط للمستخدم
    update_user_data(uid, points=reward, accumulated_points=reward)
    update_user_rank_and_quests(uid)
    
    # تسجيل الاستلام
    claim_giveaway(code, uid)
    
    return True, reward

def get_all_giveaways():
    """جلب كل الـ giveaways للأدمن"""
    init_giveaway_config()
    return bot_config.get("giveaways", {})

def cancel_giveaway(code):
    """إلغاء giveaway"""
    gw = get_giveaway(code)
    if not gw:
        return False
    
    gw["status"] = "cancelled"
    save_json(DB_CONFIG, bot_config)
    
    # حذف الرسالة من القناة
    msg_id = gw.get("channel_msg_id")
    if msg_id:
        try:
            bot.delete_message(CHANNEL_ID, msg_id)
        except: pass
    
    return True

# =====================================================
# 📨 إرسال/حذف رسائل القناة
# =====================================================

def send_custom_channel_message(text):
    """
    إرسال رسالة مخصصة للقناة (من الأدمن)
    """
    try:
        # زخرفة الرسالة بشكل جميل
        formatted = (
            f"╔═══════════════════════╗\n"
            f"║     📢 <b>NOTICE</b> 📢     ║\n"
            f"╚═══════════════════════╝\n\n"
            f"{text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <i>Official Announcement</i>"
        )
        sent = bot.send_message(CHANNEL_ID, formatted, parse_mode="HTML")
        return sent.message_id
    except Exception as e:
        print(f"❌ Error sending channel message: {e}")
        return None

def send_raw_channel_message(text):
    """
    إرسال رسالة خام للقناة (بدون زخرفة)
    """
    try:
        sent = bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
        return sent.message_id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def delete_channel_message(msg_id):
    """
    حذف رسالة من القناة بواسطة الـ ID
    """
    try:
        bot.delete_message(CHANNEL_ID, int(msg_id))
        return True
    except Exception as e:
        print(f"❌ Error deleting: {e}")
        return False

# =====================================================
# 🎉 رسائل الفوز الجميلة
# =====================================================

def format_giveaway_win_message(reward, lang="ar"):
    """رسالة فوز جميلة بالـ giveaway"""
    messages = {
        "ar": (
            f"╔═══════════════════════╗\n"
            f"║  🎊 <b>مبروك!</b> 🎊    ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🎉 <b>لقد حصلت على الجائزة!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <b>الجائزة:</b> +{reward} نقطة\n"
            f"✅ <b>تمت الإضافة لرصيدك!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎁 <i>استمتع بجائزتك!</i>\n"
            f"💫 <i>شارك البوت مع أصدقائك</i>"
        ),
        "en": (
            f"╔═══════════════════════╗\n"
            f"║  🎊 <b>CONGRATS!</b> 🎊  ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🎉 <b>You won the giveaway!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <b>Prize:</b> +{reward} points\n"
            f"✅ <b>Added to your balance!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎁 <i>Enjoy your reward!</i>\n"
            f"💫 <i>Share the bot with friends</i>"
        ),
        "fr": (
            f"🎊 <b>Félicitations!</b> 🎊\n\n"
            f"💎 +{reward} points ajoutés!"
        ),
        "es": (
            f"🎊 <b>¡Felicidades!</b> 🎊\n\n"
            f"💎 +{reward} puntos añadidos!"
        ),
        "vi": (
            f"🎊 <b>Chúc mừng!</b> 🎊\n\n"
            f"💎 +{reward} điểm đã thêm!"
        )
    }
    return messages.get(lang, messages["en"])

def format_giveaway_error(reason, lang="ar"):
    """رسائل أخطاء الـ giveaway"""
    errors = {
        "ar": {
            "not_found": "❌ <b>الرابط غير صحيح!</b>\n\n💡 <i>تأكد من الرابط</i>",
            "expired": "⏰ <b>انتهى وقت العرض!</b>\n\n💔 <i>لقد فاتك هذا العرض</i>",
            "full": "😢 <b>العرض ممتلئ!</b>\n\n💔 <i>وصل للحد الأقصى</i>",
            "already_claimed": "⚠️ <b>لقد استلمت الجائزة من قبل!</b>\n\n💡 <i>غير مسموح بأكثر من مرة</i>",
            "inactive": "❌ <b>هذا العرض غير نشط</b>",
            "cancelled": "❌ <b>تم إلغاء هذا العرض</b>"
        },
        "en": {
            "not_found": "❌ <b>Invalid link!</b>\n\n💡 <i>Check the link</i>",
            "expired": "⏰ <b>Time's up!</b>\n\n💔 <i>You missed this offer</i>",
            "full": "😢 <b>Giveaway is full!</b>\n\n💔 <i>Max users reached</i>",
            "already_claimed": "⚠️ <b>You already claimed!</b>\n\n💡 <i>Only once per user</i>",
            "inactive": "❌ <b>This giveaway is not active</b>",
            "cancelled": "❌ <b>This giveaway was cancelled</b>"
        }
    }
    lang_errors = errors.get(lang, errors["en"])
    return lang_errors.get(reason, "❌ Error")

# =====================================================
# 📊 إحصائيات Giveaway
# =====================================================

def get_giveaways_stats():
    """إحصائيات كل الـ giveaways"""
    gws = get_all_giveaways()
    active = sum(1 for g in gws.values() if g.get("status") == "active")
    expired = sum(1 for g in gws.values() if g.get("status") == "expired")
    full = sum(1 for g in gws.values() if g.get("status") == "full")
    cancelled = sum(1 for g in gws.values() if g.get("status") == "cancelled")
    total_claimed = sum(len(g.get("claimed_by", [])) for g in gws.values())
    total_points = sum(g.get("reward", 0) * len(g.get("claimed_by", [])) for g in gws.values())
    
    return {
        "total": len(gws),
        "active": active,
        "expired": expired,
        "full": full,
        "cancelled": cancelled,
        "total_claimed": total_claimed,
        "total_points_given": total_points
    }
