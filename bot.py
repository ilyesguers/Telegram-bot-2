import telebot
from telebot import types
import random
import os
import time
import json
from datetime import datetime, timedelta

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, LOCALES
from database import (engine, text, init_db, get_user, update_user_data, register_user,
                      keys_store, redeem_codes, prices_config, bot_config, save_json,
                      DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG, update_user_rank_and_quests)
from utils import (check_spam, is_user_banned, check_channel_join, generate_fake_key,
                   trigger_captcha, is_captcha_pending, verify_captcha, require_verification_on_start)
from keyboards import get_lang_inline, get_join_inline, get_main_keyboard, get_admin_keyboard

# =====================================================
# 🚀 تهيئة قاعدة البيانات
# =====================================================
init_db()

def is_admin(uid, u=None):
    if u is None:
        u = get_user(uid) or {}
    return int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)

def get_all_user_ids():
    with engine.connect() as conn:
        return [str(r[0]) for r in conn.execute(text("SELECT uid FROM users")).fetchall()]

# =====================================================
# 🔒 دالة فحص الاشتراك (تُستخدم قبل أي فعل)
# =====================================================
def enforce_channel_subscription(message):
    """يفحص الاشتراك ويرسل رسالة الإجبار إذا لم يكن مشترك"""
    uid = str(message.from_user.id)
    if not check_channel_join(uid):
        u = get_user(uid) or {}
        lang = u.get("lang", "ar")
        bot.send_message(message.chat.id, 
            f"🔐 <b>═══ اشتراك إجباري ═══</b>\n\n"
            f"⚠️ يجب الاشتراك بقناتنا الرسمية أولاً\n"
            f"لاستخدام جميع مميزات البوت.\n\n"
            f"📢 القناة: {CHANNEL_LINK}\n\n"
            f"✅ بعد الاشتراك، اضغط <b>«تحقق»</b> أدناه",
            reply_markup=get_join_inline(lang), parse_mode="HTML")
        return False
    return True

# =====================================================
# 🎯 الأوامر
# =====================================================
@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "🚫 حسابك محظور حالياً.")

    u = get_user(uid) or {}
    
    if message.text.startswith('/id'):
        if not enforce_channel_subscription(message):
            return
        return bot.send_message(message.chat.id, 
            f"🆔 <b>معلومات حسابك:</b>\n\n"
            f"👤 الآيدي: <code>{uid}</code>\n"
            f"📝 اليوزر: @{u.get('username', 'N/A')}", parse_mode="HTML")

    # نظام الإحالة
    args = message.text.split()
    if len(args) > 1 and u.get("invited_by") is None:
        inviter_id = args[1]
        if get_user(inviter_id) and inviter_id != uid:
            update_user_data(uid, invited_by=inviter_id)
            reward = bot_config.get("invite_reward", 20)
            update_user_data(inviter_id, points=reward, accumulated_points=reward, invite_count=1)
            update_user_rank_and_quests(inviter_id)
            try:
                bot.send_message(int(inviter_id), 
                    f"🎊 <b>دعوة جديدة ناجحة!</b>\n\n"
                    f"🎁 مكافأتك: <b>+{reward}</b> نقطة", parse_mode="HTML")
            except: pass

    # 🔒 الاشتراك الإجباري
    if not enforce_channel_subscription(message):
        return

    # 🛡️ كابتشا إجبارية للحسابات غير الموثقة
    if not u.get("verified", False):
        require_verification_on_start(uid)
        return bot.send_message(message.chat.id, 
            "🛡️ <b>تحقق أمني إلزامي</b>\n\n"
            "🤖 لضمان أنك لست بوت، حل الكابتشا المرسل لك.")

    bot.send_message(message.chat.id, 
        f"🌟 <b>═══ أهلاً بك في متجرنا ═══</b>\n\n"
        f"👋 مرحباً بك! نحن سعداء بانضمامك.\n"
        f"🌐 اختر لغتك المفضلة أدناه:", 
        reply_markup=get_lang_inline(), parse_mode="HTML")

