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
    }
}
# تم اختصار بقية اللغات هنا لتقليل حجم الكود، يمكنك إضافة قواميس اللغات السابقة كما كانت

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
    markup.add(types.KeyboardButton("💰 شحن الأعضاء"), types.KeyboardButton("🎫 إنشاء أكواد الشحن"))
    markup.add(types.KeyboardButton("🔥 التخفيضات"), types.KeyboardButton("📢 الإذاعة الشاملة"))
    markup.add(types.KeyboardButton("📤 نشر الأسعار بالقناة"), types.KeyboardButton("📣 التسويق الوهمي"))
    markup.add(types.KeyboardButton("✨ تعديل المكافأة"), types.KeyboardButton("☁️ النسخ الاحتياطي"))
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
    if lang not in LOCALES: lang = "ar"
    txt = message.text

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config["maintenance"] and not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    # --- أزرار المستخدمين ---
    if txt in [LOCALES[l].get("id_btn") for l in LOCALES if "id_btn" in LOCALES[l]]:
        bot.send_message(message.chat.id, f"🆔 الآيدي الخاص بك: <code>{uid}</code>", parse_mode="HTML")

    elif txt in [LOCALES[l].get("balance_btn") for l in LOCALES if "balance_btn" in LOCALES[l]]:
        u = users[uid]
        msg = f"💰 <b>بيانات رصيدك وحسابك:</b>\n\n• ID: {uid}\n• رصيد النقاط: {u['points']} نقطة\n• عدد الدعوات الناجحة: {u.get('invite_count', 0)}\n• لغة البوت الحالية: {u['lang'].upper()}\n• حالة الحظر: نشط 🟢"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    elif txt in [LOCALES[l].get("bonus_btn") for l in LOCALES if "bonus_btn" in LOCALES[l]]:
        now = datetime.now()
        lc = users[uid].get("last_claim")
        if lc and now < datetime.fromisoformat(lc) + timedelta(days=1):
            bot.send_message(message.chat.id, "❌ لقد استلمت المكافأة اليومية بالفعل، يرجى المحاولة بعد انتهاء 24 ساعة.")
        else:
            users[uid]["last_claim"] = now.isoformat()
            users[uid]["points"] += bot_config["daily_bonus"]
            save_json(DB_USERS, users)
            bot.send_message(message.chat.id, f"✨ تم استلام مكافأتك اليومية بنجاح وهي +{bot_config['daily_bonus']} نقاط!")

    # --- واجهة الإدارة ---
    elif txt in [LOCALES[l].get("admin_btn") for l in LOCALES if "admin_btn" in LOCALES[l]] and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 مرحباً بك في لوحة تحكم ميزات الإدارة للمتجر:", reply_markup=get_admin_keyboard())

    elif int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False):
        if txt == "🔄 واجهة المستخدم":
            bot.send_message(message.chat.id, "🔙 تم الانتقال إلى واجهة المستخدم العادية.", reply_markup=get_main_keyboard(uid, lang))

        elif txt == "✨ تعديل المكافأة":
            m = bot.send_message(message.chat.id, f"⚙️ القيمة الحالية للمكافأة: {bot_config['daily_bonus']} نقطة.\n\n✍️ أرسل القيمة الجديدة الآن (أرقام فقط):")
            bot.register_next_step_handler(m, admin_edit_daily_bonus)

        elif txt == "👥 إدارة الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل آيدي العضو لعرض تفاصيله والتحكم في رتبته وحظره بالأزرار:")
            bot.register_next_step_handler(m, admin_view_member_func)

        elif txt == "📣 التسويق الوهمي":
            m = bot.send_message(message.chat.id, "⚠️ <b>تأكيد الإجراء:</b> من فضلك اكتب كلمة عشوائية أو كلمة <code>تأكيد</code> لتفادي الإرسال بالغلط:", parse_mode="HTML")
            bot.register_next_step_handler(m, admin_confirm_fake_marketing)
        
        # يمكنك إضافة بقية الأوامر هنا بنفس الطريقة المتبعة سابقاً (إضافة منتج، إنشاء أكواد... الخ)

# ==========================================
# معالجة تعديل المكافأة والأزرار التفاعلية للإدارة
# ==========================================

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

def admin_view_member_func(message):
    t_id = message.text.strip()
    if t_id in users:
        u = users[t_id]
        role = "أدمن مالك" if int(t_id) == ADMIN_PRIMARY else ("أدمن مدير" if u.get("is_admin", False) else "مستخدم عادي")
        ban_status = "محظور نهائي ⛔" if u.get("banned", False) else ("محظور مؤقت 🔴" if u.get("banned_until") else "نشط 🟢")
        
        msg = f"👥 <b>بيانات العضو المستعلم عنه:</b>\n\n• ID: <code>{t_id}</code>\n• Username: @{u['username']}\n• الرصيد الحالي: {u['points']} نقطة\n• الرتبة الحالية: {role}\n• حالة الحظر: {ban_status}"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        if u.get("is_admin", False): markup.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"adm_demote_{t_id}"))
        else: markup.add(types.InlineKeyboardButton("🛡️ ترقية إلى أدمن", callback_data=f"adm_promote_{t_id}"))
            
        markup.add(
            types.InlineKeyboardButton("⛔ حظر نهائي", callback_data=f"adm_ban_{t_id}"),
            types.InlineKeyboardButton("⏱️ حظر 24 ساعة", callback_data=f"adm_tempban_{t_id}")
        )
        markup.add(types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"adm_unban_{t_id}"))
        
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")
    else: 
        bot.send_message(message.chat.id, "❌ هذا الآيدي غير مسجل.")

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
        bot.send_message(CHANNEL_USERNAME, marketing_msg, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ تم تأكيد الإجراء ونشر التسويق الوهمي لـ <b>Flourite Cheat ({chosen_plan})</b> بقناتك.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ تعذر النشر بالقناة: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def handle_admin_inline(call):
    uid = str(call.from_user.id)
    if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(uid, {}).get("is_admin", False)):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحيات مسؤول لاستخدام هذا الزر.", show_alert=True)
        
    parts = call.data.split("_")
    action, target_id = parts[1], parts[2]
    
    if target_id not in users: return bot.answer_callback_query(call.id, "❌ لم يتم العثور على هذا العضو.", show_alert=True)
        
    if action == "promote": users[target_id]["is_admin"] = True
    elif action == "demote": users[target_id]["is_admin"] = False
    elif action == "ban": users[target_id]["banned"] = True
    elif action == "tempban": users[target_id]["banned_until"] = (datetime.now() + timedelta(days=1)).isoformat()
    elif action == "unban":
        users[target_id]["banned"] = False
        users[target_id]["banned_until"] = None
        
    save_json(DB_USERS, users)
    bot.answer_callback_query(call.id, "✅ تم تنفيذ الإجراء بنجاح!", show_alert=False)

if __name__ == "__main__":
    print("🚀 تم التشغيل...")
    bot.infinity_polling()
