import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta

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
products_db = load_db(DB_PRODUCTS, {}) 
settings_db = load_db(DB_SETTINGS, {"invite_reward": 5, "daily_bonus": 10})

def register_user(user):
    uid = str(user.id)
    if uid not in users_db:
        users_db[uid] = {
            "username": user.username or f"User_{uid}",
            "points": 0,
            "invited_by": None,
            "invite_count": 0,
            "last_claim": None,
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
        keyboard.add(types.KeyboardButton("🛒 متجر المنتجات (Shop)"), types.KeyboardButton("🎁 المكافأة اليومية"))
        keyboard.add(types.KeyboardButton("🔗 نظام الدعوات (نقاط)"), types.KeyboardButton("🎟️ شحن كابون (Redeem)"))
    else:
        keyboard.add(types.KeyboardButton("show my id 🆔"))
        keyboard.add(types.KeyboardButton("🛒 Product Shop"), types.KeyboardButton("🎁 Daily Bonus"))
        keyboard.add(types.KeyboardButton("🔗 Referral System"), types.KeyboardButton("🎟️ Redeem Coupon"))
        
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        keyboard.add(types.KeyboardButton("⚙️ وضع الأدمن"))
        
    return keyboard

def get_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("➕ Add Product"), types.KeyboardButton("❌ Delete Product"))
    keyboard.add(types.KeyboardButton("🔑 Manage Keys"), types.KeyboardButton("🏷️ Edit Price"))
    keyboard.add(types.KeyboardButton("🔗 Edit Invite Reward"), types.KeyboardButton("🎁 Edit Daily Bonus"))
    keyboard.add(types.KeyboardButton("TXT 🎫 Create Redeem"), types.KeyboardButton("💰 Add Balance"))
    keyboard.add(types.KeyboardButton("📊 Statistics"))
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

    # --- عرض الآيدي والنقاط ---
    if txt in ["show my id 🆔", "عرض الآيدي الخاص بي 🆔"]:
        pts = users_db[uid]["points"]
        msg_id = f"👤 <b>الآيدي الخاص بك:</b> <code>{uid}</code>\n💰 <b>رصيد نقاطك:</b> <code>{pts}</code>" if lang == "ar" else f"👤 <b>Your ID:</b> <code>{uid}</code>\n💰 <b>Your Points:</b> <code>{pts}</code>"
        bot.send_message(message.chat.id, msg_id, parse_mode="HTML")

    # --- نظام الدعوات ---
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

    # --- شحن كابون ---
    elif txt in ["🎟️ شحن كابون (Redeem)", "🎟️ Redeem Coupon"]:
        m = bot.send_message(message.chat.id, "📥 أرسل رمز الكابون:" if lang == "ar" else "📥 Send coupon code:")
        bot.register_next_step_handler(m, process_redeem_coupon)

    # --- المكافأة اليومية ---
    elif txt in ["🎁 المكافأة اليومية", "🎁 Daily Bonus"]:
        handle_daily_bonus(message, uid, lang)

    # --- متجر المنتجات (الشوب) ---
    elif txt in ["🛒 متجر المنتجات (Shop)", "🛒 Product Shop"]:
        if not products_db:
            return bot.send_message(message.chat.id, "📭 المتجر فارغ حالياً." if lang == "ar" else "📭 The shop is currently empty.")
        
        markup = types.InlineKeyboardMarkup()
        for p_name in products_db.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {p_name}", callback_data=f"shop_select_{p_name}"))
            
        msg_shop = "🛒 <b>قائمة المنتجات المتوفرة:</b>\nاختر المنتج لمعاينة خططه وأسعاره المتاحة:" if lang == "ar" else "🛒 <b>Available Products:</b>\nSelect a product to view plans & prices:"
        bot.send_message(message.chat.id, msg_shop, reply_markup=markup, parse_mode="HTML")

    # --- دخول لوحة التحكم للآدمن ---
    elif txt == "⚙️ وضع الأدمن" and is_admin:
        bot.send_message(message.chat.id, "⚙️ تم الدخول للوحة التحكم بنجاح!", reply_markup=get_admin_keyboard())

    # ==========================================
    # 5️⃣ إدارة أزرار لوحة التحكم 
    # ==========================================
    elif is_admin:
        if txt == "🔄 User Mode":
            bot.send_message(message.chat.id, "🔙 العودة لوضع المستخدم.", reply_markup=get_main_keyboard(uid, lang))
            
        elif txt == "📊 Statistics":
            total_users = len(users_db)
            bot.send_message(message.chat.id, f"📈 <b>إحصائيات المتجر:</b>\n\n👥 الأعضاء: <code>{total_users}</code>", parse_mode="HTML")

        elif txt == "TXT 🎫 Create Redeem":
            m = bot.send_message(message.chat.id, "✍️ أرسل كود الكابون متبوعاً بمسافة ثم قيمة النقاط (مثال: VIP 50)")
            bot.register_next_step_handler(m, process_create_coupon)

        elif txt == "💰 Add Balance":
            m = bot.send_message(message.chat.id, "✍️ أرسل الآيدي ثم مسافة ثم عدد النقاط لإضافتها (مثال: 5145154527 100)")
            bot.register_next_step_handler(m, process_modify_points)

        elif txt == "🔗 Edit Invite Reward":
            m = bot.send_message(message.chat.id, f"🔗 الجائزة الحالية هي: {settings_db.get('invite_reward', 5)}\nأرسل عدد النقاط الجديد لكل دعوة:")
            bot.register_next_step_handler(m, process_edit_invite_reward)

        elif txt == "🎁 Edit Daily Bonus":
            m = bot.send_message(message.chat.id, f"🎁 المكافأة اليومية الحالية هي: {settings_db.get('daily_bonus', 10)} نقاط.\nأرسل القيمة الجديدة للمكافأة:")
            bot.register_next_step_handler(m, process_edit_daily_bonus)

        elif txt == "➕ Add Product":
            m = bot.send_message(message.chat.id, "➕ أرسل اسم المنتج الجديد (سيتم تقسيمه تلقائياً لـ يوم، 7 أيام، 30 يوم):")
            bot.register_next_step_handler(m, process_add_product)

        elif txt == "❌ Delete Product":
            if not products_db: return bot.send_message(message.chat.id, "📭 لا يوجد منتجات لحذفها.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for p in products_db: markup.add(types.KeyboardButton(p))
            markup.add(types.KeyboardButton("إلغاء ❌"))
            m = bot.send_message(message.chat.id, "❌ اختر المنتج الذي تريد حذفه بالكامل:", reply_markup=markup)
            bot.register_next_step_handler(m, process_delete_product)

        elif txt == "🏷️ Edit Price":
            if not products_db: return bot.send_message(message.chat.id, "📭 لا يوجد منتجات.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for p in products_db: markup.add(types.KeyboardButton(p))
            markup.add(types.KeyboardButton("إلغاء ❌"))
            m = bot.send_message(message.chat.id, "🏷️ اختر المنتج لتعديل أسعار خططه:", reply_markup=markup)
            bot.register_next_step_handler(m, process_select_product_price)

        elif txt == "🔑 Manage Keys":
            if not products_db: return bot.send_message(message.chat.id, "📭 لا يوجد منتجات.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for p in products_db: markup.add(types.KeyboardButton(p))
            markup.add(types.KeyboardButton("إلغاء ❌"))
            m = bot.send_message(message.chat.id, "🔑 اختر المنتج لإضافة مفاتيح داخله:", reply_markup=markup)
            bot.register_next_step_handler(m, process_select_product_keys)

# ==========================================
# 6️⃣ تفاعل أزرار الإنلاين (الشراء من الشوب)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def handle_shop_clicks(call):
    uid = str(call.from_user.id)
    lang = users_db[uid]["lang"]
    data = call.data.split("_")
    
    # عند اختيار منتج يظهر انقسام المدد (يوم، 7 أيام، 30 يوم) وأسعارها
    if data[1] == "select":
        p_name = data[2]
        if p_name not in products_db: return
        
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            price = products_db[p_name][plan]["price"]
            stock = len(products_db[p_name][plan]["keys"])
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} | 💰 {price} Pts (المخزون: {stock})", callback_data=f"shop_buy_{p_name}_{plan}"))
            
        msg = f"🛒 <b>المنتج: {p_name}</b>\nاختر خطة الاشتراك المناسبة لإتمام الشراء بالنقاط:" if lang == "ar" else f"🛒 <b>Product: {p_name}</b>\nSelect a plan to buy with points:"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        
    # معالجة عملية الشراء وخصم النقاط
    elif data[1] == "buy":
        p_name = data[2]
        plan = data[3]
        
        if p_name not in products_db: return
        price = products_db[p_name][plan]["price"]
        keys_list = products_db[p_name][plan]["keys"]
        
        if users_db[uid]["points"] < price:
            err = "❌ رصيد نقاطك غير كافٍ لإتمام عملية الشراء!" if lang == "ar" else "❌ Insufficient points balance!"
            bot.answer_callback_query(call.id, err, show_alert=True)
            return
            
        if not keys_list:
            err = "⚠️ عذراً، هذا المنتج غير متوفر حالياً في المخزن." if lang == "ar" else "⚠️ Sorry, this product is out of stock."
            bot.answer_callback_query(call.id, err, show_alert=True)
            return
            
        # خصم النقاط وتسليم المفتاح الأول
        users_db[uid]["points"] -= price
        delivered_key = keys_list.pop(0)
        save_db(DB_USERS, users_db)
        save_db(DB_PRODUCTS, products_db)
        
        success = f"🎉 <b>تمت عملية الشراء بنجاح!</b>\n\n📦 المنتج: <code>{p_name} ({plan})</code>\n🔐 المفتاح الخاص بك:\n<code>{delivered_key}</code>" if lang == "ar" else f"🎉 <b>Purchase successful!</b>\n\n📦 Product: <code>{p_name} ({plan})</code>\n🔐 Your Key:\n<code>{delivered_key}</code>"
        bot.edit_message_text(success, call.message.chat.id, call.message.message_id, parse_mode="HTML")

# ==========================================
# 7️⃣ دوال المعالجة المساعدة والخلفية
# ==========================================

# دالة المكافأة اليومية
def handle_daily_bonus(message, uid, lang):
    now = datetime.now()
    last_claim_str = users_db[uid].get("last_claim")
    
    if last_claim_str:
        last_claim = datetime.fromisoformat(last_claim_str)
        if now < last_claim + timedelta(days=1):
            remaining = (last_claim + timedelta(days=1)) - now
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            msg_wait = f"⏳ لقد استلمت مكافأتك اليومية بالفعل، يرجى الانتظار <code>{hours} ساعة و {minutes} دقيقة</code> أخرى." if lang == "ar" else f"⏳ You have already claimed your daily bonus. Please wait <code>{hours}h {minutes}m</code>."
            bot.send_message(message.chat.id, msg_wait, parse_mode="HTML")
            return
            
    bonus = settings_db.get("daily_bonus", 10)
    users_db[uid]["points"] += bonus
    users_db[uid]["last_claim"] = now.isoformat()
    save_db(DB_USERS, users_db)
    
    msg_ok = f"🎁 <b>مبروك!</b> لقد حصلت على مكافأتك اليومية المجانية بقيمة <code>+{bonus}</code> نقاط!" if lang == "ar" else f"🎁 <b>Congratulations!</b> You got your free daily bonus of <code>+{bonus}</code> points!"
    bot.send_message(message.chat.id, msg_ok, parse_mode="HTML")

def process_redeem_coupon(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    if code in coupons_db:
        pts = coupons_db.pop(code)
        users_db[uid]["points"] += pts
        save_db(DB_USERS, users_db)
        save_db(DB_COUPONS, coupons_db)
        bot.send_message(message.chat.id, f"🎉 <b>تم الشحن!</b>\nأضيفت <code>+{pts}</code> نقاط.", parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ الكوبون غير صحيح.")

def process_create_coupon(message):
    try:
        code, points = message.text.split()
        coupons_db[code] = int(points)
        save_db(DB_COUPONS, coupons_db)
        bot.send_message(message.chat.id, f"✅ تم إنشاء كوبون: <code>{code}</code> بقيمة {points} نقطة.", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ خطأ بالصيغة.")

def process_modify_points(message):
    try:
        target_id, points = message.text.split()
        points = int(points)
        if target_id in users_db:
            users_db[target_id]["points"] += points
            save_db(DB_USERS, users_db)
            bot.send_message(message.chat.id, f"✅ تمت الإضافة بنجاح للمستخدم.")
        else: bot.send_message(message.chat.id, "❌ المستخدم غير موجود.")
    except: bot.send_message(message.chat.id, "❌ خطأ بالصيغة.")

def process_edit_invite_reward(message):
    try:
        settings_db["invite_reward"] = int(message.text.strip())
        save_db(DB_SETTINGS, settings_db)
        bot.send_message(message.chat.id, f"✅ تم تعديل جائزة الدعوة لتصبح: {settings_db['invite_reward']} نقاط.")
    except: bot.send_message(message.chat.id, "❌ أرقام فقط.")

def process_edit_daily_bonus(message):
    try:
        settings_db["daily_bonus"] = int(message.text.strip())
        save_db(DB_SETTINGS, settings_db)
        bot.send_message(message.chat.id, f"✅ تم تحديث المكافأة اليومية لتصبح: <code>{settings_db['daily_bonus']}</code> نقاط.", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ خطأ بالصيغة. يرجى إدخال رقم صحيح.")

# دالة إضافة منتج (ينقسم تلقائياً لـ 3 مدد)
def process_add_product(message):
    name = message.text.strip()
    if name not in products_db:
        products_db[name] = {
            "1 Day": {"price": 10, "keys": []},
            "7 Days": {"price": 50, "keys": []},
            "30 Days": {"price": 150, "keys": []}
        }
        save_db(DB_PRODUCTS, products_db)
        bot.send_message(message.chat.id, f"✅ تمت إضافة المنتج ({name}) بنجاح.\nتم إنشاء الأقسام تلقائياً (1 Day, 7 Days, 30 Days).\n⚠️ يمكنك الآن استخدام الأزرار لتعديل الأسعار وإضافة المفاتيح لكل خطة.")
    else: bot.send_message(message.chat.id, "❌ المنتج موجود مسبقاً.")

def process_delete_product(message):
    name = message.text.strip()
    if name == "إلغاء ❌": return bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=get_admin_keyboard())
    if name in products_db:
        del products_db[name]
        save_db(DB_PRODUCTS, products_db)
        bot.send_message(message.chat.id, f"✅ تم حذف {name} بالكامل من المتجر.", reply_markup=get_admin_keyboard())

# تعديل الأسعار للمدد الـ 3
def process_select_product_price(message):
    name = message.text.strip()
    if name in products_db:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("1 Day", "7 Days", "30 Days")
        m = bot.send_message(message.chat.id, f"اختر الخطة الزمنية المراد تعديل سعرها للمنتج ({name}):", reply_markup=markup)
        bot.register_next_step_handler(m, lambda msg: process_enter_new_price(msg, name))

def process_enter_new_price(message, name):
    plan = message.text.strip()
    if plan in ["1 Day", "7 Days", "30 Days"]:
        m = bot.send_message(message.chat.id, f"🏷️ أدخل السعر الجديد (نقاط) للخطة {plan}:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(m, lambda msg: process_save_price(msg, name, plan))

def process_save_price(message, name, plan):
    try:
        products_db[name][plan]["price"] = int(message.text.strip())
        save_db(DB_PRODUCTS, products_db)
        bot.send_message(message.chat.id, f"✅ تم تعديل سعر {name} ({plan}) إلى {message.text} نقطة.", reply_markup=get_admin_keyboard())
    except: bot.send_message(message.chat.id, "❌ خطأ في القيمة.", reply_markup=get_admin_keyboard())

# إضافة المفاتيح للمدد الـ 3
def process_select_product_keys(message):
    name = message.text.strip()
    if name in products_db:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("1 Day", "7 Days", "30 Days")
        m = bot.send_message(message.chat.id, f"اختر الفئة الزمنية التي تريد شحن المفاتيح داخلها للمنتج ({name}):", reply_markup=markup)
        bot.register_next_step_handler(m, lambda msg: process_enter_keys(msg, name))

def process_enter_keys(message, name):
    plan = message.text.strip()
    if plan in ["1 Day", "7 Days", "30 Days"]:
        m = bot.send_message(message.chat.id, f"🔑 أرسل المفاتيح لـ ({name} - {plan}).\n(كل مفتاح في سطر جديد):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(m, lambda msg: process_save_keys(msg, name, plan))

def process_save_keys(message, name, plan):
    keys = message.text.strip().split("\n")
    products_db[name][plan]["keys"].extend(keys)
    save_db(DB_PRODUCTS, products_db)
    bot.send_message(message.chat.id, f"✅ تم حفظ {len(keys)} مفتاح في خطة {plan}. الإجمالي الحالي: {len(products_db[name][plan]['keys'])}", reply_markup=get_admin_keyboard())

# التشغيل المستمر
if __name__ == "__main__":
    print("🚀 البوت المحدث والشوب يعملان الآن بنجاح..")
    bot.infinity_polling()
