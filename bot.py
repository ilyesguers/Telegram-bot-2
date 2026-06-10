import telebot
from telebot import types
import json
import os
import time
import random
import string
import requests
from datetime import datetime, timedelta

# 1️⃣ الإعدادات الأساسية والتوكن
API_TOKEN = "8868383649:AAEVxFynrH7u_M8e9-wjxo6h8-NP8dtWNUQ"
bot = telebot.TeleBot(API_TOKEN)

ADMIN_PRIMARY = 5145154527
ADMIN_SECONDARY = 8878290572

CHANNEL_ID = -1003763276411  
CHANNEL_LINK = "https://t.me/evee7x"

# 🔑 مفتاح الذكاء الاصطناعي (Gemini API)
AI_API_KEY = os.getenv("AI_API_KEY", "YOUR_DEFAULT_KEY_HERE")

DB_USERS = "users_data.json"
DB_KEYS = "keys_store.json"
DB_REDEEM = "redeem_codes.json"
DB_PRICES = "prices_config.json"
DB_CONFIG = "bot_config.json"

# 🏆 قوائم الألقاب والشارات المضافة حديثاً
AVAILABLE_TITLES = [
    "𓆩👑𓆪 المـ👑ـلك", "𓆩🔥𓆪 الأسـ🔥ـطورة", "𓆩⚔️𓆪 الـجـلاد", "𓆩💎𓆪 الـمـاسـي", 
    "𓆩⚡𓆪 الـمـشـع", "𓆩👻𓆪 الـشـبح", "𓆩🎯𓆪 الـقـنـاص", "𓆩✨𓆪 الـمـتـألـق",
    "𓆩🪐𓆪 الـفـضـائـي", "𓆩🐉𓆪 الـتـنـيـن", "𓆩🖤𓆪 الـجـوكر", "𓆩🛡️𓆪 الـمـدافع",
    "𓆩🔮𓆪 الـسـاحـر", "𓆩🌟𓆪 الـنـجـم", "𓆩🐺𓆪 الـذئـب", "𓆩🦅𓆪 الـصـقـر",
    "𓆩 Samurai 𓆪", "𓆩 VIP 𓆪", "𓆩 HERO 𓆪", "𓆩 HACKER 𓆪"
]

AVAILABLE_BADGES = [
    "🥇 شارة الصدارة", "🥈 شارة التميز", "🥉 شارة الكفاح", "🎖️ وسام الشرف",
    "🚀 الصاروخ", "💎 الجوهرة", "🔥 الشعلة", "👑 التاج", "🎯 الهدف",
    "⚡ الصاعقة", "👾 المخترق", "🛸 الغامض", "🍀 المحظوظ", "🧩 الذكي",
    "🌟 المميز", "🎵 الفنان", "🎨 الرسام", "🏆 البطل", "🦁 الأسد", "🦊 الثعلب"
]

# متغيرات الألعاب المباشرة
active_games = {}

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
    "discount": 0, 
    "invite_reward": 5, 
    "daily_bonus": 10,
    "total_sales": 0,
    "total_earnings": 0,
    "sales_log": [],
    "tickets": {},
    "product_requests": {},
    "temp_req": {}
})

# تفعيل الإعدادات التلقائية للميزات الجديدة والمهام الديناميكية بقاعدة البيانات
if "lootbox_price" not in bot_config: bot_config["lootbox_price"] = 50
if "lootbox_chance" not in bot_config: bot_config["lootbox_chance"] = 25
if "wheel_price" not in bot_config: bot_config["wheel_price"] = 40
if "wheel_chance" not in bot_config: bot_config["wheel_chance"] = 5
if "title_price" not in bot_config: bot_config["title_price"] = 200
if "badge_price" not in bot_config: bot_config["badge_price"] = 150
if "quests" not in bot_config:
    bot_config["quests"] = {
        "invite": {"target": 15, "reward": 150},
        "buy": {"target": 7, "reward": 200},
        "points": {"target": 5000, "reward": 350}
    }
save_json(DB_CONFIG, bot_config)

# ✨ إعداد الرتب الثابتة
RANKS = {
    "silver":  {"name": "🥈 رتبة الفضي",     "points_needed": 200,   "discount": 0.01},
    "gold":    {"name": "🥇 رتبة الذهبي",     "points_needed": 600,   "discount": 0.02},
    "diamond": {"name": "💎 رتبة الماسي",     "points_needed": 1500,  "discount": 0.03},
    "hero":    {"name": "⚡ رتبة الهيرو",     "points_needed": 3500,  "discount": 0.04},
    "master":  {"name": "👑 رتبة الماستر",    "points_needed": 7000,  "discount": 0.045},
    "legend":  {"name": "🏆 رتبة الأسطورة",   "points_needed": 12000, "discount": 0.05}
}

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
        member = bot.get_chat_member(CHANNEL_ID, uid)
        if member.status in ['member', 'creator', 'administrator']: return True
    except: pass
    return False

