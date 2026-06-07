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

# ملفات قواعد البيانات الخمسة
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
    "tickets": {}
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

# فحص الاشتراك الإجباري الصارم بالقناة
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

# توليد مفتاح وهمي يطابق شكل الصورة image_3.png بطول 16 حرفاً رقمياً هجائياً كبيراً
def generate_fake_key():
    chars = string.ascii_uppercase + string.digits
    fake_key = ''.join(random.choice(chars) for _ in range(16))
    # إظهار أول 6 أحرف وآخر 4 أحرف فقط لحماية الخصوصية بشكل واقعي
    masked_key = f"{fake_key[:6]}***********{fake_key[-4:]}"
    return masked_key

LOCALES = {
    "ar": {
        "welcome": "🌐 الرجاء اختيار لغة البوت لتفعيل حسابك / Please select language:",
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
        "must_join": f"⚠️ You must subscribe to our channel first!\nJoin here: {CHANNEL_USERNAME}",
        "check_btn": "🔄 Check Subscription",
        "main_menu": "🏠 Store Main Menu:",
        "id_btn": "🆔 Show ID",
        "balance_btn": "💰 My Balance",
        "shop_btn": "🛍️ Product Shop",
        "redeem_btn": "🎁 Redeem Codes",
        "invite_btn": "🔗 Referral System",
        "bonus_btn": "✨ Daily Bonus",
        "support_btn": "💬 Technical Support",
        "lang_btn": "🌐 Change Language",
        "admin_btn": "👑 Admin Features",
        "maint_msg": "🛠️ Maintenance mode is currently active."
    },
    "fr": {
        "welcome": "🌐 Veuillez sélectionner votre langue:",
        "must_join": f"⚠️ Vous devez d'abord vous abonner à la chaîne!\nRejoignez: {CHANNEL_USERNAME}",
        "check_btn": "🔄 Vérifier l'abonnement",
        "main_menu": "🏠 Menu Principal de la Boutique:",
        "id_btn": "🆔 Afficher l'ID",
        "balance_btn": "💰 Mon Solde",
        "shop_btn": "🛍️ Boutique de Produits",
        "redeem_btn": "🎁 Codes de Recharge",
        "invite_btn": "🔗 Système de Parrainage",
        "bonus_btn": "✨ Bonus Quotidien",
        "support_btn": "💬 Support Technique",
        "lang_btn": "🌐 Changer de Langue",
        "admin_btn": "👑 Fonctions Admin",
        "maint_msg": "🛠️ Le mode maintenance est activé."
    },
    "vi": {
        "welcome": "🌐 Vui lòng chọn ngôn ngữ của bạn:",
        "must_join": f"⚠️ Bạn phải đăng ký kênh trước!\nTham gia tại: {CHANNEL_USERNAME}",
        "check_btn": "🔄 Kiểm tra đăng ký",
        "main_menu": "🏠 Danh Mục Chính Cửa Hàng:",
        "id_btn": "🆔 Hiển thị ID",
        "balance_btn": "💰 Số dư của tôi",
        "shop_btn": "🛍️ Cửa hàng sản phẩm",
        "redeem_btn": "🎁 Nạp mã giảm giá",
        "invite_btn": "🔗 Hệ thống giới thiệu",
        "bonus_btn": "✨ Phần thưởng hàng ngày",
        "support_btn": "💬 Hỗ trợ kỹ thuật",
        "lang_btn": "Thay đổi ngôn ngữ",
        "admin_btn": "👑 Tính năng Admin",
        "maint_msg": "🛠️ Bot hiện đang được bảo trì."
    }
}

