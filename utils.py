import time
import random
import inspect
from telebot import types

# Bot API 9.4 style is optional on older pyTelegramBotAPI versions.
_STYLE_OK = 'style' in inspect.signature(types.InlineKeyboardButton.__init__).parameters
_REPLY_STYLE_OK = 'style' in inspect.signature(types.KeyboardButton.__init__).parameters

def ikb(text, cb=None, url=None, style=None):
    kw = {}
    if cb is not None: kw['callback_data'] = cb
    if url is not None: kw['url'] = url
    if style and _STYLE_OK: kw['style'] = style
    return types.InlineKeyboardButton(text, **kw)

def rkb(text, style=None, **kwargs):
    if style and _REPLY_STYLE_OK: kwargs['style'] = style
    return types.KeyboardButton(text, **kwargs)

import random
import string
from datetime import datetime, timedelta
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, t

# =====================================================
# 🌐 متغيرات عامة للحالات المؤقتة
# =====================================================
user_last_msg = {}
captcha_sessions = {}
spam_warnings = {}
active_ticket_chats = {}    # {user_uid: ticket_id}
admin_ticket_chats = {}     # {admin_uid: {ticket_id, user_uid}}
join_check_cooldown = {}    # {uid: timestamp} - منع الرشق على زر التحقق

# =====================================================
# 🛡️ مكافحة السبام الذكي
# =====================================================
def check_spam(uid):
    """
    فحص السبام - إذا أرسل أكثر من رسالة كل نصف ثانية = سبام
    بعد 5 تحذيرات = كابتشا إجبارية
    """
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

# =====================================================
# ⛔ فحص الحظر
# =====================================================
def is_user_banned(uid):
    """فحص إذا كان المستخدم محظور (دائم أو مؤقت)"""
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
                # انتهى الحظر المؤقت
                update_user_data(uid, banned_until=None)
        except: pass
    return False

# =====================================================
# 📢 فحص الاشتراك بالقناة (محسّن + منع الرشق)
# =====================================================
def check_channel_join(uid):
    """Return True only when the user joined every configured channel."""
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        return True
    from database import bot_config
    channels = bot_config.get("force_sub_channels", [])
    for channel in channels:
        try:
            member = bot.get_chat_member(channel["id"], int(uid))
            if str(member.status).lower() not in ("member", "creator", "administrator", "owner"):
                return False
        except Exception as e:
            print(f"⚠️ Channel check error for {uid}: {e}")
            return False
    return True

def can_check_join(uid):
    """
    منع الرشق على زر التحقق - يسمح بفحص واحد كل 3 ثواني
    """
    uid = str(uid)
    now = time.time()
    if uid in join_check_cooldown:
        if now - join_check_cooldown[uid] < 3:
            return False
    join_check_cooldown[uid] = now
    return True

# =====================================================
# 🔐 توليد مفتاح وهمي للتسويق
# =====================================================
def generate_fake_key():
    """مفتاح وهمي جميل للنشر التسويقي"""
    chars = string.ascii_uppercase + string.digits
    fk = ''.join(random.choice(chars) for _ in range(16))
    return f"{fk[:6]}***********{fk[-4:]}"

