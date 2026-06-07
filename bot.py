import telebot
from telebot import types
import json
import os
import random
import time
from datetime import datetime, timedelta

# ==========================================
# 1️⃣ الإعدادات الأساسية
# ==========================================
TOKEN = "8334852539:AAHPw623oyuwcUQ5d9tkZY-2oJDiq51QiAQ"
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "EVEE7X_FMALIY"
CHANNEL_LINK = "https://t.me/EVEE7X_FMALIY"
SUPPORT_USERNAME = "EVEE7XX_IOS"

OWNER_ID = 8878290572  
DEFAULT_ADMIN = 5145154527

USERS_FILE = "users_data.json"
KEYS_FILE = "keys_store.json"
REDEEM_FILE = "redeem_codes.json"
PRICES_FILE = "prices_config.json"
CONFIG_FILE = "bot_config.json"

# ==========================================
# 2️⃣ قاموس اللغات
# ==========================================
LANGUAGES = {
    "ar": {
        "lang_name": "العربية 🇸🇦",
        "welcome": "⚡️ <b>مرحباً بك في عالم التميز والألعاب الرسمي!</b> 👋\n\n🆔 <b>الآيدي الخاص بك هو:</b> <code>{uid}</code>\n\n🚀 هنا تجد أقوى المفافتح والهاكات الحصرية بأسرع تسليم تلقائي في التلغرام.",
        "sub_required": "⚠️ <b>تنبيه أمني صارم!</b>\n\nعذراً عزيزي، الوصول للبوت متاح فقط لمشتركي القناة الرسمية لدعم استمرار التحديثات.\n\n📢 اشترك في القناة ثم اضغط على زر التحقق بالأسفل لتفعيل حسابك:",
        "btn_join": "📢 إشترك في القناة الرسمية",
        "btn_check": "✅ تفعيل الحساب والتحقق",
        "not_subbed": "❌ لم نشهد انضمامك بعد! يرجى الاشتراك أولاً لتتمكن من العبور.",
        "sub_success": "🎉 أهلاً بك! تم التحقق من اشتراكك بنجاح، تم فتح كامل الصلاحيات لك الآن.",
        "get_id": "🆔 إظهار الآيدي",
        "buy": "🛍️ شراء المنتجات 🛒",
        "redeem": "🎁 شحن كود 🎫",
        "invite": "🔗 دعوة الأصدقاء 👥",
        "daily": "✨ مكافأتي اليومية 🎁",
        "support": "💡 مركز الدعم 🛠️",
        "change_lang": "🌐 تغيير اللغة 🔄",
        "admin_mode": "⚙️ لوحة الإدارة العليا",
        "user_mode": "🔄 العودة كعضو عادي",
        "invite_text": "🤝 <b>برنامج الإحالة الماسي!</b>\n\n🔗 <code>{ref_link}</code>\n\n🎁 بمجرد دخول شخص من رابطك ستحصل على <b>{reward} نقطة</b>!",
        "ref_notify": "🔔 <b>بشرى سارة!</b> انضم عضو جديد برابطك، تمت إضافة <code>+{reward} نقطة</code>!",
        "choose_hack": "🎯 <b>قائمة المنتجات:</b>\n\nاختر المنتج الذي ترغب بشراء مفتاحه:",
        "choose_duration": "⏱️ <b>اختر مدة اشتراك ({hack}):</b>",
        "empty_key": "❌ نأسف جداً! هذا المنتج نفذت كميته من المخزن حالياً.",
        "buy_success": "🎉 <b>تمت عملية الشراء بنجاح!</b>\n\n🔑 مفتاحك الرقمي:\n<code>{key}</code>",
        "no_balance": "❌ <b>فشل!</b> رصيدك غير كافٍ. السعر هو <code>{price} نقطة</code>.",
        "enter_redeem": "📥 <b>بوابة شحن الأكواد:</b>\nأرسل كود الشحن هنا:",
        "redeem_success": "✅ <b>تم الشحن!</b> أُضيفت <code>+{amount} نقطة</code> إلى محفظتك.",
        "redeem_fail": "❌ الكود غير صحيح أو مستخدم مسبقاً.",
        "support_text": "🛠️ <b>مركز الدعم:</b>\nللمساعدة تواصل معنا بالضغط أدناه:",
        "choose_language": "🌐 <b>إعدادات اللغة:</b>\nيرجى اختيار لغة الواجهة:",
        "language_saved": "✅ تم حفظ لغتك بنجاح.",
        "shop_empty": "📦 المتجر فارغ تماماً حالياً.",
        "contact_support": "💬 مراسلة الدعم المباشر",
        "daily_success": "🎁 <b>مبروك!</b> استلمت مكافأتك وحصلت على <code>+{amount} نقطة</code>!",
        "daily_wait": "⏳ <b>عذراً!</b> استلمت مكافأتك اليومية بالفعل. انتظر: <code>{time_left}</code>."
    },
    "en": {
        "lang_name": "English 🇺🇸",
        "get_id": "🆔 Get My ID",
        "welcome": "⚡️ <b>Welcome to the Premium Hacks Store!</b> 👋\n\n🆔 <b>Your ID:</b> <code>{uid}</code>\n\n🚀 Exclusive keys with instant delivery.",
        "sub_required": "⚠️ Please join the channel first.",
        "btn_join": "📢 Join Official Channel",
        "btn_check": "✅ Verify Account",
        "not_subbed": "❌ Please join first.",
        "sub_success": "🎉 Verified successfully.",
        "buy": "🛍️ Premium Shop 🛒",
        "redeem": "🎁 Redeem Code 🎫",
        "invite": "🔗 Earn Points 👥",
        "daily": "✨ Daily Reward 🎁",
        "support": "💡 Technical Support 🛠️",
        "change_lang": "🌐 Change Language 🔄",
        "admin_mode": "⚙️ Admin Control Panel",
        "user_mode": "🔄 Return to User Mode",
        "invite_text": "🤝 <b>Referral Program!</b>\n\n🔗 <code>{ref_link}</code>\n\n🎁 Get <b>{reward} points</b>!",
        "ref_notify": "🔔 <code>+{reward} points</code> added from invite!",
        "choose_hack": "🎯 Select a product:",
        "choose_duration": "⏱️ <b>Choose duration for ({hack}):</b>",
        "empty_key": "❌ Out of stock!",
        "buy_success": "🎉 <b>Purchase Completed!</b>\n\n🔑 Your key:\n<code>{key}</code>",
        "no_balance": "❌ Insufficient balance. Price is <code>{price} points</code>.",
        "enter_redeem": "📥 Send your redeem code here:",
        "redeem_success": "✅ <code>+{amount} points</code> added.",
        "redeem_fail": "❌ Invalid code.",
        "support_text": "🛠️ Contact us below:",
        "choose_language": "🌐 Choose language:",
        "language_saved": "✅ Language saved.",
        "shop_empty": "📦 Store is empty.",
        "contact_support": "💬 Contact Live Support",
        "daily_success": "🎁 You claimed <code>+{amount} points</code>!",
        "daily_wait": "⏳ Already claimed. Wait: <code>{time_left}</code>."
    },
    "fr": {
        "lang_name": "Français 🇫🇷",
        "get_id": "🆔 Mon ID",
        "welcome": "⚡️ <b>Bienvenue!</b> 👋\n\n🆔 <b>Votre ID:</b> <code>{uid}</code>",
        "sub_required": "⚠️ Rejoignez la chaîne.",
        "btn_join": "📢 Rejoindre la chaîne",
        "btn_check": "✅ Vérifier",
        "not_subbed": "❌ Rejoignez d'abord.",
        "sub_success": "🎉 Vérifié.",
        "buy": "🛍️ Boutique Privée 🛒",
        "redeem": "🎁 Utiliser un Code 🎫",
        "invite": "🔗 Gagner des Points 👥",
        "daily": "✨ Bonus Quotidien 🎁",
        "support": "💡 Support Technique 🛠️",
        "change_lang": "🌐 Changer de Langue 🔄",
        "admin_mode": "⚙️ Panneau d'Administration",
        "user_mode": "🔄 Mode Utilisateur",
        "invite_text": "🤝 <b>Parrainage!</b>\n🔗 <code>{ref_link}</code>\n🎁 <b>{reward} points</b> par ami!",
        "ref_notify": "🔔 <code>+{reward} points</code> de parrainage!",
        "choose_hack": "🎯 Choisissez un produit:",
        "choose_duration": "⏱️ <b>Durée ({hack}):</b>",
        "empty_key": "❌ Rupture de stock!",
        "buy_success": "🎉 <b>Achat Réussi!</b>\n\n🔑 Clé:\n<code>{key}</code>",
        "no_balance": "❌ Solde insuffisant (<code>{price} points</code>).",
        "enter_redeem": "📥 Envoyez le code:",
        "redeem_success": "✅ <code>+{amount} points</code> ajoutés.",
        "redeem_fail": "❌ Code invalide.",
        "support_text": "🛠️ Contactez-nous:",
        "choose_language": "🌐 Choisir la langue:",
        "language_saved": "✅ Langue configurée.",
        "shop_empty": "📦 Boutique vide.",
        "contact_support": "💬 Contacter le Support",
        "daily_success": "🎁 Bonus: <code>+{amount} points</code>!",
        "daily_wait": "⏳ Déjà récupéré. Attendez: <code>{time_left}</code>."
    },
    "vi": {
        "lang_name": "Tiếng Việt 🇻🇳",
        "get_id": "🆔 Lấy ID",
        "welcome": "⚡️ <b>Chào Mừng!</b> 👋\n\n🆔 <b>ID:</b> <code>{uid}</code>",
        "sub_required": "⚠️ Tham gia kênh trước.",
        "btn_join": "📢 Tham Gia Kênh",
        "btn_check": "✅ Xác Minh",
        "not_subbed": "❌ Vui lòng tham gia kênh.",
        "sub_success": "🎉 Thành công.",
        "buy": "🛍️ Cửa Hàng 🛒",
        "redeem": "🎁 Nhập Mã 🎫",
        "invite": "🔗 Kiếm Điểm 👥",
        "daily": "✨ Điểm Danh 🎁",
        "support": "💡 Hỗ Trợ 🛠️",
        "change_lang": "🌐 Đổi Ngôn Ngữ 🔄",
        "admin_mode": "⚙️ Admin",
        "user_mode": "🔄 Người Dùng",
        "invite_text": "🤝 <b>Giới Thiệu!</b>\n🔗 <code>{ref_link}</code>\n🎁 <b>{reward} điểm</b>!",
        "ref_notify": "🔔 <code>+{reward} điểm</code> từ lượt mời!",
        "choose_hack": "🎯 Chọn sản phẩm:",
        "choose_duration": "⏱️ <b>Gói ({hack}):</b>",
        "empty_key": "❌ Hết hàng!",
        "buy_success": "🎉 <b>Thành Công!</b>\n\n🔑 Key:\n<code>{key}</code>",
        "no_balance": "❌ Không đủ điểm (<code>{price}</code>).",
        "enter_redeem": "📥 Gửi mã:",
        "redeem_success": "✅ Đã cộng <code>+{amount} điểm</code>.",
        "redeem_fail": "❌ Mã sai.",
        "support_text": "🛠️ Trò chuyện hỗ trợ:",
        "choose_language": "🌐 Chọn ngôn ngữ:",
        "language_saved": "✅ Đã lưu.",
        "shop_empty": "📦 Trống.",
        "contact_support": "💬 Liên Hệ Hỗ Trợ",
        "daily_success": "🎁 <code>+{amount} điểm</code>!",
        "daily_wait": "⏳ Chờ: <code>{time_left}</code>."
    }
}

