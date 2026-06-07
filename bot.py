import telebot
from telebot import types
import json
import os

# 1️⃣ الإعدادات الأساسية والتوكن
API_TOKEN = "8868383649:AAEVxFynrH7u_M8e9-wjxo6h8-NP8dtWNUQ"
bot = telebot.TeleBot(API_TOKEN)

# تحديد الإدارة بوضوح
ADMIN_PRIMARY = 5145154527   # أنت (الآدمن الأول والأقوى)
ADMIN_SECONDARY = 88782290572 # الآدمن الثانوي

# ملفات حفظ البيانات (قاعدة بيانات بسيطة JSON)
DB_USERS = "users_data.json"
DB_COUPONS = "coupons_data.json"

# دوال إدارة قواعد البيانات
def load_db(file_path, default_value):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_value

def save_db(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل البيانات عند بدء تشغيل البوت
users_db = load_db(DB_USERS, {})
coupons_db = load_db(DB_COUPONS, {})

# دالة تسجيل المستخدم أو تحديث بياناته
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
    
    # الخانات الأساسية بناءً على اللغة
    if lang == "ar":
        btn_id = types.KeyboardButton("عرض الآيدي الخاص بي 🆔")
        btn_invite = types.KeyboardButton("🔗 نظام الدعوات (نقاط)")
        btn_coupon = types.KeyboardButton("🎟️ شحن كابون (Redeem)")
    else:
        btn_id = types.KeyboardButton("show my id 🆔")
        btn_invite = types.KeyboardButton("🔗 Referral System")
        btn_coupon = types.KeyboardButton("🎟️ Redeem Coupon")
        
    keyboard.add(btn_id)
    keyboard.add(btn_invite, btn_coupon)
    
    # إذا كان المستخدم آدمن (أول أو ثانوي) تظهر له خانة لوحة التحكم تلقائياً
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        btn_admin = types.KeyboardButton("💻 لوحة التحكم الإدارية")
        keyboard.add(btn_admin)
        
    return keyboard

def get_admin_keyboard(uid):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("➕ صنع كابون نقاط"), types.KeyboardButton("✍️ تعديل نقاط مستخدم"))
    
    # ميزة خاصة بالآدمن الأول والأقوى فقط (تصفير أو تعديل بيانات الكاملة)
    if int(uid) == ADMIN_PRIMARY:
        keyboard.add(types.KeyboardButton("👑 صلاحيات الآدمن الأقوى"))
        
    keyboard.add(types.KeyboardButton("🔙 العودة للقائمة الرئيسية"))
    return keyboard