# =====================================================
# 🎯 التوجيه الرئيسي (بمطابقة دقيقة)
# =====================================================
@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "🚫 حسابك محظور حالياً.")
    
    # الكابتشا المعلقة
    if is_captcha_pending(uid):
        return bot.send_message(message.chat.id, 
            "🛡️ يجب حل الكابتشا أولاً!\nاضغط على الإجابة من الأزرار المرسلة.")
        
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    txt = message.text.strip() if message.text else ""
    admin_flag = is_admin(uid, u)

    # 🔒 الاشتراك الإجباري
    if not enforce_channel_subscription(message):
        return

    if bot_config.get("maintenance", False) and not admin_flag:
        return bot.send_message(message.chat.id, 
            "🛠️ <b>البوت تحت الصيانة</b>\n⏳ نعود قريباً!", parse_mode="HTML")

    # ================================================
    # 🔴 أزرار الأدمن
    # ================================================
    if admin_flag:
        if txt == "➡️ إعدادات الألعاب":
            return bot.send_message(message.chat.id, 
                "⚙️ <b>═══ إعدادات الألعاب ═══</b>", 
                reply_markup=get_admin_keyboard(page=2), parse_mode="HTML")
        
        if txt == "⬅️ لوحة الإدارة الرئيسية":
            return bot.send_message(message.chat.id, 
                "👑 <b>═══ لوحة الإدارة ═══</b>", 
                reply_markup=get_admin_keyboard(page=1), parse_mode="HTML")

        if txt == "🔙 العودة للمستخدم":
            return bot.send_message(message.chat.id, 
                "🔙 عدت إلى واجهة المستخدم.", 
                reply_markup=get_main_keyboard(uid, lang, page=1))

        if txt == "⚙️ إعدادات صندوق الحظ":
            return show_lootbox_settings(message)
        
        if txt == "⚙️ إعدادات عجلة الحظ":
            return show_wheel_settings(message)
        
        if txt == "⚙️ إعدادات المهام":
            return show_quests_settings(message)
        
        if txt == "✨ تعديل المكافأة اليومية":
            m = bot.send_message(message.chat.id, 
                f"✨ <b>تعديل المكافأة اليومية</b>\n\n"
                f"💰 القيمة الحالية: <b>{bot_config.get('daily_gift', 10)}</b> نقطة\n\n"
                f"✍️ أرسل القيمة الجديدة (أرقام فقط):", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_edit_daily_bonus)

        if txt == "🔗 تعديل نقاط الدعوة":
            m = bot.send_message(message.chat.id, 
                f"🔗 <b>تعديل نقاط الدعوة</b>\n\n"
                f"💰 القيمة الحالية: <b>{bot_config.get('invite_reward', 20)}</b> نقطة\n\n"
                f"✍️ أرسل القيمة الجديدة (أرقام فقط):", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_edit_invite_reward)

        if txt == "🎫 إدارة التذاكر":
            return admin_show_tickets(message)

        if txt == "💡 طلبات المنتجات":
            return admin_show_product_requests(message)

        if txt == "➕ إضافة منتج":
            m = bot.send_message(message.chat.id, "➕ <b>إضافة منتج</b>\n\n✍️ أرسل اسم المنتج:", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_add_product_func)

        if txt == "❌ حذف منتج":
            m = bot.send_message(message.chat.id, "❌ <b>حذف منتج</b>\n\n✍️ أرسل اسم المنتج:", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_delete_product_func)

        if txt == "🔑 إضافة مفاتيح":
            return admin_add_keys_menu(message)

        if txt == "💵 إدارة الأسعار":
            return admin_manage_prices_menu(message)

        if txt == "🔢 حذف مفتاح معين":
            return admin_delete_key_menu(message)

        if txt == "👁️ استعراض المفاتيح":
            return admin_view_keys(message)

        if txt == "🗑️ مسح جميع المفاتيح":
            keys_store.clear()
            for prod in prices_config.keys():
                keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
            save_json(DB_KEYS, keys_store)
            return bot.send_message(message.chat.id, "🗑️ <b>تم مسح جميع المفاتيح!</b>", parse_mode="HTML")

        if txt == "👥 إدارة الأعضاء":
            m = bot.send_message(message.chat.id, "👥 ✍️ أرسل آيدي العضو:", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_view_member_func)

        if txt == "💰 شحن الأعضاء":
            m = bot.send_message(message.chat.id, 
                "💰 <b>شحن رصيد</b>\n\n✍️ الصيغة: <code>ID المبلغ</code>", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_charge_member_func)

        if txt == "🎫 إنشاء أكواد الشحن":
            m = bot.send_message(message.chat.id, 
                "🎫 <b>إنشاء كود شحن</b>\n\n✍️ الصيغة: <code>الكود القيمة</code>", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_create_code_func)

        if txt == "🔥 التخفيضات":
            m = bot.send_message(message.chat.id, 
                "🔥 <b>خصم عام</b>\n\n✍️ أرسل نسبة الخصم (0-99):", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_set_discount_func)

        if txt == "📢 الإذاعة الشاملة":
            m = bot.send_message(message.chat.id, 
                "📢 <b>إذاعة شاملة</b>\n\n✍️ أرسل نص الرسالة:", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_broadcast_func)

        if txt == "📤 نشر الأسعار بالقناة":
            return admin_publish_prices(message)

        if txt == "📣 التسويق الوهمي":
            m = bot.send_message(message.chat.id, 
                "📣 <b>تسويق وهمي</b>\n\n⚠️ اكتب <code>تأكيد</code>:", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_confirm_fake_marketing)

        if txt == "☁️ النسخ الاحتياطي":
            return admin_show_stats_backup(message)

    # ================================================
    # 🟢 أزرار المستخدم العادي (مطابقة دقيقة!)
    # ================================================
    
    if txt == "➡️ الصفحة التالية":
        return bot.send_message(message.chat.id, 
            "🎮 <b>═══ الترفيه والمهام ═══</b>", 
            reply_markup=get_main_keyboard(uid, lang, page=2), parse_mode="HTML")
    
    if txt == "⬅️ الصفحة السابقة":
        return bot.send_message(message.chat.id, 
            "🏠 <b>القائمة الرئيسية</b>", 
            reply_markup=get_main_keyboard(uid, lang, page=1), parse_mode="HTML")

    if txt == "🎰 صندوق الحظ":
        return show_lootbox(message)

    if txt == "🎡 عجلة الحظ":
        return show_wheel(message)

    if txt == "🔥 المهام والإنجازات":
        return show_quests(message, uid)

    if txt == "🏆 رتبتي":
        return show_rank(message, uid)

    if txt == "🆔 معلوماتي":
        return bot.send_message(message.chat.id, 
            f"🆔 <b>═══ معلوماتك ═══</b>\n\n"
            f"👤 الآيدي: <code>{uid}</code>\n"
            f"📝 اليوزر: @{u.get('username', 'N/A')}", parse_mode="HTML")

    if txt == "💰 محفظتي":
        return show_balance(message, uid)

    if txt == "🌐 تغيير اللغة":
        return bot.send_message(message.chat.id, 
            "🌐 <b>اختر لغتك:</b>", 
            reply_markup=get_lang_inline(), parse_mode="HTML")

    if txt == "✨ المكافأة اليومية":
        return claim_daily_bonus(message, uid, u)

    if txt == "🔗 نظام الإحالة":
        return show_referral(message, uid)

    if txt == "🎁 استرداد كود":
        m = bot.send_message(message.chat.id, 
            "🎁 <b>═══ استرداد كود ═══</b>\n\n✍️ أدخل كود الشحن:", parse_mode="HTML")
        return bot.register_next_step_handler(m, process_redeem_user)

    if txt == "💬 الدعم الفني":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ فتح تذكرة", callback_data="confirm_open_ticket"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
        )
        return bot.send_message(message.chat.id, 
            "💬 <b>═══ الدعم الفني ═══</b>\n\n"
            "📩 سيتم فتح تذكرة دعم فني.\n\n"
            "❓ هل تريد المتابعة؟", 
            reply_markup=markup, parse_mode="HTML")

    if txt == "💡 طلب منتج":
        m = bot.send_message(message.chat.id, 
            "💡 <b>═══ طلب منتج جديد ═══</b>\n\n"
            "📝 اكتب اسم المنتج وتفاصيله:", parse_mode="HTML")
        return bot.register_next_step_handler(m, process_product_request_input)

    if txt == "🛍️ المتجر":
        return show_shop_enhanced(message, uid, u)

    if txt == "👑 لوحة الإدارة" and admin_flag:
        return bot.send_message(message.chat.id, 
            "👑 <b>═══ لوحة الإدارة ═══</b>", 
            reply_markup=get_admin_keyboard(page=1), parse_mode="HTML")


