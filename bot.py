import telebot
from telebot import types
import json
import os
import random
import time
from datetime import datetime, timedelta

# ==========================================
# 1️⃣ الإعدادات الأساسية (بناءً على صورة image.png)
# ==========================================
API_TOKEN = "8868383649:AAEVxFynrH7u_M8e9-wjxo6h8-NP8dtWNUQ"
app_bot = telebot.TeleBot(API_TOKEN)

MAIN_CHANNEL = "Elite_Cyber_Store"
CHANNEL_URL = "https://t.me/Elite_Cyber_Store"
HELP_DESK = "Elite_Support"

MASTER_ID = 111111111  # ضع آيدي المالك الخاص بك هنا
SUB_MASTER_ID = 222222222  # ضع آيدي المساعد هنا (اختياري)

DB_CLIENTS = "clients_database.json"
DB_STOCK = "inventory_keys.json"
DB_COUPONS = "vouchers_data.json"
DB_RATES = "costs_config.json"
DB_SETTINGS = "system_preferences.json"

# ==========================================
# 2️⃣ قاموس اللغات (عربي وانجليزي بنصوص جديدة وجذابة)
# ==========================================
LOCALES = {
    "ar": {
        "locale_name": "العربية 🇸🇦",
        "greeting": "🛡️ <b>أهلاً بك في الخزنة الرقمية للخدمات المميزة!</b> 👋\n\n📝 <b>رقم هويتك:</b> <code>{uid}</code>\n\n💎 نوفر لك هنا أفضل المفاتيح الرقمية مع نظام تسليم آلي فوري وسريع.",
        "must_join": "🚨 <b>تنبيه نظام الحماية!</b>\n\nعزيزي العميل، لاستخدام خدماتنا يجب أن تكون ضمن مجتمعنا الرسمي لدعم استمرار التحديثات.\n\n📌 يرجى الانضمام للقناة ثم النقر على زر التأكيد أدناه:",
        "btn_join_ch": "📡 الانضمام للشبكة الرسمية",
        "btn_verify_ch": "🔄 تأكيد الدخول",
        "not_in_ch": "⚠️ لم يتم رصد انضمامك حتى الآن. يرجى الاشتراك أولاً لتتمكن من العبور.",
        "joined_ok": "✅ اكتمل التوثيق بنجاح! جميع الخدمات ومفاتيح المتجر متاحة لك الآن.",
        "btn_profile": "👤 هويتي",
        "btn_purchase": "🛒 شراء المنتجات 🛍️",
        "btn_voucher": "🎟️ شحن قسيمة 💳",
        "btn_referral": "🤝 كسب النقاط 👥",
        "btn_daily_gift": "🎁 الهدية اليومية ✨",
        "btn_help": "📞 مكتب المساعدة 💬",
        "btn_switch_lang": "🌍 تعديل اللغة 🔄",
        "btn_dashboard": "💻 لوحة القيادة العليا",
        "btn_client_mode": "🔙 العودة كعميل",
        "referral_msg": "🔗 <b>نظام الوكلاء الماسي الخاص بنا!</b>\n\n📌 رابطك الفريد لدعوة الأصدقاء:\n<code>{ref_link}</code>\n\n💸 ستحصل على <b>{reward} رصيد</b> تلقائياً عن كل شخص يسجل من خلالك!",
        "new_referral": "🎉 <b>إشعار جديد!</b> شخص ما انضم عبر رابطك، تمت إضافة <code>+{reward} رصيد</code> لمحفظتك بنجاح!",
        "select_item": "📦 <b>كتالوج المنتجات المتوفرة:</b>\n\nحدد السلعة التي تريد شراء مفتاحها الرقمي:",
        "select_plan": "⏳ <b>حدد خطة الاشتراك المناسبة لـ ({item}):</b>",
        "out_of_stock": "⚠️ نعتذر جداً! المخزون الحالي لهذه السلعة فارغ تماماً حالياً.",
        "purchase_ok": "🛍️ <b>تمت الصفقة بنجاح! شكراً لثقتك.</b>\n\n🔐 مفتاحك الرقمي السري:\n<code>{key}</code>",
        "insufficient_funds": "🛑 <b>رصيد غير كافٍ!</b> التكلفة المطلوبة لإتمام الشراء هي <code>{price} رصيد</code>.",
        "send_voucher": "📥 <b>بوابة شحن القسائم والأكواد:</b>\nيرجى كتابة أو لصق رمز القسيمة هنا:",
        "voucher_ok": "💰 <b>تم الشحن بنجاح!</b> تمت إضافة <code>+{amount} رصيد</code> لملفك الشخصي.",
        "voucher_err": "🚫 عذراً، هذه القسيمة غير صحيحة أو تم استهلاكها مسبقاً.",
        "help_msg": "🛠️ <b>قسم الدعم الفني والمساعدة:</b>\nلأي استفسار تواصل مع وكلائنا عبر الزر أدناه:",
        "lang_prompt": "🌍 <b>تخصيص لغة الواجهة:</b>\nاختر لغتك المفضلة من الخيارات التالية:",
        "lang_set": "✅ تم تحديث تفضيلات اللغة بنجاح.",
        "store_empty": "📭 الرفوف فارغة حالياً في المتجر. انتظر التعبئة قريباً.",
        "btn_contact": "✉️ تواصل مع الوكيل المباشر",
        "gift_ok": "🎊 <b>رائع!</b> لقد استلمت هديتك اليومية وحصلت على: <code>+{amount} رصيد</code>!",
        "gift_wait": "⏳ <b>مهلاً!</b> لقد أخذت هديتك مؤخراً بالفعل. يرجى الانتظار: <code>{time_left}</code> لتطالب بها مجدداً."
    },
    "en": {
        "locale_name": "English 🇺🇸",
        "btn_profile": "👤 My Profile",
        "greeting": "🛡️ <b>Welcome to the Premium Digital Vault!</b> 👋\n\n📝 <b>Your ID:</b> <code>{uid}</code>\n\n💎 The best digital keys with automated instant delivery.",
        "must_join": "🚨 <b>Security Alert!</b>\n\nYou must be part of our community to use this service.\n\n📌 Please join the network and verify below:",
        "btn_join_ch": "📡 Join Official Network",
        "btn_verify_ch": "🔄 Verify Access",
        "not_in_ch": "⚠️ Membership not detected. Please join first.",
        "joined_ok": "✅ Verification complete! Access granted.",
        "btn_purchase": "🛒 Purchase Items 🛍️",
        "btn_voucher": "🎟️ Load Voucher 💳",
        "btn_referral": "🤝 Earn Credits 👥",
        "btn_daily_gift": "🎁 Daily Bonus ✨",
        "btn_help": "📞 Help Desk 💬",
        "btn_switch_lang": "🌍 Switch Locale 🔄",
        "btn_dashboard": "💻 Admin Dashboard",
        "btn_client_mode": "🔙 Client Mode",
        "referral_msg": "🔗 <b>Affiliate System!</b>\n\n📌 Your unique link:\n<code>{ref_link}</code>\n\n💸 Earn <b>{reward} credits</b> per referral!",
        "new_referral": "🎉 <b>Alert!</b> A new user joined via your link. <code>+{reward} credits</code> added!",
        "select_item": "📦 <b>Item Catalog:</b>\n\nSelect a product:",
        "select_plan": "⏳ <b>Select plan for ({item}):</b>",
        "out_of_stock": "⚠️ Apologies! This item is currently out of stock.",
        "purchase_ok": "🛍️ <b>Transaction Successful!</b>\n\n🔐 Your Secret Key:\n<code>{key}</code>",
        "insufficient_funds": "🛑 <b>Insufficient funds!</b> Required: <code>{price} credits</code>.",
        "send_voucher": "📥 <b>Voucher Center:</b>\nSend your voucher code below:",
        "voucher_ok": "💰 <b>Loaded!</b> <code>+{amount} credits</code> applied to your account.",
        "voucher_err": "🚫 Invalid or consumed voucher.",
        "help_msg": "🛠️ <b>Support Center:</b>\nContact our agents below:",
        "lang_prompt": "🌍 <b>Localization:</b>\nSelect your preferred language:",
        "lang_set": "✅ Language preferences updated.",
        "store_empty": "📭 The inventory is currently empty.",
        "btn_contact": "✉️ Contact Agent",
        "gift_ok": "🎊 <b>Awesome!</b> You received <code>+{amount} credits</code>!",
        "gift_wait": "⏳ <b>Hold on!</b> Bonus already claimed. Wait: <code>{time_left}</code>."
    }
}

