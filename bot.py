import telebot
from telebot import types
import json
import os
import time
import random
import string
from datetime import datetime, timedelta

# 1️⃣ الإعدادات الأساسية والتوكن
API_TOKEN = "8868383649:AAEVxFynrH7u_M8e9-wjxo6h8-NP8dtWNUQ"
bot = telebot.TeleBot(API_TOKEN)

ADMIN_PRIMARY = 5145154527
ADMIN_SECONDARY = 88782290572
CHANNEL_USERNAME = "@EVEE7X_FMALIY"
SUPPORT_USER_URL = "https://t.me/EVEE7XX_IOS"

DB_USERS = "users_data.json"
DB_KEYS = "keys_store.json"
DB_REDEEM = "redeem_codes.json"
DB_PRICES = "prices_config.json"
DB_CONFIG = "bot_config.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2) # تقليل الـ indent لتخفيف حجم الملف

users = load_json(DB_USERS, {})
keys_store = load_json(DB_KEYS, {})
redeem_codes = load_json(DB_REDEEM, {})
prices_config = load_json(DB_PRICES, {})
bot_config = load_json(DB_CONFIG, {
    "maintenance": False, 
    "invite_reward": 5, 
    "daily_bonus": 10
})

user_last_msg = {}
def check_spam(uid):
    current_time = time.time()
    if uid in user_last_msg and current_time - user_last_msg[uid] < 0.8:
        return True
    user_last_msg[uid] = current_time
    return False

def is_user_banned(uid):
    uid = str(uid)
    if uid not in users: return False
    if users[uid].get("banned", False): return True
    temp_until = users[uid].get("banned_until")
    if temp_until:
        if datetime.now() < datetime.fromisoformat(temp_until): return True
        else:
            users[uid]["banned_until"] = None
            save_json(DB_USERS, users)
    return False

def check_channel_join(uid):
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]: return True
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, uid)
        if member.status in ['member', 'creator', 'administrator']: return True
    except: pass
    return False

def register_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "username": user.username or f"User_{uid}",
            "points": 0,
            "invited_by": None,
            "invite_count": 0,
            "last_claim": None,
            "lang": "ar",
            "banned": False,
            "banned_until": None,
            "is_admin": uid in [str(ADMIN_PRIMARY), str(ADMIN_SECONDARY)],
            "logged_in": uid in [str(ADMIN_PRIMARY), str(ADMIN_SECONDARY)] # الإدمن معه تصريح تلقائي
        }
        save_json(DB_USERS, users)

def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

# 🌐 تقليص القواميس للغتين فقط لتخفيف الكود
LOCALES = {
    "ar": {
        "welcome": "🌐 الرجاء اختيار لغة البوت لتفعيل حسابك:\nPlease select a language:",
        "must_join": f"⚠️ يجب عليك الاشتراك في قناتنا أولاً لاستخدام البوت!\nاشترك هنا: {CHANNEL_USERNAME}",
        "check_btn": "🔄 تحقق من الاشتراك",
        "main_menu": "🏠 القائمة الرئيسية للمتجر:",
        "id_btn": "🆔 إظهار الآيدي",
        "balance_btn": "💰 رصيدي",
        "shop_btn": "🛍️ متجر المنتجات",
        "redeem_btn": "🎁 أكواد الشحن",
        "invite_btn": "🔗 نظام الدعوات",
        "bonus_btn": "✨ مكافأة يومية",
        "support_btn": "💬 الدعم الفني",
        "lang_btn": "🌐 تغيير اللغة",
        "admin_btn": "👑 الإدارة",
        "maint_msg": "🛠️ وضع الصيانة مفعل حالياً."
    },
    "en": {
        "welcome": "🌐 Please select your language to activate account:",
        "must_join": f"⚠️ You must subscribe to our channel first!\nJoin here: {CHANNEL_USERNAME}",
        "check_btn": "🔄 Check Subscription",
        "main_menu": "🏠 Store Main Menu:",
        "id_btn": "🆔 Show ID",
        "balance_btn": "💰 My Balance",
        "shop_btn": "🛍️ Product Shop",
        "redeem_btn": "🎁 Redeem Codes",
        "invite_btn": "🔗 Referral System",
        "bonus_btn": "✨ Daily Bonus",
        "support_btn": "💬 Support",
        "lang_btn": "🌐 Language",
        "admin_btn": "👑 Admin",
        "maint_msg": "🛠️ Maintenance mode active."
    }
}

