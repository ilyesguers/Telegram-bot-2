from telebot import types
from config import LOCALES, CHANNEL_LINK, ADMIN_PRIMARY, ADMIN_SECONDARY, t, TICKET_CATEGORIES
from database import get_user

def get_lang_inline():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi")
    )
    return m

def get_join_inline(lang):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(t(lang, "join_channel"), url=CHANNEL_LINK))
    m.add(types.InlineKeyboardButton(t(lang, "check_btn"), callback_data="check_join"))
    return m

def get_main_keyboard(uid, lang):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton(t(lang, "btn_account")))
    m.add(types.KeyboardButton(t(lang, "btn_shop")), types.KeyboardButton(t(lang, "btn_rewards")))
    m.add(types.KeyboardButton(t(lang, "btn_entertainment")), types.KeyboardButton(t(lang, "btn_support")))
    m.add(types.KeyboardButton(t(lang, "btn_settings")))
    u = get_user(str(uid)) or {}
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
        m.add(types.KeyboardButton(t(lang, "btn_admin")))
    return m

def get_account_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_balance"), callback_data="menu_balance"),
        types.InlineKeyboardButton(t(lang, "btn_my_id"), callback_data="menu_myid")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_my_rank"), callback_data="menu_rank"),
        types.InlineKeyboardButton(t(lang, "btn_referral"), callback_data="menu_referral")
    )
    m.add(types.InlineKeyboardButton(t(lang, "btn_my_purchases"), callback_data="menu_purchases"))
    return m

def get_rewards_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_daily_bonus"), callback_data="menu_daily"),
        types.InlineKeyboardButton(t(lang, "btn_redeem_code"), callback_data="menu_redeem")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_quests"), callback_data="menu_quests"),
        types.InlineKeyboardButton(t(lang, "btn_flash_sale"), callback_data="menu_flash")
    )
    return m

def get_entertainment_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_lootbox"), callback_data="menu_lootbox"),
        types.InlineKeyboardButton(t(lang, "btn_wheel"), callback_data="menu_wheel")
    )
    return m

def get_support_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_new_ticket"), callback_data="menu_new_ticket"),
        types.InlineKeyboardButton(t(lang, "btn_my_tickets"), callback_data="menu_my_tickets")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_request_product"), callback_data="menu_request_product"),
        types.InlineKeyboardButton(t(lang, "btn_faq"), callback_data="menu_faq")
    )
    return m

def get_settings_menu(lang, u):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(t(lang, "btn_change_lang"), callback_data="menu_lang"))
    notif_icon = "🔔" if u.get("notifications_on", True) else "🔕"
    m.add(
        types.InlineKeyboardButton(f"{notif_icon} " + t(lang, "btn_notifications"), callback_data="menu_notif"),
        types.InlineKeyboardButton(t(lang, "btn_theme"), callback_data="menu_theme")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_privacy"), callback_data="menu_privacy"),
        types.InlineKeyboardButton(t(lang, "btn_about"), callback_data="menu_about")
    )
    return m

def get_ticket_categories(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_key, cat_names in TICKET_CATEGORIES.items():
        name = cat_names.get(lang, cat_names["en"])
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"tcat_{cat_key}"))
    m.add(*buttons)
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
    return m

def get_admin_keyboard():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("📦 المنتجات"), types.KeyboardButton("🔑 المفاتيح"))
    m.add(types.KeyboardButton("👥 الأعضاء"), types.KeyboardButton("🎫 التذاكر"))
    m.add(types.KeyboardButton("💰 المبيعات"), types.KeyboardButton("📢 التسويق"))
    m.add(types.KeyboardButton("⚡ عروض خاطفة"), types.KeyboardButton("🎮 الألعاب"))
    m.add(types.KeyboardButton("⚙️ النظام"), types.KeyboardButton("📊 الإحصائيات"))
    m.add(types.KeyboardButton("💡 الطلبات"), types.KeyboardButton("🔙 العودة"))
    return m

def admin_products_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("➕ إضافة", callback_data="admp_add"),
          types.InlineKeyboardButton("❌ حذف", callback_data="admp_del"))
    m.add(types.InlineKeyboardButton("💵 الأسعار", callback_data="admp_prices"))
    return m

def admin_keys_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🔑 إضافة", callback_data="admk_add"),
          types.InlineKeyboardButton("👁️ عرض", callback_data="admk_view"))
    m.add(types.InlineKeyboardButton("🔢 حذف واحد", callback_data="admk_del"),
          types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="admk_clear"))
    return m

def admin_members_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👤 عرض عضو", callback_data="admm_view"))
    m.add(types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admm_charge"))
    return m

def admin_sales_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎫 كود شحن", callback_data="adms_code"))
    m.add(types.InlineKeyboardButton("🔥 خصم عام", callback_data="adms_discount"))
    return m

def admin_marketing_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="admmk_broadcast"))
    m.add(types.InlineKeyboardButton("📤 نشر الأسعار", callback_data="admmk_prices"))
    m.add(types.InlineKeyboardButton("📣 تسويق وهمي", callback_data="admmk_fake"))
    return m

def admin_flash_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚡ إنشاء عرض", callback_data="admf_create"))
    m.add(types.InlineKeyboardButton("❌ إلغاء العرض الحالي", callback_data="admf_cancel"))
    return m

def admin_games_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎰 صندوق الحظ", callback_data="admg_lootbox"))
    m.add(types.InlineKeyboardButton("🎡 عجلة الحظ", callback_data="admg_wheel"))
    m.add(types.InlineKeyboardButton("🔥 المهام", callback_data="admg_quests"))
    return m

def admin_system_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✨ المكافأة اليومية", callback_data="adsys_daily"))
    m.add(types.InlineKeyboardButton("🔗 نقاط الإحالة", callback_data="adsys_invite"))
    return m
