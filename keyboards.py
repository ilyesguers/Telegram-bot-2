from telebot import types
from config import LOCALES, CHANNEL_LINK, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import get_user

# =====================================================
# 🎨 أزرار اللغات
# =====================================================
def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es")
    )
    return markup

# =====================================================
# 🔒 زر الاشتراك الإجباري
# =====================================================
def get_join_inline(lang):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_join"))
    return markup

# =====================================================
# 🏠 لوحة المستخدم الرئيسية (جديدة كلياً)
# =====================================================
def get_main_keyboard(uid, lang, page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if page == 1:
        # الصفحة 1 - الأزرار الأساسية
        markup.add(
            types.KeyboardButton("💰 محفظتي"),
            types.KeyboardButton("🆔 معلوماتي")
        )
        markup.add(
            types.KeyboardButton("🛍️ المتجر"),
            types.KeyboardButton("🎁 استرداد كود")
        )
        markup.add(
            types.KeyboardButton("🔗 نظام الإحالة"),
            types.KeyboardButton("✨ المكافأة اليومية")
        )
        markup.add(
            types.KeyboardButton("💬 الدعم الفني"),
            types.KeyboardButton("💡 طلب منتج")
        )
        markup.add(
            types.KeyboardButton("🌐 تغيير اللغة"),
            types.KeyboardButton("➡️ الصفحة التالية")
        )
        
        # زر الأدمن يظهر فقط للمشرفين
        u = get_user(str(uid)) or {}
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
            markup.add(types.KeyboardButton("👑 لوحة الإدارة"))
    else:
        # الصفحة 2 - الألعاب والمهام
        markup.add(
            types.KeyboardButton("🎰 صندوق الحظ"),
            types.KeyboardButton("🎡 عجلة الحظ")
        )
        markup.add(
            types.KeyboardButton("🔥 المهام والإنجازات"),
            types.KeyboardButton("🏆 رتبتي")
        )
        markup.add(types.KeyboardButton("⬅️ الصفحة السابقة"))
    
    return markup

# =====================================================
# 👑 لوحة الإدارة
# =====================================================
def get_admin_keyboard(page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if page == 1:
        markup.add(
            types.KeyboardButton("➕ إضافة منتج"),
            types.KeyboardButton("❌ حذف منتج")
        )
        markup.add(
            types.KeyboardButton("🔑 إضافة مفاتيح"),
            types.KeyboardButton("👁️ استعراض المفاتيح")
        )
        markup.add(
            types.KeyboardButton("🔢 حذف مفتاح معين"),
            types.KeyboardButton("🗑️ مسح جميع المفاتيح")
        )
        markup.add(
            types.KeyboardButton("💵 إدارة الأسعار"),
            types.KeyboardButton("👥 إدارة الأعضاء")
        )
        markup.add(
            types.KeyboardButton("💰 شحن الأعضاء"),
            types.KeyboardButton("🎫 إنشاء أكواد الشحن")
        )
        markup.add(
            types.KeyboardButton("🔥 التخفيضات"),
            types.KeyboardButton("📢 الإذاعة الشاملة")
        )
        markup.add(
            types.KeyboardButton("📤 نشر الأسعار بالقناة"),
            types.KeyboardButton("📣 التسويق الوهمي")
        )
        markup.add(
            types.KeyboardButton("✨ تعديل المكافأة اليومية"),
            types.KeyboardButton("🔗 تعديل نقاط الدعوة")
        )
        markup.add(
            types.KeyboardButton("☁️ النسخ الاحتياطي"),
            types.KeyboardButton("🎫 إدارة التذاكر")
        )
        markup.add(
            types.KeyboardButton("💡 طلبات المنتجات"),
            types.KeyboardButton("➡️ إعدادات الألعاب")
        )
        markup.add(types.KeyboardButton("🔙 العودة للمستخدم"))
    else:
        markup.add(
            types.KeyboardButton("⚙️ إعدادات صندوق الحظ"),
            types.KeyboardButton("⚙️ إعدادات عجلة الحظ")
        )
        markup.add(types.KeyboardButton("⚙️ إعدادات المهام"))
        markup.add(types.KeyboardButton("⬅️ لوحة الإدارة الرئيسية"))
    
    return markup
