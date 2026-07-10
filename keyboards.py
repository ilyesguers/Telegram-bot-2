from telebot import types
from config import LOCALES, CHANNEL_LINK, ADMIN_PRIMARY, ADMIN_SECONDARY, t
from database import get_user

# =====================================================
# 🌐 اختيار اللغة
# =====================================================
def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi")
    )
    return markup

# =====================================================
# 🔒 الاشتراك
# =====================================================
def get_join_inline(lang):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t(lang, "join_channel"), url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton(t(lang, "check_btn"), callback_data="check_join"))
    return markup

# =====================================================
# 🏠 القائمة الرئيسية (تصميم أنيق - 5 أزرار فقط)
# =====================================================
def get_main_keyboard(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add(types.KeyboardButton(t(lang, "btn_account")))
    markup.add(
        types.KeyboardButton(t(lang, "btn_shop")),
        types.KeyboardButton(t(lang, "btn_rewards"))
    )
    markup.add(
        types.KeyboardButton(t(lang, "btn_entertainment")),
        types.KeyboardButton(t(lang, "btn_support"))
    )
    markup.add(types.KeyboardButton(t(lang, "btn_settings")))
    
    u = get_user(str(uid)) or {}
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
        markup.add(types.KeyboardButton(t(lang, "btn_admin")))
    
    return markup

# =====================================================
# 👤 قائمة الحساب (Inline - جميلة!)
# =====================================================
def get_account_menu(lang):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t(lang, "btn_balance"), callback_data="menu_balance"),
        types.InlineKeyboardButton(t(lang, "btn_my_id"), callback_data="menu_myid")
    )
    markup.add(
        types.InlineKeyboardButton(t(lang, "btn_my_rank"), callback_data="menu_rank"),
        types.InlineKeyboardButton(t(lang, "btn_referral"), callback_data="menu_referral")
    )
    markup.add(types.InlineKeyboardButton(t(lang, "btn_my_purchases"), callback_data="menu_purchases"))
    return markup

# =====================================================
# 🎁 قائمة المكافآت
# =====================================================
def get_rewards_menu(lang):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t(lang, "btn_daily_bonus"), callback_data="menu_daily"))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_redeem_code"), callback_data="menu_redeem"))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_quests"), callback_data="menu_quests"))
    return markup

# =====================================================
# 🎮 قائمة الترفيه
# =====================================================
def get_entertainment_menu(lang):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t(lang, "btn_lootbox"), callback_data="menu_lootbox"),
        types.InlineKeyboardButton(t(lang, "btn_wheel"), callback_data="menu_wheel")
    )
    return markup

# =====================================================
# 💬 قائمة الدعم
# =====================================================
def get_support_menu(lang):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t(lang, "btn_open_ticket"), callback_data="menu_open_ticket"))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_my_tickets"), callback_data="menu_my_tickets"))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_request_product"), callback_data="menu_request_product"))
    return markup

# =====================================================
# ⚙️ قائمة الإعدادات
# =====================================================
def get_settings_menu(lang):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t(lang, "btn_change_lang"), callback_data="menu_lang"))
    return markup

# =====================================================
# 👑 لوحة الإدارة (تصميم مصنّف)
# =====================================================
def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📦 إدارة المنتجات"),
        types.KeyboardButton("🔑 إدارة المفاتيح")
    )
    markup.add(
        types.KeyboardButton("👥 إدارة الأعضاء"),
        types.KeyboardButton("🎫 إدارة التذاكر")
    )
    markup.add(
        types.KeyboardButton("💰 المبيعات والأكواد"),
        types.KeyboardButton("📢 التسويق والإذاعة")
    )
    markup.add(
        types.KeyboardButton("🎮 إعدادات الألعاب"),
        types.KeyboardButton("⚙️ إعدادات النظام")
    )
    markup.add(
        types.KeyboardButton("📊 الإحصائيات"),
        types.KeyboardButton("💡 طلبات المنتجات")
    )
    markup.add(types.KeyboardButton("🔙 العودة للمستخدم"))
    return markup

# ---- قوائم الإدارة الفرعية Inline ----
def admin_products_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("➕ إضافة منتج", callback_data="admp_add"),
        types.InlineKeyboardButton("❌ حذف منتج", callback_data="admp_del")
    )
    m.add(types.InlineKeyboardButton("💵 إدارة الأسعار", callback_data="admp_prices"))
    return m

def admin_keys_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🔑 إضافة مفاتيح", callback_data="admk_add"),
        types.InlineKeyboardButton("👁️ استعراض", callback_data="admk_view")
    )
    m.add(
        types.InlineKeyboardButton("🔢 حذف مفتاح", callback_data="admk_del"),
        types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="admk_clear")
    )
    return m

def admin_members_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👤 عرض عضو", callback_data="admm_view"))
    m.add(types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admm_charge"))
    return m

def admin_sales_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎫 إنشاء كود شحن", callback_data="adms_code"))
    m.add(types.InlineKeyboardButton("🔥 تفعيل خصم عام", callback_data="adms_discount"))
    return m

def admin_marketing_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 إذاعة شاملة", callback_data="admmk_broadcast"))
    m.add(types.InlineKeyboardButton("📤 نشر الأسعار", callback_data="admmk_prices"))
    m.add(types.InlineKeyboardButton("📣 تسويق وهمي", callback_data="admmk_fake"))
    return m

def admin_games_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎰 إعدادات صندوق الحظ", callback_data="admg_lootbox"))
    m.add(types.InlineKeyboardButton("🎡 إعدادات عجلة الحظ", callback_data="admg_wheel"))
    m.add(types.InlineKeyboardButton("🔥 إعدادات المهام", callback_data="admg_quests"))
    return m

def admin_system_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✨ المكافأة اليومية", callback_data="adsys_daily"))
    m.add(types.InlineKeyboardButton("🔗 نقاط الإحالة", callback_data="adsys_invite"))
    return m
