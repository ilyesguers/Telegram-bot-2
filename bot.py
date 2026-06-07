import telebot
from telebot import types
import json
import os

# 1️⃣ الإعدادات الأساسية والتوكن
API_TOKEN = "8868383649:AAEVxFynrH7u_M8e9-wjxo6h8-NP8dtWNUQ"
bot = telebot.TeleBot(API_TOKEN)

# الإدارة
ADMIN_PRIMARY = 5145154527   # أنت (الآدمن الأول والأقوى)
ADMIN_SECONDARY = 88782290572 # الآدمن الثانوي

# ملفات قواعد البيانات
DB_USERS = "users_data.json"
DB_COUPONS = "coupons_data.json"
DB_PRODUCTS = "products_data.json"
DB_SETTINGS = "settings_data.json"

# دوال إدارة قواعد البيانات
def load_db(file_path, default_value):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_value

def save_db(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل البيانات
users_db = load_db(DB_USERS, {})
coupons_db = load_db(DB_COUPONS, {})
products_db = load_db(DB_PRODUCTS, {}) # الهيكل: {"ProductA": {"price": 10, "keys": ["key1", "key2"]}}
settings_db = load_db(DB_SETTINGS, {"invite_reward": 5}) # المكافأة الافتراضية للدعوة

def register_user(user):
    uid = str(user.id)
    if uid not in users_db:
        users_db[uid] = {
            "username": user.username or f"User_{uid}",
            "points": 0,
            "invited_by": None,
            "invite_count": 0,
            "lang": "ar"
        }
        save_db(DB_USERS, users_db)

# 2️⃣ بناء الكيبوردات والواجهات
def get_language_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar"),
        types.InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")
    )
    return keyboard

def get_main_keyboard(uid, lang):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if lang == "ar":
        keyboard.add(types.KeyboardButton("عرض الآيدي الخاص بي 🆔"))
        keyboard.add(types.KeyboardButton("🔗 نظام الدعوات (نقاط)"), types.KeyboardButton("🎟️ شحن كابون (Redeem)"))
    else:
        keyboard.add(types.KeyboardButton("show my id 🆔"))
        keyboard.add(types.KeyboardButton("🔗 Referral System"), types.KeyboardButton("🎟️ Redeem Coupon"))
        
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        keyboard.add(types.KeyboardButton("⚙️ وضع الأدمن"))
        
    return keyboard

# كيبورد الأدمن المطابق تماماً لصورة "image_2.png"
def get_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("➕ Add Product"), types.KeyboardButton("❌ Delete Product"))
    keyboard.add(types.KeyboardButton("🔑 Manage Keys"), types.KeyboardButton("🏷️ Edit Price"))
    keyboard.add(types.KeyboardButton("🔗 Edit Invite Reward"), types.KeyboardButton("🎫 Create Redeem"))
    keyboard.add(types.KeyboardButton("💰 Add Balance"), types.KeyboardButton("📊 Statistics"))
    keyboard.add(types.KeyboardButton("🔄 User Mode"))
    return keyboard

