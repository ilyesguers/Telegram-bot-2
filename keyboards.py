"""
=====================================================
 keyboards.py — Premium Keyboard System v3.0
=====================================================
 🎨 Beautiful emoji-decorated buttons
 ✨ Clean and organized menus
 🌍 Multi-language support
=====================================================
"""

from telebot import types
from config import LOCALES, CHANNEL_LINK, CHANNEL_ID, ADMIN_PRIMARY, ADMIN_SECONDARY, t, TICKET_CATEGORIES
from database import get_user


# =====================================================
# 🌐 LANGUAGE SELECTOR
# =====================================================

def get_lang_inline():
    """Language selection keyboard"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi")
    )
    return m


# =====================================================
# 📢 JOIN CHANNEL
# =====================================================

def get_join_inline(lang):
    """Join channel keyboard"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK))
    m.add(types.InlineKeyboardButton("✅ I've Joined — Verify", callback_data="check_join"))
    return m


# =====================================================
# 🏠 MAIN KEYBOARD
# =====================================================

def get_main_keyboard(uid, lang):
    """Main menu reply keyboard"""
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
# 👤 ACCOUNT MENU
# =====================================================

def get_account_menu(lang):
    """Account section menu"""
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


# =====================================================
# 🎁 REWARDS MENU
# =====================================================

def get_rewards_menu(lang):
    """Rewards section menu"""
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


# =====================================================
# 🎮 ENTERTAINMENT MENU
# =====================================================

def get_entertainment_menu(lang):
    """Entertainment section menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(f"🎰 {t(lang, 'btn_lootbox')}", callback_data="menu_lootbox"),
        types.InlineKeyboardButton(f"🎡 {t(lang, 'btn_wheel')}", callback_data="menu_wheel")
    )
    return m


# =====================================================
# 💬 SUPPORT MENU
# =====================================================

def get_support_menu(lang):
    """Support section menu"""
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


# =====================================================
# ⚙️ SETTINGS MENU
# =====================================================

def get_settings_menu(lang, u):
    """Settings section menu"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"🌐 {t(lang, 'btn_change_lang')}", callback_data="menu_lang"))
    notif_status = u.get("notifications_on", True)
    notif_text = "🔔 ON" if notif_status else "🔕 OFF"
    m.add(
        types.InlineKeyboardButton(f"🔔 Notif: {notif_text}", callback_data="menu_notif"),
        types.InlineKeyboardButton(f"🎨 {t(lang, 'btn_theme')}", callback_data="menu_theme")
    )
    m.add(
        types.InlineKeyboardButton(f"🔒 {t(lang, 'btn_privacy')}", callback_data="menu_privacy"),
        types.InlineKeyboardButton(f"ℹ️ {t(lang, 'btn_about')}", callback_data="menu_about")
    )
    m.add(types.InlineKeyboardButton(f"💻 {t(lang, 'btn_bot_dev')}", url="https://t.me/fkLJh00302"))
    return m


# =====================================================
# 🎫 TICKET CATEGORIES
# =====================================================

def get_ticket_categories(lang):
    """Ticket category selection"""
    m = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_key, cat_names in TICKET_CATEGORIES.items():
        name = cat_names.get(lang, cat_names["en"])
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"tcat_{cat_key}"))
    m.add(*buttons)
    m.add(types.InlineKeyboardButton(f"🔙 {t(lang, 'btn_back')}", callback_data="back_support"))
    return m


# =====================================================
# 👑 ADMIN KEYBOARD
# =====================================================

def get_admin_keyboard():
    """Admin panel reply keyboard"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(
        types.KeyboardButton("📦 المنتجات"),
        types.KeyboardButton("🔑 المفاتيح")
    )
    m.add(
        types.KeyboardButton("👥 الأعضاء"),
        types.KeyboardButton("🎫 التذاكر")
    )
    m.add(
        types.KeyboardButton("💰 المبيعات"),
        types.KeyboardButton("📢 التسويق")
    )
    m.add(
        types.KeyboardButton("⚡ عروض خاطفة"),
        types.KeyboardButton("🎁 Giveaway")
    )
    m.add(
        types.KeyboardButton("👑 إدارة VIP"),
        types.KeyboardButton("📦 التجديد التلقائي")
    )
    m.add(
        types.KeyboardButton("📨 رسائل القناة"),
        types.KeyboardButton("🎮 الألعاب")
    )
    m.add(
        types.KeyboardButton("🛡️ مكافحة الرشق"),
        types.KeyboardButton("🔧 استعادة المشتريات")
    )
    m.add(
        types.KeyboardButton("⚙️ النظام"),
        types.KeyboardButton("📊 الإحصائيات")
    )
    m.add(
        types.KeyboardButton("💡 الطلبات"),
        types.KeyboardButton("🛠️ وضع الصيانة")
    )
    m.add(
        types.KeyboardButton("🎮 ألعاب القناة التفاعلية"),
        types.KeyboardButton("🧑‍💻 التحكم الشامل بالأعضاء")
    )
    m.add(types.KeyboardButton("🔙 العودة"))
    return m


# =====================================================
# 📦 ADMIN PRODUCTS MENU
# =====================================================

def admin_products_menu():
    """Admin products management"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("➕ إضافة", callback_data="admp_add"),
        types.InlineKeyboardButton("❌ حذف", callback_data="admp_del")
    )
    m.add(types.InlineKeyboardButton("💵 الأسعار", callback_data="admp_prices"))
    return m