# =====================================================
# 🎨 توليد كابتشا سهلة (إيموجي مترجمة)
# =====================================================
def generate_captcha(lang="ar"):
    """كابتشا إيموجي - سهلة جداً للمستخدم الحقيقي"""
    pool = {
        "ar": [
            ("🍎", "التفاحة"), ("🍌", "الموزة"), ("🍇", "العنب"), ("🍓", "الفراولة"),
            ("🚗", "السيارة"), ("✈️", "الطائرة"), ("⚽", "الكرة"), ("🎈", "البالون"),
            ("🐶", "الكلب"), ("🐱", "القط"), ("⭐", "النجمة"), ("❤️", "القلب")
        ],
        "en": [
            ("🍎", "Apple"), ("🍌", "Banana"), ("🍇", "Grapes"), ("🍓", "Strawberry"),
            ("🚗", "Car"), ("✈️", "Airplane"), ("⚽", "Ball"), ("🎈", "Balloon"),
            ("🐶", "Dog"), ("🐱", "Cat"), ("⭐", "Star"), ("❤️", "Heart")
        ],
        "fr": [
            ("🍎", "Pomme"), ("🍌", "Banane"), ("🍇", "Raisin"), ("🍓", "Fraise"),
            ("🚗", "Voiture"), ("✈️", "Avion"), ("⚽", "Ballon"), ("🎈", "Ballon"),
            ("🐶", "Chien"), ("🐱", "Chat"), ("⭐", "Étoile"), ("❤️", "Cœur")
        ],
        "es": [
            ("🍎", "Manzana"), ("🍌", "Plátano"), ("🍇", "Uvas"), ("🍓", "Fresa"),
            ("🚗", "Coche"), ("✈️", "Avión"), ("⚽", "Pelota"), ("🎈", "Globo"),
            ("🐶", "Perro"), ("🐱", "Gato"), ("⭐", "Estrella"), ("❤️", "Corazón")
        ],
        "vi": [
            ("🍎", "Táo"), ("🍌", "Chuối"), ("🍇", "Nho"), ("🍓", "Dâu"),
            ("🚗", "Xe"), ("✈️", "Máy bay"), ("⚽", "Bóng"), ("🎈", "Bóng bay"),
            ("🐶", "Chó"), ("🐱", "Mèo"), ("⭐", "Sao"), ("❤️", "Tim")
        ]
    }
    p = pool.get(lang, pool["en"])
    chosen = random.sample(p, 4)
    correct = random.choice(chosen)
    return correct[0], correct[1], [i[0] for i in chosen]

def trigger_captcha(uid):
    """إرسال كابتشا للمستخدم"""
    from telebot import types
    from database import get_user
    uid = str(uid)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    emoji, name, opts = generate_captcha(lang)
    captcha_sessions[uid] = {
        "answer": emoji,
        "attempts": 0,
        "expires": time.time() + 300  # 5 دقائق
    }
    
    m = types.InlineKeyboardMarkup(row_width=2)
    random.shuffle(opts)
    m.add(*[types.InlineKeyboardButton(o, callback_data=f"captcha_ans_{o}") for o in opts])
    
    try:
        bot.send_message(
            int(uid),
            t(lang, "captcha_title", name=name, emoji=emoji),
            reply_markup=m,
            parse_mode="HTML"
        )
    except: pass

def is_captcha_pending(uid):
    """فحص إذا كان المستخدم لديه كابتشا معلقة"""
    uid = str(uid)
    if uid not in captcha_sessions: return False
    if time.time() > captcha_sessions[uid]["expires"]:
        del captcha_sessions[uid]
        return False
    return True

def verify_captcha(uid, ans):
    """التحقق من إجابة الكابتشا"""
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
    """كابتشا إجبارية للمستخدمين الجدد"""
    from database import get_user
    u = get_user(uid)
    if u and not u.get("verified", False):
        trigger_captcha(uid)
        return True
    return False

# =====================================================
# ⚡ نظام العروض الخاطفة
# =====================================================
def get_active_flash_sale():
    """جلب العرض الخاطف النشط (إن وجد)"""
    from database import bot_config
    fs = bot_config.get("flash_sales", {})
    active = fs.get("current")
    if not active: return None
    try:
        if datetime.now() > datetime.fromisoformat(active["expires"]):
            # انتهى العرض
            bot_config["flash_sales"]["current"] = None
            from database import save_json, DB_CONFIG
            save_json(DB_CONFIG, bot_config)
            return None
    except:
        return None
    return active

