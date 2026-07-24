"""Regression tests for publishing announcements to all configured channels."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = tempfile.mkdtemp(prefix="telegram-bot-channel-tests-")
os.environ.setdefault("API_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.chdir(TEST_DATA_DIR)
sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
import utils  # noqa: E402


class FakeBot:
    """Small Telegram API double that records channel deliveries."""

    def __init__(self):
        self.messages = []
        self.voices = []

    def get_me(self):
        return SimpleNamespace(username="testbot")

    def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))
        return SimpleNamespace(message_id=len(self.messages))

    def send_voice(self, chat_id, voice, **kwargs):
        self.voices.append((chat_id, voice, kwargs))
        return SimpleNamespace(message_id=len(self.voices))


class ChannelBroadcastingTests(unittest.TestCase):
    def setUp(self):
        self.real_bot = utils.bot
        self.bot = FakeBot()
        utils.bot = self.bot
        database.bot_config.clear()
        database.bot_config.update({
            "force_sub_channels": [
                {"id": -10001, "label": "الأولى"},
                {"id": "-10002", "label": "الثانية"},
            ],
            "managed_channels": [
                {"id": -10002, "label": "نسخة مكررة"},
                {"id": -10003, "label": "الثالثة"},
            ],
            "channel_payment_announcements": [],
        })

    def tearDown(self):
        utils.bot = self.real_bot

    def test_channel_union_is_deduplicated_and_receives_marketing(self):
        self.assertEqual(
            [channel["id"] for channel in utils.get_publish_channels()],
            [-10001, -10002, -10003],
        )

        utils.publish_sale_to_channel("Product", "30 Days", 500)

        self.assertEqual(
            [delivery[0] for delivery in self.bot.messages],
            [-10001, -10002, -10003],
        )
        self.assertTrue(all("NEW SALE" in delivery[1] for delivery in self.bot.messages))

    def test_every_vip_purchase_is_sent_to_every_channel(self):
        delivered = utils.publish_vip_purchase_to_channels(1, "vip-1")
        self.assertEqual(set(delivered), {"-10001", "-10002", "-10003"})
        self.assertEqual(len(self.bot.messages), 3)

    def test_stars_purchase_requires_more_than_twenty_and_is_sent_once(self):
        self.assertEqual(utils.publish_stars_conversion_to_channels(20, 40, "stars-20"), {})
        self.assertEqual(self.bot.messages, [])

        delivered = utils.publish_stars_conversion_to_channels(21, 42, "stars-21")
        self.assertEqual(set(delivered), {"-10001", "-10002", "-10003"})
        self.assertEqual(len(self.bot.messages), 3)

        # A duplicate Telegram update must not create duplicate channel posts.
        self.assertEqual(utils.publish_stars_conversion_to_channels(21, 42, "stars-21"), {})
        self.assertEqual(len(self.bot.messages), 3)


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
