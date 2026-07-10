import time
import random
import string
from datetime import datetime, timedelta
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, t

user_last_msg = {}
captcha_sessions = {}
spam_warnings = {}
active_ticket_chats = {}  # {uid: ticket_id} = المستخدم في وضع دردشة مع تذكرة
admin_ticket_chats = {}  # {admin_uid: {ticket_id, user_uid}} = الأدمن يرد على تذكرة

def check_spam(uid):
    uid = str(uid)
    current = time.time()
    if uid in user_last_msg:
        if current - user_last_msg[uid] < 0.5:
            spam_warnings[uid] = spam_warnings.get(uid, 0) + 1
            user_last_msg[uid] = current
            if spam_warnings[uid] >= 5:
                trigger_captcha(uid)
                spam_warnings[uid] = 0
            return True
    user_last_msg[uid] = current
    return False

def is_user_banned(uid):
    from database import get_user, update_user_data
    uid = str(uid)
    u = get_user(uid)
    if not u: return False
    if u.get("banned", False): return True
    tu = u.get("banned_until")
    if tu:
        try:
            if datetime.now() < datetime.fromisoformat(tu):
                return True
            else:
                update_user_data(uid, banned_until=None)
        except: pass
    return False

def check_channel_join(uid):
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        return True
    try:
        m = bot.get_chat_member(CHANNEL_ID, uid)
        if m.status in ['member', 'creator', 'administrator']:
            return True
    except: pass
    return False

def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fk = ''.join(random.choice(chars) for _ in range(16))
    return f"{fk[:6]}***********{fk[-4:]}"

def generate_captcha(lang="ar"):
    pool = {
        "ar": [("🍎", "التفاحة"), ("🍌", "الموزة"), ("🍇", "العنب"), ("🚗", "السيارة"),
               ("⚽", "الكرة"), ("🐶", "الكلب"), ("🐱", "القط"), ("⭐", "النجمة")],
        "en": [("🍎", "Apple"), ("🍌", "Banana"), ("🍇", "Grapes"), ("🚗", "Car"),
               ("⚽", "Ball"), ("🐶", "Dog"), ("🐱", "Cat"), ("⭐", "Star")],
        "fr": [("🍎", "Pomme"), ("🍌", "Banane"), ("🍇", "Raisin"), ("🚗", "Voiture"),
               ("⚽", "Ballon"), ("🐶", "Chien"), ("🐱", "Chat"), ("⭐", "Étoile")],
        "es": [("🍎", "Manzana"), ("🍌", "Plátano"), ("🍇", "Uvas"), ("🚗", "Coche"),
               ("⚽", "Pelota"), ("🐶", "Perro"), ("🐱", "Gato"), ("⭐", "Estrella")],
        "vi": [("🍎", "Táo"), ("🍌", "Chuối"), ("🍇", "Nho"), ("🚗", "Xe"),
               ("⚽", "Bóng"), ("🐶", "Chó"), ("🐱", "Mèo"), ("⭐", "Sao")]
    }
    p = pool.get(lang, pool["en"])
    chosen = random.sample(p, 4)
    correct = random.choice(chosen)
    return correct[0], correct[1], [i[0] for i in chosen]

def trigger_captcha(uid):
    from telebot import types
    from database import get_user
    uid = str(uid)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    emoji, name, opts = generate_captcha(lang)
    captcha_sessions[uid] = {"answer": emoji, "attempts": 0, "expires": time.time() + 300}
    m = types.InlineKeyboardMarkup(row_width=2)
    random.shuffle(opts)
    m.add(*[types.InlineKeyboardButton(o, callback_data=f"captcha_ans_{o}") for o in opts])
    try:
        bot.send_message(int(uid), t(lang, "captcha_title", name=name, emoji=emoji),
                        reply_markup=m, parse_mode="HTML")
    except: pass

def is_captcha_pending(uid):
    uid = str(uid)
    if uid not in captcha_sessions: return False
    if time.time() > captcha_sessions[uid]["expires"]:
        del captcha_sessions[uid]
        return False
    return True

def verify_captcha(uid, ans):
    uid = str(uid)
    if uid not in captcha_sessions: return "no_session"
    s = captcha_sessions[uid]
    if time.time() > s["expires"]:
        del captcha_sessions[uid]
        return "expired"
    if str(ans) == s["answer"]:
        del captcha_sessions[uid]
        return "correct"
    s["attempts"] += 1
    if s["attempts"] >= 3:
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

# ================================
# ⚡ نظام العروض الخاطفة
# ================================
def get_active_flash_sale():
    from database import bot_config
    fs = bot_config.get("flash_sales", {})
    active = fs.get("current")
    if not active: return None
    if datetime.now() > datetime.fromisoformat(active["expires"]):
        bot_config["flash_sales"]["current"] = None
        from database import save_json, DB_CONFIG
        save_json(DB_CONFIG, bot_config)
        return None
    return active

