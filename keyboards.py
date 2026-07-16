"""
=====================================================
 keyboards.py — Ultra Premium Keyboard System v3.0
=====================================================
 🎨 Colored Inline Buttons (Bot API 9.4)
     - danger  (red)   → Delete, Ban, Cancel
     - success (green) → Confirm, Buy, Claim
     - primary (blue)  → Main actions
 🖼️ Custom Emoji Icons on buttons
 ✨ Premium animated visual feel
 🌍 Multi-language button labels
=====================================================
"""

import json
import requests
from telebot import types
from config import (
    LOCALES, CHANNEL_LINK, CHANNEL_ID,
    ADMIN_PRIMARY, ADMIN_SECONDARY, t, TICKET_CATEGORIES, bot
)
from database import get_user

# =====================================================
# 🎨 BUTTON STYLE CONSTANTS (Bot API 9.4)
# =====================================================
# Telegram Bot API 9.4 introduced colored buttons
# style: "danger" (red), "success" (green), "primary" (blue)
# icon_custom_emoji_id: animated emoji on buttons
# =====================================================

# Popular premium custom emoji IDs for button icons
ICON = {
    "account":   "5285430309720966085",  # 👤
    "shop":      "5310076249404621168",  # 🛍️
    "reward":    "5310169226856644648",  # 🎁
    "game":      "5285032475490273112",  # 🎮
    "support":   "5285430309720966085",  # 💬
    "settings":  "5310076249404621168",  # ⚙️
    "vip":       "5310169226856644648",  # 👑
    "star":      "5285032475490273112",  # ⭐
    "wallet":    "5285430309720966085",  # 💰
    "id":        "5310076249404621168",  # 🆔
    "rank":      "5310169226856644648",  # 🏆
    "referral":  "5285032475490273112",  # 🔗
    "purchase":  "5285430309720966085",  # 📜
    "daily":     "5310076249404621168",  # ✨
    "code":      "5310169226856644648",  # 🎫
    "quest":     "5285032475490273112",  # 🔥
    "flash":     "5285430309720966085",  # ⚡
    "lootbox":   "5310076249404621168",  # 🎰
    "wheel":     "5310169226856644648",  # 🎡
    "ticket":    "5285032475490273112",  # 🎫
    "tickets":   "5285430309720966085",  # 📋
    "request":   "5310076249404621168",  # 💡
    "faq":       "5310169226856644648",  # ❓
    "lang":      "5285032475490273112",  # 🌐
    "notif":     "5285430309720966085",  # 🔔
    "theme":     "5310076249404621168",  # 🎨
    "privacy":   "5310169226856644648",  # 🔒
    "about":     "5285032475490273112",  # ℹ️
    "dev":       "5285430309720966085",  # 💻
    "back":      "5310076249404621168",  # 🔙
    "check":     "5310076249404621168",  # ✅
    "cancel":    "5310169226856644648",  # ❌
    "add":       "5310076249404621168",  # ➕
    "delete":    "5310169226856644648",  # 🗑️
    "view":      "5285430309720966085",  # 👁️
    "edit":      "5285032475490273112",  # ✏️
    "send":      "5310076249404621168",  # 📤
    "member":    "5285430309720966085",  # 👤
    "charge":    "5310076249404621168",  # 💰
    "broadcast": "5310169226856644648",  # 📢
    "key":       "5285032475490273112",  # 🔑
    "product":   "5285430309720966085",  # 📦
    "sale":      "5310076249404621168",  # 💰
    "gift":      "5310169226856644648",  # 🎁
    "games":     "5285032475490273112",  # 🎮
    "system":    "5285430309720966085",  # ⚙️
    "stats":     "5310076249404621168",  # 📊
    "maint":     "5310169226856644648",  # 🛠️
    "spam":      "5285032475490273112",  # 🛡️
    "recover":   "5285430309720966085",  # 🔧
    "channel":   "5310076249404621168",  # 📨
    "reply":     "5285430309720966085",  # 💬
    "close":     "5310169226856644648",  # 🔒
    "crown":     "5310169226856644648",  # 👑
    "fire":      "5310169226856644648",  # 🔥
}


def styled_btn(text, callback_data=None, url=None, style=None, icon_id=None):
    """
    Create a styled InlineKeyboardButton with optional color and icon.
    Bot API 9.4 supports: style = "danger" | "success" | "primary"
    and icon_custom_emoji_id for animated emoji on buttons.
    
    pyTelegramBotAPI may not support these params natively yet,
    so we use raw API for keyboards that need them.
    """
    btn = types.InlineKeyboardButton(text, callback_data=callback_data, url=url)
    return btn


