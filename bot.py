import telebot
from telebot import types
import json
import os
import time
import random
import string
from datetime import datetime, timedelta

# 1️⃣ الإعدادات الأساسية والتوكن
API_TOKEN = os.getenv("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

ADMIN_PRIMARY = 5145154527
ADMIN_SECONDARY = 8878290572

CHANNEL_ID = -1003763276411  
CHANNEL_LINK = "https://t.me/evee7x"

DB_USERS = "users_data.json"
DB_KEYS = "keys_store.json"
DB_REDEEM = "redeem_codes.json"
DB_PRICES = "prices_config.json"
DB_CONFIG = "bot_config.json"

# 🏆 قوائم الألقاب والشارات
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
    "flourite_price": 100, # سعر ريسيت الفلورايت الافتراضي
    "sales_log": [],
    "tickets": {},
    "product_requests": {},
    "temp_req": {}
})

# تفعيل الإعدادات التلقائية
if "lootbox_price" not in bot_config: bot_config["lootbox_price"] = 50
if "lootbox_chance" not in bot_config: bot_config["lootbox_chance"] = 25
if "wheel_price" not in bot_config: bot_config["wheel_price"] = 40
if "wheel_chance" not in bot_config: bot_config["wheel_chance"] = 5
if "title_price" not in bot_config: bot_config["title_price"] = 200
if "badge_price" not in bot_config: bot_config["badge_price"] = 150
if "flourite_price" not in bot_config: bot_config["flourite_price"] = 100
if "quests" not in bot_config:
    bot_config["quests"] = {
        "invite": {"target": 15, "reward": 150},
        "buy": {"target": 7, "reward": 200},
        "points": {"target": 5000, "reward": 350}
    }
save_json(DB_CONFIG, bot_config)

# ✨ إعداد الرتب
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
    else:
        updated = False
        if "rank" not in users[uid]:
            users[uid]["rank"] = "عضو عادي 🔹"
            users[uid]["rank_discount"] = 0.0
            updated = True
        if "accumulated_points" not in users[uid]:
            users[uid]["accumulated_points"] = users[uid].get("points", 0)
            updated = True
        if "completed_quests" not in users[uid]:
            users[uid]["completed_quests"] = []
            updated = True
        if "spins" not in users[uid]:
            users[uid]["spins"] = 0
            users[uid]["boxes"] = 0
            users[uid]["active_title"] = ""
            users[uid]["active_badge"] = ""
            updated = True
        if updated: save_json(DB_USERS, users)

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
        try: bot.send_message(int(uid), f"🎉 تهانينا! لقد أنجزت مهمة الدعوات بنجاح:\n👥 دعوة {q['invite']['target']} صديق\n🎁 تم إضافة مكافأتك: <b>+{q['invite']['reward']} نقطة!</b>", parse_mode="HTML")
        except: pass
        
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    if "quest_buy" not in completed and user_buys >= q["buy"]["target"]:
        completed.append("quest_buy")
        u["points"] += q["buy"]["reward"]
        u["accumulated_points"] += q["buy"]["reward"]
        try: bot.send_message(int(uid), f"🎉 تهانينا! لقد أنجزت مهمة المشتريات بنجاح:\n🛒 إتمام {q['buy']['target']} عمليات شراء\n🎁 تم إضافة مكافأتك: <b>+{q['buy']['reward']} نقطة!</b>", parse_mode="HTML")
        except: pass
        
    if "quest_points" not in completed and acc_pts >= q["points"]["target"]:
        completed.append("quest_points")
        u["points"] += q["points"]["reward"]
        u["accumulated_points"] += q["points"]["reward"]
        try: bot.send_message(int(uid), f"🎉 تهانينا! لقد أنجزت مهمة النقاط التراكمية بنجاح:\n💎 تجميع {q['points']['target']} نقطة\n🎁 تم إضافة مكافأتك: <b>+{q['points']['reward']} نقطة!</b>", parse_mode="HTML")
        except: pass
        
    u["completed_quests"] = completed
    save_json(DB_USERS, users)

def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    return f"{fake_key[:6]}***********{fake_key[-4:]}"

LOCALES = {
    "ar": {
        "welcome": "🌐 الرجاء اختيار لغة البوت لتفعيل حسابك / Please select language:",
        "must_join": f"⚠️ يجب عليك الاشتراك في قناتنا أولاً لاستخدام البوت!\nاشترك هنا: {CHANNEL_LINK}",
        "check_btn": "🔄 تحقق من الاشتراك",
        "main_menu": "🏠 القائمة الرئيسية للمتجر:",
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
        "maint_msg": "🛠️ وضع الصيانة مفعل حالياً، نعتذر عن الإزعاج."
    },
    "en": {
        "welcome": "🌐 Please select your language to activate account:",
        "must_join": f"⚠️ You must subscribe to our channel first!\nJoin here: {CHANNEL_LINK}",
        "check_btn": "🔄 Check Subscription",
        "main_menu": "🏠 Store Main Menu:",
        "id_btn": "🆔 Show ID",
        "balance_btn": "💰 My Balance",
        "shop_btn": "🛍️ Product Shop",
        "redeem_btn": "🎁 Redeem Codes",
        "invite_btn": "🔗 Referral System",
        "bonus_btn": "✨ Daily Bonus",
        "support_btn": "💬 Technical Support",
        "req_prod_btn": "💡 Request Product",
        "lang_btn": "🌐 Change Language",
        "admin_btn": "👑 Admin Features",
        "maint_msg": "🛠️ Maintenance mode is currently active."
    },
    "fr": {
        "welcome": "🌐 Veuillez sélectionner votre langue:",
        "must_join": f"⚠️ Vous devez d'abord vous abonner à la chaîne!\nRejoignez: {CHANNEL_LINK}",
        "check_btn": "🔄 Vérifier l'abonnement",
        "main_menu": "🏠 Menu Principal de la Boutique:",
        "id_btn": "🆔 Afficher l'ID",
        "balance_btn": "💰 Mon Solde",
        "shop_btn": "🛍️ Boutique de Produits",
        "redeem_btn": "🎁 Codes de Recharge",
        "invite_btn": "🔗 Système de Parrainage",
        "bonus_btn": "✨ Bonus Quotidien",
        "support_btn": "💬 Support Technique",
        "req_prod_btn": "💡 Demander produit",
        "lang_btn": "🌐 Changer de Langue",
        "admin_btn": "👑 Fonctions Admin",
        "maint_msg": "🛠️ Le mode maintenance est activé."
    },
    "vi": {
        "welcome": "🌐 Vui lòng chọn ngôn ngữ của bạn:",
        "must_join": f"⚠️ Bạn phải đăng ký kênh trước!\nTham gia tại: {CHANNEL_LINK}",
        "check_btn": "🔄 Kiểm tra đăng ký",
        "main_menu": "🏠 Danh Mục Chính Cửa Hàng:",
        "id_btn": "🆔 Hiển thị ID",
        "balance_btn": "💰 Số dư của tôi",
        "shop_btn": "🛍️ Cửa hàng sản phẩm",
        "redeem_btn": "🎁 Nạp mã giảm giá",
        "invite_btn": "🔗 Hệ thống giới thiệu",
        "bonus_btn": "✨ Phần thưởng hàng ngày",
        "support_btn": "💬 Hỗ trợ kỹ thuật",
        "req_prod_btn": "💡 Yêu cầu sản phẩm",
        "lang_btn": "🌐 Thay đổi ngôn ngữ",
        "admin_btn": "👑 Tính năng Admin",
        "maint_msg": "🛠️ Bot hiện đang được bảo trì."
    },
    "es": {
        "welcome": "🌐 Por favor, seleccione el idioma del bot para activar su cuenta:",
        "must_join": f"⚠️ ¡Debe suscribirse a nuestro canal primero para usar el bot!\nÚnase aquí: {CHANNEL_LINK}",
        "check_btn": "🔄 Verificar Suscripción",
        "main_menu": "🏠 Menú Principal de la Tienda:",
        "id_btn": "🆔 Mostrar ID",
        "balance_btn": "💰 Mi Saldo",
        "shop_btn": "🛍️ Tienda de Productos",
        "redeem_btn": "🎁 Canjear Códigos",
        "invite_btn": "🔗 Sistema de Referidos",
        "bonus_btn": "✨ Bono Diario",
        "support_btn": "💬 Soporte Técnico",
        "req_prod_btn": "💡 Solicitar Producto",
        "lang_btn": "🌐 Cambiar Idioma",
        "admin_btn": "👑 Funciones de Admin",
        "maint_msg": "🛠️ El mode de mantenimiento está activo actualmente."
    }
}

