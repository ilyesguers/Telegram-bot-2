import time
import random
import string
from datetime import datetime, timedelta
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID

user_last_msg = {}
captcha_sessions = {}  # {uid: {"answer": "X", "attempts": 0, "expires": timestamp}}
spam_warnings = {}

# =====================================================
# 🛡️ مكافحة السبام
# =====================================================
def check_spam(uid):
    uid = str(uid)
    current_time = time.time()
    
    if uid in user_last_msg:
        diff = current_time - user_last_msg[uid]
        if diff < 0.5:
            spam_warnings[uid] = spam_warnings.get(uid, 0) + 1
            user_last_msg[uid] = current_time
            
            if spam_warnings[uid] >= 5:
                trigger_captcha(uid)
                spam_warnings[uid] = 0
            return True
    
    user_last_msg[uid] = current_time
    return False

# =====================================================
# ⛔ فحص الحظر
# =====================================================
def is_user_banned(uid):
    from database import get_user, update_user_data
    uid = str(uid)
    u = get_user(uid)
    if not u:
        return False
    if u.get("banned", False):
        return True
    temp_until = u.get("banned_until")
    if temp_until:
        try:
            if datetime.now() < datetime.fromisoformat(temp_until):
                return True
            else:
                update_user_data(uid, banned_until=None)
        except:
            pass
    return False

# =====================================================
# 📢 فحص الاشتراك بالقناة
# =====================================================
def check_channel_join(uid):
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, uid)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception as e:
        print(f"⚠️ فحص القناة {uid}: {e}")
    return False

# =====================================================
# 🔐 مفتاح وهمي للتسويق
# =====================================================
def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

# =====================================================
# 🎨 كابتشا سهلة (إيموجي بسيط)
# =====================================================
def generate_captcha():
    """كابتشا إيموجي بسيطة - اختر الإيموجي المطلوب"""
    emojis_pool = [
        ("🍎", "التفاحة"),
        ("🍌", "الموزة"),
        ("🍇", "العنب"),
        ("🍓", "الفراولة"),
        ("🚗", "السيارة"),
        ("⚽", "الكرة"),
        ("🐶", "الكلب"),
        ("🐱", "القط"),
        ("🌙", "القمر"),
        ("⭐", "النجمة"),
        ("❤️", "القلب"),
        ("🎈", "البالون")
    ]
    
    # اختر 4 إيموجي عشوائياً
    chosen = random.sample(emojis_pool, 4)
    correct = random.choice(chosen)
    
    return correct[0], correct[1], [item[0] for item in chosen]

def trigger_captcha(uid):
    """إرسال كابتشا سهلة للمستخدم"""
    from telebot import types
    uid = str(uid)
    
    emoji_correct, name_correct, options = generate_captcha()
    captcha_sessions[uid] = {
        "answer": emoji_correct,
        "attempts": 0,
        "expires": time.time() + 300  # 5 دقائق
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    random.shuffle(options)
    buttons = []
    for opt in options:
        buttons.append(types.InlineKeyboardButton(opt, callback_data=f"captcha_ans_{opt}"))
    markup.add(*buttons)
    
    try:
        bot.send_message(int(uid), 
            f"🛡️ <b>═══ تحقق أمني بسيط ═══</b>\n\n"
            f"⚠️ للاستمرار، اضغط على <b>{name_correct}</b> {emoji_correct}\n\n"
            f"⏰ لديك 5 دقائق | 3 محاولات",
            reply_markup=markup, parse_mode="HTML")
    except:
        pass

def is_captcha_pending(uid):
    uid = str(uid)
    if uid not in captcha_sessions:
        return False
    session = captcha_sessions[uid]
    if time.time() > session["expires"]:
        del captcha_sessions[uid]
        return False
    return True

def verify_captcha(uid, user_answer):
    uid = str(uid)
    if uid not in captcha_sessions:
        return "no_session"
    
    session = captcha_sessions[uid]
    
    if time.time() > session["expires"]:
        del captcha_sessions[uid]
        return "expired"
    
    if str(user_answer) == session["answer"]:
        del captcha_sessions[uid]
        return "correct"
    
    session["attempts"] += 1
    if session["attempts"] >= 3:
        del captcha_sessions[uid]
        from database import update_user_data
        until = (datetime.now() + timedelta(hours=1)).isoformat()
        update_user_data(uid, banned_until=until)
        return "banned"
    
    return "wrong"

def require_verification_on_start(uid):
    """كابتشا إجبارية للتحقق من كل مستخدم جديد"""
    from database import get_user
    u = get_user(uid)
    if u and not u.get("verified", False):
        trigger_captcha(uid)
        return True
    return False