# ==========================================
# 3️⃣ إدارة البيانات
# ==========================================
def load_data(filename, default_value):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    return default_value

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

users_data = load_data(USERS_FILE, {})
bot_config = load_data(CONFIG_FILE, {"referral_reward": 1.0, "daily_min": 1, "daily_max": 10, "maintenance": False, "discount": 0})
keys_store = load_data(KEYS_FILE, {})
PRICES = load_data(PRICES_FILE, {})
redeem_codes = load_data(REDEEM_FILE, {})

def get_text(uid, key, **kwargs):
    lang = users_data.get(str(uid), {}).get("lang", "ar")
    if lang not in LANGUAGES: lang = "ar"
    return LANGUAGES[lang].get(key, LANGUAGES["ar"].get(key, "Error")).format(**kwargs)

def is_admin(uid):
    if uid == OWNER_ID or uid == DEFAULT_ADMIN: return True
    return users_data.get(str(uid), {}).get("is_admin", False)

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return True

def check_user(user):
    uid_str = str(user.id)
    if uid_str not in users_data:
        users_data[uid_str] = {
            "balance": 0.0, "username": user.username or f"User_{user.id}", 
            "referred_by": None, "invited_count": 0, "lang": "ar", 
            "admin_mode": False, "last_daily": None, "is_admin": False,
            "banned": False, "ban_reason": ""
        }
        if int(uid_str) == OWNER_ID or int(uid_str) == DEFAULT_ADMIN:
            users_data[uid_str]["is_admin"] = True
        save_data(USERS_FILE, users_data)

