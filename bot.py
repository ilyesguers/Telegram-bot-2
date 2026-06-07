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
# اليوزر المختار للدعم الفني
SUPPORT_USERNAME = "EVEE7XX_IOS" 

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
        json.dump(data, f, ensure_ascii=False, indent=4)

users = load_json(DB_USERS, {})
keys_store = load_json(DB_KEYS, {})
redeem_codes = load_json(DB_REDEEM, {})
prices_config = load_json(DB_PRICES, {})
bot_config = load_json(DB_CONFIG, {
    "maintenance": False, 
    "invite_reward": 5, 
    "daily_bonus": 10,
    "total_sales": 0,
    "total_earnings": 0,
    "sales_log": []
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
        if datetime.now() < datetime.fromisoformat(temp_until):
            return True
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
            "is_admin": uid in [str(ADMIN_PRIMARY), str(ADMIN_SECONDARY)]
        }
        save_json(DB_USERS, users)

def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

# 🌐 اللغات: العربية والإنجليزية فقط
LOCALES = {
    "ar": {
        "welcome": "🌐 الرجاء اختيار لغة البوت لتفعيل حسابك:\n\n🌍 Please select language:",
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
        "admin_btn": "👑 ميزات الإدارة",
        "maint_msg": "🛠️ وضع الصيانة مفعل حالياً، نعتذر عن الإزعاج."
    },
    "en": {
        "welcome": "🌐 Please select your language to activate account:",
        "must_join": f"⚠️ You must subscribe to our channel first to use the bot!\nJoin here: {CHANNEL_USERNAME}",
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
        "admin_btn": "👑 Admin Features",
        "maint_msg": "🛠️ Maintenance mode active, sorry for the inconvenience."
    }
}

def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"),
        types.InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en")
    )
    return markup

def get_join_inline(lang):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LOCALES[lang]["check_btn"], callback_data="check_join"))
    return markup

def get_main_keyboard(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    t = LOCALES[lang]
    markup.add(types.KeyboardButton(t["id_btn"]), types.KeyboardButton(t["balance_btn"]))
    markup.add(types.KeyboardButton(t["shop_btn"]), types.KeyboardButton(t["redeem_btn"]))
    markup.add(types.KeyboardButton(t["invite_btn"]), types.KeyboardButton(t["bonus_btn"]))
    
    support_btn = types.KeyboardButton(t["support_btn"])
    markup.add(support_btn, types.KeyboardButton(t["lang_btn"]))
    
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
        markup.add(types.KeyboardButton(t["admin_btn"]))
    return markup

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ إضافة منتج"), types.KeyboardButton("❌ حذف منتج"))
    markup.add(types.KeyboardButton("🔑 إضافة مفاتيح"), types.KeyboardButton("👁️ استعراض المفاتيح"))
    markup.add(types.KeyboardButton("🔢 حذف مفتاح معين"), types.KeyboardButton("🗑️ مسح جميع المفاتيح"))
    markup.add(types.KeyboardButton("💵 إدارة الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
    markup.add(types.KeyboardButton("📢 الإذاعة الشاملة"), types.KeyboardButton("📤 نشر الأسعار بالقناة"))
    markup.add(types.KeyboardButton("📣 التسويق الوهمي"), types.KeyboardButton("✨ تعديل المكافأة اليومية"))
    markup.add(types.KeyboardButton("🔗 تعديل نقاط الدعوة"), types.KeyboardButton("🔄 واجهة المستخدم"))
    return markup

@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")

    if message.text.startswith('/id'):
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك هو: <code>{uid}</code>", parse_mode="HTML")
        return
    
    bot.send_message(message.chat.id, LOCALES["ar"]["welcome"], reply_markup=get_lang_inline())

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")
        
    lang = users[uid].get("lang", "ar")
    txt = message.text

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    # --- أزرار المستخدمين ---
    # استخدام in [ar, en] يضمن استجابة الزر حتى لو ضغط عليه المستخدم بلغة مختلفة قبل التحديث
    if txt in [LOCALES["ar"]["id_btn"], LOCALES["en"]["id_btn"]]:
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك: <code>{uid}</code>", parse_mode="HTML")

    elif txt in [LOCALES["ar"]["balance_btn"], LOCALES["en"]["balance_btn"]]:
        u = users[uid]
        msg = f"💰 <b>بيانات رصيدك:</b>\n\n• النقاط: {u['points']}\n• عدد الدعوات: {u.get('invite_count', 0)}"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif txt in [LOCALES["ar"]["lang_btn"], LOCALES["en"]["lang_btn"]]:
        bot.send_message(message.chat.id, LOCALES[lang]["welcome"], reply_markup=get_lang_inline())

    elif txt in [LOCALES["ar"]["support_btn"], LOCALES["en"]["support_btn"]]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 تواصل مع الدعم", url=f"tg://resolve?domain={SUPPORT_USERNAME}"))
        bot.send_message(message.chat.id, "💬 اضغط على الزر أدناه للتواصل مع الدعم الفني مباشرة:", reply_markup=markup)

    elif txt in [LOCALES["ar"]["shop_btn"], LOCALES["en"]["shop_btn"]]:
        if not prices_config:
            return bot.send_message(message.chat.id, "📭 لا توجد منتجات متوفرة حالياً.")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"select_prod_{prod}"))
        bot.send_message(message.chat.id, "🛍️ اختر منتجاً:", reply_markup=markup)

    # --- واجهة الإدارة ---
    elif txt in [LOCALES["ar"]["admin_btn"], LOCALES["en"]["admin_btn"]] and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 لوحة الإدارة:", reply_markup=get_admin_keyboard())

    elif int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False):
        if txt == "🔄 واجهة المستخدم":
            bot.send_message(message.chat.id, "🔙 تم العودة للقائمة الرئيسية.", reply_markup=get_main_keyboard(uid, lang))
        
        elif txt == "➕ إضافة منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج:")
            bot.register_next_step_handler(m, lambda msg: bot.send_message(msg.chat.id, "✅ وظيفة الإضافة قيد التنفيذ.")) # يمكنك إضافة دوالك هنا
            
        elif txt == "👥 إدارة الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو:")
            bot.register_next_step_handler(m, lambda msg: bot.send_message(msg.chat.id, "✅ وظيفة إدارة الأعضاء قيد التنفيذ.")) # يمكنك إضافة دوالك هنا

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    data = call.data
    
    # معالجة تغيير اللغة لكي يفتح الكيبورد مباشرة باللغة المختارة
    if data.startswith("setlang_"):
        lang = data.split("_")[1]
        if uid in users:
            users[uid]["lang"] = lang
            save_json(DB_USERS, users)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang))
            
    elif data == "check_join":
        lang = users[uid].get("lang", "ar")
        if check_channel_join(uid):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang))
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد! / You have not subscribed yet!", show_alert=True)

if __name__ == "__main__":
    bot.infinity_polling()
