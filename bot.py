import telebot
from telebot import types
import random
import os
import time
import json
from datetime import datetime, timedelta

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, LOCALES
from database import engine, text, init_db, get_user, update_user_data, register_user, keys_store, redeem_codes, prices_config, bot_config, save_json, DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG, update_user_rank_and_quests
from utils import check_spam, is_user_banned, check_channel_join, generate_fake_key
from keyboards import get_lang_inline, get_join_inline, get_main_keyboard, get_admin_keyboard

# -------------------------------------------------------------
# 🔄 تنظيف النصوص
# -------------------------------------------------------------
def clean_text(text_str):
    if not text_str:
        return ""
    return " ".join(text_str.strip().replace('\ufe0f', '').split())

def is_admin(uid, u=None):
    if u is None:
        u = get_user(uid) or {}
    return int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)

# -------------------------------------------------------------
# 🔄 نقل البيانات القديمة
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
        print("✅ تم دمج بيانات users.json بنجاح.")
except Exception as e:
    print(f"⚠️ خطأ نقل البيانات: {e}")

def get_all_user_ids():
    with engine.connect() as conn:
        return [str(r[0]) for r in conn.execute(text("SELECT uid FROM users")).fetchall()]

# -------------------------------------------------------------
# /start و /id
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
            try: bot.send_message(int(inviter_id), f"🔗 انضم مستخدم جديد عن طريق رابط الإحالة! حصلت على {bot_config['invite_reward']} نقاط.")
            except: pass

    if not check_channel_join(uid):
        lang = u.get("lang", "ar")
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    bot.send_message(message.chat.id, LOCALES["ar"]["welcome"], reply_markup=get_lang_inline())

