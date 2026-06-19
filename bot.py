import telebot
from telebot import types
import json
import os
import time
import random
import string
from datetime import datetime, timedelta

# 1️⃣ الإعدادات الأساسية والتوكن الخاص بك
API_TOKEN = "8765508457:AAHLzXj9JEMCbnIWfeov39bN75JrRZ9JcfQ"
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

RANKS = {
    "silver":  {"points_needed": 200,   "discount": 0.01},
    "gold":    {"points_needed": 600,   "discount": 0.02},
    "diamond": {"points_needed": 1500,  "discount": 0.03},
    "hero":    {"points_needed": 3500,  "discount": 0.04},
    "master":  {"points_needed": 7000,  "discount": 0.045},
    "legend":  {"points_needed": 12000, "discount": 0.05}
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
        if datetime.now() < datetime.fromisoformat(temp_until): return True
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
            "accumulated_points": 0,
            "completed_quests": []
        }
        save_json(DB_USERS, users)
    else:
        updated = False
        if "accumulated_points" not in users[uid]:
            users[uid]["accumulated_points"] = users[uid].get("points", 0)
            updated = True
        if "completed_quests" not in users[uid]:
            users[uid]["completed_quests"] = []
            updated = True
        if updated: save_json(DB_USERS, users)

def get_rank_key(acc_pts):
    current_key = "default"
    for r_key, r_val in RANKS.items():
        if acc_pts >= r_val["points_needed"]:
            current_key = r_key
    return current_key

def get_localized_rank_name(rank_key, lang):
    names = {
        "ar": {"default": "عضو عادي 🔹", "silver": "🥈 رتبة الفضي", "gold": "🥇 رتبة الذهبي", "diamond": "💎 رتبة الماسي", "hero": "⚡ رتبة الهيرو", "master": "👑 رتبة الماستر", "legend": "🏆 رتبة الأسطورة"},
        "en": {"default": "Regular Member 🔹", "silver": "🥈 Silver Rank", "gold": "🥇 Gold Rank", "diamond": "💎 Diamond Rank", "hero": "⚡ Hero Rank", "master": "👑 Master Rank", "legend": "🏆 Legend Rank"},
        "fr": {"default": "Membre Régulier 🔹", "silver": "🥈 Grade Argent", "gold": "🥇 Grade Or", "diamond": "💎 Grade Diamant", "hero": "⚡ Grade Héros", "master": "👑 Grade Maître", "legend": "🏆 Grade Légende"},
        "vi": {"default": "Thành viên thường 🔹", "silver": "🥈 Hạng Bạc", "gold": "🥇 Hạng Vàng", "diamond": "💎 Hạng Kim Cương", "hero": "⚡ Hạng Anh Hùng", "master": "👑 Hạng Bậc Thầy", "legend": "🏆 Hạng Huyền Thoại"},
        "es": {"default": "Miembro Regular 🔹", "silver": "🥈 Rango Plata", "gold": "🥇 Rango Oro", "diamond": "💎 Rango Diamante", "hero": "⚡ Rango Héroe", "master": "👑 Rango Maestro", "legend": "🏆 Rango Leyenda"}
    }
    return names.get(lang, names["ar"]).get(rank_key, names["ar"]["default"])

def update_user_rank_and_quests(uid):
    uid = str(uid)
    if uid not in users: return
    u = users[uid]
    lang = u.get("lang", "ar")
    acc_pts = u.get("accumulated_points", 0)
    
    current_discount = 0.0
    for r_key, r_val in RANKS.items():
        if acc_pts >= r_val["points_needed"]:
            current_discount = r_val["discount"]
    u["rank_discount"] = current_discount
    
    completed = u.get("completed_quests", [])
    q = bot_config.get("quests")
    
    notifs = {
        "ar": {
            "inv": f"🎉 تهانينا! لقد أنجزت مهمة الدعوات بنجاح:\n👥 دعوة {q['invite']['target']} صديق\n🎁 تم إضافة مكافأتك: <b>+{q['invite']['reward']} نقطة!</b>",
            "buy": f"🎉 تهانينا! لقد أنجزت مهمة المشتريات بنجاح:\n🛒 إتمام {q['buy']['target']} عمليات شراء\n🎁 تم إضافة مكافأتك: <b>+{q['buy']['reward']} نقطة!</b>",
            "pts": f"🎉 تهانينا! لقد أنجزت مهمة النقاط التراكمية بنجاح:\n💎 تجميع {q['points']['target']} نقطة\n🎁 تم إضافة مكافأتك: <b>+{q['points']['reward']} نقطة!</b>"
        },
        "en": {
            "inv": f"🎉 Congratulations! You have successfully completed the referral quest:\n👥 Invited {q['invite']['target']} friends\n🎁 Your reward has been added: <b>+{q['invite']['reward']} points!</b>",
            "buy": f"🎉 Congratulations! You have successfully completed the purchase quest:\n🛒 Completed {q['buy']['target']} purchases\n🎁 Your reward has been added: <b>+{q['buy']['reward']} points!</b>",
            "pts": f"🎉 Congratulations! You have successfully completed the points quest:\n💎 Accumulated {q['points']['target']} points\n🎁 Your reward has been added: <b>+{q['points']['reward']} points!</b>"
        },
        "fr": {
            "inv": f"🎉 Félicitations ! Vous avez terminé la quête de parrainage :\n👥 {q['invite']['target']} amis invités\n🎁 Votre récompense : <b>+{q['invite']['reward']} points !</b>",
            "buy": f"🎉 Félicitations ! Vous avez terminé la quête d'achat :\n🛒 {q['buy']['target']} achats effectués\n🎁 Votre récompense : <b>+{q['buy']['reward']} points !</b>",
            "pts": f"🎉 Félicitations ! Vous avez terminé la quête de points :\n💎 {q['points']['target']} points accumulés\n🎁 Votre récompense : <b>+{q['points']['reward']} points !</b>"
        },
        "vi": {
            "inv": f"🎉 Chúc mừng! Bạn đã hoàn thành nhiệm vụ giới thiệu:\n👥 Đã mời {q['invite']['target']} người bạn\n🎁 Phần thưởng của bạn: <b>+{q['invite']['reward']} điểm!</b>",
            "buy": f"🎉 Chúc mừng! Bạn đã hoàn thành nhiệm vụ mua hàng:\n🛒 Đã mua {q['buy']['target']} lần thành công\n🎁 Phần thưởng của bạn: <b>+{q['buy']['reward']} điểm!</b>",
            "pts": f"🎉 Chúc mừng! Bạn đã hoàn thành nhiệm vụ tích lũy điểm:\n💎 Đã tích lũy {q['points']['target']} điểm\n🎁 Phần thưởng của bạn: <b>+{q['points']['reward']} điểm!</b>"
        },
        "es": {
            "inv": f"🎉 ¡Felicitaciones! Has completado la misión de referidos:\n👥 Invitaste a {q['invite']['target']} amigos\n🎁 Tu premio: <b>+{q['invite']['reward']} puntos!</b>",
            "buy": f"🎉 ¡Felicitaciones! Has completado la misión de compras:\n🛒 Realizaste {q['buy']['target']} compras\n🎁 Tu premio: <b>+{q['buy']['reward']} puntos!</b>",
            "pts": f"🎉 ¡Felicitaciones! Has completado la misión de puntos:\n💎 Acumulaste {q['points']['target']} puntos\n🎁 Tu premio: <b>+{q['points']['reward']} puntos!</b>"
        }
    }

    if "quest_invite" not in completed and u.get("invite_count", 0) >= q["invite"]["target"]:
        completed.append("quest_invite")
        u["points"] += q["invite"]["reward"]
        u["accumulated_points"] += q["invite"]["reward"]
        try: bot.send_message(int(uid), notifs[lang]["inv"], parse_mode="HTML")
        except: pass
        
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    if "quest_buy" not in completed and user_buys >= q["buy"]["target"]:
        completed.append("quest_buy")
        u["points"] += q["buy"]["reward"]
        u["accumulated_points"] += q["buy"]["reward"]
        try: bot.send_message(int(uid), notifs[lang]["buy"], parse_mode="HTML")
        except: pass
        
    if "quest_points" not in completed and acc_pts >= q["points"]["target"]:
        completed.append("quest_points")
        u["points"] += q["points"]["reward"]
        u["accumulated_points"] += q["points"]["reward"]
        try: bot.send_message(int(uid), notifs[lang]["pts"], parse_mode="HTML")
        except: pass
        
    u["completed_quests"] = completed
    save_json(DB_USERS, users)

