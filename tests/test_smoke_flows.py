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


class ExperiencePackTests(unittest.TestCase):
    """المرحلة 1: بطاقة العضوية، الشارات، المتصدرون، تأكيد الشراء، تنبيه المخزون."""

    USER = 777002

    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.rec = Recorder()
        cls.rec.install()

    def setUp(self):
        self.rec.reset()
        database.register_user(SimpleNamespace(id=self.USER, username="uxtester", first_name="UX"))
        database.update_user_data(str(self.USER), verified=True, lang_selected=True, lang="ar")

    def test_profile_card_shows_rank_progress(self):
        import bot12
        bot12.show_profile(make_call(self.USER, "menu_profile"))
        self.assertTrue(self.rec.texts)
        body = self.rec.texts[-1]
        self.assertIn("بطاقة العضوية", body)
        self.assertTrue("█" in body or "░" in body, "شريط التقدّم غير ظاهر")
        markup = self.rec.last_markup()
        buttons = [b.callback_data for row in markup.keyboard for b in row]
        self.assertIn("menu_badges", buttons)
        self.assertIn("menu_leaderboard", buttons)

    def test_badges_screen_lists_all_badges(self):
        import bot12
        bot12.show_badges(make_call(self.USER, "menu_badges"))
        body = self.rec.texts[-1]
        self.assertIn("الإنجازات", body)
        self.assertEqual(body.count("✅") + body.count("🔒"), len(bot12.BADGES))

    def test_leaderboard_has_both_modes(self):
        import bot12
        bot12.show_leaderboard(make_call(self.USER, "menu_leaderboard"))
        markup = self.rec.last_markup()
        buttons = [b.callback_data for row in markup.keyboard for b in row]
        self.assertIn("lb_points", buttons)
        self.assertIn("lb_invites", buttons)

    def test_purchase_confirmation_before_charging(self):
        import bot12
        database.prices_config["TestProd"] = {"1 Day": 50, "7 Days": 200, "30 Days": 500}
        database.keys_store["TestProd"] = {"1 Day": ["KEY-1"], "7 Days": [], "30 Days": []}
        database.update_user_data(str(self.USER), points=1000, accumulated_points=1000)

        before = (database.get_user(str(self.USER)) or {}).get("points", 0)
        bot12.confirm_purchase(make_call(self.USER, "cbuy|TestProd|1 Day"))
        after = (database.get_user(str(self.USER)) or {}).get("points", 0)

        self.assertEqual(before, after, "شاشة التأكيد يجب ألا تخصم أي نقاط")
        body = self.rec.texts[-1]
        self.assertIn("تأكيد الشراء", body)
        buttons = [b.callback_data for row in self.rec.last_markup().keyboard for b in row]
        self.assertIn("buy_plan|TestProd|1 Day", buttons, "زر التأكيد النهائي مفقود")

    def test_restock_watcher_gets_notified(self):
        import bot12
        database.bot_config["stock_watchers"] = {}
        bot12.subscribe_restock(make_call(self.USER, "notifyme|TestProd|7 Days"))
        self.assertIn(str(self.USER), database.bot_config["stock_watchers"]["TestProd||7 Days"])

        self.rec.reset()
        sent = bot12.notify_restock("TestProd", "7 Days")
        self.assertEqual(sent, 1)
        self.assertTrue(any("عاد للمخزون" in text for text in self.rec.texts))
        self.assertEqual(database.bot_config["stock_watchers"]["TestProd||7 Days"], [],
                         "قائمة الانتظار يجب أن تُفرَغ بعد الإرسال")

    def test_back_main_button_works(self):
        import bot12
        bot12.back_to_main(make_call(self.USER, "back_main"))
        self.assertTrue(self.rec.texts, "زر الرجوع للرئيسية لا يستجيب")
        self.assertIsNotNone(self.rec.last_markup())


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