# -------------------------------------------------------------
# 🎯 نظام التوجيه الذكي - مطابقة دقيقة بدون تداخل
# -------------------------------------------------------------
def match_button(txt, keywords):
    """تحقق ذكي من مطابقة أي كلمة دلالية في النص"""
    txt_lower = txt.lower()
    return any(kw.lower() in txt_lower for kw in keywords)

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")
        
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    txt = clean_text(message.text)
    admin_flag = is_admin(uid, u)

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config.get("maintenance", False) and not admin_flag:
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    # ============================================================
    # 🔴 أزرار الأدمن أولاً (لها الأولوية القصوى)
    # ============================================================
    if admin_flag:
        # التنقل بين صفحات الأدمن
        if match_button(txt, ["التالي للمشرف", "التالي المشرف"]):
            return bot.send_message(message.chat.id, "⚙️ لوحة إعدادات الألعاب التسويقية:", reply_markup=get_admin_keyboard(page=2))
        
        if match_button(txt, ["سابق المشرف", "سابق للمشرف", "السابق المشرف"]):
            return bot.send_message(message.chat.id, "👑 لوحة التحكم الرئيسية:", reply_markup=get_admin_keyboard(page=1))

        # 🔧 إعدادات صندوق الحظ (أدمن)
        if "إعدادات" in txt and "صندوق" in txt:
            return show_lootbox_settings(message)
        
        # 🔧 إعدادات عجلة الحظ (أدمن)
        if "إعدادات" in txt and "عجلة" in txt:
            return show_wheel_settings(message)
        
        # 🔧 إعدادات المهام (أدمن)
        if "إعدادات" in txt and "مهام" in txt:
            return show_quests_settings(message)
        
        # 🔧 تعديل المكافأة اليومية (أدمن)
        if match_button(txt, ["تعديل المكافأة", "تعديل الهدية", "المكافأة اليومية"]) and "إعدادات" not in txt:
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية: {bot_config.get('daily_gift', 10)} نقطة.\n\n✍️ أرسل القيمة الجديدة (أرقام فقط):")
            return bot.register_next_step_handler(m, admin_edit_daily_bonus)

        # 🔧 تعديل نقاط الدعوة (أدمن)
        if match_button(txt, ["تعديل نقاط الدعوة", "نقاط الدعوة", "نقاط الاحالة", "نقاط الإحالة"]):
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية: {bot_config.get('invite_reward', 20)} نقطة.\n\n✍️ أرسل القيمة الجديدة (أرقام فقط):")
            return bot.register_next_step_handler(m, admin_edit_invite_reward)

        # باقي أزرار الأدمن
        if match_button(txt, ["واجهة المستخدم", "الرجوع للمستخدم"]):
            return bot.send_message(message.chat.id, "🔙 تم الانتقال إلى واجهة المستخدم.", reply_markup=get_main_keyboard(uid, lang, page=1))

        if match_button(txt, ["إدارة التذاكر", "التذاكر", "تذاكر"]):
            return admin_show_tickets(message)

        if "طلبات المنتجات" in txt or ("طلب" in txt and "منتج" in txt):
            return admin_show_product_requests(message)

        if match_button(txt, ["إضافة منتج", "اضافة منتج"]):
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج الجديد:")
            return bot.register_next_step_handler(m, admin_add_product_func)

        if "حذف منتج" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج المراد حذفه:")
            return bot.register_next_step_handler(m, admin_delete_product_func)

        if match_button(txt, ["إضافة مفاتيح", "اضافة مفاتيح"]):
            return admin_add_keys_menu(message)

        if match_button(txt, ["إدارة الأسعار", "الأسعار", "الاسعار"]):
            return admin_manage_prices_menu(message)

        if "حذف مفتاح" in txt:
            return admin_delete_key_menu(message)

        if match_button(txt, ["استعراض المفاتيح", "عرض المفاتيح"]):
            return admin_view_keys(message)

        if "مسح" in txt and "مفاتيح" in txt:
            keys_store.clear()
            for prod in prices_config.keys():
                keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
            save_json(DB_KEYS, keys_store)
            return bot.send_message(message.chat.id, "🗑️ تم مسح جميع المفاتيح بنجاح.")

        if match_button(txt, ["إدارة الأعضاء", "الاعضاء", "الأعضاء"]):
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو:")
            return bot.register_next_step_handler(m, admin_view_member_func)

        if match_button(txt, ["شحن الأعضاء", "شحن الاعضاء", "شحن عضو"]):
            m = bot.send_message(message.chat.id, "✍️ أرسل: الآيدي مسافة القيمة (مثال: 123456 500):")
            return bot.register_next_step_handler(m, admin_charge_member_func)

        if "إنشاء" in txt and "كود" in txt or "اكواد الشحن" in txt:
            m = bot.send_message(message.chat.id, "✍️ أرسل: الكود مسافة القيمة (مثال: FREE100 100):")
            return bot.register_next_step_handler(m, admin_create_code_func)

        if match_button(txt, ["التخفيضات", "خصم عام"]):
            m = bot.send_message(message.chat.id, "✍️ أرسل نسبة الخصم العام (0-99):")
            return bot.register_next_step_handler(m, admin_set_discount_func)

        if match_button(txt, ["الإذاعة", "اذاعة", "بث"]):
            m = bot.send_message(message.chat.id, "✍️ أرسل نص الإذاعة:")
            return bot.register_next_step_handler(m, admin_broadcast_func)

        if "نشر" in txt and "أسعار" in txt or "نشر الاسعار" in txt:
            return admin_publish_prices(message)

        if "تسويق" in txt:
            m = bot.send_message(message.chat.id, "⚠️ اكتب <code>تأكيد</code> لنشر منشور تسويقي:", parse_mode="HTML")
            return bot.register_next_step_handler(m, admin_confirm_fake_marketing)

        if "إحصائيات" in txt or "النسخ الاحتياطي" in txt:
            return admin_show_stats_backup(message)

    # ============================================================
    # 🟢 أزرار المستخدم العادي
    # ============================================================
    
    # التنقل بين صفحات المستخدم
    if txt == "التالي ➡️" or (txt in ["التالي", "التالي ⏭"]) or ("التالي" in txt and "مشرف" not in txt):
        return bot.send_message(message.chat.id, "🎡 ميزات التسلية والمهام:", reply_markup=get_main_keyboard(uid, lang, page=2))
    
    if txt == "⬅️ السابق" or txt in ["السابق", "⏮ السابق"] or ("السابق" in txt and "مشرف" not in txt):
        return bot.send_message(message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))

    # 🎰 صندوق الحظ
    if "صندوق الحظ" in txt or "صندوق حظ" in txt:
        return show_lootbox(message)

    # 🎡 عجلة الحظ
    if "عجلة الحظ" in txt or "عجلة حظ" in txt:
        return show_wheel(message)

    # 🔥 المهام الصعبة
    if match_button(txt, ["المهام الصعبة", "المهام", "مهامي", "quests"]):
        return show_quests(message, uid)

    # 🏆 الرتبة
    if match_button(txt, ["رتبتي", "الرتبة", "رتبة", "rank"]):
        return show_rank(message, uid)

    # 🆔 الآيدي
    if match_button(txt, ["آيدي", "الآيدي", "id", "المعرف", "معرفي"]):
        return bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك: <code>{uid}</code>", parse_mode="HTML")

    # 💰 الرصيد
    if match_button(txt, ["رصيد", "حسابي", "النقاط", "balance"]):
        return show_balance(message, uid)

    # 🌐 اللغة
    if match_button(txt, ["اللغة", "لغة", "lang", "language"]):
        return bot.send_message(message.chat.id, "🌐 اختر لغة البوت:", reply_markup=get_lang_inline())

    # 🎁 المكافأة اليومية
    if match_button(txt, ["هدية", "مكافأة", "يومية", "bonus", "gift", "daily"]) and "تعديل" not in txt:
        return claim_daily_bonus(message, uid, u)

    # 🔗 نظام الإحالة
    if match_button(txt, ["دعوة", "رابط", "احالة", "إحالة", "invite", "referral", "refer"]):
        return show_referral(message, uid)

    # 🎫 استرداد كود
    if match_button(txt, ["شحن كود", "كود شحن", "تفعيل كود", "redeem"]) or (txt == "🎁 استرداد كود"):
        m = bot.send_message(message.chat.id, "🎁 أدخل كود الشحن:")
        return bot.register_next_step_handler(m, process_redeem_user)

    # 📞 الدعم
    if match_button(txt, ["دعم", "تذكرة", "تواصل", "support"]) and "إدارة" not in txt:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ فتح تذكرة", callback_data="confirm_open_ticket"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
        )
        return bot.send_message(message.chat.id, "⚠️ <b>تأكيد فتح تذكرة دعم؟</b>", reply_markup=markup, parse_mode="HTML")

    # 💡 طلب منتج
    if match_button(txt, ["طلب منتج", "اقتراح منتج", "منتج جديد"]) and "طلبات" not in txt:
        m = bot.send_message(message.chat.id, "💡 اكتب اسم وتفاصيل المنتج المطلوب:")
        return bot.register_next_step_handler(m, process_product_request_input)

    # 🛍️ المتجر (النسخة المحسّنة)
    if match_button(txt, ["متجر", "المتجر", "shop", "منتجات", "شراء"]) and "إدارة" not in txt and "طلب" not in txt:
        return show_shop_enhanced(message, uid, u)

    # 👑 لوحة الأدمن
    if admin_flag and match_button(txt, ["لوحة", "ادارة", "إدارة", "التحكم", "admin"]) and "أعضاء" not in txt and "أسعار" not in txt and "تذاكر" not in txt:
        return bot.send_message(message.chat.id, "👑 لوحة تحكم الإدارة:", reply_markup=get_admin_keyboard(page=1))


# =====================================================================
# 🎨 دوال العرض المنفصلة (منظمة ونظيفة)
# =====================================================================