# ==========================================
# 4️⃣ بناء لوحات التفاعل
# ==========================================
def user_keyboard(uid):
    lang = users_data.get(str(uid), {}).get("lang", "ar")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(LANGUAGES[lang]["get_id"]))
    markup.add(types.KeyboardButton(LANGUAGES[lang]["buy"]), types.KeyboardButton(LANGUAGES[lang]["redeem"]))
    markup.add(types.KeyboardButton(LANGUAGES[lang]["invite"]), types.KeyboardButton(LANGUAGES[lang]["daily"]))
    markup.add(types.KeyboardButton(LANGUAGES[lang]["support"]), types.KeyboardButton(LANGUAGES[lang]["change_lang"]))
    if is_admin(uid): markup.add(types.KeyboardButton(LANGUAGES[lang]["admin_mode"]))
    return markup

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("➕ أضف منتج"), types.KeyboardButton("❌ احذف منتج"))
    markup.add(types.KeyboardButton("🔑 إضافة أكواد"), types.KeyboardButton("📋 استعراض وتعديل الأكواد"))
    markup.add(types.KeyboardButton("🏷️ الأسعار"), types.KeyboardButton("👥 إدارة الأعضاء"))
    markup.add(types.KeyboardButton("🔥 تخفيضات (Sale)"), types.KeyboardButton("📢 إذاعة شاملة"))
    markup.add(types.KeyboardButton("📤 نشر الأسعار بالقناة"), types.KeyboardButton("📣 تسويق وهمي"))
    markup.add(types.KeyboardButton("🎫 توليد كود شحن"), types.KeyboardButton("💰 شحن عضو"))
    markup.add(types.KeyboardButton("🛠️ وضع الصيانة"), types.KeyboardButton("☁️ نسخ احتياطي"))
    markup.add(types.KeyboardButton("🔄 وضع المستخدم"))
    return markup

def sub_keyboard(uid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text(uid, "btn_join"), url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton(get_text(uid, "btn_check"), callback_data="verify_sub"))
    return markup

def lang_setup_keyboard():
    markup = types.InlineKeyboardMarkup()
    for code, info in LANGUAGES.items(): 
        markup.add(types.InlineKeyboardButton(info["lang_name"], callback_data=f"firstlang_{code}"))
    return markup