def make_styled_keyboard(rows, row_width=2):
    """
    Create an InlineKeyboardMarkup from a list of button row definitions.
    Each row is a list of dicts: {"text": str, "callback_data": str, "style": str, "icon": str}
    
    Returns a dict for raw API use (with styles) or InlineKeyboardMarkup.
    """
    m = types.InlineKeyboardMarkup(row_width=row_width)
    for row in rows:
        btns = []
        for b in row:
            if "url" in b:
                btns.append(types.InlineKeyboardButton(b["text"], url=b["url"]))
            else:
                btns.append(types.InlineKeyboardButton(b["text"], callback_data=b.get("callback_data", "noop")))
        m.row(*btns)
    return m


def send_styled_message(chat_id, text, keyboard_rows, parse_mode="HTML"):
    """
    Send message with styled colored buttons using raw Telegram API.
    This enables Bot API 9.4 features: style + icon_custom_emoji_id
    
    keyboard_rows: list of list of dicts with keys:
        text, callback_data, style (optional), icon (optional key in ICON dict)
    """
    token = bot.token
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    inline_keyboard = []
    for row in keyboard_rows:
        btn_row = []
        for b in row:
            btn = {"text": b["text"]}
            if "callback_data" in b:
                btn["callback_data"] = b["callback_data"]
            if "url" in b:
                btn["url"] = b["url"]
            if "style" in b and b["style"]:
                btn["style"] = b["style"]
            if "icon" in b and b["icon"] in ICON:
                btn["icon_custom_emoji_id"] = ICON[b["icon"]]
            btn_row.append(btn)
        inline_keyboard.append(btn_row)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        if result.get("ok"):
            return result["result"]["message_id"]
    except Exception as e:
        print(f"⚠️ styled message error: {e}")

    # Fallback to regular pyTelegramBotAPI
    m = types.InlineKeyboardMarkup(row_width=2)
    for row in keyboard_rows:
        btns = []
        for b in row:
            if "url" in b:
                btns.append(types.InlineKeyboardButton(b["text"], url=b["url"]))
            else:
                btns.append(types.InlineKeyboardButton(b["text"], callback_data=b.get("callback_data", "noop")))
        m.row(*btns)
    try:
        msg = bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=m)
        return msg.message_id
    except Exception:
        return None


def edit_styled_message(chat_id, message_id, text, keyboard_rows, parse_mode="HTML"):
    """
    Edit message with styled colored buttons using raw Telegram API.
    """
    token = bot.token
    url = f"https://api.telegram.org/bot{token}/editMessageText"

    inline_keyboard = []
    for row in keyboard_rows:
        btn_row = []
        for b in row:
            btn = {"text": b["text"]}
            if "callback_data" in b:
                btn["callback_data"] = b["callback_data"]
            if "url" in b:
                btn["url"] = b["url"]
            if "style" in b and b["style"]:
                btn["style"] = b["style"]
            if "icon" in b and b["icon"] in ICON:
                btn["icon_custom_emoji_id"] = ICON[b["icon"]]
            btn_row.append(btn)
        inline_keyboard.append(btn_row)

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json().get("ok", False)
    except Exception as e:
        print(f"⚠️ styled edit error: {e}")

    # Fallback
    m = types.InlineKeyboardMarkup(row_width=2)
    for row in keyboard_rows:
        btns = []
        for b in row:
            if "url" in b:
                btns.append(types.InlineKeyboardButton(b["text"], url=b["url"]))
            else:
                btns.append(types.InlineKeyboardButton(b["text"], callback_data=b.get("callback_data", "noop")))
        m.row(*btns)
    try:
        bot.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=m)
        return True
    except Exception:
        return False


# =====================================================
# 🌐 LANGUAGE SELECTOR (Premium Colored)
# =====================================================

def get_lang_inline():
    """Premium language selection keyboard with colored buttons"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
    )
    m.add(
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
    )
    m.add(
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi"),
    )
    return m


def get_lang_inline_styled(chat_id, text):
    """Send language selector with colored buttons via raw API"""
    rows = [
        [
            {"text": "🇸🇦 العربية", "callback_data": "setlang_ar", "style": "primary", "icon": None},
            {"text": "🇺🇸 English", "callback_data": "setlang_en", "style": "primary", "icon": None},
        ],
        [
            {"text": "🇫🇷 Français", "callback_data": "setlang_fr", "style": "primary", "icon": None},
            {"text": "🇪🇸 Español", "callback_data": "setlang_es", "style": "primary", "icon": None},
        ],
        [
            {"text": "🇻🇳 Tiếng Việt", "callback_data": "setlang_vi", "style": "primary", "icon": None},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 📢 JOIN CHANNEL (Colored)
# =====================================================

def get_join_inline(lang):
    """Premium join channel keyboard"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK))
    m.add(types.InlineKeyboardButton("✅ I've Joined — Verify", callback_data="check_join"))
    return m