def show_lootbox(message):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = (f"🎰 <b>صناديق الحظ العشوائية (Loot Boxes):</b>\n\n"
           f"افتح صندوق حظ الآن وجرب مغامرة الفوز!\n\n"
           f"💸 سعر الصندوق: <b>{price} نقطة</b>\n"
           f"📈 نسبة الفوز: <b>{chance}%</b>\n\n"
           f"🎁 الجائزة: <b>+100 إلى +500 نقطة عشوائياً!</b>")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 فتح صندوق الآن", callback_data="game_buy_lootbox"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_wheel(message):
    price = bot_config.get("wheel_price", 40)
    msg = (f"🎡 <b>عجلة الحظ المدفوعة:</b>\n\n"
           f"أدر العجلة الآن وشاهد حظك!\n\n"
           f"💸 سعر اللفة: <b>{price} نقطة</b>\n"
           f"🎁 الجوائز: 0 | 10 | 20 | سعر اللفة | 🏆 <b>+1000 نقطة!</b>")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💫 تدوير العجلة", callback_data="game_spin_wheel"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def show_quests(message, uid):
    update_user_rank_and_quests(uid)
    u = get_user(uid)
    completed = u.get("completed_quests", "") or ""
    invite_cnt = u.get("invite_count", 0)
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    acc_pts = u.get("accumulated_points", 0)
    q = bot_config.get("quests", {
        "invite": {"target": 5, "reward": 100},
        "buy": {"target": 3, "reward": 150},
        "points": {"target": 1000, "reward": 200}
    })
    
    msg = "🔥 <b>قائمة المهام والانجازات:</b>\n\n"
    st1 = "✅ مكتمل" if "quest_invite" in completed else f"⏳ ({invite_cnt}/{q['invite']['target']})"
    msg += f"1️⃣ 👥 دعوة {q['invite']['target']} صديق\n🎁 +{q['invite']['reward']} نقطة | {st1}\n──────────────\n"
    
    st2 = "✅ مكتمل" if "quest_buy" in completed else f"⏳ ({user_buys}/{q['buy']['target']})"
    msg += f"2️⃣ 🛒 إتمام {q['buy']['target']} عمليات شراء\n🎁 +{q['buy']['reward']} نقطة | {st2}\n──────────────\n"
    
    st3 = "✅ مكتمل" if "quest_points" in completed else f"⏳ ({acc_pts}/{q['points']['target']})"
    msg += f"3️⃣ 💎 تجميع {q['points']['target']} نقطة\n🎁 +{q['points']['reward']} نقطة | {st3}\n"
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def show_rank(message, uid):
    update_user_rank_and_quests(uid)
    u = get_user(uid)
    r_name = u.get("rank", "عضو عادي 🔹")
    r_disc = int(u.get("rank_discount", 0.0) * 100)
    acc_pts = u.get("accumulated_points", 0)
    msg = (f"🏆 <b>نظام الرتب:</b>\n\n"
           f"• رتبتك: <b>{r_name}</b>\n"
           f"• الخصم الثابت: <b>{r_disc}%</b>\n"
           f"• نقاطك التراكمية: <code>{acc_pts}</code>\n\n"
           f"📋 <b>مستويات الرتب:</b>\n"
           f"🥈 الفضي: 200 نقطة (خصم 1%)\n"
           f"🥇 الذهبي: 600 نقطة (خصم 2%)\n"
           f"💎 الماسي: 1500 نقطة (خصم 3%)\n"
           f"⚡ الهيرو: 3500 نقطة (خصم 4%)\n"
           f"👑 الماستر: 7000 نقطة (خصم 4.5%)\n"
           f"🏆 الأسطورة: 12000 نقطة (خصم 5%)")
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def show_balance(message, uid):
    update_user_rank_and_quests(uid)
    u = get_user(uid)
    msg = (f"💰 <b>بيانات حسابك:</b>\n\n"
           f"• ID: <code>{uid}</code>\n"
           f"• الرصيد: <b>{u['points']}</b> نقطة\n"
           f"• الرتبة: {u.get('rank', 'عضو عادي 🔹')}\n"
           f"• الدعوات: {u.get('invite_count', 0)}\n"
           f"• اللغة: {u['lang'].upper()}\n"
           f"• الحالة: نشط 🟢")
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def claim_daily_bonus(message, uid, u):
    now = datetime.now()
    lc = u.get("last_claim")
    if lc:
        try:
            last_time = datetime.fromisoformat(lc)
            if now < last_time + timedelta(days=1):
                remaining = (last_time + timedelta(days=1)) - now
                hours = remaining.seconds // 3600
                mins = (remaining.seconds % 3600) // 60
                return bot.send_message(message.chat.id, f"⏰ تم استلام المكافأة! العودة بعد: <b>{hours}س {mins}د</b>", parse_mode="HTML")
        except: pass
    
    gift = bot_config.get("daily_gift", 10)
    update_user_data(uid, last_claim=now.isoformat(), points=gift, accumulated_points=gift)
    update_user_rank_and_quests(uid)
    bot.send_message(message.chat.id, f"✨ <b>تم استلام المكافأة اليومية!</b>\n\n🎁 +{gift} نقطة أُضيفت لرصيدك.", parse_mode="HTML")

def show_referral(message, uid):
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "your_bot"
    link = f"https://t.me/{bot_user}?start={uid}"
    u = get_user(uid) or {}
    invites = u.get("invite_count", 0)
    reward = bot_config.get("invite_reward", 20)
    
    msg = (f"🔗 <b>نظام الإحالة والدعوات:</b>\n\n"
           f"👥 عدد دعواتك الناجحة: <b>{invites}</b>\n"
           f"🎁 مكافأة كل دعوة: <b>{reward} نقطة</b>\n\n"
           f"📎 <b>رابط الإحالة الخاص بك:</b>\n"
           f"<code>{link}</code>\n\n"
           f"💡 شارك الرابط مع أصدقائك واحصل على {reward} نقطة عن كل عضو جديد ينضم!")
    
    markup = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={link}&text=🔥 انضم لأفضل بوت متجر وأحصل على مكافأت مجانية!"
    markup.add(types.InlineKeyboardButton("📤 مشاركة الرابط", url=share_url))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