def create_flash_sale(product, discount, hours):
    """إنشاء عرض خاطف جديد"""
    from database import bot_config, save_json, DB_CONFIG
    expires = datetime.now() + timedelta(hours=hours)
    if "flash_sales" not in bot_config:
        bot_config["flash_sales"] = {}
    bot_config["flash_sales"]["current"] = {
        "product": product,
        "discount": discount,
        "expires": expires.isoformat(),
        "created": datetime.now().isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    return expires

def format_time_remaining(expires_iso):
    """تنسيق الوقت المتبقي بشكل جميل"""
    try:
        exp = datetime.fromisoformat(expires_iso)
        diff = exp - datetime.now()
        if diff.total_seconds() <= 0:
            return "00:00:00"
        h = diff.seconds // 3600
        m = (diff.seconds % 3600) // 60
        s = diff.seconds % 60
        # إضافة الأيام إن وجدت
        if diff.days > 0:
            return f"{diff.days}d {h:02d}:{m:02d}"
        return f"{h:02d}:{m:02d}:{s:02d}"
    except:
        return "00:00:00"

# =====================================================
# 🎬 تأثيرات الأنيميشن
# =====================================================
def animate_message(chat_id, msg_id, frames, delay=0.4):
    """
    تأثير أنيميشن على رسالة موجودة
    مثال: ["⏳ Loading...", "✨ Loading...", "✅ Done!"]
    """
    for f in frames:
        try:
            bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
            time.sleep(delay)
        except: pass

def send_typing_action(chat_id, duration=1):
    """إظهار 'يكتب...' في المحادثة"""
    try:
        bot.send_chat_action(chat_id, "typing")
        if duration > 0:
            time.sleep(duration)
    except: pass

# =====================================================
# 📢 النشر الموحد في كل القنوات المضافة
# =====================================================
# يتم جمع القنوات من قائمتي الاشتراك الإجباري والقنوات المُدارة، مع إزالة
# التكرار. لذلك فإن أي قناة أضيفت من لوحة الإدارة تستقبل جميع إعلانات
# التسويق ورسائل القناة وإشعارات المبيعات تلقائياً.
VIP_CHANNEL_ANNOUNCEMENT_MIN_STARS = 20


def get_publish_channels():
    """Return every unique administrator-configured channel for publishing.

    ``force_sub_channels`` is the source of truth for channels added through
    the subscription panel, while ``managed_channels`` keeps compatibility
    with the older publishing panel.  A channel may appear in both lists, so
    it is deliberately sent to once only.
    """
    from database import bot_config

    channels = []
    seen_ids = set()
    for config_key in ("force_sub_channels", "managed_channels"):
        for channel in bot_config.get(config_key, []) or []:
            if not isinstance(channel, dict) or channel.get("id") in (None, ""):
                continue
            try:
                channel_id = int(channel["id"])
            except (TypeError, ValueError):
                # Keep supporting valid Telegram @usernames stored by an older
                # configuration, while still deduplicating them reliably.
                channel_id = str(channel["id"]).strip()
            if not channel_id or channel_id in seen_ids:
                continue
            seen_ids.add(channel_id)
            channels.append({
                "id": channel_id,
                "label": str(channel.get("label") or "قناة"),
                "url": channel.get("url"),
            })

    # Fresh installations and legacy configurations may have no saved list
    # yet.  Preserve their original single configured channel as a fallback.
    if not channels and CHANNEL_ID:
        channels.append({"id": int(CHANNEL_ID), "label": "القناة", "url": CHANNEL_LINK})
    return channels


def broadcast_channel_message(text, **kwargs):
    """Send one text message to every added channel.

    Returns ``{channel_id: message_id}`` for successfully delivered messages.
    One inaccessible channel never prevents delivery to the remaining ones.
    The bot must be an administrator with posting permission in each channel.
    """
    delivered = {}
    for channel in get_publish_channels():
        channel_id = channel["id"]
        try:
            sent = bot.send_message(channel_id, text, **kwargs)
            delivered[str(channel_id)] = sent.message_id
        except Exception as exc:
            print(f"⚠️ Channel publish failed for {channel_id}: {exc}")
    return delivered


def broadcast_channel_voice(voice, **kwargs):
    """Send a voice message to every added channel and return delivered IDs."""
    delivered = {}
    for channel in get_publish_channels():
        channel_id = channel["id"]
        try:
            sent = bot.send_voice(channel_id, voice, **kwargs)
            delivered[str(channel_id)] = sent.message_id
        except Exception as exc:
            print(f"⚠️ Channel voice publish failed for {channel_id}: {exc}")
    return delivered


def _claim_payment_announcement(event_type, charge_id):
    """Prevent duplicate channel announcements when payment handlers overlap."""
    if not charge_id:
        return True
    from database import bot_config, save_json, DB_CONFIG

    key = f"{event_type}:{charge_id}"
    announced = bot_config.setdefault("channel_payment_announcements", [])
    if key in announced:
        return False
    announced.append(key)
    # A bounded history is enough to deduplicate Telegram's payment updates
    # without allowing the configuration file to grow indefinitely.
    bot_config["channel_payment_announcements"] = announced[-1000:]
    save_json(DB_CONFIG, bot_config)
    return True


def publish_vip_purchase_to_channels(stars_amount, charge_id=None):
    """Announce a paid VIP purchase only when it is strictly above 20 Stars."""
    try:
        stars_amount = int(stars_amount)
    except (TypeError, ValueError):
        return {}
    if stars_amount <= VIP_CHANNEL_ANNOUNCEMENT_MIN_STARS:
        return {}
    if not _claim_payment_announcement("vip", charge_id):
        return {}

    try:
        bot_user = bot.get_me().username
    except Exception:
        bot_user = "bot"
    hook = random.choice([
        "👑 <b>NEW VIP MEMBER!</b>",
        "💎 <b>VIP UPGRADED!</b>",
        "⭐ <b>EXCLUSIVE MEMBER!</b>",
        "🎊 <b>ANOTHER HAPPY VIP!</b>",
    ])
    message = (
        f"╔═══════════════════════╗\n"
        f"║ {hook} \n"
        f"╚═══════════════════════╝\n\n"
        f"🎉 A user just joined VIP club!\n\n"
        f"💎 Exclusive Benefits:\n"
        f"├── 🎁 2x Daily bonus\n"
        f"├── 💰 15% off everything\n"
        f"├── 📊 Advanced stock info\n"
        f"├── 🎫 Weekly free code\n"
        f"├── ⚡ Priority support\n"
        f"└── 👑 VIP badge\n\n"
        f"🌟 <b>Join VIP now:</b>\n"
        f"🤖 t.me/{bot_user}"
    )
    return broadcast_channel_message(message, parse_mode="HTML")


def publish_stars_conversion_to_channels(stars_amount, points_amount, charge_id=None):
    """Announce a Stars-to-points purchase in every added channel once."""
    if not _claim_payment_announcement("stars_conversion", charge_id):
        return {}
    try:
        bot_user = bot.get_me().username
    except Exception:
        bot_user = "bot"
    hook = random.choice([
        "⭐ <b>NEW CONVERSION!</b>",
        "💫 <b>STARS TO POINTS!</b>",
        "🌟 <b>SMART TRADE!</b>",
    ])
    message = (
        f"╔═══════════════════════╗\n"
        f"║ {hook} \n"
        f"╚═══════════════════════╝\n\n"
        f"⚡ Instant conversion completed!\n\n"
        f"⭐ Stars used: <b>{stars_amount}</b>\n"
        f"💎 Points received: <b>{points_amount}</b>\n"
        f"✅ Status: Delivered\n\n"
        f"🌟 <b>Convert now:</b>\n"
        f"🤖 t.me/{bot_user}"
    )
    return broadcast_channel_message(message, parse_mode="HTML")


# =====================================================
# 📢 دوال النشر بالقناة (بالإنجليزية - جميلة)
# =====================================================
def publish_sale_to_channel(product, plan, price):
    """نشر عملية بيع ناجحة للقناة"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    msg = (
        f"╔═══════════════════╗\n"
        f"║  🔥 <b>NEW SALE!</b> 🔥   ║\n"
        f"╚═══════════════════╝\n\n"
        f"📦 <b>Product:</b> <code>{product}</code>\n"
        f"⏱️ <b>Duration:</b> {plan}\n"
        f"💰 <b>Price:</b> {price} 💎\n"
        f"⚡ <b>Delivery:</b> Instant ✅\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 <b>Buy Now:</b> t.me/{bot_user}\n"
        f"⭐ <b>24/7 Support Available</b>\n"
        f"🔒 <b>100% Secure Transactions</b>"
    )
    broadcast_channel_message(msg, parse_mode="HTML")

def publish_fake_marketing():
    """نشر منشور تسويقي وهمي جميل"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    plans = ["1 Day", "7 Days", "30 Days"]
    plan = random.choice(plans)
    fake_key = generate_fake_key()
    
    # اختيار عبارة عشوائية للتنوع
    hooks = [
        "🔥 <b>SALE ALERT!</b> 🔥",
        "⚡ <b>NEW ORDER!</b> ⚡",
        "💎 <b>PURCHASE COMPLETE!</b> 💎",
        "🎉 <b>ANOTHER HAPPY CUSTOMER!</b> 🎉"
    ]
    hook = random.choice(hooks)
    
    msg = (
        f"╔═══════════════════╗\n"
        f"║  {hook}   \n"
        f"╚═══════════════════╝\n\n"
        f"✅ <b>Successfully Delivered!</b>\n\n"
        f"📦 <b>Product:</b> <code>Flourite Cheat</code>\n"
        f"⏱️ <b>Duration:</b> {plan}\n"
        f"🔐 <b>Key:</b> <code>{fake_key}</code>\n"
        f"⚡ <b>Status:</b> ✅ Delivered\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 <b>Get Yours:</b> t.me/{bot_user}\n"
        f"⭐ <b>Trusted by 1000+ users</b>\n"
        f"💎 <b>Best prices guaranteed</b>"
    )
    return bool(broadcast_channel_message(msg, parse_mode="HTML"))

def publish_prices_to_channel(prices_config, discount=0):
    """نشر قائمة الأسعار الكاملة بالقناة"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    msg = (
        f"╔═══════════════════╗\n"
        f"║  🛍️ <b>PRICE LIST</b> 🛍️   ║\n"
        f"╚═══════════════════╝\n\n"
    )
    
    for prod, plans in prices_config.items():
        msg += f"📦 <b>{prod}</b>\n"
        for plan, base_p in plans.items():
            final = int(base_p * (1 - discount/100))
            if discount > 0:
                msg += f"   ⏱️ {plan} ➜ <s>{base_p}</s> <b>{final}</b> 💎\n"
            else:
                msg += f"   ⏱️ {plan} ➜ <b>{final}</b> 💎\n"
        msg += "\n"
    
    if discount > 0:
        msg += f"🔥 <b>SPECIAL DISCOUNT:</b> {discount}% OFF\n"
        msg += f"⏰ <b>Limited time offer!</b>\n\n"
    
    msg += (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Instant Delivery</b>\n"
        f"🔒 <b>100% Secure Payment</b>\n"
        f"⭐ <b>24/7 Customer Support</b>\n"
        f"💎 <b>Best Quality Guarantee</b>\n\n"
        f"🛒 <b>Buy Now:</b> t.me/{bot_user}"
    )
    
    return bool(broadcast_channel_message(msg, parse_mode="HTML"))

def publish_flash_sale_to_channel(product, discount, hours):
    """نشر إعلان عرض خاطف مميز"""
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    msg = (
        f"⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\n"
        f"    🔥 <b>FLASH SALE!</b> 🔥\n"
        f"⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\n\n"
        f"💥💥 <b>{discount}% OFF</b> 💥💥\n\n"
        f"📦 <b>Product:</b> <code>{product}</code>\n"
        f"⏰ <b>Duration:</b> {hours} hours ONLY\n"
        f"🎯 <b>You Save:</b> {discount}%\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>⏳ LIMITED TIME!</b>\n"
        f"💨 <b>Don't miss out!</b>\n"
        f"🏃 <b>Hurry before it ends!</b>\n\n"
        f"🛒 <b>Grab Now:</b> t.me/{bot_user}"
    )
    return bool(broadcast_channel_message(msg, parse_mode="HTML"))

def publish_maintenance_notice(is_on):
    """نشر إشعار الصيانة بالقناة"""
    if is_on:
        msg = (
            f"╔═══════════════════╗\n"
            f"║  🛠️ <b>MAINTENANCE</b> 🛠️  ║\n"
            f"╚═══════════════════╝\n\n"
            f"⚠️ <b>Bot is under maintenance</b>\n"
            f"⏳ <b>We'll be back soon!</b>\n\n"
            f"🔧 <i>Improving your experience...</i>\n"
            f"💎 <i>Thank you for your patience</i>"
        )
    else:
        msg = (
            f"╔═══════════════════╗\n"
            f"║  ✅ <b>WE'RE BACK!</b> ✅   ║\n"
            f"╚═══════════════════╝\n\n"
            f"🎉 <b>Bot is now ONLINE!</b>\n"
            f"⚡ <b>All services restored</b>\n\n"
            f"🛒 <i>Start shopping now!</i>"
        )
    broadcast_channel_message(msg, parse_mode="HTML")