# ==========================================
# 3️⃣ الأوامر ومعالجة النصوص
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = str(message.from_user.id)
    register_user(message.from_user)
    
    # نظام الإحالة: التحقق إذا كان الرابط يحتوي على دعوة من شخص آخر
    args = message.text.split()
    if len(args) > 1 and users_db[uid]["invited_by"] is None:
        inviter_id = args[1]
        # شروط الإحالة: أن يكون الحساب الداعي موجود وغير حساب المستخدم نفسه
        if inviter_id in users_db and inviter_id != uid:
            users_db[uid]["invited_by"] = inviter_id
            # مكافأة الداعي بـ 5 نقاط كمثال
            users_db[inviter_id]["points"] += 5
            users_db[inviter_id]["invite_count"] += 1
            save_db(DB_USERS, users_db)
            try:
                bot.send_message(int(inviter_id), f"🎉 <b>إشعار إحالة!</b>\nدخل شخص جديد عبر رابطك، حصلت على <code>+5</code> نقاط!")
            except:
                pass

    bot.send_message(message.chat.id, "🌐 Please select your language / يرجى تحديد لغتك:", reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_choice(call):
    uid = str(call.from_user.id)
    selected_lang = call.data.split("_")[1]
    
    users_db[uid]["lang"] = selected_lang
    save_db(DB_USERS, users_db)
    
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

    if selected_lang == "ar":
        reply_text = "✅ تم تفعيل الحساب بنجاح!\n\nأهلاً بك في القائمة الرئيسية، تفضل باختيار الخانة المطلوبة من الأسفل 👇"
    else:
        reply_text = "✅ Account activated successfully!\n\nWelcome to the main menu, please select an option from below 👇"

    bot.send_message(call.message.chat.id, reply_text, reply_markup=get_main_keyboard(uid, selected_lang))

# ==========================================
# 4️⃣ مراقب أزرار الشاشة الرئيسية
# ==========================================

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    register_user(message.from_user)
    txt = message.text
    lang = users_db[uid]["lang"]

    # --- خانة عرض الآيدي والنقاط الحالية ---
    if txt in ["show my id 🆔", "عرض الآيدي الخاص بي 🆔"]:
        pts = users_db[uid]["points"]
        if lang == "ar":
            msg_id = f"👤 <b>الآيدي الخاص بك:</b> <code>{uid}</code>\n💰 <b>رصيد نقاطك الحالي:</b> <code>{pts}</code> نقطة"
        else:
            msg_id = f"👤 <b>Your Telegram ID:</b> <code>{uid}</code>\n💰 <b>Your Current Points:</b> <code>{pts}</code> points"
        bot.send_message(message.chat.id, msg_id, parse_mode="HTML")

    # --- خانة نظام الإحالات والدعوات ---
    elif txt in ["🔗 نظام الدعوات (نقاط)", "🔗 Referral System"]:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        invites = users_db[uid].get("invite_count", 0)
        if lang == "ar":
            msg_ref = f"🔗 <b>نظام كسب النقاط عبر دعوة الأصدقاء:</b>\n\nقم بنسخ رابطك الخاص وإرساله لأصدقائك، ستحصل على <b>5 نقاط</b> عن كل صديق يقوم بتفعيل البوت!\n\n👥 عدد دعواتك الحالية: <code>{invites}</code>\n\n📌 رابط الدعوة الخاص بك:\n<code>{ref_link}</code>"
        else:
            msg_ref = f"🔗 <b>Referral & Earn Points System:</b>\n\nShare your link with your friends to get <b>5 points</b> for each successful referral!\n\n👥 Total Referrals: <code>{invites}</code>\n\n📌 Your Referral Link:\n<code>{ref_link}</code>"
        bot.send_message(message.chat.id, msg_ref, parse_mode="HTML")

    # --- خانة شحن الكوبونات للمستخدمين ---
    elif txt in ["🎟️ شحن كابون (Redeem)", "🎟️ Redeem Coupon"]:
        if lang == "ar":
            prompt = "📥 يرجى إرسال رمز الكابون المراد شحنه الآن:"
        else:
            prompt = "📥 Please send the coupon code you want to redeem:"
        m = bot.send_message(message.chat.id, prompt)
        bot.register_next_step_handler(m, process_redeem_coupon)

    # --- خانة الدخول للوحة التحكم الإدارية (للأدمن فقط) ---
    elif txt == "💻 لوحة التحكم الإدارية" and int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        bot.send_message(message.chat.id, "⚙️ مرحباً بك في لوحة تحكم الإدارة الشاملة:", reply_markup=get_admin_keyboard(uid))

    # --- العودة للقائمة الرئيسية من لوحة الإدارة ---
    elif txt == "🔙 العودة للقائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 تم الانتقال للقائمة الرئيسية للمستخدمين.", reply_markup=get_main_keyboard(uid, lang))

    # --- أزرار داخل لوحة الإدارة ---
    elif txt == "➕ صنع كابون نقاط" and int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        m = bot.send_message(message.chat.id, "✍️ أرسل كود الكابون المطلوب ثم قيمته (نقاطه) وبينهما مسافة واحدة فقط\nمثال: `VIP2026 50`")
        bot.register_next_step_handler(m, process_create_coupon)

    elif txt == "✍️ تعديل نقاط مستخدم" and int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        m = bot.send_message(message.chat.id, "✍️ أرسل آيدي المستخدم (ID) ثم عدد النقاط المراد إضافتها أو خصمها وبينهما مسافة\nمثال لإضافة نقاط: `5145154527 100`\nمثال لخصم نقاط: `5145154527 -50`")
        bot.register_next_step_handler(m, process_modify_points)

    elif txt == "👑 صلاحيات الآدمن الأقوى" and int(uid) == ADMIN_PRIMARY:
        total_users = len(users_db)
        total_coupons = len(coupons_db)
        bot.send_message(message.chat.id, f"👑 <b>مرحباً بك يا مالك البوت الأقوى!</b>\n\n📊 إحصائيات سريعة:\n👥 عدد المستخدمين الكلي: <code>{total_users}</code>\n🎟️ عدد الكوبونات الفعالة: <code>{total_coupons}</code>")