def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"),
        types.InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en")
    )
    return markup

def get_main_keyboard(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    t = LOCALES[lang]
    markup.add(types.KeyboardButton(t["id_btn"]), types.KeyboardButton(t["balance_btn"]))
    markup.add(types.KeyboardButton(t["shop_btn"]), types.KeyboardButton(t["redeem_btn"]))
    markup.add(types.KeyboardButton(t["invite_btn"]), types.KeyboardButton(t["bonus_btn"]))
    markup.add(types.KeyboardButton(t["support_btn"]), types.KeyboardButton(t["lang_btn"]))
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
        markup.add(types.KeyboardButton(t["admin_btn"]))
    return markup

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ إضافة منتج"), types.KeyboardButton("❌ حذف منتج"))
    markup.add(types.KeyboardButton("🔑 إضافة مفاتيح"), types.KeyboardButton("👁️ استعراض المفاتيح"))
    markup.add(types.KeyboardButton("💵 إدارة الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
    markup.add(types.KeyboardButton("🎫 إنشاء أكواد الشحن"), types.KeyboardButton("📢 الإذاعة الشاملة"))
    markup.add(types.KeyboardButton("🔑 إعطاء تصريح دخول"), types.KeyboardButton("📤 نشر الأسعار بالقناة"))
    markup.add(types.KeyboardButton("✨ تعديل المكافأة"), types.KeyboardButton("🔄 واجهة المستخدم"))
    return markup

@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")

    # نظام تسجيل الدخول
    if not users[uid].get("logged_in", False):
        return bot.send_message(message.chat.id, "من فضلك احصل على login خصتك لفتح البوت مع ايموجيات جذابة وجميلة رجاء اتصل ب @i6issiiiii للحصول على تصريح")

    if message.text.startswith('/id'):
        return bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك هو: <code>{uid}</code>", parse_mode="HTML")

    args = message.text.split()
    if len(args) > 1 and users[uid]["invited_by"] is None:
        inviter_id = args[1]
        if inviter_id in users and inviter_id != uid:
            users[uid]["invited_by"] = inviter_id
            users[inviter_id]["points"] += bot_config["invite_reward"]
            users[inviter_id]["invite_count"] += 1
            save_json(DB_USERS, users)
            try: bot.send_message(int(inviter_id), f"🔗 انضم مستخدم جديد برابطك! حصلت على {bot_config['invite_reward']} نقطة.")
            except: pass

    bot.send_message(message.chat.id, LOCALES["ar"]["welcome"], reply_markup=get_lang_inline())

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")
        
    if not users[uid].get("logged_in", False):
        return bot.send_message(message.chat.id, "من فضلك احصل على login خصتك لفتح البوت مع ايموجيات جذابة وجميلة رجاء اتصل ب @i6issiiiii للحصول على تصريح")

    lang = users[uid].get("lang", "ar")
    txt = message.text

    if not check_channel_join(uid):
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(LOCALES[lang]["check_btn"], callback_data="check_join"))
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=markup)

    # --- أوامر المستخدم ---
    if txt in [LOCALES["ar"]["id_btn"], LOCALES["en"]["id_btn"]]:
        bot.send_message(message.chat.id, f"🆔 الآيدي: <code>{uid}</code>", parse_mode="HTML")

    elif txt in [LOCALES["ar"]["balance_btn"], LOCALES["en"]["balance_btn"]]:
        u = users[uid]
        bot.send_message(message.chat.id, f"💰 <b>رصيدك:</b>\n\n• النقاط: {u['points']}\n• الدعوات: {u.get('invite_count', 0)}", parse_mode="HTML")

    elif txt in [LOCALES["ar"]["lang_btn"], LOCALES["en"]["lang_btn"]]:
        bot.send_message(message.chat.id, "🌐 اختر لغة البوت:", reply_markup=get_lang_inline())

    elif txt in [LOCALES["ar"]["bonus_btn"], LOCALES["en"]["bonus_btn"]]:
        now = datetime.now()
        lc = users[uid].get("last_claim")
        if lc and now < datetime.fromisoformat(lc) + timedelta(days=1):
            bot.send_message(message.chat.id, "❌ يرجى المحاولة بعد 24 ساعة.")
        else:
            users[uid]["last_claim"] = now.isoformat()
            users[uid]["points"] += bot_config["daily_bonus"]
            save_json(DB_USERS, users)
            bot.send_message(message.chat.id, f"✨ تم استلام +{bot_config['daily_bonus']} نقاط!")

    elif txt in [LOCALES["ar"]["invite_btn"], LOCALES["en"]["invite_btn"]]:
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(message.chat.id, f"🔗 <b>رابط الدعوة:</b>\n<code>{link}</code>\n\n🎁 المكافأة: {bot_config['invite_reward']} نقطة", parse_mode="HTML")

    elif txt in [LOCALES["ar"]["redeem_btn"], LOCALES["en"]["redeem_btn"]]:
        m = bot.send_message(message.chat.id, "🎁 أرسل كود الشحن:")
        bot.register_next_step_handler(m, process_redeem_user)

    elif txt in [LOCALES["ar"]["support_btn"], LOCALES["en"]["support_btn"]]:
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💬 تواصل مع الدعم", url=SUPPORT_USER_URL))
        bot.send_message(message.chat.id, "👨‍💻 الدعم الفني:", reply_markup=markup)

    elif txt in [LOCALES["ar"]["shop_btn"], LOCALES["en"]["shop_btn"]]:
        if not prices_config: return bot.send_message(message.chat.id, "📭 لا توجد منتجات حالياً.")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys(): markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"select_prod_{prod}"))
        bot.send_message(message.chat.id, "🛍️ <b>المتجر:</b> اختر المنتج:", reply_markup=markup, parse_mode="HTML")

    # --- أوامر الإدارة ---
    elif txt in [LOCALES["ar"]["admin_btn"], LOCALES["en"]["admin_btn"]] and users[uid].get("is_admin"):
        bot.send_message(message.chat.id, "👑 لوحة الإدارة:", reply_markup=get_admin_keyboard())

    elif users[uid].get("is_admin"):
        if txt == "🔄 واجهة المستخدم":
            bot.send_message(message.chat.id, "🔙 عودة للمتجر.", reply_markup=get_main_keyboard(uid, lang))
            
        elif txt == "🔑 إعطاء تصريح دخول":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو لمنحه الـ Login:")
            bot.register_next_step_handler(m, admin_grant_login)

        elif txt == "➕ إضافة منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج:")
            bot.register_next_step_handler(m, lambda msg: [prices_config.setdefault(msg.text, {"1 Day": 20, "7 Days": 100, "30 Days": 300}), keys_store.setdefault(msg.text, {"1 Day": [], "7 Days": [], "30 Days": []}), save_json(DB_PRICES, prices_config), save_json(DB_KEYS, keys_store), bot.send_message(msg.chat.id, "✅ تم")])

        elif txt == "❌ حذف منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج للحذف:")
            bot.register_next_step_handler(m, lambda msg: [prices_config.pop(msg.text, None), keys_store.pop(msg.text, None), save_json(DB_PRICES, prices_config), save_json(DB_KEYS, keys_store), bot.send_message(msg.chat.id, "✅ تم الحذف")])

        elif txt == "🔑 إضافة مفاتيح":
            m = bot.send_message(message.chat.id, "✍️ أرسل: [اسم_المنتج] [المدة] [المفتاح]")
            bot.register_next_step_handler(m, admin_add_keys_func)

        elif txt == "🎫 إنشاء أكواد الشحن":
            m = bot.send_message(message.chat.id, "✍️ أرسل الكود وقيمته (مثال: FREE 100):")
            bot.register_next_step_handler(m, lambda msg: [redeem_codes.update({msg.text.split()[0]: int(msg.text.split()[1])}), save_json(DB_REDEEM, redeem_codes), bot.send_message(msg.chat.id, "✅ تم إنشاء الكود")])

        elif txt == "👥 إدارة الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو:")
            bot.register_next_step_handler(m, admin_view_member_func)