# ==========================================
# 3️⃣ إدارة قواعد البيانات والملفات
# ==========================================
def fetch_db(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file: return json.load(file)
    return default

def write_db(path, content):
    with open(path, "w", encoding="utf-8") as file: json.dump(content, file, ensure_ascii=False, indent=4)

clients_db = fetch_db(DB_CLIENTS, {})
sys_prefs = fetch_db(DB_SETTINGS, {"invite_bonus": 1.0, "bonus_min": 1, "bonus_max": 10, "is_down": False, "sale_pct": 0})
inventory = fetch_db(DB_STOCK, {})
costs_db = fetch_db(DB_RATES, {})
vouchers_data = fetch_db(DB_COUPONS, {})

def fetch_msg(uid, text_key, **kwargs):
    pref = clients_db.get(str(uid), {}).get("locale", "ar")
    if pref not in LOCALES: pref = "ar"
    return LOCALES[pref].get(text_key, LOCALES["ar"].get(text_key, "N/A")).format(**kwargs)

def check_if_boss(uid):
    if uid == MASTER_ID or uid == SUB_MASTER_ID: return True
    return clients_db.get(str(uid), {}).get("is_boss", False)

def verify_membership(uid):
    try:
        member_info = app_bot.get_chat_member(f"@{MAIN_CHANNEL}", uid)
        return member_info.status in ['member', 'administrator', 'creator']
    except: return True

def register_or_update_client(client_obj):
    c_id = str(client_obj.id)
    if c_id not in clients_db:
        clients_db[c_id] = {
            "funds": 0.0, "tag": client_obj.username or f"G_{client_obj.id}", 
            "invited_by": None, "invite_count": 0, "locale": "ar", 
            "boss_mode": False, "last_bonus": None, "is_boss": False,
            "is_blocked": False, "block_note": ""
        }
        if int(c_id) == MASTER_ID or int(c_id) == SUB_MASTER_ID:
            clients_db[c_id]["is_boss"] = True
        write_db(DB_CLIENTS, clients_db)

# ==========================================
# 4️⃣ بناء الواجهات وقوائم التفاعل
# ==========================================
def client_menu(uid):
    pref = clients_db.get(str(uid), {}).get("locale", "ar")
    ui = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ui.add(types.KeyboardButton(LOCALES[pref]["btn_profile"]))
    ui.add(types.KeyboardButton(LOCALES[pref]["btn_purchase"]), types.KeyboardButton(LOCALES[pref]["btn_voucher"]))
    ui.add(types.KeyboardButton(LOCALES[pref]["btn_referral"]), types.KeyboardButton(LOCALES[pref]["btn_daily_gift"]))
    ui.add(types.KeyboardButton(LOCALES[pref]["btn_help"]), types.KeyboardButton(LOCALES[pref]["btn_switch_lang"]))
    if check_if_boss(uid): ui.add(types.KeyboardButton(LOCALES[pref]["btn_dashboard"]))
    return ui

def boss_menu():
    ui = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ui.add(types.KeyboardButton("➕ إدراج سلعة"), types.KeyboardButton("🗑️ إزالة سلعة"))
    ui.add(types.KeyboardButton("🔐 تخزين مفاتيح"), types.KeyboardButton("📂 فحص المستودع"))
    ui.add(types.KeyboardButton("💵 تسعير السلع"), types.KeyboardButton("🕵️ إدارة العملاء"))
    ui.add(types.KeyboardButton("📉 تفعيل عرض خاص"), types.KeyboardButton("📡 رسالة عامة"))
    ui.add(types.KeyboardButton("📤 بث الأسعار للشبكة"), types.KeyboardButton("🔔 إشعار شراء وهمي"))
    ui.add(types.KeyboardButton("💳 إصدار قسيمة"), types.KeyboardButton("💸 تمويل عميل"))
    ui.add(types.KeyboardButton("🚧 إغلاق للصيانة"), types.KeyboardButton("💾 استخراج البيانات"))
    ui.add(types.KeyboardButton("🔙 واجهة العميل"))
    return ui

def channel_gate_ui(uid):
    ui = types.InlineKeyboardMarkup()
    ui.add(types.InlineKeyboardButton(fetch_msg(uid, "btn_join_ch"), url=CHANNEL_URL))
    ui.add(types.InlineKeyboardButton(fetch_msg(uid, "btn_verify_ch"), callback_data="check_sub_status"))
    return ui

def locale_ui():
    ui = types.InlineKeyboardMarkup()
    for key, data in LOCALES.items(): 
        ui.add(types.InlineKeyboardButton(data["locale_name"], callback_data=f"initlang_{key}"))
    return ui

def client_ctrl_ui(t_id):
    ui = types.InlineKeyboardMarkup()
    t_str = str(t_id)
    blocked = clients_db.get(t_str, {}).get("is_blocked", False)
    boss_status = clients_db.get(t_str, {}).get("is_boss", False)
    
    if blocked: ui.add(types.InlineKeyboardButton("✅ فك القيود", callback_data=f"mbr_unblock_{t_id}"))
    else: ui.add(types.InlineKeyboardButton("⏳ تقييد مؤقت", callback_data=f"mbr_softblock_{t_id}"), types.InlineKeyboardButton("🚫 حظر دائم", callback_data=f"mbr_hardblock_{t_id}"))
    
    if boss_status: ui.add(types.InlineKeyboardButton("🔻 سحب الصلاحيات", callback_data=f"mbr_downgrade_{t_id}"))
    else: ui.add(types.InlineKeyboardButton("🔺 ترقية لوكيل", callback_data=f"mbr_upgrade_{t_id}"))
    return ui

# ==========================================
# 5️⃣ الأوامر البرمجية المباشرة
# ==========================================
@app_bot.message_handler(commands=['id'])
def cmd_id(msg):
    app_bot.reply_to(msg, f"📝 رقم هويتك المسجل: <code>{msg.from_user.id}</code>", parse_mode="HTML")

@app_bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id
    c_id = str(uid)
    register_or_update_client(msg.from_user)
    
    if clients_db[c_id].get("is_blocked", False):
        app_bot.send_message(msg.chat.id, "🛑 <b>أنت ممنوع من دخول الخزنة الرقمية حالياً!</b>", parse_mode="HTML")
        return

    if sys_prefs.get("is_down", False) and not check_if_boss(uid):
        app_bot.send_message(msg.chat.id, "🚧 <b>الأنظمة قيد التحديث والصيانة الشاملة! يرجى العودة لاحقاً.</b>", parse_mode="HTML")
        return
        
    args = msg.text.split()
    if clients_db[c_id]["invited_by"] is None and len(args) > 1:
        inviter = args[1]
        if inviter in clients_db and inviter != c_id:
            clients_db[c_id]["invited_by"] = inviter
            clients_db[inviter]["invite_count"] = clients_db[inviter].get("invite_count", 0) + 1
            write_db(DB_CLIENTS, clients_db)
            
    app_bot.send_message(msg.chat.id, "🌐 Please select your language / يرجى تحديد لغتك الفريدة:", reply_markup=locale_ui())

# ==========================================
# 6️⃣ مراقب النصوص ومعالج الطلبات
# ==========================================
@app_bot.message_handler(func=lambda m: True)
def text_router(msg):
    uid = msg.from_user.id
    c_id = str(uid)
    register_or_update_client(msg.from_user)
    
    if clients_db[c_id].get("is_blocked", False):
        return app_bot.send_message(msg.chat.id, "🛑 <b>تم إيقاف صلاحيات حسابك!</b>", parse_mode="HTML")

    if sys_prefs.get("is_down", False) and not check_if_boss(uid):
        return app_bot.send_message(msg.chat.id, "🚧 <b>النظام مغلق مؤقتاً للصيانة!</b>", parse_mode="HTML")

    if not verify_membership(uid):
        return app_bot.send_message(msg.chat.id, fetch_msg(uid, "must_join"), reply_markup=channel_gate_ui(uid), parse_mode="HTML")

    txt = msg.text

    # --- إدارة شاشات المشرف والأدمن ---
    if check_if_boss(uid):
        if any(kw in txt for kw in ["القيادة", "Dashboard", "admin_mode", "لوحة القيادة العليا"]):
            clients_db[c_id]["boss_mode"] = True
            write_db(DB_CLIENTS, clients_db)
            return app_bot.send_message(msg.chat.id, "💻 <b>تم الاتصال بنجاح مع لوحة القيادة.</b>", reply_markup=boss_menu(), parse_mode="HTML")
            
        if clients_db[c_id].get("boss_mode", False):
            if txt == "➕ إدراج سلعة":
                m = app_bot.send_message(msg.chat.id, "🏷️ أرسل اسم السلعة الجديدة المراد إضافتها:")
                app_bot.register_next_step_handler(m, handle_new_item)
                return
            elif txt == "🗑️ إزالة سلعة":
                if not costs_db: return app_bot.send_message(msg.chat.id, "📭 الكتالوج فارغ تماماً.")
                ui = types.InlineKeyboardMarkup()
                for item in costs_db.keys(): ui.add(types.InlineKeyboardButton(f"❌ مسح {item}", callback_data=f"drop_item_{item}"))
                return app_bot.send_message(msg.chat.id, "🗑️ حدد السلعة المطلوبة للإزالة النهائية:", reply_markup=ui)
            elif txt == "🔐 تخزين مفاتيح":
                if not costs_db: return app_bot.send_message(msg.chat.id, "📭 لا يوجد سلع حالياً لتخزينها.")
                ui = types.InlineKeyboardMarkup()
                for item in costs_db.keys(): ui.add(types.InlineKeyboardButton(f"📦 {item}", callback_data=f"stock_item_{item}"))
                return app_bot.send_message(msg.chat.id, "🔐 اختر السلعة المراد ملء مستودعها بالمفاتيح:", reply_markup=ui)
            elif txt == "📂 فحص المستودع":
                if not costs_db: return app_bot.send_message(msg.chat.id, "📭 لا يوجد سلع متوفرة للفحص.")
                ui = types.InlineKeyboardMarkup()
                for item in costs_db.keys(): ui.add(types.InlineKeyboardButton(f"🔍 {item}", callback_data=f"inspect_item_{item[:20]}"))
                return app_bot.send_message(msg.chat.id, "📂 حدد السلعة المستهدفة لاستعراض مخزونها وتعديله:", reply_markup=ui)
            elif txt == "💵 تسعير السلع":
                if not costs_db: return app_bot.send_message(msg.chat.id, "📭 الكتالوج فارغ حالياً من أي سلع لتسعيرها.")
                ui = types.InlineKeyboardMarkup()
                for item in costs_db.keys(): ui.add(types.InlineKeyboardButton(f"💵 تسعير {item}", callback_data=f"cost_item_{item}"))
                return app_bot.send_message(msg.chat.id, "📝 اختر السلعة المستهدفة لضبط وتعديل تكاليفها:", reply_markup=ui)
            
            elif txt == "📤 بث الأسعار للشبكة":
                if not costs_db: return app_bot.send_message(msg.chat.id, "📭 الكتالوج فارغ تماماً.")
                try:
                    bot_id = app_bot.get_me().username
                    ad_msg = "💎 <b>تحديث مستودع الخزنة الرقمية!</b> 💎\n"
                    ad_msg += "🚀 <b>أفضل المفاتيح بأقل الأسعار الممكنة مع تسليم آلي 100%!</b> 🚀\n\n"
                    ad_msg += "📜 <b>قائمة السلع والخدمات المتوفرة:</b>\n\n"
                    
                    for i, plans in costs_db.items():
                        ad_msg += f"🔥 <b>{i}</b>:\n"
                        for plan, cst in plans.items():
                            ad_msg += f" ├ ⏳ {plan} ━ 💰 <code>{cst}</code> رصيد\n"
                        ad_msg += "\n"
                    
                    ad_msg += "✅ <b>استلام فوري ومضمون بمجرد إتمام الشراء!</b>\n"
                    ad_msg += f"🔗 <b>احجز طلبك الآن وباشر الاستخدام عبر النظام:</b>\n👉 https://t.me/{bot_id}"
                    
                    app_bot.send_message(f"@{MAIN_CHANNEL}", ad_msg, parse_mode="HTML")
                    return app_bot.send_message(msg.chat.id, "✅ تم إرسال وبث نشرة الأسعار للشبكة بنجاح!")
                except Exception:
                    return app_bot.send_message(msg.chat.id, "❌ خطأ في الإرسال. تأكد من ترقية البوت مشرفاً داخل القناة.")
            
            elif txt == "🕵️ إدارة العملاء":
                m = app_bot.send_message(msg.chat.id, "🔎 أرسل رقم هوية العميل (ID) لفتح لوحة التحكم به:")
                app_bot.register_next_step_handler(m, handle_client_lookup)
                return
            elif txt == "💾 استخراج البيانات":
                app_bot.send_message(msg.chat.id, "💾 جاري تجميع وتصدير ملفات النظام وقواعد البيانات...")
                for file_path in [DB_CLIENTS, DB_STOCK, DB_RATES, DB_COUPONS, DB_SETTINGS]:
                    if os.path.exists(file_path): app_bot.send_document(msg.chat.id, open(file_path, "rb"))
                return
            elif txt == "🚧 إغلاق للصيانة":
                sys_prefs["is_down"] = not sys_prefs.get("is_down", False)
                write_db(DB_SETTINGS, sys_prefs)
                st = "🟢 نشط (المتجر مغلق الآن)" if sys_prefs["is_down"] else "🔴 متوقف (المتجر مفتوح للعامة)"
                return app_bot.send_message(msg.chat.id, f"🚧 حالة وضع الصيانة العامة الآن: {st}")
            elif txt == "📉 تفعيل عرض خاص":
                m = app_bot.send_message(msg.chat.id, "📉 اكتب نسبة الخصم المراد تفعيلها بالأرقام (مثال: 15 للخصم 15%) أو 0 للإلغاء:")
                app_bot.register_next_step_handler(m, handle_sale_event)
                return
            elif txt == "🔔 إشعار شراء وهمي":
                if not costs_db: return app_bot.send_message(msg.chat.id, "الكتالوج فارغ لتوليد إشعار.")
                rnd_item = random.choice(list(costs_db.keys()))
                fake_txt = f"🛒 <b>عملية اقتناء ناجحة وجديدة!</b>\n\nقام أحد العملاء بشراء مفتاح لـ <code>{rnd_item}</code> بنجاح! ⚡️\nاحصل على خدماتك الرقمية الفورية الآن من داخل البوت."
                try: app_bot.send_message(f"@{MAIN_CHANNEL}", fake_txt, parse_mode="HTML")
                except: pass
                return app_bot.send_message(msg.chat.id, "✅ تم بث الإشعار الوهمي بنجاح إلى القناة!")
            elif txt == "📡 رسالة عامة":
                m = app_bot.send_message(msg.chat.id, "📝 اكتب نص الإذاعة التي سيتم بثها فوراً لجميع الأعضاء:")
                app_bot.register_next_step_handler(m, handle_mass_broadcast)
                return
            elif txt == "🔙 واجهة العميل":
                clients_db[c_id]["boss_mode"] = False
                write_db(DB_CLIENTS, clients_db)
                return app_bot.send_message(msg.chat.id, "🔙 تم تحويلك للوضع العادي بنجاح.", reply_markup=client_menu(uid))
            elif txt == "💸 تمويل عميل":
                m = app_bot.send_message(msg.chat.id, "✍️ اكتب الـ ID الخاص بالعميل ثم الرصيد مفصولين بمسافة واحدة:")
                app_bot.register_next_step_handler(m, process_fund_transfer)
                return
            elif txt == "💳 إصدار قسيمة":
                m = app_bot.send_message(msg.chat.id, "✍️ اكتب رمز القسيمة المطلوب متبوعاً بقيمتها المالية (بينهما مسافة):")
                app_bot.register_next_step_handler(m, process_create_voucher)
                return

    # --- واجهة العملاء العادية ---
    if "هوية" in txt or "Profile" in txt or "هويتي" in txt:
        app_bot.send_message(msg.chat.id, f"📝 رقم هويتك الشخصية في النظام: <code>{uid}</code>\n💰 رصيدك الحالي: <code>{clients_db[c_id]['funds']}</code> رصيد", parse_mode="HTML")
        
    elif "كسب" in txt or "دعوة" in txt or "Earn" in txt or "Referral" in txt:
        bot_usr = app_bot.get_me().username
        r_link = f"https://t.me/{bot_usr}?start={uid}"
        app_bot.send_message(msg.chat.id, fetch_msg(uid, "referral_msg", ref_link=r_link, reward=sys_prefs.get("invite_bonus", 1.0)), parse_mode="HTML")
        
    elif "الهدية" in txt or "Daily" in txt or "Bonus" in txt:
        handle_daily_claim(msg)
        
    elif "شراء" in txt or "منتجات" in txt or "Purchase" in txt or "Items" in txt:
        if not costs_db: return app_bot.send_message(msg.chat.id, fetch_msg(uid, "store_empty"), parse_mode="HTML")
        ui = types.InlineKeyboardMarkup()
        pct = sys_prefs.get("sale_pct", 0)
        sale_badge = f" 📉 عرض ترويجي بخصم {pct}%!" if pct > 0 else ""
        for item in costs_db.keys(): ui.add(types.InlineKeyboardButton(f"⚡ {item}", callback_data=f"buy_item_{item[:20]}"))
        app_bot.send_message(msg.chat.id, fetch_msg(uid, "select_item") + sale_badge, reply_markup=ui, parse_mode="HTML")
        
    elif "قسيمة" in txt or "Voucher" in txt or "Load" in txt:
        m = app_bot.send_message(msg.chat.id, fetch_msg(uid, "send_voucher"), parse_mode="HTML")
        app_bot.register_next_step_handler(m, handle_redeem_voucher)
        
    elif "المساعدة" in txt or "Help" in txt or "Support" in txt:
        ui = types.InlineKeyboardMarkup()
        ui.add(types.InlineKeyboardButton(fetch_msg(uid, "btn_contact"), url=f"https://t.me/{HELP_DESK}"))
        app_bot.send_message(msg.chat.id, fetch_msg(uid, "help_msg"), reply_markup=ui, parse_mode="HTML")
        
    elif "لغة" in txt or "Language" in txt or "Locale" in txt:
        ui = types.InlineKeyboardMarkup()
        for key, data in LOCALES.items(): ui.add(types.InlineKeyboardButton(data["locale_name"], callback_data=f"set_lang_{key}"))
        app_bot.send_message(msg.chat.id, fetch_msg(uid, "lang_prompt"), reply_markup=ui, parse_mode="HTML")

# ==========================================
# 7️⃣ معالجة الكولباك والأزرار التفاعلية
# ==========================================
@app_bot.callback_query_handler(func=lambda c: True)
def btn_events(call):
    uid = call.from_user.id
    c_id = str(uid)
    
    app_bot.answer_callback_query(call.id)
    if clients_db.get(c_id, {}).get("is_blocked", False): return

    # تم التعديل هنا: عند اختيار اللغة، تظهر لوحة الكيبورد فوراً مع الرسالة الترحيبية
    if call.data.startswith("initlang_") or call.data.startswith("set_lang_"):
        pref = call.data.split("_")[-1]
        clients_db[c_id]["locale"] = pref
        write_db(DB_CLIENTS, clients_db)
        try: app_bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        if not verify_membership(uid): 
            app_bot.send_message(call.message.chat.id, fetch_msg(uid, "must_join"), reply_markup=channel_gate_ui(uid), parse_mode="HTML")
        else: 
            app_bot.send_message(call.message.chat.id, fetch_msg(uid, "greeting", uid=uid), reply_markup=client_menu(uid), parse_mode="HTML")
        return
        
    if call.data == "check_sub_status":
        if verify_membership(uid):
            try: app_bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            app_bot.send_message(call.message.chat.id, fetch_msg(uid, "joined_ok"), parse_mode="HTML")
            app_bot.send_message(call.message.chat.id, fetch_msg(uid, "greeting", uid=uid), reply_markup=client_menu(uid), parse_mode="HTML")
        else:
            app_bot.send_message(call.message.chat.id, fetch_msg(uid, "not_in_ch"), parse_mode="HTML")
        return

    # --- إجراءات لوحة التحكم للمشرفين ---
    if call.data.startswith("mbr_") and check_if_boss(uid):
        cmds = call.data.split("_")
        action, t_id = cmds[1], cmds[2]
        if int(t_id) == MASTER_ID: return
        
        if action in ["hardblock", "softblock"]: clients_db[t_id]["is_blocked"] = True
        elif action == "unblock": clients_db[t_id]["is_blocked"] = False
        elif action == "upgrade": clients_db[t_id]["is_boss"] = True
        elif action == "downgrade": clients_db[t_id]["is_boss"] = False
        
        write_db(DB_CLIENTS, clients_db)
        try: app_bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        app_bot.send_message(call.message.chat.id, f"✅ تم تطبيق التعديل بنظام الحماية للمستخدم <code>{t_id}</code>.", parse_mode="HTML")
        return

    if check_if_boss(uid):
        if call.data.startswith("drop_item_"):
            item = call.data.replace("drop_item_", "")
            if item in costs_db: del costs_db[item]
            if item in inventory: del inventory[item]
            write_db(DB_RATES, costs_db)
            write_db(DB_STOCK, inventory)
            app_bot.edit_message_text(f"✅ تم حذف السلعة ({item}) نهائياً وتصفير مخازنها.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return
            
        elif call.data.startswith("stock_item_"):
            item = call.data.replace("stock_item_", "")
            ui = types.InlineKeyboardMarkup()
            for plan in costs_db.get(item, {}).keys():
                ui.add(types.InlineKeyboardButton(f"➕ تلقيم {plan}", callback_data=f"push_keys_{item[:20]}_{plan[:10]}"))
            app_bot.edit_message_text(f"📦 السلعة: {item}\nحدد المدة المستهدفة لشحن المستودع بالمفاتيح الحصرية:", call.message.chat.id, call.message.message_id, reply_markup=ui, parse_mode="HTML")
            return
            
        elif call.data.startswith("push_keys_"):
            parts = call.data.split("_")
            real_item = next((i for i in costs_db.keys() if i.startswith(parts[2])), None)
            real_plan = next((p for p in costs_db[real_item].keys() if p.startswith(parts[3])), None) if real_item else None
            if real_item and real_plan:
                m = app_bot.send_message(call.message.chat.id, f"📥 الصق الآن الأكواد والمفاتيح لـ ({real_item} - {real_plan})\n⚠️ يرجى جعل كل مفتاح في سطر مستقل لضمان التسليم الدقيق:")
                app_bot.register_next_step_handler(m, store_new_keys, real_item, real_plan)
            return

        elif call.data.startswith("inspect_item_"):
            item_pfx = call.data.replace("inspect_item_", "")
            real_item = next((i for i in costs_db.keys() if i.startswith(item_pfx)), None)
            if not real_item: return
            ui = types.InlineKeyboardMarkup()
            for plan in costs_db.get(real_item, {}).keys():
                ui.add(types.InlineKeyboardButton(f"📂 {plan}", callback_data=f"inspect_time_{real_item[:20]}_{plan[:10]}"))
            app_bot.edit_message_text(f"📦 السلعة: {real_item}\nاختر الفئة الزمنية المحددة للاستكشاف والتحرير المباشر:", call.message.chat.id, call.message.message_id, reply_markup=ui, parse_mode="HTML")
            return

        elif call.data.startswith("inspect_time_"):
            parts = call.data.split("_")
            real_item = next((i for i in costs_db.keys() if i.startswith(parts[2])), None)
            real_plan = next((p for p in costs_db[real_item].keys() if p.startswith(parts[3])), None) if real_item else None
            if real_item and real_plan:
                k_list = inventory.get(real_item, {}).get(real_plan, [])
                if not k_list:
                    return app_bot.edit_message_text(f"📭 لا يوجد أي مفاتيح مخزنة في فرع ({real_item} - {real_plan}).", call.message.chat.id, call.message.message_id)
                
                txt_body = f"🔐 <b>المفاتيح النشطة في المستودع لـ ({real_item} - {real_plan}):</b>\n\n"
                for idx, val in enumerate(k_list):
                    txt_body += f"<b>{idx+1}.</b> <code>{val}</code>\n"
                
                txt_body += "\n🗑️ <i>لشطب كود معين، اكتب الرقم التسلسلي له (مثال: 1).\nلمسح كافة الأكواد دفعة واحدة: اكتب 'تصفير'.\nللخروج الفوري: اكتب 'رجوع'.</i>"
                m = app_bot.send_message(call.message.chat.id, txt_body, parse_mode="HTML")
                app_bot.register_next_step_handler(m, handle_key_removal, real_item, real_plan)
            return
            
        elif call.data.startswith("cost_item_"):
            item = call.data.replace("cost_item_", "")
            ui = types.InlineKeyboardMarkup()
            for plan in costs_db.get(item, {}).keys():
                ui.add(types.InlineKeyboardButton(f"💵 تسعير {plan}", callback_data=f"update_cost_{item[:20]}_{plan[:10]}"))
            app_bot.edit_message_text(f"💵 لوحة تعديل تكاليف: {item}", call.message.chat.id, call.message.message_id, reply_markup=ui, parse_mode="HTML")
            return
            
        elif call.data.startswith("update_cost_"):
            parts = call.data.split("_")
            real_item = next((i for i in costs_db.keys() if i.startswith(parts[2])), None)
            real_plan = next((p for p in costs_db[real_item].keys() if p.startswith(parts[3])), None) if real_item else None
            if real_item and real_plan:
                m = app_bot.send_message(call.message.chat.id, f"💵 اكتب القيمة والتكلفة المالية الجديدة لخطة ({real_plan}) التابعة لمنتج ({real_item}):")
                app_bot.register_next_step_handler(m, store_new_cost, real_item, real_plan)
            return

    # --- بوابة الشراء التلقائي للعميل ---
    if call.data.startswith("buy_item_"):
        i_pfx = call.data.replace("buy_item_", "")
        item = next((i for i in costs_db.keys() if i.startswith(i_pfx)), None)
        if not item: return
        pct = sys_prefs.get("sale_pct", 0)
        ui = types.InlineKeyboardMarkup()
        for plan, base_c in costs_db[item].items():
            net_c = base_c * (1 - (pct / 100))
            btn_lbl = f"⏳ {plan} ({net_c} رصيد)"
            ui.add(types.InlineKeyboardButton(btn_lbl, callback_data=f"buy_time_{item[:20]}_{plan[:10]}"))
        app_bot.edit_message_text(fetch_msg(uid, "select_plan", item=item), call.message.chat.id, call.message.message_id, reply_markup=ui, parse_mode="HTML")

    elif call.data.startswith("buy_time_"):
        parts = call.data.split("_")
        item = next((i for i in costs_db.keys() if i.startswith(parts[2])), None)
        plan = next((p for p in costs_db[item].keys() if p.startswith(parts[3])), None) if item else None
        if not item or not plan: return
        
        base_c = costs_db[item].get(plan, 0)
        pct = sys_prefs.get("sale_pct", 0)
        net_c = base_c * (1 - (pct / 100))
        
        if not inventory.get(item, {}).get(plan):
            app_bot.send_message(call.message.chat.id, fetch_msg(uid, "out_of_stock"), parse_mode="HTML")
        else:
            if clients_db[c_id]["funds"] >= net_c:
                clients_db[c_id]["funds"] -= net_c
                sec_key = inventory[item][plan].pop(0)
                write_db(DB_CLIENTS, clients_db)
                write_db(DB_STOCK, inventory)
                app_bot.send_message(call.message.chat.id, fetch_msg(uid, "purchase_ok", key=sec_key), parse_mode="HTML")
            else:
                app_bot.send_message(call.message.chat.id, fetch_msg(uid, "insufficient_funds", price=net_c), parse_mode="HTML")

# ==========================================
# 8️⃣ دوال المعالجة المتقدمة والوظائف الخلفية
# ==========================================
def handle_key_removal(msg, item, plan):
    val = msg.text.strip()
    if val == "رجوع":
        return app_bot.send_message(msg.chat.id, "✅ تم إلغاء الخطوة بنجاح.")
        
    k_list = inventory.get(item, {}).get(plan, [])
    if val == "تصفير":
        inventory[item][plan] = []
        write_db(DB_STOCK, inventory)
        return app_bot.send_message(msg.chat.id, "🗑️ تم إفراغ المستودع كلياً للقسم المختار.")
        
    try:
        pos = int(val) - 1
        if 0 <= pos < len(k_list):
            rm_key = k_list.pop(pos)
            write_db(DB_STOCK, inventory)
            app_bot.send_message(msg.chat.id, f"✅ تم تدمير وإزالة المفتاح: <code>{rm_key}</code> بنجاح.", parse_mode="HTML")
        else:
            app_bot.send_message(msg.chat.id, "❌ خطأ في تحديد الرقم التسلسلي للمفتاح.")
    except:
        app_bot.send_message(msg.chat.id, "❌ إدخال غير منطقي ومرفوض. تم التراجع التلقائي.")

def handle_client_lookup(msg):
    t_id = msg.text.strip()
    if t_id not in clients_db: return app_bot.send_message(msg.chat.id, "❌ رقم الهوية هذا غير مسجل بأنظمتنا.")
    c_info = clients_db[t_id]
    st = "🚫 مقيد ومحظور" if c_info.get("is_blocked") else "✅ نشط ومسموح"
    lvl = "👑 وكيل إدارة شامل" if c_info.get("is_boss") else "👤 عميل مستهلك"
    info_txt = f"🔎 <b>ملف بيانات العميل:</b>\n\n📝 الرقم التسلسلي: <code>{t_id}</code>\n🏷️ المعرف الرقمي: @{c_info.get('tag', 'بدون')}\n💰 رصيد المحفظة: <code>{c_info['funds']}</code> رصيد\n📌 رتبة الحساب: {lvl}\n🔒 حالة الأمان: {st}"
    app_bot.send_message(msg.chat.id, info_txt, reply_markup=client_ctrl_ui(t_id), parse_mode="HTML")

def handle_sale_event(msg):
    try:
        val = int(msg.text.strip())
        sys_prefs["sale_pct"] = val
        write_db(DB_SETTINGS, sys_prefs)
        app_bot.send_message(msg.chat.id, f"📉 تم تعميم الخصم الترويجي الجديد بنسبة: <code>{val}%</code> لجميع العملاء.", parse_mode="HTML")
    except: app_bot.send_message(msg.chat.id, "❌ قيمة خاطئة، يرجى التعبير بأرقام صحيحة فقط.")

def handle_daily_claim(msg):
    c_id = str(msg.from_user.id)
    now_dt = datetime.now()
    prev_dt_str = clients_db[c_id].get("last_bonus")
    if prev_dt_str:
        prev_dt = datetime.fromisoformat(prev_dt_str)
        if now_dt < prev_dt + timedelta(days=1):
            diff = (prev_dt + timedelta(days=1)) - now_dt
            hh, rem = divmod(diff.seconds, 3600)
            mm, ss = divmod(rem, 60)
            return app_bot.send_message(msg.chat.id, fetch_msg(c_id, "gift_wait", time_left=f"{hh:02d}:{mm:02d}:{ss:02d}"), parse_mode="HTML")
            
    val = random.randint(sys_prefs.get("bonus_min", 1), sys_prefs.get("bonus_max", 10))
    clients_db[c_id]["funds"] += float(val)
    clients_db[c_id]["last_bonus"] = now_dt.isoformat()
    write_db(DB_CLIENTS, clients_db)
    app_bot.send_message(msg.chat.id, fetch_msg(c_id, "gift_ok", amount=val), parse_mode="HTML")

def handle_mass_broadcast(msg):
    app_bot.send_message(msg.chat.id, "📡 جاري إطلاق بث الإشارة...")
    cnt = 0
    for cl_id in clients_db.keys():
        try: 
            app_bot.send_message(int(cl_id), msg.text)
            cnt += 1
            time.sleep(0.04)
        except: pass
    app_bot.send_message(msg.chat.id, f"✅ تم إيصال الإذاعة الإدارية لـ {cnt} عميل مسجل.", parse_mode="HTML")

def handle_new_item(msg):
    i_name = msg.text.strip()
    if i_name and i_name not in costs_db:
        costs_db[i_name] = {"24 Hours": 15.0, "7 Days": 45.0, "30 Days": 120.0}
        inventory[i_name] = {"24 Hours": [], "7 Days": [], "30 Days": []}
        write_db(DB_RATES, costs_db)
        write_db(DB_STOCK, inventory)
        app_bot.send_message(msg.chat.id, f"🎉 السلعة الجديدة ({i_name}) مضافة بنجاح ومتاحة للبيع الفوري.")

def store_new_keys(msg, item, plan):
    lines = msg.text.split('\n')
    cnt = 0
    if item not in inventory: inventory[item] = {}
    if plan not in inventory[item]: inventory[item][plan] = []
    for ln in lines:
        if ln.strip(): 
            inventory[item][plan].append(ln.strip())
            cnt += 1
    write_db(DB_STOCK, inventory)
    app_bot.send_message(msg.chat.id, f"✅ تم بنجاح استيعاب وحفظ {cnt} مفتاح داخل مستودعات الخزنة الرقمية.", parse_mode="HTML")

def store_new_cost(msg, item, plan):
    try:
        costs_db[item][plan] = float(msg.text.strip())
        write_db(DB_RATES, costs_db)
        app_bot.send_message(msg.chat.id, f"✅ تم تحديث وقبول التكلفة الجديدة بنجاح.", parse_mode="HTML")
    except: app_bot.send_message(msg.chat.id, "❌ خطأ برميجي: يرجى التعبير بالأرقام والقيم العددية فقط.")

def handle_redeem_voucher(msg):
    v_code, c_id = msg.text.strip(), str(msg.from_user.id)
    if v_code in vouchers_data:
        val = vouchers_data.pop(v_code)
        clients_db[c_id]["funds"] += float(val)
        write_db(DB_CLIENTS, clients_db)
        write_db(DB_COUPONS, vouchers_data)
        app_bot.send_message(msg.chat.id, fetch_msg(c_id, "voucher_ok", amount=val), parse_mode="HTML")
    else: app_bot.send_message(msg.chat.id, fetch_msg(c_id, "voucher_err"), parse_mode="HTML")

def process_fund_transfer(msg):
    try:
        cl_id, val = msg.text.split()
        if cl_id in clients_db:
            clients_db[cl_id]["funds"] += float(val)
            write_db(DB_CLIENTS, clients_db)
            app_bot.send_message(msg.chat.id, f"✅ تم إيداع الرصيد التمويلي المباشر بنجاح للمستهلك.")
        else: app_bot.send_message(msg.chat.id, "❌ رقم هوية العميل المدخل غير موجود.")
    except: app_bot.send_message(msg.chat.id, "❌ خطأ في الصياغة الفنية للطلب.")

def process_create_voucher(msg):
    try:
        v_code, val = msg.text.split()
        vouchers_data[v_code] = float(val)
        write_db(DB_COUPONS, vouchers_data)
        app_bot.send_message(msg.chat.id, f"💳 تم تجهيز وإصدار قسيمة التعبئة الرقمية بنجاح: <code>{v_code}</code>", parse_mode="HTML")
    except: app_bot.send_message(msg.chat.id, "❌ خطأ في الصياغة، تأكد من وضع مسافة بين الرمز والقيمة.")

if __name__ == "__main__":
    print("🤖 خادم البوت متصل الآن ومثبت التوكن المستخرج بنجاح...")
    app_bot.infinity_polling()
