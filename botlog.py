"""
=====================================================================
 botlog.py — نظام السجلات المركزي وحماية البوت من الأعطال (المرحلة 3)
=====================================================================
🎯 المشكلة: 237 `except:` صامتة و116 `print()` متفرّقة — أي خطأ حقيقي
   كان يختفي بلا أثر، ويصعب معرفة سبب أي مشكلة عند العميل.

✅ ما يوفّره هذا الملف:
 1) 📝 سجلات موحّدة بتوقيت ومستوى ووحدة المصدر (logging القياسي)
 2) 🛡️ مُعالج استثناءات عام للبوت: أي خطأ داخل أي Handler يُسجَّل
    ويصل تنبيه مختصر للأدمن بدل أن يمرّ صامتاً
 3) 🔁 إعادة المحاولة تلقائياً عند أخطاء شبكة تيليجرام المؤقتة
 4) 🧯 safe() — غلاف تنفيذ آمن يستخدمه أي كود بدل except الصامتة

📌 التركيب: يُستورد أولاً في bot.py:  import botlog
=====================================================================
"""

import logging
import os
import sys
import threading
import time
import traceback
from datetime import datetime

import telebot

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY

# =====================================================================
# 📝 إعداد السجلات
# =====================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-10s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_root = logging.getLogger("bot")
if not _root.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    _root.addHandler(handler)
    _root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    _root.propagate = False

# تهدئة سجلات المكتبات الخارجية المزعجة
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("TeleBot").setLevel(logging.WARNING)


def get_logger(name):
    """سجل مخصّص لكل ملف: log = get_logger(__name__)"""
    short = str(name).replace("__main__", "bot").split(".")[-1]
    return _root.getChild(short)


log = get_logger("core")


# =====================================================================
# 🧯 تنفيذ آمن بدل except الصامتة
# =====================================================================
def safe(func, *args, default=None, context="", **kwargs):
    """ينفّذ الدالة ويُرجع القيمة، وعند أي خطأ يسجّله ويرجع default."""
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        log.warning("خطأ %s: %s", context or getattr(func, "__name__", "?"), exc)
        return default


# =====================================================================
# 🛡️ مُعالج الاستثناءات العام + تنبيه الأدمن
# =====================================================================
_last_alert = {"key": None, "at": 0.0}
_alert_lock = threading.Lock()
ALERT_COOLDOWN = 120  # لا تُغرق الأدمن بنفس الخطأ


def _notify_admin(summary, detail):
    """تنبيه مختصر للأدمن مع كولداون لمنع التكرار."""
    with _alert_lock:
        now = time.time()
        if _last_alert["key"] == summary and now - _last_alert["at"] < ALERT_COOLDOWN:
            return
        _last_alert["key"] = summary
        _last_alert["at"] = now

    body = (f"🚨 <b>خطأ في البوت</b>\n\n"
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⚠️ <code>{summary[:200]}</code>\n\n"
            f"<pre>{detail[-600:]}</pre>")
    for admin_id in (ADMIN_PRIMARY, ADMIN_SECONDARY):
        try:
            bot.send_message(admin_id, body, parse_mode="HTML")
        except Exception:
            pass


class BotExceptionHandler(telebot.ExceptionHandler):
    """يلتقط أي استثناء داخل أي Handler بدل أن يمرّ صامتاً."""

    def handle(self, exception):
        detail = "".join(traceback.format_exception(type(exception), exception,
                                                    exception.__traceback__))
        summary = f"{type(exception).__name__}: {exception}"
        log.error("استثناء غير معالج: %s\n%s", summary, detail)
        _notify_admin(summary, detail)
        return True  # البوت يواصل العمل ولا يتوقف


bot.exception_handler = BotExceptionHandler()


# =====================================================================
# 🔁 إعادة المحاولة عند أخطاء شبكة تيليجرام المؤقتة
# =====================================================================
try:
    telebot.apihelper.RETRY_ON_ERROR = True
    telebot.apihelper.RETRY_TIMEOUT = 2
    telebot.apihelper.MAX_RETRIES = 3
    telebot.apihelper.CONNECT_TIMEOUT = 20
    telebot.apihelper.READ_TIMEOUT = 30
except Exception as exc:  # pragma: no cover
    log.warning("تعذّر ضبط إعدادات إعادة المحاولة: %s", exc)


log.info("=" * 45)
log.info("✅ botlog.py — السجلات المركزية جاهزة (المستوى: %s)", LOG_LEVEL)
log.info("🛡️ مُعالج الاستثناءات العام: مفعّل")
log.info("🔁 إعادة المحاولة على أخطاء الشبكة: مفعّلة")
log.info("=" * 45)


# =====================================================================
# 🧱 درع المعالجات: أي خطأ داخل أي زر لا يترك المستخدم بلا رد
# =====================================================================
FRIENDLY_ERROR = {
    "ar": "⚠️ حدث خطأ مؤقت. حاول مرة أخرى — تم إبلاغ الإدارة.",
    "en": "⚠️ A temporary error occurred. Please try again — admins notified.",
    "fr": "⚠️ Erreur temporaire. Réessayez — les admins sont informés.",
    "es": "⚠️ Error temporal. Inténtalo de nuevo — admins notificados.",
    "vi": "⚠️ Lỗi tạm thời. Hãy thử lại — quản trị viên đã được báo.",
}


def _friendly(uid):
    try:
        from database import get_user
        lang = (get_user(str(uid)) or {}).get("lang", "ar")
    except Exception:
        lang = "ar"
    return FRIENDLY_ERROR.get(lang, FRIENDLY_ERROR["ar"])


def _wrap_handler(func, kind):
    if getattr(func, "_botlog_guarded", False):
        return func

    def guarded(payload, *args, **kwargs):
        try:
            return func(payload, *args, **kwargs)
        except Exception as exc:
            detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            name = getattr(func, "__name__", "handler")
            log.error("خطأ في %s (%s): %s\n%s", name, kind, exc, detail)
            _notify_admin(f"{name}: {type(exc).__name__}: {exc}", detail)
            try:
                uid = payload.from_user.id
                if kind == "callback":
                    bot.answer_callback_query(payload.id, _friendly(uid)[:190], show_alert=True)
                elif kind == "payment":
                    # لا نترك المستخدم في شاشة دفع معلّقة
                    bot.answer_pre_checkout_query(payload.id, ok=False,
                                                  error_message="⚠️ خطأ مؤقت، حاول لاحقاً")
                else:
                    bot.send_message(payload.chat.id, _friendly(uid))
            except Exception:
                pass
            return None

    guarded._botlog_guarded = True
    guarded.__name__ = getattr(func, "__name__", "guarded_handler")
    return guarded


def install_handler_guards(target_bot=None):
    """يغلّف كل المعالجات المسجَّلة — يُستدعى بعد تحميل كل الموديولات."""
    target_bot = target_bot or bot
    wrapped = 0
    groups = (
        ("message", getattr(target_bot, "message_handlers", [])),
        ("callback", getattr(target_bot, "callback_query_handlers", [])),
        ("payment", getattr(target_bot, "pre_checkout_query_handlers", [])),
        ("payment", getattr(target_bot, "shipping_query_handlers", [])),
    )
    for kind, handlers in groups:
        for entry in handlers:
            try:
                original = entry.get("function")
                if original and not getattr(original, "_botlog_guarded", False):
                    entry["function"] = _wrap_handler(original, kind)
                    wrapped += 1
            except Exception as exc:
                log.warning("تعذّر تغليف معالج: %s", exc)
    log.info("🧱 درع المعالجات: تم تأمين %s معالجاً", wrapped)
    return wrapped