# =====================================================================
# 🛍️ المتجر المحسّن (نسخة جديدة احترافية)
# =====================================================================
def show_shop_enhanced(message, uid, u):
    if not prices_config:
        return bot.send_message(message.chat.id, "📭 لا توجد منتجات متوفرة حالياً.")
    
    u_discount = u.get("rank_discount", 0.0)
    disc = bot_config.get("discount", 0)
    rank = u.get("rank", "عضو عادي 🔹")
    points = u.get("points", 0)
    
    header = (f"🛍️ <b>═══ متجر المنتجات ═══</b>\n\n"
              f"👤 <b>مرحباً بك في المتجر!</b>\n"
              f"💰 رصيدك: <b>{points}</b> نقطة\n"
              f"🏆 رتبتك: {rank}\n"
              f"🎁 خصم رتبتك: <b>{int(u_discount*100)}%</b>\n")
    
    if disc > 0:
        header += f"🔥 خصم عام إضافي: <b>{disc}%</b>\n"
    
    header += f"\n📦 <b>عدد المنتجات المتاحة:</b> {len(prices_config)}\n"
    header += f"═══════════════════════\n\n"
    header += f"👇 <b>اضغط على المنتج لعرض تفاصيله:</b>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for prod in prices_config.keys():
        total_stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        emoji = "✅" if total_stock > 0 else "⚠️"
        markup.add(types.InlineKeyboardButton(f"{emoji} 📦 {prod}  |  📊 مخزون: {total_stock}", callback_data=f"select_prod_{prod}"))
    
    markup.add(types.InlineKeyboardButton("🔄 تحديث المتجر", callback_data="refresh_shop"))
    bot.send_message(message.chat.id, header, reply_markup=markup, parse_mode="HTML")