# 🌍 القاموس اللغوي الشامل والموسع لكل اللغات المضافة بالكامل لقسم المستخدمين
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
        "maint_msg": "🛠️ وضع الصيانة مفعل حالياً، نعتذر عن الإزعاج.",
        "next_btn": "التالي ➡️",
        "prev_btn": "⬅️ السابق",
        "lootbox_btn": "🎰 صندوق الحظ",
        "wheel_btn": "🎡 عجلة الحظ",
        "quests_btn": "🔥 المهام الصعبة",
        "rank_btn": "🏆 رتبتي الحالية",
        "banned_err": "❌ نعتذر، حسابك محظور حالياً.",
        "id_msg": "🆔 الآيدي الخاص بك هو: <code>{}</code>",
        "page2_welcome": "🎡 ميزات التسلية والمهام التسويقية الإبداعية المضافة حديثاً للمتجر:",
        "lootbox_msg": "🎰 <b>صناديق الحظ العشوائية (Loot Boxes):</b>\n\nقم بفتح صندوق حظ عشوائي الآن وجرب مغامرة الحظ الحقيقية لتكسب مئات النقاط الفورية!\n\n💸 سعر فتح الصندوق: <b>{} نقطة</b>\n📈 نسبة الفوز المقرنة: <b>{}%</b>\n\n🎁 الجائزة الكبرى المخبأة: <b>شحن عشوائي فوري من +100 إلى +500 نقطة!</b>",
        "lootbox_buy_btn": "🛒 فتح صندوق حظ الآن",
        "wheel_msg": "🎡 <b>عجلة الحظ المدفوعة التفاعلية:</b>\n\nأدر العجلة الآن وشاهد حظك وهو يتحرك مباشرة أمامك للربح!\n\n💸 سعر تدوير اللفة: <b>{} نقطة</b>\n🎁 الجوائز المتاحة بالعجلة: 0 Pts | 10 Pts | 20 Pts | مساوي سعر اللفة | 🏆 <b>الجائزة الكبرى (+1000 نقطة كاملة)</b>",
        "wheel_spin_btn": "💫 تدوير عجلة الحظ الآن",
        "no_prod": "📭 لا توجد منتجات متوفرة بالمتجر حالياً.",
        "insufficient": "❌ عذراً! رصيد نقاطك الحالي غير كافٍ.",
        "out_of_stock": "⚠️ نعتذر منك! نفذت كمية مفاتيح هذه الخطة من المخزن.",
        "bonus_claimed": "❌ لقد استلمت المكافأة اليومية بالفعل، يرجى المحاولة بعد انتهاء 24 ساعة.",
        "bonus_success": "✨ تم استلام مكافأتك اليومية بنجاح وهي +{} نقاط!",
        "redeem_prompt": "🎁 الرجاء إدخال كود الشحن لإضافة الرصيد تلقائياً:",
        "redeem_ok": "🎉 تم تفعيل كود الشحن وإضافة +{} نقطة إلى رصيدك.",
        "redeem_fail": "❌ كود الشحن المدخل غير صحيح أو مستعمل مسبقاً.",
        "support_prompt_confirm": "⚠️ <b>تأكيد فتح تذكرة:</b>\nهل أنت متأكد من رغبتك في فتح تذكرة دعم فني جديدة؟",
        "support_yes": "✅ نعم، فتح تذكرة",
        "support_cancel": "❌ إلغاء",
        "support_write": "💬 اكتب رسالة الدعم الفني الخاصة بك الآن لفتح تذكرة:",
        "support_done": "✅ <b>تم العملية بنجاح!</b>\n• الرقم المرجعي للطلب: <code>#{}</code>\n• انتظر الرد قريباً هنا.",
        "req_prompt": "💡 من فضلك اكتب اسم وتفاصيل المنتج الذي ترغب في إضافته للمتجر بالتفصيل:",
        "req_confirm": "⚠️ <b>تأكيد طلب إضافة منتج:</b>\nهل أنت متأكد من رغبتك في إرسال هذا الاقتراح إلى إدارة المتجر؟\n\n📦 <b>تفاصيل المنتج:</b>\n<code>{}</code>",
        "req_btn": "✅ تأكيد وإرسال الطلب",
        "empty_err": "❌ لا يمكن إرسال رسالة فارغة.",
        "cancel_ok": "❌ تم إلغاء العملية بنجاح.",
        "shop_title": "📦 المنتج المختار: <b>{}</b>\nرتبتك الحالية تمنحك خصماً إضافياً بمقدار: {}%\nاختر مدة الاشتراك الشراء التلقائي:",
        "buy_success_msg": "🎉 تم الشراء بنجاح!\n📦 المنتج: <b>{prod}</b>\n⏱️ الخطة: {plan}\n💸 السعر: {price} نقطة\n🔑 المفتاح الخاص بك هو:\n<code>{key}</code>",
        "rank_msg_text": "🏆 <b>نظام ترقية الرتب التلقائي:</b>\n\n• رتبتك الحالية: <b>{r_name}</b>\n• نسبة خصم الرتبة الثابت لك: <b>{r_disc}%</b>\n• مجموع نقاطك التراكمية: <code>{acc_pts}</code> نقطة"
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
        "maint_msg": "🛠️ Maintenance mode is currently active.",
        "next_btn": "Next ➡️",
        "prev_btn": "⬅️ Previous",
        "lootbox_btn": "🎰 Lucky Box",
        "wheel_btn": "🎡 Lucky Wheel",
        "quests_btn": "🔥 Quests & Tasks",
        "rank_btn": "🏆 My Current Rank",
        "banned_err": "❌ Sorry, your account is currently banned.",
        "id_msg": "🆔 Your ID is: <code>{}</code>",
        "page2_welcome": "🎡 Newly added entertainment features and creative marketing tasks:",
        "lootbox_msg": "🎰 <b>Random Lucky Boxes (Loot Boxes):</b>\n\nOpen a lucky box now and win hundreds of instant points!\n\n💸 Box Price: <b>{} points</b>\n📈 Winning Chance: <b>{}%</b>\n\n🎁 Hidden Grand Prize: <b>Instant random reward from +100 to +500 points!</b>",
        "lootbox_buy_btn": "🛒 Open a Lucky Box Now",
        "wheel_msg": "🎡 <b>Interactive Lucky Wheel:</b>\n\nSpin the wheel now and test your luck to win real instant points!\n\n💸 Spin Price: <b>{} points</b>\n🎁 Available Prizes: 0 Pts | 10 Pts | 20 Pts | Spin Price Back | 🏆 <b>Grand Prize (+1000 points)</b>",
        "wheel_spin_btn": "💫 Spin the Wheel Now",
        "no_prod": "📭 No products available in the shop currently.",
        "insufficient": "❌ Sorry! Your current points balance is insufficient.",
        "out_of_stock": "⚠️ Sorry! This plan's keys are out of stock in the inventory.",
        "bonus_claimed": "❌ You have already claimed your daily bonus. Try again after 24 hours.",
        "bonus_success": "✨ Daily bonus claimed successfully! You got +{} points!",
        "redeem_prompt": "🎁 Please enter the redeem code to automatically add points:",
        "redeem_ok": "🎉 Redeem code activated successfully! +{} points added to your balance.",
        "redeem_fail": "❌ The entered redeem code is incorrect or has already been used.",
        "support_prompt_confirm": "⚠️ <b>Confirm Ticket Opening:</b>\nAre you sure you want to open a new support ticket?",
        "support_yes": "✅ Yes, open ticket",
        "support_cancel": "❌ Cancel",
        "support_write": "💬 Write your support message now to open a ticket:",
        "support_done": "✅ <b>Operation completed successfully!</b>\n• Ticket ID: <code>#{}</code>\n• Please wait for admin response.",
        "req_prompt": "💡 Please write the name and details of the product you want to request:",
        "req_confirm": "⚠️ <b>Confirm Product Request:</b>\nAre you sure you want to send this request to management?\n\n📦 <b>Product Details:</b>\n<code>{}</code>",
        "req_btn": "✅ Confirm & Send Request",
        "empty_err": "❌ You cannot send an empty message.",
        "cancel_ok": "❌ Operation cancelled successfully.",
        "shop_title": "📦 Selected Product: <b>{}</b>\nYour rank gives you an extra discount of: {}%\nSelect subscription duration for automated purchase:",
        "buy_success_msg": "🎉 Purchase successful!\n📦 Product: <b>{prod}</b>\n⏱️ Plan: {plan}\n💸 Price: {price} points\n🔑 Your key is:\n<code>{key}</code>",
        "rank_msg_text": "🏆 <b>Automatic Rank System:</b>\n\n• Your Current Rank: <b>{r_name}</b>\n• Permanent Discount: <b>{r_disc}%</b>\n• Total Accumulated Points: <code>{acc_pts}</code> points"
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
        "maint_msg": "🛠️ Le mode maintenance est activé.",
        "next_btn": "Suivant ➡️",
        "prev_btn": "⬅️ Précédent",
        "lootbox_btn": "🎰 Boîte Chance",
        "wheel_btn": "🎡 Roue de la Fortune",
        "quests_btn": "🔥 Quêtes & Défis",
        "rank_btn": "🏆 Mon Grade Actuel",
        "banned_err": "❌ Désolé, votre compte est actuellement banni.",
        "id_msg": "🆔 Votre ID est : <code>{}</code>",
        "page2_welcome": "🎡 Fonctionnalités de divertissement et tâches de marketing créatives récemment ajoutées :",
        "lootbox_msg": "🎰 <b>Boîtes de la Chance Aléatoires (Loot Boxes) :</b>\n\nOuvrez une boîte de la chance maintenant et vivez l'aventure pour gagner des centaines de points !\n\n💸 Prix de la boîte : <b>{} points</b>\n📈 Chance de gagner : <b>{}%</b>\n\n🎁 Grand Prix Caché : <b>Recharge instantanée de +100 à +500 points !</b>",
        "lootbox_buy_btn": "🛒 Ouvrir une boîte maintenant",
        "wheel_msg": "🎡 <b>Roue de la Fortune Interactive :</b>\n\nTournez la roue maintenant et regardez votre chance pour gagner des points instantanés !\n\n💸 Prix du lancer : <b>{} points</b>\n🎁 Prix disponibles : 0 Pts | 10 Pts | 20 Pts | Lancer remboursé | 🏆 <b>Grand Prix (+1000 points)</b>",
        "wheel_spin_btn": "💫 Tourner la roue maintenant",
        "no_prod": "📭 Aucun produit disponible dans la boutique actuellement.",
        "insufficient": "❌ Désolé ! Votre solde de points actuel est insuffisant.",
        "out_of_stock": "⚠️ Désolé ! Les clés de cette formule sont épuisées.",
        "bonus_claimed": "❌ Vous avez déjà récupéré votre bonus quotidien. Réessayez après 24 heures.",
        "bonus_success": "✨ Bonus quotidien récupéré avec succès ! Vous avez +{} points !",
        "redeem_prompt": "🎁 Veuillez saisir le code de recharge pour ajouter des points :",
        "redeem_ok": "🎉 Code activé avec succès ! +{} points ajoutés à votre solde.",
        "redeem_fail": "❌ Le code de recharge entré est incorrect ou déjà utilisé.",
        "support_prompt_confirm": "⚠️ <b>Confirmer l'ouverture du ticket :</b>\nÊtes-vous sûr de vouloir ouvrir un ticket de support ?",
        "support_yes": "✅ Oui, ouvrir un ticket",
        "support_cancel": "❌ Annuler",
        "support_write": "💬 Écrivez votre message d'assistance maintenant pour ouvrir un ticket :",
        "support_done": "✅ <b>Opération réussie !</b>\n• ID Ticket : <code>#{}</code>\n• Veuillez patienter.",
        "req_prompt": "💡 Veuillez écrire le nom et les détails du produit que vous souhaitez demander :",
        "req_confirm": "⚠️ <b>Confirmer la demande de produit :</b>\nÊtes-vous sûr de vouloir envoyer cette suggestion ?\n\n📦 <b>Détails du produit :</b>\n<code>{}</code>",
        "req_btn": "✅ Confirmer & Envoyer",
        "empty_err": "❌ Vous ne pouvez pas envoyer un message vide.",
        "cancel_ok": "❌ Opération annulée avec succès.",
        "shop_title": "📦 Produit Sélectionné : <b>{}</b>\nVotre grade offre une remise de : {}%\nChoisissez la durée de l'achat :",
        "buy_success_msg": "🎉 Achat réussi !\n📦 Produit : <b>{prod}</b>\n⏱️ Formule : {plan}\n💸 Prix : {price} points\n🔑 Votre clé est :\n<code>{key}</code>",
        "rank_msg_text": "🏆 <b>Système de Grade Automatique :</b>\n\n• Votre Grade Actuel : <b>{r_name}</b>\n• Remise Permanente : <b>{r_disc}%</b>\n• Total des Points Accumulés : <code>{acc_pts}</code> points"
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
        "maint_msg": "🛠️ Bot hiện đang được bảo trì.",
        "next_btn": "Tiếp theo ➡️",
        "prev_btn": "⬅️ Quay lại",
        "lootbox_btn": "🎰 Hộp may mắn",
        "wheel_btn": "🎡 Vòng quay may mắn",
        "quests_btn": "🔥 Nhiệm vụ & Thử thách",
        "rank_btn": "🏆 Hạng của tôi",
        "banned_err": "❌ Xin lỗi, tài khoản của bạn hiện đang bị khóa.",
        "id_msg": "🆔 ID của bạn là: <code>{}</code>",
        "page2_welcome": "🎡 Các tính năng giải trí và nhiệm vụ tiếp thị sáng tạo mới được thêm vào:",
        "lootbox_msg": "🎰 <b>Hộp May Mắn Ngẫu Nhiên (Loot Boxes):</b>\n\nMở hộp may mắn ngay bây giờ để nhận hàng trăm điểm ngay lập tức!\n\n💸 Giá mở hộp: <b>{} điểm</b>\n📈 Tỷ lệ trúng thưởng: <b>{}%</b>\n\n🎁 Phần thưởng lớn ẩn giấu: <b>Cộng điểm ngẫu nhiên từ +100 đến +500 điểm!</b>",
        "lootbox_buy_btn": "🛒 Mở hộp may mắn ngay",
        "wheel_msg": "🎡 <b>Vòng Quay May Mắn Tương Tác:</b>\n\nQuay vòng quay ngay để kiểm tra vận may của bạn và giành điểm!\n\n💸 Giá mỗi lượt quay: <b>{} điểm</b>\n🎁 Giải thưởng: 0 Pts | 10 Pts | 20 Pts | Hoàn lại giá quay | 🏆 <b>Giải đặc biệt (+1000 điểm)</b>",
        "wheel_spin_btn": "💫 Quay vòng quay ngay",
        "no_prod": "📭 Hiện tại không có sản phẩm nào trong cửa hàng.",
        "insufficient": "❌ Xin lỗi! Số dư điểm hiện tại của bạn không đủ.",
        "out_of_stock": "⚠️ Xin lỗi! Mã kích hoạt của gói này đã hết hàng.",
        "bonus_claimed": "❌ Bạn đã nhận phần thưởng hôm nay rồi. Vui lòng quay lại sau 24 giờ.",
        "bonus_success": "✨ Nhận phần thưởng hàng ngày thành công! Bạn được +{} điểm!",
        "redeem_prompt": "🎁 Vui lòng nhập mã nạp tiền để tự động cộng điểm:",
        "redeem_ok": "🎉 Kích hoạt mã thành công! Đã cộng +{} điểm vào tài khoản.",
        "redeem_fail": "❌ Mã nạp tiền không chính xác hoặc đã được sử dụng trước đó.",
        "support_prompt_confirm": "⚠️ <b>Xác nhận mở phiếu hỗ trợ:</b>\nBạn có chắc chắn muốn mở một phiếu hỗ trợ kỹ thuật mới không?",
        "support_yes": "✅ Có, mở phiếu",
        "support_cancel": "❌ Hủy bỏ",
        "support_write": "💬 Vui lòng viết nội dung bạn cần hỗ trợ kỹ thuật ngay bây giờ:",
        "support_done": "✅ <b>Thành công!</b>\n• Mã số phiếu: <code>#{}</code>\n• Vui lòng chờ phản hồi.",
        "req_prompt": "💡 Vui lòng viết tên và chi tiết sản phẩm bạn muốn yêu cầu thêm:",
        "req_confirm": "⚠️ <b>Xác nhận yêu cầu sản phẩm:</b>\nBạn có chắc muốn gửi gợi ý này đến ban quản lý không?\n\n📦 <b>Chi tiết sản phẩm:</b>\n<code>{}</code>",
        "req_btn": "✅ Xác nhận & Gửi yêu cầu",
        "empty_err": "❌ Bạn không thể gửi tin nhắn trống.",
        "cancel_ok": "❌ Đã hủy bỏ thao tác thành công.",
        "shop_title": "📦 Sản phẩm đã chọn: <b>{}</b>\nHạng hiện tại giúp bạn được giảm giá thêm: {}%\nChọn thời gian đăng ký để mua:",
        "buy_success_msg": "🎉 Mua hàng thành công!\n📦 Sản phẩm: <b>{prod}</b>\n⏱️ Gói: {plan}\n💸 Giá: {price} điểm\n🔑 Mã của bạn là:\n<code>{key}</code>",
        "rank_msg_text": "🏆 <b>Hệ thống cấp bậc tự động:</b>\n\n• Cấp bậc hiện tại: <b>{r_name}</b>\n• Giảm giá cố định: <b>{r_disc}%</b>\n• Tổng điểm tích lũy: <code>{acc_pts}</code> điểm"
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
        "maint_msg": "🛠️ El modo de mantenimiento está activo actualmente.",
        "next_btn": "Siguiente ➡️",
        "prev_btn": "⬅️ Anterior",
        "lootbox_btn": "🎰 Caja de la Suerte",
        "wheel_btn": "🎡 Ruleta de la Fortuna",
        "quests_btn": "🔥 Misiones & Logros",
        "rank_btn": "🏆 Mi Rango Actual",
        "banned_err": "❌ Lo sentimos, su cuenta está actualmente baneada.",
        "id_msg": "🆔 Su ID es: {}.",
        "page2_welcome": "🎡 Funciones de entretenimiento y tareas de marketing creativo añadidas recientemente:",
        "lootbox_msg": "🎰 <b>Cajas de la Suerte Aleatorias (Loot Boxes):</b>\n\n¡Abre una caja de la suerte ahora y gana cientos de puntos instantáneos!\n\n💸 Precio de la caja: <b>{} puntos</b>\n📈 Probabilidad de ganar: <b>{}%</b>\n\n🎁 Gran Premio Oculto: <b>¡Recarga aleatoria instantánea de +100 a +500 puntos!</b>",
        "lootbox_buy_btn": "🛒 Abrir caja de la suerte ahora",
        "wheel_msg": "🎡 <b>Ruleta de la Fortuna Interactiva:</b>\n\n¡Gira la ruleta ahora y prueba tu suerte para ganar puntos inmediatos!\n\n💸 Precio del giro: <b>{} puntos</b>\n🎁 Premios disponibles: 0 Pts | 10 Pts | 20 Pts | Reembolso del giro | 🏆 <b>Gran Premio (+1000 puntos)</b>",
        "wheel_spin_btn": "💫 Girar la ruleta ahora",
        "no_prod": "📭 No hay productos disponibles en la tienda actualmente.",
        "insufficient": "❌ ¡Lo sentimos! Su saldo de puntos actual es insuficiente.",
        "out_of_stock": "⚠️ ¡Lo sentimos! Las claves de este plan están agotadas.",
        "bonus_claimed": "❌ Ya has reclamado tu bono diario. Inténtalo de nuevo después de 24 horas.",
        "bonus_success": "✨ ¡Bono diario reclamado con éxito! Recibiste +{} puntos!",
        "redeem_prompt": "🎁 Por favor ingrese el código de recarga para añadir puntos automáticamente:",
        "redeem_ok": "🎉 ¡Código activado con éxito! +{} puntos añadidos a tu saldo.",
        "redeem_fail": "❌ El código de recarga ingresado es incorrecto o ya fue usado.",
        "support_prompt_confirm": "⚠️ <b>Confirmar Apertura de Ticket:</b>\n¿Está seguro de que desea abrir un nuevo ticket de soporte?",
        "support_yes": "✅ Sí, abrir ticket",
        "support_cancel": "❌ Cancelar",
        "support_write": "💬 Escriba su mensaje de soporte técnico ahora para abrir un ticket:",
        "support_done": "✅ <b>¡Operación exitosa!</b>\n• ID del Ticket: <code>#{}</code>\n• Por favor espere respuesta.",
        "req_prompt": "💡 Por favor escriba el nombre y detalles del producto que desea solicitar:",
        "req_confirm": "⚠️ <b>Confirmar Solicitud de Producto:</b>\n¿Está seguro de enviar esta sugerencia a la administración?\n\n📦 <b>Detalles del producto:</b>\n<code>{}</code>",
        "req_btn": "✅ Confirmar y Enviar",
        "empty_err": "❌ No puede enviar un mensaje vacío.",
        "cancel_ok": "❌ Operación cancelada con éxito.",
        "shop_title": "📦 Producto Seleccionado: <b>{}</b>\nTu rango te otorga un descuento del: {}%\nElige la duración de suscripción para la compra:",
        "buy_success_msg": "🎉 ¡Compra exitosa!\n📦 Producto: <b>{prod}</b>\n⏱️ Plan: {plan}\n💸 Precio: {price} puntos\n🔑 Su clave es:\n<code>{key}</code>",
        "rank_msg_text": "🏆 <b>Sistema de Rango Automático:</b>\n\n• Su Rango Actual: <b>{r_name}</b>\n• Descuento Permanente: <b>{r_disc}%</b>\n• Total de Puntos Acumulados: <code>{acc_pts}</code> puntos"
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
        markup.add(types.KeyboardButton(t["lang_btn"]), types.KeyboardButton(t["next_btn"]))
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users.get(str(uid), {}).get("is_admin", False):
            markup.add(types.KeyboardButton(t["admin_btn"]))
    else:
        markup.add(types.KeyboardButton(t["lootbox_btn"]), types.KeyboardButton(t["wheel_btn"]))
        markup.add(types.KeyboardButton(t["quests_btn"]), types.KeyboardButton(t["rank_btn"]))
        markup.add(types.KeyboardButton(t["prev_btn"]))
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
    lang = users.get(uid, {}).get("lang", "ar")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["banned_err"])

    if message.text.startswith('/id'):
        if not check_channel_join(uid):
            return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))
        bot.send_message(message.chat.id, LOCALES[lang]["id_msg"].format(uid), parse_mode="HTML")
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
            try:
                inv_lang = users[str(inviter_id)].get("lang", "ar")
                txt_inv = f"🔗 لقد إنضم مستخدم جديد عن طريق رابط الإحالة الخاص بك! حصلت على {bot_config['invite_reward']} نقاط." if inv_lang == "ar" else f"🔗 A new user joined via your link! You received +{bot_config['invite_reward']} points."
                bot.send_message(int(inviter_id), txt_inv)
            except: pass

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    bot.send_message(message.chat.id, LOCALES["ar"]["welcome"], reply_markup=get_lang_inline())

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    lang = users[uid].get("lang", "ar")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["banned_err"])
        
    txt = message.text

    if not check_channel_join(uid):
        return bot.send_message(message.chat.id, LOCALES[lang]["must_join"], reply_markup=get_join_inline(lang))

    if bot_config["maintenance"] and not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, LOCALES[lang]["maint_msg"])

    # 📥 استقبال ردود الدعم الفني وإغلاق التذاكر من الإدارة تلقائياً
    if txt.startswith("الرد|") and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        parts = txt.split("|", 2)
        if len(parts) == 3:
            t_id = parts[1].strip()
            reply_msg = parts[2].strip()
            if t_id in bot_config.get("tickets", {}):
                t_user = bot_config["tickets"][t_id]["uid"]
                bot_config["tickets"][t_id]["status"] = "closed"
                save_json(DB_CONFIG, bot_config)
                try:
                    bot.send_message(int(t_user), f"💬 <b>جاءك رد من الدعم الفني بخصوص تذكرتك #{t_id}:</b>\n\n{reply_msg}", parse_mode="HTML")
                    bot.send_message(message.chat.id, f"✅ تم إرسال الرد بنجاح للعضو وإغلاق التذكرة #{t_id}.")
                except:
                    bot.send_message(message.chat.id, f"⚠️ تم إغلاق التذكرة ولكن تعذر إرسال إشعار للعضو.")
            else:
                bot.send_message(message.chat.id, "❌ رقم التذكرة غير موجود.")
        return

    # 🔄 الانتقال بين الصفحات للمستخدمين
    if txt in (LOCALES[l]["next_btn"] for l in LOCALES):
        return bot.send_message(message.chat.id, LOCALES[lang]["page2_welcome"], reply_markup=get_main_keyboard(uid, lang, page=2))
        
    elif txt in (LOCALES[l]["prev_btn"] for l in LOCALES):
        return bot.send_message(message.chat.id, LOCALES[lang]["main_menu"], reply_markup=get_main_keyboard(uid, lang, page=1))
        
    # 🔄 الانتقال بين الصفحات للمشرفين
    elif txt == "التالي للمشرف ➡️" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, "⚙️ لوحة تحكم إعدادات الألعاب التسويقية الجديدة لمشرفي النظام:", reply_markup=get_admin_keyboard(page=2))
        
    elif txt == "⬅️ سابق المشرف" and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        return bot.send_message(message.chat.id, "👑 لوحة التحكم والميزات الرئيسية للإدارة:", reply_markup=get_admin_keyboard(page=1))

    # 🎰 صندوق الحظ
    elif txt in (LOCALES[l]["lootbox_btn"] for l in LOCALES):
        price = bot_config.get("lootbox_price", 50)
        chance = bot_config.get("lootbox_chance", 25)
        msg = LOCALES[lang]["lootbox_msg"].format(price, chance)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES[lang]["lootbox_buy_btn"], callback_data="game_buy_lootbox"))
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    # 🎡 عجلة الحظ
    elif txt in (LOCALES[l]["wheel_btn"] for l in LOCALES):
        price = bot_config.get("wheel_price", 40)
        msg = LOCALES[lang]["wheel_msg"].format(price)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES[lang]["wheel_spin_btn"], callback_data="game_spin_wheel"))
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

    # 🔥 المهام الصعبة
    elif txt in (LOCALES[l]["quests_btn"] for l in LOCALES):
        update_user_rank_and_quests(uid)
        u = users[uid]
        completed = u.get("completed_quests", [])
        invite_cnt = u.get("invite_count", 0)
        user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
        acc_pts = u.get("accumulated_points", 0)
        q = bot_config.get("quests")
        st_ok = "✅ مكتمل ومستلم" if lang == "ar" else "✅ Completed"
        st_prog = "⏳ قيد التقدم" if lang == "ar" else "⏳ Progress"
        
        msg = "🔥 <b>قائمة المهام والانجازات المتوفرة بالمتجر:</b>\n\n" if lang == "ar" else "🔥 <b>Available Store Quests & Achievements:</b>\n\n"
        st1 = st_ok if "quest_invite" in completed else f"{st_prog} ({invite_cnt}/{q['invite']['target']})"
        msg += f"1️⃣ 👥 دعوة {q['invite']['target']} صديقاً\n🎁 الجائزة: +{q['invite']['reward']} | الحالة: <b>{st1}</b>\n──────────────────\n" if lang == "ar" else f"1️⃣ 👥 Invite {q['invite']['target']} friends\n🎁 Reward: +{q['invite']['reward']} | Status: <b>{st1}</b>\n──────────────────\n"
        st2 = st_ok if "quest_buy" in completed else f"{st_prog} ({user_buys}/{q['buy']['target']})"
        msg += f"2️⃣ 🛒 إتمام {q['buy']['target']} عمليات شراء\n🎁 الجائزة: +{q['buy']['reward']} | الحالة: <b>{st2}</b>\n──────────────────\n" if lang == "ar" else f"2️⃣ 🛒 Complete {q['buy']['target']} purchases\n🎁 Reward: +{q['buy']['reward']} | Status: <b>{st2}</b>\n──────────────────\n"
        st3 = st_ok if "quest_points" in completed else f"{st_prog} ({acc_pts}/{q['points']['target']})"
        msg += f"3️⃣ 💎 تجميع {q['points']['target']} نقطة إجمالاً\n🎁 الجائزة: +{q['points']['reward']} | الحالة: <b>{st3}</b>\n" if lang == "ar" else f"3️⃣ 💎 Accumulate {q['points']['target']} total points\n🎁 Reward: +{q['points']['reward']} | Status: <b>{st3}</b>\n"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    # 🏆 رتبتي الحالية
    elif txt in (LOCALES[l]["rank_btn"] for l in LOCALES):
        update_user_rank_and_quests(uid)
        u = users[uid]
        acc_pts = u.get("accumulated_points", 0)
        rank_key = get_rank_key(acc_pts)
        r_name = get_localized_rank_name(rank_key, lang)
        r_disc = int(u.get("rank_discount", 0.0) * 100)
        msg = LOCALES[lang]["rank_msg_text"].format(r_name=r_name, r_disc=r_disc, acc_pts=acc_pts)
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    # 🆔 إظهار الآيدي
    elif txt in (LOCALES[l]["id_btn"] for l in LOCALES):
        bot.send_message(message.chat.id, LOCALES[lang]["id_msg"].format(uid), parse_mode="HTML")

    # 💰 رصيدي حسابي
    elif txt in (LOCALES[l]["balance_btn"] for l in LOCALES):
        u = users[uid]
        update_user_rank_and_quests(uid)
        rank_key = get_rank_key(u.get("accumulated_points", 0))
        r_name = get_localized_rank_name(rank_key, lang)
        msg = f"💰 <b>بيانات رصيدك وحسابك:</b>\n\n• ID: {uid}\n• رصيد النقاط: {u['points']} نقطة\n• الرتبة الحالية: {r_name}\n• عدد الدعوات الناجحة: {u.get('invite_count', 0)}\n• لغة البوت: {lang.upper()}\n• الحالة: نشط 🟢"
        if lang != "ar":
            msg = f"💰 <b>Your Balance & Account Details:</b>\n\n• ID: {uid}\n• Points Balance: {u['points']} points\n• Current Rank: {r_name}\n• Successful Invites: {u.get('invite_count', 0)}\n• Language: {lang.upper()}\n• Status: Active 🟢"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    # 🌐 تغيير اللغة
    elif txt in (LOCALES[l]["lang_btn"] for l in LOCALES):
        bot.send_message(message.chat.id, LOCALES[lang]["welcome"], reply_markup=get_lang_inline())

    # ✨ المكافأة اليومية
    elif txt in (LOCALES[l]["bonus_btn"] for l in LOCALES):
        now = datetime.now()
        lc = users[uid].get("last_claim")
        if lc and now < datetime.fromisoformat(lc) + timedelta(days=1):
            bot.send_message(message.chat.id, LOCALES[lang]["bonus_claimed"])
        else:
            users[uid]["last_claim"] = now.isoformat()
            users[uid]["points"] += bot_config["daily_bonus"]
            users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + bot_config["daily_bonus"]
            save_json(DB_USERS, users)
            update_user_rank_and_quests(uid)
            bot.send_message(message.chat.id, LOCALES[lang]["bonus_success"].format(bot_config["daily_bonus"]))

    # 🔗 نظام الدعوات
    elif txt in (LOCALES[l]["invite_btn"] for l in LOCALES):
        bot_user = bot.get_me().username
        link = f"https://t.me/{bot_user}?start={uid}"
        msg = f"🔗 <b>نظام الدعوات:</b>\n\nقم بنسخ رابط الإحالة الخاص بك وأرسله لأصدقائك للحصول على نقاط مجانية عند تسجيلهم:\n<code>{link}</code>\n\n🎁 مكافأة الدعوة الحالية: <b>{bot_config['invite_reward']} نقطة</b>"
        if lang != "ar":
            msg = f"🔗 <b>Referral System:</b>\n\nCopy your referral link and send it to your friends to get free points:\n<code>{link}</code>\n\n🎁 Reward: <b>{bot_config['invite_reward']} points</b>"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

    # 🎁 أكواد الشحن
    elif txt in (LOCALES[l]["redeem_btn"] for l in LOCALES):
        m = bot.send_message(message.chat.id, LOCALES[lang]["redeem_prompt"])
        bot.register_next_step_handler(m, process_redeem_user)

    # 💬 الدعم الفني للمستخدم
    elif txt in (LOCALES[l]["support_btn"] for l in LOCALES):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LOCALES[lang]["support_yes"], callback_data="confirm_open_ticket"), types.InlineKeyboardButton(LOCALES[lang]["support_cancel"], callback_data="cancel_action"))
        bot.send_message(message.chat.id, LOCALES[lang]["support_prompt_confirm"], reply_markup=markup, parse_mode="HTML")

    # 💡 طلب منتج جديد
    elif txt in (LOCALES[l]["req_prod_btn"] for l in LOCALES):
        m = bot.send_message(message.chat.id, LOCALES[lang]["req_prompt"])
        bot.register_next_step_handler(m, process_product_request_input)

    # 🛍️ متجر المنتجات
    elif txt in (LOCALES[l]["shop_btn"] for l in LOCALES):
        if not prices_config: return bot.send_message(message.chat.id, LOCALES[lang]["no_prod"])
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys(): markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"select_prod_{prod}"))
        txt_shop = "🛍️ متجر المنتجات:" if lang == "ar" else "🛍️ Product Shop:"
        bot.send_message(message.chat.id, txt_shop, reply_markup=markup, parse_mode="HTML")

    # 👑 فتح لوحة الإدارة
    elif txt in (LOCALES[l]["admin_btn"] for l in LOCALES) and (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)):
        bot.send_message(message.chat.id, "👑 مرحباً بك في لوحة تحكم ميزات الإدارة للمتجر:", reply_markup=get_admin_keyboard(page=1))

    # ==========================================
    # 👑 تنفيذ كامل وظائف وحسابات أزرار الإدارة دون استثناء
    # ==========================================
    elif int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False):
        if txt == "🔄 واجهة المستخدم":
            bot.send_message(message.chat.id, "🔙 تم الانتقال إلى واجهة المستخدم العادية.", reply_markup=get_main_keyboard(uid, lang, page=1))
            
        elif txt == "➕ إضافة منتج":
            m = bot.send_message(message.chat.id, "✍️ أرسل اسم المنتج الجديد بالكامل لإضافته:")
            bot.register_next_step_handler(m, admin_add_product_func)
            
        elif txt == "❌ حذف منتج":
            if not prices_config: return bot.send_message(message.chat.id, "❌ لا توجد منتجات بالمتجر لحذفها.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys(): markup.add(types.InlineKeyboardButton(f"❌ {prod}", callback_data=f"admin_del_prod_confirm|{prod}"))
            bot.send_message(message.chat.id, "👇 اختر المنتج المراد حذفه نهائياً من السيستم:", reply_markup=markup)
            
        elif txt == "🔑 إضافة مفاتيح":
            if not prices_config: return bot.send_message(message.chat.id, "❌ لا توجد منتجات مضافة بعد لملء مخزونها.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys(): markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_addkey_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 اختر المنتج لإضافة مفاتيح داخل مخزونه الخاص:", reply_markup=markup, parse_mode="HTML")
            
        elif txt == "👁️ استعراض المفاتيح":
            msg = "👁️ <b>مخزون المفاتيح المتوفرة حالياً بالسيستم:</b>\n\n"
            if not keys_store: msg += "📭 لا توجد منتجات مضافة في المخازن بعد."
            for prod, plans in keys_store.items():
                msg += f"📦 <b>{prod}:</b>\n"
                for plan, k_list in plans.items():
                    msg += f"  ⏱️ {plan}: <code>{len(k_list)}</code> مفتاح متوفر\n"
                msg += "──────────────────\n"
            bot.send_message(message.chat.id, msg, parse_mode="HTML")
            
        elif txt == "🔢 حذف مفتاح معين":
            m = bot.send_message(message.chat.id, "✍️ أرسل المفتاح الدقيق الذي ترغب في حذفه من مخازن البوت كلياً:")
            bot.register_next_step_handler(m, process_admin_delete_specific_key)
            
        elif txt == "🗑️ مسح جميع المفاتيح":
            for prod in keys_store:
                keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
            save_json(DB_KEYS, keys_store)
            bot.send_message(message.chat.id, "🗑️ تم تصفير وحذف جميع المفاتيح لكافة المنتجات بالكامل بنجاح.")
            
        elif txt == "💵 إدارة الأسعار":
            if not prices_config: return bot.send_message(message.chat.id, "❌ لا توجد منتجات بالمتجر لتعديل أسعارها.")
            markup = types.InlineKeyboardMarkup()
            for prod in prices_config.keys(): markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"step_price_prod|{prod}"))
            bot.send_message(message.chat.id, "👇 اختر المنتج لتعديل أسعاره بالنقاط والاشتراكات:", reply_markup=markup, parse_mode="HTML")
            
        elif txt == "👥 إدارة الأعضاء":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚫 حظر عضو نهائي", callback_data="admin_member_ban"), types.InlineKeyboardButton("🟢 إلغاء حظر عضو", callback_data="admin_member_unban"))
            markup.add(types.InlineKeyboardButton("🔍 فحص تفاصيل حساب عضو", callback_data="admin_member_check"))
            msg = f"👥 <b>قسم إدارة والتحكم بالأعضاء:</b>\n\n• إجمالي الأعضاء المسجلين بالبوت: <code>{len(users)}</code> مستخدم\n\nاختر أحد الخيارات للتحكم في حالة الحسابات والمجموعات:"
            bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")
            
        elif txt == "💰 شحن الأعضاء":
            m = bot.send_message(message.chat.id, "✍️ أرسل الآيدي (ID) الرقمي الخاص بالعضو المراد شحنه وتعديل رصيده:")
            bot.register_next_step_handler(m, process_admin_charge_uid)
            
        elif txt == "🎫 إنشاء أكواد الشحن":
            m = bot.send_message(message.chat.id, "✍️ أرسل كود الشحن الجديد (أو اكتب <code>auto</code> لتوليد كود عشوائي قوي):", parse_mode="HTML")
            bot.register_next_step_handler(m, process_admin_create_redeem_code)
            
        elif txt == "🔥 التخفيضات":
            current_discount = bot_config.get("discount", 0)
            m = bot.send_message(message.chat.id, f"🔥 <b>إدارة التخفيضات العامة للمتجر:</b>\n\n• نسبة التخفيض الحالية: <b>{current_discount}%</b>\n\n✍️ أرسل النسبة المئوية للتخفيض الجديد (رقم من 0 إلى 99):", parse_mode="HTML")
            bot.register_next_step_handler(m, process_admin_set_discount)
            
        elif txt == "📢 الإذاعة الشاملة":
            m = bot.send_message(message.chat.id, "✍️ أرسل نص الرسالة أو المنشور المراد إذاعته لجميع المشتركين بالبوت:")
            bot.register_next_step_handler(m, admin_broadcast_func)
            
        elif txt == "📤 نشر الأسعار بالقناة":  # 📢 ENGLISH VERSION
            if not prices_config: return bot.send_message(message.chat.id, "❌ No products available to publish.")
            msg = "🛍️ <b>OUR OFFICIAL PRICE LIST</b> 🛍️\n\n"
            for prod, plans in prices_config.items():
                msg += f"📦 <b>{prod}</b>\n"
                for plan, price in plans.items():
                    stock_count = len(keys_store.get(prod, {}).get(plan, []))
                    msg += f"  ⏱️ {plan} ➔ <b>{price} Pts</b> [In Stock: {stock_count}]\n"
                msg += "──────────────────\n"
            msg += f"🤖 <b>Buy instantly via our automated Bot:</b> @{bot.get_me().username}\n"
            msg += f"📢 <b>Official Channel:</b> {CHANNEL_LINK}"
            try:
                bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
                bot.send_message(message.chat.id, "✅ Official price list has been posted to your channel in English successfully!")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Failed to publish to channel. Error: {str(e)}")
                
        elif txt == "📣 التسويق الوهمي":  # 📢 ENGLISH FAKE MARKETING ALERT
            if not prices_config: return bot.send_message(message.chat.id, "❌ Add products first to simulate marketing posts.")
            random_prod = random.choice(list(prices_config.keys()))
            random_plan = random.choice(["1 Day", "7 Days", "30 Days"])
            random_price = prices_config[random_prod].get(random_plan, 120)
            fake_user = "@" + "".join(random.choices(string.ascii_lowercase, k=4)) + "***"
            marketing_templates = [
                f"🔥 <b>HOT SALE ALERT! SUCCESSFUL PURCHASE!</b> 🔥\n\n👤 User <b>{fake_user}</b> has just purchased <b>{random_prod}</b> ({random_plan}) for <b>{random_price} Pts</b>! ✅\n\n⚡ Delivery was completely instant via our automated store system! 🤖\n\n🛒 <b>Buy your subscription now:</b> @{bot.get_me().username}",
                f"⚡ <b>AUTOMATED CHECKOUT COMPLETED!</b> ⚡\n\n📦 Product: <b>{random_prod}</b>\n⏱️ Duration: <b>{random_plan}</b>\n💰 Points Paid: <b>{random_price} Pts</b>\n👤 Customer status: <b>{fake_user} [Verified]</b>\n\n🚀 Join the best and fastest digital store now!\n🤖 <b>Shop Bot Link:</b> @{bot.get_me().username}"
            ]
            selected_fake_msg = random.choice(marketing_templates)
            try:
                bot.send_message(CHANNEL_ID, selected_fake_msg, parse_mode="HTML")
                bot.send_message(message.chat.id, "✅ Fake marketing notification has been dispatched to the channel in English!")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Failed to post fake notification. Error: {str(e)}")
                
        elif txt == "✨ تعديل المكافأة اليومية":
            m = bot.send_message(message.chat.id, f"✨ قيمة المكافأة اليومية للمستخدمين حالياً هي: <b>{bot_config.get('daily_bonus', 10)}</b> نقاط.\n✍️ أرسل القيمة الجديدة للمكافأة اليومية بالنقاط:", parse_mode="HTML")
            bot.register_next_step_handler(m, process_admin_edit_daily_bonus)
            
        elif txt == "🔗 تعديل نقاط الدعوة":
            m = bot.send_message(message.chat.id, f"🔗 نقاط مكافأة نظام الإحالة الحالية هي: <b>{bot_config.get('invite_reward', 5)}</b> نقاط.\n✍️ أرسل القيمة الجديدة لنقاط المكافأة لكل دعوة ناجحة:", parse_mode="HTML")
            bot.register_next_step_handler(m, process_admin_edit_invite_reward)
            
        elif txt == "☁️ النسخ الاحتياطي":
            stats = f"📊 <b>إحصائيات وخلفية النظام الشاملة:</b>\n👥 إجمالي المستخدمين: {len(users)}\n🛒 إجمالي مبيعات المتجر التلقائي: {bot_config.get('total_sales', 0)}"
            bot.send_message(message.chat.id, stats, parse_mode="HTML")
            for f_name in [DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
                if os.path.exists(f_name):
                    with open(f_name, "rb") as fd: bot.send_document(message.chat.id, fd)
                    
        elif txt == "🎫 إدارة التذاكر":
            tickets = bot_config.get("tickets", {})
            open_tickets = {tid: tval for tid, tval in tickets.items() if tval.get("status") == "open"}
            if not open_tickets: return bot.send_message(message.chat.id, "🎫 لا توجد تذاكر دعم فني مفتوحة حالياً بالسيستم.")
            msg = "🎫 <b>قائمة تذاكر الدعم الفني المفتوحة المعلقة:</b>\n\n"
            for tid, tval in open_tickets.items():
                msg += f"• التذكرة: <code>#{tid}</code>\n• العضو: <code>{tval.get('uid')}</code>\n• الرسالة: {tval.get('text')}\n──────────────────\n"
            msg += "✍️ للرد على أي تذكرة وإغلاقها تلقائياً، أرسل المنشور كالتالي:\n<code>الرد|رقم_التذكرة|نص الرد الخاص بك</code>"
            bot.send_message(message.chat.id, msg, parse_mode="HTML")
            
        elif txt == "💡 طلبات المنتجات":
            reqs = bot_config.get("product_requests", {})
            if not reqs: return bot.send_message(message.chat.id, "💡 لا توجد تطلعات أو مقترحات منتجات مقدمة من الأعضاء حالياً.")
            msg = "💡 <b>طلبات ومقترحات المنتجات المقدمة من المستخدمين:</b>\n\n"
            for rid, rval in reqs.items():
                msg += f"• معرف المقترح: <code>#{rid}</code>\n• العضو ID: <code>{rval.get('uid')}</code>\n• التفاصيل: <code>{rval.get('text')}</code>\n──────────────────\n"
            bot.send_message(message.chat.id, msg, parse_mode="HTML")
            
        elif txt == "⚙️ إعدادات صندوق الحظ":
            refresh_box_settings(message)
            
        elif txt == "⚙️ إعدادات عجلة الحظ":
            refresh_wheel_settings(message)
            
        elif txt == "⚙️ إعدادات المهام الصعبة":
            refresh_quests_settings(message)

# ==========================================
# ⚙️ دوال الاستجابة والتحديث التلقائي للوحات التحكم الفرعية للإدارة (Page 2)
# ==========================================
def refresh_box_settings(message):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = f"⚙️ <b>لوحة ضبط صندوق الحظ العشوائي:</b>\n\n• السعر الحالي: <b>{price} نقطة</b>\n• نسبة الفوز الحالية: <b>{chance}%</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ سعر أعلى (+5)", callback_data="cfg_box_price_up"), types.InlineKeyboardButton("➖ سعر أقل (-5)", callback_data="cfg_box_price_down"))
    markup.row(types.InlineKeyboardButton("📈 نسبة أعلى (+5%)", callback_data="cfg_box_chance_up"), types.InlineKeyboardButton("📉 نسبة أقل (-5%)", callback_data="cfg_box_chance_down"))
    if isinstance(message, types.CallbackQuery):
        try: bot.edit_message_text(msg, message.message.chat.id, message.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def refresh_wheel_settings(message):
    price = bot_config.get("wheel_price", 40)
    chance = bot_config.get("wheel_chance", 5)
    msg = f"⚙️ <b>لوحة ضبط وتدوير عجلة الحظ المدفوعة:</b>\n\n• السعر الحالي للفة: <b>{price} نقطة</b>\n• نسبة الجائزة الكبرى: <b>{chance}%</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ سعر لفة أعلى (+5)", callback_data="cfg_wheel_price_up"), types.InlineKeyboardButton("➖ سعر لفة أقل (-5)", callback_data="cfg_wheel_price_down"))
    markup.row(types.InlineKeyboardButton("📈 نسبة أعلى (+1%)", callback_data="cfg_wheel_chance_up"), types.InlineKeyboardButton("📉 نسبة أقل (-1%)", callback_data="cfg_wheel_chance_down"))
    if isinstance(message, types.CallbackQuery):
        try: bot.edit_message_text(msg, message.message.chat.id, message.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def refresh_quests_settings(message):
    q = bot_config["quests"]
    msg = f"⚙️ <b>لوحة التحكم الشاملة بالمهام والتحديات الصعبة:</b>\n\n👥 هدف الدعوات: {q['invite']['target']} صديق | الجائزة: {q['invite']['reward']} نقطة\n🛒 هدف عمليات الشراء: {q['buy']['target']} مرات | الجائزة: {q['buy']['reward']} نقطة\n💎 هدف نقاط تراكمية: {q['points']['target']} نقطة | الجائزة: {q['points']['reward']} نقطة"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("👥 هدف دعوات ➖", callback_data="cfg_q_inv_t_down"), types.InlineKeyboardButton("👥 هدف دعوات ➕", callback_data="cfg_q_inv_t_up"))
    markup.row(types.InlineKeyboardButton("🛒 هدف شراء ➖", callback_data="cfg_q_buy_t_down"), types.InlineKeyboardButton("🛒 هدف شراء ➕", callback_data="cfg_q_buy_t_up"))
    markup.row(types.InlineKeyboardButton("💎 هدف نقاط ➖", callback_data="cfg_q_pts_t_down"), types.InlineKeyboardButton("💎 هدف نقاط ➕", callback_data="cfg_q_pts_t_up"))
    if isinstance(message, types.CallbackQuery):
        try: bot.edit_message_text(msg, message.message.chat.id, message.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

# ==========================================
# 🎮 معالجة التفاعلات والأزرار الشفافة بالمتجر (Callback Queries)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    lang = users[uid].get("lang", "ar")
    data = call.data

    if data != "check_join" and not check_channel_join(uid):
        try: bot.answer_callback_query(call.id, LOCALES[lang]["must_join"], show_alert=True)
        except: pass
        return

    # 🎛️ تحديث إعدادات الألعاب والمهام لحظياً من كولباك المشرفين
    if data.startswith("cfg_box_") or data.startswith("cfg_wheel_") or data.startswith("cfg_q_"):
        if not (int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or users[uid].get("is_admin", False)): return
        if data == "cfg_box_price_up": bot_config["lootbox_price"] += 5
        elif data == "cfg_box_price_down": bot_config["lootbox_price"] = max(0, bot_config["lootbox_price"] - 5)
        elif data == "cfg_box_chance_up": bot_config["lootbox_chance"] = min(100, bot_config["lootbox_chance"] + 5)
        elif data == "cfg_box_chance_down": bot_config["lootbox_chance"] = max(0, bot_config["lootbox_chance"] - 5)
        elif data == "cfg_wheel_price_up": bot_config["wheel_price"] += 5
        elif data == "cfg_wheel_price_down": bot_config["wheel_price"] = max(0, bot_config["wheel_price"] - 5)
        elif data == "cfg_wheel_chance_up": bot_config["wheel_chance"] = min(100, bot_config["wheel_chance"] + 1)
        elif data == "cfg_wheel_chance_down": bot_config["wheel_chance"] = max(0, bot_config["wheel_chance"] - 1)
        elif data == "cfg_q_inv_t_up": bot_config["quests"]["invite"]["target"] += 5
        elif data == "cfg_q_inv_t_down": bot_config["quests"]["invite"]["target"] = max(1, bot_config["quests"]["invite"]["target"] - 5)
        elif data == "cfg_q_buy_t_up": bot_config["quests"]["buy"]["target"] += 1
        elif data == "cfg_q_buy_t_down": bot_config["quests"]["buy"]["target"] = max(1, bot_config["quests"]["buy"]["target"] - 1)
        elif data == "cfg_q_pts_t_up": bot_config["quests"]["points"]["target"] += 500
        elif data == "cfg_q_pts_t_down": bot_config["quests"]["points"]["target"] = max(100, bot_config["quests"]["points"]["target"] - 500)
        save_json(DB_CONFIG, bot_config)
        if "box" in data: refresh_box_settings(call)
        elif "wheel" in data: refresh_wheel_settings(call)
        elif "cfg_q_" in data: refresh_quests_settings(call)
        bot.answer_callback_query(call.id, "⚙️ Done!")
        return

    # 👥 إدارة الأعضاء (البان والتحقق)
    elif data == "admin_member_ban":
        m = bot.send_message(call.message.chat.id, "✍️ أرسل الآيدي (ID) الرقمي الخاص بالعضو المراد حظره كلياً:")
        bot.register_next_step_handler(m, process_admin_ban_uid)
    elif data == "admin_member_unban":
        m = bot.send_message(call.message.chat.id, "✍️ أرسل الآيدي (ID) لإلغاء الحظر وتفعيل الحساب مجدداً:")
        bot.register_next_step_handler(m, process_admin_unban_uid)
    elif data == "admin_member_check":
        m = bot.send_message(call.message.chat.id, "✍️ أرسل آيدي (ID) العضو لفحص رصيده وإحصائياته بالتفصيل:")
        bot.register_next_step_handler(m, process_admin_check_uid)

    # ❌ كولباك تأكيد حذف المنتج
    elif data.startswith("admin_del_prod_confirm|"):
        prod = data.split("|")[1]
        if prod in prices_config:
            prices_config.pop(prod, None)
            keys_store.pop(prod, None)
            save_json(DB_PRICES, prices_config)
            save_json(DB_KEYS, keys_store)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, f"✅ تم حذف منتج {prod} وإلغاء مخزنه بالكامل من السيستم.")

    # 🎰 تشغيل ولعب لعبة صندوق الحظ للمستخدمين
    elif data == "game_buy_lootbox":
        price = bot_config.get("lootbox_price", 50)
        if users[uid]["points"] < price:
            return bot.answer_callback_query(call.id, LOCALES[lang]["insufficient"], show_alert=True)
        users[uid]["points"] -= price
        chance = bot_config.get("lootbox_chance", 25)
        if random.randint(1, 100) <= chance:
            win_pts = random.randint(100, 500)
            users[uid]["points"] += win_pts
            users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + win_pts
            save_json(DB_USERS, users)
            txt_win = f"🎰 <b>مبروك الفوز حالفك بنجاح! 🎉🔥</b>\n\n🎁 <b>+{win_pts} نقطة مضافة فوراً لحسابك!</b>" if lang == "ar" else f"🎰 <b>Congratulations, you won! 🎉🔥</b>\n\n🎁 <b>+{win_pts} points added instantly to your account!</b>"
            bot.edit_message_text(txt_win, call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            save_json(DB_USERS, users)
            txt_lose = "🎰 <b>للأسف.. الصندوق كان فارغاً تقريباً 📉 حاول مجدداً!</b>" if lang == "ar" else "🎰 <b>Unfortunately.. the box was empty 📉 Try again!</b>"
            bot.edit_message_text(txt_lose, call.message.chat.id, call.message.message_id, parse_mode="HTML")
        update_user_rank_and_quests(uid)
        return

    # 🎡 تدوير ولعب عجلة الحظ للمتجر
    elif data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if users[uid]["points"] < price:
            return bot.answer_callback_query(call.id, LOCALES[lang]["insufficient"], show_alert=True)
        users[uid]["points"] -= price
        save_json(DB_USERS, users)
        bot.answer_callback_query(call.id, "💫 Spinning...")
        result = random.choice([0, 10, 20, price])
        if result > 0:
            users[uid]["points"] += result
            users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + result
            save_json(DB_USERS, users)
            txt_w = f"🎡 النتيجة: حصلت على <b>+{result} نقطة!</b>" if lang == "ar" else f"🎡 Result: You got <b>+{result} points!</b>"
            bot.edit_message_text(txt_w, call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else:
            txt_l = "🎡 النتيجة: <b>0 نقطة 💔 حظ أوفر في اللفة القادمة!</b>" if lang == "ar" else "🎡 Result: <b>0 points 💔 Better luck next time!</b>"
            bot.edit_message_text(txt_l, call.message.chat.id, call.message.message_id, parse_mode="HTML")
        update_user_rank_and_quests(uid)
        return

    elif data.startswith("step_addkey_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"step_addkey_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 {prod}\n👇 اختر مدة الخطة المحددة للمفتاح لمملئها:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif data.startswith("step_addkey_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"📦 {prod} | ⏱️ {plan}\n\n✍️ أرسل المفاتيح والرموز السريّة الآن (كل مفتاح في سطر منفصل كلياً):", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(m, lambda msg: process_save_new_keys(msg, prod, plan))

    elif data.startswith("step_price_prod|"):
        prod = data.split("|")[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"step_price_plan|{prod}|{plan}"))
        bot.edit_message_text(f"📦 {prod}\n👇 اختر الاشتراك والخطة لتعديل قيمتها وسعرها الفعلي بالنقاط:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif data.startswith("step_price_plan|"):
        _, prod, plan = data.split("|")
        m = bot.edit_message_text(f"📦 {prod} | ⏱️ {plan}\n\n✍️ أرسل السعر الجديد بالنقاط (أرقام فقط):", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(m, lambda msg: process_save_new_price(msg, prod, plan))

    elif data == "confirm_open_ticket":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        m = bot.send_message(call.message.chat.id, LOCALES[lang]["support_write"])
        bot.register_next_step_handler(m, process_support_ticket)

    elif data == "confirm_send_prod_req":
        temp_reqs = bot_config.get("temp_req", {})
        if uid in temp_reqs:
            text = temp_reqs[uid]
            req_id = str(random.randint(10000, 99999))
            if "product_requests" not in bot_config: bot_config["product_requests"] = {}
            bot_config["product_requests"][req_id] = {"uid": uid, "text": text, "date": datetime.now().isoformat()}
            bot_config["temp_req"].pop(uid, None)
            save_json(DB_CONFIG, bot_config)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, LOCALES[lang]["support_done"].format(req_id), parse_mode="HTML")
        return

    elif data == "cancel_action":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, LOCALES[lang]["cancel_ok"])

    elif data.startswith("setlang_"):
        lang_choice = data.split("_")[1]
        users[uid]["lang"] = lang_choice
        save_json(DB_USERS, users)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, LOCALES[lang_choice]["main_menu"], reply_markup=get_main_keyboard(uid, lang_choice, page=1))

    elif data == "check_join":
        if check_channel_join(uid):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            msg_ok = "✅ تم التحقق وتفعيل حسابك بنجاح!" if lang == "ar" else "✅ Account activated successfully!"
            bot.send_message(call.message.chat.id, msg_ok, reply_markup=get_main_keyboard(uid, lang, page=1))
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد!", show_alert=True)

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
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} | {final_p} Pts ({stock_count})", callback_data=f"buy_plan_{prod}_{plan}"))
        bot.edit_message_text(LOCALES[lang]["shop_title"].format(prod, int(u_discount*100)), call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("buy_plan_"):
        parts = data.split("_")
        prod = parts[2]
        plan = parts[3] + " " + parts[4] if len(parts) > 4 else parts[3]
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config["discount"]
        u_discount = users.get(uid, {}).get("rank_discount", 0.0)
        final_p = int(base_p * (1 - disc/100) * (1 - u_discount))
        
        if users[uid]["points"] < final_p:
            return bot.answer_callback_query(call.id, LOCALES[lang]["insufficient"], show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, LOCALES[lang]["out_of_stock"], show_alert=True)
            
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
        bot.edit_message_text(LOCALES[lang]["buy_success_msg"].format(prod=prod, plan=plan, price=final_p, key=delivered_key), call.message.chat.id, call.message.message_id, parse_mode="HTML")

# ==========================================
# 🛠️ الخطوات التابعة لمدخلات لوحة التحكم (Next Step Handlers)
# ==========================================
def process_admin_ban_uid(message):
    target = message.text.strip()
    if target in users:
        users[target]["banned"] = True
        save_json(DB_USERS, users)
        bot.send_message(message.chat.id, f"✅ تم حظر العضو {target} بنجاح ومنعه من استخدام السيستم.")
    else: bot.send_message(message.chat.id, "❌ لم يتم العثور على هذا الآيدي في قاعدة البيانات.")

def process_admin_unban_uid(message):
    target = message.text.strip()
    if target in users:
        users[target]["banned"] = False
        users[target]["banned_until"] = None
        save_json(DB_USERS, users)
        bot.send_message(message.chat.id, f"✅ تم إلغاء حظر العضو {target} بنجاح وإعادة تفعيل حسابه.")
    else: bot.send_message(message.chat.id, "❌ لم يتم العثور على هذا الآيدي في قاعدة البيانات.")

def process_admin_check_uid(message):
    target = message.text.strip()
    if target in users:
        u = users[target]
        status = "محظور 🔴" if u.get("banned") else "نشط 🟢"
        msg = f"🔍 <b>بيانات العضو المطلوب فحصها:</b>\n\n• المعرف: @{u.get('username')}\n• الرصيد الحالي: <code>{u.get('points')}</code> نقطة\n• مجموع النقاط التراكمي: <code>{u.get('accumulated_points', 0)}</code>\n• عدد الإحالات والدعوات: <code>{u.get('invite_count', 0)}</code>\n• اللغة الافتراضية: {u.get('lang', 'ar').upper()}\n• حالة الحساب: <b>{status}</b>"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ هذا العضو غير مسجل في البوت.")

def process_admin_charge_uid(message):
    target_uid = message.text.strip()
    if target_uid not in users: return bot.send_message(message.chat.id, "❌ العضو غير مسجل بالبوت حالياً.")
    m = bot.send_message(message.chat.id, f"👤 العضو المستهدف: @{users[target_uid]['username']}\n✍️ أرسل عدد النقاط لإضافتها لحسابه فواً (أو ضع علامة سالب للخصم منها):")
    bot.register_next_step_handler(m, lambda msg: process_admin_charge_amount(msg, target_uid))

def process_admin_charge_amount(message, target_uid):
    try:
        amount = int(message.text.strip())
        users[target_uid]["points"] += amount
        if amount > 0: users[target_uid]["accumulated_points"] = users[target_uid].get("accumulated_points", 0) + amount
        save_json(DB_USERS, users)
        update_user_rank_and_quests(target_uid)
        bot.send_message(message.chat.id, f"✅ تم تعديل رصيد العضو بنجاح بمقدار: {amount} نقطة.")
        try:
            u_lang = users[target_uid].get("lang", "ar")
            notif = f"💰 تم إضافة +{amount} نقطة إلى حسابك من قبل الإدارة!" if u_lang == "ar" else f"💰 +{amount} points added to your account by admin!"
            bot.send_message(int(target_uid), notif)
        except: pass
    except: bot.send_message(message.chat.id, "❌ خطأ! يرجى إدخال أرقام صحيحة فقط.")

def process_admin_create_redeem_code(message):
    code_input = message.text.strip()
    if code_input.lower() == "auto":
        code_input = "RESELLER-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    m = bot.send_message(message.chat.id, f"🎫 الكود المعتمد: <code>{code_input}</code>\n✍️ أرسل عدد النقاط والجهة المانحة التي يعطيها هذا الكود:", parse_mode="HTML")
    bot.register_next_step_handler(m, lambda msg: process_admin_save_redeem_code(msg, code_input))

def process_admin_save_redeem_code(message, code_input):
    try:
        pts = int(message.text.strip())
        redeem_codes[code_input] = pts
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"✅ تم تكوين وحفظ كود الشحن بنجاح:\n<code>{code_input}</code>\n💸 القيمة: {pts} نقطة.", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ خطأ! أدخل أرقام صحيحة.")

def process_admin_set_discount(message):
    try:
        disc = int(message.text.strip())
        if 0 <= disc < 100:
            bot_config["discount"] = disc
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ تم تحديث نسبة التخفيضات الكلية بالمتجر بنجاح لتصبح: {disc}%")
        else: bot.send_message(message.chat.id, "❌ يرجى إدخال نسبة مئوية صالحة بين 0 و 99.")
    except: bot.send_message(message.chat.id, "❌ يرجى إدخال أرقام فقط.")

def process_admin_delete_specific_key(message):
    target_key = message.text.strip()
    found = False
    for prod, plans in keys_store.items():
        for plan, k_list in plans.items():
            if target_key in k_list:
                k_list.remove(target_key)
                found = True
                break
        if found: break
    if found:
        save_json(DB_KEYS, keys_store)
        bot.send_message(message.chat.id, "✅ تم العثور على المفتاح المستهدف وحذفه تماماً من المخازن.")
    else: bot.send_message(message.chat.id, "❌ هذا المفتاح غير موجود بأي منتج أو خطة اشتراك.")

def process_admin_edit_daily_bonus(message):
    try:
        val = int(message.text.strip())
        if val >= 0:
            bot_config["daily_bonus"] = val
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ تم تحديث قيمة المكافأة اليومية بنجاح لتصبح: {val} نقطة.")
        else: bot.send_message(message.chat.id, "❌ لا يمكن وضع قيمة سالبة للمكافآت.")
    except: bot.send_message(message.chat.id, "❌ يرجى إدخال أرقام صحيحة فقط.")

def process_admin_edit_invite_reward(message):
    try:
        val = int(message.text.strip())
        if val >= 0:
            bot_config["invite_reward"] = val
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ تم تعديل نقاط الدعوة لتصبح: {val} نقطة لكل صديق ينضم.")
        else: bot.send_message(message.chat.id, "❌ لا يمكن وضع قيمة سالبة.")
    except: bot.send_message(message.chat.id, "❌ يرجى إدخال رقم صحيح.")

def process_save_new_keys(message, prod, plan):
    keys = message.text.strip().split('\n')
    added = 0
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ تم حفظ {added} مفتاح ترخيص وتوزيعها بنجاح لـ {prod} خطة {plan}.")

def process_save_new_price(message, prod, plan):
    try:
        new_price = int(message.text.strip())
        prices_config[prod][plan] = new_price
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ تم تحديث سعر {prod} خطة ({plan}) لتصبح {new_price} نقطة.")
    except: bot.send_message(message.chat.id, "❌ خطأ في الإدخال!")

def process_redeem_user(message):
    uid = str(message.from_user.id)
    lang = users[uid].get("lang", "ar")
    code = message.text.strip()
    if code in redeem_codes:
        added_pts = redeem_codes.pop(code)
        users[uid]["points"] += added_pts
        users[uid]["accumulated_points"] = users[uid].get("accumulated_points", 0) + added_pts
        save_json(DB_USERS, users)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id, LOCALES[lang]["redeem_ok"].format(added_pts))
    else: bot.send_message(message.chat.id, LOCALES[lang]["redeem_fail"])

def process_support_ticket(message):
    uid = str(message.from_user.id)
    lang = users[uid].get("lang", "ar")
    u_text = message.text.strip()
    if not u_text: return bot.send_message(message.chat.id, LOCALES[lang]["empty_err"])
    ticket_id = str(random.randint(10000, 99999))
    if "tickets" not in bot_config: bot_config["tickets"] = {}
    bot_config["tickets"][ticket_id] = {"uid": uid, "text": u_text, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, LOCALES[lang]["support_done"].format(ticket_id), parse_mode="HTML")

def process_product_request_input(message):
    uid = str(message.from_user.id)
    lang = users[uid].get("lang", "ar")
    text = message.text.strip()
    if not text: return bot.send_message(message.chat.id, LOCALES[lang]["empty_err"])
    if "temp_req" not in bot_config: bot_config["temp_req"] = {}
    bot_config["temp_req"][uid] = text
    save_json(DB_CONFIG, bot_config)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LOCALES[lang]["req_btn"], callback_data="confirm_send_prod_req"), types.InlineKeyboardButton(LOCALES[lang]["support_cancel"], callback_data="cancel_action"))
    bot.send_message(message.chat.id, LOCALES[lang]["req_confirm"].format(text), reply_markup=markup, parse_mode="HTML")

def admin_add_product_func(message):
    prod = message.text.strip()
    if prod not in prices_config:
        prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
        keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
        save_json(DB_PRICES, prices_config)
        save_json(DB_KEYS, keys_store)
        bot.send_message(message.chat.id, f"➕ تم إنشاء المنتج {prod} بنجاح، وتهيئة خططه في المستودع.")

def admin_broadcast_func(message):
    txt = message.text
    success = 0
    for u_id in users.keys():
        try:
            bot.send_message(int(u_id), txt)
            success += 1
            time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"📢 تم إرسال الإذاعة الشاملة بنجاح وإيصالها لـ {success} عضو.")

if __name__ == "__main__":
    print("🚀 Reseller Store Bot is running flawlessly and fully translated...")
    bot.infinity_polling()