def get_lang_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"),
        types.InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en"),
        types.InlineKeyboardButton("Français 🇫🇷", callback_data="setlang_fr"),
        types.InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="setlang_vi")
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
    markup.add(types.KeyboardButton(t["support_btn"]), types.KeyboardButton(t["lang_btn"]))
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
        markup.add(types.KeyboardButton(t["admin_btn"]))
    return markup

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ إضافة منتج"), types.KeyboardButton("❌ حذف منتج"))
    markup.add(types.KeyboardButton("🔑 إضافة مفاتيح"), types.KeyboardButton("👁️ استعراض المفاتيح"))
    markup.add(types.KeyboardButton("🔢 حذف مفتاح معين"), types.KeyboardButton("🗑️ مسح جميع المفاتيح"))
    markup.add(types.KeyboardButton("💵 إدارة الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
    markup.add(types.KeyboardButton("🔨 صلاحيات الأعضاء"), types.KeyboardButton("💰 شحن الأعضاء"))
    markup.add(types.KeyboardButton("🎫 إنشاء أكواد الشحن"), types.KeyboardButton("🔥 التخفيضات"))
    markup.add(types.KeyboardButton("📢 الإذاعة الشاملة"), types.KeyboardButton("📤 نشر الأسعار بالقناة"))
    markup.add(types.KeyboardButton("📣 التسويق الوهمي"), types.KeyboardButton("☁️ النسخ الاحتياطي"))
    markup.add(types.KeyboardButton("🔄 واجهة المستخدم"))
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

    args = message.text.split()
    if len(args) > 1 and users[uid]["invited_by"] is None:
        inviter_id = args[1]
        if inviter_id in users and inviter_id != uid:
            users[uid]["invited_by"] = inviter_id
            users[inviter_id]["points"] += bot_config["invite_reward"]
            users[inviter_id]["invite_count"] += 1
            save_json(DB_USERS, users)
            try: bot.send_message(int(inviter_id), f"🔗 لقد إنضم مستخدم جديد عن طريق رابط الإحالة الخاص بك! حصلت على {bot_config['invite_reward']} نقاط.")
            except: pass

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

    # التحقق الصارم من الاشتراك - البوت لا يرسل أي رد حتى يتم التأكد من الاشتراك
    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config["maintenance"] and not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    # --- أزرار المستخدمين ---
    if txt in [LOCALES[l]["id_btn"] for l in LOCALES]:
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك: <code>{uid}</code>", parse_mode="HTML")

    elif txt in [LOCALES[l]["balance_btn"] for l in LOCALES]:
        u = users[uid]
        msg = f"💰 <b>بيانات رصيدك وحسابك:</b>\n\n• رصيد النقاط: {u['points']} نقطة\n• عدد الدعوات الناجحة: {u.get('invite_count', 0)}\n• لغة البوت الحالية: {u['lang'].upper()}\n• حالة الحظر: نشط 🟢"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif txt in [LOCALES[l]["lang_btn"] for l in LOCALES]:
        bot.send_message(message.chat.id, "🌐 اختر لغة البوت المفضلة لديك:", reply_markup=get_lang_inline())

    elif txt in [LOCALES[l]["bonus_btn"] for l in LOCALES]:
        now = datetime.now()
        lc = users[uid].get("last_claim")
        if lc and now < datetime.fromisoformat(lc) + timedelta(days=1):
            bot.send_message(message.chat.id, "❌ لقد استلمت المكافأة اليومية بالفعل، يرجى المحاولة بعد انتهاء 24 ساعة.")
        else:
            users[uid]["last_claim"] = now.isoformat()
            users[uid]["points"] += bot_config["daily_bonus"]
            save_json(DB_USERS, users)
            bot.send_message(message.chat.id, f"✨ تم استلام مكافأتك اليومية بنجاح وهي +{bot_config['daily_bonus']} نقاط!")

    elif txt in [LOCALES[l]["invite_btn"] for l in LOCALES]:
        bot_user = bot.get_me().username
        link = f"https://t.me/{bot_user}?start={uid}"
        bot.send_message(message.chat.id, f"🔗 <b>نظام الدعوات:</b>\n\nقم بنسخ رابط الإحالة الخاص بك وأرسله لأصدقائك للحصول على نقاط مجانية عند تسجيلهم:\n<code>{link}</code>", parse_mode="HTML")

    elif txt in [LOCALES[l]["redeem_btn"] for l in LOCALES]:
        m = bot.send_message(message.chat.id, "🎁 الرجاء إدخال كود الشحن لإضافة الرصيد تلقائياً:")
        bot.register_next_step_handler(m, process_redeem_user)

    elif txt in [LOCALES[l]["support_btn"] for l in LOCALES]:
        m = bot.send_message(message.chat.id, "💬 اكتب رسالة الدعم الفني الخاصة بك الآن لفتح تذكرة:")
        bot.register_next_step_handler(m, process_support_ticket)

    elif txt in [LOCALES[l]["shop_btn"] for l in LOCALES]:
        if not prices_config:
            return bot.send_message(message.chat.id, "📭 لا توجد منتجات متوفرة بالمتجر حالياً.")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"select_prod_{prod}"))
        bot.send_message(message.chat.id, "🛍️ <b>متجر المنتجات</b>\nالرجاء اختيار المنتج المراد تصفحه:", reply_markup=markup, parse_mode="HTML")

    # --- واجهة الإدارة ---
    elif txt in [LOCALES[l]["admin_btn"] for l in LOCALES] and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 مرحباً بك في لوحة تحكم ميزات الإدارة للمتجر:", reply_markup=get_admin_keyboard())

    elif int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False):
        if txt == "🔄 واجهة المستخدم":
            bot.send_message(message.chat.id, "🔙 تم الانتقال إلى واجهة المستخدم العادية.", reply_markup=get_main_keyboard(uid, lang))

        elif txt == "🛠️ وضع الصيانة":
            bot_config["maintenance"] = not bot_config["maintenance"]
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🛠️ وضع الصيانة الآن: {'[مفعل] 🔴' if bot_config['maintenance'] else '[معطل] 🟢'}")

        elif txt == "➕ إضافة منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج الجديد:")
            bot.register_next_step_handler(m, admin_add_product_func)

        elif txt == "❌ حذف منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج المراد حذفه بالكامل:")
            bot.register_next_step_handler(m, admin_delete_product_func)

        elif txt == "🔑 إضافة مفاتيح":
            m = bot.send_message(message.chat.id, "✍️ أرسل البيانات بالترتيب الموضح:\n[اسم_المنتج] [المدة: 1 Day أو 7 Days أو 30 Days] [المفتاح]")
            bot.register_next_step_handler(m, admin_add_keys_func)

        elif txt == "👁️ استعراض المفاتيح":
            status = "🔑 <b>جميع المفاتيح المخزنة في النظام:</b>\n\n"
            for prod, plans in keys_store.items():
                status += f"📦 <b>{prod}:</b>\n"
                for plan, lst in plans.items():
                    status += f" ├ {plan}: {len(lst)} مفتاح متوفر\n"
            bot.send_message(message.chat.id, status, parse_mode="HTML")

        elif txt == "🔢 حذف مفتاح معين":
            m = bot.send_message(message.chat.id, "✍️ أرسل الإدخال لحذف مفتاح محدد:\n[اسم_المنتج] [المدة] [رقم_المفتاح]:")
            bot.register_next_step_handler(m, admin_delete_specific_key)

        elif txt == "🗑️ مسح جميع المفاتيح":
            keys_store.clear()
            for prod in prices_config.keys(): keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
            save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, "🗑️ تم مسح جميع المفاتيح المخزنة دفعة واحدة بنجاح.")

        elif txt == "💵 إدارة الأسعار":
            m = bot.send_message(message.chat.id, "✍️ لتغيير سعر أي مدة أرسل بالترتيب:\n[اسم_المنتج] [المدة] [السعر]")
            bot.register_next_step_handler(m, admin_edit_price_func)

        elif txt == "👥 إدارة الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو لعرض تفاصيله:")
            bot.register_next_step_handler(m, admin_view_member_func)

        elif txt == "🔨 صلاحيات الأعضاء":
            m = bot.send_message(message.chat.id, "⚙️ أرسل أحد الأوامر التالية متبوعاً بالآيدي:\n• `ban ID`\n• `tempban ID`\n• `unban ID`\n• `promote ID`\n• `demote ID`")
            bot.register_next_step_handler(m, admin_action_member_func)

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
                bot.send_message(CHANNEL_USERNAME, pub_text, parse_mode="HTML")
                bot.send_message(message.chat.id, "✅ تم نشر وتحديث قائمة الأسعار الحالية في القناة.")
            except: bot.send_message(message.chat.id, "❌ حدث خطأ، يرجى تحقق من صلاحيات البوت بالقناة.")

        elif txt == "📣 التسويق الوهمي":
            # تحديث الأمن: إجبار الأدمن على كتابة كلمة تأكيد لتفادي الإرسال الخاطئ
            m = bot.send_message(message.chat.id, "⚠️ <b>تأكيد الإجراء:</b> من فضلك اكتب كلمة عشوائية أو كلمة <code>تأكيد</code> لتفادي إرسال منشور التسويق الوهمي بالغلط إلى القناة:", parse_mode="HTML")
            bot.register_next_step_handler(m, admin_confirm_fake_marketing)

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