def admin_grant_login(message):
    t_id = message.text.strip()
    if t_id in users:
        users[t_id]["logged_in"] = True
        save_json(DB_USERS, users)
        bot.send_message(message.chat.id, f"✅ تم منح تصريح الدخول للعضو {t_id}.")
        try: bot.send_message(int(t_id), "🎉 تم منحك تصريح الدخول! يمكنك الآن استخدام البوت.")
        except: pass
    else: bot.send_message(message.chat.id, "❌ العضو غير مسجل.")

def process_redeem_user(message):
    uid, code = str(message.from_user.id), message.text.strip()
    if code in redeem_codes:
        users[uid]["points"] += redeem_codes.pop(code)
        save_json(DB_USERS, users); save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, "🎉 تم تفعيل الكود بنجاح.")
    else: bot.send_message(message.chat.id, "❌ الكود غير صحيح.")

def admin_add_keys_func(message):
    try:
        parts = message.text.strip().split(" ", 2)
        prod, plan, key_content = parts[0], f"{parts[1]} {parts[2].split()[0]}", parts[2].split(" ", 1)[1] if " " in parts[2] else parts[2]
        if prod in keys_store and plan in ["1 Day", "7 Days", "30 Days"]:
            keys_store[prod][plan].append(key_content); save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, "✅ تمت الإضافة.")
    except: bot.send_message(message.chat.id, "❌ خطأ في الصيغة.")

