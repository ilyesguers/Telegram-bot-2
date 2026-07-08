import telebot
from telebot import types
import random
import os
import time
import json
from datetime import datetime, timedelta

# استدعاء الملفات المقسمة (محدث ليتوافق مع دوال قاعدة البيانات الجديدة)
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, LOCALES
from database import engine, text, init_db, get_user, update_user_data, register_user, keys_store, redeem_codes, prices_config, bot_config, save_json, DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG, update_user_rank_and_quests
from utils import check_spam, is_user_banned, check_channel_join, generate_fake_key
from keyboards import get_lang_inline, get_join_inline, get_main_keyboard, get_admin_keyboard

# -------------------------------------------------------------
# 🔄 دالة تنظيف النصوص لحل مشكلة عدم استجابة الأزرار
# -------------------------------------------------------------
def clean_text(text_str):
    if not text_str:
        return ""
    # إزالة الرموز المخفية والمسافات الزائدة لضمان تطابق الأزرار 100%
    return " ".join(text_str.strip().replace('\ufe0f', '').split())

# -------------------------------------------------------------
# 🔄 نقل البيانات من ملف JSON القديم إلى قاعدة البيانات (يعمل تلقائياً)
# -------------------------------------------------------------
try:
    init_db()
    if os.path.exists(DB_USERS):
        with open(DB_USERS, "r", encoding="utf-8") as f:
            old_users = json.load(f)
            with engine.connect() as conn:
                for old_uid, u_data in old_users.items():
                    res = conn.execute(text("SELECT uid FROM users WHERE uid = :uid"), {"uid": str(old_uid)}).fetchone()
                    if not res:
                        conn.execute(text("""
                            INSERT INTO users (uid, username, points, accumulated_points, lang, rank, rank_discount, invite_count, completed_quests, invited_by, last_claim, banned, banned_until, is_admin)
                            VALUES (:uid, :username, :points, :accumulated_points, :lang, :rank, :rank_discount, :invite_count, :completed_quests, :invited_by, :last_claim, :banned, :banned_until, :is_admin)
                        """), {
                            "uid": str(old_uid),
                            "username": u_data.get("username", ""),
                            "points": u_data.get("points", 0),
                            "accumulated_points": u_data.get("accumulated_points", 0),
                            "lang": u_data.get("lang", "ar"),
                            "rank": u_data.get("rank", "عضو عادي 🔹"),
                            "rank_discount": float(u_data.get("rank_discount", 0.0)),
                            "invite_count": u_data.get("invite_count", 0),
                            "completed_quests": str(u_data.get("completed_quests", "")),
                            "invited_by": u_data.get("invited_by"),
                            "last_claim": u_data.get("last_claim"),
                            "banned": u_data.get("banned", False),
                            "banned_until": u_data.get("banned_until"),
                            "is_admin": u_data.get("is_admin", False)
                        })
                conn.commit()
        print("✅ تم التأكد من دمج بيانات ملف users.json القديمة داخل قاعدة البيانات بنجاح.")
except Exception as e:
    print(f"⚠️ خطأ أثناء نقل البيانات القديمة: {e}")

def get_all_user_ids():
    with engine.connect() as conn:
        return [str(r[0]) for r in conn.execute(text("SELECT uid FROM users")).fetchall()]
# -------------------------------------------------------------