def register_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "username": user.username or f"User_{uid}",
            "points": 0,
            "spins": 0,
            "boxes": 0,
            "active_title": "",
            "active_badge": "",
            "invited_by": None,
            "invite_count": 0,
            "last_claim": None,
            "lang": "ar",
            "banned": False,
            "banned_until": None,
            "is_admin": uid in [str(ADMIN_PRIMARY), str(ADMIN_SECONDARY)],
            "rank": "عضو عادي 🔹",
            "rank_discount": 0.0,
            "accumulated_points": 0,
            "completed_quests": []
        }
        save_json(DB_USERS, users)

def update_user_rank_and_quests(uid):
    uid = str(uid)
    if uid not in users: return
    u = users[uid]
    
    acc_pts = u.get("accumulated_points", 0)
    current_rank = "عضو عادي 🔹"
    current_discount = 0.0
    for r_key, r_val in RANKS.items():
        if acc_pts >= r_val["points_needed"]:
            current_rank = r_val["name"]
            current_discount = r_val["discount"]
    u["rank"] = current_rank
    u["rank_discount"] = current_discount
    
    completed = u.get("completed_quests", [])
    q = bot_config.get("quests")
    
    if "quest_invite" not in completed and u.get("invite_count", 0) >= q["invite"]["target"]:
        completed.append("quest_invite")
        u["points"] += q["invite"]["reward"]
        u["accumulated_points"] += q["invite"]["reward"]
        
    if "quest_buy" not in completed:
        user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
        if user_buys >= q["buy"]["target"]:
            completed.append("quest_buy")
            u["points"] += q["buy"]["reward"]
            u["accumulated_points"] += q["buy"]["reward"]
        
    if "quest_points" not in completed and acc_pts >= q["points"]["target"]:
        completed.append("quest_points")
        u["points"] += q["points"]["reward"]
        u["accumulated_points"] += q["points"]["reward"]
        
    u["completed_quests"] = completed
    save_json(DB_USERS, users)

def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

