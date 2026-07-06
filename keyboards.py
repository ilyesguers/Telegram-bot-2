from telebot import types
from config import LOCALES, CHANNEL_LINK, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import users

def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"),
        types.InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en"),
        types.InlineKeyboardButton("Français 🇫🇷", callback_data="setlang_fr"),
        types.InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="setlang_vi"),
        types.InlineKeyboardButton("Español 🇪🇸", callback_data="setlang_es")
    )
    return markup

def get_join_inline(lang):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LOCALES[lang]["check_btn"], url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton(LOCALES[lang]["check_btn"], callback_data="check_join"))
    return markup

def get_main_keyboard(uid, lang, page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    t = LOCALES[lang]
    if page == 1:
        markup.add(types.KeyboardButton(t["id_btn"]), types.KeyboardButton(t["balance_btn"]))
        markup.add(types.KeyboardButton(t["shop_btn"]), types.KeyboardButton(t["redeem_btn"]))
        markup.add(types.KeyboardButton(t["invite_btn"]), types.KeyboardButton(t["bonus_btn"]))
        markup.add(types.KeyboardButton(t["support_btn"]), types.KeyboardButton(t["req_prod_btn"]))
        markup.add(types.KeyboardButton(t["lang_btn"]), types.KeyboardButton("التالي ➡️"))
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
            markup.add(types.KeyboardButton(t["admin_btn"]))
    else:
        markup.add(types.KeyboardButton("🎰 صندوق الحظ"), types.KeyboardButton("🎡 عجلة الحظ"))
        markup.add(types.KeyboardButton("🔥 المهام الصعبة"), types.KeyboardButton("🏆 رتبتي الحالية"))
        markup.add(types.KeyboardButton("⬅️ السابق"))
    return markup

def get_admin_keyboard(page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if page == 1:
        markup.add(types.KeyboardButton("➕ إضافة منتج"), types.KeyboardButton("❌ حذف منتج"))
        markup.add(types.KeyboardButton("🔑 إضافة مفاتيح"), types.KeyboardButton("👁️ استعراض المفاتيح"))
        markup.add(types.KeyboardButton("🔢 حذف مفتاح معين"), types.KeyboardButton("🗑️ مسح جميع المفاتيح"))
        markup.add(types.KeyboardButton("💵 إدارة الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
        markup.add(types.KeyboardButton("💰 شحن الأعضاء"), types.KeyboardButton("🎫 إنشاء أكواد الشحن"))
        markup.add(types.KeyboardButton("🔥 التخفيضات"), types.KeyboardButton("📢 الإذاعة الشاملة"))
        markup.add(types.KeyboardButton("📤 نشر الأسعار بالقناة"), types.KeyboardButton("📣 التسويق الوهمي"))
        markup.add(types.KeyboardButton("✨ تعديل المكافأة اليومية"), types.KeyboardButton("🔗 تعديل نقاط الدعوة"))
        markup.add(types.KeyboardButton("☁️ النسخ الاحتياطي"), types.KeyboardButton("🎫 إدارة التذاكر"))
        markup.add(types.KeyboardButton("💡 طلبات المنتجات"), types.KeyboardButton("التالي للمشرف ➡️"))
    else:
        markup.add(types.KeyboardButton("⚙️ إعدادات صندوق الحظ"), types.KeyboardButton("⚙️ إعدادات عجلة الحظ"))
        markup.add(types.KeyboardButton("⚙️ إعدادات المهام الصعبة"), types.KeyboardButton("🔄 واجهة المستخدم"))
        markup.add(types.KeyboardButton("⬅️ سابق المشرف"))
    return markup
