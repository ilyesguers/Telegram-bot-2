import time
import random
import string
from datetime import datetime
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID

user_last_msg = {}
captcha_sessions = {}  # {uid: {"answer": "X", "attempts": 0, "expires": timestamp}}
spam_warnings = {}  # {uid: count}

def check_spam(uid):
    """نظام مكافحة السبام المحسّن"""
    uid = str(uid)
    current_time = time.time()
    
    if uid in user_last_msg:
        diff = current_time - user_last_msg[uid]
        if diff < 0.5:  # أقل من نصف ثانية = سبام
            spam_warnings[uid] = spam_warnings.get(uid, 0) + 1
            user_last_msg[uid] = current_time
            
            # 5 تحذيرات = يحتاج كابتشا
            if spam_warnings[uid] >= 5:
                trigger_captcha(uid)
                spam_warnings[uid] = 0
            return True
    
    user_last_msg[uid] = current_time
    return False

def is_user_banned(uid):
    """فحص حظر المستخدم من قاعدة البيانات"""
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

def check_channel_join(uid):
    """فحص الاشتراك في القناة الإجباري"""
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, uid)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception as e:
        print(f"خطأ فحص القناة للمستخدم {uid}: {e}")
    return False

def generate_fake_key():
    """توليد مفتاح وهمي للتسويق"""
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

# ==========================================================
# 🛡️ نظام الكابتشا الذكي (مضاد للرشق والبوتات)
# ==========================================================
def generate_captcha():
    """
    توليد كابتشا رياضي ذكي
    3 مستويات صعوبة تدور عشوائياً
    """
    difficulty = random.choice([1, 2, 3])
    
    if difficulty == 1:
        # جمع بسيط
        a = random.randint(10, 50)
        b = random.randint(10, 50)
        question = f"{a} ➕ {b}"
        answer = str(a + b)
    elif difficulty == 2:
        # طرح
        a = random.randint(50, 100)
        b = random.randint(10, 49)
        question = f"{a} ➖ {b}"
        answer = str(a - b)
    else:
        # ضرب
        a = random.randint(3, 12)
        b = random.randint(3, 12)
        question = f"{a} ✖️ {b}"
        answer = str(a * b)
    
    # توليد خيارات خاطئة
    correct = int(answer)
    options = {correct}
    while len(options) < 4:
        offset = random.randint(-15, 15)
        if offset != 0:
            options.add(max(0, correct + offset))
    
    options_list = list(options)
    random.shuffle(options_list)
    
    return question, answer, options_list

def trigger_captcha(uid):
    """تفعيل الكابتشا لمستخدم مشتبه به"""
    from telebot import types
    uid = str(uid)
    
    question, answer, options = generate_captcha()
    captcha_sessions[uid] = {
        "answer": answer,
        "attempts": 0,
        "expires": time.time() + 120  # ساعتين
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for opt in options:
        markup.add(types.InlineKeyboardButton(f"  {opt}  ", callback_data=f"captcha_ans_{opt}"))
    
    try:
        bot.send_message(int(uid), 
            f"🛡️ <b>═══ فحص أمني ═══</b>\n\n"
            f"⚠️ تم رصد نشاط مشبوه من حسابك (رشق أزرار).\n\n"
            f"🧮 <b>حل المعادلة للمتابعة:</b>\n\n"
            f"<code>{question} = ?</code>\n\n"
            f"⏱️ لديك <b>دقيقتان</b> فقط | 3 محاولات",
            reply_markup=markup, parse_mode="HTML")
    except:
        pass

def is_captcha_pending(uid):
    """فحص إذا كان المستخدم لديه كابتشا معلقة"""
    uid = str(uid)
    if uid not in captcha_sessions:
        return False
    session = captcha_sessions[uid]
    if time.time() > session["expires"]:
        del captcha_sessions[uid]
        return False
    return True

def verify_captcha(uid, user_answer):
    """التحقق من إجابة الكابتشا"""
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
        # حظر مؤقت لمدة ساعة
        from database import update_user_data
        from datetime import timedelta
        until = (datetime.now() + timedelta(hours=1)).isoformat()
        update_user_data(uid, banned_until=until)
        return "banned"
    
    return "wrong"

def require_verification_on_start(uid):
    """كابتشا إجبارية عند أول تسجيل"""
    from database import get_user
    u = get_user(uid)
    if u and not u.get("verified", False):
        trigger_captcha(uid)
        return True
    return False