# =====================================================================
# 🛠️ إعدادات الأدمن (لوحات إعدادات المهام والألعاب)
# =====================================================================
def show_lootbox_settings(message):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = (f"⚙️ <b>إعدادات صندوق الحظ:</b>\n\n"
           f"• السعر الحالي: <b>{price} نقطة</b>\n"
           f"• نسبة الفوز: <b>{chance}%</b>")
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
    msg = (f"⚙️ <b>إعدادات عجلة الحظ:</b>\n\n"
           f"• السعر الحالي: <b>{price} نقطة</b>\n"
           f"• نسبة الجائزة الكبرى: <b>{chance}%</b>")
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
    q = bot_config.get("quests", {
        "invite": {"target": 5, "reward": 100},
        "buy": {"target": 3, "reward": 150},
        "points": {"target": 1000, "reward": 200}
    })
    if "quests" not in bot_config:
        bot_config["quests"] = q
        save_json(DB_CONFIG, bot_config)
    
    msg = (f"⚙️ <b>إعدادات المهام:</b>\n\n"
           f"1️⃣ 👥 <b>مهمة الدعوات:</b>\n• الهدف: {q['invite']['target']} | الجائزة: {q['invite']['reward']}\n\n"
           f"2️⃣ 🛒 <b>مهمة المبيعات:</b>\n• الهدف: {q['buy']['target']} | الجائزة: {q['buy']['reward']}\n\n"
           f"3️⃣ 💎 <b>مهمة النقاط:</b>\n• الهدف: {q['points']['target']} | الجائزة: {q['points']['reward']}")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("👥 هدف ➖", callback_data="cfg_q_inv_t_down"), types.InlineKeyboardButton("👥 هدف ➕", callback_data="cfg_q_inv_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 جائزة ➖", callback_data="cfg_q_inv_r_down"), types.InlineKeyboardButton("🎁 جائزة ➕", callback_data="cfg_q_inv_r_up"))
    markup.row(types.InlineKeyboardButton("🛒 هدف ➖", callback_data="cfg_q_buy_t_down"), types.InlineKeyboardButton("🛒 هدف ➕", callback_data="cfg_q_buy_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 جائزة ➖", callback_data="cfg_q_buy_r_down"), types.InlineKeyboardButton("🎁 جائزة ➕", callback_data="cfg_q_buy_r_up"))
    markup.row(types.InlineKeyboardButton("💎 هدف ➖", callback_data="cfg_q_pts_t_down"), types.InlineKeyboardButton("💎 هدف ➕", callback_data="cfg_q_pts_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 جائزة ➖", callback_data="cfg_q_pts_r_down"), types.InlineKeyboardButton("🎁 جائزة ➕", callback_data="cfg_q_pts_r_up"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

# =====================================================================
# 🔴 دوال الأدمن الإضافية
# =====================================================================
def admin_show_tickets(message):
    tickets = bot_config.get("tickets", {})
    open_tickets = {k: v for k, v in tickets.items() if v.get("status", "open") == "open"}
    if not open_tickets:
        return bot.send_message(message.chat.id, "🎉 لا توجد تذاكر مفتوحة.")
    markup = types.InlineKeyboardMarkup()
    for t_id, t_info in open_tickets.items():
        markup.add(types.InlineKeyboardButton(f"🎫 #{t_id} - {t_info['uid']}", callback_data=f"view_ticket_{t_id}"))
    bot.send_message(message.chat.id, "👇 <b>التذاكر المفتوحة:</b>", reply_markup=markup, parse_mode="HTML")

def admin_show_product_requests(message):
    reqs = bot_config.get("product_requests", {})
    if not reqs:
        return bot.send_message(message.chat.id, "📭 لا توجد طلبات منتجات.")
    msg = "💡 <b>طلبات المنتجات:</b>\n\n"
    for r_id, r_info in reqs.items():
        msg += f"🔹 <b>#{r_id}</b>\n👤 {r_info['uid']}\n📦 {r_info['text']}\n📅 {r_info.get('date','')[:10]}\n──────────\n"
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def admin_add_keys_menu(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا توجد منتجات.")
    markup = types.InlineKeyboardMarkup()
    for prod in prices_config.keys():
        markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_addkey_prod|{prod}"))
    bot.send_message(message.chat.id, "👇 اختر المنتج:", reply_markup=markup, parse_mode="HTML")

def admin_manage_prices_menu(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا توجد منتجات.")
    markup = types.InlineKeyboardMarkup()
    for prod in prices_config.keys():
        markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_price_prod|{prod}"))
    bot.send_message(message.chat.id, "👇 اختر منتج لتعديل أسعاره:", reply_markup=markup, parse_mode="HTML")

def admin_delete_key_menu(message):
    if not prices_config:
        return bot.send_message(message.chat.id, "❌ لا توجد منتجات.")
    markup = types.InlineKeyboardMarkup()
    for prod in prices_config.keys():
        markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_delkey_prod|{prod}"))
    bot.send_message(message.chat.id, "👇 اختر المنتج:", reply_markup=markup, parse_mode="HTML")

def admin_view_keys(message):
    status = "🔑 <b>المفاتيح المخزنة:</b>\n\n"
    for prod, plans in keys_store.items():
        status += f"📦 <b>{prod}:</b>\n"
        for plan, lst in plans.items():
            status += f" ├ {plan}: {len(lst)}\n"
    bot.send_message(message.chat.id, status, parse_mode="HTML")

def admin_publish_prices(message):
    pub_text = "📢 <b>قائمة الأسعار:</b>\n\n"
    for prod, plans in prices_config.items():
        pub_text += f"📦 <b>{prod}</b>\n"
        for plan, b_price in plans.items():
            disc = bot_config.get("discount", 0)
            f_price = int(b_price * (1 - disc/100))
            pub_text += f" ├ {plan} ➡️ {f_price} نقطة\n"
    try:
        pub_text += f"\n🤖 للشراء: t.me/{bot.get_me().username}"
    except: pass
    try:
        bot.send_message(CHANNEL_ID, pub_text, parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ تم النشر بالقناة.")
    except:
        bot.send_message(message.chat.id, "❌ تأكد من صلاحيات البوت بالقناة.")

def admin_show_stats_backup(message):
    stats = (f"📊 <b>الإحصائيات:</b>\n\n"
             f"👥 المستخدمين: {len(get_all_user_ids())}\n"
             f"🛒 المبيعات: {bot_config.get('total_sales', 0)}\n"
             f"💰 الأرباح: {bot_config.get('total_earnings', 0)}")
    bot.send_message(message.chat.id, stats, parse_mode="HTML")
    for file_name in [DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
        if os.path.exists(file_name):
            try:
                with open(file_name, "rb") as f_doc:
                    bot.send_document(message.chat.id, f_doc)
            except: pass

# =====================================================================
# 🔁 معالج الأزرار Inline (Callback)
# =====================================================================
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

    # 🔧 إعدادات المهام
    if data.startswith("cfg_q_"):
        if not is_admin(uid, u):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات.", show_alert=True)
        parts = data.split("_")
        task_type, field_type, action = parts[2], parts[3], parts[4]
        t_key = "invite" if task_type == "inv" else ("buy" if task_type == "buy" else "points")
        f_key = "target" if field_type == "t" else "reward"
        step = 1
        if t_key == "points" and f_key == "target": step = 250
        elif t_key == "points" and f_key == "reward": step = 50
        elif f_key == "reward": step = 10
        if "quests" not in bot_config:
            bot_config["quests"] = {"invite": {"target": 5, "reward": 100}, "buy": {"target": 3, "reward": 150}, "points": {"target": 1000, "reward": 200}}
        if action == "up":
            bot_config["quests"][t_key][f_key] += step
        else:
            bot_config["quests"][t_key][f_key] = max(1, bot_config["quests"][t_key][f_key] - step)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "⚙️ تم التحديث!")
        q = bot_config["quests"]
        msg = (f"⚙️ <b>إعدادات المهام:</b>\n\n"
               f"1️⃣ 👥 <b>مهمة الدعوات:</b>\n• الهدف: {q['invite']['target']} | الجائزة: {q['invite']['reward']}\n\n"
               f"2️⃣ 🛒 <b>مهمة المبيعات:</b>\n• الهدف: {q['buy']['target']} | الجائزة: {q['buy']['reward']}\n\n"
               f"3️⃣ 💎 <b>مهمة النقاط:</b>\n• الهدف: {q['points']['target']} | الجائزة: {q['points']['reward']}")
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        except: pass
        return

    # 🔧 إعدادات الصناديق والعجلة
    if data.startswith("cfg_box_") or data.startswith("cfg_wheel_"):
        if not is_admin(uid, u):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات.", show_alert=True)
        if data == "cfg_box_price_up": bot_config["lootbox_price"] = bot_config.get("lootbox_price", 50) + 5
        elif data == "cfg_box_price_down": bot_config["lootbox_price"] = max(5, bot_config.get("lootbox_price", 50) - 5)
        elif data == "cfg_box_chance_up": bot_config["lootbox_chance"] = min(100, bot_config.get("lootbox_chance", 25) + 5)
        elif data == "cfg_box_chance_down": bot_config["lootbox_chance"] = max(1, bot_config.get("lootbox_chance", 25) - 5)
        elif data == "cfg_wheel_price_up": bot_config["wheel_price"] = bot_config.get("wheel_price", 40) + 5
        elif data == "cfg_wheel_price_down": bot_config["wheel_price"] = max(5, bot_config.get("wheel_price", 40) - 5)
        elif data == "cfg_wheel_chance_up": bot_config["wheel_chance"] = min(100, bot_config.get("wheel_chance", 5) + 1)
        elif data == "cfg_wheel_chance_down": bot_config["wheel_chance"] = max(1, bot_config.get("wheel_chance", 5) - 1)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "⚙️ تم التحديث!")
        if "box" in data:
            msg = f"⚙️ <b>إعدادات صندوق الحظ:</b>\n\n• السعر: <b>{bot_config['lootbox_price']} نقطة</b>\n• نسبة الفوز: <b>{bot_config['lootbox_chance']}%</b>"
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("➕ سعر +5", callback_data="cfg_box_price_up"), types.InlineKeyboardButton("➖ سعر -5", callback_data="cfg_box_price_down"))
            markup.row(types.InlineKeyboardButton("📈 نسبة +5%", callback_data="cfg_box_chance_up"), types.InlineKeyboardButton("📉 نسبة -5%", callback_data="cfg_box_chance_down"))
        else:
            msg = f"⚙️ <b>إعدادات عجلة الحظ:</b>\n\n• السعر: <b>{bot_config['wheel_price']} نقطة</b>\n• الجائزة الكبرى: <b>{bot_config['wheel_chance']}%</b>"
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("➕ سعر +5", callback_data="cfg_wheel_price_up"), types.InlineKeyboardButton("➖ سعر -5", callback_data="cfg_wheel_price_down"))
            markup.row(types.InlineKeyboardButton("📈 نسبة +1%", callback_data="cfg_wheel_chance_up"), types.InlineKeyboardButton("📉 نسبة -1%", callback_data="cfg_wheel_chance_down"))
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    # 🎰 صندوق الحظ
    elif data == "game_buy_lootbox":
        price = bot_config.get("lootbox_price", 50)
        if u["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ.", show_alert=True)
        update_user_data(uid, points=-price)
        chance = bot_config.get("lootbox_chance", 25)
        if random.randint(1, 100) <= chance:
            win_pts = random.randint(100, 500)
            update_user_data(uid, points=win_pts, accumulated_points=win_pts)
            bot.edit_message_text(f"🎰 <b>مبروووك الفوز! 🎉</b>\n\n🎁 <b>+{win_pts} نقطة</b> أضيفت لرصيدك!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(f"🎰 <b>الصندوق فارغ 📉</b>\n\nحظاً أوفر في المرة القادمة!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        update_user_rank_and_quests(uid)
        return

    # 🎡 عجلة الحظ
    elif data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if u["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ.", show_alert=True)
        update_user_data(uid, points=-price)
        bot.answer_callback_query(call.id, "💫 جاري التدوير...")
        for frame in ["🎰 [ 🔁 جاري التدوير... ]", "🎡 [ 🔄 المؤشر يتحرك... ]", "🎰 [ 🔁 توقف المؤشر... ]"]:
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
            win_pts = 1000
            update_user_data(uid, points=win_pts, accumulated_points=win_pts)
            bot.edit_message_text(f"🏆 <b>الجائزة الكبرى!!</b> 🔥\n\n👑 <b>+1000 نقطة</b>!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            try:
                pub_msg = f"🎡 <b>انفجار بعجلة الحظ!</b>\n\n🏆 مستخدم فاز بـ <b>+1000 نقطة</b>!\n🤖 جرب حظك: t.me/{bot.get_me().username}"
                bot.send_message(CHANNEL_ID, pub_msg, parse_mode="HTML")
            except: pass
        else:
            if result > 0:
                update_user_data(uid, points=result, accumulated_points=result)
                bot.edit_message_text(f"🎡 توقفت العجلة!\n\n🎁 <b>+{result} نقطة</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            else:
                bot.edit_message_text(f"🎡 توقفت العجلة!\n\n💔 <b>0 نقطة</b> - حظاً أوفر!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        update_user_rank_and_quests(uid)
        return

    # 🛍️ تحديث المتجر
    elif data == "refresh_shop":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        return show_shop_enhanced(call.message, uid, u)

    # 🔧 إضافة مفاتيح
    elif data.startswith("step_addkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"step_addkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\n👇 اختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_addkey_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"📦 <b>{prod}</b> | ⏱️ <b>{plan}</b>\n\n✍️ أرسل المفتاح (أو عدة مفاتيح كل واحد بسطر):", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_save_new_keys(msg, prod, plan))

    elif data.startswith("step_price_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            curr = prices_config.get(prod, {}).get(plan, 0)
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} ({curr} نقطة)", callback_data=f"step_price_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\n👇 اختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_price_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"📦 <b>{prod}</b> | ⏱️ <b>{plan}</b>\n\n✍️ أرسل السعر الجديد:", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_save_new_price(msg, prod, plan))

    elif data.startswith("step_delkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            count = len(keys_store.get(prod, {}).get(plan, []))
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} ({count})", callback_data=f"step_delkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\n👇 اختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("step_delkey_plan|"):
        _, prod, plan = data.split("|")
        keys = keys_store.get(prod, {}).get(plan, [])
        if not keys:
            return bot.answer_callback_query(call.id, "❌ لا توجد مفاتيح.", show_alert=True)
        m = bot.edit_message_text(f"📦 <b>{prod}</b> | ⏱️ <b>{plan}</b>\n\n✍️ أرسل المفتاح أو رقمه التسلسلي:", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(m, lambda msg: process_delete_specific_key(msg, prod, plan))

    # 🎫 التذاكر
    elif data == "confirm_open_ticket":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        m = bot.send_message(call.message.chat.id, "💬 اكتب رسالة الدعم:")
        bot.register_next_step_handler(m, process_support_ticket)

    elif data == "confirm_send_prod_req":
        temp_reqs = bot_config.get("temp_req", {})
        if uid in temp_reqs:
            text_req = temp_reqs[uid]
            req_id = str(random.randint(10000, 99999))
            if "product_requests" not in bot_config: bot_config["product_requests"] = {}
            bot_config["product_requests"][req_id] = {"uid": uid, "text": text_req, "date": datetime.now().isoformat()}
            bot_config["temp_req"].pop(uid, None)
            save_json(DB_CONFIG, bot_config)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, f"✅ تم إرسال طلبك برقم: <code>#{req_id}</code>", parse_mode="HTML")
            try: bot.send_message(ADMIN_PRIMARY, f"💡 طلب #{req_id} من {uid}:\n{text_req}")
            except: pass
        else:
            bot.answer_callback_query(call.id, "❌ انتهت الصلاحية.", show_alert=True)

    elif data == "cancel_action":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "❌ تم الإلغاء.")

    elif data.startswith("view_ticket_"):
        t_id = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if t_id not in tickets:
            return bot.answer_callback_query(call.id, "❌ التذكرة غير موجودة.", show_alert=True)
        t_info = tickets[t_id]
        msg = f"🎫 <b>تذكرة #{t_id}</b>\n\n👤 من: <code>{t_info['uid']}</code>\n📝 {t_info['text']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 رد", callback_data=f"reply_ticket_{t_id}"), types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"close_ticket_{t_id}"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("reply_ticket_"):
        t_id = data.split("_")[2]
        m = bot.send_message(call.message.chat.id, f"✍️ اكتب ردك للتذكرة #{t_id}:")
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
            bot.edit_message_text(f"✅ تم إغلاق #{t_id}", call.message.chat.id, call.message.message_id)

    # 👤 إدارة الأعضاء
    elif data.startswith("adm_"):
        if not is_admin(uid, u):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات.", show_alert=True)
        parts = data.split("_")
        action, target_id = parts[1], parts[2]
        tgt_u = get_user(target_id)
        if not tgt_u:
            return bot.answer_callback_query(call.id, "❌ العضو غير موجود.", show_alert=True)
        if action == "promote":
            update_user_data(target_id, is_admin=True)
            bot.answer_callback_query(call.id, "🛡️ تم الترقية!", show_alert=True)
        elif action == "demote":
            update_user_data(target_id, is_admin=False)
            bot.answer_callback_query(call.id, "⬇️ تم السحب!", show_alert=True)
        elif action == "ban":
            update_user_data(target_id, banned=True)
            bot.answer_callback_query(call.id, "⛔ تم الحظر!", show_alert=True)
        elif action == "tempban":
            until = datetime.now() + timedelta(days=1)
            update_user_data(target_id, banned_until=until.isoformat())
            bot.answer_callback_query(call.id, "⏱️ حظر مؤقت!", show_alert=True)
        elif action == "unban":
            update_user_data(target_id, banned=False, banned_until=None)
            bot.answer_callback_query(call.id, "🟢 فك الحظر!", show_alert=True)
        tgt_u = get_user(target_id)
        role = "أدمن مالك" if int(target_id) == ADMIN_PRIMARY else ("أدمن" if tgt_u.get("is_admin", False) else "عادي")
        ban_st = "محظور نهائي ⛔" if tgt_u.get("banned", False) else ("محظور مؤقت 🔴" if tgt_u.get("banned_until") else "نشط 🟢")
        msg = (f"👥 <b>العضو:</b>\n\n• ID: <code>{target_id}</code>\n• @{tgt_u['username']}\n• الرصيد: {tgt_u['points']}\n• {role}\n• {ban_st}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        if tgt_u.get("is_admin", False):
            markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{target_id}"))
        else:
            markup.add(types.InlineKeyboardButton("🛡️ ترقية أدمن", callback_data=f"adm_promote_{target_id}"))
        markup.add(types.InlineKeyboardButton("⛔ حظر نهائي", callback_data=f"adm_ban_{target_id}"), types.InlineKeyboardButton("⏱️ حظر 24س", callback_data=f"adm_tempban_{target_id}"))
        markup.add(types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"adm_unban_{target_id}"))
        try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass

    # 🌐 اللغة
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
            bot.send_message(call.message.chat.id, "✅ شكراً لاشتراكك!", reply_markup=get_main_keyboard(uid, lang, page=1))
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

    # 🛍️ عرض المنتج
    elif data.startswith("select_prod_"):
        prod = data.split("_", 2)[2]
        if prod not in prices_config: return
        markup = types.InlineKeyboardMarkup()
        u_discount = u.get("rank_discount", 0.0)
        
        info = f"📦 <b>═══ {prod} ═══</b>\n\n"
        info += f"💎 رتبتك تمنحك خصم: <b>{int(u_discount*100)}%</b>\n"
        info += f"💰 رصيدك: <b>{u.get('points', 0)}</b> نقطة\n\n"
        info += f"👇 <b>اختر مدة الاشتراك:</b>\n"
        
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_p = prices_config[prod].get(plan, 0)
            disc = bot_config.get("discount", 0)
            final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
            stock = len(keys_store.get(prod, {}).get(plan, []))
            emoji = "✅" if stock > 0 else "❌"
            markup.add(types.InlineKeyboardButton(f"{emoji} ⏱️ {plan} | 💰 {final_p} Pts | 📊 {stock}", callback_data=f"buy_plan|{prod}|{plan}"))
        
        markup.add(types.InlineKeyboardButton("🔙 رجوع للمتجر", callback_data="refresh_shop"))
        try:
            bot.edit_message_text(info, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            bot.send_message(call.message.chat.id, info, reply_markup=markup, parse_mode="HTML")

    # 🛒 الشراء
    elif data.startswith("buy_plan|"):
        parts = data.split("|")
        prod, plan = parts[1], parts[2]
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config.get("discount", 0)
        u_discount = u.get("rank_discount", 0.0)
        final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
        if u["points"] < final_p:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, "⚠️ نفذت الكمية!", show_alert=True)
        key = keys_store[prod][plan].pop(0)
        update_user_data(uid, points=-final_p)
        bot_config["total_sales"] = bot_config.get("total_sales", 0) + 1
        bot_config["total_earnings"] = bot_config.get("total_earnings", 0) + final_p
        if "sales_log" not in bot_config: bot_config["sales_log"] = []
        bot_config["sales_log"].append({"uid": uid, "username": u["username"], "product": prod, "plan": plan, "price": final_p, "key": key, "date": datetime.now().isoformat()})
        save_json(DB_KEYS, keys_store)
        save_json(DB_CONFIG, bot_config)
        update_user_rank_and_quests(uid)
        bot.edit_message_text(f"🎉 <b>عملية شراء ناجحة!</b>\n\n📦 <b>{prod}</b>\n⏱️ <b>{plan}</b>\n💰 <b>{final_p}</b> نقطة\n\n🔐 <b>مفتاحك:</b>\n<code>{key}</code>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        try:
            pub = f"🔥 <b>عملية بيع جديدة!</b>\n📦 {prod} | ⏱️ {plan}\n💰 {final_p} نقطة\n🤖 t.me/{bot.get_me().username}"
            bot.send_message(CHANNEL_ID, pub, parse_mode="HTML")
        except: pass

# =====================================================================
# 📥 دوال المعالجة (Handlers)
# =====================================================================
def process_save_new_keys(message, prod, plan):
    keys = message.text.strip().split('\n')
    added = 0
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ تم إضافة {added} مفتاح لـ {prod} | {plan}")

def process_save_new_price(message, prod, plan):
    try:
        new_price = int(message.text.strip())
        prices_config[prod][plan] = new_price
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ سعر {prod}/{plan} = {new_price}")
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
    bot.send_message(message.chat.id, "❌ لم يتم العثور على المفتاح.")

def admin_view_member_func(message):
    t_id = message.text.strip()
    u = get_user(t_id)
    if not u:
        return bot.send_message(message.chat.id, "❌ العضو غير موجود.")
    role = "أدمن مالك" if int(t_id) == ADMIN_PRIMARY else ("أدمن" if u.get("is_admin", False) else "عادي")
    ban_st = "محظور ⛔" if u.get("banned", False) else "نشط 🟢"
    msg = f"👥 <b>العضو:</b>\n\n• ID: <code>{t_id}</code>\n• @{u['username']}\n• الرصيد: {u['points']}\n• الرتبة: {u.get('rank', 'عادي')}\n• {role}\n• {ban_st}"
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
        marketing = f"🔥 <b>مبيعات جديدة!</b>\n\n📦 <code>Flourite Cheat</code>\n⏱️ <b>{plan}</b>\n🔐 <code>{fake_key}</code>\n\n🛒 t.me/{bot.get_me().username}"
        bot.send_message(CHANNEL_ID, marketing, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ نشر تسويقي لـ {plan}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {e}")

def process_redeem_user(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in redeem_codes:
        added = redeem_codes.pop(code)
        update_user_data(uid, points=added, accumulated_points=added)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id, f"🎉 تم إضافة +{added} نقطة!")
    else:
        bot.send_message(message.chat.id, "❌ كود غير صحيح أو مستعمل.")

def process_support_ticket(message):
    uid = str(message.from_user.id)
    txt = message.text.strip()
    if not txt: return bot.send_message(message.chat.id, "❌ لا تذكرة فارغة.")
    tid = str(random.randint(10000, 99999))
    if "tickets" not in bot_config: bot_config["tickets"] = {}
    bot_config["tickets"][tid] = {"uid": uid, "text": txt, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ فُتحت التذكرة #{tid}", parse_mode="HTML")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 رد", callback_data=f"reply_ticket_{tid}"), types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"close_ticket_{tid}"))
    try: bot.send_message(ADMIN_PRIMARY, f"🎫 <b>#{tid}</b> من {uid}:\n{txt}", reply_markup=markup, parse_mode="HTML")
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
    bot.send_message(message.chat.id, f"⚠️ <b>تأكيد؟</b>\n\n<code>{txt}</code>", reply_markup=markup, parse_mode="HTML")

def admin_send_reply_ticket_func(message, tid):
    tickets = bot_config.get("tickets", {})
    if tid not in tickets: return bot.send_message(message.chat.id, "❌ لا توجد.")
    reply = message.text.strip()
    try:
        bot.send_message(int(tickets[tid]["uid"]), f"💬 <b>رد #{tid}:</b>\n{reply}", parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ أُرسل الرد للتذكرة #{tid}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {e}")

def admin_add_product_func(message):
    prod = message.text.strip()
    if prod in prices_config:
        return bot.send_message(message.chat.id, "❌ موجود.")
    prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
    keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"➕ أُضيف: {prod}")

def admin_delete_product_func(message):
    prod = message.text.strip()
    if prod not in prices_config:
        return bot.send_message(message.chat.id, "❌ غير موجود.")
    prices_config.pop(prod)
    if prod in keys_store: keys_store.pop(prod)
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ حُذف: {prod}")

def admin_charge_member_func(message):
    try:
        t_id, pts = message.text.strip().split()
        if get_user(t_id):
            update_user_data(t_id, points=int(pts), accumulated_points=int(pts))
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 شُحن {t_id} بـ +{pts}")
            try: bot.send_message(int(t_id), f"🔔 أُضيف +{pts} من الإدارة.")
            except: pass
        else:
            bot.send_message(message.chat.id, "❌ الآيدي غير موجود.")
    except:
        bot.send_message(message.chat.id, "❌ خطأ! صيغة: ID مسافة القيمة")

def admin_create_code_func(message):
    try:
        code, pts = message.text.strip().split()
        redeem_codes[code] = int(pts)
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 كود: <code>{code}</code> = {pts}", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ خطأ! صيغة: CODE مسافة القيمة")

def admin_set_discount_func(message):
    try:
        disc = int(message.text.strip())
        if 0 <= disc < 100:
            bot_config["discount"] = disc
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 خصم عام: {disc}%")
        else:
            bot.send_message(message.chat.id, "❌ قيمة بين 0 و 99")
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
            bot.send_message(message.chat.id, f"✅ المكافأة اليومية = {new_val} نقطة")
        else:
            bot.send_message(message.chat.id, "❌ قيمة سالبة!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ أرقام صحيحة فقط.")

def admin_edit_invite_reward(message):
    try:
        new_val = int(message.text.strip())
        if new_val >= 0:
            bot_config["invite_reward"] = new_val
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ نقاط الإحالة = {new_val} نقطة لكل دعوة")
        else:
            bot.send_message(message.chat.id, "❌ قيمة سالبة!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ أرقام صحيحة فقط.")

# =====================================================================
if __name__ == "__main__":
    print("🚀 البوت يعمل بنجاح مع الأزرار التفاعلية المُصلحة...")
    bot.infinity_polling()
