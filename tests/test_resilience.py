"""اختبارات المتانة (المرحلة 3): حفظ ذرّي، أقفال تزامن، درع المعالجات، سجلات.

    python tests/test_resilience.py
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = tempfile.mkdtemp(prefix="telegram-bot-resilience-")
os.environ.setdefault("API_TOKEN", "123456:TEST_TOKEN")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATA_DIR}/res.db"
os.chdir(TEST_DATA_DIR)
sys.path.insert(0, str(PROJECT_ROOT))

import botlog  # noqa: E402
import database  # noqa: E402
from config import bot as BOT  # noqa: E402


class AtomicSaveTests(unittest.TestCase):
    """الحفظ يجب ألا يترك ملفاً تالفاً أبداً."""

    def test_save_writes_valid_json(self):
        path = os.path.join(TEST_DATA_DIR, "store.json")
        payload = {"منتج": {"1 Day": ["KEY-1", "KEY-2"]}, "عدد": 42}
        database.save_json(path, payload)
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), payload)

    def test_no_temp_files_left_behind(self):
        path = os.path.join(TEST_DATA_DIR, "clean.json")
        database.save_json(path, {"a": 1})
        leftovers = [name for name in os.listdir(TEST_DATA_DIR) if name.endswith(".tmp")]
        self.assertEqual(leftovers, [], f"ملفات مؤقتة لم تُنظَّف: {leftovers}")

    def test_concurrent_saves_never_corrupt_file(self):
        path = os.path.join(TEST_DATA_DIR, "concurrent.json")
        errors = []

        def writer(index):
            try:
                for _ in range(15):
                    database.save_json(path, {"writer": index, "items": list(range(120))})
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)  # يفشل لو كان الملف تالفاً
        self.assertEqual(len(data["items"]), 120)

    def test_save_survives_mutation_during_write(self):
        """تعديل القاموس أثناء الحفظ كان يرمي RuntimeError ويفشل الحفظ بصمت."""
        path = os.path.join(TEST_DATA_DIR, "mutating.json")
        shared = {str(i): i for i in range(300)}
        stop = threading.Event()

        def mutate():
            counter = 0
            # مساحة مفاتيح محدودة: يحاكي تعديل الإعدادات الحيّة بلا تضخّم ذاكرة
            while not stop.is_set():
                shared[f"live{counter % 50}"] = counter
                if counter % 7 == 0:
                    shared.pop(f"live{(counter + 3) % 50}", None)
                counter += 1
                time.sleep(0.0005)

        mutator = threading.Thread(target=mutate, daemon=True)
        mutator.start()
        try:
            for _ in range(15):
                database.save_json(path, shared)
        finally:
            stop.set()
            mutator.join(timeout=2)

        self.assertTrue(os.path.exists(path), "الحفظ فشل تماماً أثناء التعديل المتزامن")
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertGreater(len(data), 200)

    def test_corrupted_file_is_quarantined_not_lost(self):
        path = os.path.join(TEST_DATA_DIR, "broken.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{ not valid json")
        self.assertEqual(database.load_json(path), {})
        self.assertTrue(os.path.exists(path + ".corrupted"),
                        "الملف التالف يجب أن يُحفظ كنسخة بدل ضياعه")


class EngineTests(unittest.TestCase):
    def test_engine_uses_pre_ping(self):
        self.assertTrue(database.engine.pool._pre_ping,
                        "pool_pre_ping مطلوب حتى لا تنهار الاتصالات الخاملة")


class HandlerShieldTests(unittest.TestCase):
    """أي خطأ داخل معالج لا يجب أن يترك المستخدم بلا رد."""

    def test_message_handler_error_is_caught_and_answered(self):
        replies = []
        BOT.send_message = lambda chat_id, text, **kwargs: replies.append(text)
        botlog._notify_admin = lambda summary, detail: None

        def boom(message):
            raise ValueError("انفجار تجريبي")

        guarded = botlog._wrap_handler(boom, "message")
        message = SimpleNamespace(chat=SimpleNamespace(id=1),
                                  from_user=SimpleNamespace(id=1))
        guarded(message)  # يجب ألا يرفع استثناء

        self.assertTrue(replies, "المستخدم لم يتلقَ أي رد عند الخطأ")
        self.assertIn("⚠️", replies[-1])

    def test_callback_handler_error_shows_alert(self):
        alerts = []
        BOT.answer_callback_query = lambda call_id, text=None, **kw: alerts.append(text)
        botlog._notify_admin = lambda summary, detail: None

        def boom(call):
            raise RuntimeError("خطأ زر")

        guarded = botlog._wrap_handler(boom, "callback")
        guarded(SimpleNamespace(id="cb", from_user=SimpleNamespace(id=1),
                                message=SimpleNamespace(chat=SimpleNamespace(id=1))))
        self.assertTrue(alerts and alerts[-1])

    def test_guards_are_idempotent(self):
        def handler(message):
            return "ok"

        once = botlog._wrap_handler(handler, "message")
        twice = botlog._wrap_handler(once, "message")
        self.assertIs(once, twice, "التغليف تكرر مرتين على نفس المعالج")

    def test_install_guards_covers_registered_handlers(self):
        installed = botlog.install_handler_guards(BOT)
        self.assertGreaterEqual(installed, 0)
        for entry in BOT.message_handlers:
            self.assertTrue(getattr(entry["function"], "_botlog_guarded", False),
                            "بقي معالج غير مؤمَّن")


class LoggingTests(unittest.TestCase):
    def test_logger_is_namespaced(self):
        log = botlog.get_logger("tests.module")
        self.assertTrue(log.name.startswith("bot."))

    def test_safe_returns_default_on_error(self):
        def broken():
            raise KeyError("x")

        self.assertEqual(botlog.safe(broken, default="fallback", context="اختبار"), "fallback")
        self.assertEqual(botlog.safe(lambda: 5), 5)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    finally:
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
