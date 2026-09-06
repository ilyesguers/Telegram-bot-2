"""
=====================================================================
 bot11.py — إصلاحات جوهرية وتحسينات تجربة (Core Fixes & QoL)
=====================================================================
🎯 ما يحلّه هذا الملف (بدون حذف أي ميزة قائمة):

 1) 🚪 أمر /cancel عام:
    كان المستخدم أو الأدمن "يعلق" داخل أي خطوة إدخال
    (register_next_step_handler) بلا أي طريقة للخروج، لأن تيليبوت
    يوجّه الرسالة التالية إلى الخطوة ويتجاهل بقية المعالجات.
    الحل: نغلّف register_next_step_handler عالمياً، فإذا كتب المستخدم
    /cancel (أو "إلغاء") تُلغى الخطوة وتُعاد له القائمة الرئيسية.

 2) 🧭 لوحة تنقّل موحّدة (nav_kb) تستخدمها بقية الملفات لإضافة زر رجوع
    لأي شاشة كانت بلا أزرار.

 3) 🛡️ guard_user() — فحص موحّد (حظر + اشتراك إجباري) لأي شاشة.

📌 طريقة التركيب: يُستورد أولاً في bot.py قبل بقية الموديولات:
        import bot11
=====================================================================
"""

from telebot import types

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, t

# =====================================================================
# 🌍 نصوص الإلغاء (5 لغات)
# =====================================================================
CANCEL_WORDS = {
    "/cancel", "/الغاء", "/إلغاء",
    "إلغاء", "الغاء", "إلغاء العملية", "الغاء العملية",
    "cancel", "annuler", "cancelar", "hủy", "huy",
    "❌ إلغاء", "❌ Cancel", "🔙 إلغاء",
}

CANCEL_TEXT = {
    "ar": "🚪 <b>تم إلغاء العملية</b>\n\n✅ <i>يمكنك المتابعة من القائمة الرئيسية.</i>",
    "en": "🚪 <b>Operation cancelled</b>\n\n✅ <i>You can continue from the main menu.</i>",
    "fr": "🚪 <b>Opération annulée</b>\n\n✅ <i>Vous pouvez continuer depuis le menu principal.</i>",
    "es": "🚪 <b>Operación cancelada</b>\n\n✅ <i>Puedes continuar desde el menú principal.</i>",
    "vi": "🚪 <b>Đã hủy thao tác</b>\n\n✅ <i>Bạn có thể tiếp tục từ menu chính.</i>",
}

NOTHING_TEXT = {
    "ar": "ℹ️ <b>لا توجد عملية جارية لإلغائها.</b>",
    "en": "ℹ️ <b>There is no ongoing operation to cancel.</b>",
    "fr": "ℹ️ <b>Aucune opération en cours à annuler.</b>",
    "es": "ℹ️ <b>No hay ninguna operación en curso.</b>",
    "vi": "ℹ️ <b>Không có thao tác nào để hủy.</b>",
}


def _lang_of(uid):
    try:
        from database import get_user
        return (get_user(str(uid)) or {}).get("lang", "ar")
    except Exception:
        return "ar"


def _is_cancel_message(message):
    text = (getattr(message, "text", "") or "").strip()
    if not text:
        return False
    return text.lower() in {w.lower() for w in CANCEL_WORDS}