# ==========================================
# 3️⃣ الأوامر الأساسية ومعالجة الدعوات
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = str(message.from_user.id)
    register_user(message.from_user)
    
    args = message.text.split()
    if len(args) > 1 and users_db[uid]["invited_by"] is None:
        inviter_id = args[1]
        if inviter_id in users_db and inviter_id != uid:
            users_db[uid]["invited_by"] = inviter_id
            reward = settings_db.get("invite_reward", 5)
            users_db[inviter_id]["points"] += reward
            users_db[inviter_id]["invite_count"] += 1
            save_db(DB_USERS, users_db)
            try: bot.send_message(int(inviter_id), f"🎉 <b>إشعار إحالة!</b>\nدخل شخص جديد عبر رابطك، حصلت على <code>+{reward}</code> نقاط!", parse_mode="HTML")
            except: pass

    bot.send_message(message.chat.id, "🌐 Please select your language / يرجى تحديد لغتك:", reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_choice(call):
    uid = str(call.from_user.id)
    selected_lang = call.data.split("_")[1]
    users_db[uid]["lang"] = selected_lang
    save_db(DB_USERS, users_db)
    
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

    reply_text = "✅ تم تفعيل الحساب بنجاح!" if selected_lang == "ar" else "✅ Account activated successfully!"
    bot.send_message(call.message.chat.id, reply_text, reply_markup=get_main_keyboard(uid, selected_lang))

# ==========================================
# 4️⃣ مراقب نصوص الأزرار (لوحة المستخدم والأدمن)
# ==========================================

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    register_user(message.from_user)
    txt = message.text
    lang = users_db[uid]["lang"]
    is_admin = int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]

    # --- أزرار المستخدم العادية ---
    if txt in ["show my id 🆔", "عرض الآيدي الخاص بي 🆔"]:
        pts = users_db[uid]["points"]
        msg_id = f"👤 <b>الآيدي الخاص بك:</b> <code>{uid}</code>\n💰 <b>رصيد نقاطك:</b> <code>{pts}</code>" if lang == "ar" else f"👤 <b>Your ID:</b> <code>{uid}</code>\n💰 <b>Your Points:</b> <code>{pts}</code>"
        bot.send_message(message.chat.id, msg_id, parse_mode="HTML")

    elif txt in ["🔗 نظام الدعوات (نقاط)", "🔗 Referral System"]:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        invites = users_db[uid].get("invite_count", 0)
        reward = settings_db.get("invite_reward", 5)
        if lang == "ar":
            msg_ref = f"🔗 <b>اربح {reward} نقاط لكل دعوة!</b>\n\n👥 عدد دعواتك: <code>{invites}</code>\n📌 رابطك:\n<code>{ref_link}</code>"
        else:
            msg_ref = f"🔗 <b>Earn {reward} points per referral!</b>\n\n👥 Total Referrals: <code>{invites}</code>\n📌 Your Link:\n<code>{ref_link}</code>"
        bot.send_message(message.chat.id, msg_ref, parse_mode="HTML")

    elif txt in ["🎟️ شحن كابون (Redeem)", "🎟️ Redeem Coupon"]:
        m = bot.send_message(message.chat.id, "📥 أرسل رمز الكابون:" if lang == "ar" else "📥 Send coupon code:")
        bot.register_next_step_handler(m, process_redeem_coupon)

    # --- دخول لوحة التحكم ---
    elif txt == "⚙️ وضع الأدمن" and is_admin:
        bot.send_message(message.chat.id, "⚙️ تم الدخول للوحة التحكم بنجاح!", reply_markup=get_admin_keyboard())

    # ==========================================
    # 5️⃣ أزرار لوحة التحكم (المطابقة لـ image_2.png)
    # ==========================================
    elif is_admin:
        if txt == "🔄 User Mode":
            bot.send_message(message.chat.id, "🔙 العودة لوضع المستخدم.", reply_markup=get_main_keyboard(uid, lang))
            
        elif txt == "📊 Statistics":
            total_users = len(users_db)
            bot.send_message(message.chat.id, f"📈 <b>إحصائيات المتجر:</b>\n\n👥 الأعضاء: <code>{total_users}</code>", parse_mode="HTML")

        elif txt == "🎫 Create Redeem":
            m = bot.send_message(message.chat.id, "✍️ أرسل كود الكابون متبوعاً بمسافة ثم قيمة النقاط (مثال: VIP 50)")
            bot.register_next_step_handler(m, process_create_coupon)

        elif txt == "💰 Add Balance":
            m = bot.send_message(message.chat.id, "✍️ أرسل الآيدي ثم مسافة ثم عدد النقاط لإضافتها (مثال: 5145154527 100)")
            bot.register_next_step_handler(m, process_modify_points)

        elif txt == "🔗 Edit Invite Reward":
            m = bot.send_message(message.chat.id, f"🔗 الجائزة الحالية هي: {settings_db.get('invite_reward', 5)}\nأرسل عدد النقاط الجديد لكل دعوة:")
            bot.register_next_step_handler(m, process_edit_invite_reward)

        elif txt == "➕ Add Product":
            m = bot.send_message(message.chat.id, "➕ أرسل اسم المنتج الجديد:")
            bot.register_next_step_handler(m, process_add_product)

        elif txt == "❌ Delete Product":
            if not products_db: return bot.send_message(message.chat.id, "📭 لا يوجد منتجات لحذفها.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for p in products_db: markup.add(types.KeyboardButton(p))
            markup.add(types.KeyboardButton("إلغاء ❌"))
            m = bot.send_message(message.chat.id, "❌ اختر المنتج الذي تريد حذفه:", reply_markup=markup)
            bot.register_next_step_handler(m, process_delete_product)

        elif txt == "🏷️ Edit Price":
            if not products_db: return bot.send_message(message.chat.id, "📭 لا يوجد منتجات.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for p in products_db: markup.add(types.KeyboardButton(p))
            markup.add(types.KeyboardButton("إلغاء ❌"))
            m = bot.send_message(message.chat.id, "🏷️ اختر المنتج لتعديل سعره:", reply_markup=markup)
            bot.register_next_step_handler(m, process_select_product_price)

        elif txt == "🔑 Manage Keys":
            if not products_db: return bot.send_message(message.chat.id, "📭 لا يوجد منتجات.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for p in products_db: markup.add(types.KeyboardButton(p))
            markup.add(types.KeyboardButton("إلغاء ❌"))
            m = bot.send_message(message.chat.id, "🔑 اختر المنتج لإضافة مفاتيح له:", reply_markup=markup)
            bot.register_next_step_handler(m, process_select_product_keys)

# ==========================================
# 6️⃣ دوال المعالجة المساعدة (للمستخدم والأدمن)
# ==========================================

def process_redeem_coupon(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in coupons_db:
        pts = coupons_db.pop(code)
        users_db[uid]["points"] += pts
        save_db(DB_USERS, users_db)
        save_db(DB_COUPONS, coupons_db)
        bot.send_message(message.chat.id, f"🎉 <b>تم الشحن!</b>\nأضيفت <code>+{pts}</code> نقاط.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ الكوبون غير صحيح أو مستخدم.")

def process_create_coupon(message):
    try:
        code, points = message.text.split()
        coupons_db[code] = int(points)
        save_db(DB_COUPONS, coupons_db)
        bot.send_message(message.chat.id, f"✅ تم إنشاء كوبون: <code>{code}</code> بقيمة {points} نقطة.", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ خطأ بالصيغة.")

def process_modify_points(message):
    try:
        target_id, points = message.text.split()
        points = int(points)
        if target_id in users_db:
            users_db[target_id]["points"] += points
            save_db(DB_USERS, users_db)
            bot.send_message(message.chat.id, f"✅ تمت الإضافة. رصيد {target_id} الجديد: {users_db[target_id]['points']}")
        else: bot.send_message(message.chat.id, "❌ المستخدم غير موجود.")
    except: bot.send_message(message.chat.id, "❌ خطأ بالصيغة.")

def process_edit_invite_reward(message):
    try:
        settings_db["invite_reward"] = int(message.text.strip())
        save_db(DB_SETTINGS, settings_db)
        bot.send_message(message.chat.id, f"✅ تم تعديل جائزة الدعوة لتصبح: {settings_db['invite_reward']} نقاط.")
    except: bot.send_message(message.chat.id, "❌ يرجى إرسال أرقام فقط.")

def process_add_product(message):
    name = message.text.strip()
    if name not in products_db:
        products_db[name] = {"price": 0, "keys": []}
        save_db(DB_PRODUCTS, products_db)
        bot.send_message(message.chat.id, f"✅ تمت إضافة المنتج: {name}")
    else: bot.send_message(message.chat.id, "❌ المنتج موجود مسبقاً.")

def process_delete_product(message):
    name = message.text.strip()
    if name == "إلغاء ❌": return bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=get_admin_keyboard())
    if name in products_db:
        del products_db[name]
        save_db(DB_PRODUCTS, products_db)
        bot.send_message(message.chat.id, f"✅ تم حذف {name} بنجاح.", reply_markup=get_admin_keyboard())
    else: bot.send_message(message.chat.id, "❌ لم يتم العثور على المنتج.", reply_markup=get_admin_keyboard())

def process_select_product_price(message):
    name = message.text.strip()
    if name == "إلغاء ❌": return bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=get_admin_keyboard())
    if name in products_db:
        m = bot.send_message(message.chat.id, f"🏷️ أرسل السعر الجديد بالنقاط للمنتج ({name}):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(m, lambda msg: process_save_price(msg, name))
    else: bot.send_message(message.chat.id, "❌ لم يتم العثور على المنتج.", reply_markup=get_admin_keyboard())

def process_save_price(message, name):
    try:
        products_db[name]["price"] = int(message.text.strip())
        save_db(DB_PRODUCTS, products_db)
        bot.send_message(message.chat.id, f"✅ تم حفظ السعر للمنتج {name} ليصبح {products_db[name]['price']} نقاط.", reply_markup=get_admin_keyboard())
    except: bot.send_message(message.chat.id, "❌ خطأ. يرجى إدخال أرقام فقط.", reply_markup=get_admin_keyboard())

def process_select_product_keys(message):
    name = message.text.strip()
    if name == "إلغاء ❌": return bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=get_admin_keyboard())
    if name in products_db:
        m = bot.send_message(message.chat.id, f"🔑 أرسل المفاتيح للمنتج ({name}).\nيمكنك إرسال أكثر من مفتاح بجعل كل مفتاح في سطر جديد:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(m, lambda msg: process_save_keys(msg, name))
    else: bot.send_message(message.chat.id, "❌ لم يتم العثور على المنتج.", reply_markup=get_admin_keyboard())

def process_save_keys(message, name):
    keys = message.text.strip().split("\n")
    products_db[name]["keys"].extend(keys)
    save_db(DB_PRODUCTS, products_db)
    bot.send_message(message.chat.id, f"✅ تم إضافة {len(keys)} مفتاح للمنتج {name}. الإجمالي: {len(products_db[name]['keys'])}", reply_markup=get_admin_keyboard())

# التشغيل المستمر
if __name__ == "__main__":
    print("🚀 البوت يعمل الآن..")
    bot.infinity_polling()