# ==========================================
# 5️⃣ الكولباك لمعالجة العمليات والترخيص
# ==========================================

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    data = call.data

    if data.startswith("setlang_"):
        lang = data.split("_")[1]
        users[uid]["lang"] = lang
        save_json(DB_USERS, users)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang))

    elif data == "check_join":
        lang = users[uid].get("lang", "ar")
        if check_channel_join(uid):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, "✅ شكراً لتعاونك واشتراكك بالقناة، تم تفعيل حسابك!", reply_markup=get_main_keyboard(uid, lang))
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في القناة المطلوبة بعد!", show_alert=True)

    elif data.startswith("select_prod_"):
        prod = data.split("_")[2]
        if prod not in prices_config: return
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_p = prices_config[prod].get(plan, 0)
            disc = bot_config["discount"]
            final_p = int(base_p * (1 - disc/100))
            stock_count = len(keys_store.get(prod, {}).get(plan, []))
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} | {final_p} Pts (المخزن: {stock_count})", callback_data=f"buy_plan_{prod}_{plan}"))
        bot.edit_message_text(f"📦 المنتج المختار: <b>{prod}</b>\nاختر مدة الاشتراك الشراء التلقائي:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("buy_plan_"):
        prod = data.split("_")[2]
        plan = data.split("_")[3] + " " + data.split("_")[4] if len(data.split("_")) > 4 else data.split("_")[3]
        
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config["discount"]
        final_p = int(base_p * (1 - disc/100))
        
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
        
        bot.edit_message_text(f"🎉 <b>تمت عملية الشراء التلقائي بنجاح!</b>\n\n📦 المنتج: <code>{prod}</code>\n⏱️ مدة الاشتراك: <code>{plan}</code>\n💰 السعر المخصوم: {final_p} نقطة\n\n🔐 <b>المفتاح الخاص بك هو:</b>\n<code>{delivered_key}</code>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        
        try:
            pub_notif = f"🔥 <b>عملية بيع موثقة وناجحة!</b>\n\n📦 المنتج المشترى: <code>{prod}</code>\n⏱️ مدة الاشتراك الترخيصي: {plan}\n💰 الثمن المدفوع: {final_p} نقطة\n🤖 تم الشراء والتسليم الفوري عبر نظام البوت المتكامل."
            bot.send_message(CHANNEL_USERNAME, pub_notif, parse_mode="HTML")
        except: pass

# ==========================================
# 6️⃣ دوال الإدارة والتحقق الفني المتكامل
# ==========================================

def admin_confirm_fake_marketing(message):
    # التحقق من أن الأدمن قام بكتابة النص بنجاح لتفادي الإرسال بالخطأ
    confirm_text = message.text.strip()
    if not confirm_text:
        return bot.send_message(message.chat.id, "❌ تم إلغاء العملية بسبب إدخال فارغ.")
        
    # دائماً يتم الاختيار العشوائي للمدة لمنتج Flourite Cheat والمفتاح يطابق صيغة الأكواد في صورة image_3.png
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
        bot.send_message(CHANNEL_USERNAME, marketing_msg, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ تم تأكيد الإجراء بنجاح بعد كتابتك '{confirm_text}'! ونشر منشور التسويق الوهمي لـ <b>Flourite Cheat ({chosen_plan})</b> بقناتك الموثقة.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ تعذر النشر بالقناة، يرجى مراجعة الصلاحيات: {str(e)}")

def process_redeem_user(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in redeem_codes:
        added_pts = redeem_codes.pop(code)
        users[uid]["points"] += added_pts
        save_json(DB_USERS, users)
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎉 تم تفعيل كود الشحن وإضافة +{added_pts} نقطة إلى رصيدك.")
    else: bot.send_message(message.chat.id, "❌ كود الشحن المدخل غير صحيح أو مستعمل مسبقاً.")

def process_support_ticket(message):
    uid = str(message.from_user.id)
    u_text = message.text.strip()
    ticket_id = str(random.randint(10000, 99999))
    bot_config["tickets"][ticket_id] = {"uid": uid, "text": u_text, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ تم فتح تذكرة دعم فني جديدة برقم: <code>#{ticket_id}</code>", parse_mode="HTML")
    try: bot.send_message(ADMIN_PRIMARY, f"💬 تذكرة دعم جديدة برقم #{ticket_id} من {uid}:\n{u_text}")
    except: pass

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

def admin_add_keys_func(message):
    try:
        parts = message.text.strip().split(" ", 2)
        prod = parts[0]
        plan = parts[1] + " " + parts[2].split(" ")[0] if "Day" in parts[1] or "Days" in parts[1] else parts[1]
        key_content = message.text.strip().replace(prod, "").replace(plan, "").strip()
        if prod in keys_store and plan in ["1 Day", "7 Days", "30 Days"]:
            keys_store[prod][plan].append(key_content)
            save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, f"✅ تم إضافة المفتاح بنجاح لقسم {prod} ({plan}).")
        else: bot.send_message(message.chat.id, "❌ خطأ بالاسم أو المدة.")
    except: bot.send_message(message.chat.id, "❌ صيغة الإدخال خاطئة.")

def admin_delete_specific_key(message):
    try:
        parts = message.text.strip().split()
        prod = parts[0]
        plan = parts[1] + " " + parts[2]
        idx = int(parts[3]) - 1
        if prod in keys_store and plan in keys_store[prod] and 0 <= idx < len(keys_store[prod][plan]):
            removed = keys_store[prod][plan].pop(idx)
            save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, f"✅ تم حذف المفتاح بنجاح:\n<code>{removed}</code>", parse_mode="HTML")
        else: bot.send_message(message.chat.id, "❌ تعذر العثور على المفتاح.")
    except: bot.send_message(message.chat.id, "❌ صيغة الأمر خاطئة.")

def admin_edit_price_func(message):
    try:
        parts = message.text.strip().split()
        prod = parts[0]
        plan = parts[1] + " " + parts[2]
        new_price = int(parts[3])
        if prod in prices_config and plan in ["1 Day", "7 Days", "30 Days"]:
            prices_config[prod][plan] = new_price
            save_json(DB_PRICES, prices_config)
            bot.send_message(message.chat.id, f"💵 تم تعديل السعر لـ {prod} ({plan}) إلى {new_price} نقطة.")
        else: bot.send_message(message.chat.id, "❌ المدة أو المنتج غير صحيح.")
    except: bot.send_message(message.chat.id, "❌ خطأ بالبيانات.")

def admin_view_member_func(message):
    t_id = message.text.strip()
    if t_id in users:
        u = users[t_id]
        role = "أدمن مالك" if int(t_id) == ADMIN_PRIMARY else ("أدمن مدير" if u.get("is_admin", False) else "مستخدم")
        ban_status = "محظور نهائي ⛔" if u.get("banned", False) else ("محظور مؤقت 🔴" if u.get("banned_until") else "نشط 🟢")
        msg = f"👥 <b>تفاصيل العضو:</b>\n\n• ID: <code>{t_id}</code>\n• Username: @{u['username']}\n• الرصيد: {u['points']} نقطة\n• الرتبة: {role}\n• حالة الحظر: {ban_status}"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ هذا الآيدي غير مسجل.")

def admin_action_member_func(message):
    try:
        cmd, t_id = message.text.strip().split()
        if t_id not in users: return bot.send_message(message.chat.id, "❌ آيدي العضو غير مسجل.")
        if cmd == "ban":
            users[t_id]["banned"] = True
            bot.send_message(message.chat.id, f"⛔ تم فرض حظر نهائي على الحساب {t_id}.")
        elif cmd == "tempban":
            until_time = datetime.now() + timedelta(days=1)
            users[t_id]["banned_until"] = until_time.isoformat()
            bot.send_message(message.chat.id, f"🔴 تم تطبيق حظر مؤقت 24 ساعة على الحساب {t_id}.")
        elif cmd == "unban":
            users[t_id]["banned"] = False
            users[t_id]["banned_until"] = None
            bot.send_message(message.chat.id, f"🟢 تم إلغاء الحظر عن الحساب {t_id}.")
        elif cmd == "promote":
            users[t_id]["is_admin"] = True
            bot.send_message(message.chat.id, f"⬆️ تم ترقية الحساب {t_id} إلى مدير.")
        elif cmd == "demote":
            users[t_id]["is_admin"] = False
            bot.send_message(message.chat.id, f"⬇️ تم إزالة الإدارة من الحساب {t_id}.")
        save_json(DB_USERS, users)
    except: bot.send_message(message.chat.id, "❌ خطأ في كتابة الأمر.")

def admin_charge_member_func(message):
    try:
        t_id, pts = message.text.strip().split()
        if t_id in users:
            users[t_id]["points"] += int(pts)
            save_json(DB_USERS, users)
            bot.send_message(message.chat.id, f"💰 تم شحن الحساب {t_id} بمقدار +{pts} نقطة.")
            try: bot.send_message(int(t_id), f"🔔 تم إضافة +{pts} رصيد لنقاطك من قبل الإدارة.")
            except: pass
        else: bot.send_message(message.chat.id, "❌ الآيدي غير موجود.")
    except: bot.send_message(message.chat.id, "❌ خطأ بالإدخال.")

def admin_create_code_func(message):
    try:
        code, pts = message.text.strip().split()
        redeem_codes[code] = int(pts)
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 تم إنشاء كود شحن فعال:\n• الكود: <code>{code}</code>\n• قيمته: {pts} نقطة", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ تعذر إنشاء الكود.")

def admin_set_discount_func(message):
    try:
        disc = int(message.text.strip())
        if 0 <= disc < 100:
            bot_config["discount"] = disc
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 تم تفعيل خصم عام بمقدار {disc}%")
        else: bot.send_message(message.chat.id, "❌ أدخل رقم بين 0 و 99.")
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

if __name__ == "__main__":
    print("🚀 تم تشغيل وتفعيل البوت بكافة تحديثات التسويق الوهمي والمفاتيح الوهمية الحصرية...")
    bot.infinity_polling()
