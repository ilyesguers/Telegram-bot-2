"""اختبارات دخان (Smoke tests) لمسارات المستخدم والأدمن الأساسية.

تشغّل البوت بالكامل في الذاكرة (SQLite + بوت وهمي) بدون أي اتصال بتيليجرام،
وتتحقق من أن الأزرار والأوامر ترد فعلاً بدل أن "تتجمّد".

    python tests/test_smoke_flows.py
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = tempfile.mkdtemp(prefix="telegram-bot-smoke-")
os.environ.setdefault("API_TOKEN", "123456:TEST_TOKEN")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATA_DIR}/smoke.db"
os.chdir(TEST_DATA_DIR)
sys.path.insert(0, str(PROJECT_ROOT))

import telebot  # noqa: E402
from telebot import types  # noqa: E402

import config  # noqa: E402
import utils  # noqa: E402

# لا يوجد اتصال بالشبكة في الاختبارات: نعتبر المستخدم مشتركاً دائماً.
utils.check_channel_join = lambda uid: True

import database  # noqa: E402
import bot as mainbot  # noqa: E402
import bot10  # noqa: E402
import bot11  # noqa: E402
import keyboards  # noqa: E402

BOT = config.bot


class Recorder:
    """يلتقط كل ما كان البوت سيرسله إلى تيليجرام."""

    def __init__(self):
        self.sent = []
        self.edited = []
        self.answers = []
        self._mid = 1000

    def install(self):
        BOT.send_message = self._send_message
        BOT.edit_message_text = self._edit_message_text
        BOT.answer_callback_query = self._answer
        BOT.delete_message = lambda *a, **k: True
        BOT.send_chat_action = lambda *a, **k: True
        BOT.edit_message_reply_markup = lambda *a, **k: True
        BOT.get_me = lambda: SimpleNamespace(username="testbot", id=1, first_name="Test")

    def _send_message(self, chat_id, text, **kwargs):
        self._mid += 1
        self.sent.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})
        return SimpleNamespace(message_id=self._mid, chat=SimpleNamespace(id=chat_id))

    def _edit_message_text(self, text, chat_id=None, message_id=None, **kwargs):
        self.edited.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})
        return SimpleNamespace(message_id=message_id, chat=SimpleNamespace(id=chat_id))

    def _answer(self, call_id, text=None, **kwargs):
        self.answers.append({"id": call_id, "text": text, "kwargs": kwargs})
        return True

    # أدوات مساعدة
    @property
    def texts(self):
        return [m["text"] for m in self.sent] + [m["text"] for m in self.edited]

    def contains(self, needle):
        return any(needle in text for text in self.texts if text)

    def last_markup(self):
        for entry in reversed(self.sent + self.edited):
            markup = entry["kwargs"].get("reply_markup")
            if markup is not None:
                return markup
        return None

    def reset(self):
        self.sent.clear()
        self.edited.clear()
        self.answers.clear()


def make_message(uid, text, chat_id=None):
    chat_id = chat_id or uid
    payload = {
        "message_id": 1,
        "from": {"id": uid, "is_bot": False, "first_name": "Tester", "username": f"user{uid}"},
        "chat": {"id": chat_id, "type": "private"},
        "date": 1700000000,
        "text": text,
    }
    return types.Message.de_json(payload)


def make_call(uid, data, chat_id=None):
    chat_id = chat_id or uid
    payload = {
        "id": "cb-1",
        "from": {"id": uid, "is_bot": False, "first_name": "Tester", "username": f"user{uid}"},
        "message": {
            "message_id": 55,
            "from": {"id": 1, "is_bot": True, "first_name": "Bot"},
            "chat": {"id": chat_id, "type": "private"},
            "date": 1700000000,
            "text": "…",
        },
        "chat_instance": "1",
        "data": data,
    }
    return types.CallbackQuery.de_json(payload)


class UserFlowTests(unittest.TestCase):
    USER = 777001

    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.rec = Recorder()
        cls.rec.install()

    def setUp(self):
        self.rec.reset()
        utils.user_last_msg.clear()
        utils.spam_warnings.clear()
        database.register_user(SimpleNamespace(id=self.USER, username="tester", first_name="Tester"))
        database.update_user_data(str(self.USER), verified=True, lang_selected=True, lang="ar")

    # ── /start يعرض القائمة الرئيسية ──
    def test_start_shows_main_menu(self):
        mainbot.handle_commands(make_message(self.USER, "/start"))
        self.assertTrue(self.rec.sent, "‏/start لم يُرجع أي رسالة")
        markup = self.rec.last_markup()
        self.assertIsNotNone(markup, "القائمة الرئيسية بلا أزرار")

    # ── أي نص غير معروف يجب ألا يُهمَل ──
    def test_unknown_text_has_fallback(self):
        mainbot.main_router(make_message(self.USER, "نص عشوائي جداً ##"))
        self.assertTrue(self.rec.sent, "لا يوجد رد احتياطي على النص غير المعروف")

    # ── زر المتجر يعمل حتى لو كان المتجر فارغاً ──
    def test_shop_button_responds(self):
        mainbot.main_router(make_message(self.USER, config.t("ar", "btn_shop")))
        self.assertTrue(self.rec.sent)

    # ── شاشة المحفظة الفاخرة (bot10) ترد ومعها أزرار تنقّل ──
    def test_premium_wallet_has_navigation(self):
        bot10.premium_wallet(make_call(self.USER, "menu_balance"))
        self.assertTrue(self.rec.edited or self.rec.sent, "شاشة المحفظة لم تُعرض")
        markup = self.rec.last_markup()
        self.assertIsNotNone(markup, "شاشة المحفظة بلا زر رجوع (طريق مسدود)")
        buttons = [b.callback_data for row in markup.keyboard for b in row]
        self.assertIn("back_account", buttons)

    # ── /cancel يخرج المستخدم من أي خطوة إدخال عالقة ──
    def test_global_cancel_releases_pending_step(self):
        called = {"value": False}

        def step(message):
            called["value"] = True

        msg = make_message(self.USER, "/anything")
        BOT.register_next_step_handler(msg, step)
        wrapped = BOT.next_step_backend.handlers.get(self.USER)
        self.assertTrue(wrapped, "لم تُسجَّل خطوة تالية")

        handler = wrapped[0].callback
        handler(make_message(self.USER, "/cancel"))
        self.assertFalse(called["value"], "‏/cancel لم يلغِ الخطوة")
        self.assertTrue(self.rec.sent, "‏/cancel لم يُرجع أي رسالة")


class AdminFlowTests(unittest.TestCase):
    ADMIN = config.ADMIN_PRIMARY

    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.rec = Recorder()
        cls.rec.install()

    def setUp(self):
        self.rec.reset()
        utils.user_last_msg.clear()
        database.register_user(SimpleNamespace(id=self.ADMIN, username="admin", first_name="Admin"))
        database.update_user_data(str(self.ADMIN), verified=True, lang_selected=True,
                                  lang="ar", is_admin=True)

    def test_admin_keyboard_keeps_every_feature(self):
        labels = set()
        for row in keyboards.get_admin_keyboard().keyboard:
            for button in row:
                labels.add(button["text"] if isinstance(button, dict) else button.text)
        for expected in ("📦 المنتجات", "🔑 المفاتيح", "👥 الأعضاء", "🎫 التذاكر",
                         "💰 المبيعات", "📢 التسويق", "⚡ عروض خاطفة", "🎁 Giveaway",
                         "👑 إدارة VIP", "📦 التجديد التلقائي", "📨 رسائل القناة",
                         "📢 نشر في القنوات", "🔐 إدارة الاشتراك الإجباري", "🎮 الألعاب",
                         "🛡️ مكافحة الرشق", "🧠 الحماية الذكية", "🔧 استعادة المشتريات",
                         "⚙️ النظام", "📊 الإحصائيات", "💡 الطلبات", "🛠️ وضع الصيانة",
                         "🎮 ألعاب القناة التفاعلية", "🧑‍💻 التحكم الشامل بالأعضاء",
                         "🔙 العودة"):
            self.assertIn(expected, labels, f"زر مفقود من لوحة الأدمن: {expected}")

    def test_admin_panel_opens(self):
        mainbot.main_router(make_message(self.ADMIN, config.t("ar", "btn_admin")))
        self.assertTrue(self.rec.contains("ADMIN PANEL"))

    def test_smart_protection_panel_is_reachable(self):
        import bot8
        self.rec.reset()
        bot8.show_protection_panel(make_message(self.ADMIN, "🧠 الحماية الذكية"))
        self.assertTrue(self.rec.sent or self.rec.edited,
                        "لوحة الحماية الذكية ما زالت غير قابلة للفتح")


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    finally:
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