def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"),
        types.InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en"),
        types.InlineKeyboardButton("Français 🇫🇷", callback_data="setlang_fr"),
        types.InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="setlang_vi"),
        types.InlineKeyboardButton("Español 🇪🇸", callback_data="setlang_es")
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
        markup.add(types.KeyboardButton(t["lang_btn"]), types.KeyboardButton("التالي ➡️"))
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
            markup.add(types.KeyboardButton(t["admin_btn"]))
    else:
        markup.add(types.KeyboardButton("🎰 صندوق الحظ"), types.KeyboardButton("🎡 عجلة الحظ"))
        markup.add(types.KeyboardButton("🎮 الألعاب والمنافسات"), types.KeyboardButton("🛍️ متجر الألقاب والشارات"))
        markup.add(types.KeyboardButton("💸 تحويل الرصيد (P2P)"), types.KeyboardButton("🔄 ريسيت مفتاح الفلورايت"))
        markup.add(types.KeyboardButton("🔥 المهام الصعبة"), types.KeyboardButton("🏆 رتبتي الحالية"))
        markup.add(types.KeyboardButton("⬅️ السابق"))
    return markup

def get_admin_keyboard(page=1):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if page == 1:
        markup.add(types.KeyboardButton("➕ إضافة منتج"), types.KeyboardButton("❌ حذف منتج"))
        markup.add(types.KeyboardButton("🔑 إضافة مفاتيح"), types.KeyboardButton("👁️ استعراض المفاتيح"))
        markup.add(types.KeyboardButton("🔢 حذف مفتاح معين"), types.KeyboardButton("🗑️ مسح جميع المفاتيح"))
        markup.add(types.KeyboardButton("💵 إدارة الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
        markup.add(types.KeyboardButton("💰 شحن الأعضاء"), types.KeyboardButton("🎫 إنشاء أكواد الشحن"))
        markup.add(types.KeyboardButton("🔥 التخفيضات"), types.KeyboardButton("📢 الإذاعة الشاملة"))
        markup.add(types.KeyboardButton("📤 نشر الأسعار بالقناة"), types.KeyboardButton("📣 التسويق الوهمي"))
        markup.add(types.KeyboardButton("✨ تعديل المكافأة اليومية"), types.KeyboardButton("🔗 تعديل نقاط الدعوة"))
        markup.add(types.KeyboardButton("☁️ النسخ الاحتياطي"), types.KeyboardButton("🎫 إدارة التذاكر"))
        markup.add(types.KeyboardButton("التالي للمشرف ➡️"))
    else:
        markup.add(types.KeyboardButton("⚙️ إعدادات سعر الفلورايت"), types.KeyboardButton("🏷️ إعدادات أسعار الألقاب"))
        markup.add(types.KeyboardButton("⚙️ إعدادات صندوق الحظ"), types.KeyboardButton("⚙️ إعدادات عجلة الحظ"))
        markup.add(types.KeyboardButton("⚙️ إعدادات المهام الصعبة"), types.KeyboardButton("🔄 واجهة المستخدم"))
        markup.add(types.KeyboardButton("⬅️ سابق المشرف"))
    return markup

# 💸 دوال تحويل الرصيد (P2P)
def process_p2p_id(message, t_type):
    target_id = message.text.strip()
    if target_id not in users:
        return bot.send_message(message.chat.id, "❌ هذا الحساب (الآيدي) غير مسجل في البوت!")
    if target_id == str(message.from_user.id):
        return bot.send_message(message.chat.id, "❌ لا يمكنك التحويل لنفسك.")
    m = bot.send_message(message.chat.id, f"✅ تم العثور على الحساب.\nأدخل الآن الكمية التي تود تحويلها (أرقام فقط):")
    bot.register_next_step_handler(m, lambda msg: process_p2p_amount(msg, target_id, t_type))

def process_p2p_amount(message, target_id, t_type):
    uid = str(message.from_user.id)
    try:
        amount = int(message.text.strip())
        if amount <= 0: raise ValueError
    except:
        return bot.send_message(message.chat.id, "❌ يجب إدخال رقم صحيح أكبر من الصفر.")
        
    t_map = {"points": "نقاط", "spins": "عجلات حظ", "boxes": "صناديق حظ"}
    user_bal = users[uid].get(t_type, 0)
    
    if user_bal < amount:
        return bot.send_message(message.chat.id, f"❌ رصيدك غير كافٍ!\nتتملك حالياً: {user_bal} من {t_map[t_type]}")
        
    users[uid][t_type] -= amount
    users[target_id][t_type] = users[target_id].get(t_type, 0) + amount
    save_json(DB_USERS, users)
    
    bot.send_message(message.chat.id, f"✅ **تم التحويل بنجاح!**\nأرسلت `{amount}` {t_map[t_type]} إلى `{target_id}`.", parse_mode="Markdown")
    try:
        bot.send_message(int(target_id), f"🎉 **وصلتك هدية!**\nقام العضو `{uid}` بتحويل `{amount}` {t_map[t_type]} لحسابك.")
    except: pass

# 🏷️ دوال تحديث أسعار الألقاب والشارات (للأدمن)
def admin_set_title_price(message):
    try:
        val = int(message.text)
        bot_config["title_price"] = val
        save_json(DB_CONFIG, bot_config)
        bot.send_message(message.chat.id, f"✅ تم تحديث سعر جميع الألقاب ليصبح: {val} نقطة.")
    except: bot.send_message(message.chat.id, "❌ خطأ، يجب كتابة أرقام فقط.")

def admin_set_badge_price(message):
    try:
        val = int(message.text)
        bot_config["badge_price"] = val
        save_json(DB_CONFIG, bot_config)
        bot.send_message(message.chat.id, f"✅ تم تحديث سعر جميع الشارات ليصبح: {val} نقطة.")
    except: bot.send_message(message.chat.id, "❌ خطأ، يجب كتابة أرقام فقط.")

# 🔄 دوال ريسيت الفلورايت (للمستخدم والإدارة)
def admin_set_flourite_price(message):
    try:
        val = int(message.text.strip())
        bot_config["flourite_price"] = val
        save_json(DB_CONFIG, bot_config)
        bot.send_message(message.chat.id, f"✅ تم تحديث سعر ريسيت الفلورايت بنجاح ليصبح: {val} نقطة.")
    except:
        bot.send_message(message.chat.id, "❌ خطأ، يجب إدخال أرقام صحيحة فقط.")

def user_enter_flourite_key(message, price):
    uid = str(message.from_user.id)
    key_text = message.text.strip()
    
    # خصم النقاط
    users[uid]["points"] -= price
    save_json(DB_USERS, users)
    
    # رسالة للمستخدم
    bot.send_message(message.chat.id, "انتضر البوت يقوم بمعالجة المفتاح...")
    
    # إرسال للإدارة
    admin_msg = f"🔔 **طلب ريسيت فلورايت جديد!**\n👤 المستخدم: {uid} (@{message.from_user.username})\n🔑 المفتاح المطلوب عمل ريسيت له:\n`{key_text}`"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 إرسال رسالة الريسيت للمستخدم", callback_data=f"flourite_reply_{uid}"))
    
    for admin_id in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        try: bot.send_message(admin_id, admin_msg, reply_markup=markup, parse_mode="Markdown")
        except: pass

def admin_send_flourite_reply(message, target_uid):
    reply_text = message.text
    try:
        bot.send_message(int(target_uid), f"✅ **تم الريسيت بنجاح!**\n\nرسالة الإدارة:\n{reply_text}", parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ تم إرسال رسالة الريسيت للمستخدم بنجاح.")
    except:
        bot.send_message(message.chat.id, "❌ فشل الإرسال. قد يكون المستخدم قد قام بحظر البوت.")

# ============================================================
# مسار الرسائل الرئيسي (الذي يعالج الأزرار)
# ============================================================
@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")

    if message.text.startswith('/id'):
        if not check_channel_join(uid):
            lang = users.get(uid, {}).get("lang", "ar")
            return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك هو: <code>{uid}</code>", parse_mode="HTML")
        return

    args = message.text.split()
    if len(args) > 1 and users[uid]["invited_by"] is None:
        inviter_id = args[1]
        if inviter_id in users and inviter_id != uid:
            users[uid]["invited_by"] = inviter_id
            users[inviter_id]["points"] += bot_config["invite_reward"]
            users[inviter_id]["accumulated_points"] += bot_config["invite_reward"]
            users[inviter_id]["invite_count"] += 1
            save_json(DB_USERS, users)
            update_user_rank_and_quests(inviter_id)
            try: bot.send_message(int(inviter_id), f"🔗 لقد إنضم مستخدم جديد عن طريق رابط الإحالة الخاص بك!\nحصلت على {bot_config['invite_reward']} نقاط.")
            except: pass

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
        return bot.send_message(message.chat.id, "❌ نعتذر، حسابك محظور حالياً.")
        
    lang = users[uid].get("lang", "ar")
    txt = message.text

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config["maintenance"] and not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    if txt == "التالي ➡️":
        return bot.send_message(message.chat.id, "🎡 ميزات التسلية والمهام التسويقية الإبداعية المضافة حديثاً للمتجر:", reply_markup=get_main_keyboard(uid, lang, page=2))
        
    elif txt == "⬅️ السابق":
        return bot.send_message(message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))
        
    elif txt == "التالي للمشرف ➡️" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, "⚙️ لوحة تحكم إعدادات الألعاب التسويقية الجديدة لمشرفي النظام:", reply_markup=get_admin_keyboard(page=2))
        
    elif txt == "⬅️ سابق المشرف" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, "👑 لوحة التحكم والميزات الرئيسية للإدارة:", reply_markup=get_admin_keyboard(page=1))

    # --- الميزات المضافة ---
    elif txt == "🔄 ريسيت مفتاح الفلورايت":
        price = bot_config.get("flourite_price", 100)
        if users[uid]["points"] < price:
            return bot.send_message(message.chat.id, f"❌ رصيدك غير كافٍ. يتطلب الريسيت {price} نقطة للاستمرار.")
        m = bot.send_message(message.chat.id, f"🔑 **ريسيت مفتاح الفلورايت:**\nسعر الخدمة: {price} نقطة.\n\nمن فضلك أرسل المفتاح الذي ترغب بعمل ريسيت له الآن:")
        bot.register_next_step_handler(m, lambda msg: user_enter_flourite_key(msg, price))

    elif txt == "⚙️ إعدادات سعر الفلورايت" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        current_price = bot_config.get("flourite_price", 100)
        m = bot.send_message(message.chat.id, f"⚙️ **إعدادات سعر الفلورايت:**\nالسعر الحالي للريسيت هو: {current_price} نقطة.\n\nأرسل السعر الجديد الآن (أرقام فقط):")
        bot.register_next_step_handler(m, admin_set_flourite_price)

    elif txt == "🏷️ إعدادات أسعار الألقاب" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚙️ تعديل سعر الألقاب", callback_data="admin_edit_title_price"))
        markup.add(types.InlineKeyboardButton("⚙️ تعديل سعر الشارات", callback_data="admin_edit_badge_price"))
        bot.send_message(message.chat.id, "⚙️ اختر الإعداد الذي ترغب بتعديله:", reply_markup=markup)

    elif txt == "💸 تحويل الرصيد (P2P)":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("💰 تحويل نقاط", callback_data="p2p_points"),
            types.InlineKeyboardButton("🎡 تحويل عجلات حظ", callback_data="p2p_spins"),
            types.InlineKeyboardButton("🎁 تحويل صناديق حظ", callback_data="p2p_boxes")
        )
        bot.send_message(message.chat.id, "🔄 **نظام التحويل الآمن بين الأعضاء:**\nاختر نوع الرصيد الذي تريد إرساله لصديقك:", reply_markup=markup, parse_mode="Markdown")

    elif txt == "🛍️ متجر الألقاب والشارات":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🎭 تصفح الألقاب", callback_data="shop_titles"),
            types.InlineKeyboardButton("🎖️ تصفح الشارات", callback_data="shop_badges")
        )
        bot.send_message(message.chat.id, "🛍️ **متجر الألقاب والشارات المميزة:**\nاشترِ لقباً أو شارة لتظهر بجوار اسمك في لوحة معلوماتك!", reply_markup=markup, parse_mode="Markdown")

    elif txt == "🎮 الألعاب والمنافسات":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("❌ Tic-Tac-Toe (إكس أو) ⭕", callback_data="g_create_xo"),
            types.InlineKeyboardButton("✂️ حجرة ورقة مقص 💎", callback_data="g_create_rps"),
            types.InlineKeyboardButton("🧠 تحدي الذاكرة البصرية 👁️", callback_data="g_create_mem")
        )
        bot.send_message(message.chat.id, "🎮 **تحديات الألعاب المصغرة:**\nراهن بنقاطك (بحد أقصى 3 نقاط) والعب ضد أعضاء آخرين!\nالفائز يأخذ الرهان مضاعفاً.", reply_markup=markup, parse_mode="Markdown")

    elif txt == "🎰 صندوق الحظ":
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

    elif txt == "🎡 عجلة الحظ":
        price = bot_config.get("wheel_price", 40)
        msg = (f"🎡 <b>عجلة الحظ المدفوعة التفاعلية:</b>\n\n"
               f"أدر العجلة الآن وشاهد حظك وهو يتحرك مباشرة أمامك للربح!\n\n"
               f"💸 سعر تدوير اللفة: <b>{price} نقطة</b>\n"
               f"🎁 الجوائز المتاحة بالعجلة: 0 Pts | 10 Pts | 20 Pts | مساوي سعر اللفة | \n🏆 <b>الجائزة الكبرى (+1000 نقطة كاملة)</b>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💫 تدوير عجلة الحظ الآن", callback_data="game_spin_wheel"))
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    elif txt == "🔥 المهام الصعبة":
        update_user_rank_and_quests(uid)
        u = users[uid]
        completed = u.get("completed_quests", [])
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
        msg += f"3️⃣ 💎 تجميع {q['points']['target']} نقطة إجمالاً في حسابك (مجمعة)\n🎁 الجائزة: +{q['points']['reward']} نقطة | الحالة: <b>{st3}</b>\n"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif txt == "🏆 رتبتي الحالية":
        update_user_rank_and_quests(uid)
        u = users[uid]
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

    elif txt == "⚙️ إعدادات صندوق الحظ" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
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

    elif txt == "⚙️ إعدادات عجلة الحظ" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
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

    elif txt == "⚙️ إعدادات المهام الصعبة" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
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

    elif txt in (LOCALES[l]["id_btn"] for l in LOCALES):
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك: <code>{uid}</code>", parse_mode="HTML")

    elif txt in (LOCALES[l]["balance_btn"] for l in LOCALES):
        u = users[uid]
        update_user_rank_and_quests(uid)
        t_active = u.get('active_title', 'لا يوجد')
        b_active = u.get('active_badge', 'لا يوجد')
        msg = f"💰 <b>بيانات رصيدك وحسابك:</b>\n\n• ID: {uid}\n• اللقب الحالي: {t_active}\n• الشارة: {b_active}\n• رصيد النقاط: {u['points']} نقطة\n• عجلات الحظ: {u.get('spins', 0)}\n• صناديق الحظ: {u.get('boxes', 0)}\n• الرتبة الحالية: {u.get('rank', 'عضو عادي 🔹')}\n• عدد الدعوات: {u.get('invite_count', 0)}\n• حالة الحظر: نشط 🟢"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif txt in (LOCALES[l]["lang_btn"] for l in LOCALES):
        bot.send_message(message.chat.id, "🌐 اختر لغة البوت المفضلة لديك:", reply_markup=get_lang_inline())

    elif txt in (LOCALES[l]["bonus_btn"] for l in LOCALES):
        now = datetime.now()
        lc = users[uid].get("last_claim")
        if lc and now < datetime.fromisoformat(lc) + timedelta(days=1):
            bot.send_message(message.chat.id, "❌ لقد استلمت المكافأة اليومية بالفعل، يرجى المحاولة بعد انتهاء 24 ساعة.")
        else:
            users[uid]["last_claim"] = now.isoformat()
            users[uid]["points"] += bot_config["daily_bonus"]
            users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + bot_config["daily_bonus"]
            save_json(DB_USERS, users)
            update_user_rank_and_quests(uid)
            bot.send_message(message.chat.id, f"✨ تم استلام مكافأتك اليومية بنجاح وهي +{bot_config['daily_bonus']} نقاط!")

    elif txt in (LOCALES[l]["invite_btn"] for l in LOCALES):
        bot_user = bot.get_me().username
        link = f"https://t.me/{bot_user}?start={uid}"
        bot.send_message(message.chat.id, f"🔗 <b>نظام الدعوات:</b>\n\nقم بنسخ رابط الإحالة الخاص بك وأرسله لأصدقائك للحصول على نقاط مجانية عند تسجيلهم:\n<code>{link}</code>\n\n🎁 مكافأة الدعوة الحالية: <b>{bot_config['invite_reward']} نقطة</b>", parse_mode="HTML")

    elif txt in (LOCALES[l]["redeem_btn"] for l in LOCALES):
        m = bot.send_message(message.chat.id, "🎁 الرجاء إدخال كود الشحن لإضافة الرصيد تلقائياً:")
        bot.register_next_step_handler(m, process_redeem_user)

    elif txt in (LOCALES[l]["support_btn"] for l in LOCALES):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ نعم، فتح تذكرة", callback_data="confirm_open_ticket"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
        )
        bot.send_message(message.chat.id, "⚠️ <b>تأكيد فتح تذكرة:</b>\nهل أنت متأكد من رغبتك في فتح تذكرة دعم فني جديدة؟", reply_markup=markup, parse_mode="HTML")

    elif txt in (LOCALES[l]["req_prod_btn"] for l in LOCALES):
        m = bot.send_message(message.chat.id, "💡 من فضلك اكتب اسم وتفاصيل المنتج الذي ترغب في إضافته للمتجر بالتفصيل:")
        bot.register_next_step_handler(m, process_product_request_input)

    elif txt in (LOCALES[l]["shop_btn"] for l in LOCALES):
        if not prices_config:
            return bot.send_message(message.chat.id, "📭 لا توجد منتجات متوفرة بالمتجر حالياً.")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"select_prod_{prod}"))
        bot.send_message(message.chat.id, "🛍️ <b>متجر المنتجات</b>\nالرجاء اختيار المنتج المراد تصفحه:", reply_markup=markup, parse_mode="HTML")

    elif txt in (LOCALES[l]["admin_btn"] for l in LOCALES) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 مرحباً بك في لوحة تحكم ميزات الإدارة للمتجر:", reply_markup=get_admin_keyboard(page=1))

    elif int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False):
        if txt == "🔄 واجهة المستخدم":
            bot.send_message(message.chat.id, "🔙 تم الانتقال إلى واجهة المستخدم العادية.", reply_markup=get_main_keyboard(uid, lang, page=1))

        elif txt == "🎫 إدارة التذاكر":
            tickets = bot_config.get("tickets", {})
            open_tickets = {k: v for k, v in tickets.items() if v.get("status", "open") == "open"}
            if not open_tickets:
                return bot.send_message(message.chat.id, "🎉 لا توجد تذاكر دعم مفتوحة حالياً.")
            markup = types.InlineKeyboardMarkup()
            for t_id, t_info in open_tickets.items():
                markup.add(types.InlineKeyboardButton(f"🎫 #{t_id} - من: {t_info['uid']}", callback_data=f"view_ticket_{t_id}"))
            bot.send_message(message.chat.id, "👇 <b>قائمة التذاكر المفتوحة حالياً:</b>", reply_markup=markup, parse_mode="HTML")

        elif txt == "💡 طلبات المنتجات":
            reqs = bot_config.get("product_requests", {})
            if not reqs:
                return bot.send_message(message.chat.id, "📭 لا توجد طلبات منتجات مقدمة من المستخدمين حالياً.")
            msg = "💡 <b>قائمة طلبات المنتجات الواردة من المستخدمين:</b>\n\n"
            for r_id, r_info in reqs.items():
                msg += f"🔹 <b>طلب #{r_id}</b>\n👤 العضو: <code>{r_info['uid']}</code>\n📦 المنتج المطلوب:\n<code>{r_info['text']}</code>\n📅 التاريخ: {r_info.get('date','')[:10]}\n──────────────────\n"
            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        elif txt == "➕ إضافة منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج الجديد:")
            bot.register_next_step_handler(m, admin_add_product_func)

        elif txt == "❌ حذف منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج المراد حذفه بالكامل:")
            bot.register_next_step_handler(m, admin_delete_product_func)

        elif txt == "🔑 إضافة مفاتيح":
            if not prices_config:
                return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد، قم بإضافة منتج أولاً.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys():
                markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_addkey_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 <b>اختر المنتج الذي تريد إضافة مفاتيح له:</b>", reply_markup=markup, parse_mode="HTML")

        elif txt == "💵 إدارة الأسعار":
            if not prices_config:
                return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys():
                markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_price_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 <b>اختر المنتج الذي تريد تعديل أسعاره:</b>", reply_markup=markup, parse_mode="HTML")

        elif txt == "🔢 حذف مفتاح معين":
            if not prices_config:
                return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys():
                markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_delkey_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 <b>اختر المنتج الذي تريد حذف مفتاح منه:</b>", reply_markup=markup, parse_mode="HTML")

        elif txt == "👁️ استعراض المفاتيح":
            status = "🔑 <b>جميع المفاتيح المخزنة في النظام:</b>\n\n"
            for prod, plans in keys_store.items():
                status += f"📦 <b>{prod}:</b>\n"
                for plan, lst in plans.items():
                    status += f" ├ {plan}: {len(lst)} مفتاح متوفر\n"
            bot.send_message(message.chat.id, status, parse_mode="HTML")

        elif txt == "🗑️ مسح جميع المفاتيح":
            keys_store.clear()
            for prod in prices_config.keys(): keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
            save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, "🗑️ تم مسح جميع المفاتيح المخزنة دفعة واحدة بنجاح.")

        elif txt == "👥 إدارة الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو لعرض تفاصيله والتحكم في رتبته وحظره بالأزرار:")
            bot.register_next_step_handler(m, admin_view_member_func)

        elif txt == "💰 شحن الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي المستخدم ثم مسافة ثم القيمة (مثال: 123456789 500):")
            bot.register_next_step_handler(m, admin_charge_member_func)

        elif txt == "🎫 إنشاء أكواد الشحن":
            m = bot.send_message(message.chat.id, "✍️ أرسل الكود المراد إنشاؤه متبوعاً بقيمته (مثال: FREE100 100):")
            bot.register_next_step_handler(m, admin_create_code_func)

        elif txt == "🔥 التخفيضات":
            m = bot.send_message(message.chat.id, "✍️ أرسل النسبة المئوية الجديدة للتخفيض العام (مثال: 10 أو 20 أو 50):")
            bot.register_next_step_handler(m, admin_set_discount_func)

        elif txt == "📢 الإذاعة الشاملة":
            m = bot.send_message(message.chat.id, "✍️ أرسل نص الرسالة التي ترغب بإذاعتها لجميع الأعضاء:")
            bot.register_next_step_handler(m, admin_broadcast_func)

        elif txt == "📤 نشر الأسعار بالقناة":
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

        elif txt == "📣 التسويق الوهمي":
            m = bot.send_message(message.chat.id, "⚠️ <b>تأكيد الإجراء:</b> من فضلك اكتب كلمة عشوائية أو كلمة <code>تأكيد</code> لتفادي إرسال منشور التسويق الوهمي بالغلط إلى القناة:", parse_mode="HTML")
            bot.register_next_step_handler(m, admin_confirm_fake_marketing)

        elif txt == "✨ تعديل المكافأة اليومية":
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية للمكافأة: {bot_config['daily_bonus']} نقطة.\n\n✍️ أرسل القيمة الجديدة الآن (أرقام فقط):")
            bot.register_next_step_handler(m, admin_edit_daily_bonus)

        elif txt == "🔗 تعديل نقاط الدعوة":
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية لنقاط الدعوة: {bot_config['invite_reward']} نقطة.\n\n✍️ أرسل القيمة الجديدة الآن (أرقام فقط):")
            bot.register_next_step_handler(m, admin_edit_invite_reward)

        elif txt == "☁️ النسخ الاحتياطي":
            stats = (f"📊 <b>إحصائيات وتقارير المتجر الحالية:</b>\n\n"
                     f"👥 عدد المستخدمين المسجلين: {len(users)}\n"
                     f"🛒 إجمالي عدد المبيعات: {bot_config.get('total_sales', 0)}\n"
                     f"💰 إجمالي الأرباح المكتسبة: {bot_config.get('total_earnings', 0)} نقطة")
            bot.send_message(message.chat.id, stats, parse_mode="HTML")
            for file_name in [DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
                if os.path.exists(file_name):
                    with open(file_name, "rb") as f_doc:
                        bot.send_document(message.chat.id, f_doc)

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    data = call.data

    # -- معالجة ريسيت الفلورايت --
    if data.startswith("flourite_reply_"):
        target_uid = data.split("_")[2]
        m = bot.send_message(call.message.chat.id, f"✍️ اكتب رسالة الريسيت الآن ليتم تحويلها مباشرة للمستخدم صاحب الطلب:")
        bot.register_next_step_handler(m, lambda msg: admin_send_flourite_reply(msg, target_uid))
        return

    # 1. تحديث الأسعار
    if data == "admin_edit_title_price":
        m = bot.send_message(call.message.chat.id, "✏️ أدخل السعر الجديد للألقاب (أرقام فقط):")
        bot.register_next_step_handler(m, admin_set_title_price)
        return
        
    elif data == "admin_edit_badge_price":
        m = bot.send_message(call.message.chat.id, "✏️ أدخل السعر الجديد للشارات (أرقام فقط):")
        bot.register_next_step_handler(m, admin_set_badge_price)
        return

    # 2. تحويل الرصيد
    elif data.startswith("p2p_"):
        t_type = data.split("_")[1]
        m = bot.send_message(call.message.chat.id, f"👤 حسناً، أرسل الآيدي (ID) الخاص بالشخص الذي تريد التحويل إليه:")
        bot.register_next_step_handler(m, lambda msg: process_p2p_id(msg, t_type))
        return

    # 3. متجر الألقاب والشارات
    elif data in ["shop_titles", "shop_badges"]:
        is_title = (data == "shop_titles")
        items = AVAILABLE_TITLES if is_title else AVAILABLE_BADGES
        price = bot_config.get("title_price", 200) if is_title else bot_config.get("badge_price", 150)
        t_type = "title" if is_title else "badge"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for idx, item in enumerate(items):
            markup.add(types.InlineKeyboardButton(f"{item} | {price} 🪙", callback_data=f"buy_item_{t_type}_{idx}"))
        bot.edit_message_text(f"🛍️ **تصفح المتجر:**\nانقر على العنصر لشرائه وتجهيزه مباشرة:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return
        
    elif data.startswith("buy_item_"):
        _, _, item_type, idx = data.split("_")
        idx = int(idx)
        item_name = AVAILABLE_TITLES[idx] if item_type == "title" else AVAILABLE_BADGES[idx]
        price = bot_config.get("title_price", 200) if item_type == "title" else bot_config.get("badge_price", 150)
        
        if users[uid]["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ للشراء!", show_alert=True)
            
        users[uid]["points"] -= price
        if item_type == "title": users[uid]["active_title"] = item_name
        else: users[uid]["active_badge"] = item_name
        save_json(DB_USERS, users)
        
        bot.edit_message_text(f"🎉 **مبروك الشراء!**\nتم خصم {price} نقطة، وتم تجهيز {item_name} في ملفك الشخصي بنجاح.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return

    # 4. الألعاب التنافسية
    elif data.startswith("g_create_"):
        g_type = data.split("_")[2]
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("1 🪙", callback_data=f"wager_{g_type}_1"),
            types.InlineKeyboardButton("2 🪙", callback_data=f"wager_{g_type}_2"),
            types.InlineKeyboardButton("3 🪙", callback_data=f"wager_{g_type}_3")
        )
        bot.edit_message_text("💰 **اختر الرهان بالنقاط لهذه المباراة:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return
        
    elif data.startswith("wager_"):
        _, g_type, wager = data.split("_")
        wager = int(wager)
        if users[uid]["points"] < wager:
            return bot.answer_callback_query(call.id, "❌ رصيدك لا يكفي لهذا الرهان!", show_alert=True)
            
        room_id = f"R{int(time.time())}{random.randint(10,99)}"
        active_games[room_id] = {"type": g_type, "p1": uid, "p2": None, "wager": wager, "r": 1, "p1_s": 0, "p2_s": 0, "moves": {}}
        
        users[uid]["points"] -= wager
        save_json(DB_USERS, users)
        
        gnames = {"xo": "Tic-Tac-Toe ❌⭕", "rps": "حجرة ورقة مقص ✂️", "mem": "الذاكرة البصرية 🧠"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎮 اضغط هنا لقبول التحدي", callback_data=f"join_game_{room_id}"))
        bot.send_message(call.message.chat.id, f"📢 **تحدي جديد متاح!**\n\nاللعبة: {gnames[g_type]}\nالرهان: {wager} نقاط\nالفائز يحصل على: {wager*2}\n\nمن يجرؤ على مواجهة العضو؟", reply_markup=markup, parse_mode="Markdown")
        return
        
    elif data.startswith("join_game_"):
        room_id = data.split("_")[2]
        if room_id not in active_games:
            return bot.answer_callback_query(call.id, "❌ اللعبة غير متاحة أو انتهت.", show_alert=True)
        game = active_games[room_id]
        if game["p1"] == uid:
            return bot.answer_callback_query(call.id, "❌ لا يمكنك اللعب ضد نفسك!", show_alert=True)
        if game["p2"] is not None:
            return bot.answer_callback_query(call.id, "❌ الغرفة ممتلئة!", show_alert=True)
        if users[uid]["points"] < game["wager"]:
            return bot.answer_callback_query(call.id, "❌ رصيدك لا يكفي لدخول الرهان!", show_alert=True)
            
        users[uid]["points"] -= game["wager"]
        save_json(DB_USERS, users)
        game["p2"] = uid
        
        bot.edit_message_text("⚔️ **بدأ التحدي! تجهزوا...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
        if game["type"] == "rps":
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(types.InlineKeyboardButton("💎", callback_data=f"grps_{room_id}_R"), types.InlineKeyboardButton("📄", callback_data=f"grps_{room_id}_P"), types.InlineKeyboardButton("✂️", callback_data=f"grps_{room_id}_S"))
            bot.send_message(call.message.chat.id, f"🏁 الجولة {game['r']} من 3\nاختر حركتك:", reply_markup=markup)
        
        elif game["type"] == "mem":
            pool = ["🔥", "👑", "💎", "🎯", "⚡", "🔮"]
            seq = "".join(random.sample(pool, 4))
            game["seq"] = seq
            bot.send_message(call.message.chat.id, f"🧠 احفظ هذا الرمز بسرعة:\n\n{seq}")
            time.sleep(2)
            choices = [seq]
            while len(choices) < 4:
                wrong = "".join(random.sample(pool, 4))
                if wrong not in choices: choices.append(wrong)
            random.shuffle(choices)
            markup = types.InlineKeyboardMarkup(row_width=2)
            for c in choices: markup.add(types.InlineKeyboardButton(c, callback_data=f"gmem_{room_id}_{c}"))
            bot.send_message(call.message.chat.id, "⏰ اختفى الرمز! أي واحد كان الصحيح؟", reply_markup=markup)
            
        elif game["type"] == "xo":
            game["board"] = [" "]*9
            game["turn"] = game["p1"]
            markup = types.InlineKeyboardMarkup(row_width=3)
            btns = [types.InlineKeyboardButton("⬛", callback_data=f"gxo_{room_id}_{i}") for i in range(9)]
            markup.add(*btns)
            bot.send_message(call.message.chat.id, "❌⭕ **لعبة إكس أو**\nدور اللاعب الأول (❌):", reply_markup=markup)
        return

    # منطق حجرة ورقة مقص
    elif data.startswith("grps_"):
        _, room_id, move = data.split("_")
        game = active_games.get(room_id)
        if not game or uid not in [game["p1"], game["p2"]]: return
        game["moves"][uid] = move
        bot.answer_callback_query(call.id, "تم تسجيل حركتك!")
        
        if len(game["moves"]) == 2:
            m1, m2 = game["moves"][game["p1"]], game["moves"][game["p2"]]
            emjs = {"R": "💎", "P": "📄", "S": "✂️"}
            
            if m1 == m2: res = "تعادل!"
            elif (m1=="R" and m2=="S") or (m1=="P" and m2=="R") or (m1=="S" and m2=="P"):
                game["p1_s"] += 1; res = "نقطة للاعب الأول!"
            else:
                game["p2_s"] += 1; res = "نقطة للاعب الثاني!"
                
            bot.send_message(call.message.chat.id, f"💥 النتيجة:\nالأول: {emjs[m1]} | الثاني: {emjs[m2]}\n{res}")
            
            game["r"] += 1
            game["moves"] = {}
            if game["r"] > 3 or game["p1_s"]==2 or game["p2_s"]==2:
                win_id = game["p1"] if game["p1_s"] > game["p2_s"] else (game["p2"] if game["p2_s"] > game["p1_s"] else None)
                if win_id:
                    users[win_id]["points"] += game["wager"] * 2
                    save_json(DB_USERS, users)
                    bot.send_message(call.message.chat.id, f"🏆 انتهت المباراة! الفائز أخذ {game['wager']*2} نقطة!")
                else:
                    users[game["p1"]]["points"] += game["wager"]
                    users[game["p2"]]["points"] += game["wager"]
                    save_json(DB_USERS, users)
                    bot.send_message(call.message.chat.id, "🤝 انتهت المباراة بالتعادل، تم استرجاع الرهان.")
                del active_games[room_id]
            else:
                markup = types.InlineKeyboardMarkup(row_width=3)
                markup.add(types.InlineKeyboardButton("💎", callback_data=f"grps_{room_id}_R"), types.InlineKeyboardButton("📄", callback_data=f"grps_{room_id}_P"), types.InlineKeyboardButton("✂️", callback_data=f"grps_{room_id}_S"))
                bot.send_message(call.message.chat.id, f"🏁 الجولة {game['r']} من 3\nاختر حركتك:", reply_markup=markup)
        return

    # منطق الذاكرة البصرية
    elif data.startswith("gmem_"):
        _, room_id, choice = data.split("_")
        game = active_games.get(room_id)
        if not game or uid not in [game["p1"], game["p2"]]: return
        if uid in game["moves"]: return
        game["moves"][uid] = choice
        
        if choice == game["seq"]:
            if uid == game["p1"]: game["p1_s"] += 1
            else: game["p2_s"] += 1
            bot.send_message(call.message.chat.id, "🎯 إجابة صحيحة!\nحصلت على نقطة.")
        else:
            bot.send_message(call.message.chat.id, "❌ إجابة خاطئة!")
            
        if len(game["moves"]) == 2:
            game["r"] += 1
            game["moves"] = {}
            if game["r"] > 3:
                win_id = game["p1"] if game["p1_s"] > game["p2_s"] else (game["p2"] if game["p2_s"] > game["p1_s"] else None)
                if win_id:
                    users[win_id]["points"] += game["wager"] * 2
                    save_json(DB_USERS, users)
                    bot.send_message(call.message.chat.id, f"🏆 انتهت المباراة! الفائز أخذ {game['wager']*2} نقطة!")
                else:
                    users[game["p1"]]["points"] += game["wager"]
                    users[game["p2"]]["points"] += game["wager"]
                    save_json(DB_USERS, users)
                    bot.send_message(call.message.chat.id, "🤝 تعادل! تم استرجاع الرهان.")
                del active_games[room_id]
            else:
                pool = ["🔥", "👑", "💎", "🎯", "⚡", "🔮"]
                seq = "".join(random.sample(pool, 4))
                game["seq"] = seq
                bot.send_message(call.message.chat.id, f"🧠 الجولة {game['r']}!\nاحفظ هذا الرمز بسرعة:\n\n{seq}")
                time.sleep(2)
                choices = [seq]
                while len(choices) < 4:
                    wrong = "".join(random.sample(pool, 4))
                    if wrong not in choices: choices.append(wrong)
                random.shuffle(choices)
                markup = types.InlineKeyboardMarkup(row_width=2)
                for c in choices: markup.add(types.InlineKeyboardButton(c, callback_data=f"gmem_{room_id}_{c}"))
                bot.send_message(call.message.chat.id, "⏰ اختفى الرمز! أي واحد كان الصحيح؟", reply_markup=markup)
        return

    # منطق الإكس أو
    elif data.startswith("gxo_"):
        _, room_id, pos = data.split("_")
        pos = int(pos)
        game = active_games.get(room_id)
        if not game or uid != game["turn"]: return
        if game["board"][pos] != " ": return
        
        mark = "❌" if uid == game["p1"] else "⭕"
        game["board"][pos] = mark
        game["turn"] = game["p2"] if uid == game["p1"] else game["p1"]
        
        # فحص الفوز
        b = game["board"]
        win_lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        winner = None
        for x,y,z in win_lines:
            if b[x]==b[y]==b[z] and b[x]!=" ": winner = uid
            
        if winner:
            users[winner]["points"] += game["wager"] * 2
            save_json(DB_USERS, users)
            bot.edit_message_text(f"🏆 الفائز هو {mark}!\nربح {game['wager']*2} نقطة.", call.message.chat.id, call.message.message_id)
            del active_games[room_id]
            return
        elif " " not in b:
            users[game["p1"]]["points"] += game["wager"]
            users[game["p2"]]["points"] += game["wager"]
            save_json(DB_USERS, users)
            bot.edit_message_text("🤝 تعادل! تم استرجاع الرهان.", call.message.chat.id, call.message.message_id)
            del active_games[room_id]
            return
            
        markup = types.InlineKeyboardMarkup(row_width=3)
        btns = [types.InlineKeyboardButton(b[i] if b[i]!=" " else "⬛", callback_data=f"gxo_{room_id}_{i}") for i in range(9)]
        markup.add(*btns)
        next_mark = "❌" if game["turn"] == game["p1"] else "⭕"
        bot.edit_message_text(f"دور اللاعب ({next_mark}):", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return

    # -- نهاية الألعاب --

    if data != "check_join":
        if not check_channel_join(uid):
            lang = users.get(uid, {}).get("lang", "ar")
            try: bot.answer_callback_query(call.id, LOCALES[lang]["must_join"], show_alert=True)
            except: pass
            return bot.send_message(call.message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    # 🎮 نظام الأزرار السريعة لتعديل المهام
    if data.startswith("cfg_q_"):
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
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
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
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
        if users[uid]["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيد نقاطك الحالي غير كافٍ لفتح صندوق حظ عشوائي.", show_alert=True)
            
        users[uid]["points"] -= price
        chance = bot_config.get("lootbox_chance", 25)
        
        if random.randint(1, 100) <= chance:
            win_pts = random.randint(100, 500)
            users[uid]["points"] += win_pts
            users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + win_pts
            save_json(DB_USERS, users)
            bot.edit_message_text(f"🎰 <b>مبروووووك الفوز حالفك بنجاح! 🎉🔥</b>\n\nفتحت صندوق الحظ ووجدت بداخله رصيداً كبيراً جداً:\n🎁 <b>+{win_pts} نقطة مضافة فورا لحسابك!</b> كفو يا بطل حظك أسطوري.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            save_json(DB_USERS, users)
            bot.edit_message_text(f"🎰 <b>للأسف.. الصندوق كان فارغاً تقريباً 📉</b>\n\nالحظ لم يحالفك في هذه المرة. لا تستسلم وعاود المحاولة لتعويض خسائرك والفوز بالجائزة القادمة!", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        
        update_user_rank_and_quests(uid)
        return

    elif data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if users[uid]["points"] < price:
            return bot.answer_callback_query(call.id, "❌ رصيد نقاطك غير كافٍ لتدوير عجلة الحظ حالياً.", show_alert=True)
            
        users[uid]["points"] -= price
        save_json(DB_USERS, users)
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
            users[uid]["points"] += win_pts
            users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + win_pts
            save_json(DB_USERS, users)
            
            bot.edit_message_text(f"🏆 <b>المستحيل حدث بالكامل!! حظك أسطوري خارق للعادة! 🔥🎖️</b>\n\nلقد ربحت الآن: 👑 <b>الجائزة الكبرى الهائلة (+1000 نقطة بالرصيد)!</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            
            try:
                pub_msg = f"🎡 <b>انفجار هائل داخل عجلة الحظ!</b>\n\n👤 مستخدم محظوظ قام الآن بتدوير عجلة الحظ المدفوعة وفجر الجائزة المستحيلة:\n🏆 <b>فاز بالجائزة الكبرى (+1000 نقطة كاملة) سحب فوري!</b> 🎉🔥\n🤖 أثبت وجودك وجرب حظك الحقيقي داخل البوت الآن."
                bot.send_message(CHANNEL_ID, pub_msg, parse_mode="HTML")
            except: pass
        else:
            if result > 0:
                users[uid]["points"] += result
                users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + result
                save_json(DB_USERS, users)
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
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات مسؤول لاستخدام هذا الزر.", show_alert=True)
            
        parts = data.split("_")
        action = parts[1]
        target_id = parts[2]
        
        if target_id not in users:
            return bot.answer_callback_query(call.id, "❌ لم يتم العثور على هذا العضو في النظام.", show_alert=True)
            
        if action == "promote":
            users[target_id]["is_admin"] = True
            bot.answer_callback_query(call.id, "🛡️ تم ترقية العضو ليصبح أدمن بنجاح!", show_alert=True)
        elif action == "demote":
            users[target_id]["is_admin"] = False
            bot.answer_callback_query(call.id, "⬇️ تم سحب صلاحيات الإدارة من العضو بنجاح.", show_alert=True)
        elif action == "ban":
            users[target_id]["banned"] = True
            bot.answer_callback_query(call.id, "⛔ تم حظر العضو حظراً نهائياً.", show_alert=True)
        elif action == "tempban":
            until_time = datetime.now() + timedelta(days=1)
            users[target_id]["banned_until"] = until_time.isoformat()
            bot.answer_callback_query(call.id, "⏱️ تم حظر العضو مؤقتاً لمدة 24 ساعة.", show_alert=True)
        elif action == "unban":
            users[target_id]["banned"] = False
            users[target_id]["banned_until"] = None
            bot.answer_callback_query(call.id, "🟢 تم فك الحظر عن العضو بالكامل.", show_alert=True)
            
        save_json(DB_USERS, users)
        
        u = users[target_id]
        role = "أدمن مالك" if int(target_id) == ADMIN_PRIMARY else ("أدمن مدير" if u.get("is_admin", False) else "مستخدم عادي")
        ban_status = "محظور نهائي ⛔" if u.get("banned", False) else ("محظور مؤقت 🔴" if u.get("banned_until") else "نشط 🟢")
        
        updated_msg = (f"👥 <b>بيانات العضو المحدثة:</b>\n\n• ID: <code>{target_id}</code>\n"
                       f"• Username: @{u['username']}\n• الرصيد الحالي: {u['points']} نقطة\n"
                       f"• الرتبة الحالية: {role}\n• حالة الحظر: {ban_status}")
                       
        markup = types.InlineKeyboardMarkup(row_width=2)
        if u.get("is_admin", False):
            markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{target_id}"))
        else:
            markup.add(types.InlineKeyboardButton("🛡️ ترقية إلى أدمن", callback_data=f"adm_promote_{target_id}"))
            
        markup.add(
            types.InlineKeyboardButton("⛔ حظر نهائي", callback_data=f"adm_ban_{target_id}"),
            types.InlineKeyboardButton("⏱️ حظر 24 ساعة", callback_data=f"adm_tempban_{target_id}")
        )
        markup.add(types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"adm_unban_{target_id}"))
        
        try: bot.edit_message_text(updated_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: bot.send_message(call.message.chat.id, updated_msg, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("setlang_"):
        lang = data.split("_")[1]
        users[uid]["lang"] = lang
        save_json(DB_USERS, users)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))

    elif data.startswith("select_prod_"):
        prod = data.split("_")[2]
        if prod not in prices_config: return
        markup = types.InlineKeyboardMarkup()
        u_discount = users.get(uid, {}).get("rank_discount", 0.0)
        
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
        u_discount = users.get(uid, {}).get("rank_discount", 0.0)
        final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
        
        if users[uid]["points"] < final_p:
            return bot.answer_callback_query(call.id, "❌ عذراً! رصيد نقاطك الحالي غير كافٍ.", show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, "⚠️ نعتذر منك! نفذت كمية مفاتيح هذه الخطة من المخزن.", show_alert=True)
            
        delivered_key = keys_store[prod][plan].pop(0)
        users[uid]["points"] -= final_p
        
        bot_config["total_sales"] += 1
        bot_config["total_earnings"] += final_p
        bot_config["sales_log"].append({
            "uid": uid, "username": users[uid]["username"], "product": prod, "plan": plan, "price": final_p, "key": delivered_key, "date": datetime.now().isoformat()
        })
        
        save_json(DB_USERS, users)
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
    if t_id in users:
        u = users[t_id]
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
        bot.send_message(message.chat.id, "❌ لم يتم العثور على العضو في قاعدة البيانات.")

# إكمال الدوال الناقصة لضمان عمل البوت بدون أي أخطاء
def admin_charge_member_func(message):
    try:
        parts = message.text.strip().split()
        uid = parts[0]
        amount = int(parts[1])
        if uid in users:
            users[uid]["points"] += amount
            save_json(DB_USERS, users)
            bot.send_message(message.chat.id, "✅ تم الشحن بنجاح.")
            bot.send_message(int(uid), f"💰 تم شحن رصيدك بـ {amount} نقطة.")
        else:
            bot.send_message(message.chat.id, "❌ المستخدم غير موجود.")
    except: bot.send_message(message.chat.id, "❌ خطأ في الإدخال. تأكد من الصيغة.")

def admin_create_code_func(message):
    try:
        parts = message.text.strip().split()
        code = parts[0]
        amount = int(parts[1])
        redeem_codes[code] = amount
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"✅ تم إنشاء كود الشحن {code} بقيمة {amount} نقطة.")
    except: bot.send_message(message.chat.id, "❌ خطأ في الإدخال.")

def admin_set_discount_func(message):
    try:
        bot_config["discount"] = int(message.text.strip())
        save_json(DB_CONFIG, bot_config)
        bot.send_message(message.chat.id, f"✅ تم تعيين التخفيض بنسبة {bot_config['discount']}%.")
    except: bot.send_message(message.chat.id, "❌ يجب إدخال رقم صحيح.")

def admin_broadcast_func(message):
    txt = message.text
    count = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 **إعلان من الإدارة:**\n\n{txt}", parse_mode="Markdown")
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ تمت الإذاعة بنجاح إلى {count} مستخدم.")

def admin_confirm_fake_marketing(message):
    if message.text.strip() == "تأكيد":
        try:
            bot.send_message(CHANNEL_ID, "🔥 عرض جديد ومميز متاح الآن في البوت! سارع بالشراء قبل نفاذ الكمية.")
            bot.send_message(message.chat.id, "✅ تم نشر إعلان التسويق الوهمي في القناة.")
        except: bot.send_message(message.chat.id, "❌ خطأ في الإرسال للقناة.")
    else: bot.send_message(message.chat.id, "❌ تم الإلغاء.")

def admin_edit_daily_bonus(message):
    try:
        bot_config["daily_bonus"] = int(message.text.strip())
        save_json(DB_CONFIG, bot_config)
        bot.send_message(message.chat.id, "✅ تم تحديث قيمة المكافأة اليومية.")
    except: bot.send_message(message.chat.id, "❌ يجب إدخال رقم صحيح.")

def admin_edit_invite_reward(message):
    try:
        bot_config["invite_reward"] = int(message.text.strip())
        save_json(DB_CONFIG, bot_config)
        bot.send_message(message.chat.id, "✅ تم تحديث قيمة مكافأة الدعوة.")
    except: bot.send_message(message.chat.id, "❌ يجب إدخال رقم صحيح.")

def process_redeem_user(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in redeem_codes:
        amt = redeem_codes.pop(code)
        users[uid]["points"] += amt
        users[uid]["accumulated_points"] += amt
        save_json(DB_USERS, users)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id, f"🎉 مبروك! تم شحن حسابك بقيمة {amt} نقطة.")
    else:
        bot.send_message(message.chat.id, "❌ كود الشحن غير صحيح أو تم استخدامه مسبقاً.")

def process_product_request_input(message):
    req_id = str(random.randint(10000, 99999))
    bot_config["product_requests"][req_id] = {"uid": str(message.from_user.id), "text": message.text, "date": datetime.now().isoformat()}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, "✅ تم إرسال طلبك للإدارة وسيتم مراجعته قريباً.")

def process_support_ticket(message):
    t_id = str(random.randint(1000, 9999))
    bot_config["tickets"][t_id] = {"uid": str(message.from_user.id), "text": message.text, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ تم فتح تذكرة دعم برقم #{t_id}. سيتواصل معك فريق الدعم قريباً.")
    for admin_id in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        try: bot.send_message(admin_id, f"🔔 تذكرة دعم جديدة #{t_id} من العضو {message.from_user.id}:\n{message.text}")
        except: pass

def admin_send_reply_ticket_func(message, t_id):
    if t_id in bot_config["tickets"]:
        u_id = bot_config["tickets"][t_id]["uid"]
        try:
            bot.send_message(int(u_id), f"💬 **رد من الإدارة على تذكرتك #{t_id}:**\n\n{message.text}", parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ تم إرسال الرد للمستخدم بنجاح.")
        except: bot.send_message(message.chat.id, "❌ تعذر إرسال الرد للمستخدم.")
    else: bot.send_message(message.chat.id, "❌ التذكرة غير موجودة.")

def admin_add_product_func(message):
    prod = message.text.strip()
    prices_config[prod] = {"1 Day": 100, "7 Days": 500, "30 Days": 1500}
    keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ تم إضافة المنتج '{prod}' بنجاح للأنظمة. يمكنك الآن تعديل أسعاره ومفاتيحه.")

def admin_delete_product_func(message):
    prod = message.text.strip()
    if prod in prices_config:
        prices_config.pop(prod, None)
        keys_store.pop(prod, None)
        save_json(DB_PRICES, prices_config)
        save_json(DB_KEYS, keys_store)
        bot.send_message(message.chat.id, f"✅ تم حذف المنتج '{prod}' بالكامل من النظام.")
    else:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على هذا المنتج.")

# تشغيل البوت بشكل مستمر
if __name__ == "__main__":
    print("Bot is up and running...")
    bot.infinity_polling()
