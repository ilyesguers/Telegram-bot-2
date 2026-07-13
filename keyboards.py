"""
══════════════════════════════════════════════════════════════════════════════
║                    keyboards.py - COMPLETE KEYBOARDS v3.0                   ║
║            🎹 جميع الكيبوردات + 5 لغات كاملة (ar/en/fr/es/vi)              ║
══════════════════════════════════════════════════════════════════════════════
║  Developer: @fkLJh00302                                                     ║
║  Includes:                                                                   ║
║   ✅ كيبوردات المستخدم (الرئيسية، الحساب، المتجر، المكافآت، الترفيه...)     ║
║   ✅ كيبوردات الأدمن (المنتجات، المفاتيح، الأعضاء، التذاكر...)              ║
║   ✅ كيبوردات Giveaway + رسائل القناة + الألعاب                              ║
║   ✅ كيبوردات VIP + Stars + الحماية                                          ║
║   ✅ 5 لغات كاملة: العربية، الإنجليزية، الفرنسية، الإسبانية، الفيتنامية     ║
══════════════════════════════════════════════════════════════════════════════
"""

from telebot import types
from config import LOCALES, CHANNEL_LINK, CHANNEL_ID, ADMIN_PRIMARY, ADMIN_SECONDARY, t, TICKET_CATEGORIES
from database import get_user

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 كيبورد اختيار اللغة
# ═══════════════════════════════════════════════════════════════════════════

def get_lang_inline():
    """كيبورد اختيار اللغة"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi")
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📢 كيبورد الانضمام للقناة
# ═══════════════════════════════════════════════════════════════════════════

def get_join_inline(lang):
    """كيبورد الانضمام للقناة"""
    # نصوص حسب اللغة
    join_texts = {
        "ar": ("📢 اشترك في القناة", "✅ تحققت - تحقق"),
        "en": ("📢 Join Our Channel", "✅ I've Joined - Verify"),
        "fr": ("📢 Rejoindre la chaîne", "✅ Rejoint - Vérifier"),
        "es": ("📢 Únete al Canal", "✅ Me uní - Verificar"),
        "vi": ("📢 Tham gia Kênh", "✅ Đã tham gia - Xác minh")
    }
    
    join_txt, verify_txt = join_texts.get(lang, join_texts["en"])
    
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(join_txt, url=CHANNEL_LINK))
    m.add(types.InlineKeyboardButton(verify_txt, callback_data="check_join"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🏠 الكيبورد الرئيسي للمستخدم
# ═══════════════════════════════════════════════════════════════════════════

def get_main_keyboard(uid, lang):
    """الكيبورد الرئيسي مع كل اللغات"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # الصف 1: الحساب
    m.add(types.KeyboardButton(t(lang, "btn_account")))
    
    # الصف 2: المتجر والمكافآت
    m.add(
        types.KeyboardButton(t(lang, "btn_shop")),
        types.KeyboardButton(t(lang, "btn_rewards"))
    )
    
    # الصف 3: الترفيه والدعم
    m.add(
        types.KeyboardButton(t(lang, "btn_entertainment")),
        types.KeyboardButton(t(lang, "btn_support"))
    )
    
    # الصف 4: VIP و Stars
    vip_texts = {
        "ar": "👑 VIP", "en": "👑 VIP", "fr": "👑 VIP",
        "es": "👑 VIP", "vi": "👑 VIP"
    }
    stars_texts = {
        "ar": "⭐ Stars", "en": "⭐ Stars", "fr": "⭐ Stars",
        "es": "⭐ Stars", "vi": "⭐ Stars"
    }
    m.add(
        types.KeyboardButton(vip_texts.get(lang, "👑 VIP")),
        types.KeyboardButton(stars_texts.get(lang, "⭐ Stars"))
    )
    
    # الصف 5: Mini Games
    games_texts = {
        "ar": "🎮 Mini Games",
        "en": "🎮 Mini Games",
        "fr": "🎮 Mini Jeux",
        "es": "🎮 Mini Juegos",
        "vi": "🎮 Mini Games"
    }
    m.add(types.KeyboardButton(games_texts.get(lang, "🎮 Mini Games")))
    
    # الصف 6: الإعدادات
    m.add(types.KeyboardButton(t(lang, "btn_settings")))
    
    # الصف 7: الأدمن (إذا كان مشرف)
    u = get_user(str(uid)) or {}
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
        m.add(types.KeyboardButton(t(lang, "btn_admin")))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 👤 قائمة الحساب
# ═══════════════════════════════════════════════════════════════════════════

def get_account_menu(lang):
    """كيبورد الحساب"""
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

# ═══════════════════════════════════════════════════════════════════════════
# 🎁 قائمة المكافآت
# ═══════════════════════════════════════════════════════════════════════════

def get_rewards_menu(lang):
    """كيبورد المكافآت"""
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

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 قائمة الترفيه
# ═══════════════════════════════════════════════════════════════════════════