def create_flash_sale(product, discount, hours):
    from database import bot_config, save_json, DB_CONFIG
    expires = datetime.now() + timedelta(hours=hours)
    if "flash_sales" not in bot_config: bot_config["flash_sales"] = {}
    bot_config["flash_sales"]["current"] = {
        "product": product, "discount": discount,
        "expires": expires.isoformat(),
        "created": datetime.now().isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    return expires

def format_time_remaining(expires_iso):
    try:
        exp = datetime.fromisoformat(expires_iso)
        diff = exp - datetime.now()
        if diff.total_seconds() <= 0: return "00:00:00"
        h = diff.seconds // 3600
        m = (diff.seconds % 3600) // 60
        s = diff.seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    except:
        return "00:00:00"

# ================================
# 🎬 أنيميشن (تأثيرات بصرية)
# ================================
def animate_message(chat_id, msg_id, frames, delay=0.4):
    """تأثير أنيميشن على الرسالة"""
    for f in frames:
        try:
            bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
            time.sleep(delay)
        except: pass

# ================================
# 🌐 نشر بالقناة (إنجليزي فقط + جميل)
# ================================
def publish_sale_to_channel(product, plan, price):
    """نشر عملية بيع للقناة - بالإنجليزية"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    msg = (
        f"🔥 ═══════════════════ 🔥\n"
        f"      💎 <b>NEW SALE!</b> 💎\n"
        f"🔥 ═══════════════════ 🔥\n\n"
        f"📦 <b>Product:</b> <code>{product}</code>\n"
        f"⏱️ <b>Duration:</b> {plan}\n"
        f"💰 <b>Price:</b> {price} 💎\n"
        f"⚡ <b>Delivery:</b> Instant\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🛒 <b>Buy Now:</b> t.me/{bot_user}\n"
        f"⭐ <b>24/7 Support</b>"
    )
    try:
        bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
    except: pass

def publish_fake_marketing():
    """تسويق وهمي - بالإنجليزية"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    plans = ["1 Day", "7 Days", "30 Days"]
    plan = random.choice(plans)
    fake_key = generate_fake_key()
    
    msg = (
        f"⚡ ═══════════════════ ⚡\n"
        f"    🔥 <b>SALE ALERT!</b> 🔥\n"
        f"⚡ ═══════════════════ ⚡\n\n"
        f"✅ <b>Successfully Sold!</b>\n\n"
        f"📦 <b>Product:</b> <code>Flourite Cheat</code>\n"
        f"⏱️ <b>Duration:</b> {plan}\n"
        f"🔐 <b>Key:</b> <code>{fake_key}</code>\n"
        f"⚡ <b>Status:</b> ✅ Delivered\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🛒 <b>Get Yours:</b> t.me/{bot_user}\n"
        f"⭐ <b>Trusted by 1000+ users</b>"
    )
    try:
        bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
        return True
    except:
        return False

def publish_prices_to_channel(prices_config, discount=0):
    """نشر قائمة الأسعار - بالإنجليزية"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    msg = (
        f"💎 ═══════════════════ 💎\n"
        f"   🛍️ <b>PRICE LIST</b> 🛍️\n"
        f"💎 ═══════════════════ 💎\n\n"
    )
    
    for prod, plans in prices_config.items():
        msg += f"📦 <b>{prod}</b>\n"
        for plan, base_p in plans.items():
            final = int(base_p * (1 - discount/100))
            msg += f"   ⏱️ {plan} ➜ <b>{final}</b> 💎\n"
        msg += "\n"
    
    if discount > 0:
        msg += f"🔥 <b>Special Discount:</b> {discount}% OFF\n\n"
    
    msg += (
        f"━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Instant Delivery</b>\n"
        f"🔒 <b>100% Secure</b>\n"
        f"⭐ <b>24/7 Support</b>\n\n"
        f"🛒 <b>Buy Now:</b> t.me/{bot_user}"
    )
    
    try:
        bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
        return True
    except:
        return False

def publish_flash_sale_to_channel(product, discount, hours):
    """نشر إعلان عرض خاطف - بالإنجليزية"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    msg = (
        f"⚡⚡⚡ ═══════════════ ⚡⚡⚡\n"
        f"     🔥 <b>FLASH SALE!</b> 🔥\n"
        f"⚡⚡⚡ ═══════════════ ⚡⚡⚡\n\n"
        f"💥 <b>{discount}% OFF</b> 💥\n\n"
        f"📦 <b>Product:</b> {product}\n"
        f"⏰ <b>Duration:</b> {hours} hours ONLY\n"
        f"🎯 <b>Save:</b> {discount}%\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>LIMITED TIME!</b>\n"
        f"💨 <b>Don't miss out!</b>\n\n"
        f"🛒 <b>Grab Now:</b> t.me/{bot_user}"
    )
    try:
        bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
        return True
    except:
        return False
