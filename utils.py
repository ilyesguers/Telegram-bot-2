import time
import random
import string
from datetime import datetime, timedelta
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, t

user_last_msg = {}
captcha_sessions = {}
spam_warnings = {}

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

def is_user_banned(uid):
    from database import get_user, update_user_data
    uid = str(uid)
    u = get_user(uid)
    if not u: return False
    if u.get("banned", False): return True
    temp_until = u.get("banned_until")
    if temp_until:
        try:
            if datetime.now() < datetime.fromisoformat(temp_until):
                return True
            else:
                update_user_data(uid, banned_until=None)
        except: pass
    return False

def check_channel_join(uid):
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, uid)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception as e:
        print(f"⚠️ {uid}: {e}")
    return False

def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

def generate_captcha(lang="ar"):
    """كابتشا إيموجي بمترجم"""
    emojis_pool = {
        "ar": [("🍎", "التفاحة"), ("🍌", "الموزة"), ("🍇", "العنب"), ("🚗", "السيارة"),
               ("⚽", "الكرة"), ("🐶", "الكلب"), ("🐱", "القط"), ("⭐", "النجمة"), ("❤️", "القلب"), ("🎈", "البالون")],
        "en": [("🍎", "Apple"), ("🍌", "Banana"), ("🍇", "Grapes"), ("🚗", "Car"),
               ("⚽", "Ball"), ("🐶", "Dog"), ("🐱", "Cat"), ("⭐", "Star"), ("❤️", "Heart"), ("🎈", "Balloon")],
        "fr": [("🍎", "Pomme"), ("🍌", "Banane"), ("🍇", "Raisin"), ("🚗", "Voiture"),
               ("⚽", "Ballon"), ("🐶", "Chien"), ("🐱", "Chat"), ("⭐", "Étoile"), ("❤️", "Cœur"), ("🎈", "Ballon")],
        "es": [("🍎", "Manzana"), ("🍌", "Plátano"), ("🍇", "Uvas"), ("🚗", "Coche"),
               ("⚽", "Pelota"), ("🐶", "Perro"), ("🐱", "Gato"), ("⭐", "Estrella"), ("❤️", "Corazón"), ("🎈", "Globo")],
        "vi": [("🍎", "Táo"), ("🍌", "Chuối"), ("🍇", "Nho"), ("🚗", "Xe"),
               ("⚽", "Bóng"), ("🐶", "Chó"), ("🐱", "Mèo"), ("⭐", "Sao"), ("❤️", "Tim"), ("🎈", "Bóng bay")]
    }
    pool = emojis_pool.get(lang, emojis_pool["en"])
    chosen = random.sample(pool, 4)
    correct = random.choice(chosen)
    return correct[0], correct[1], [item[0] for item in chosen]

def trigger_captcha(uid):
    from telebot import types
    from database import get_user
    uid = str(uid)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    emoji, name, options = generate_captcha(lang)
    captcha_sessions[uid] = {"answer": emoji, "attempts": 0, "expires": time.time() + 300}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    random.shuffle(options)
    buttons = [types.InlineKeyboardButton(opt, callback_data=f"captcha_ans_{opt}") for opt in options]
    markup.add(*buttons)
    
    try:
        bot.send_message(int(uid), t(lang, "captcha_title", name=name, emoji=emoji),
                        reply_markup=markup, parse_mode="HTML")
    except: pass

def is_captcha_pending(uid):
    uid = str(uid)
    if uid not in captcha_sessions: return False
    if time.time() > captcha_sessions[uid]["expires"]:
        del captcha_sessions[uid]
        return False
    return True

def verify_captcha(uid, user_answer):
    uid = str(uid)
    if uid not in captcha_sessions: return "no_session"
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
    from database import get_user
    u = get_user(uid)
    if u and not u.get("verified", False):
        trigger_captcha(uid)
        return True
    return False