def get_entertainment_menu(lang):
    """كيبورد الترفيه"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_lootbox"), callback_data="menu_lootbox"),
        types.InlineKeyboardButton(t(lang, "btn_wheel"), callback_data="menu_wheel")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_leaderboard"), callback_data="menu_leaderboard")
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 💬 قائمة الدعم
# ═══════════════════════════════════════════════════════════════════════════

def get_support_menu(lang):
    """كيبورد الدعم"""
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

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ قائمة الإعدادات
# ═══════════════════════════════════════════════════════════════════════════

def get_settings_menu(lang, u):
    """كيبورد الإعدادات"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    m.add(types.InlineKeyboardButton(t(lang, "btn_change_lang"), callback_data="menu_lang"))
    
    notif_status = u.get("notifications_on", True)
    if lang == "ar":
        notif_text = "🔔 الإشعارات: مفعّلة" if notif_status else "🔕 الإشعارات: معطّلة"
    elif lang == "fr":
        notif_text = "🔔 Notifications: ON" if notif_status else "🔕 Notifications: OFF"
    elif lang == "es":
        notif_text = "🔔 Notificaciones: ON" if notif_status else "🔕 Notificaciones: OFF"
    elif lang == "vi":
        notif_text = "🔔 Thông báo: BẬT" if notif_status else "🔕 Thông báo: TẮT"
    else:
        notif_text = "🔔 Notifications: ON" if notif_status else "🔕 Notifications: OFF"
    
    m.add(
        types.InlineKeyboardButton(notif_text, callback_data="menu_notif"),
        types.InlineKeyboardButton(t(lang, "btn_theme"), callback_data="menu_theme")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_privacy"), callback_data="menu_privacy"),
        types.InlineKeyboardButton(t(lang, "btn_about"), callback_data="menu_about")
    )
    m.add(types.InlineKeyboardButton("💻 " + t(lang, "btn_bot_dev"), url="https://t.me/fkLJh00302"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎫 قائمة أنواع التذاكر
# ═══════════════════════════════════════════════════════════════════════════

def get_ticket_categories(lang):
    """كيبورد أنواع التذاكر"""
    m = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_key, cat_names in TICKET_CATEGORIES.items():
        name = cat_names.get(lang, cat_names.get("en", cat_key))
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"tcat_{cat_key}"))
    m.add(*buttons)
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#                        🔴 كيبوردات الأدمن
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 👑 الكيبورد الرئيسي للأدمن
# ═══════════════════════════════════════════════════════════════════════════