def admin_view_member_func(message):
    t_id = message.text.strip()
    if t_id in users:
        u = users[t_id]
        msg = f"👥 <b>بيانات:</b>\nID: <code>{t_id}</code>\nالرصيد: {u['points']}\nمحظور: {u.get('banned', False)}"
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("⛔ حظر", callback_data=f"adm_ban_{t_id}"),
            types.InlineKeyboardButton("🟢 فك حظر", callback_data=f"adm_unban_{t_id}")
        )
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ غير مسجل.")

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid, data = str(call.from_user.id), call.data
    
    if data.startswith("adm_") and users[uid].get("is_admin"):
        _, action, target_id = data.split("_")
        if action == "ban": users[target_id]["banned"] = True
        elif action == "unban": users[target_id]["banned"] = False
        save_json(DB_USERS, users)
        bot.answer_callback_query(call.id, "✅ تم تنفيذ الإجراء.", show_alert=True)

    elif data.startswith("setlang_"):
        lang = data.split("_")[1]
        users[uid]["lang"] = lang
        save_json(DB_USERS, users)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang))

    elif data == "check_join":
        lang = users[uid].get("lang", "ar")
        if check_channel_join(uid):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ تم التفعيل!", reply_markup=get_main_keyboard(uid, lang))
        else: bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

    elif data.startswith("select_prod_"):
        prod = data.split("_")[2]
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} | {prices_config[prod].get(plan, 0)} Pts", callback_data=f"buy_{prod}_{plan}"))
        bot.edit_message_text(f"📦 <b>{prod}</b>\nاختر المدة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("buy_"):
        parts = data.split("_")
        prod, plan = parts[1], f"{parts[2]} {parts[3]}" if len(parts) > 3 else parts[2]
        price = prices_config.get(prod, {}).get(plan, 0)
        
        if users[uid]["points"] < price: return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ.", show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []): return bot.answer_callback_query(call.id, "⚠️ نفدت الكمية.", show_alert=True)
            
        key = keys_store[prod][plan].pop(0)
        users[uid]["points"] -= price
        save_json(DB_USERS, users); save_json(DB_KEYS, keys_store)
        bot.edit_message_text(f"🎉 <b>تم الشراء!</b>\n\n📦 {prod} | ⏱️ {plan}\n🔐 <b>مفتاحك:</b> <code>{key}</code>", call.message.chat.id, call.message.message_id, parse_mode="HTML")

if __name__ == "__main__":
    print("🚀 تم تشغيل البوت المخفف بنجاح...")
    bot.infinity_polling()
