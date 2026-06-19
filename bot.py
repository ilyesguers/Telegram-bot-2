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
        markup.add(types.KeyboardButton("💡 طلبات المنتجات"), types.KeyboardButton("التالي للمشرف ➡️"))
    else:
        markup.add(types.KeyboardButton("⚙️ إعدادات صندوق الحظ"), types.KeyboardButton("⚙️ إعدادات عجلة الحظ"))
        markup.add(types.KeyboardButton("⚙️ إعدادات المهام الصعبة"), types.KeyboardButton("🔄 واجهة المستخدم"))
        markup.add(types.KeyboardButton("⬅️ سابق المشرف"))
    return markup

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
            try: bot.send_message(int(inviter_id), f"🔗 لقد إنضم مستخدم جديد عن طريق رابط الإحالة الخاص بك! حصلت على {bot_config['invite_reward']} نقاط.")
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
               f"🎁 الجوائز المتاحة بالعجلة: 0 Pts | 10 Pts | 20 Pts | مساوي سعر اللفة | 🏆 <b>الجائزة الكبرى (+1000 نقطة كاملة)</b>")
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
        msg = f"💰 <b>بيانات رصيدك وحسابك:</b>\n\n• ID: {uid}\n• رصيد النقاط: {u['points']} نقطة\n• الرتبة الحالية: {u.get('rank', 'عضو عادي 🔹')}\n• عدد الدعوات الناجحة: {u.get('invite_count', 0)}\n• لغة البوت الحالية: {u['lang'].upper()}\n• حالة الحظر: نشط 🟢"
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

    if data != "check_join":
        if not check_channel_join(uid):
            lang = users.get(uid, {}).get("lang", "ar")
            try: bot.answer_callback_query(call.id, LOCALES[lang]["must_join"], show_alert=True)
            except: pass
            return bot.send_message(call.message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    # 🎮 نظام الأزرار السريعة لتعديل المهام (➕ و ➖)
    if data.startswith("cfg_q_"):
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
            return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات مسؤول.", show_alert=True)
        
        parts = data.split("_")
        task_type = parts[2] # inv, buy, pts
        field_type = parts[3] # t (target) or r (reward)
        action = parts[4] # up or down
        
        t_key = "invite" if task_type == "inv" else ("buy" if task_type == "buy" else "points")
        f_key = "target" if field_type == "t" else "reward"
        
        # مقدار القفزة التلقائية لكل ضغطة زر
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
        except: pass

    elif data.startswith("setlang_"):
        lang = data.split("_")[1]
        users[uid]["lang"] = lang
        save_json(DB_USERS, users)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))

    elif data == "check_join":
        lang = users[uid].get("lang", "ar")
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
        users[uid]["points"] += added_pts
        users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + added_pts
        save_json(DB_USERS, users)
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
        if t_id in users:
            users[t_id]["points"] += int(pts)
            users[t_id]["accumulated_points"] = users[t_id].get("accumulated_points", 0) + int(pts)
            save_json(DB_USERS, users)
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 تم شحن الحساب {t_id} بمقدار +{pts} نقطة.")
            try: bot.send_message(int(t_id), f"🔔 تم إضافة +{pts} رصيد لنقاطك من قبل الإدارة.")
            except: pass
        else: bot.send_message(message.chat.id, "❌ الآيدي غير موجود.")
    except: bot.send_message(message.chat.id, "❌ خطأ بالإدخال، يرجى كتابة الآيدي ثم مسافة ثم المبلغ.")

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
    for u_id in users.keys():
        try:
            bot.send_message(int(u_id), txt)
            success_count += 1
            time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"📢 تم إكمال الإذاعة الشاملة لـ {success_count} عضو.")

def admin_edit_daily_bonus(message):
    try:
        new_bonus = int(message.text.strip())
        if new_bonus >= 0:
            bot_config["daily_bonus"] = new_bonus
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ تم تحديث المكافأة اليومية بنجاح لتصبح: {new_bonus} نقطة.")
        else:
            bot.send_message(message.chat.id, "❌ يجب أن تكون القيمة أكبر من أو تساوي صفر.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال أرقام صحيحة فقط.")

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