# =====================================================
# 🔑 ADMIN KEYS MENU
# =====================================================

def admin_keys_menu():
    """Admin keys management"""
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


# =====================================================
# 👥 ADMIN MEMBERS MENU
# =====================================================

def admin_members_menu():
    """Admin members management"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👤 عرض عضو", callback_data="admm_view"))
    m.add(types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admm_charge"))
    return m


# =====================================================
# 💰 ADMIN SALES MENU
# =====================================================

def admin_sales_menu():
    """Admin sales management"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎫 كود شحن", callback_data="adms_code"))
    m.add(types.InlineKeyboardButton("🔥 خصم عام", callback_data="adms_discount"))
    return m


# =====================================================
# 📢 ADMIN MARKETING MENU
# =====================================================

def admin_marketing_menu():
    """Admin marketing management"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 إذاعة للمستخدمين", callback_data="admmk_broadcast"))
    m.add(types.InlineKeyboardButton("📤 نشر الأسعار بالقناة", callback_data="admmk_prices"))
    m.add(types.InlineKeyboardButton("📣 تسويق وهمي", callback_data="admmk_fake"))
    return m


# =====================================================
# ⚡ ADMIN FLASH SALE MENU
# =====================================================

def admin_flash_menu():
    """Admin flash sale management"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚡ إنشاء عرض", callback_data="admf_create"))
    m.add(types.InlineKeyboardButton("❌ إلغاء العرض الحالي", callback_data="admf_cancel"))
    return m


# =====================================================
# 🎮 ADMIN GAMES MENU
# =====================================================

def admin_games_menu():
    """Admin games configuration"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎰 صندوق الحظ", callback_data="admg_lootbox"),
        types.InlineKeyboardButton("🎡 عجلة الحظ", callback_data="admg_wheel")
    )
    m.add(types.InlineKeyboardButton("🔥 المهام", callback_data="admg_quests"))
    return m


# =====================================================
# ⚙️ ADMIN SYSTEM MENU
# =====================================================

def admin_system_menu():
    """Admin system settings"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("✨ المكافأة اليومية", callback_data="adsys_daily"),
        types.InlineKeyboardButton("🔗 مكافأة الإحالة", callback_data="adsys_invite")
    )
    return m


# =====================================================
# 🎁 ADMIN GIVEAWAY MENU
# =====================================================

def admin_giveaway_menu():
    """Admin giveaway management"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🎁 إنشاء", callback_data="admgw_create"),
        types.InlineKeyboardButton("📋 عرض الكل", callback_data="admgw_list")
    )
    m.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="admgw_cancel"))
    return m


# =====================================================
# 📨 ADMIN CHANNEL MENU
# =====================================================

def admin_channel_menu():
    """Admin channel messages"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📝 رسالة منسقة", callback_data="admch_styled"))
    m.add(types.InlineKeyboardButton("📄 رسالة عادية", callback_data="admch_raw"))
    m.add(types.InlineKeyboardButton("🗑️ حذف رسالة", callback_data="admch_delete"))
    return m


# =====================================================
# 🎁 GIVEAWAY SETUP MENUS
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
# 🎮 MINI GAMES MENU
# =====================================================

def get_mini_games_menu(lang):
    """Mini games selection"""
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
# ✅ CONFIRMATION DIALOGS
# =====================================================

def confirm_dialog(confirm_data, cancel_data):
    """Confirm/Cancel dialog"""
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
    """VIP features menu"""
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
# 🎫 ADMIN TICKET ACTIONS
# =====================================================

def admin_ticket_actions(tid):
    """Admin ticket action buttons"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💬 رد مباشر", callback_data=f"admchat_{tid}"),
        types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"admclosetick_{tid}")
    )
    return m


# =====================================================
# 👤 ADMIN MEMBER ACTIONS
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


# =====================================================
# 📊 RATING BUTTONS
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
# ✅ MODULE LOADED
# =====================================================

print("=" * 55)
print("✅ keyboards.py v3.0 — Premium Keyboard System")
print("🎨 Beautiful Emoji Buttons: Active")
print("🌍 Multi-Language: AR/EN/FR/ES/VI")
print("=" * 55)