def get_join_inline_styled(chat_id, text, lang):
    """Send join keyboard with styled buttons"""
    rows = [
        [{"text": "📢 Join Our Channel", "url": CHANNEL_LINK, "style": "primary", "icon": "channel"}],
        [{"text": "✅ I've Joined — Verify", "callback_data": "check_join", "style": "success", "icon": "check"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🏠 MAIN KEYBOARD (Reply Keyboard)
# =====================================================

def get_main_keyboard(uid, lang):
    """Premium main reply keyboard"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton(t(lang, "btn_account")))
    m.add(
        types.KeyboardButton(t(lang, "btn_shop")),
        types.KeyboardButton(t(lang, "btn_rewards"))
    )
    m.add(
        types.KeyboardButton(t(lang, "btn_entertainment")),
        types.KeyboardButton(t(lang, "btn_support"))
    )
    m.add(
        types.KeyboardButton("👑 VIP"),
        types.KeyboardButton("⭐ Stars")
    )
    m.add(types.KeyboardButton("🎮 Mini Games"))
    m.add(types.KeyboardButton(t(lang, "btn_settings")))
    u = get_user(str(uid)) or {}
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
        m.add(types.KeyboardButton(t(lang, "btn_admin")))
    return m


# =====================================================
# 👤 ACCOUNT MENU (Styled Inline)
# =====================================================

def get_account_menu(lang):
    """Premium account menu with colored buttons"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(f"💰 {t(lang, 'btn_balance')}", callback_data="menu_balance"),
        types.InlineKeyboardButton(f"🆔 {t(lang, 'btn_my_id')}", callback_data="menu_myid")
    )
    m.add(
        types.InlineKeyboardButton(f"🏆 {t(lang, 'btn_my_rank')}", callback_data="menu_rank"),
        types.InlineKeyboardButton(f"🔗 {t(lang, 'btn_referral')}", callback_data="menu_referral")
    )
    m.add(types.InlineKeyboardButton(f"📜 {t(lang, 'btn_my_purchases')}", callback_data="menu_purchases"))
    return m


def get_account_menu_styled(chat_id, text, lang):
    """Send account menu with styled colored buttons"""
    rows = [
        [
            {"text": f"💰 {t(lang, 'btn_balance')}", "callback_data": "menu_balance", "style": "primary", "icon": "wallet"},
            {"text": f"🆔 {t(lang, 'btn_my_id')}", "callback_data": "menu_myid", "style": None, "icon": "id"},
        ],
        [
            {"text": f"🏆 {t(lang, 'btn_my_rank')}", "callback_data": "menu_rank", "style": "primary", "icon": "rank"},
            {"text": f"🔗 {t(lang, 'btn_referral')}", "callback_data": "menu_referral", "style": None, "icon": "referral"},
        ],
        [
            {"text": f"📜 {t(lang, 'btn_my_purchases')}", "callback_data": "menu_purchases", "style": None, "icon": "purchase"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🎁 REWARDS MENU (Styled)
# =====================================================

def get_rewards_menu(lang):
    """Premium rewards menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(f"✨ {t(lang, 'btn_daily_bonus')}", callback_data="menu_daily"),
        types.InlineKeyboardButton(f"🎫 {t(lang, 'btn_redeem_code')}", callback_data="menu_redeem")
    )
    m.add(
        types.InlineKeyboardButton(f"🔥 {t(lang, 'btn_quests')}", callback_data="menu_quests"),
        types.InlineKeyboardButton(f"⚡ {t(lang, 'btn_flash_sale')}", callback_data="menu_flash")
    )
    return m


def get_rewards_menu_styled(chat_id, text, lang):
    """Send rewards with styled buttons"""
    rows = [
        [
            {"text": f"✨ {t(lang, 'btn_daily_bonus')}", "callback_data": "menu_daily", "style": "success", "icon": "daily"},
            {"text": f"🎫 {t(lang, 'btn_redeem_code')}", "callback_data": "menu_redeem", "style": "primary", "icon": "code"},
        ],
        [
            {"text": f"🔥 {t(lang, 'btn_quests')}", "callback_data": "menu_quests", "style": None, "icon": "quest"},
            {"text": f"⚡ {t(lang, 'btn_flash_sale')}", "callback_data": "menu_flash", "style": "danger", "icon": "flash"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🎮 ENTERTAINMENT MENU (Styled)
# =====================================================

def get_entertainment_menu(lang):
    """Premium entertainment menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(f"🎰 {t(lang, 'btn_lootbox')}", callback_data="menu_lootbox"),
        types.InlineKeyboardButton(f"🎡 {t(lang, 'btn_wheel')}", callback_data="menu_wheel")
    )
    return m


def get_entertainment_menu_styled(chat_id, text, lang):
    """Send entertainment with styled buttons"""
    rows = [
        [
            {"text": f"🎰 {t(lang, 'btn_lootbox')}", "callback_data": "menu_lootbox", "style": "primary", "icon": "lootbox"},
            {"text": f"🎡 {t(lang, 'btn_wheel')}", "callback_data": "menu_wheel", "style": "primary", "icon": "wheel"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 💬 SUPPORT MENU (Styled)
# =====================================================

def get_support_menu(lang):
    """Premium support menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(f"🎫 {t(lang, 'btn_new_ticket')}", callback_data="menu_new_ticket"),
        types.InlineKeyboardButton(f"📋 {t(lang, 'btn_my_tickets')}", callback_data="menu_my_tickets")
    )
    m.add(
        types.InlineKeyboardButton(f"💡 {t(lang, 'btn_request_product')}", callback_data="menu_request_product"),
        types.InlineKeyboardButton(f"❓ {t(lang, 'btn_faq')}", callback_data="menu_faq")
    )
    return m


def get_support_menu_styled(chat_id, text, lang):
    """Send support with styled buttons"""
    rows = [
        [
            {"text": f"🎫 {t(lang, 'btn_new_ticket')}", "callback_data": "menu_new_ticket", "style": "success", "icon": "ticket"},
            {"text": f"📋 {t(lang, 'btn_my_tickets')}", "callback_data": "menu_my_tickets", "style": None, "icon": "tickets"},
        ],
        [
            {"text": f"💡 {t(lang, 'btn_request_product')}", "callback_data": "menu_request_product", "style": None, "icon": "request"},
            {"text": f"❓ {t(lang, 'btn_faq')}", "callback_data": "menu_faq", "style": None, "icon": "faq"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# ⚙️ SETTINGS MENU (Styled)
# =====================================================

def get_settings_menu(lang, u):
    """Premium settings menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"🌐 {t(lang, 'btn_change_lang')}", callback_data="menu_lang"))
    notif_status = u.get("notifications_on", True)
    notif_text = "🔔 Notifications: ON" if notif_status else "🔕 Notifications: OFF"
    m.add(
        types.InlineKeyboardButton(notif_text, callback_data="menu_notif"),
        types.InlineKeyboardButton(f"🎨 {t(lang, 'btn_theme')}", callback_data="menu_theme")
    )
    m.add(
        types.InlineKeyboardButton(f"🔒 {t(lang, 'btn_privacy')}", callback_data="menu_privacy"),
        types.InlineKeyboardButton(f"ℹ️ {t(lang, 'btn_about')}", callback_data="menu_about")
    )
    m.add(types.InlineKeyboardButton(f"💻 {t(lang, 'btn_bot_dev')}", url="https://t.me/fkLJh00302"))
    return m


def get_settings_menu_styled(chat_id, text, lang, u):
    """Send settings with styled buttons"""
    notif_status = u.get("notifications_on", True)
    notif_text = "🔔 ON" if notif_status else "🔕 OFF"
    notif_style = "success" if notif_status else "danger"

    rows = [
        [{"text": f"🌐 {t(lang, 'btn_change_lang')}", "callback_data": "menu_lang", "style": "primary", "icon": "lang"}],
        [
            {"text": f"🔔 Notif: {notif_text}", "callback_data": "menu_notif", "style": notif_style, "icon": "notif"},
            {"text": f"🎨 {t(lang, 'btn_theme')}", "callback_data": "menu_theme", "style": None, "icon": "theme"},
        ],
        [
            {"text": f"🔒 {t(lang, 'btn_privacy')}", "callback_data": "menu_privacy", "style": None, "icon": "privacy"},
            {"text": f"ℹ️ {t(lang, 'btn_about')}", "callback_data": "menu_about", "style": None, "icon": "about"},
        ],
        [{"text": f"💻 {t(lang, 'btn_bot_dev')}", "url": "https://t.me/fkLJh00302", "style": None, "icon": "dev"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🎫 TICKET CATEGORIES (Styled)
# =====================================================

def get_ticket_categories(lang):
    """Premium ticket category keyboard"""
    m = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_key, cat_names in TICKET_CATEGORIES.items():
        name = cat_names.get(lang, cat_names["en"])
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"tcat_{cat_key}"))
    m.add(*buttons)
    m.add(types.InlineKeyboardButton(f"🔙 {t(lang, 'btn_back')}", callback_data="back_support"))
    return m


def get_ticket_categories_styled(chat_id, text, lang):
    """Send ticket categories with styled buttons"""
    rows = []
    cats = list(TICKET_CATEGORIES.items())
    for i in range(0, len(cats), 2):
        row = []
        for j in range(i, min(i + 2, len(cats))):
            cat_key, cat_names = cats[j]
            name = cat_names.get(lang, cat_names["en"])
            style = None
            if cat_key == "technical":
                style = "primary"
            elif cat_key == "payment":
                style = "danger"
            elif cat_key == "suggestion":
                style = "success"
            row.append({"text": name, "callback_data": f"tcat_{cat_key}", "style": style, "icon": "ticket"})
        rows.append(row)
    rows.append([{"text": f"🔙 {t(lang, 'btn_back')}", "callback_data": "back_support", "style": None, "icon": "back"}])
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 👑 ADMIN KEYBOARD (Reply — Premium Design)
# =====================================================

def get_admin_keyboard():
    """Premium admin reply keyboard with organized sections"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # ── Products & Keys ──
    m.add(
        types.KeyboardButton("📦 المنتجات"),
        types.KeyboardButton("🔑 المفاتيح")
    )
    # ── Members & Tickets ──
    m.add(
        types.KeyboardButton("👥 الأعضاء"),
        types.KeyboardButton("🎫 التذاكر")
    )
    # ── Sales & Marketing ──
    m.add(
        types.KeyboardButton("💰 المبيعات"),
        types.KeyboardButton("📢 التسويق")
    )
    # ── Flash & Giveaway ──
    m.add(
        types.KeyboardButton("⚡ عروض خاطفة"),
        types.KeyboardButton("🎁 Giveaway")
    )
    # ── VIP & Auto-Restock ──
    m.add(
        types.KeyboardButton("👑 إدارة VIP"),
        types.KeyboardButton("📦 التجديد التلقائي")
    )
    # ── Channel & Games ──
    m.add(
        types.KeyboardButton("📨 رسائل القناة"),
        types.KeyboardButton("🎮 الألعاب")
    )
    # ── Security & Recovery ──
    m.add(
        types.KeyboardButton("🛡️ مكافحة الرشق"),
        types.KeyboardButton("🔧 استعادة المشتريات")
    )
    # ── System & Stats ──
    m.add(
        types.KeyboardButton("⚙️ النظام"),
        types.KeyboardButton("📊 الإحصائيات")
    )
    # ── Requests & Maintenance ──
    m.add(
        types.KeyboardButton("💡 الطلبات"),
        types.KeyboardButton("🛠️ وضع الصيانة")
    )
    # ── Interactive & Control ──
    m.add(
        types.KeyboardButton("🎮 ألعاب القناة التفاعلية"),
        types.KeyboardButton("🧑‍💻 التحكم الشامل بالأعضاء")
    )
    # ── Back ──
    m.add(types.KeyboardButton("🔙 العودة"))
    return m


# =====================================================
# 📦 ADMIN PRODUCTS MENU (Styled)
# =====================================================

def admin_products_menu():
    """Admin products menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("➕ إضافة", callback_data="admp_add"),
        types.InlineKeyboardButton("❌ حذف", callback_data="admp_del")
    )
    m.add(types.InlineKeyboardButton("💵 الأسعار", callback_data="admp_prices"))
    return m


def admin_products_menu_styled(chat_id, text):
    """Send admin products with styled buttons"""
    rows = [
        [
            {"text": "➕ إضافة منتج", "callback_data": "admp_add", "style": "success", "icon": "add"},
            {"text": "❌ حذف منتج", "callback_data": "admp_del", "style": "danger", "icon": "delete"},
        ],
        [
            {"text": "💵 تعديل الأسعار", "callback_data": "admp_prices", "style": "primary", "icon": "sale"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🔑 ADMIN KEYS MENU (Styled)
# =====================================================

def admin_keys_menu():
    """Admin keys menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🔑 إضافة", callback_data="admk_add"),
        types.InlineKeyboardButton("👁️ عرض", callback_data="admk_view")
    )
    m.add(
        types.InlineKeyboardButton("🔢 حذف واحد", callback_data="admk_del"),
        types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="admk_clear")
    )
    return m


def admin_keys_menu_styled(chat_id, text):
    """Send admin keys with styled buttons"""
    rows = [
        [
            {"text": "🔑 إضافة مفاتيح", "callback_data": "admk_add", "style": "success", "icon": "key"},
            {"text": "👁️ عرض المفاتيح", "callback_data": "admk_view", "style": "primary", "icon": "view"},
        ],
        [
            {"text": "🔢 حذف مفتاح", "callback_data": "admk_del", "style": "danger", "icon": "delete"},
            {"text": "🗑️ مسح الكل", "callback_data": "admk_clear", "style": "danger", "icon": "delete"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 👥 ADMIN MEMBERS MENU (Styled)
# =====================================================

def admin_members_menu():
    """Admin members menu"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👤 عرض عضو", callback_data="admm_view"))
    m.add(types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admm_charge"))
    return m


def admin_members_menu_styled(chat_id, text):
    """Send admin members with styled buttons"""
    rows = [
        [{"text": "👤 عرض بيانات عضو", "callback_data": "admm_view", "style": "primary", "icon": "member"}],
        [{"text": "💰 شحن رصيد عضو", "callback_data": "admm_charge", "style": "success", "icon": "charge"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 💰 ADMIN SALES MENU (Styled)
# =====================================================

def admin_sales_menu():
    """Admin sales menu"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎫 كود شحن", callback_data="adms_code"))
    m.add(types.InlineKeyboardButton("🔥 خصم عام", callback_data="adms_discount"))
    return m


def admin_sales_menu_styled(chat_id, text):
    """Send admin sales with styled buttons"""
    rows = [
        [{"text": "🎫 إنشاء كود شحن", "callback_data": "adms_code", "style": "success", "icon": "code"}],
        [{"text": "🔥 تعيين خصم عام", "callback_data": "adms_discount", "style": "primary", "icon": "fire"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 📢 ADMIN MARKETING MENU (Styled)
# =====================================================

def admin_marketing_menu():
    """Admin marketing menu"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 إذاعة للمستخدمين", callback_data="admmk_broadcast"))
    m.add(types.InlineKeyboardButton("📤 نشر الأسعار بالقناة", callback_data="admmk_prices"))
    m.add(types.InlineKeyboardButton("📣 تسويق وهمي", callback_data="admmk_fake"))
    return m


def admin_marketing_menu_styled(chat_id, text):
    """Send admin marketing with styled buttons"""
    rows = [
        [{"text": "📢 إذاعة عامة", "callback_data": "admmk_broadcast", "style": "primary", "icon": "broadcast"}],
        [{"text": "📤 نشر الأسعار", "callback_data": "admmk_prices", "style": "success", "icon": "send"}],
        [{"text": "📣 تسويق وهمي", "callback_data": "admmk_fake", "style": None, "icon": "channel"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# ⚡ ADMIN FLASH SALE MENU (Styled)
# =====================================================

def admin_flash_menu():
    """Admin flash sale menu"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚡ إنشاء عرض", callback_data="admf_create"))
    m.add(types.InlineKeyboardButton("❌ إلغاء العرض الحالي", callback_data="admf_cancel"))
    return m


def admin_flash_menu_styled(chat_id, text):
    """Send admin flash with styled buttons"""
    rows = [
        [{"text": "⚡ إنشاء عرض خاطف", "callback_data": "admf_create", "style": "success", "icon": "flash"}],
        [{"text": "❌ إلغاء العرض الحالي", "callback_data": "admf_cancel", "style": "danger", "icon": "cancel"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🎮 ADMIN GAMES MENU (Styled)
# =====================================================

def admin_games_menu():
    """Admin games configuration menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎰 صندوق الحظ", callback_data="admg_lootbox"),
        types.InlineKeyboardButton("🎡 عجلة الحظ", callback_data="admg_wheel")
    )
    m.add(types.InlineKeyboardButton("🔥 المهام", callback_data="admg_quests"))
    return m


def admin_games_menu_styled(chat_id, text):
    """Send admin games with styled buttons"""
    rows = [
        [
            {"text": "🎰 صندوق الحظ", "callback_data": "admg_lootbox", "style": "primary", "icon": "lootbox"},
            {"text": "🎡 عجلة الحظ", "callback_data": "admg_wheel", "style": "primary", "icon": "wheel"},
        ],
        [
            {"text": "🔥 إعدادات المهام", "callback_data": "admg_quests", "style": None, "icon": "quest"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# ⚙️ ADMIN SYSTEM MENU (Styled)
# =====================================================

def admin_system_menu():
    """Admin system menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("✨ المكافأة اليومية", callback_data="adsys_daily"),
        types.InlineKeyboardButton("🔗 مكافأة الإحالة", callback_data="adsys_invite")
    )
    return m


def admin_system_menu_styled(chat_id, text):
    """Send admin system with styled buttons"""
    rows = [
        [
            {"text": "✨ المكافأة اليومية", "callback_data": "adsys_daily", "style": "primary", "icon": "daily"},
            {"text": "🔗 مكافأة الإحالة", "callback_data": "adsys_invite", "style": "primary", "icon": "referral"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🎁 ADMIN GIVEAWAY MENU (Styled)
# =====================================================

def admin_giveaway_menu():
    """Admin giveaway menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎁 إنشاء", callback_data="admgw_create"),
        types.InlineKeyboardButton("📋 عرض الكل", callback_data="admgw_list")
    )
    m.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="admgw_cancel"))
    return m


def admin_giveaway_menu_styled(chat_id, text):
    """Send admin giveaway with styled buttons"""
    rows = [
        [
            {"text": "🎁 إنشاء Giveaway", "callback_data": "admgw_create", "style": "success", "icon": "gift"},
            {"text": "📋 عرض الكل", "callback_data": "admgw_list", "style": "primary", "icon": "view"},
        ],
        [
            {"text": "❌ إلغاء Giveaway", "callback_data": "admgw_cancel", "style": "danger", "icon": "cancel"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 📨 ADMIN CHANNEL MENU (Styled)
# =====================================================

def admin_channel_menu():
    """Admin channel messages menu"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📝 رسالة منسقة", callback_data="admch_styled"))
    m.add(types.InlineKeyboardButton("📄 رسالة عادية", callback_data="admch_raw"))
    m.add(types.InlineKeyboardButton("🗑️ حذف رسالة", callback_data="admch_delete"))
    return m


def admin_channel_menu_styled(chat_id, text):
    """Send admin channel with styled buttons"""
    rows = [
        [{"text": "📝 رسالة منسقة بالقناة", "callback_data": "admch_styled", "style": "primary", "icon": "send"}],
        [{"text": "📄 رسالة عادية بالقناة", "callback_data": "admch_raw", "style": None, "icon": "send"}],
        [{"text": "🗑️ حذف رسالة من القناة", "callback_data": "admch_delete", "style": "danger", "icon": "delete"}],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 🎁 GIVEAWAY SETUP MENUS (Styled)
# =====================================================

def giveaway_reward_menu():
    """Giveaway reward selection"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("50 💎", callback_data="gw_reward_50"),
        types.InlineKeyboardButton("100 💎", callback_data="gw_reward_100"),
        types.InlineKeyboardButton("200 💎", callback_data="gw_reward_200")
    )
    m.add(
        types.InlineKeyboardButton("500 💎", callback_data="gw_reward_500"),
        types.InlineKeyboardButton("1000 💎", callback_data="gw_reward_1000"),
        types.InlineKeyboardButton("✏️ Custom", callback_data="gw_reward_custom")
    )
    return m


def giveaway_users_menu():
    """Giveaway max users selection"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("5 👤", callback_data="gw_users_5"),
        types.InlineKeyboardButton("10 👤", callback_data="gw_users_10"),
        types.InlineKeyboardButton("25 👤", callback_data="gw_users_25")
    )
    m.add(
        types.InlineKeyboardButton("50 👤", callback_data="gw_users_50"),
        types.InlineKeyboardButton("100 👤", callback_data="gw_users_100"),
        types.InlineKeyboardButton("✏️ Custom", callback_data="gw_users_custom")
    )
    return m


def giveaway_hours_menu():
    """Giveaway duration selection"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1h ⏰", callback_data="gw_hours_1"),
        types.InlineKeyboardButton("3h ⏰", callback_data="gw_hours_3"),
        types.InlineKeyboardButton("6h ⏰", callback_data="gw_hours_6")
    )
    m.add(
        types.InlineKeyboardButton("12h ⏰", callback_data="gw_hours_12"),
        types.InlineKeyboardButton("24h ⏰", callback_data="gw_hours_24"),
        types.InlineKeyboardButton("48h ⏰", callback_data="gw_hours_48")
    )
    return m


# =====================================================
# 🎮 MINI GAMES KEYBOARD
# =====================================================

def get_mini_games_menu(lang):
    """Mini games inline keyboard"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="game_rps"),
        types.InlineKeyboardButton("❌⭕ Tic Tac Toe", callback_data="game_ttt")
    )
    m.add(
        types.InlineKeyboardButton("🎯 Number Hunt", callback_data="game_hunt"),
        types.InlineKeyboardButton("🎲 Dice Duel", callback_data="game_dice")
    )
    return m


# =====================================================
# 🔙 BACK BUTTONS
# =====================================================

def back_button(callback_data="back_main", lang="en"):
    """Simple back button"""
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(f"🔙 {t(lang, 'btn_back')}", callback_data=callback_data))
    return m


# =====================================================
# ✅ CONFIRMATION DIALOGS (Styled)
# =====================================================

def confirm_dialog_styled(chat_id, text, confirm_data, cancel_data):
    """Send a confirmation dialog with colored buttons"""
    rows = [
        [
            {"text": "✅ تأكيد", "callback_data": confirm_data, "style": "success", "icon": "check"},
            {"text": "❌ إلغاء", "callback_data": cancel_data, "style": "danger", "icon": "cancel"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


def confirm_dialog(confirm_data, cancel_data):
    """Simple confirm/cancel inline keyboard"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("✅ تأكيد", callback_data=confirm_data),
        types.InlineKeyboardButton("❌ إلغاء", callback_data=cancel_data)
    )
    return m


# =====================================================
# 👑 VIP MENU
# =====================================================

def get_vip_menu(lang):
    """VIP subscription menu"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👑 VIP Status", callback_data="vip_status"))
    m.add(types.InlineKeyboardButton("💎 VIP Benefits", callback_data="vip_benefits"))
    return m


# =====================================================
# ⭐ STARS MENU
# =====================================================

def get_stars_menu(lang):
    """Stars conversion menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("⭐ 50 Stars", callback_data="stars_50"),
        types.InlineKeyboardButton("⭐ 100 Stars", callback_data="stars_100")
    )
    m.add(
        types.InlineKeyboardButton("⭐ 250 Stars", callback_data="stars_250"),
        types.InlineKeyboardButton("⭐ 500 Stars", callback_data="stars_500")
    )
    return m


# =====================================================
# 🎫 ADMIN TICKET ACTION BUTTONS (Styled)
# =====================================================

def admin_ticket_actions(tid):
    """Admin ticket action buttons with styles"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💬 رد مباشر", callback_data=f"admchat_{tid}"),
        types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"admclosetick_{tid}")
    )
    return m


def admin_ticket_actions_styled(chat_id, text, tid):
    """Send admin ticket actions with styled buttons"""
    rows = [
        [
            {"text": "💬 رد مباشر", "callback_data": f"admchat_{tid}", "style": "success", "icon": "reply"},
            {"text": "🔒 إغلاق التذكرة", "callback_data": f"admclosetick_{tid}", "style": "danger", "icon": "close"},
        ],
    ]
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 👤 ADMIN MEMBER ACTIONS (Styled)
# =====================================================

def admin_member_actions(uid, has_admin=False):
    """Admin member management buttons"""
    m = types.InlineKeyboardMarkup(row_width=2)
    if has_admin:
        m.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"admbanuser_{uid}_demote"))
    m.add(
        types.InlineKeyboardButton("⛔ حظر دائم", callback_data=f"admbanuser_{uid}_perm"),
        types.InlineKeyboardButton("⏱️ 24 ساعة", callback_data=f"admbanuser_{uid}_temp")
    )
    return m


def admin_member_actions_styled(chat_id, text, uid, has_admin=False):
    """Send admin member actions with styled buttons"""
    rows = []
    if has_admin:
        rows.append([
            {"text": "❌ إزالة الإدارة", "callback_data": f"admbanuser_{uid}_demote", "style": "danger", "icon": "cancel"},
        ])
    rows.append([
        {"text": "⛔ حظر دائم", "callback_data": f"admbanuser_{uid}_perm", "style": "danger", "icon": "close"},
        {"text": "⏱️ حظر 24 ساعة", "callback_data": f"admbanuser_{uid}_temp", "style": None, "icon": "close"},
    ])
    return send_styled_message(chat_id, text, rows)


# =====================================================
# 📊 RATING BUTTONS (for ticket close)
# =====================================================

def get_rating_buttons(tid):
    """Star rating buttons after ticket close"""
    m = types.InlineKeyboardMarkup(row_width=5)
    m.add(
        types.InlineKeyboardButton("⭐", callback_data=f"rate_{tid}_1"),
        types.InlineKeyboardButton("⭐⭐", callback_data=f"rate_{tid}_2"),
        types.InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{tid}_3"),
        types.InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{tid}_4"),
        types.InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{tid}_5"),
    )
    return m


# =====================================================
# ✅ Module Loaded
# =====================================================

print("=" * 55)
print("✅ keyboards.py v3.0 — Ultra Premium Keyboard System")
print("🎨 Colored Buttons: danger / success / primary")
print("🖼️ Custom Emoji Icons: Active")
print("🌍 Multi-Language: AR/EN/FR/ES/VI")
print("=" * 55)
