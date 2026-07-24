"""Regression tests for the shop screens, price engine and animations."""

import os
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("API_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
sys.path.insert(0, str(PROJECT_ROOT))

import shop_ui  # noqa: E402


LANGS = ("ar", "en", "fr", "es", "vi")

PRICES = {
    "Alpha": {"1 Day": 20, "7 Days": 100, "30 Days": 300},
    "Beta": {"1 Day": 50, "7 Days": 250, "30 Days": 700},
}

KEYS = {
    "Alpha": {"1 Day": ["k1", "k2"], "7 Days": [], "30 Days": ["k3"]},
    "Beta": {"1 Day": [], "7 Days": [], "30 Days": []},
}

USER = {"points": 1000, "rank": "🥇 Gold", "rank_discount": 0.02}


def buttons(markup):
    return [button for row in markup.keyboard for button in row]


class TranslationTests(unittest.TestCase):
    def test_every_language_defines_every_key(self):
        reference = set(shop_ui.SHOP_TRANSLATIONS["en"])
        for lang in LANGS:
            self.assertEqual(set(shop_ui.SHOP_TRANSLATIONS[lang]), reference, lang)

    def test_unknown_language_and_key_fall_back(self):
        self.assertEqual(shop_ui.gt_shop("zz", "title"), shop_ui.SHOP_TRANSLATIONS["en"]["title"])
        self.assertEqual(shop_ui.gt_shop("ar", "not_a_key"), "not_a_key")


class PriceEngineTests(unittest.TestCase):
    def test_discounts_stack_multiplicatively(self):
        # 100 → -10% global → -30% flash → -2% rank
        self.assertEqual(shop_ui.compute_price(100, 10, 30, 0.02), 58)

    def test_percentage_discount_is_capped_so_nothing_is_free(self):
        self.assertGreater(shop_ui.compute_price(100, 100, 100, 0.0), 0)
        self.assertGreater(shop_ui.compute_price(1000, 90, 90, 0.9), 0)

    def test_invalid_input_never_raises(self):
        for bad in (None, "", "abc", -50):
            self.assertEqual(shop_ui.compute_price(bad), 0)
        self.assertEqual(shop_ui.compute_price(100, -5, -5, -1), 100)

    def test_flash_discount_only_applies_to_its_own_product(self):
        sale = {"product": "Alpha", "discount": 40}
        self.assertEqual(shop_ui.flash_discount_for(sale, "Alpha"), 40)
        self.assertEqual(shop_ui.flash_discount_for(sale, "Beta"), 0)
        self.assertEqual(shop_ui.flash_discount_for(None, "Alpha"), 0)


class ProductIdTests(unittest.TestCase):
    def test_id_is_stable_short_and_callback_safe(self):
        for name in ("Alpha", "منتج عربي", "Name With | Pipe", "x" * 200):
            token = shop_ui.product_id(name)
            self.assertEqual(token, shop_ui.product_id(name))
            self.assertLessEqual(len(f"select_prod_{token}".encode("utf-8")), 64)

    def test_resolve_accepts_new_id_and_legacy_raw_name(self):
        self.assertEqual(shop_ui.resolve_product(shop_ui.product_id("Alpha"), PRICES), "Alpha")
        self.assertEqual(shop_ui.resolve_product("Alpha", PRICES), "Alpha")
        self.assertIsNone(shop_ui.resolve_product("deleted", PRICES))
        self.assertIsNone(shop_ui.resolve_product(None, PRICES))


class ShopViewTests(unittest.TestCase):
    def test_catalogue_lists_every_product_with_stock_and_navigation(self):
        for lang in LANGS:
            text, markup = shop_ui.build_shop_view(lang, USER, PRICES, KEYS, {"discount": 0})
            self.assertNotIn("None", text)
            labels = [b.text for b in buttons(markup)]
            self.assertTrue(any("Alpha" in label for label in labels))
            self.assertTrue(any("Beta" in label for label in labels))
            callbacks = [b.callback_data for b in buttons(markup)]
            self.assertIn("shop_refresh", callbacks)
            self.assertIn("shop_home", callbacks)
            self.assertIn(f"select_prod_{shop_ui.product_id('Alpha')}", callbacks)

    def test_empty_shop_still_offers_a_way_out(self):
        text, markup = shop_ui.build_shop_view("ar", USER, {}, {}, {})
        self.assertIn(shop_ui.gt_shop("ar", "empty"), text)
        self.assertEqual(
            [b.callback_data for b in buttons(markup)], ["shop_refresh", "shop_home"])

    def test_flash_sale_is_highlighted_on_its_product_only(self):
        sale = {"product": "Alpha", "discount": 30, "expires": "x"}
        text, markup = shop_ui.build_shop_view(
            "en", USER, PRICES, KEYS, {"discount": 0}, sale, "01:00:00")
        self.assertIn("30%", text)
        self.assertIn("01:00:00", text)
        labels = {b.text.split(" | ")[0]: b.text for b in buttons(markup)}
        self.assertTrue(any(label.startswith("🔥") and "Alpha" in label for label in labels))
        self.assertFalse(any(label.startswith("🔥") and "Beta" in label for label in labels))

    def test_out_of_stock_product_is_flagged(self):
        _, markup = shop_ui.build_shop_view("en", USER, PRICES, KEYS, {})
        beta = [b for b in buttons(markup) if "Beta" in b.text][0]
        self.assertTrue(beta.text.startswith("⚠️"))
        self.assertIn("0", beta.text)


class ProductViewTests(unittest.TestCase):
    def test_plan_buttons_carry_prices_stock_and_buy_callback(self):
        text, markup = shop_ui.build_product_view(
            "en", USER, "Alpha", PRICES, KEYS, {"discount": 0})
        self.assertIn("Alpha", text)
        callbacks = [b.callback_data for b in buttons(markup)]
        for plan in shop_ui.PLANS:
            self.assertIn(f"buy_plan|Alpha|{plan}", callbacks)
        self.assertIn("menu_shop_back", callbacks)

    def test_button_price_matches_the_price_engine(self):
        config = {"discount": 10}
        sale = {"product": "Alpha", "discount": 30}
        _, markup = shop_ui.build_product_view(
            "en", USER, "Alpha", PRICES, KEYS, config, sale)
        expected = shop_ui.compute_price(PRICES["Alpha"]["1 Day"], 10, 30, 0.02)
        day_button = [b for b in buttons(markup) if b.callback_data.endswith("|1 Day")][0]
        self.assertIn(str(expected), day_button.text)

    def test_fully_sold_out_product_shows_a_hint_instead_of_a_prompt(self):
        text, _ = shop_ui.build_product_view("en", USER, "Beta", PRICES, KEYS, {})
        self.assertIn(shop_ui.gt_shop("en", "soldout_hint"), text)
        self.assertNotIn(shop_ui.gt_shop("en", "duration"), text)

    def test_missing_product_does_not_raise(self):
        text, markup = shop_ui.build_product_view("en", USER, "Ghost", PRICES, KEYS, {})
        self.assertIn("Ghost", text)
        self.assertTrue(buttons(markup))


class SuccessViewTests(unittest.TestCase):
    def test_receipt_contains_key_price_and_navigation(self):
        text, markup = shop_ui.build_success_view("ar", "Alpha", "1 Day", 58, "KEY-123", 100)
        self.assertIn("KEY-123", text)
        self.assertIn("58", text)
        self.assertIn("42", text)  # saved amount
        self.assertEqual(
            [b.callback_data for b in buttons(markup)], ["menu_shop_back", "shop_home"])

    def test_receipt_handles_missing_base_price(self):
        text, _ = shop_ui.build_success_view("en", "Alpha", "1 Day", 58, "KEY-1", None)
        self.assertIn("KEY-1", text)


class AnimationTests(unittest.TestCase):
    def test_purchase_frames_end_at_a_full_bar(self):
        frames = shop_ui.purchase_frames(["a", "b", "c", "d"])
        self.assertEqual(len(frames), 4)
        self.assertIn("100%", frames[-1])
        self.assertEqual(shop_ui.purchase_frames([]), [])
        self.assertEqual(shop_ui.purchase_frames(None), [])

    def test_loading_frames_are_localised_and_finish_with_ready(self):
        frames = shop_ui.loading_frames("ar", "opening", 3)
        self.assertEqual(len(frames), 3)
        self.assertIn(shop_ui.gt_shop("ar", "opening"), frames[0])
        self.assertIn(shop_ui.gt_shop("ar", "ready"), frames[-1])

    def test_animation_swallows_telegram_errors(self):
        class ExplodingBot:
            def edit_message_text(self, *args, **kwargs):
                raise RuntimeError("flood limit")

        self.assertFalse(
            shop_ui.animate_frames(ExplodingBot(), 1, 2, ["a", "b"], delay=0))

    def test_animation_is_skipped_without_a_message_to_edit(self):
        class CountingBot:
            def __init__(self):
                self.calls = 0

            def edit_message_text(self, *args, **kwargs):
                self.calls += 1

        bot = CountingBot()
        self.assertFalse(shop_ui.animate_frames(bot, 1, None, ["a"], delay=0))
        self.assertFalse(shop_ui.animate_frames(bot, 1, 2, [], delay=0))
        self.assertEqual(bot.calls, 0)

        self.assertTrue(shop_ui.animate_frames(bot, 1, 2, ["a", "b"], delay=0))
        self.assertEqual(bot.calls, 2)


if __name__ == "__main__":
    unittest.main()