LOCALES = {
    "ar": {
        "welcome": "🌐 الرجاء اختيار لغة البوت لتفعيل حسابك",
        "must_join": f"⚠️ يجب عليك الاشتراك في قناتنا أولاً!\nاشترك هنا: {CHANNEL_LINK}",
        "check_btn": "🔄 تحقق من الاشتراك",
        "main_menu": "🏠 القائمة الرئيسية:",
        "id_btn": "🆔 إظهار الآيدي",
        "balance_btn": "💰 رصيدي",
        "shop_btn": "🛍️ متجر المنتجات",
        "redeem_btn": "🎁 أكواد الشحن",
        "invite_btn": "🔗 نظام الدعوات",
        "bonus_btn": "✨ مكافأة يومية",
        "support_btn": "💬 الدعم الفني",
        "req_prod_btn": "💡 طلب منتج جديد",
        "lang_btn": "🌐 تغيير اللغة",
        "admin_btn": "👑 ميزات الإدارة",
        "maint_msg": "🛠️ وضع الصيانة مفعل."
    },
    "en": {
        "welcome": "🌐 Please select your language",
        "must_join": f"⚠️ You must subscribe to our channel first!\nJoin: {CHANNEL_LINK}",
        "check_btn": "🔄 Check Subscription",
        "main_menu": "🏠 Main Menu:",
        "id_btn": "🆔 Show ID",
        "balance_btn": "💰 My Balance",
        "shop_btn": "🛍️ Shop",
        "redeem_btn": "🎁 Redeem",
        "invite_btn": "🔗 Referral",
        "bonus_btn": "✨ Daily Bonus",
        "support_btn": "💬 Support",
        "req_prod_btn": "💡 Request Product",
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

def get_join_inline(lang):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LOCALES[lang]["check_btn"], url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton(LOCALES[lang]["check_btn"], callback_data="check_join"))
    return markup

def get_main_keyboard(uid, lang, page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    t = LOCALES[lang]
    if page == 1:
        markup.add(types.KeyboardButton(t["id_btn"]), types.KeyboardButton(t["balance_btn"]))
        markup.add(types.KeyboardButton(t["shop_btn"]), types.KeyboardButton(t["redeem_btn"]))
        markup.add(types.KeyboardButton(t["invite_btn"]), types.KeyboardButton(t["bonus_btn"]))
        markup.add(types.KeyboardButton(t["support_btn"]), types.KeyboardButton(t["req_prod_btn"]))
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
            markup.add(types.KeyboardButton(t["admin_btn"]))
    return markup

def get_admin_keyboard(page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ إضافة منتج"), types.KeyboardButton("❌ حذف منتج"))
    markup.add(types.KeyboardButton("🔑 إضافة مفاتيح"), types.KeyboardButton("👁️ استعراض المفاتيح"))
    markup.add(types.KeyboardButton("💵 إدارة الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
    markup.add(types.KeyboardButton("💰 شحن الأعضاء"), types.KeyboardButton("🎫 إنشاء أكواد"))
    markup.add(types.KeyboardButton("📢 الإذاعة"), types.KeyboardButton("🤖 المطور والذكاء"))
    return markup

# 🧠 دالة Gemini API المُصلَّحة
def call_gemini_api(prompt, system_inst=""):
    """
    استدعاء Gemini API بطريقة صحيحة مع معالجة الأخطاء
    """
    if not AI_API_KEY or AI_API_KEY == "YOUR_DEFAULT_KEY_HERE":
        print("❌ خطأ: لم يتم تعيين مفتاح API_KEY بشكل صحيح!")
        return None
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_API_KEY}"
        
        # النص الكامل للإرسال
        full_text = f"{system_inst}\n\n{prompt}" if system_inst else prompt
        
        # صيغة الطلب الصحيحة
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_text
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024
            }
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        print(f"📤 إرسال طلب إلى Gemini API...")
        print(f"🔑 المفتاح: {AI_API_KEY[:10]}...")
        
        # إرسال الطلب
        response = requests.post(
            url, 
            json=payload, 
            headers=headers, 
            timeout=30
        )
        
        print(f"📊 رمز الحالة: {response.status_code}")
        
        # معالجة الأخطاء
        if response.status_code != 200:
            print(f"❌ خطأ: {response.status_code}")
            print(f"📝 النص: {response.text}")
            return None
        
        # معالجة الاستجابة الناجحة
        result = response.json()
        
        if 'candidates' not in result or len(result['candidates']) == 0:
            print("❌ لا توجد استجابة من النموذج")
            return None
        
        candidate = result['candidates'][0]
        
        if 'content' not in candidate or 'parts' not in candidate['content']:
            print("❌ صيغة الاستجابة غير صحيحة")
            return None
        
        if len(candidate['content']['parts']) == 0:
            print("❌ لا توجد أجزاء في الاستجابة")
            return None
        
        text = candidate['content']['parts'][0].get('text', '')
        
        if not text:
            print("❌ النص فارغ")
            return None
        
        print(f"✅ تم الحصول على الاستجابة: {text[:50]}...")
        return text
        
    except requests.exceptions.Timeout:
        print("⏱️ انتهت مهلة الانتظار")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"🌐 خطأ في الاتصال: {e}")
        return None
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return None

def process_user_ai(message):
    uid = str(message.from_user.id)
    if message.text in ["⬅️ السابق", "/start"]: 
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    user_lang = users.get(uid, {}).get("lang", "ar")
    
    sys_prompt = f"أنت مساعد ذكي لبوت تليجرام. أجب بلغة {user_lang} بشكل موجز."
    
    reply = call_gemini_api(message.text, sys_prompt)
    
    if reply:
        # تقسيم الرسالة إذا كانت طويلة جداً (حد تليجرام 4096 حرف)
        if len(reply) > 4000:
            for i in range(0, len(reply), 4000):
                bot.send_message(message.chat.id, reply[i:i+4000])
        else:
            bot.send_message(message.chat.id, reply)
    else:
        bot.send_message(message.chat.id, "❌ عذراً، فشل الاتصال بـ AI. تأكد من مفتاح API في المتغيرات البيئية.")

def process_admin_ai_coder(message):
    if message.text in ["⬅️ سابق", "/start"]: 
        return
    
    bot.send_message(message.chat.id, "⚡ جاري توليد الكود...")
    
    sys_prompt = "أنت خبير برمجة Python. اكتب كود الميزة المطلوبة بشكل كامل وجاهز للعمل."
    
    code = call_gemini_api(message.text, sys_prompt)
    
    if code:
        clean_code = code.replace("```python", "").replace("```", "").strip()
        filename = f"AI_Feature_{int(time.time())}.py"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(clean_code)
            
            with open(filename, "rb") as doc:
                bot.send_document(message.chat.id, doc, caption="🚀 تم توليد الميزة بنجاح!")
            
            os.remove(filename)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ في حفظ الملف: {str(e)}")
    else:
        bot.send_message(message.chat.id, "❌ فشل توليد الكود. تحقق من:\n1. مفتاح API\n2. الاتصال بالإنترنت\n3. القيود على الـ API")

# باقي الدوال...
def process_p2p_id(message, t_type):
    target_id = message.text.strip()
    if target_id not in users:
        return bot.send_message(message.chat.id, "❌ الحساب غير مسجل!")
    if target_id == str(message.from_user.id):
        return bot.send_message(message.chat.id, "❌ لا تحول لنفسك.")
    m = bot.send_message(message.chat.id, "✅ أدخل الكمية:")
    bot.register_next_step_handler(m, lambda msg: process_p2p_amount(msg, target_id, t_type))

def process_p2p_amount(message, target_id, t_type):
    uid = str(message.from_user.id)
    try:
        amount = int(message.text.strip())
        if amount <= 0: raise ValueError
    except:
        return bot.send_message(message.chat.id, "❌ أدخل رقم صحيح!")
    
    t_map = {"points": "نقاط", "spins": "عجلات", "boxes": "صناديق"}
    user_bal = users[uid].get(t_type, 0)
    
    if user_bal < amount:
        return bot.send_message(message.chat.id, f"❌ رصيدك: {user_bal}")
    
    users[uid][t_type] -= amount
    users[target_id][t_type] = users[target_id].get(t_type, 0) + amount
    save_json(DB_USERS, users)
    
    bot.send_message(message.chat.id, f"✅ تم التحويل: {amount} {t_map[t_type]}")

@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ حسابك محظور.")

    if message.text.startswith('/id'):
        if not check_channel_join(uid):
            lang = users.get(uid, {}).get("lang", "ar")
            return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))
        bot.send_message(message.chat.id, f"🆔 الآيدي: <code>{uid}</code>", parse_mode="HTML")
        return

    if not check_channel_join(uid):
        lang = users.get(uid, {}).get("lang", "ar")
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    bot.send_message(message.chat.id, LOCALES["ar"]["welcome"], reply_markup=get_lang_inline())

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ حسابك محظور.")
    
    lang = users[uid].get("lang", "ar")
    txt = message.text

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config["maintenance"] and not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    if txt == "🤖 المساعد الذكي (AI)":
        m = bot.send_message(message.chat.id, "🤖 اكتب سؤالك:")
        bot.register_next_step_handler(m, process_user_ai)
        
    elif txt == "🤖 المطور والذكاء الاصطناعي" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📊 ملخص البوت", callback_data="admin_ai_summary"))
        markup.add(types.InlineKeyboardButton("🛠️ المطور", callback_data="admin_ai_coder"))
        bot.send_message(message.chat.id, "اختر:", reply_markup=markup)

    elif txt in (LOCALES[l]["id_btn"] for l in LOCALES):
        bot.send_message(message.chat.id, f"🆔 الآيدي: <code>{uid}</code>", parse_mode="HTML")

    elif txt in (LOCALES[l]["lang_btn"] for l in LOCALES):
        bot.send_message(message.chat.id, "🌐 اختر اللغة:", reply_markup=get_lang_inline())

    elif txt in (LOCALES[l]["admin_btn"] for l in LOCALES) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 لوحة الإدارة:", reply_markup=get_admin_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    data = call.data

    if data == "admin_ai_summary":
        bot.answer_callback_query(call.id, "⏳ جاري التحليل...", show_alert=False)
        
        sys_prompt = "أنت محلل بيانات. لخص الحالة."
        prompt = f"عدد المستخدمين: {len(users)}, المبيعات: {bot_config.get('total_sales',0)}"
        
        res = call_gemini_api(prompt, sys_prompt)
        
        if res:
            bot.send_message(call.message.chat.id, f"📊 **التقرير:**\n\n{res}")
        else:
            bot.send_message(call.message.chat.id, "❌ خطأ في الاتصال بـ AI")
        return
        
    elif data == "admin_ai_coder":
        m = bot.send_message(call.message.chat.id, "🚀 اكتب الميزة المطلوبة:")
        bot.register_next_step_handler(m, process_admin_ai_coder)
        return
        
    elif data.startswith("setlang_"):
        lang = data.split("_")[1]
        users[uid]["lang"] = lang
        save_json(DB_USERS, users)
        bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang))

if __name__ == "__main__":
    print("🚀 البوت يعمل بنجاح...")
    print(f"🔑 مفتاح API: {AI_API_KEY[:10] if AI_API_KEY else 'لم يتم التعيين'}...")
    bot.infinity_polling(skip_pending=True)