# ==========================================
# 5️⃣ وظائف المعالجة والخلفية
# ==========================================

# دالة شحن الكوبون من قبل مستخدم
def process_redeem_coupon(message):
    uid = str(message.from_user.id)
    coupon_code = message.text.strip()
    lang = users_db[uid]["lang"]

    if coupon_code in coupons_db:
        points_to_give = coupons_db[coupon_code]
        users_db[uid]["points"] += points_to_give
        del coupons_db[coupon_code] # مسح الكوبون حتى لا يستعمل مرة أخرى
        save_db(DB_USERS, users_db)
        save_db(DB_COUPONS, coupons_db)
        
        if lang == "ar":
            bot.send_message(message.chat.id, f"🎉 <b>تم الشحن بنجاح!</b>\nتم إضافة <code>+{points_to_give}</code> نقاط إلى حسابك.", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, f"🎉 <b>Redeemed successfully!</b>\n<code>+{points_to_give}</code> points have been added to your account.", parse_mode="HTML")
    else:
        if lang == "ar":
            bot.send_message(message.chat.id, "❌ الكوبون خاطئ أو مستخدم مسبقاً، يرجى التحقق من الكود.")
        else:
            bot.send_message(message.chat.id, "❌ Invalid or already redeemed coupon code.")

# دالة صنع الكوبون من قبل الإدارة
def process_create_coupon(message):
    uid = str(message.from_user.id)
    try:
        code, points = message.text.split()
        points = int(points)
        coupons_db[code] = points
        save_db(DB_COUPONS, coupons_db)
        bot.send_message(message.chat.id, f"✅ <b>تم إنشاء الكوبون بنجاح!</b>\n🎫 الكود: <code>{code}</code>\n💰 قيمته: <code>{points}</code> نقاط", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ خطأ في الإدخال، تأكد من كتابة الكود ثم مسافة ثم عدد النقاط بشكل صحيح.")

# دالة تعديل نقاط مستخدم من قبل الإدارة
def process_modify_points(message):
    try:
        target_id, points_change = message.text.split()
        points_change = int(points_change)
        
        if target_id in users_db:
            users_db[target_id]["points"] += points_change
            save_db(DB_USERS, users_db)
            bot.send_message(message.chat.id, f"✅ تم تعديل النقاط للمستخدم بنجاح.\nالرصيد الجديد للحساب <code>{target_id}</code> هو: <code>{users_db[target_id]['points']}</code>", parse_mode="HTML")
            try:
                bot.send_message(int(target_id), f"🔔 <b>إشعار إداري:</b>\nتم تعديل رصيد نقاطك من قبل الإدارة بمقدار: <code>{points_change}</code>")
            except: pass
        else:
            bot.send_message(message.chat.id, "❌ لم يتم العثور على هذا الآيدي في قاعدة بيانات البوت.")
    except:
        bot.send_message(message.chat.id, "❌ خطأ في الإدخال، يرجى الالتزام بالصيغة (الآيدي ثم مسافة ثم عدد النقاط).")

# تشغيل البوت
if __name__ == "__main__":
    print("🚀 البوت المتكامل والذكي يعمل الآن..")
    bot.infinity_polling()