@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")

    u = get_user(uid) or {}
    
    if message.text.startswith('/id'):
        if not check_channel_join(uid):
            lang = u.get("lang", "ar")
            return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك هو: <code>{uid}</code>", parse_mode="HTML")
        return

    args = message.text.split()
    if len(args) > 1 and u.get("invited_by") is None:
        inviter_id = args[1]
        if get_user(inviter_id) and inviter_id != uid:
            update_user_data(uid, invited_by=inviter_id)
            update_user_data(inviter_id, points=bot_config["invite_reward"], accumulated_points=bot_config["invite_reward"], invite_count=1)
            update_user_rank_and_quests(inviter_id)
            try: bot.send_message(int(inviter_id), f"🔗 لقد إنضم مستخدم جديد عن طريق رابط الإحالة الخاص بك! حصلت على {bot_config['invite_reward']} نقاط.")
            except: pass

    if not check_channel_join(uid):
        lang = u.get("lang", "ar")
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    bot.send_message(message.chat.id, LOCALES["ar"]["welcome"], reply_markup=get_lang_inline())

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")
        
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    # تطبيق التنظيف والتحقق الذكي هنا
    txt = clean_text(message.text)

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config["maintenance"] and not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)):
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    # فحص أزرار لوحة المشرف الفرعية أولاً لمنع أي تداخل نصي
    if (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)) and ("التالي للمشرف" in txt or "التالي للمشرف" in message.text):
        return bot.send_message(message.chat.id, "⚙️ لوحة تحكم إعدادات الألعاب التسويقية الجديدة لمشرفي النظام:", reply_markup=get_admin_keyboard(page=2))
        
    elif (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)) and ("سابق المشرف" in txt or "سابق للمشرف" in txt or "سابق المشرف" in message.text):
        return bot.send_message(message.chat.id, "👑 لوحة التحكم والميزات الرئيسية للإدارة:", reply_markup=get_admin_keyboard(page=1))

    # فحص أزرار التنقل للمستخدم العادي
    elif "التالي" in txt or "التالي" in message.text:
        return bot.send_message(message.chat.id, "🎡 ميزات التسلية والمهام التسويقية الإبداعية المضافة حديثاً للمتجر:", reply_markup=get_main_keyboard(uid, lang, page=2))
        
    elif "السابق" in txt or "السابق" in message.text:
        return bot.send_message(message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))

    elif "صندوق الحظ" in txt or "صندوق الحظ" in message.text:
        price = bot_config.get("lootbox_price", 50)
        chance = bot_config.get("lootbox_chance", 25)
        msg = (f"🎰 <b>صناديق الحظ العشوائية (Loot Boxes):</b>\n\n"
               f"قم بفتح صندوق حظ عشوائي الآن وجرب مغامرة الحظ الحقيقية لتكسب مئات النقاط الفورية!\n\n"
               f"💸 سعر فتح الصندوق: <b>{price} نقطة</b>\n"
               f"📈 نسبة الفوز المقررة: <b>{chance}%</b>\n\n"
               f"🎁 الجائزة الكبرى المخبأة: <b>شحن عشوائي فوري من +100 إلى +500 نقطة!</b>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 فتح صندوق حظ الآن", callback_data="game_buy_lootbox"))
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    elif "عجلة الحظ" in txt or "عجلة الحظ" in message.text:
        price = bot_config.get("wheel_price", 40)
        msg = (f"🎡 <b>عجلة الحظ المدفوعة التفاعلية:</b>\n\n"
               f"أدر العجلة الآن وشاهد حظك وهو يتحرك مباشرة أمامك للربح!\n\n"
               f"💸 سعر تدوير اللفة: <b>{price} نقطة</b>\n"
               f"🎁 الجوائز المتاحة بالعجلة: 0 Pts | 10 Pts | 20 Pts | مساوي سعر اللفة | 🏆 <b>الجائزة الكبرى (+1000 نقطة كاملة)</b>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💫 تدوير عجلة الحظ الآن", callback_data="game_spin_wheel"))
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    elif "المهام الصعبة" in txt or "المهام" in txt or "المهام الصعبة" in message.text:
        update_user_rank_and_quests(uid)
        u = get_user(uid)
        completed = u.get("completed_quests", "")
        invite_cnt = u.get("invite_count", 0)
        user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
        acc_pts = u.get("accumulated_points", 0)
        q = bot_config.get("quests")
        
        msg = "🔥 <b>قائمة المهام والانجازات المتوفرة بالمتجر:</b>\n\n"
        
        st1 = "✅ مكتمل ومستلم" if "quest_invite" in completed else f"⏳ قيد التقدم ({invite_cnt}/{q['invite']['target']})"
        msg += f"1️⃣ 👥 دعوة {q['invite']['target']} صديقاً عبر رابط الإحالة الخاص بك\n🎁 الجائزة: +{q['invite']['reward']} نقطة | الحالة: <b>{st1}</b>\n──────────────────\n"
        
        st2 = "✅ مكتمل ومستلم" if "quest_buy" in completed else f"⏳ قيد التقدم ({user_buys}/{q['buy']['target']})"
        msg += f"2️⃣ 🛒 إتمام {q['buy']['target']} عمليات شراء ناجحة من المتجر\n🎁 الجائزة: +{q['buy']['reward']} نقطة | الحالة: <b>{st2}</b>\n──────────────────\n"
        
        st3 = "✅ مكتمل ومستلم" if "quest_points" in completed else f"⏳ قيد التقدم ({acc_pts}/{q['points']['target']})"
        msg += f"3️⃣ 💎 تجميع {q['points']['target']} نقطة إجمالاً in حسابك (مجمعة)\n🎁 الجائزة: +{q['points']['reward']} نقطة | الحالة: <b>{st3}</b>\n"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif "رتبتي الحالية" in txt or "رتبتي" in txt or "الرتبة" in txt:
        update_user_rank_and_quests(uid)
        u = get_user(uid)
        r_name = u.get("rank", "عضو عادي 🔹")
        r_disc = int(u.get("rank_discount", 0.0) * 100)
        acc_pts = u.get("accumulated_points", 0)
        
        msg = (f"🏆 <b>نظام ترقية رتب العميل والمكافآت التلقائي:</b>\n\n"
               f"• رتبتك الحالية في النظام: <b>{r_name}</b>\n"
               f"• نسبة خصم الرتبة الثابت لك: <b>{r_disc}%</b> من سعر أي منتج!\n"
               f"• مجموع نقاطك التراكمية التاريخية: <code>{acc_pts}</code> نقطة\n\n"
               f"📋 <b>قائمة ترتيب مستويات رانك المتجر وعتباتها:</b>\n"
               f"🥈 رتبة الفضي: تبدأ من 200 نقطة مجمعة (خصم 1%)\n"
               f"🥇 رتبة الذهبي: تبدأ من 600 نقطة مجمعة (خصم 2%)\n"
               f"💎 رتبة الماسي: تبدأ من 1500 نقطة مجمعة (خصم 3%)\n"
               f"⚡ رتبة الهيرو: تبدأ من 3500 نقطة مجمعة (خصم 4%)\n"
               f"👑 رتبة الماستر: تبدأ من 7000 نقطة مجمعة (خصم 4.5%)\n"
               f"🏆 رتبة الأسطورة: تبدأ من 12000 نقطة مجمعة (خصم 5% وهو أقصى حد خصم مقرر)\n\n"
               f"💡 نصيحة: استمر في تجميع وشحن النقاط لرفع رانك حسابك آلياً والاستمتاع بالخصومات الثابتة!")
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif ("إعدادات صندوق الحظ" in txt or "صندوق الحظ" in txt) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)) and "إعدادات" in txt:
        price = bot_config.get("lootbox_price", 50)
        chance = bot_config.get("lootbox_chance", 25)
        msg = (f"⚙️ <b>لوحة ضبط صندوق الحظ (التحكم بالخانات بدون أوامر):</b>\n\n"
               f"• سعر الصندوق الحالي: <b>{price} نقطة</b>\n"
               f"• نسبة فوز الجائزة الكبرى: <b>{chance}%</b>")
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("➕ سعر أعلى (+5)", callback_data="cfg_box_price_up"),
            types.InlineKeyboardButton("➖ سعر أقل (-5)", callback_data="cfg_box_price_down")
        )
        markup.row(
            types.InlineKeyboardButton("📈 نسبة أعلى (+5%)", callback_data="cfg_box_chance_up"),
            types.InlineKeyboardButton("📉 نسبة أقل (-5%)", callback_data="cfg_box_chance_down")
        )
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    elif ("إعدادات عجلة الحظ" in txt or "عجلة الحظ" in txt) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)) and "إعدادات" in txt:
        price = bot_config.get("wheel_price", 40)
        chance = bot_config.get("wheel_chance", 5)
        msg = (f"⚙️ <b>لوحة ضبط عجلة الحظ المخصصة (التحكم بالخانات بدون أوامر):</b>\n\n"
               f"• سعر لفة العجلة الحالي: <b>{price} نقطة</b>\n"
               f"• نسبة فوز الجائزة الكبرى العشوائية: <b>{chance}%</b>")
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("➕ سعر اللفة أعلى (+5)", callback_data="cfg_wheel_price_up"),
            types.InlineKeyboardButton("➖ سعر اللفة أقل (-5)", callback_data="cfg_wheel_price_down")
        )
        markup.row(
            types.InlineKeyboardButton("📈 النسبة الكبرى أعلى (+1%)", callback_data="cfg_wheel_chance_up"),
            types.InlineKeyboardButton("📉 النسبة الكبرى أقل (-1%)", callback_data="cfg_wheel_chance_down")
        )
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    elif ("إعدادات المهام الصعبة" in txt or "المهام الصعبة" in txt) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)) and "إعدادات" in txt:
        q = bot_config["quests"]
        msg = (f"⚙️ <b>لوحة التحكم بالمهام (تعديل مباشر بالأزرار وبدون أوامر):</b>\n\n"
               f"1️⃣ <b>👥 مهمة الدعوات:</b>\n• الهدف الحالي: {q['invite']['target']} عضو | الجائزة: {q['invite']['reward']} نقطة\n\n"
               f"2️⃣ <b>🛒 مهمة المبيعات:</b>\n• الهدف الحالي: {q['buy']['target']} شراء | الجائزة: {q['buy']['reward']} نقطة\n\n"
               f"3️⃣ <b>💎 مهمة النقاط التراكمية:</b>\n• الهدف الحالي: {q['points']['target']} نقطة | الجائزة: {q['points']['reward']} نقطة\n\n"
               f"💡 اضغط على الأزرار بالأسفل لتغيير الأهداف والجوائز فوراً وبكل سهولة:")
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("👥 هدف الدعوات ➖", callback_data="cfg_q_inv_t_down"), types.InlineKeyboardButton("👥 هدف الدعوات ➕", callback_data="cfg_q_inv_t_up"))
        markup.row(types.InlineKeyboardButton("🎁 جائزة الدعوات ➖", callback_data="cfg_q_inv_r_down"), types.InlineKeyboardButton("🎁 جائزة الدعوات ➕", callback_data="cfg_q_inv_r_up"))
        markup.row(types.InlineKeyboardButton("🛒 هدف الشراء ➖", callback_data="cfg_q_buy_t_down"), types.InlineKeyboardButton("🛒 هدف الشراء ➕", callback_data="cfg_q_buy_t_up"))
        markup.row(types.InlineKeyboardButton("🎁 جائزة الشراء ➖", callback_data="cfg_q_buy_r_down"), types.InlineKeyboardButton("🎁 جائزة الشراء ➕", callback_data="cfg_q_buy_r_up"))
        markup.row(types.InlineKeyboardButton("💎 هدف النقاط ➖", callback_data="cfg_q_pts_t_down"), types.InlineKeyboardButton("💎 هدف النقاط ➕", callback_data="cfg_q_pts_t_up"))
        markup.row(types.InlineKeyboardButton("🎁 جائزة النقاط ➖", callback_data="cfg_q_pts_r_down"), types.InlineKeyboardButton("🎁 جائزة النقاط ➕", callback_data="cfg_q_pts_r_up"))
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    # فحص أزرار LOCALES والأسماء المختلفة للمستخدم بشكل مرن للغاية لمنع أي تعطل
    elif any(clean_text(LOCALES[l]["id_btn"]) in txt or "آيدي" in txt or "id" in txt or "المعرف" in txt for l in LOCALES):
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك: <code>{uid}</code>", parse_mode="HTML")

    elif any(clean_text(LOCALES[l]["balance_btn"]) in txt or "رصيد" in txt or "حسابي" in txt or "النقاط" in txt for l in LOCALES):
        update_user_rank_and_quests(uid)
        u = get_user(uid)
        msg = f"💰 <b>بيانات رصيدك وحسابك:</b>\n\n• ID: {uid}\n• رصيد النقاط: {u['points']} نقطة\n• الرتبة الحالية: {u.get('rank', 'عضو عادي 🔹')}\n• عدد الدعوات الناجحة: {u.get('invite_count', 0)}\n• لغة البوت الحالية: {u['lang'].upper()}\n• حالة الحظر: نشط 🟢"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif any(clean_text(LOCALES[l]["lang_btn"]) in txt or "اللغة" in txt or "لغة" in txt or "lang" in txt for l in LOCALES):
        bot.send_message(message.chat.id, "🌐 اختر لغة البوت المفضلة لديك:", reply_markup=get_lang_inline())

    # تعديل المكافأة اليومية هنا لتقبل أسماء مختلفة وتتحول برمجياً إلى daily_gift
    elif any(clean_text(LOCALES[l]["bonus_btn"]) in txt or "هدية" in txt or "مكافأة" in txt or "يومية" in txt or "bonus" in txt or "gift" in txt for l in LOCALES):
        now = datetime.now()
        lc = u.get("last_claim")
        if lc and now < datetime.fromisoformat(lc) + timedelta(days=1):
            bot.send_message(message.chat.id, "❌ لقد استلمت المكافأة اليومية بالفعل، يرجى المحاولة بعد انتهاء 24 ساعة.")
        else:
            update_user_data(uid, last_claim=now.isoformat(), points=bot_config["daily_gift"], accumulated_points=bot_config["daily_gift"])
            update_user_rank_and_quests(uid)
            bot.send_message(message.chat.id, f"✨ تم استلام مكافأتك اليومية بنجاح وهي +{bot_config['daily_gift']} نقاط!")

    elif any(clean_text(LOCALES[l]["invite_btn"]) in txt or "دعوة" in txt or "رابط" in txt or "احالة" in txt or "invite" in txt for l in LOCALES):
        bot_user = bot.get_me().username
        link = f"https://t.me/{bot_user}?start={uid}"
        bot.send_message(message.chat.id, f"🔗 <b>نظام الدعوات:</b>\n\nقم بنسخ رابط الإحالة الخاص بك وأرسله لأصدقائك للحصول على نقاط مجانية عند تسجيلهم:\n<code>{link}</code>\n\n🎁 مكافأة الدعوة الحالية: <b>{bot_config['invite_reward']} نقطة</b>", parse_mode="HTML")

    elif any(clean_text(LOCALES[l]["redeem_btn"]) in txt or "شحن" in txt or "كود" in txt or "تفعيل" in txt or "redeem" in txt for l in LOCALES):
        m = bot.send_message(message.chat.id, "🎁 الرجاء إدخال كود الشحن لإضافة الرصيد تلقائياً:")
        bot.register_next_step_handler(m, process_redeem_user)

    elif any(clean_text(LOCALES[l]["support_btn"]) in txt or "دعم" in txt or "تذكرة" in txt or "تواصل" in txt or "الدعم" in txt for l in LOCALES):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ نعم، فتح تذكرة", callback_data="confirm_open_ticket"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
        )
        bot.send_message(message.chat.id, "⚠️ <b>تأكيد فتح تذكرة:</b>\nهل أنت متأكد من رغبتك في فتح تذكرة دعم فني جديدة؟", reply_markup=markup, parse_mode="HTML")

    elif any(clean_text(LOCALES[l]["req_prod_btn"]) in txt or "طلب منتج" in txt or "اقتراح" in txt or "منتج جديد" in txt for l in LOCALES):
        m = bot.send_message(message.chat.id, "💡 من فضلك اكتب اسم وتفاصيل المنتج الذي ترغب في إضافته للمتجر بالتفصيل:")
        bot.register_next_step_handler(m, process_product_request_input)

    elif any(clean_text(LOCALES[l]["shop_btn"]) in txt or "متجر" in txt or "المنتجات" in txt or "شراء" in txt or "shop" in txt for l in LOCALES):
        if not prices_config:
            return bot.send_message(message.chat.id, "📭 لا توجد منتجات متوفرة بالمتجر حالياً.")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"select_prod_{prod}"))
        bot.send_message(message.chat.id, "🛍️ <b>متجر المنتجات</b>\nالرجاء اختيار المنتج المراد تصفحه:", reply_markup=markup, parse_mode="HTML")

    elif any(clean_text(LOCALES[l]["admin_btn"]) in txt or "لوحة" in txt or "ادارة" in txt or "التحكم" in txt for l in LOCALES) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 مرحباً بك في لوحة تحكم ميزات الإدارة للمتجر:", reply_markup=get_admin_keyboard(page=1))

    # أزرار لوحة تحكم الإدارة الكاملة بنظام البحث النصي الفرعي
    elif int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
        if "واجهة المستخدم" in txt:
            bot.send_message(message.chat.id, "🔙 تم الانتقال إلى واجهة المستخدم العادية.", reply_markup=get_main_keyboard(uid, lang, page=1))

        elif "إدارة التذاكر" in txt or "تذاكر" in txt:
            tickets = bot_config.get("tickets", {})
            open_tickets = {k: v for k, v in tickets.items() if v.get("status", "open") == "open"}
            if not open_tickets:
                return bot.send_message(message.chat.id, "🎉 لا توجد تذاكر دعم مفتوحة حالياً.")
            markup = types.InlineKeyboardMarkup()
            for t_id, t_info in open_tickets.items():
                markup.add(types.InlineKeyboardButton(f"🎫 #{t_id} - من: {t_info['uid']}", callback_data=f"view_ticket_{t_id}"))
            bot.send_message(message.chat.id, "👇 <b>قائمة التذاكر المفتوحة حالياً:</b>", reply_markup=markup, parse_mode="HTML")

        elif "طلب" in txt and "منتج" in txt or "طلبات المنتجات" in txt:
            reqs = bot_config.get("product_requests", {})
            if not reqs:
                return bot.send_message(message.chat.id, "📭 لا توجد طلبات منتجات مقدمة من المستخدمين حالياً.")
            msg = "💡 <b>قائمة طلبات المنتجات الواردة من المستخدمين:</b>\n\n"
            for r_id, r_info in reqs.items():
                msg += f"🔹 <b>طلب #{r_id}</b>\n👤 العضو: <code>{r_info['uid']}</code>\n📦 المنتج المطلوب:\n<code>{r_info['text']}</code>\n📅 التاريخ: {r_info.get('date','')[:10]}\n──────────────────\n"
            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        elif "إضافة منتج" in txt or "اضافة منتج" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج الجديد:")
            bot.register_next_step_handler(m, admin_add_product_func)

        elif "حذف منتج" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج المراد حذفه بالكامل:")
            bot.register_next_step_handler(m, admin_delete_product_func)

        elif "إضافة مفاتيح" in txt or "اضافة مفاتيح" in txt:
            if not prices_config:
                return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد، قم بإضافة منتج أولاً.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys():
                markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_addkey_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 <b>اختر المنتج الذي تريد إضافة مفاتيح له:</b>", reply_markup=markup, parse_mode="HTML")

        elif "إدارة الأسعار" in txt or "الأسعار" in txt or "الاسعار" in txt:
            if not prices_config:
                return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys():
                markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_price_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 <b>اختر المنتج الذي تريد تعديل أسعاره:</b>", reply_markup=markup, parse_mode="HTML")

        elif "حذف مفتاح معين" in txt or "حذف مفتاح" in txt:
            if not prices_config:
                return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys():
                markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_delkey_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 <b>اختر المنتج الذي تريد حذف مفتاح منه:</b>", reply_markup=markup, parse_mode="HTML")

        elif "استعراض المفاتيح" in txt or "المفاتيح" in txt:
            status = "🔑 <b>جميع المفاتيح المخزنة في النظام:</b>\n\n"
            for prod, plans in keys_store.items():
                status += f"📦 <b>{prod}:</b>\n"
                for plan, lst in plans.items():
                    status += f" ├ {plan}: {len(lst)} مفتاح متوفر\n"
            bot.send_message(message.chat.id, status, parse_mode="HTML")

        elif "مسح جميع المفاتيح" in txt or "مسح المفاتيح" in txt:
            keys_store.clear()
            for prod in prices_config.keys(): keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
            save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, "🗑️ تم مسح جميع المفاتيح المخزنة دفعة واحدة بنجاح.")

        elif "إدارة الأعضاء" in txt or "الاعضاء" in txt or "الأعضاء" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو لعرض تفاصيله والتحكم في رتبته وحظره بالأزرار:")
            bot.register_next_step_handler(m, admin_view_member_func)

        elif "شحن الأعضاء" in txt or "شحن" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي المستخدم ثم مسافة ثم القيمة (مثال: 123456789 500):")
            bot.register_next_step_handler(m, admin_charge_member_func)

        elif "إنشاء أكواد الشحن" in txt or "اكواد الشحن" in txt or "إنشاء كود" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل الكود المراد إنشاؤه متبوعاً بقيمته (مثال: FREE100 100):")
            bot.register_next_step_handler(m, admin_create_code_func)

        elif "التخفيضات" in txt or "خصم" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل النسبة المئوية الجديدة للتخفيض العام (مثال: 10 أو 20 أو 50):")
            bot.register_next_step_handler(m, admin_set_discount_func)

        elif "الإذاعة الشاملة" in txt or "اذاعة" in txt or "الإذاعة" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل نص الرسالة التي ترغب بإذاعتها لجميع الأعضاء:")
            bot.register_next_step_handler(m, admin_broadcast_func)

        elif "نشر الأسعار بالقناة" in txt or "نشر الاسعار" in txt:
            pub_text = "📢 <b>قائمة أسعار ومفاتيح المتجر المتوفرة لدينا:</b>\n\n"
            for prod, plans in prices_config.items():
                pub_text += f"📦 <b>المنتج: {prod}</b>\n"
                for plan, b_price in plans.items():
                    disc = bot_config["discount"]
                    f_price = int(b_price * (1 - disc/100))
                    pub_text += f" ├ {plan} ➡️ {f_price} نقطة \n"
            pub_text += f"\n🤖 رابط البوت الرسمي للشراء الفوري: t.me/{bot.get_me().username}"
            try:
                bot.send_message(CHANNEL_ID, pub_text, parse_mode="HTML")
                bot.send_message(message.chat.id, "✅ تم نشر وتحديث قائمة الأسعار الحالية في القناة.")
            except: bot.send_message(message.chat.id, "❌ حدث خطأ، يرجى تحقق من صلاحيات البوت بالقناة.")

        elif "التسويق الوهمي" in txt or "تسويق" in txt:
            m = bot.send_message(message.chat.id, "⚠️ <b>تأكيد الإجراء:</b> من فضلك اكتب كلمة عشوائية أو كلمة <code>تأكيد</code> لتفادي إرسال منشور التسويق الوهمي بالغلط إلى القناة:", parse_mode="HTML")
            bot.register_next_step_handler(m, admin_confirm_fake_marketing)

        elif "تعديل المكافأة اليومية" in txt or "تعديل الهدية" in txt or "المكافأة اليومية" in txt:
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية للمكافأة: {bot_config['daily_gift']} نقطة.\n\n✍️ أرسل القيمة الجديدة الآن (أرقام فقط):")
            bot.register_next_step_handler(m, admin_edit_daily_bonus)

        elif "تعديل نقاط الدعوة" in txt or "نقاط الدعوة" in txt:
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية لنقاط الدعوة: {bot_config['invite_reward']} نقطة.\n\n✍️ أرسل القيمة الجديدة الآن (أرقام فقط):")
            bot.register_next_step_handler(m, admin_edit_invite_reward)

        elif "النسخ الاحتياطي" in txt or "النسخ" in txt or "إحصائيات" in txt:
            stats = (f"📊 <b>إحصائيات وتقارير المتجر الحالية:</b>\n\n"
                     f"👥 عدد المستخدمين المسجلين: {len(get_all_user_ids())}\n"
                     f"🛒 إجمالي عدد المبيعات: {bot_config.get('total_sales', 0)}\n"
                     f"💰 إجمالي الأرباح المكتسبة: {bot_config.get('total_earnings', 0)} نقطة")
            bot.send_message(message.chat.id, stats, parse_mode="HTML")
            for file_name in [DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
                if os.path.exists(file_name):
                    with open(file_name, "rb") as f_doc:
                        bot.send_document(message.chat.id, f_doc)

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    u = get_user(uid) or {}
    data = call.data

    if data != "check_join":
        if not check_channel_join(uid):
            lang = u.get("lang", "ar")
            try: bot.answer_callback_query(call.id, LOCALES[lang]["must_join"], show_alert=True)
            except: pass
            return bot.send_message(call.message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if data.startswith("cfg_q_"):
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات مسؤول.", show_alert=True)
        
        parts = data.split("_")
        task_type = parts[2] 
        field_type = parts[3] 
        action = parts[4] 
        
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
        bot.answer_callback_query(call.id, "⚙️ تم تحديث المهمة!")
        
        q = bot_config["quests"]
        msg = (f"⚙️ <b>لوحة التحكم بالمهام (تعديل مباشر بالأزرار وبدون أوامر):</b>\n\n"
               f"1️⃣ <b>👥 مهمة الدعوات:</b>\n• الهدف الحالي: {q['invite']['target']} عضو | الجائزة: {q['invite']['reward']} نقطة\n\n"
               f"2️⃣ <b>🛒 مهمة المبيعات:</b>\n• الهدف الحالي: {q['buy']['target']} شراء | الجائزة: {q['buy']['reward']} نقطة\n\n"
               f"3️⃣ <b>💎 مهمة النقاط التراكمية:</b>\n• الهدف الحالي: {q['points']['target']} نقطة | الجائزة: {q['points']['reward']} نقطة\n\n"
               f"💡 اضغط على الأزرار بالأسفل لتغيير الأهداف والجوائز فوراً وبكل سهولة:")
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("cfg_box_") or data.startswith("cfg_wheel_"):
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات مسؤول لاستخدام هذا الإجراء.", show_alert=True)
            
        if data == "cfg_box_price_up": bot_config["lootbox_price"] += 5
        elif data == "cfg_box_price_down": bot_config["lootbox_price"] = max(5, bot_config["lootbox_price"] - 5)
        elif data == "cfg_box_chance_up": bot_config["lootbox_chance"] = min(100, bot_config["lootbox_chance"] + 5)
        elif data == "cfg_box_chance_down": bot_config["lootbox_chance"] = max(1, bot_config["lootbox_chance"] - 5)
        
        elif data == "cfg_wheel_price_up": bot_config["wheel_price"] += 5
        elif data == "cfg_wheel_price_down": bot_config["wheel_price"] = max(5, bot_config["wheel_price"] - 5)
        elif data == "cfg_wheel_chance_up": bot_config["wheel_chance"] = min(100, bot_config["wheel_chance"] + 1)
        elif data == "cfg_wheel_chance_down": bot_config["wheel_chance"] = max(1, bot_config["wheel_chance"] - 1)
        
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "⚙️ تم تحديث البيانات بنجاح!")
        
        if "box" in data:
            msg = f"⚙️ <b>لوحة ضبط صندوق الحظ (التحكم بالخانات بدون أوامر):</b>\n\n• سعر الصندوق الحالي: <b>{bot_config['lootbox_price']} نقطة</b>\n• نسبة فوز الجائزة الكبرى: <b>{bot_config['lootbox_chance']}%</b>"
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("➕ سعر أعلى (+5)", callback_data="cfg_box_price_up"), types.InlineKeyboardButton("➖ سعر أقل (-5)", callback_data="cfg_box_price_down"))
            markup.row(types.InlineKeyboardButton("📈 نسبة أعلى (+5%)", callback_data="cfg_box_chance_up"), types.InlineKeyboardButton("📉 نسبة أقل (-5%)", callback_data="cfg_box_chance_down"))
        else:
            msg = f"⚙️ <b>لوحة ضبط عجلة الحظ المخصصة (التحكم بالخانات بدون أوامر):</b>\n\n• سعر لفة العجلة الحالي: <b>{bot_config['wheel_price']} نقطة</b>\n• نسبة فوز الجائزة الكبرى العشوائية: <b>{bot_config['wheel_chance']}%</b>"
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("➕ سعر اللفة أعلى (+5)", callback_data="cfg_wheel_price_up"), types.InlineKeyboardButton("➖ سعر اللفة أقل (-5)", callback_data="cfg_wheel_price_down"))
            markup.row(types.InlineKeyboardButton("📈 النسبة الكبرى أعلى (+1%)", callback_data="cfg_wheel_chance_up"), types.InlineKeyboardButton("📉 النسبة الكبرى أقل (-1%)", callback_data="cfg_wheel_chance_down"))
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    elif data == "game_buy_lootbox":
        price = bot_config.get("lootbox_price", 50)
        if u["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيد نقاطك الحالي غير كافٍ لفتح صندوق حظ عشوائي.", show_alert=True)
            
        update_user_data(uid, points=-price)
        chance = bot_config.get("lootbox_chance", 25)
        
        if random.randint(1, 100) <= chance:
            win_pts = random.randint(100, 500)
            update_user_data(uid, points=win_pts, accumulated_points=win_pts)
            bot.edit_message_text(f"🎰 <b>مبروووووك الفوز حالفك بنجاح! 🎉🔥</b>\n\nفتحت صندوق الحظ ووجدت بداخله رصيداً كبيراً جداً:\n🎁 <b>+{win_pts} نقطة مضافة فورا لحسابك!</b> كفو يا بطل حظك أسطوري.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(f"🎰 <b>للأسف.. الصندوق كان فارغاً تقريباً 📉</b>\n\nالحظ لم يحالفك في هذه المرة. لا تستسلم وعاود المحاولة لتعويض خسائرك والفوز بالجائزة القادمة!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        
        update_user_rank_and_quests(uid)
        return

    elif data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if u["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيد نقاطك غير كافٍ لتدوير عجلة الحظ حالياً.", show_alert=True)
            
        update_user_data(uid, points=-price)
        bot.answer_callback_query(call.id, "💫 جاري تدوير عجلة الحظ الآن...")
        
        frames = ["🎰 [ 🔁 جاري سحب وتدوير العجلة... ]", "🎡 [ 🔄 مؤشر الحظ يتحرك بحماس... ]", "🎰 [ 🔁 ترقب توقف المؤشر الفوري... ]"]
        for frame in frames:
            try:
                bot.edit_message_text(frame, call.message.chat.id, call.message.message_id)
                time.sleep(0.5)
            except: pass
            
        chance_grand = bot_config.get("wheel_chance", 5)
        if random.randint(1, 100) <= chance_grand:
            result = "GRAND_PRIZE"
        else:
            result = random.choice([0, 10, 20, price, price + 30])
            
        if result == "GRAND_PRIZE":
            win_pts = 1000
            update_user_data(uid, points=win_pts, accumulated_points=win_pts)
            bot.edit_message_text(f"🏆 <b>المستحيل حدث بالكامل!! حظك أسطوري خارق للعادة! 🔥🎖️</b>\n\nلقد ربحت الآن: 👑 <b>الجائزة الكبرى الهائلة (+1000 نقطة بالرصيد)!</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            
            try:
                pub_msg = f"🎡 <b>انفجار هائل داخل عجلة الحظ!</b>\n\n👤 مستخدم محظوظ قام الآن بتدوير عجلة الحظ المدفوعة وفجر الجائزة المستحيلة:\n🏆 <b>فاز بالجائزة الكبرى (+1000 نقطة كاملة) سحب فوري!</b> 🎉🔥\n🤖 أثبت وجودك وجرب حظك الحقيقي داخل البوت الآن."
                bot.send_message(CHANNEL_ID, pub_msg, parse_mode="HTML")
            except: pass
        else:
            if result > 0:
                update_user_data(uid, points=result, accumulated_points=result)
                bot.edit_message_text(f"🎡 <b>توقفت عجلة الحظ بنجاح!</b>\n\nالنتيجة النهائية للمؤشر: حصلت على <b>+{result} نقطة!</b> تعوضها باللفات القادمة 👍", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            else:
                bot.edit_message_text(f"🎡 <b>توقفت العجلة بنجاح!</b>\n\nالنتيجة النهائية: <b>0 نقطة 💔</b>\nحظاً أوفر وأفضل في المرة القادمة يا بطل لا تيأس!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
                
        update_user_rank_and_quests(uid)
        return

    elif data.startswith("step_addkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"step_addkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 المنتج: <b>{prod}</b>\n👇 <b>الرجاء اختيار المدة للمفتاح:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_addkey_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"📦 المنتج: <b>{prod}</b>\n⏱️ المدة: <b>{plan}</b>\n\n✍️ <b>أرسل المفتاح الآن:</b>\n(يمكنك إرسال مفتاح واحد، أو عدة مفاتيح في رسالة واحدة بحيث يكون كل مفتاح في سطر جديد)", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_save_new_keys(msg, prod, plan))

    elif data.startswith("step_price_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            curr_price = prices_config.get(prod, {}).get(plan, 0)
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} (السعر الحالي: {curr_price})", callback_data=f"step_price_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 المنتج: <b>{prod}</b>\n👇 <b>اختر المدة التي تريد تغيير سعرها:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_price_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"📦 المنتج: <b>{prod}</b>\n⏱️ المدة: <b>{plan}</b>\n\n✍️ <b>أرسل السعر الجديد الآن (أرقام فقط):</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_save_new_price(msg, prod, plan))

    elif data.startswith("step_delkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            count = len(keys_store.get(prod, {}).get(plan, []))
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} (المخزن: {count} مفتاح)", callback_data=f"step_delkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 المنتج: <b>{prod}</b>\n👇 <b>اختر المدة التي تريد حذف مفتاح منها:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_delkey_plan|"):
        _, prod, plan = data.split("|")
        keys = keys_store.get(prod, {}).get(plan, [])
        if not keys:
            return bot.answer_callback_query(call.id, "❌ لا توجد مفاتيح في هذا القسم لحذفها.", show_alert=True)
            
        m = bot.edit_message_text(f"📦 المنتج: <b>{prod}</b>\n⏱️ المدة: <b>{plan}</b>\n\n✍️ <b>أرسل المفتاح الذي تريد حذفه بدقة</b>،\nأو أرسل <b>رقمه التسلسلي</b> (مثال: أرسل رقم 1 لحذف أول مفتاح في المخزن):", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_delete_specific_key(msg, prod, plan))

    elif data == "confirm_open_ticket":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        m = bot.send_message(call.message.chat.id, "💬 اكتب رسالة الدعم الفني الخاصة بك الآن لفتح تذكرة:")
        bot.register_next_step_handler(m, process_support_ticket)

    elif data == "confirm_send_prod_req":
        temp_reqs = bot_config.get("temp_req", {})
        if uid in temp_reqs:
            text = temp_reqs[uid]
            req_id = str(random.randint(10000, 99999))
            if "product_requests" not in bot_config:
                bot_config["product_requests"] = {}
            bot_config["product_requests"][req_id] = {"uid": uid, "text": text, "date": datetime.now().isoformat()}
            bot_config["temp_req"].pop(uid, None)
            save_json(DB_CONFIG, bot_config)
            
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, f"✅ تم إرسال طلبك بنجاح للإدارة برقم: <code>#{req_id}</code> وسيتم مراجعته قريباً!", parse_mode="HTML")
            try: bot.send_message(ADMIN_PRIMARY, f"💡 <b>طلب منتج جديد #{req_id}</b> من العضو {uid}:\n{text}")
            except: pass
        else:
            bot.answer_callback_query(call.id, "❌ انتهت صلاحية هذا الطلب، يرجى المحاولة مجدداً.", show_alert=True)

    elif data == "cancel_action":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "❌ تم إلغاء العملية بنجاح.")

    elif data.startswith("view_ticket_"):
        t_id = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if t_id not in tickets:
            return bot.answer_callback_query(call.id, "❌ التذكرة غير موجودة أو محذوفة.", show_alert=True)
        t_info = tickets[t_id]
        msg = f"🎫 <b>تفاصيل تذكرة الدعم #{t_id}:</b>\n\n👤 صاحب التذكرة: <code>{t_info['uid']}</code>\n⚙️ الحالة: {t_info.get('status', 'open').upper()}\n\n📝 <b>الرسالة:</b>\n{t_info['text']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💬 الرد على التذكرة", callback_data=f"reply_ticket_{t_id}"),
            types.InlineKeyboardButton("🔒 إغلاق التذكرة", callback_data=f"close_ticket_{t_id}")
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("reply_ticket_"):
        t_id = data.split("_")[2]
        m = bot.send_message(call.message.chat.id, f"✍️ اكتب الآن ردك الفني لإرساله مباشرة إلى صاحب التذكرة #{t_id}:")
        bot.register_next_step_handler(m, lambda msg: admin_send_reply_ticket_func(msg, t_id))
        bot.answer_callback_query(call.id)

    elif data.startswith("close_ticket_"):
        t_id = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if t_id in tickets:
            tickets[t_id]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
            u_id = tickets[t_id]["uid"]
            try: bot.send_message(int(u_id), f"🔒 <b>تحديث الدعم:</b> تم إغلاق تذكرتك الفنية ذات الرقم #{t_id} بنجاح.", parse_mode="HTML")
            except: pass
            bot.edit_message_text(f"✅ تم إغلاق التذكرة #{t_id} بنجاح وإرسال إشعار للمستخدم.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ لم يتم العثور على التذكرة.", show_alert=True)

    elif data.startswith("adm_"):
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات مسؤول لاستخدام هذا الزر.", show_alert=True)
            
        parts = data.split("_")
        action = parts[1]
        target_id = parts[2]
        
        tgt_u = get_user(target_id)
        if not tgt_u:
            return bot.answer_callback_query(call.id, "❌ لم يتم العثور على هذا العضو في النظام.", show_alert=True)
            
        if action == "promote":
            update_user_data(target_id, is_admin=True)
            bot.answer_callback_query(call.id, "🛡️ تم ترقية العضو ليصبح أدمن بنجاح!", show_alert=True)
        elif action == "demote":
            update_user_data(target_id, is_admin=False)
            bot.answer_callback_query(call.id, "⬇️ تم سحب صلاحيات الإدارة من العضو بنجاح.", show_alert=True)
        elif action == "ban":
            update_user_data(target_id, banned=True)
            bot.answer_callback_query(call.id, "⛔ تم حظر العضو حظراً نهائياً.", show_alert=True)
        elif action == "tempban":
            until_time = datetime.now() + timedelta(days=1)
            update_user_data(target_id, banned_until=until_time.isoformat())
            bot.answer_callback_query(call.id, "⏱️ تم حظر العضو مؤقتاً لمدة 24 ساعة.", show_alert=True)
        elif action == "unban":
            update_user_data(target_id, banned=False, banned_until=None)
            bot.answer_callback_query(call.id, "🟢 تم فك الحظر عن العضو بالكامل.", show_alert=True)
            
        tgt_u = get_user(target_id)
        role = "أدمن مالك" if int(target_id) == ADMIN_PRIMARY else ("أدمن مدير" if tgt_u.get("is_admin", False) else "مستخدم عادي")
        ban_status = "محظور نهائي ⛔" if tgt_u.get("banned", False) else ("محظور مؤقت 🔴" if tgt_u.get("banned_until") else "نشط 🟢")
        
        updated_msg = (f"👥 <b>بيانات العضو المحدثة:</b>\n\n• ID: <code>{target_id}</code>\n"
                       f"• Username: @{tgt_u['username']}\n• الرصيد الحالي: {tgt_u['points']} نقطة\n"
                       f"• الرتبة الحالية: {role}\n• حالة الحظر: {ban_status}")
                       
        markup = types.InlineKeyboardMarkup(row_width=2)
        if tgt_u.get("is_admin", False):
            markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{target_id}"))
        else:
            markup.add(types.InlineKeyboardButton("🛡️ ترقية إلى أدمن", callback_data=f"adm_promote_{target_id}"))
            
        markup.add(
            types.InlineKeyboardButton("⛔ حظر نهائي", callback_data=f"adm_ban_{target_id}"),
            types.InlineKeyboardButton("⏱️ حظر 24 ساعة", callback_data=f"adm_tempban_{target_id}")
        )
        markup.add(types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"adm_unban_{target_id}"))
        
        try: bot.edit_message_text(updated_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass

    elif data.startswith("setlang_"):
        lang = data.split("_")[1]
        update_user_data(uid, lang=lang)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))

    elif data == "check_join":
        lang = u.get("lang", "ar")
        if check_channel_join(uid):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, "✅ شكراً لتعاونك واشتراكك بالقناة، تم تفعيل حسابك!", reply_markup=get_main_keyboard(uid, lang, page=1))
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في القناة المطلوبة بعد!", show_alert=True)

    elif data.startswith("select_prod_"):
        prod = data.split("_")[2]
        if prod not in prices_config: return
        markup = types.InlineKeyboardMarkup()
        u_discount = u.get("rank_discount", 0.0)
        
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_p = prices_config[prod].get(plan, 0)
            disc = bot_config["discount"]
            final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
            stock_count = len(keys_store.get(prod, {}).get(plan, []))
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} | {final_p} Pts (المخزن: {stock_count})", callback_data=f"buy_plan_{prod}_{plan}"))
        bot.edit_message_text(f"📦 المنتج المختار: <b>{prod}</b>\nرتبتك الحالية تمنحك خصماً إضافياً بمقدار: {int(u_discount*100)}%\nاختر مدة الاشتراك الشراء التلقائي:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("buy_plan_"):
        prod = data.split("_")[2]
        plan = data.split("_")[3] + " " + data.split("_")[4] if len(data.split("_")) > 4 else data.split("_")[3]
        
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config["discount"]
        u_discount = u.get("rank_discount", 0.0)
        final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
        
        if u["points"] < final_p:
            return bot.answer_callback_query(call.id, "❌ عذراً! رصيد نقاطك الحالي غير كافٍ.", show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, "⚠️ نعتذر منك! نفذت كمية مفاتيح هذه الخطة من المخزن.", show_alert=True)
            
        delivered_key = keys_store[prod][plan].pop(0)
        update_user_data(uid, points=-final_p)
        
        bot_config["total_sales"] += 1
        bot_config["total_earnings"] += final_p
        bot_config["sales_log"].append({
            "uid": uid, "username": u["username"], "product": prod, "plan": plan, "price": final_p, "key": delivered_key, "date": datetime.now().isoformat()
        })
        
        save_json(DB_KEYS, keys_store)
        save_json(DB_CONFIG, bot_config)
        update_user_rank_and_quests(uid)
        
        bot.edit_message_text(f"🎉 <b>تمت عملية الشراء التلقائي بنجاح!</b>\n\n📦 المنتج: <code>{prod}</code>\n⏱️ مدة الاشتراك: <code>{plan}</code>\n💰 السعر المخصوم: {final_p} نقطة\n\n🔐 <b>المفتاح الخاص بك هو:</b>\n<code>{delivered_key}</code>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        
        try:
            pub_notif = f"🔥 <b>عملية بيع موثقة وناجحة!</b>\n\n📦 المنتج المشترى: <code>{prod}</code>\n⏱️ مدة الاشتراك الترخيصي: {plan}\n💰 الثمن المدفوع: {final_p} نقطة\n🤖 تم الشراء والتسليم الفوري عبر نظام البوت المتكامل."
            bot.send_message(CHANNEL_ID, pub_notif, parse_mode="HTML")
        except: pass

def process_save_new_keys(message, prod, plan):
    keys = message.text.strip().split('\n')
    added = 0
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ تم حفظ المفاتيح بنجاح!\n📦 المنتج: {prod}\n⏱️ المدة: {plan}\n🔢 عدد المفاتيح المضافة: {added}")

def process_save_new_price(message, prod, plan):
    try:
        new_price = int(message.text.strip())
        prices_config[prod][plan] = new_price
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ تم تحديث السعر بنجاح.\n📦 {prod} | {plan} ➡️ السعر الجديد: {new_price} نقطة.")
    except:
        bot.send_message(message.chat.id, "❌ حدث خطأ! يرجى إرسال أرقام صحيحة فقط (مثال: 50).")

def process_delete_specific_key(message, prod, plan):
    val = message.text.strip()
    keys_list = keys_store.get(prod, {}).get(plan, [])
    
    if val.isdigit() and 0 < int(val) <= len(keys_list):
        removed = keys_list.pop(int(val) - 1)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ تم حذف المفتاح بنجاح:\n<code>{removed}</code>", parse_mode="HTML")
        
    if val in keys_list:
        keys_list.remove(val)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ تم حذف المفتاح بنجاح:\n<code>{val}</code>", parse_mode="HTML")
        
    bot.send_message(message.chat.id, "❌ لم يتم العثور على المفتاح، تأكد من نسخه بشكل صحيح أو إرسال رقمه التسلسلي المضبوط.")

def admin_view_member_func(message):
    t_id = message.text.strip()
    u = get_user(t_id)
    if u:
        role = "أدمن مالك" if int(t_id) == ADMIN_PRIMARY else ("أدمن مدير" if u.get("is_admin", False) else "مستخدم عادي")
        ban_status = "محظور نهائي ⛔" if u.get("banned", False) else ("محظور مؤقت 🔴" if u.get("banned_until") else "نشط 🟢")
        
        msg = f"👥 <b>بيانات العضو المستعلم عنه:</b>\n\n• ID: <code>{t_id}</code>\n• Username: @{u['username']}\n• الرصيد الحالي: {u['points']} نقطة\n• الرتبة الحالية: {u.get('rank', 'عضو عادي 🔹')}\n• الرتبة الإدارية: {role}\n• حالة الحظر: {ban_status}"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        if u.get("is_admin", False):
            markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{t_id}"))
        else:
            markup.add(types.InlineKeyboardButton("🛡️ ترقية إلى أدمن", callback_data=f"adm_promote_{t_id}"))
            
        markup.add(
            types.InlineKeyboardButton("⛔ حظر نهائي", callback_data=f"adm_ban_{t_id}"),
            types.InlineKeyboardButton("⏱️ حظر 24 ساعة", callback_data=f"adm_tempban_{t_id}")
        )
        markup.add(types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"adm_unban_{t_id}"))
        
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")
    else: 
        bot.send_message(message.chat.id, "❌ هذا الآيدي غير مسجل في قاعدة بيانات البوت حالياً.")

def admin_confirm_fake_marketing(message):
    confirm_text = message.text.strip()
    if not confirm_text:
        return bot.send_message(message.chat.id, "❌ تم إلغاء العملية بسبب إدخال فارغ.")
        
    chosen_plan = random.choice(["1 Day", "7 Days", "30 Days"])
    fake_masked_key = generate_fake_key()
    
    marketing_msg = (
        f"🔥 <b>مبيعات جديدة وتلقائية داخل المتجر!</b>\n\n"
        f"قام أحد المستخدمين الآن بشراء مفتاح بنجاح لـ: <code>Flourite Cheat</code> 🌟\n"
        f"⏱️ مدة الاشتراك الترخيصي: <b>{chosen_plan}</b>\n"
        f"🔐 رخصة العميل: <code>{fake_masked_key}</code>\n\n"
        f"🛒 لشراء مفتاحك وتفعيل اشتراكك الفوري تلقائياً عبر البوت: t.me/{bot.get_me().username}"
    )
    
    try:
        bot.send_message(CHANNEL_ID, marketing_msg, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ تم تأكيد الإجراء بنجاح بعد كتابتك '{confirm_text}'! ونشر منشور التسويق الوهمي لـ <b>Flourite Cheat ({chosen_plan})</b> بقناتك الموثقة.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ تعذر النشر بالقناة: {str(e)}")

def process_redeem_user(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in redeem_codes:
        added_pts = redeem_codes.pop(code)
        update_user_data(uid, points=added_pts, accumulated_points=added_pts)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id, f"🎉 تم تفعيل كود الشحن وإضافة +{added_pts} نقطة إلى رصيدك.")
    else: bot.send_message(message.chat.id, "❌ كود الشحن المدخل غير صحيح أو مستعمل مسبقاً.")

def process_support_ticket(message):
    uid = str(message.from_user.id)
    u_text = message.text.strip()
    if not u_text:
        return bot.send_message(message.chat.id, "❌ لا يمكنك إرسال تذكرة فارغة.")
        
    ticket_id = str(random.randint(10000, 99999))
    if "tickets" not in bot_config:
        bot_config["tickets"] = {}
        
    bot_config["tickets"][ticket_id] = {"uid": uid, "text": u_text, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    
    bot.send_message(message.chat.id, f"✅ <b>تم فتح تذكرة دعم فني جديدة بنجاح!</b>\n• رقم التذكرة: <code>#{ticket_id}</code>\n• انتظر رد الإدارة قريباً هنا.", parse_mode="HTML")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 رد فوري", callback_data=f"reply_ticket_{ticket_id}"),
        types.InlineKeyboardButton("🔒 إغلاق التذكرة", callback_data=f"close_ticket_{ticket_id}")
    )
    
    admin_msg = f"🎫 <b>تذكرة دعم جديدة برقم #{ticket_id}</b>\n👤 من المستخدم: <code>{uid}</code>\n\n📝 <b>محتوى التذكرة:</b>\n{u_text}"
    try: bot.send_message(ADMIN_PRIMARY, admin_msg, reply_markup=markup, parse_mode="HTML")
    except: pass

def process_product_request_input(message):
    uid = str(message.from_user.id)
    text = message.text.strip()
    if not text:
        return bot.send_message(message.chat.id, "❌ لا يمكن إرسال طلب فارغ.")
    
    if "temp_req" not in bot_config:
        bot_config["temp_req"] = {}
    bot_config["temp_req"][uid] = text
    save_json(DB_CONFIG, bot_config)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد وإرسال الطلب", callback_data="confirm_send_prod_req"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
    )
    bot.send_message(message.chat.id, f"⚠️ <b>تأكيد طلب إضافة منتج:</b>\nهل أنت متأكد من رغبتك في إرسال هذا الاقتراح إلى إدارة المتجر؟\n\n📦 <b>تفاصيل المنتج:</b>\n<code>{text}</code>", reply_markup=markup, parse_mode="HTML")

def admin_send_reply_ticket_func(message, ticket_id):
    tickets = bot_config.get("tickets", {})
    if ticket_id not in tickets:
        return bot.send_message(message.chat.id, "❌ خطأ: التذكرة لم تعد متاحة في النظام.")
        
    reply_text = message.text.strip()
    user_id = tickets[ticket_id]["uid"]
    
    user_notif = f"💬 <b>وصلك رد جديد من الدعم الفني بخصوص التذكرة #{ticket_id}:</b>\n\n<code>{reply_text}</code>"
    try:
        bot.send_message(int(user_id), user_notif, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ تم إرسال الرد بنجاح للمستخدم صاحب التذكرة #{ticket_id}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ تعذر تسليم الرسالة للمستخدم. الخطأ: {str(e)}")

def admin_add_product_func(message):
    prod = message.text.strip()
    if prod not in prices_config:
        prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
        keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
        save_json(DB_PRICES, prices_config)
        save_json(DB_KEYS, keys_store)
        bot.send_message(message.chat.id, f"➕ تم إضافة المنتج <b>{prod}</b> بنجاح.", parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ المنتج مضاف بالفعل.")

def admin_delete_product_func(message):
    prod = message.text.strip()
    if prod in prices_config:
        prices_config.pop(prod)
        if prod in keys_store: keys_store.pop(prod)
        save_json(DB_PRICES, prices_config)
        save_json(DB_KEYS, keys_store)
        bot.send_message(message.chat.id, f"✅ تم حذف المنتج <b>{prod}</b> بالكامل.", parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ المنتج غير موجود.")

def admin_charge_member_func(message):
    try:
        t_id, pts = message.text.strip().split()
        if get_user(t_id):
            update_user_data(t_id, points=int(pts), accumulated_points=int(pts))
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 تم شحن الحساب {t_id} بمقدار +{pts} نقطة.")
            try: bot.send_message(int(t_id), f"🔔 تم إضافة +{pts} رصيد لنقاطك من قبل الإدارة.")
            except: pass
        else: bot.send_message(message.chat.id, "❌ الآيدي غير موجود.")
    except: bot_config.send_message(message.chat.id, "❌ خطأ بالإدخال، يرجى كتابة الآيدي ثم مسافة ثم المبلغ.")

def admin_create_code_func(message):
    try:
        code, pts = message.text.strip().split()
        redeem_codes[code] = int(pts)
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 تم إنشاء كود شحن فعال:\n• الكود: <code>{code}</code>\n• قيمته: {pts} نقطة", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ خطأ! اكتب الكود ثم مسافة ثم القيمة.")

def admin_set_discount_func(message):
    try:
        disc = int(message.text.strip())
        if 0 <= disc < 100:
            bot_config["discount"] = disc
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 تم تفعيل خصم عام بمقدار {disc}%")
        else: bot_config["discount"] = 0
    except: bot.send_message(message.chat.id, "❌ أرسل أرقام فقط.")

def admin_broadcast_func(message):
    txt = message.text
    success_count = 0
    for u_id in get_all_user_ids():
        try:
            bot.send_message(int(u_id), txt)
            success_count += 1
            time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"📢 تم إكمال الإذاعة الشاملة لـ {success_count} عضو.")

# دالة تعديل المكافأة اليومية المحدثة لملف الإعدادات بقيمة daily_gift
def admin_edit_daily_bonus(message):
    try:
        new_bonus = int(message.text.strip())
        if new_bonus >= 0:
            bot_config["daily_gift"] = new_bonus
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ تم تحديث المكافأة اليومية بنجاح لتصبح: {new_bonus} نقطة.")
        else:
            bot.send_message(message.chat.id, "❌ يجب أن تكون القيمة أكبر من أو تساوي صفر.")
    except ValueError:
        bot_config.send_message(message.chat.id, "❌ يرجى إدخال أرقام صحيحة فقط.")

def admin_edit_invite_reward(message):
    try:
        new_reward = int(message.text.strip())
        if new_reward >= 0:
            bot_config["invite_reward"] = new_reward
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ تم تحديث نقاط الدعوة بنجاح لتصبح: {new_reward} نقطة لكل دعوة.")
        else:
            bot.send_message(message.chat.id, "❌ يجب أن تكون القيمة أكبر من أو تساوي صفر.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال أرقام صحيحة فقط.")

if __name__ == "__main__":
    print("🚀 تم تشغيل البوت بنظام الأزرار والخانات التفاعلية لإدارة المهام والألعاب بنجاح...")
    bot.infinity_polling()