def _send_main_menu(chat_id, uid, lang):
    """يعيد المستخدم إلى القائمة الرئيسية بأمان (بدون استيراد دائري)."""
    try:
        from keyboards import get_main_keyboard
        bot.send_message(chat_id, CANCEL_TEXT.get(lang, CANCEL_TEXT["ar"]),
                         reply_markup=get_main_keyboard(uid, lang), parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(chat_id, CANCEL_TEXT.get(lang, CANCEL_TEXT["ar"]), parse_mode="HTML")
        except Exception:
            pass


# =====================================================================
# 🚪 تغليف register_next_step_handler عالمياً
# =====================================================================
_original_register_next_step = bot.register_next_step_handler
_original_register_next_step_by_chat = bot.register_next_step_handler_by_chat_id


def _wrap_callback(callback):
    """يلفّ أي دالة خطوة تالية بحيث تحترم أمر الإلغاء."""
    if callback is None or getattr(callback, "_bot11_wrapped", False):
        return callback

    def wrapper(message, *args, **kwargs):
        if _is_cancel_message(message):
            uid = str(message.from_user.id)
            lang = _lang_of(uid)
            try:
                bot.clear_step_handler_by_chat_id(message.chat.id)
            except Exception:
                pass
            _send_main_menu(message.chat.id, uid, lang)
            return
        return callback(message, *args, **kwargs)

    wrapper._bot11_wrapped = True
    wrapper.__name__ = getattr(callback, "__name__", "step_handler")
    return wrapper


def _patched_register_next_step(message, callback, *args, **kwargs):
    return _original_register_next_step(message, _wrap_callback(callback), *args, **kwargs)


def _patched_register_next_step_by_chat(chat_id, callback, *args, **kwargs):
    return _original_register_next_step_by_chat(chat_id, _wrap_callback(callback), *args, **kwargs)


bot.register_next_step_handler = _patched_register_next_step
bot.register_next_step_handler_by_chat_id = _patched_register_next_step_by_chat


# =====================================================================
# 🚪 أمر /cancel عندما لا توجد خطوة جارية
# =====================================================================
@bot.message_handler(commands=["cancel"])
def _cancel_command(message):
    uid = str(message.from_user.id)
    lang = _lang_of(uid)
    try:
        bot.clear_step_handler_by_chat_id(message.chat.id)
    except Exception:
        pass
    try:
        bot.send_message(message.chat.id, NOTHING_TEXT.get(lang, NOTHING_TEXT["ar"]),
                         parse_mode="HTML")
    except Exception:
        pass


# =====================================================================
# 🧭 لوحة تنقّل موحّدة — تُستخدم في أي شاشة بلا أزرار
# =====================================================================
def nav_kb(lang="ar", back_cb="back_main", refresh_cb=None, extra=None):
    """زر رجوع (+ تحديث اختياري + أزرار إضافية) بتنسيق موحّد."""
    m = types.InlineKeyboardMarkup(row_width=2)
    row = []
    if refresh_cb:
        row.append(types.InlineKeyboardButton(t(lang, "btn_refresh") if t(lang, "btn_refresh") != "btn_refresh"
                                              else "🔄 تحديث", callback_data=refresh_cb))
    back_label = t(lang, "btn_back")
    if back_label == "btn_back":
        back_label = "🔙 رجوع"
    row.append(types.InlineKeyboardButton(back_label, callback_data=back_cb))
    m.add(*row)
    for button in (extra or []):
        m.add(button)
    return m


# =====================================================================
# 🛡️ فحص موحّد قبل عرض أي شاشة للمستخدم
# =====================================================================
def guard_user(call_or_uid, answer_call=None):
    """يرجع True إذا كان المستخدم مسموحاً له (غير محظور ومشترك بالقنوات)."""
    try:
        uid = str(getattr(getattr(call_or_uid, "from_user", None), "id", call_or_uid))
    except Exception:
        return True

    try:
        if int(uid) in (ADMIN_PRIMARY, ADMIN_SECONDARY):
            return True
    except Exception:
        pass

    try:
        from utils import is_user_banned, check_channel_join
        lang = _lang_of(uid)
        if is_user_banned(uid):
            if answer_call is not None:
                bot.answer_callback_query(answer_call.id, t(lang, "banned")[:190], show_alert=True)
            return False
        if not check_channel_join(uid):
            if answer_call is not None:
                bot.answer_callback_query(answer_call.id, t(lang, "join_first_alert")[:190], show_alert=True)
            return False
    except Exception:
        return True
    return True


print("=" * 55)
print("✅ bot11.py — إصلاحات جوهرية")
print("🚪 أمر /cancel العام: مفعّل")
print("🧭 لوحة التنقّل الموحّدة: جاهزة")
print("=" * 55)