def get_admin_keyboard():
    """الكيبورد الرئيسي للأدمن"""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # الصف 1: المنتجات والمفاتيح
    m.add(
        types.KeyboardButton("📦 المنتجات"),
        types.KeyboardButton("🔑 المفاتيح")
    )
    
    # الصف 2: الأعضاء والتذاكر
    m.add(
        types.KeyboardButton("👥 الأعضاء"),
        types.KeyboardButton("🎫 التذاكر")
    )
    
    # الصف 3: المبيعات والتسويق
    m.add(
        types.KeyboardButton("💰 المبيعات"),
        types.KeyboardButton("📢 التسويق")
    )
    
    # الصف 4: العروض و Giveaway
    m.add(
        types.KeyboardButton("⚡ عروض خاطفة"),
        types.KeyboardButton("🎁 Giveaway")
    )
    
    # الصف 5: VIP والتجديد التلقائي
    m.add(
        types.KeyboardButton("👑 إدارة VIP"),
        types.KeyboardButton("📦 التجديد التلقائي")
    )
    
    # الصف 6: رسائل القناة والألعاب
    m.add(
        types.KeyboardButton("📨 رسائل القناة"),
        types.KeyboardButton("🎮 الألعاب")
    )
    
    # الصف 7: الحماية والاستعادة
    m.add(
        types.KeyboardButton("🛡️ مكافحة الرشق"),
        types.KeyboardButton("🔧 استعادة المشتريات")
    )
    
    # الصف 8: النظام والإحصائيات
    m.add(
        types.KeyboardButton("⚙️ النظام"),
        types.KeyboardButton("📊 الإحصائيات")
    )
    
    # الصف 9: الطلبات والصيانة
    m.add(
        types.KeyboardButton("💡 الطلبات"),
        types.KeyboardButton("🛠️ وضع الصيانة")
    )
    
    # الصف 10: العودة
    m.add(types.KeyboardButton("🔙 العودة"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📦 قائمة إدارة المنتجات
# ═══════════════════════════════════════════════════════════════════════════

def admin_products_menu():
    """كيبورد إدارة المنتجات"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("➕ إضافة", callback_data="admp_add"),
        types.InlineKeyboardButton("❌ حذف", callback_data="admp_del")
    )
    m.add(types.InlineKeyboardButton("💵 الأسعار", callback_data="admp_prices"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🔑 قائمة إدارة المفاتيح
# ═══════════════════════════════════════════════════════════════════════════

def admin_keys_menu():
    """كيبورد إدارة المفاتيح"""
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

# ═══════════════════════════════════════════════════════════════════════════
# 👥 قائمة إدارة الأعضاء
# ═══════════════════════════════════════════════════════════════════════════

def admin_members_menu():
    """كيبورد إدارة الأعضاء"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👤 عرض عضو", callback_data="admm_view"))
    m.add(types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admm_charge"))
    m.add(types.InlineKeyboardButton("🔍 بحث عن عضو", callback_data="admm_search"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 💰 قائمة المبيعات
# ═══════════════════════════════════════════════════════════════════════════

def admin_sales_menu():
    """كيبورد المبيعات"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎫 كود شحن", callback_data="adms_code"))
    m.add(types.InlineKeyboardButton("🔥 خصم عام", callback_data="adms_discount"))
    m.add(types.InlineKeyboardButton("📜 سجل المبيعات", callback_data="adms_log"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📢 قائمة التسويق
# ═══════════════════════════════════════════════════════════════════════════

def admin_marketing_menu():
    """كيبورد التسويق"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 إذاعة للمستخدمين", callback_data="admmk_broadcast"))
    m.add(types.InlineKeyboardButton("📤 نشر الأسعار بالقناة", callback_data="admmk_prices"))
    m.add(types.InlineKeyboardButton("📣 تسويق وهمي", callback_data="admmk_fake"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ⚡ قائمة العروض الخاطفة
# ═══════════════════════════════════════════════════════════════════════════

def admin_flash_menu():
    """كيبورد العروض الخاطفة"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚡ إنشاء عرض", callback_data="admf_create"))
    m.add(types.InlineKeyboardButton("❌ إلغاء العرض الحالي", callback_data="admf_cancel"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎁 قائمة Giveaway
# ═══════════════════════════════════════════════════════════════════════════

def admin_giveaway_menu():
    """كيبورد Giveaway"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("➕ إنشاء Giveaway جديد", callback_data="admgw_create"))
    m.add(types.InlineKeyboardButton("📋 عرض النشطة", callback_data="admgw_list"))
    m.add(types.InlineKeyboardButton("❌ إلغاء Giveaway", callback_data="admgw_cancel"))
    m.add(types.InlineKeyboardButton("📊 إحصائيات Giveaway", callback_data="admgw_stats"))
    return m

def giveaway_reward_menu():
    """كيبورد اختيار مكافأة Giveaway"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("10 💎", callback_data="gwrew_10"),
        types.InlineKeyboardButton("25 💎", callback_data="gwrew_25"),
        types.InlineKeyboardButton("50 💎", callback_data="gwrew_50")
    )
    m.add(
        types.InlineKeyboardButton("100 💎", callback_data="gwrew_100"),
        types.InlineKeyboardButton("250 💎", callback_data="gwrew_250"),
        types.InlineKeyboardButton("500 💎", callback_data="gwrew_500")
    )
    m.add(types.InlineKeyboardButton("✏️ مخصص", callback_data="gwrew_custom"))
    return m

def giveaway_users_menu():
    """كيبورد اختيار عدد الفائزين"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("5 👥", callback_data="gwusr_5"),
        types.InlineKeyboardButton("10 👥", callback_data="gwusr_10"),
        types.InlineKeyboardButton("25 👥", callback_data="gwusr_25")
    )
    m.add(
        types.InlineKeyboardButton("50 👥", callback_data="gwusr_50"),
        types.InlineKeyboardButton("100 👥", callback_data="gwusr_100"),
        types.InlineKeyboardButton("∞ 👥", callback_data="gwusr_99999")
    )
    m.add(types.InlineKeyboardButton("✏️ مخصص", callback_data="gwusr_custom"))
    return m

def giveaway_hours_menu():
    """كيبورد اختيار مدة Giveaway"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1 ساعة", callback_data="gwhr_1"),
        types.InlineKeyboardButton("3 ساعات", callback_data="gwhr_3"),
        types.InlineKeyboardButton("6 ساعات", callback_data="gwhr_6")
    )
    m.add(
        types.InlineKeyboardButton("12 ساعة", callback_data="gwhr_12"),
        types.InlineKeyboardButton("24 ساعة", callback_data="gwhr_24"),
        types.InlineKeyboardButton("48 ساعة", callback_data="gwhr_48")
    )
    m.add(types.InlineKeyboardButton("72 ساعة", callback_data="gwhr_72"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📨 قائمة رسائل القناة
# ═══════════════════════════════════════════════════════════════════════════

def admin_channel_menu():
    """كيبورد رسائل القناة"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📝 رسالة منسّقة", callback_data="admch_styled"))
    m.add(types.InlineKeyboardButton("📄 رسالة خام (HTML)", callback_data="admch_raw"))
    m.add(types.InlineKeyboardButton("🗑️ حذف رسالة", callback_data="admch_delete"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 قائمة إعدادات الألعاب
# ═══════════════════════════════════════════════════════════════════════════

def admin_games_menu():
    """كيبورد إعدادات الألعاب"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎰 صندوق الحظ", callback_data="admg_lootbox"))
    m.add(types.InlineKeyboardButton("🎡 عجلة الحظ", callback_data="admg_wheel"))
    m.add(types.InlineKeyboardButton("🔥 المهام", callback_data="admg_quests"))
    m.add(types.InlineKeyboardButton("🎮 إعدادات Mini Games", callback_data="admg_minigames"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ قائمة النظام
# ═══════════════════════════════════════════════════════════════════════════

def admin_system_menu():
    """كيبورد النظام"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✨ المكافأة اليومية", callback_data="adsys_daily"))
    m.add(types.InlineKeyboardButton("🔗 مكافأة الإحالة", callback_data="adsys_invite"))
    m.add(types.InlineKeyboardButton("🔄 إعادة تشغيل البوت", callback_data="adsys_restart"))
    m.add(types.InlineKeyboardButton("📊 حالة النظام", callback_data="adsys_status"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ قائمة الحماية (Shield)
# ═══════════════════════════════════════════════════════════════════════════

def admin_shield_menu():
    """كيبورد نظام الحماية"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🚫 المحظورين", callback_data="shield_bans"),
        types.InlineKeyboardButton("🔍 المشبوهين", callback_data="shield_suspicious")
    )
    m.add(
        types.InlineKeyboardButton("⚙️ إعدادات الحماية", callback_data="shield_settings"),
        types.InlineKeyboardButton("📜 السجلات", callback_data="shield_logs")
    )
    m.add(types.InlineKeyboardButton("📊 إحصائيات الحماية", callback_data="shield_stats"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 👑 قائمة VIP للأدمن
# ═══════════════════════════════════════════════════════════════════════════

def admin_vip_menu():
    """كيبورد إدارة VIP"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("💰 تغيير سعر VIP", callback_data="adm_vip_price"))
    m.add(types.InlineKeyboardButton("⭐ تغيير سعر Stars", callback_data="adm_vip_rate"))
    m.add(types.InlineKeyboardButton("👥 قائمة VIP", callback_data="adm_vip_list"))
    m.add(types.InlineKeyboardButton("👤 إدارة مستخدم", callback_data="adm_manage_user"))
    m.add(types.InlineKeyboardButton("➕ منح VIP", callback_data="adm_vip_grant"))
    m.add(types.InlineKeyboardButton("❌ سحب VIP", callback_data="adm_vip_revoke"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📦 قائمة التجديد التلقائي للأدمن
# ═══════════════════════════════════════════════════════════════════════════

def admin_restock_menu():
    """كيبورد التجديد التلقائي"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("➕ جدولة تجديد جديد", callback_data="adm_restock_new"))
    m.add(types.InlineKeyboardButton("📋 عرض المعلقة", callback_data="adm_restock_list"))
    m.add(types.InlineKeyboardButton("❌ إلغاء تجديد", callback_data="adm_restock_cancel"))
    m.add(types.InlineKeyboardButton("📜 سجل التجديد", callback_data="adm_restock_history"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#            🎨 كيبوردات إضافية متعددة اللغات
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 🛍️ كيبورد المتجر - اختيار المنتج
# ═══════════════════════════════════════════════════════════════════════════

def get_shop_products_inline(products, keys_store, lang):
    """كيبورد منتجات المتجر"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    for prod in products.keys():
        total_stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        status = "✅" if total_stock > 0 else "❌"
        m.add(types.InlineKeyboardButton(
            f"{status} 📦 {prod} ({total_stock})",
            callback_data=f"shop_{prod}"
        ))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ⏱️ كيبورد خطط المنتج
# ═══════════════════════════════════════════════════════════════════════════

def get_product_plans_inline(prod, plans, keys_store, user_points, rank_disc, global_disc, lang):
    """كيبورد خطط المنتج"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    plan_labels = {
        "ar": {"1 Day": "يوم واحد", "7 Days": "7 أيام", "30 Days": "30 يوم"},
        "en": {"1 Day": "1 Day", "7 Days": "7 Days", "30 Days": "30 Days"},
        "fr": {"1 Day": "1 Jour", "7 Days": "7 Jours", "30 Days": "30 Jours"},
        "es": {"1 Day": "1 Día", "7 Days": "7 Días", "30 Days": "30 Días"},
        "vi": {"1 Day": "1 Ngày", "7 Days": "7 Ngày", "30 Days": "30 Ngày"}
    }
    
    labels = plan_labels.get(lang, plan_labels["en"])
    
    for plan, base_price in plans.items():
        final_price = int(base_price * (1 - global_disc / 100) * (1 - rank_disc))
        stock = len(keys_store.get(prod, {}).get(plan, []))
        label = labels.get(plan, plan)
        
        if stock > 0:
            status = "✅" if user_points >= final_price else "💰"
            cb = f"buy_plan|{prod}|{plan}"
        else:
            status = "❌"
            cb = "shop_nostock"
        
        btn_text = f"{status} ⏱️ {label} → {final_price} 💎 ({stock})"
        m.add(types.InlineKeyboardButton(btn_text, callback_data=cb))
    
    back_texts = {
        "ar": "🔙 رجوع", "en": "🔙 Back", "fr": "🔙 Retour",
        "es": "🔙 Atrás", "vi": "🔙 Quay lại"
    }
    m.add(types.InlineKeyboardButton(back_texts.get(lang, "🔙 Back"), callback_data="shop_back"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ✅ كيبورد تأكيد الشراء
# ═══════════════════════════════════════════════════════════════════════════

def get_purchase_confirm_inline(prod, plan, price, lang):
    """كيبورد تأكيد الشراء"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    confirm_texts = {
        "ar": "✅ تأكيد الشراء", "en": "✅ Confirm Purchase",
        "fr": "✅ Confirmer l'achat", "es": "✅ Confirmar compra",
        "vi": "✅ Xác nhận mua"
    }
    cancel_texts = {
        "ar": "❌ إلغاء", "en": "❌ Cancel",
        "fr": "❌ Annuler", "es": "❌ Cancelar",
        "vi": "❌ Hủy"
    }
    
    m.add(
        types.InlineKeyboardButton(
            confirm_texts.get(lang, "✅ Confirm"),
            callback_data=f"buy_plan|{prod}|{plan}"
        ),
        types.InlineKeyboardButton(
            cancel_texts.get(lang, "❌ Cancel"),
            callback_data="shop_back"
        )
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🏆 كيبورد المتصدرين
# ═══════════════════════════════════════════════════════════════════════════

def get_leaderboard_inline(lang):
    """كيبورد المتصدرين"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    by_points = {
        "ar": "💎 بالنقاط", "en": "💎 By Points",
        "fr": "💎 Par Points", "es": "💎 Por Puntos",
        "vi": "💎 Theo Điểm"
    }
    by_invites = {
        "ar": "👥 بالدعوات", "en": "👥 By Invites",
        "fr": "👥 Par Invitations", "es": "👥 Por Invitaciones",
        "vi": "👥 Theo Lời mời"
    }
    by_purchases = {
        "ar": "🛒 بالمشتريات", "en": "🛒 By Purchases",
        "fr": "🛒 Par Achats", "es": "🛒 Por Compras",
        "vi": "🛒 Theo Mua hàng"
    }
    
    m.add(
        types.InlineKeyboardButton(by_points.get(lang, "💎 By Points"), callback_data="lb_points"),
        types.InlineKeyboardButton(by_invites.get(lang, "👥 By Invites"), callback_data="lb_invites")
    )
    m.add(
        types.InlineKeyboardButton(by_purchases.get(lang, "🛒 By Purchases"), callback_data="lb_purchases")
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🔥 كيبورد المهام
# ═══════════════════════════════════════════════════════════════════════════

def get_quests_inline(lang, completed_quests=None):
    """كيبورد المهام"""
    if completed_quests is None:
        completed_quests = []
    
    m = types.InlineKeyboardMarkup(row_width=1)
    
    claim_texts = {
        "ar": "🎁 استلام المكافأة", "en": "🎁 Claim Reward",
        "fr": "🎁 Réclamer", "es": "🎁 Reclamar",
        "vi": "🎁 Nhận thưởng"
    }
    
    quests = [
        ("invite", "👥"),
        ("buy", "🛒"),
        ("points", "💎")
    ]
    
    for quest_id, emoji in quests:
        if quest_id in completed_quests:
            m.add(types.InlineKeyboardButton(f"✅ {emoji} Completed!", callback_data=f"quest_done"))
        else:
            m.add(types.InlineKeyboardButton(
                f"{emoji} {claim_texts.get(lang, '🎁 Claim')}",
                callback_data=f"quest_claim_{quest_id}"
            ))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 👑 كيبورد VIP للمستخدم
# ═══════════════════════════════════════════════════════════════════════════

def get_vip_user_inline(is_vip, lang, price=100):
    """كيبورد VIP للمستخدم"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    if is_vip:
        stock_texts = {
            "ar": "📊 تفاصيل المخزون", "en": "📊 View Stock Details",
            "fr": "📊 Détails du Stock", "es": "📊 Detalles del Stock",
            "vi": "📊 Chi tiết Kho"
        }
        weekly_texts = {
            "ar": "🎫 كود أسبوعي مجاني", "en": "🎫 Get Weekly Code",
            "fr": "🎫 Code Hebdomadaire", "es": "🎫 Código Semanal",
            "vi": "🎫 Mã hàng tuần"
        }
        convert_texts = {
            "ar": "⭐ تحويل Stars", "en": "⭐ Convert Stars",
            "fr": "⭐ Convertir Stars", "es": "⭐ Convertir Stars",
            "vi": "⭐ Đổi Stars"
        }
        renew_texts = {
            "ar": "🔄 تجديد VIP", "en": "🔄 Renew VIP",
            "fr": "🔄 Renouveler VIP", "es": "🔄 Renovar VIP",
            "vi": "🔄 Gia hạn VIP"
        }
        
        m.add(types.InlineKeyboardButton(stock_texts.get(lang, stock_texts["en"]), callback_data="vip_stock"))
        m.add(types.InlineKeyboardButton(weekly_texts.get(lang, weekly_texts["en"]), callback_data="vip_weekly_code"))
        m.add(types.InlineKeyboardButton(convert_texts.get(lang, convert_texts["en"]), callback_data="vip_convert_stars"))
        m.add(types.InlineKeyboardButton(renew_texts.get(lang, renew_texts["en"]), callback_data="vip_buy"))
    else:
        subscribe_texts = {
            "ar": f"👑 اشتراك ({price} ⭐)", "en": f"👑 Subscribe ({price} ⭐)",
            "fr": f"👑 S'abonner ({price} ⭐)", "es": f"👑 Suscribirse ({price} ⭐)",
            "vi": f"👑 Đăng ký ({price} ⭐)"
        }
        convert_texts = {
            "ar": "⭐ تحويل Stars إلى نقاط", "en": "⭐ Convert Stars to Points",
            "fr": "⭐ Convertir Stars en Points", "es": "⭐ Convertir Stars a Puntos",
            "vi": "⭐ Đổi Stars thành Điểm"
        }
        
        m.add(types.InlineKeyboardButton(subscribe_texts.get(lang, subscribe_texts["en"]), callback_data="vip_buy"))
        m.add(types.InlineKeyboardButton(convert_texts.get(lang, convert_texts["en"]), callback_data="vip_convert_stars"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ كيبورد Stars
# ═══════════════════════════════════════════════════════════════════════════

def get_stars_inline(rate, lang):
    """كيبورد تحويل Stars"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    for stars in [1, 5, 10, 25, 50, 100]:
        points = stars * rate
        m.add(types.InlineKeyboardButton(
            f"⭐ {stars} = {points} 💎",
            callback_data=f"star_buy_{stars}"
        ))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 كيبورد Mini Games
# ═══════════════════════════════════════════════════════════════════════════

def get_games_inline(lang):
    """كيبورد الألعاب المصغرة"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    rps_texts = {
        "ar": "✂️ حجرة ورقة مقص", "en": "✂️ Rock Paper Scissors",
        "fr": "✂️ Pierre Papier Ciseaux", "es": "✂️ Piedra Papel Tijeras",
        "vi": "✂️ Kéo Búa Bao"
    }
    ttt_texts = {
        "ar": "⭕ X و O", "en": "⭕ Tic Tac Toe",
        "fr": "⭕ Morpion", "es": "⭕ Tres en Raya",
        "vi": "⭕ Cờ Caro"
    }
    hunt_texts = {
        "ar": "🐾 صيد الحيوانات", "en": "🐾 Animal Hunt",
        "fr": "🐾 Chasse aux Animaux", "es": "🐾 Caza de Animales",
        "vi": "🐾 Săn Thú"
    }
    stats_texts = {
        "ar": "📊 إحصائياتي", "en": "📊 My Stats",
        "fr": "📊 Mes Stats", "es": "📊 Mis Stats",
        "vi": "📊 Thống kê"
    }
    lb_texts = {
        "ar": "🏆 المتصدرون", "en": "🏆 Leaderboard",
        "fr": "🏆 Classement", "es": "🏆 Ranking",
        "vi": "🏆 BXH"
    }
    
    m.add(types.InlineKeyboardButton(rps_texts.get(lang, rps_texts["en"]), callback_data="game_rps"))
    m.add(types.InlineKeyboardButton(ttt_texts.get(lang, ttt_texts["en"]), callback_data="game_ttt"))
    m.add(types.InlineKeyboardButton(hunt_texts.get(lang, hunt_texts["en"]), callback_data="game_hunt"))
    
    m2 = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(stats_texts.get(lang, stats_texts["en"]), callback_data="game_stats"),
        types.InlineKeyboardButton(lb_texts.get(lang, lb_texts["en"]), callback_data="game_leaderboard")
    )
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 كيبورد اختيار وضع اللعبة
# ═══════════════════════════════════════════════════════════════════════════

def get_game_mode_inline(game_type, lang):
    """كيبورد اختيار وضع اللعبة"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    ai_texts = {
        "ar": "🤖 ضد الذكاء الاصطناعي", "en": "🤖 Play vs AI",
        "fr": "🤖 Jouer vs IA", "es": "🤖 Jugar vs IA",
        "vi": "🤖 Chơi vs AI"
    }
    pvp_texts = {
        "ar": "👥 ضد لاعب حقيقي", "en": "👥 Play vs Player",
        "fr": "👥 Jouer vs Joueur", "es": "👥 Jugar vs Jugador",
        "vi": "👥 Chơi vs Người thật"
    }
    back_texts = {
        "ar": "🔙 رجوع", "en": "🔙 Back",
        "fr": "🔙 Retour", "es": "🔙 Atrás",
        "vi": "🔙 Quay lại"
    }
    
    m.add(types.InlineKeyboardButton(ai_texts.get(lang, ai_texts["en"]), callback_data=f"mode_ai_{game_type}"))
    m.add(types.InlineKeyboardButton(pvp_texts.get(lang, pvp_texts["en"]), callback_data=f"mode_pvp_{game_type}"))
    m.add(types.InlineKeyboardButton(back_texts.get(lang, back_texts["en"]), callback_data="game_back"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 💎 كيبورد اختيار الرهان
# ═══════════════════════════════════════════════════════════════════════════

def get_bet_inline(lang):
    """كيبورد اختيار الرهان"""
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1 💎", callback_data="bet_1"),
        types.InlineKeyboardButton("2 💎", callback_data="bet_2"),
        types.InlineKeyboardButton("3 💎", callback_data="bet_3")
    )
    
    back_texts = {
        "ar": "🔙 رجوع", "en": "🔙 Back",
        "fr": "🔙 Retour", "es": "🔙 Atrás",
        "vi": "🔙 Quay lại"
    }
    m.add(types.InlineKeyboardButton(back_texts.get(lang, "🔙 Back"), callback_data="game_back"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ✂️ كيبورد حجرة ورقة مقص
# ═══════════════════════════════════════════════════════════════════════════

def get_rps_inline(game_id, lang):
    """كيبورد حجرة ورقة مقص"""
    m = types.InlineKeyboardMarkup(row_width=3)
    
    rock_texts = {"ar": "🪨 حجرة", "en": "🪨 Rock", "fr": "🪨 Pierre", "es": "🪨 Piedra", "vi": "🪨 Đá"}
    paper_texts = {"ar": "📄 ورقة", "en": "📄 Paper", "fr": "📄 Papier", "es": "📄 Papel", "vi": "📄 Giấy"}
    scissors_texts = {"ar": "✂️ مقص", "en": "✂️ Scissors", "fr": "✂️ Ciseaux", "es": "✂️ Tijeras", "vi": "✂️ Kéo"}
    
    m.add(
        types.InlineKeyboardButton(rock_texts.get(lang, rock_texts["en"]), callback_data=f"rps_r_{game_id}"),
        types.InlineKeyboardButton(paper_texts.get(lang, paper_texts["en"]), callback_data=f"rps_p_{game_id}"),
        types.InlineKeyboardButton(scissors_texts.get(lang, scissors_texts["en"]), callback_data=f"rps_s_{game_id}")
    )
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 كيبورد اختيار الثيم
# ═══════════════════════════════════════════════════════════════════════════

def get_theme_inline(lang):
    """كيبورد اختيار الثيم"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🌿 Emerald", callback_data="theme_emerald"),
        types.InlineKeyboardButton("🌊 Ocean", callback_data="theme_ocean")
    )
    m.add(
        types.InlineKeyboardButton("🌅 Sunset", callback_data="theme_sunset"),
        types.InlineKeyboardButton("👑 Royal", callback_data="theme_royal")
    )
    m.add(
        types.InlineKeyboardButton("💫 Neon", callback_data="theme_neon")
    )
    
    back_texts = {
        "ar": "🔙 رجوع", "en": "🔙 Back",
        "fr": "🔙 Retour", "es": "🔙 Atrás",
        "vi": "🔙 Quay lại"
    }
    m.add(types.InlineKeyboardButton(back_texts.get(lang, "🔙 Back"), callback_data="settings_back"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🔒 كيبورد الخصوصية
# ═══════════════════════════════════════════════════════════════════════════

def get_privacy_inline(lang, u):
    """كيبورد الخصوصية"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    hide_lb = u.get("hide_leaderboard", False)
    
    if lang == "ar":
        lb_text = "🏆 إظهاري في المتصدرين ✅" if not hide_lb else "🏆 إخفائي من المتصدرين ❌"
    elif lang == "fr":
        lb_text = "🏆 Me montrer au classement ✅" if not hide_lb else "🏆 Me cacher du classement ❌"
    elif lang == "es":
        lb_text = "🏆 Mostrarme en ranking ✅" if not hide_lb else "🏆 Ocultarme del ranking ❌"
    elif lang == "vi":
        lb_text = "🏆 Hiển thị trên BXH ✅" if not hide_lb else "🏆 Ẩn khỏi BXH ❌"
    else:
        lb_text = "🏆 Show me on leaderboard ✅" if not hide_lb else "🏆 Hide from leaderboard ❌"
    
    m.add(types.InlineKeyboardButton(lb_text, callback_data="privacy_toggle_lb"))
    
    back_texts = {
        "ar": "🔙 رجوع", "en": "🔙 Back",
        "fr": "🔙 Retour", "es": "🔙 Atrás",
        "vi": "🔙 Quay lại"
    }
    m.add(types.InlineKeyboardButton(back_texts.get(lang, "🔙 Back"), callback_data="settings_back"))
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📜 كيبورد عام - زر العودة
# ═══════════════════════════════════════════════════════════════════════════

def get_back_button(lang, callback="main_back"):
    """زر العودة فقط"""
    m = types.InlineKeyboardMarkup()
    back_texts = {
        "ar": "🔙 رجوع", "en": "🔙 Back",
        "fr": "🔙 Retour", "es": "🔙 Atrás",
        "vi": "🔙 Quay lại"
    }
    m.add(types.InlineKeyboardButton(back_texts.get(lang, "🔙 Back"), callback_data=callback))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ كيبورد تقييم الدعم
# ═══════════════════════════════════════════════════════════════════════════

def get_rating_inline(tid, lang):
    """كيبورد تقييم الدعم بعد إغلاق التذكرة"""
    m = types.InlineKeyboardMarkup(row_width=5)
    m.add(
        types.InlineKeyboardButton("⭐", callback_data=f"rate_{tid}_1"),
        types.InlineKeyboardButton("⭐⭐", callback_data=f"rate_{tid}_2"),
        types.InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{tid}_3"),
        types.InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{tid}_4"),
        types.InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{tid}_5")
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🔄 كيبورد أزرار التأكيد/الإلغاء
# ═══════════════════════════════════════════════════════════════════════════

def get_confirm_cancel_inline(confirm_cb, cancel_cb, lang):
    """كيبورد تأكيد/إلغاء عام"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    confirm_texts = {
        "ar": "✅ تأكيد", "en": "✅ Confirm",
        "fr": "✅ Confirmer", "es": "✅ Confirmar",
        "vi": "✅ Xác nhận"
    }
    cancel_texts = {
        "ar": "❌ إلغاء", "en": "❌ Cancel",
        "fr": "❌ Annuler", "es": "❌ Cancelar",
        "vi": "❌ Hủy"
    }
    
    m.add(
        types.InlineKeyboardButton(confirm_texts.get(lang, "✅ Confirm"), callback_data=confirm_cb),
        types.InlineKeyboardButton(cancel_texts.get(lang, "❌ Cancel"), callback_data=cancel_cb)
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🔔 كيبورد تنبيه الانضمام
# ═══════════════════════════════════════════════════════════════════════════

def get_notify_restock_inline(prod, lang):
    """كيبورد إشعار عند إعادة التخزين"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    notify_texts = {
        "ar": "🔔 أبلغني عند التوفر", "en": "🔔 Notify when available",
        "fr": "🔔 Me notifier", "es": "🔔 Notificarme",
        "vi": "🔔 Thông báo khi có"
    }
    
    m.add(types.InlineKeyboardButton(
        notify_texts.get(lang, notify_texts["en"]),
        callback_data=f"notify_restock_{prod}"
    ))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🎫 كيبورد أدمن - إدارة تذكرة معينة
# ═══════════════════════════════════════════════════════════════════════════

def admin_ticket_actions(tid):
    """كيبورد إجراءات التذكرة للأدمن"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💬 دردشة مباشرة", callback_data=f"admchat_{tid}"),
        types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"admclosetick_{tid}")
    )
    m.add(
        types.InlineKeyboardButton("⚠️ تحذير المستخدم", callback_data=f"admwarntick_{tid}"),
        types.InlineKeyboardButton("⛔ حظر المستخدم", callback_data=f"admbantick_{tid}")
    )
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 👤 كيبورد أدمن - إدارة مستخدم
# ═══════════════════════════════════════════════════════════════════════════

def admin_user_actions(uid, u):
    """كيبورد إجراءات المستخدم للأدمن"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    if u.get("is_admin", False):
        m.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"admbanuser_{uid}_demote"))
    else:
        m.add(types.InlineKeyboardButton("🛡️ ترقية لأدمن", callback_data=f"userctrl_makeadmin_{uid}"))
    
    if u.get("banned", False):
        m.add(types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"userctrl_unban_{uid}"))
    else:
        m.add(
            types.InlineKeyboardButton("⛔ حظر دائم", callback_data=f"admbanuser_{uid}_perm"),
            types.InlineKeyboardButton("⏱️ حظر 24 ساعة", callback_data=f"admbanuser_{uid}_temp")
        )
    
    m.add(
        types.InlineKeyboardButton("💰 شحن رصيد", callback_data=f"admcharge_{uid}"),
        types.InlineKeyboardButton("👑 منح VIP", callback_data=f"userctrl_grantvip_{uid}")
    )
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📊 كيبورد أدمن - أنواع الإحصائيات
# ═══════════════════════════════════════════════════════════════════════════

def admin_stats_menu():
    """كيبورد الإحصائيات"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="stats_users"),
        types.InlineKeyboardButton("💰 المبيعات", callback_data="stats_sales")
    )
    m.add(
        types.InlineKeyboardButton("📦 المخزون", callback_data="stats_stock"),
        types.InlineKeyboardButton("🎫 التذاكر", callback_data="stats_tickets")
    )
    m.add(
        types.InlineKeyboardButton("🛡️ الحماية", callback_data="stats_shield"),
        types.InlineKeyboardButton("🎁 Giveaway", callback_data="stats_giveaway")
    )
    m.add(types.InlineKeyboardButton("📥 تصدير CSV", callback_data="stats_export"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 نهاية الملف
# ═══════════════════════════════════════════════════════════════════════════

print("✅ keyboards.py v3.0 loaded!")
print("🎹 All keyboards ready (5 languages)")
print("🌍 Languages: ar, en, fr, es, vi")