# =====================================================
# 🎨 دوال العرض
# =====================================================
def show_lootbox(message):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = (f"🎰 <b>═══ صندوق الحظ ═══</b>\n\n"
           f"🎁 <i>مغامرة الحظ بانتظارك!</i>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"💸 <b>السعر:</b> {price} نقطة\n"
           f"📊 <b>نسبة الفوز:</b> {chance}%\n"
           f"🏆 <b>الجائزة:</b> +100 إلى +500 نقطة\n"
           f"━━━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🎁 فتح الصندوق ({price} نقطة)", callback_data="game_buy_lootbox"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_wheel(message):
    price = bot_config.get("wheel_price", 40)
    msg = (f"🎡 <b>═══ عجلة الحظ ═══</b>\n\n"
           f"🌀 <i>أدر واكشف حظك!</i>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"💸 <b>سعر اللفة:</b> {price} نقطة\n\n"
           f"🎁 <b>الجوائز:</b>\n"
           f" ├ 🟥 0 نقطة\n"
           f" ├ 🟨 10 نقاط\n"
           f" ├ 🟩 20 نقطة\n"
           f" ├ 🟦 استرجاع السعر\n"
           f" └ 🏆 <b>+1000 نقطة</b>\n"
           f"━━━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"💫 تدوير ({price} نقطة)", callback_data="game_spin_wheel"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_quests(message, uid):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    completed = u.get("completed_quests", "") or ""
    invite_cnt = u.get("invite_count", 0) or 0
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    acc_pts = u.get("accumulated_points", 0) or 0
    q = bot_config.get("quests")
    
    msg = "🔥 <b>═══ المهام والإنجازات ═══</b>\n\n"
    
    if "quest_invite" in completed:
        st1, prog1 = "✅ مكتملة", "🟩🟩🟩🟩🟩"
    else:
        p = min(100, (invite_cnt / q['invite']['target']) * 100) if q['invite']['target'] > 0 else 0
        filled = int(p / 20)
        prog1 = "🟩" * filled + "⬜" * (5 - filled)
        st1 = f"⏳ {invite_cnt}/{q['invite']['target']}"
    
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"1️⃣ 👥 <b>مهمة الدعوات</b>\n"
    msg += f"🎯 ادعُ {q['invite']['target']} أصدقاء\n"
    msg += f"🎁 المكافأة: <b>+{q['invite']['reward']}</b>\n"
    msg += f"{prog1} {st1}\n\n"
    
    if "quest_buy" in completed:
        st2, prog2 = "✅ مكتملة", "🟩🟩🟩🟩🟩"
    else:
        p = min(100, (user_buys / q['buy']['target']) * 100) if q['buy']['target'] > 0 else 0
        filled = int(p / 20)
        prog2 = "🟩" * filled + "⬜" * (5 - filled)
        st2 = f"⏳ {user_buys}/{q['buy']['target']}"
    
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"2️⃣ 🛒 <b>مهمة المبيعات</b>\n"
    msg += f"🎯 أكمل {q['buy']['target']} مشتريات\n"
    msg += f"🎁 المكافأة: <b>+{q['buy']['reward']}</b>\n"
    msg += f"{prog2} {st2}\n\n"
    
    if "quest_points" in completed:
        st3, prog3 = "✅ مكتملة", "🟩🟩🟩🟩🟩"
    else:
        p = min(100, (acc_pts / q['points']['target']) * 100) if q['points']['target'] > 0 else 0
        filled = int(p / 20)
        prog3 = "🟩" * filled + "⬜" * (5 - filled)
        st3 = f"⏳ {acc_pts}/{q['points']['target']}"
    
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"3️⃣ 💎 <b>مهمة النقاط</b>\n"
    msg += f"🎯 اجمع {q['points']['target']} نقطة\n"
    msg += f"🎁 المكافأة: <b>+{q['points']['reward']}</b>\n"
    msg += f"{prog3} {st3}"
    
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def show_rank(message, uid):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    r_name = u.get("rank", "عضو عادي 🔹")
    r_disc = int((u.get("rank_discount", 0.0) or 0.0) * 100)
    acc_pts = u.get("accumulated_points", 0) or 0
    
    msg = (f"🏆 <b>═══ نظام الرتب ═══</b>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"🎖️ رتبتك: <b>{r_name}</b>\n"
           f"💎 خصمك: <b>{r_disc}%</b>\n"
           f"📊 نقاطك التراكمية: <code>{acc_pts}</code>\n"
           f"━━━━━━━━━━━━━━━\n\n"
           f"📋 <b>مستويات الرتب:</b>\n\n"
           f"🥈 الفضي - 200 نقطة (1%)\n"
           f"🥇 الذهبي - 600 نقطة (2%)\n"
           f"💎 الماسي - 1500 نقطة (3%)\n"
           f"⚡ الهيرو - 3500 نقطة (4%)\n"
           f"👑 الماستر - 7000 نقطة (4.5%)\n"
           f"🏆 الأسطورة - 12000 نقطة (5%)")
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def show_balance(message, uid):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    msg = (f"💰 <b>═══ محفظتي ═══</b>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"👤 <b>الآيدي:</b> <code>{uid}</code>\n"
           f"💵 <b>الرصيد:</b> {u.get('points', 0)} نقطة\n"
           f"🏆 <b>الرتبة:</b> {u.get('rank', 'عضو عادي 🔹')}\n"
           f"💎 <b>الخصم:</b> {int((u.get('rank_discount', 0) or 0)*100)}%\n"
           f"👥 <b>الدعوات:</b> {u.get('invite_count', 0)}\n"
           f"📊 <b>النقاط التراكمية:</b> {u.get('accumulated_points', 0)}\n"
           f"━━━━━━━━━━━━━━━")
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def claim_daily_bonus(message, uid, u):
    now = datetime.now()
    lc = u.get("last_claim")
    
    if lc:
        try:
            last_time = datetime.fromisoformat(lc)
            next_claim = last_time + timedelta(days=1)
            if now < next_claim:
                remaining = next_claim - now
                hours = remaining.seconds // 3600
                mins = (remaining.seconds % 3600) // 60
                return bot.send_message(message.chat.id, 
                    f"⏰ <b>═══ مكافأة يومية ═══</b>\n\n"
                    f"❌ استلمت مكافأتك اليوم!\n\n"
                    f"⏳ <b>عد بعد:</b> {hours}س {mins}د", parse_mode="HTML")
        except Exception as e:
            print(f"خطأ last_claim: {e}")
    
    gift = bot_config.get("daily_gift", 10)
    update_user_data(uid, last_claim=now.isoformat())
    update_user_data(uid, points=gift, accumulated_points=gift)
    update_user_rank_and_quests(uid)
    
    u_new = get_user(uid) or {}
    new_balance = u_new.get("points", 0)
    
    bot.send_message(message.chat.id, 
        f"🎁 <b>═══ مكافأة يومية ═══</b>\n\n"
        f"✅ تم استلامها بنجاح!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎉 حصلت على: <b>+{gift}</b> نقطة\n"
        f"💰 رصيدك الآن: <b>{new_balance}</b> نقطة\n"
        f"⏰ المكافأة القادمة: بعد 24 ساعة\n"
        f"━━━━━━━━━━━━━━━", parse_mode="HTML")

def show_referral(message, uid):
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "your_bot"
    link = f"https://t.me/{bot_user}?start={uid}"
    u = get_user(uid) or {}
    invites = u.get("invite_count", 0) or 0
    reward = bot_config.get("invite_reward", 20)
    total_earned = invites * reward
    
    msg = (f"🔗 <b>═══ نظام الإحالة ═══</b>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"👥 <b>دعواتك:</b> {invites}\n"
           f"🎁 <b>مكافأة كل دعوة:</b> {reward} نقطة\n"
           f"💵 <b>إجمالي أرباحك:</b> {total_earned} نقطة\n"
           f"━━━━━━━━━━━━━━━\n\n"
           f"📎 <b>رابطك الشخصي:</b>\n"
           f"<code>{link}</code>\n\n"
           f"💡 <b>كيف يعمل النظام؟</b>\n"
           f"1️⃣ انسخ الرابط\n"
           f"2️⃣ شاركه مع أصدقائك\n"
           f"3️⃣ احصل على {reward} نقطة عن كل عضو!")
    
    markup = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={link}&text=🔥%20انضم%20للمتجر%20واكسب%20مكافآت%20مجانية!"
    markup.add(types.InlineKeyboardButton("📤 مشاركة الرابط", url=share_url))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_shop_enhanced(message, uid, u):
    if not prices_config:
        return bot.send_message(message.chat.id, 
            "📭 <b>المتجر فارغ حالياً!</b>", parse_mode="HTML")
    
    u_discount = u.get("rank_discount", 0.0) or 0.0
    disc = bot_config.get("discount", 0)
    rank = u.get("rank", "عضو عادي 🔹")
    points = u.get("points", 0)
    
    header = (f"🛍️ <b>═══ متجر المنتجات ═══</b>\n\n"
              f"━━━━━━━━━━━━━━━\n"
              f"💰 <b>رصيدك:</b> {points} نقطة\n"
              f"🏆 <b>رتبتك:</b> {rank}\n"
              f"💎 <b>خصم رتبتك:</b> {int(u_discount*100)}%\n")
    
    if disc > 0:
        header += f"🔥 <b>خصم إضافي:</b> {disc}%\n"
    
    header += (f"📦 <b>المنتجات:</b> {len(prices_config)}\n"
               f"━━━━━━━━━━━━━━━\n\n"
               f"👇 <b>اختر المنتج:</b>")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for prod in prices_config.keys():
        stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        emoji = "✅" if stock > 0 else "⚠️"
        markup.add(types.InlineKeyboardButton(
            f"{emoji} 📦 {prod}  |  📊 {stock} متاح", 
            callback_data=f"select_prod_{prod}"))
    
    markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_shop"))
    bot.send_message(message.chat.id, header, reply_markup=markup, parse_mode="HTML")

# =====================================================
# ⚙️ إعدادات الأدمن
# =====================================================
def show_lootbox_settings(message):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = (f"⚙️ <b>═══ إعدادات صندوق الحظ ═══</b>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"💸 <b>السعر:</b> {price} نقطة\n"
           f"📊 <b>نسبة الفوز:</b> {chance}%\n"
           f"━━━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("➕ سعر +5", callback_data="cfg_box_price_up"),
        types.InlineKeyboardButton("➖ سعر -5", callback_data="cfg_box_price_down")
    )
    markup.row(
        types.InlineKeyboardButton("📈 نسبة +5%", callback_data="cfg_box_chance_up"),
        types.InlineKeyboardButton("📉 نسبة -5%", callback_data="cfg_box_chance_down")
    )
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_wheel_settings(message):
    price = bot_config.get("wheel_price", 40)
    chance = bot_config.get("wheel_chance", 5)
    msg = (f"⚙️ <b>═══ إعدادات عجلة الحظ ═══</b>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"💸 <b>السعر:</b> {price} نقطة\n"
           f"📊 <b>الجائزة الكبرى:</b> {chance}%\n"
           f"━━━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("➕ سعر +5", callback_data="cfg_wheel_price_up"),
        types.InlineKeyboardButton("➖ سعر -5", callback_data="cfg_wheel_price_down")
    )
    markup.row(
        types.InlineKeyboardButton("📈 نسبة +1%", callback_data="cfg_wheel_chance_up"),
        types.InlineKeyboardButton("📉 نسبة -1%", callback_data="cfg_wheel_chance_down")
    )
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_quests_settings(message):
    q = bot_config.get("quests")
    msg = (f"⚙️ <b>═══ إعدادات المهام ═══</b>\n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"1️⃣ 👥 <b>الدعوات:</b>\n"
           f"   🎯 الهدف: {q['invite']['target']}\n"
           f"   🎁 الجائزة: {q['invite']['reward']}\n\n"
           f"2️⃣ 🛒 <b>المبيعات:</b>\n"
           f"   🎯 الهدف: {q['buy']['target']}\n"
           f"   🎁 الجائزة: {q['buy']['reward']}\n\n"
           f"3️⃣ 💎 <b>النقاط:</b>\n"
           f"   🎯 الهدف: {q['points']['target']}\n"
           f"   🎁 الجائزة: {q['points']['reward']}\n"
           f"━━━━━━━━━━━━━━━")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("👥 هدف ➖", callback_data="cfg_q_inv_t_down"), types.InlineKeyboardButton("👥 هدف ➕", callback_data="cfg_q_inv_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 دعوات ➖", callback_data="cfg_q_inv_r_down"), types.InlineKeyboardButton("🎁 دعوات ➕", callback_data="cfg_q_inv_r_up"))
    markup.row(types.InlineKeyboardButton("🛒 هدف ➖", callback_data="cfg_q_buy_t_down"), types.InlineKeyboardButton("🛒 هدف ➕", callback_data="cfg_q_buy_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 شراء ➖", callback_data="cfg_q_buy_r_down"), types.InlineKeyboardButton("🎁 شراء ➕", callback_data="cfg_q_buy_r_up"))
    markup.row(types.InlineKeyboardButton("💎 هدف ➖", callback_data="cfg_q_pts_t_down"), types.InlineKeyboardButton("💎 هدف ➕", callback_data="cfg_q_pts_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 نقاط ➖", callback_data="cfg_q_pts_r_down"), types.InlineKeyboardButton("🎁 نقاط ➕", callback_data="cfg_q_pts_r_up"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def admin_show_tickets(message):
    tickets = bot_config.get("tickets", {})
    open_t = {k: v for k, v in tickets.items() if v.get("status", "open") == "open"}
    if not open_t:
        return bot.send_message(message.chat.id, "🎉 لا توجد تذاكر مفتوحة.")
    markup = types.InlineKeyboardMarkup()
    for t_id, t_info in open_t.items():
        markup.add(types.InlineKeyboardButton(f"🎫 #{t_id} - {t_info['uid']}", callback_data=f"view_ticket_{t_id}"))
    bot.send_message(message.chat.id, "🎫 <b>التذاكر:</b>", reply_markup=markup, parse_mode="HTML")

def admin_show_product_requests(message):
    reqs = bot_config.get("product_requests", {})
    if not reqs:
        return bot.send_message(message.chat.id, "📭 لا توجد طلبات.")
    msg = "💡 <b>طلبات المنتجات:</b>\n\n"
    for r_id, r_info in reqs.items():
        msg += f"🔹 <b>#{r_id}</b>\n👤 {r_info['uid']}\n📦 {r_info['text']}\n━━━━━━\n"
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def admin_add_keys_menu(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا منتجات.")
    markup = types.InlineKeyboardMarkup()
    for prod in prices_config.keys():
        markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_addkey_prod|{prod}"))
    bot.send_message(message.chat.id, "🔑 <b>اختر المنتج:</b>", reply_markup=markup, parse_mode="HTML")

def admin_manage_prices_menu(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا منتجات.")
    markup = types.InlineKeyboardMarkup()
    for prod in prices_config.keys():
        markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_price_prod|{prod}"))
    bot.send_message(message.chat.id, "💵 <b>اختر منتج:</b>", reply_markup=markup, parse_mode="HTML")

def admin_delete_key_menu(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا منتجات.")
    markup = types.InlineKeyboardMarkup()
    for prod in prices_config.keys():
        markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_delkey_prod|{prod}"))
    bot.send_message(message.chat.id, "🔢 <b>اختر منتج:</b>", reply_markup=markup, parse_mode="HTML")

def admin_view_keys(message):
    if not keys_store:
        return bot.send_message(message.chat.id, "📭 لا مفاتيح.")
    status = "🔑 <b>═══ المفاتيح ═══</b>\n\n"
    for prod, plans in keys_store.items():
        status += f"📦 <b>{prod}</b>\n"
        for plan, lst in plans.items():
            status += f"   ├ {plan}: {len(lst)}\n"
        status += "\n"
    bot.send_message(message.chat.id, status, parse_mode="HTML")

def admin_publish_prices(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا منتجات.")
    pub = "📢 <b>═══ قائمة الأسعار ═══</b>\n\n"
    for prod, plans in prices_config.items():
        pub += f"📦 <b>{prod}</b>\n"
        for plan, b_price in plans.items():
            disc = bot_config.get("discount", 0)
            f_price = int(b_price * (1 - disc/100))
            pub += f"   ├ {plan} ➡️ {f_price} نقطة\n"
        pub += "\n"
    try:
        pub += f"🤖 t.me/{bot.get_me().username}"
    except: pass
    try:
        bot.send_message(CHANNEL_ID, pub, parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ نُشر بالقناة!")
    except:
        bot.send_message(message.chat.id, "❌ خطأ.")

def admin_show_stats_backup(message):
    stats = (f"📊 <b>═══ الإحصائيات ═══</b>\n\n"
             f"👥 <b>المستخدمين:</b> {len(get_all_user_ids())}\n"
             f"🛒 <b>المبيعات:</b> {bot_config.get('total_sales', 0)}\n"
             f"💰 <b>الأرباح:</b> {bot_config.get('total_earnings', 0)}\n"
             f"🎫 <b>الأكواد:</b> {len(redeem_codes)}\n"
             f"📦 <b>المنتجات:</b> {len(prices_config)}")
    bot.send_message(message.chat.id, stats, parse_mode="HTML")
    for f_name in [DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
        if os.path.exists(f_name):
            try:
                with open(f_name, "rb") as f_doc:
                    bot.send_document(message.chat.id, f_doc)
            except: pass

# =====================================================
# 🔁 معالج Callback
# =====================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    u = get_user(uid) or {}
    data = call.data

    # 🛡️ كابتشا
    if data.startswith("captcha_ans_"):
        user_answer = data.split("_", 2)[2]
        result = verify_captcha(uid, user_answer)
        
        if result == "correct":
            update_user_data(uid, verified=True)
            try:
                bot.edit_message_text(
                    "✅ <b>═══ تم التحقق بنجاح ═══</b>\n\n"
                    "🎉 مرحباً بك في المتجر!",
                    call.message.chat.id, call.message.message_id, parse_mode="HTML")
            except: pass
            lang = u.get("lang", "ar")
            bot.send_message(call.message.chat.id, 
                "🏠 <b>القائمة الرئيسية</b>", 
                reply_markup=get_main_keyboard(uid, lang, page=1), parse_mode="HTML")
        elif result == "wrong":
            bot.answer_callback_query(call.id, "❌ خطأ! حاول مجدداً", show_alert=True)
        elif result == "banned":
            try:
                bot.edit_message_text(
                    "🚫 <b>تم الحظر</b>\n\n⛔ فشلت 3 مرات\n⏰ حظر ساعة كاملة",
                    call.message.chat.id, call.message.message_id, parse_mode="HTML")
            except: pass
        elif result == "expired":
            bot.answer_callback_query(call.id, "⏰ انتهت الصلاحية!", show_alert=True)
        return

    # فحص الاشتراك للـ callbacks
    if data != "check_join" and not data.startswith("setlang_") and not data.startswith("captcha_"):
        if not check_channel_join(uid):
            try: bot.answer_callback_query(call.id, "⚠️ اشترك بالقناة أولاً!", show_alert=True)
            except: pass
            return

    # ⚙️ إعدادات المهام
    if data.startswith("cfg_q_"):
        if not is_admin(uid, u):
            return bot.answer_callback_query(call.id, "❌ لا صلاحيات.", show_alert=True)
        parts = data.split("_")
        task_type, field_type, action = parts[2], parts[3], parts[4]
        t_key = "invite" if task_type == "inv" else ("buy" if task_type == "buy" else "points")
        f_key = "target" if field_type == "t" else "reward"
        step = 1
        if t_key == "points" and f_key == "target": step = 250
        elif t_key == "points" and f_key == "reward": step = 50
        elif f_key == "reward": step = 10
        if action == "up":
            bot_config["quests"][t_key][f_key] += step
        else:
            bot_config["quests"][t_key][f_key] = max(1, bot_config["quests"][t_key][f_key] - step)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ تم!")
        q = bot_config["quests"]
        msg = (f"⚙️ <b>═══ إعدادات المهام ═══</b>\n\n"
               f"━━━━━━━━━━━━━━━\n"
               f"1️⃣ 👥 <b>الدعوات:</b>\n"
               f"   🎯 الهدف: {q['invite']['target']}\n"
               f"   🎁 الجائزة: {q['invite']['reward']}\n\n"
               f"2️⃣ 🛒 <b>المبيعات:</b>\n"
               f"   🎯 الهدف: {q['buy']['target']}\n"
               f"   🎁 الجائزة: {q['buy']['reward']}\n\n"
               f"3️⃣ 💎 <b>النقاط:</b>\n"
               f"   🎯 الهدف: {q['points']['target']}\n"
               f"   🎁 الجائزة: {q['points']['reward']}\n"
               f"━━━━━━━━━━━━━━━")
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("cfg_box_") or data.startswith("cfg_wheel_"):
        if not is_admin(uid, u):
            return bot.answer_callback_query(call.id, "❌ لا صلاحيات.", show_alert=True)
        if data == "cfg_box_price_up": bot_config["lootbox_price"] = bot_config.get("lootbox_price", 50) + 5
        elif data == "cfg_box_price_down": bot_config["lootbox_price"] = max(5, bot_config.get("lootbox_price", 50) - 5)
        elif data == "cfg_box_chance_up": bot_config["lootbox_chance"] = min(100, bot_config.get("lootbox_chance", 25) + 5)
        elif data == "cfg_box_chance_down": bot_config["lootbox_chance"] = max(1, bot_config.get("lootbox_chance", 25) - 5)
        elif data == "cfg_wheel_price_up": bot_config["wheel_price"] = bot_config.get("wheel_price", 40) + 5
        elif data == "cfg_wheel_price_down": bot_config["wheel_price"] = max(5, bot_config.get("wheel_price", 40) - 5)
        elif data == "cfg_wheel_chance_up": bot_config["wheel_chance"] = min(100, bot_config.get("wheel_chance", 5) + 1)
        elif data == "cfg_wheel_chance_down": bot_config["wheel_chance"] = max(1, bot_config.get("wheel_chance", 5) - 1)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ تم!")
        if "box" in data:
            msg = (f"⚙️ <b>═══ إعدادات صندوق الحظ ═══</b>\n\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"💸 <b>السعر:</b> {bot_config['lootbox_price']} نقطة\n"
                   f"📊 <b>نسبة الفوز:</b> {bot_config['lootbox_chance']}%\n"
                   f"━━━━━━━━━━━━━━━")
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("➕ سعر +5", callback_data="cfg_box_price_up"), types.InlineKeyboardButton("➖ سعر -5", callback_data="cfg_box_price_down"))
            markup.row(types.InlineKeyboardButton("📈 نسبة +5%", callback_data="cfg_box_chance_up"), types.InlineKeyboardButton("📉 نسبة -5%", callback_data="cfg_box_chance_down"))
        else:
            msg = (f"⚙️ <b>═══ إعدادات عجلة الحظ ═══</b>\n\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"💸 <b>السعر:</b> {bot_config['wheel_price']} نقطة\n"
                   f"📊 <b>الجائزة الكبرى:</b> {bot_config['wheel_chance']}%\n"
                   f"━━━━━━━━━━━━━━━")
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("➕ سعر +5", callback_data="cfg_wheel_price_up"), types.InlineKeyboardButton("➖ سعر -5", callback_data="cfg_wheel_price_down"))
            markup.row(types.InlineKeyboardButton("📈 نسبة +1%", callback_data="cfg_wheel_chance_up"), types.InlineKeyboardButton("📉 نسبة -1%", callback_data="cfg_wheel_chance_down"))
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    elif data == "game_buy_lootbox":
        price = bot_config.get("lootbox_price", 50)
        if (u.get("points", 0) or 0) < price:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
        update_user_data(uid, points=-price)
        chance = bot_config.get("lootbox_chance", 25)
        if random.randint(1, 100) <= chance:
            win = random.randint(100, 500)
            update_user_data(uid, points=win, accumulated_points=win)
            bot.edit_message_text(
                f"🎊 <b>═══ مبروك الفوز ═══</b>\n\n"
                f"🎁 <b>+{win}</b> نقطة",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(
                f"😔 <b>الصندوق فارغ</b>\n\n💪 حاول مجدداً!",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        update_user_rank_and_quests(uid)
        return

    elif data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if (u.get("points", 0) or 0) < price:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
        update_user_data(uid, points=-price)
        bot.answer_callback_query(call.id, "💫 جاري التدوير...")
        for frame in ["🎰 [ 🔁 يدور... ]", "🎡 [ 🔄 يتحرك... ]", "🎰 [ 🔁 يتوقف... ]"]:
            try:
                bot.edit_message_text(frame, call.message.chat.id, call.message.message_id)
                time.sleep(0.5)
            except: pass
        chance_grand = bot_config.get("wheel_chance", 5)
        if random.randint(1, 100) <= chance_grand:
            result = "GRAND"
        else:
            result = random.choice([0, 10, 20, price, price + 30])
        if result == "GRAND":
            win = 1000
            update_user_data(uid, points=win, accumulated_points=win)
            bot.edit_message_text(
                f"🏆 <b>═══ الجائزة الكبرى ═══</b>\n\n👑 <b>+1000 نقطة</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
            try:
                bot.send_message(CHANNEL_ID, 
                    f"🎡 <b>انفجار بالعجلة!</b>\n🏆 مستخدم فاز بـ +1000 نقطة\n🤖 t.me/{bot.get_me().username}", 
                    parse_mode="HTML")
            except: pass
        elif result > 0:
            update_user_data(uid, points=result, accumulated_points=result)
            bot.edit_message_text(
                f"🎡 <b>توقفت العجلة!</b>\n\n🎁 <b>+{result} نقطة</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(
                f"🎡 <b>توقفت العجلة!</b>\n\n💔 <b>0 نقطة</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        update_user_rank_and_quests(uid)
        return

    elif data == "refresh_shop":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        return show_shop_enhanced(call.message, uid, u)

    elif data.startswith("step_addkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"step_addkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\n\n⏱️ اختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_addkey_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(
            f"🔑 <b>إضافة مفاتيح</b>\n📦 {prod} | ⏱️ {plan}\n\n✍️ أرسل المفاتيح (كل واحد بسطر):",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_save_new_keys(msg, prod, plan))

    elif data.startswith("step_price_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            curr = prices_config.get(prod, {}).get(plan, 0)
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} ({curr})", callback_data=f"step_price_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\n\n⏱️ اختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_price_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"💵 <b>{prod}</b> | ⏱️ <b>{plan}</b>\n\n✍️ أرسل السعر الجديد:", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_save_new_price(msg, prod, plan))

    elif data.startswith("step_delkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            count = len(keys_store.get(prod, {}).get(plan, []))
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} ({count})", callback_data=f"step_delkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\n\n⏱️ اختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_delkey_plan|"):
        _, prod, plan = data.split("|")
        keys = keys_store.get(prod, {}).get(plan, [])
        if not keys:
            return bot.answer_callback_query(call.id, "❌ لا مفاتيح.", show_alert=True)
        m = bot.edit_message_text(f"🔢 <b>{prod}</b> | <b>{plan}</b>\n\n✍️ أرسل المفتاح أو رقمه:", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_delete_specific_key(msg, prod, plan))

    elif data == "confirm_open_ticket":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        m = bot.send_message(call.message.chat.id, "💬 اكتب رسالتك:")
        bot.register_next_step_handler(m, process_support_ticket)

    elif data == "confirm_send_prod_req":
        temp_reqs = bot_config.get("temp_req", {})
        if uid in temp_reqs:
            txt_req = temp_reqs[uid]
            req_id = str(random.randint(10000, 99999))
            if "product_requests" not in bot_config: bot_config["product_requests"] = {}
            bot_config["product_requests"][req_id] = {"uid": uid, "text": txt_req, "date": datetime.now().isoformat()}
            bot_config["temp_req"].pop(uid, None)
            save_json(DB_CONFIG, bot_config)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, f"✅ تم الإرسال! رقم: <code>#{req_id}</code>", parse_mode="HTML")
            try: bot.send_message(ADMIN_PRIMARY, f"💡 <b>#{req_id}</b>\n{uid}\n{txt_req}", parse_mode="HTML")
            except: pass
        else:
            bot.answer_callback_query(call.id, "❌ انتهت الصلاحية.", show_alert=True)

    elif data == "cancel_action":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "❌ ملغى.")

    elif data.startswith("view_ticket_"):
        t_id = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if t_id not in tickets:
            return bot.answer_callback_query(call.id, "❌ غير موجودة.", show_alert=True)
        t_info = tickets[t_id]
        msg = f"🎫 <b>#{t_id}</b>\n👤 {t_info['uid']}\n\n{t_info['text']}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💬 رد", callback_data=f"reply_ticket_{t_id}"), types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"close_ticket_{t_id}"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("reply_ticket_"):
        t_id = data.split("_")[2]
        m = bot.send_message(call.message.chat.id, f"✍️ ردك للتذكرة #{t_id}:")
        bot.register_next_step_handler(m, lambda msg: admin_send_reply_ticket_func(msg, t_id))
        bot.answer_callback_query(call.id)

    elif data.startswith("close_ticket_"):
        t_id = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if t_id in tickets:
            tickets[t_id]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
            try: bot.send_message(int(tickets[t_id]["uid"]), f"🔒 تم إغلاق تذكرتك #{t_id}")
            except: pass
            bot.edit_message_text(f"✅ أُغلقت #{t_id}", call.message.chat.id, call.message.message_id)

    elif data.startswith("adm_"):
        if not is_admin(uid, u):
            return bot.answer_callback_query(call.id, "❌ لا صلاحيات.", show_alert=True)
        parts = data.split("_")
        action, target_id = parts[1], parts[2]
        tgt_u = get_user(target_id)
        if not tgt_u:
            return bot.answer_callback_query(call.id, "❌ غير موجود.", show_alert=True)
        if action == "promote":
            update_user_data(target_id, is_admin=True)
            bot.answer_callback_query(call.id, "🛡️ ترقية!", show_alert=True)
        elif action == "demote":
            update_user_data(target_id, is_admin=False)
            bot.answer_callback_query(call.id, "⬇️ إزالة!", show_alert=True)
        elif action == "ban":
            update_user_data(target_id, banned=True)
            bot.answer_callback_query(call.id, "⛔ حظر!", show_alert=True)
        elif action == "tempban":
            until = datetime.now() + timedelta(days=1)
            update_user_data(target_id, banned_until=until.isoformat())
            bot.answer_callback_query(call.id, "⏱️ مؤقت!", show_alert=True)
        elif action == "unban":
            update_user_data(target_id, banned=False, banned_until=None)
            bot.answer_callback_query(call.id, "🟢 فك!", show_alert=True)
        tgt_u = get_user(target_id) or {}
        role = "مالك 👑" if int(target_id) == ADMIN_PRIMARY else ("أدمن 🛡️" if tgt_u.get("is_admin", False) else "عادي 👤")
        ban_st = "محظور ⛔" if tgt_u.get("banned", False) else ("مؤقت 🔴" if tgt_u.get("banned_until") else "نشط 🟢")
        msg = (f"👥 <b>═══ العضو ═══</b>\n\n"
               f"🆔 <code>{target_id}</code>\n📝 @{tgt_u.get('username', 'N/A')}\n"
               f"💰 {tgt_u.get('points', 0)} نقطة\n🎖️ {role}\n🔴 {ban_st}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        if tgt_u.get("is_admin", False):
            markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{target_id}"))
        else:
            markup.add(types.InlineKeyboardButton("🛡️ ترقية", callback_data=f"adm_promote_{target_id}"))
        markup.add(types.InlineKeyboardButton("⛔ حظر", callback_data=f"adm_ban_{target_id}"), types.InlineKeyboardButton("⏱️ 24س", callback_data=f"adm_tempban_{target_id}"))
        markup.add(types.InlineKeyboardButton("🟢 فك", callback_data=f"adm_unban_{target_id}"))
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass

    elif data.startswith("setlang_"):
        lang = data.split("_")[1]
        update_user_data(uid, lang=lang)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, 
            "✅ <b>تم تغيير اللغة!</b>\n🏠 القائمة الرئيسية", 
            reply_markup=get_main_keyboard(uid, lang, page=1), parse_mode="HTML")

    elif data == "check_join":
        if check_channel_join(uid):
            lang = u.get("lang", "ar")
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, 
                "✅ <b>═══ شكراً لاشتراكك ═══</b>\n\n🎉 حسابك مُفعّل!", 
                reply_markup=get_main_keyboard(uid, lang, page=1), parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

    elif data.startswith("select_prod_"):
        prod = data.split("_", 2)[2]
        if prod not in prices_config: return
        markup = types.InlineKeyboardMarkup()
        u_discount = u.get("rank_discount", 0.0) or 0.0
        info = (f"📦 <b>═══ {prod} ═══</b>\n\n"
                f"💎 خصمك: <b>{int(u_discount*100)}%</b>\n"
                f"💰 رصيدك: <b>{u.get('points', 0)}</b>\n\n"
                f"⏱️ اختر المدة:")
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_p = prices_config[prod].get(plan, 0)
            disc = bot_config.get("discount", 0)
            final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
            stock = len(keys_store.get(prod, {}).get(plan, []))
            emoji = "✅" if stock > 0 else "❌"
            markup.add(types.InlineKeyboardButton(f"{emoji} {plan} | {final_p} | 📊 {stock}", callback_data=f"buy_plan|{prod}|{plan}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="refresh_shop"))
        try: bot.edit_message_text(info, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: bot.send_message(call.message.chat.id, info, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("buy_plan|"):
        parts = data.split("|")
        prod, plan = parts[1], parts[2]
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config.get("discount", 0)
        u_discount = u.get("rank_discount", 0.0) or 0.0
        final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
        if (u.get("points", 0) or 0) < final_p:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, "⚠️ نفذت!", show_alert=True)
        key = keys_store[prod][plan].pop(0)
        update_user_data(uid, points=-final_p)
        bot_config["total_sales"] = bot_config.get("total_sales", 0) + 1
        bot_config["total_earnings"] = bot_config.get("total_earnings", 0) + final_p
        if "sales_log" not in bot_config: bot_config["sales_log"] = []
        bot_config["sales_log"].append({"uid": uid, "username": u.get("username", ""), "product": prod, "plan": plan, "price": final_p, "key": key, "date": datetime.now().isoformat()})
        save_json(DB_KEYS, keys_store)
        save_json(DB_CONFIG, bot_config)
        update_user_rank_and_quests(uid)
        bot.edit_message_text(
            f"🎉 <b>═══ تم الشراء ═══</b>\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📦 <b>{prod}</b>\n"
            f"⏱️ <b>{plan}</b>\n"
            f"💰 <b>{final_p}</b> نقطة\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"🔐 <b>مفتاحك:</b>\n<code>{key}</code>\n\n"
            f"⚠️ احفظه في مكان آمن!",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        try:
            bot.send_message(CHANNEL_ID, 
                f"🔥 <b>مبيعات جديدة!</b>\n📦 {prod} | ⏱️ {plan}\n💰 {final_p} نقطة\n🤖 t.me/{bot.get_me().username}", 
                parse_mode="HTML")
        except: pass

# =====================================================
# 📥 معالجات الإدخال
# =====================================================
def process_save_new_keys(message, prod, plan):
    keys = message.text.strip().split('\n')
    added = 0
    if prod not in keys_store:
        keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ <b>+{added} مفتاح</b>\n📦 {prod} | ⏱️ {plan}", parse_mode="HTML")

def process_save_new_price(message, prod, plan):
    try:
        new_price = int(message.text.strip())
        prices_config[prod][plan] = new_price
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ 📦 {prod} | {plan} = <b>{new_price}</b>", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ أرقام فقط!")

def process_delete_specific_key(message, prod, plan):
    val = message.text.strip()
    keys_list = keys_store.get(prod, {}).get(plan, [])
    if val.isdigit() and 0 < int(val) <= len(keys_list):
        removed = keys_list.pop(int(val) - 1)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ حُذف: <code>{removed}</code>", parse_mode="HTML")
    if val in keys_list:
        keys_list.remove(val)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ حُذف: <code>{val}</code>", parse_mode="HTML")
    bot.send_message(message.chat.id, "❌ لم يُعثر.")

def admin_view_member_func(message):
    t_id = message.text.strip()
    u = get_user(t_id)
    if not u:
        return bot.send_message(message.chat.id, "❌ غير موجود.")
    role = "مالك 👑" if int(t_id) == ADMIN_PRIMARY else ("أدمن 🛡️" if u.get("is_admin", False) else "عادي 👤")
    ban_st = "محظور ⛔" if u.get("banned", False) else "نشط 🟢"
    msg = (f"👥 <b>═══ العضو ═══</b>\n\n"
           f"🆔 <code>{t_id}</code>\n📝 @{u.get('username', 'N/A')}\n"
           f"💰 {u.get('points', 0)} نقطة\n🏆 {u.get('rank', 'عادي')}\n"
           f"🎖️ {role}\n🔴 {ban_st}")
    markup = types.InlineKeyboardMarkup(row_width=2)
    if u.get("is_admin", False):
        markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{t_id}"))
    else:
        markup.add(types.InlineKeyboardButton("🛡️ ترقية", callback_data=f"adm_promote_{t_id}"))
    markup.add(types.InlineKeyboardButton("⛔ حظر", callback_data=f"adm_ban_{t_id}"), types.InlineKeyboardButton("⏱️ 24س", callback_data=f"adm_tempban_{t_id}"))
    markup.add(types.InlineKeyboardButton("🟢 فك", callback_data=f"adm_unban_{t_id}"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def admin_confirm_fake_marketing(message):
    if not message.text.strip():
        return bot.send_message(message.chat.id, "❌ ملغى.")
    plan = random.choice(["1 Day", "7 Days", "30 Days"])
    fake_key = generate_fake_key()
    try:
        m = (f"🔥 <b>مبيعات جديدة!</b>\n\n📦 <code>Flourite Cheat</code>\n"
             f"⏱️ <b>{plan}</b>\n🔐 <code>{fake_key}</code>\n\n"
             f"🛒 t.me/{bot.get_me().username}")
        bot.send_message(CHANNEL_ID, m, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ نُشر {plan}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {e}")

def process_redeem_user(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in redeem_codes:
        added = redeem_codes.pop(code)
        update_user_data(uid, points=added, accumulated_points=added)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id, f"🎉 +<b>{added}</b> نقطة!", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ كود غير صحيح.")

def process_support_ticket(message):
    uid = str(message.from_user.id)
    txt = message.text.strip()
    if not txt: return bot.send_message(message.chat.id, "❌ فارغ!")
    tid = str(random.randint(10000, 99999))
    if "tickets" not in bot_config: bot_config["tickets"] = {}
    bot_config["tickets"][tid] = {"uid": uid, "text": txt, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ تذكرة #{tid} فُتحت!", parse_mode="HTML")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 رد", callback_data=f"reply_ticket_{tid}"), types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"close_ticket_{tid}"))
    try: bot.send_message(ADMIN_PRIMARY, f"🎫 <b>#{tid}</b>\n👤 {uid}\n📝 {txt}", reply_markup=markup, parse_mode="HTML")
    except: pass

def process_product_request_input(message):
    uid = str(message.from_user.id)
    txt = message.text.strip()
    if not txt: return bot.send_message(message.chat.id, "❌ فارغ!")
    if "temp_req" not in bot_config: bot_config["temp_req"] = {}
    bot_config["temp_req"][uid] = txt
    save_json(DB_CONFIG, bot_config)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ إرسال", callback_data="confirm_send_prod_req"), types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action"))
    bot.send_message(message.chat.id, f"⚠️ <b>تأكيد؟</b>\n\n📦 {txt}", reply_markup=markup, parse_mode="HTML")

def admin_send_reply_ticket_func(message, tid):
    tickets = bot_config.get("tickets", {})
    if tid not in tickets: return bot.send_message(message.chat.id, "❌ غير موجودة.")
    reply = message.text.strip()
    try:
        bot.send_message(int(tickets[tid]["uid"]), f"💬 <b>رد #{tid}:</b>\n\n{reply}", parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ أُرسل #{tid}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {e}")

def admin_add_product_func(message):
    prod = message.text.strip()
    if prod in prices_config:
        return bot.send_message(message.chat.id, "❌ موجود.")
    prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
    keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"➕ أُضيف: <b>{prod}</b>", parse_mode="HTML")

def admin_delete_product_func(message):
    prod = message.text.strip()
    if prod not in prices_config:
        return bot.send_message(message.chat.id, "❌ غير موجود.")
    prices_config.pop(prod)
    if prod in keys_store: keys_store.pop(prod)
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ حُذف: <b>{prod}</b>", parse_mode="HTML")

def admin_charge_member_func(message):
    try:
        parts = message.text.strip().split()
        t_id, pts = parts[0], int(parts[1])
        if get_user(t_id):
            update_user_data(t_id, points=pts, accumulated_points=pts)
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 شُحن {t_id} بـ +{pts}")
            try: bot.send_message(int(t_id), f"🎉 <b>+{pts} نقطة</b> من الإدارة!", parse_mode="HTML")
            except: pass
        else:
            bot.send_message(message.chat.id, "❌ غير موجود.")
    except:
        bot.send_message(message.chat.id, "❌ صيغة: ID مسافة القيمة")

def admin_create_code_func(message):
    try:
        parts = message.text.strip().split()
        code, pts = parts[0], int(parts[1])
        redeem_codes[code] = pts
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 <code>{code}</code> = {pts}", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ صيغة: CODE مسافة القيمة")

def admin_set_discount_func(message):
    try:
        disc = int(message.text.strip())
        if 0 <= disc < 100:
            bot_config["discount"] = disc
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 خصم عام: {disc}%")
        else:
            bot.send_message(message.chat.id, "❌ 0-99")
    except:
        bot.send_message(message.chat.id, "❌ أرقام فقط.")

def admin_broadcast_func(message):
    txt = message.text
    success = 0
    for u_id in get_all_user_ids():
        try:
            bot.send_message(int(u_id), txt)
            success += 1
            time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"📢 أُذيع لـ {success} عضو.")

def admin_edit_daily_bonus(message):
    try:
        new_val = int(message.text.strip())
        if new_val >= 0:
            bot_config["daily_gift"] = new_val
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, 
                f"✅ <b>المكافأة اليومية:</b> <b>{new_val}</b> نقطة", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ قيمة موجبة!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ أرقام فقط.")

def admin_edit_invite_reward(message):
    try:
        new_val = int(message.text.strip())
        if new_val >= 0:
            bot_config["invite_reward"] = new_val
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, 
                f"✅ <b>نقاط الإحالة:</b> <b>{new_val}</b> نقطة", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ قيمة موجبة!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ أرقام فقط.")

# =====================================================
if __name__ == "__main__":
    print("🚀 البوت يعمل بجميع المميزات!")
    bot.infinity_polling(none_stop=True, timeout=60)