def manage_user_keyboard(target_id):
    markup = types.InlineKeyboardMarkup()
    t_str = str(target_id)
    is_banned = users_data.get(t_str, {}).get("banned", False)
    is_target_admin = users_data.get(t_str, {}).get("is_admin", False)
    
    if is_banned: markup.add(types.InlineKeyboardButton("🟢 رفع الحظر", callback_data=f"usr_unban_{target_id}"))
    else: markup.add(types.InlineKeyboardButton("🔴 حظر مؤقت (24h)", callback_data=f"usr_tmpban_{target_id}"), types.InlineKeyboardButton("⛔ حظر نهائي", callback_data=f"usr_ban_{target_id}"))
    
    if is_target_admin: markup.add(types.InlineKeyboardButton("⬇️ تنزيل من الإدارة", callback_data=f"usr_demote_{target_id}"))
    else: markup.add(types.InlineKeyboardButton("⬆️ ترقية لمدير", callback_data=f"usr_promote_{target_id}"))
    return markup

# ==========================================
# 5️⃣ الأوامر المباشرة
# ==========================================
@bot.message_handler(commands=['id'])
def send_id_directly(message):
    bot.reply_to(message, f"🆔 الآيدي الخاص بك هو: <code>{message.from_user.id}</code>", parse_mode="HTML")

@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    uid_str = str(uid)
    check_user(message.from_user)
    
    if users_data[uid_str].get("banned", False):
        bot.send_message(message.chat.id, "🚫 <b>حسابك محظور من استخدام البوت!</b>", parse_mode="HTML")
        return

    if bot_config.get("maintenance", False) and not is_admin(uid):
        bot.send_message(message.chat.id, "🛠️ <b>البوت تحت الصيانة الشاملة حالياً!</b>", parse_mode="HTML")
        return
        
    parts = message.text.split()
    if users_data[uid_str]["referred_by"] is None and len(parts) > 1:
        referrer_id = parts[1]
        if referrer_id in users_data and referrer_id != uid_str:
            users_data[uid_str]["referred_by"] = referrer_id
            users_data[referrer_id]["invited_count"] = users_data[referrer_id].get("invited_count", 0) + 1
            save_data(USERS_FILE, users_data)
            
    bot.send_message(message.chat.id, "🌐 Please select your language / يرجى اختيار لغتك:", reply_markup=lang_setup_keyboard())

# ==========================================
# 6️⃣ معالج الرسائل
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    uid = message.from_user.id
    uid_str = str(uid)
    check_user(message.from_user)
    
    if users_data[uid_str].get("banned", False):
        return bot.send_message(message.chat.id, "🚫 <b>حسابك محظور!</b>", parse_mode="HTML")

    if bot_config.get("maintenance", False) and not is_admin(uid):
        return bot.send_message(message.chat.id, "🛠️ <b>البوت تحت الصيانة!</b>", parse_mode="HTML")

    if not is_subscribed(uid):
        return bot.send_message(message.chat.id, get_text(uid, "sub_required"), reply_markup=sub_keyboard(uid), parse_mode="HTML")

    text = message.text

    # --- إدارة لوحة الأدمن (تم استخدام التطابق الدقيق == لمنع التداخل) ---
    if is_admin(uid):
        if any(keyword in text for keyword in ["الإدارة", "Admin Control", "admin_mode", "وضع الأدمن"]):
            users_data[uid_str]["admin_mode"] = True
            save_data(USERS_FILE, users_data)
            return bot.send_message(message.chat.id, "⚙️ <b>أهلاً بك في لوحة التحكم!</b>", reply_markup=admin_keyboard(), parse_mode="HTML")
            
        if users_data[uid_str].get("admin_mode", False):
            if text == "➕ أضف منتج":
                msg = bot.send_message(message.chat.id, "📥 اكتب اسم المنتج الجديد:")
                bot.register_next_step_handler(msg, process_add_product)
                return
            elif text == "❌ احذف منتج":
                if not PRICES: return bot.send_message(message.chat.id, "📦 لا توجد منتجات لحذفها.")
                markup = types.InlineKeyboardMarkup()
                for hack in PRICES.keys(): markup.add(types.InlineKeyboardButton(f"🗑️ حذف {hack}", callback_data=f"delhack_{hack}"))
                return bot.send_message(message.chat.id, "❌ إختر المنتج المراد حذفه:", reply_markup=markup)
            elif text == "🔑 إضافة أكواد":
                if not PRICES: return bot.send_message(message.chat.id, "📦 لا توجد منتجات.")
                markup = types.InlineKeyboardMarkup()
                for hack in PRICES.keys(): markup.add(types.InlineKeyboardButton(f"🎮 {hack}", callback_data=f"adminhack_{hack}"))
                return bot.send_message(message.chat.id, "⚙️ إختر المنتج لإضافة أكواده:", reply_markup=markup)
            elif text == "📋 استعراض وتعديل الأكواد":
                if not PRICES: return bot.send_message(message.chat.id, "📦 لا توجد منتجات.")
                markup = types.InlineKeyboardMarkup()
                for hack in PRICES.keys(): markup.add(types.InlineKeyboardButton(f"🔍 {hack}", callback_data=f"viewhack_{hack[:20]}"))
                return bot.send_message(message.chat.id, "⚙️ إختر المنتج لاستعراض وتعديل أكواده:", reply_markup=markup)
            elif text == "🏷️ الأسعار":
                if not PRICES: return bot.send_message(message.chat.id, "📦 لا توجد منتجات لتعديل أسعارها.")
                markup = types.InlineKeyboardMarkup()
                for hack in PRICES.keys(): markup.add(types.InlineKeyboardButton(f"⚙️ أسعار {hack}", callback_data=f"prichack_{hack}"))
                return bot.send_message(message.chat.id, "💵 إختر المنتج لتعديل أسعاره:", reply_markup=markup)
            
            # --- الإعلان الجذاب الجديد ---
            elif text == "📤 نشر الأسعار بالقناة":
                if not PRICES: return bot.send_message(message.chat.id, "📦 لا توجد منتجات لنشرها.")
                try:
                    bot_username = bot.get_me().username
                    msg_text = "🌟 <b>أقوى العروض والمنتجات الحصرية توفرت الآن!</b> 🌟\n"
                    msg_text += "🔥 <b>نقدم لكم أفضل المفاتيح بأرخص الأسعار مع تسليم فوري وتلقائي 100%!</b> 🔥\n\n"
                    msg_text += "🛒 <b>قائمة المنتجات المتوفرة:</b>\n\n"
                    
                    for h, durs in PRICES.items():
                        msg_text += f"💎 <b>{h}</b>:\n"
                        for dur, price in durs.items():
                            msg_text += f" ├ ⏱️ {dur} ━ 💰 <code>{price}</code> نقطة\n"
                        msg_text += "\n"
                    
                    msg_text += "🎁 <b>تسليم آلي ومضمون مباشرة بعد الدفع!</b> ⚡️\n"
                    msg_text += "🛡️ <b>ضمان الأمان والموثوقية العالية.</b>\n\n"
                    msg_text += f"👇 <b>سارع بالشراء الآن عبر البوت الرسمي:</b>\n👉 https://t.me/{bot_username}"
                    
                    bot.send_message(f"@{CHANNEL_USERNAME}", msg_text, parse_mode="HTML")
                    return bot.send_message(message.chat.id, "✅ تم نشر الإعلان الجذاب والأسعار في القناة بنجاح!")
                except Exception as e:
                    return bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء النشر: يُرجى التأكد من أن البوت مشرف في القناة.")
            
            elif text == "👥 إدارة الأعضاء":
                msg = bot.send_message(message.chat.id, "🕵️ أرسل الآيدي (ID) الخاص بالعضو للتحكم به:")
                bot.register_next_step_handler(msg, process_manage_user)
                return
            elif text == "☁️ نسخ احتياطي":
                bot.send_message(message.chat.id, "☁️ جارٍ سحب نسخة احتياطية من قواعد البيانات...")
                for f in [USERS_FILE, KEYS_FILE, PRICES_FILE, REDEEM_FILE, CONFIG_FILE]:
                    if os.path.exists(f): bot.send_document(message.chat.id, open(f, "rb"))
                return
            elif text == "🛠️ وضع الصيانة":
                bot_config["maintenance"] = not bot_config.get("maintenance", False)
                save_data(CONFIG_FILE, bot_config)
                state = "🟢 مفعل" if bot_config["maintenance"] else "🔴 معطل"
                return bot.send_message(message.chat.id, f"🛠️ حالة وضع الصيانة الآن: {state}")
            elif text == "🔥 تخفيضات (Sale)":
                msg = bot.send_message(message.chat.id, "🔥 أرسل نسبة الخصم بالأرقام (مثلاً: 20 لخصم 20%) أو 0 للإلغاء:")
                bot.register_next_step_handler(msg, process_discount)
                return
            elif text == "📣 تسويق وهمي":
                if not PRICES: return bot.send_message(message.chat.id, "لا توجد منتجات.")
                random_hack = random.choice(list(PRICES.keys()))
                fake_msg = f"🎉 <b>مشتريات جديدة!</b>\n\nمستخدم جديد قام بشراء مفتاح لـ <code>{random_hack}</code> للتو! 🔥\nاشترِ الآن من البوت الحصري."
                try: bot.send_message(f"@{CHANNEL_USERNAME}", fake_msg, parse_mode="HTML")
                except: pass
                return bot.send_message(message.chat.id, "✅ تم نشر الإشعار الوهمي بنجاح!")
            elif text == "📢 إذاعة شاملة":
                msg = bot.send_message(message.chat.id, "📥 اكتب رسالة الإذاعة العامة:")
                bot.register_next_step_handler(msg, process_broadcast)
                return
            elif text == "🔄 وضع المستخدم":
                users_data[uid_str]["admin_mode"] = False
                save_data(USERS_FILE, users_data)
                return bot.send_message(message.chat.id, "🔄 تم التحويل لوضع العضو.", reply_markup=user_keyboard(uid))
            elif text == "💰 شحن عضو":
                msg = bot.send_message(message.chat.id, "ارسل الآيدي ثم الرصيد بمسافة:")
                bot.register_next_step_handler(msg, save_balance)
                return
            elif text == "🎫 توليد كود شحن":
                msg = bot.send_message(message.chat.id, "ارسل الكود ثم قيمته بمسافة:")
                bot.register_next_step_handler(msg, save_redeem)
                return

    # --- فحص واجهة المستخدم العادي ---
    if "آيدي" in text or "ID" in text or "Id" in text or "ID" in text:
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك هو: <code>{uid}</code>", parse_mode="HTML")
        
    elif "دعوة" in text or "كسب" in text or "Invite" in text or "Gagner" in text or "Kiếm Điểm" in text:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        bot.send_message(message.chat.id, get_text(uid, "invite_text", ref_link=ref_link, reward=bot_config.get("referral_reward", 1.0)), parse_mode="HTML")
        
    elif "مكافأتي" in text or "Daily" in text or "Bonus" in text or "Điểm Danh" in text:
        process_daily_claim(message)
        
    elif "شراء" in text or "متجر" in text or "Shop" in text or "Boutique" in text or "Cửa Hàng" in text:
        if not PRICES: return bot.send_message(message.chat.id, get_text(uid, "shop_empty"), parse_mode="HTML")
        markup = types.InlineKeyboardMarkup()
        discount = bot_config.get("discount", 0)
        sale_text = f" 🔥 خصم {discount}% متاح الآن!" if discount > 0 else ""
        for hack in PRICES.keys(): markup.add(types.InlineKeyboardButton(f"🔥 {hack}", callback_data=f"bh_{hack[:20]}"))
        bot.send_message(message.chat.id, get_text(uid, "choose_hack") + sale_text, reply_markup=markup, parse_mode="HTML")
        
    elif "شحن كود" in text or "Redeem" in text or "Utiliser" in text or "Nhập Mã" in text:
        msg = bot.send_message(message.chat.id, get_text(uid, "enter_redeem"), parse_mode="HTML")
        bot.register_next_step_handler(msg, process_redeem)
        
    elif "الدعم" in text or "Support" in text or "Aide" in text or "Hỗ Trợ" in text:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(get_text(uid, "contact_support"), url=f"https://t.me/{SUPPORT_USERNAME}"))
        bot.send_message(message.chat.id, get_text(uid, "support_text"), reply_markup=markup, parse_mode="HTML")
        
    elif "اللغة" in text or "Language" in text or "Langue" in text or "Ngôn Ngữ" in text:
        markup = types.InlineKeyboardMarkup()
        for code, info in LANGUAGES.items(): markup.add(types.InlineKeyboardButton(info["lang_name"], callback_data=f"setlang_{code}"))
        bot.send_message(message.chat.id, get_text(uid, "choose_language"), reply_markup=markup, parse_mode="HTML")

# ==========================================
# 7️⃣ معالجة الكولباك
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    uid = call.from_user.id
    uid_str = str(uid)
    
    bot.answer_callback_query(call.id)
    if users_data.get(uid_str, {}).get("banned", False): return

    if call.data.startswith("firstlang_") or call.data.startswith("setlang_"):
        lang = call.data.split("_")[1]
        users_data[uid_str]["lang"] = lang
        save_data(USERS_FILE, users_data)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        if not is_subscribed(uid): 
            bot.send_message(call.message.chat.id, get_text(uid, "sub_required"), reply_markup=sub_keyboard(uid), parse_mode="HTML")
        else: 
            bot.send_message(call.message.chat.id, get_text(uid, "welcome", uid=uid), reply_markup=user_keyboard(uid), parse_mode="HTML")
        return
        
    if call.data == "verify_sub":
        if is_subscribed(uid):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, get_text(uid, "sub_success"), parse_mode="HTML")
            bot.send_message(call.message.chat.id, get_text(uid, "welcome", uid=uid), reply_markup=user_keyboard(uid), parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, get_text(uid, "not_subbed"), parse_mode="HTML")
        return

    # --- إجراءات المشرف ---
    if call.data.startswith("usr_") and is_admin(uid):
        parts = call.data.split("_")
        action, target = parts[1], parts[2]
        if int(target) == OWNER_ID: return
        
        if action in ["ban", "tmpban"]: users_data[target]["banned"] = True
        elif action == "unban": users_data[target]["banned"] = False
        elif action == "promote": users_data[target]["is_admin"] = True
        elif action == "demote": users_data[target]["is_admin"] = False
        
        save_data(USERS_FILE, users_data)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, f"✅ تم تنفيذ الإجراء بنجاح على <code>{target}</code>.", parse_mode="HTML")
        return

    if is_admin(uid):
        if call.data.startswith("delhack_"):
            hack = call.data.replace("delhack_", "")
            if hack in PRICES: del PRICES[hack]
            if hack in keys_store: del keys_store[hack]
            save_data(PRICES_FILE, PRICES)
            save_data(KEYS_FILE, keys_store)
            bot.edit_message_text(f"✅ تم حذف المنتج ({hack}) نهائياً.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return
            
        elif call.data.startswith("adminhack_"):
            hack = call.data.replace("adminhack_", "")
            markup = types.InlineKeyboardMarkup()
            for duration in PRICES.get(hack, {}).keys():
                markup.add(types.InlineKeyboardButton(f"📥 تعبئة {duration}", callback_data=f"addkeys_{hack[:20]}_{duration[:10]}"))
            bot.edit_message_text(f"🎮 منتج: {hack}\nاختر الفئة الزمنية لإضافة الأكواد:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return
            
        elif call.data.startswith("addkeys_"):
            parts = call.data.split("_")
            actual_hack = next((h for h in PRICES.keys() if h.startswith(parts[1])), None)
            actual_dur = next((d for d in PRICES[actual_hack].keys() if d.startswith(parts[2])), None) if actual_hack else None
            if actual_hack and actual_dur:
                msg = bot.send_message(call.message.chat.id, f"📥 أرسل الأكواد الآن لـ ({actual_hack} - {actual_dur}) كل كود في سطر:")
                bot.register_next_step_handler(msg, save_dynamic_keys, actual_hack, actual_dur)
            return

        # 🔍 استعراض الأكواد الجديدة
        elif call.data.startswith("viewhack_"):
            hack_prefix = call.data.replace("viewhack_", "")
            actual_hack = next((h for h in PRICES.keys() if h.startswith(hack_prefix)), None)
            if not actual_hack: return
            markup = types.InlineKeyboardMarkup()
            for duration in PRICES.get(actual_hack, {}).keys():
                markup.add(types.InlineKeyboardButton(f"📂 {duration}", callback_data=f"viewdur_{actual_hack[:20]}_{duration[:10]}"))
            bot.edit_message_text(f"🎮 منتج: {actual_hack}\nاختر الفئة الزمنية لاستعراض أكوادها:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return

        elif call.data.startswith("viewdur_"):
            parts = call.data.split("_")
            actual_hack = next((h for h in PRICES.keys() if h.startswith(parts[1])), None)
            actual_dur = next((d for d in PRICES[actual_hack].keys() if d.startswith(parts[2])), None) if actual_hack else None
            if actual_hack and actual_dur:
                keys = keys_store.get(actual_hack, {}).get(actual_dur, [])
                if not keys:
                    return bot.edit_message_text(f"❌ لا توجد أي أكواد في ({actual_hack} - {actual_dur}).", call.message.chat.id, call.message.message_id)
                
                msg_text = f"🔑 <b>الأكواد المتوفرة لـ ({actual_hack} - {actual_dur}):</b>\n\n"
                for i, k in enumerate(keys):
                    msg_text += f"<b>{i+1}.</b> <code>{k}</code>\n"
                
                msg_text += "\n🗑️ <i>لحذف كود معين، أرسل رقمه (مثال: 1).\nمسح الكل: أرسل 'مسح الكل'.\nللتراجع: أرسل 'إلغاء'.</i>"
                msg = bot.send_message(call.message.chat.id, msg_text, parse_mode="HTML")
                bot.register_next_step_handler(msg, process_delete_key, actual_hack, actual_dur)
            return
            
        elif call.data.startswith("prichack_"):
            hack = call.data.replace("prichack_", "")
            markup = types.InlineKeyboardMarkup()
            for duration in PRICES.get(hack, {}).keys():
                markup.add(types.InlineKeyboardButton(f"⚙️ تعديل سعر {duration}", callback_data=f"setprice_{hack[:20]}_{duration[:10]}"))
            bot.edit_message_text(f"💵 تعديل أسعار: {hack}", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return
            
        elif call.data.startswith("setprice_"):
            parts = call.data.split("_")
            actual_hack = next((h for h in PRICES.keys() if h.startswith(parts[1])), None)
            actual_dur = next((d for d in PRICES[actual_hack].keys() if d.startswith(parts[2])), None) if actual_hack else None
            if actual_hack and actual_dur:
                msg = bot.send_message(call.message.chat.id, f"💵 أرسل السعر الجديد لـ ({actual_dur}) للمنتج ({actual_hack}):")
                bot.register_next_step_handler(msg, save_dynamic_price, actual_hack, actual_dur)
            return

    # --- الشراء ---
    if call.data.startswith("bh_"):
        h_part = call.data.replace("bh_", "")
        hack = next((h for h in PRICES.keys() if h.startswith(h_part)), None)
        if not hack: return
        discount = bot_config.get("discount", 0)
        markup = types.InlineKeyboardMarkup()
        for duration, base_price in PRICES[hack].items():
            final_price = base_price * (1 - (discount / 100))
            btn_text = f"⏱️ {duration} ({final_price} ن)"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"bf_{hack[:20]}_{duration[:10]}"))
        bot.edit_message_text(get_text(uid, "choose_duration", hack=hack), call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data.startswith("bf_"):
        parts = call.data.split("_")
        hack = next((h for h in PRICES.keys() if h.startswith(parts[1])), None)
        duration = next((d for d in PRICES[hack].keys() if d.startswith(parts[2])), None) if hack else None
        if not hack or not duration: return
        
        base_price = PRICES[hack].get(duration, 0)
        discount = bot_config.get("discount", 0)
        final_price = base_price * (1 - (discount / 100))
        
        if not keys_store.get(hack, {}).get(duration):
            bot.send_message(call.message.chat.id, get_text(uid, "empty_key"), parse_mode="HTML")
        else:
            if users_data[uid_str]["balance"] >= final_price:
                users_data[uid_str]["balance"] -= final_price
                key = keys_store[hack][duration].pop(0)
                save_data(USERS_FILE, users_data)
                save_data(KEYS_FILE, keys_store)
                bot.send_message(call.message.chat.id, get_text(uid, "buy_success", key=key), parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, get_text(uid, "no_balance", price=final_price), parse_mode="HTML")

# ==========================================
# 8️⃣ دوال المعالجة الإضافية
# ==========================================
def process_delete_key(message, hack, dur):
    text = message.text.strip()
    if text == "إلغاء":
        return bot.send_message(message.chat.id, "✅ تم إلغاء العملية.")
        
    keys = keys_store.get(hack, {}).get(dur, [])
    if text == "مسح الكل":
        keys_store[hack][dur] = []
        save_data(KEYS_FILE, keys_store)
        return bot.send_message(message.chat.id, "🗑️ تم مسح جميع الأكواد بنجاح.")
        
    try:
        idx = int(text) - 1
        if 0 <= idx < len(keys):
            deleted_key = keys.pop(idx)
            save_data(KEYS_FILE, keys_store)
            bot.send_message(message.chat.id, f"✅ تم حذف الكود: <code>{deleted_key}</code> بنجاح.", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ رقم غير صحيح. العملية ألغيت.")
    except:
        bot.send_message(message.chat.id, "❌ إدخال غير صالح. العملية ألغيت.")

def process_manage_user(message):
    target = message.text.strip()
    if target not in users_data: return bot.send_message(message.chat.id, "❌ الآيدي غير موجود.")
    u_data = users_data[target]
    status = "🔴 محظور" if u_data.get("banned") else "🟢 نشط"
    role = "👑 مدير" if u_data.get("is_admin") else "👤 عضو"
    msg = f"🕵️ <b>بيانات العضو:</b>\n\n🆔 الآيدي: <code>{target}</code>\n👤 اليوزر: @{u_data.get('username', 'بدون')}\n💰 الرصيد: <code>{u_data['balance']}</code>\n📌 الرتبة: {role}\n🔒 الحالة: {status}"
    bot.send_message(message.chat.id, msg, reply_markup=manage_user_keyboard(target), parse_mode="HTML")

def process_discount(message):
    try:
        val = int(message.text.strip())
        bot_config["discount"] = val
        save_data(CONFIG_FILE, bot_config)
        bot.send_message(message.chat.id, f"🔥 تم ضبط التخفيض بنسبة: <code>{val}%</code>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ أرسل رقماً صحيحاً.")

def process_daily_claim(message):
    uid_str = str(message.from_user.id)
    now = datetime.now()
    last_claim_str = users_data[uid_str].get("last_daily")
    if last_claim_str:
        last_claim = datetime.fromisoformat(last_claim_str)
        if now < last_claim + timedelta(days=1):
            time_left = (last_claim + timedelta(days=1)) - now
            h, rem = divmod(time_left.seconds, 3600)
            m, s = divmod(rem, 60)
            return bot.send_message(message.chat.id, get_text(uid_str, "daily_wait", time_left=f"{h:02d}:{m:02d}:{s:02d}"), parse_mode="HTML")
            
    amt = random.randint(bot_config.get("daily_min", 1), bot_config.get("daily_max", 10))
    users_data[uid_str]["balance"] += float(amt)
    users_data[uid_str]["last_daily"] = now.isoformat()
    save_data(USERS_FILE, users_data)
    bot.send_message(message.chat.id, get_text(uid_str, "daily_success", amount=amt), parse_mode="HTML")

def process_broadcast(message):
    bot.send_message(message.chat.id, "📢 جارٍ الإرسال...")
    success = 0
    for user_id in users_data.keys():
        try: 
            bot.send_message(int(user_id), message.text)
            success += 1
            time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"✅ تم إرسال الإذاعة لـ {success} عضو.", parse_mode="HTML")

def process_add_product(message):
    h = message.text.strip()
    if h and h not in PRICES:
        PRICES[h] = {"1 Day": 25.0, "7 Days": 50.0, "30 Days": 100.0}
        keys_store[h] = {"1 Day": [], "7 Days": [], "30 Days": []}
        save_data(PRICES_FILE, PRICES)
        save_data(KEYS_FILE, keys_store)
        bot.send_message(message.chat.id, f"🎉 تمت إضافة المنتج ({h}) بنجاح.")

def save_dynamic_keys(message, hack, dur):
    keys = message.text.split('\n')
    added = 0
    if hack not in keys_store: keys_store[hack] = {}
    if dur not in keys_store[hack]: keys_store[hack][dur] = []
    for k in keys:
        if k.strip(): 
            keys_store[hack][dur].append(k.strip())
            added += 1
    save_data(KEYS_FILE, keys_store)
    bot.send_message(message.chat.id, f"✅ تم إضافة {added} مفتاح بنجاح.", parse_mode="HTML")

def save_dynamic_price(message, hack, dur):
    try:
        PRICES[hack][dur] = float(message.text.strip())
        save_data(PRICES_FILE, PRICES)
        bot.send_message(message.chat.id, f"✅ تم تحديث السعر بنجاح.", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ يرجى إدخال رقم فقط.")

def process_redeem(message):
    code, uid_str = message.text.strip(), str(message.from_user.id)
    if code in redeem_codes:
        amt = redeem_codes.pop(code)
        users_data[uid_str]["balance"] += float(amt)
        save_data(USERS_FILE, users_data)
        save_data(REDEEM_FILE, redeem_codes)
        bot.send_message(message.chat.id, get_text(uid_str, "redeem_success", amount=amt), parse_mode="HTML")
    else: bot.send_message(message.chat.id, get_text(uid_str, "redeem_fail"), parse_mode="HTML")

def save_balance(message):
    try:
        tid, amt = message.text.split()
        if tid in users_data:
            users_data[tid]["balance"] += float(amt)
            save_data(USERS_FILE, users_data)
            bot.send_message(message.chat.id, f"✅ تم شحن رصيد العضو بنجاح.")
        else: bot.send_message(message.chat.id, "❌ العضو غير مسجل.")
    except: bot.send_message(message.chat.id, "❌ صيغة خاطئة.")

def save_redeem(message):
    try:
        code, amt = message.text.split()
        redeem_codes[code] = float(amt)
        save_data(REDEEM_FILE, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 تم توليد كود التعبئة: <code>{code}</code>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ صيغة خاطئة.")

if __name__ == "__main__":
    print("🤖 البوت يعمل الآن بنجاح...")
    bot.infinity_polling()
