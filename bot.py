import telebot
from telebot import types
import random, os, time
from datetime import datetime, timedelta

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, LOCALES, RANKS, t
from database import (engine, text, init_db, get_user, update_user_data, register_user,
                      keys_store, redeem_codes, prices_config, bot_config, save_json,
                      DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG, update_user_rank_and_quests)
from utils import (check_spam, is_user_banned, check_channel_join, generate_fake_key,
                   trigger_captcha, is_captcha_pending, verify_captcha, require_verification_on_start)
from keyboards import *

init_db()

def is_admin(uid, u=None):
    if u is None:
        u = get_user(uid) or {}
    return int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)

def get_all_user_ids():
    with engine.connect() as conn:
        return [str(r[0]) for r in conn.execute(text("SELECT uid FROM users")).fetchall()]

def enforce_channel_subscription(message, lang="ar"):
    uid = str(message.from_user.id)
    if not check_channel_join(uid):
        bot.send_message(message.chat.id, 
            t(lang, "must_join") + f"\n\n📢 {CHANNEL_LINK}",
            reply_markup=get_join_inline(lang), parse_mode="HTML")
        return False
    return True

# =====================================================
# /start
# =====================================================
@bot.message_handler(commands=['start', 'id'])
def handle_commands(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, t(lang, "banned"), parse_mode="HTML")

    if message.text.startswith('/id'):
        if not enforce_channel_subscription(message, lang): return
        return bot.send_message(message.chat.id, 
            f"🆔 <code>{uid}</code>\n📝 @{u.get('username', 'N/A')}", parse_mode="HTML")

    # الإحالة
    args = message.text.split()
    if len(args) > 1 and u.get("invited_by") is None:
        inviter_id = args[1]
        if get_user(inviter_id) and inviter_id != uid:
            update_user_data(uid, invited_by=inviter_id)
            reward = bot_config.get("invite_reward", 20)
            update_user_data(inviter_id, points=reward, accumulated_points=reward, invite_count=1)
            update_user_rank_and_quests(inviter_id)
            inv_u = get_user(inviter_id) or {}
            inv_lang = inv_u.get("lang", "ar")
            try:
                bot.send_message(int(inviter_id), t(inv_lang, "invite_reward", reward=reward), parse_mode="HTML")
            except: pass

    if not enforce_channel_subscription(message, lang): return

    if not u.get("verified", False):
        require_verification_on_start(uid)
        return

    # عرض اختيار اللغة إذا لم يختر
    if not u.get("lang_selected", False):
        return bot.send_message(message.chat.id, t("ar", "welcome"), 
            reply_markup=get_lang_inline(), parse_mode="HTML")

    # عرض القائمة الرئيسية
    show_main_menu(message.chat.id, uid, lang)

def show_main_menu(chat_id, uid, lang):
    u = get_user(uid) or {}
    name = u.get("username") or "User"
    bot.send_message(chat_id, 
        t(lang, "main_menu_title", name=name),
        reply_markup=get_main_keyboard(uid, lang), parse_mode="HTML")

# =====================================================
# 🎯 الموجّه الرئيسي (الأزرار الرئيسية فقط - القوائم Inline)
# =====================================================
@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    if check_spam(uid): return
    register_user(message.from_user)
    
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, t(lang, "banned"), parse_mode="HTML")
    
    if is_captcha_pending(uid):
        return bot.send_message(message.chat.id, "🛡️ Solve captcha first!")
        
    txt = message.text.strip() if message.text else ""
    admin_flag = is_admin(uid, u)

    if not enforce_channel_subscription(message, lang): return

    if bot_config.get("maintenance", False) and not admin_flag:
        return bot.send_message(message.chat.id, t(lang, "maint_msg"), parse_mode="HTML")

    # ================================================
    # 🟢 الأزرار الرئيسية (تفتح قوائم Inline)
    # ================================================
    if txt == t(lang, "btn_account"):
        return bot.send_message(message.chat.id, 
            f"{t(lang, 'account_title')}\n\n<i>{t(lang, 'account_desc')}</i>",
            reply_markup=get_account_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_shop"):
        return show_shop(message, uid, u, lang)
    
    if txt == t(lang, "btn_rewards"):
        return bot.send_message(message.chat.id, 
            f"{t(lang, 'rewards_title')}\n\n<i>{t(lang, 'rewards_desc')}</i>",
            reply_markup=get_rewards_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_entertainment"):
        return bot.send_message(message.chat.id, 
            f"{t(lang, 'entertainment_title')}\n\n<i>{t(lang, 'entertainment_desc')}</i>",
            reply_markup=get_entertainment_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_support"):
        return bot.send_message(message.chat.id, 
            f"{t(lang, 'support_title')}\n\n<i>{t(lang, 'support_desc')}</i>",
            reply_markup=get_support_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_settings"):
        return bot.send_message(message.chat.id, 
            f"{t(lang, 'settings_title')}\n\n<i>{t(lang, 'settings_desc')}</i>",
            reply_markup=get_settings_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_admin") and admin_flag:
        return bot.send_message(message.chat.id, 
            "👑 <b>═══ لوحة الإدارة ═══</b>",
            reply_markup=get_admin_keyboard(), parse_mode="HTML")

    # ================================================
    # 🔴 أزرار الأدمن الرئيسية (تفتح قوائم Inline)
    # ================================================
    if admin_flag:
        if txt == "📦 إدارة المنتجات":
            return bot.send_message(message.chat.id, "📦 <b>إدارة المنتجات</b>", 
                reply_markup=admin_products_menu(), parse_mode="HTML")
        
        if txt == "🔑 إدارة المفاتيح":
            return bot.send_message(message.chat.id, "🔑 <b>إدارة المفاتيح</b>", 
                reply_markup=admin_keys_menu(), parse_mode="HTML")
        
        if txt == "👥 إدارة الأعضاء":
            return bot.send_message(message.chat.id, "👥 <b>إدارة الأعضاء</b>", 
                reply_markup=admin_members_menu(), parse_mode="HTML")
        
        if txt == "🎫 إدارة التذاكر":
            return admin_show_tickets(message)
        
        if txt == "💰 المبيعات والأكواد":
            return bot.send_message(message.chat.id, "💰 <b>المبيعات والأكواد</b>", 
                reply_markup=admin_sales_menu(), parse_mode="HTML")
        
        if txt == "📢 التسويق والإذاعة":
            return bot.send_message(message.chat.id, "📢 <b>التسويق والإذاعة</b>", 
                reply_markup=admin_marketing_menu(), parse_mode="HTML")
        
        if txt == "🎮 إعدادات الألعاب":
            return bot.send_message(message.chat.id, "🎮 <b>إعدادات الألعاب</b>", 
                reply_markup=admin_games_menu(), parse_mode="HTML")
        
        if txt == "⚙️ إعدادات النظام":
            return bot.send_message(message.chat.id, "⚙️ <b>إعدادات النظام</b>", 
                reply_markup=admin_system_menu(), parse_mode="HTML")
        
        if txt == "📊 الإحصائيات":
            return admin_show_stats(message)
        
        if txt == "💡 طلبات المنتجات":
            return admin_show_product_requests(message)
        
        if txt == "🔙 العودة للمستخدم":
            return show_main_menu(message.chat.id, uid, lang)

# =====================================================
# 🎨 دوال العرض
# =====================================================
def show_balance(chat_id, msg_id, uid, lang):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    msg = t(lang, "balance_display",
        uid=uid, points=u.get('points', 0),
        rank=u.get('rank', '🔹'),
        discount=int((u.get('rank_discount', 0) or 0)*100),
        invites=u.get('invite_count', 0),
        acc=u.get('accumulated_points', 0))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")

def show_myid(chat_id, msg_id, uid, u, lang):
    msg = f"🆔 <b>═══ Info ═══</b>\n\n👤 ID: <code>{uid}</code>\n📝 @{u.get('username', 'N/A')}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_rank(chat_id, msg_id, uid, lang):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    msg = t(lang, "rank_title",
        rank=u.get('rank', '🔹'),
        disc=int((u.get('rank_discount', 0) or 0)*100),
        acc=u.get('accumulated_points', 0))
    msg += "\n\n"
    for rk in ["silver", "gold", "diamond", "hero", "master", "legend"]:
        r = RANKS[rk]
        name = r["name_ar"] if lang == "ar" else r["name_en"]
        msg += f"{name} - {r['points_needed']} pts ({int(r['discount']*100)}%)\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_referral(chat_id, msg_id, uid, lang):
    try: bot_user = bot.get_me().username
    except: bot_user = "your_bot"
    link = f"https://t.me/{bot_user}?start={uid}"
    u = get_user(uid) or {}
    invites = u.get("invite_count", 0) or 0
    reward = bot_config.get("invite_reward", 20)
    total = invites * reward
    msg = t(lang, "referral_msg", invites=invites, reward=reward, total=total, link=link)
    markup = types.InlineKeyboardMarkup()
    share = f"https://t.me/share/url?url={link}"
    markup.add(types.InlineKeyboardButton("📤 Share", url=share))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_purchases(chat_id, msg_id, uid, lang):
    sales = [x for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid]
    if not sales:
        msg = "📭 No purchases yet"
    else:
        msg = "📜 <b>My Purchases</b>\n\n"
        for s in sales[-10:]:
            msg += f"📦 {s['product']} | ⏱️ {s['plan']}\n💰 {s['price']} pts | 📅 {s.get('date','')[:10]}\n━━━━━━━\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def claim_daily(chat_id, msg_id, uid, lang):
    u = get_user(uid) or {}
    now = datetime.now()
    lc = u.get("last_claim")
    if lc:
        try:
            last = datetime.fromisoformat(lc)
            nxt = last + timedelta(days=1)
            if now < nxt:
                remain = nxt - now
                h = remain.seconds // 3600
                m = (remain.seconds % 3600) // 60
                msg = t(lang, "daily_wait", hours=h, mins=m)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
                try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
                except: pass
                return
        except: pass
    gift = bot_config.get("daily_gift", 10)
    update_user_data(uid, last_claim=now.isoformat())
    update_user_data(uid, points=gift, accumulated_points=gift)
    update_user_rank_and_quests(uid)
    u_new = get_user(uid) or {}
    msg = t(lang, "daily_success", gift=gift, balance=u_new.get('points', 0))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_quests(chat_id, msg_id, uid, lang):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    completed = u.get("completed_quests", "") or ""
    invite_cnt = u.get("invite_count", 0) or 0
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    acc_pts = u.get("accumulated_points", 0) or 0
    q = bot_config.get("quests")
    
    msg = t(lang, "quests_title") + "\n\n"
    
    for i, (key, name, current, target, reward) in enumerate([
        ("quest_invite", "👥 Invites", invite_cnt, q['invite']['target'], q['invite']['reward']),
        ("quest_buy", "🛒 Purchases", user_buys, q['buy']['target'], q['buy']['reward']),
        ("quest_points", "💎 Points", acc_pts, q['points']['target'], q['points']['reward'])
    ], 1):
        if key in completed:
            prog, st = "🟩🟩🟩🟩🟩", "✅"
        else:
            p = min(100, (current / target) * 100) if target > 0 else 0
            filled = int(p / 20)
            prog = "🟩" * filled + "⬜" * (5 - filled)
            st = f"{current}/{target}"
        msg += f"━━━━━━━━━━━\n{i}️⃣ <b>{name}</b>\n🎁 +{reward} pts\n{prog} {st}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_lootbox(chat_id, msg_id, lang):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = (f"🎰 <b>═══ Loot Box ═══</b>\n\n"
           f"💸 Price: <b>{price}</b> pts\n"
           f"📊 Win: <b>{chance}%</b>\n"
           f"🏆 Prize: +100 to +500 pts")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🎁 Open ({price})", callback_data="game_buy_lootbox"))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_wheel(chat_id, msg_id, lang):
    price = bot_config.get("wheel_price", 40)
    msg = (f"🎡 <b>═══ Lucky Wheel ═══</b>\n\n"
           f"💸 Spin: <b>{price}</b> pts\n"
           f"🏆 Grand: <b>+1000 pts</b>")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"💫 Spin ({price})", callback_data="game_spin_wheel"))
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def show_shop(message, uid, u, lang):
    if not prices_config:
        return bot.send_message(message.chat.id, t(lang, "shop_empty"), parse_mode="HTML")
    u_disc = u.get("rank_discount", 0.0) or 0.0
    disc = bot_config.get("discount", 0)
    header = t(lang, "shop_header", points=u.get('points', 0), 
               rank=u.get('rank', '🔹'), disc=int(u_disc*100))
    markup = types.InlineKeyboardMarkup(row_width=1)
    for prod in prices_config.keys():
        stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        emoji = "✅" if stock > 0 else "⚠️"
        markup.add(types.InlineKeyboardButton(f"{emoji} 📦 {prod}  |  📊 {stock}", callback_data=f"select_prod_{prod}"))
    bot.send_message(message.chat.id, header, reply_markup=markup, parse_mode="HTML")

def show_my_tickets(chat_id, msg_id, uid, lang):
    tickets = bot_config.get("tickets", {})
    my_t = {k: v for k, v in tickets.items() if str(v.get("uid")) == uid}
    if not my_t:
        msg = t(lang, "no_tickets")
    else:
        msg = t(lang, "my_tickets_title") + "\n\n"
        for tid, info in my_t.items():
            status = "🟢" if info.get("status", "open") == "open" else "🔴"
            msg += f"{status} #{tid}\n📝 {info['text'][:50]}...\n━━━━━━━\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except: pass

def admin_show_tickets(message):
    tickets = bot_config.get("tickets", {})
    open_t = {k: v for k, v in tickets.items() if v.get("status", "open") == "open"}
    if not open_t:
        return bot.send_message(message.chat.id, "🎉 لا تذاكر مفتوحة.")
    markup = types.InlineKeyboardMarkup()
    for t_id, t_info in open_t.items():
        markup.add(types.InlineKeyboardButton(f"🎫 #{t_id}", callback_data=f"view_ticket_{t_id}"))
    bot.send_message(message.chat.id, "🎫 <b>التذاكر المفتوحة:</b>", reply_markup=markup, parse_mode="HTML")

def admin_show_product_requests(message):
    reqs = bot_config.get("product_requests", {})
    if not reqs:
        return bot.send_message(message.chat.id, "📭 لا طلبات.")
    msg = "💡 <b>طلبات المنتجات:</b>\n\n"
    for r_id, r_info in reqs.items():
        msg += f"🔹 <b>#{r_id}</b>\n👤 {r_info['uid']}\n📦 {r_info['text']}\n━━━━━━\n"
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def admin_show_stats(message):
    stats = (f"📊 <b>═══ الإحصائيات ═══</b>\n\n"
             f"👥 المستخدمين: {len(get_all_user_ids())}\n"
             f"🛒 المبيعات: {bot_config.get('total_sales', 0)}\n"
             f"💰 الأرباح: {bot_config.get('total_earnings', 0)}\n"
             f"🎫 الأكواد: {len(redeem_codes)}\n"
             f"📦 المنتجات: {len(prices_config)}")
    bot.send_message(message.chat.id, stats, parse_mode="HTML")
    for f in [DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
        if os.path.exists(f):
            try:
                with open(f, "rb") as d: bot.send_document(message.chat.id, d)
            except: pass

# =====================================================
# 🔁 معالج Callback الرئيسي
# =====================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    register_user(call.from_user)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # كابتشا
    if data.startswith("captcha_ans_"):
        user_answer = data.split("_", 2)[2]
        result = verify_captcha(uid, user_answer)
        if result == "correct":
            update_user_data(uid, verified=True)
            try: bot.edit_message_text(t(lang, "captcha_correct"), chat_id, msg_id, parse_mode="HTML")
            except: pass
            show_main_menu(chat_id, uid, lang)
        elif result == "wrong":
            bot.answer_callback_query(call.id, t(lang, "captcha_wrong"), show_alert=True)
        elif result == "banned":
            try: bot.edit_message_text(t(lang, "captcha_banned"), chat_id, msg_id, parse_mode="HTML")
            except: pass
        return

    # اللغة
    if data.startswith("setlang_"):
        new_lang = data.split("_")[1]
        update_user_data(uid, lang=new_lang, lang_selected=True)
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        bot.send_message(chat_id, t(new_lang, "lang_changed"), parse_mode="HTML")
        show_main_menu(chat_id, uid, new_lang)
        return

    # التحقق من الاشتراك
    if data == "check_join":
        if check_channel_join(uid):
            try: bot.delete_message(chat_id, msg_id)
            except: pass
            show_main_menu(chat_id, uid, lang)
        else:
            bot.answer_callback_query(call.id, t(lang, "must_join"), show_alert=True)
        return

    # الاشتراك الإجباري لباقي الأزرار
    if not check_channel_join(uid):
        bot.answer_callback_query(call.id, t(lang, "must_join"), show_alert=True)
        return

    # ============ قوائم الأقسام ============
    if data == "back_account":
        try: bot.edit_message_text(
            f"{t(lang, 'account_title')}\n\n<i>{t(lang, 'account_desc')}</i>",
            chat_id, msg_id, reply_markup=get_account_menu(lang), parse_mode="HTML")
        except: pass
        return

    if data == "back_rewards":
        try: bot.edit_message_text(
            f"{t(lang, 'rewards_title')}\n\n<i>{t(lang, 'rewards_desc')}</i>",
            chat_id, msg_id, reply_markup=get_rewards_menu(lang), parse_mode="HTML")
        except: pass
        return

    if data == "back_entertainment":
        try: bot.edit_message_text(
            f"{t(lang, 'entertainment_title')}\n\n<i>{t(lang, 'entertainment_desc')}</i>",
            chat_id, msg_id, reply_markup=get_entertainment_menu(lang), parse_mode="HTML")
        except: pass
        return

    if data == "back_support":
        try: bot.edit_message_text(
            f"{t(lang, 'support_title')}\n\n<i>{t(lang, 'support_desc')}</i>",
            chat_id, msg_id, reply_markup=get_support_menu(lang), parse_mode="HTML")
        except: pass
        return

    # ============ حسابي ============
    if data == "menu_balance": return show_balance(chat_id, msg_id, uid, lang)
    if data == "menu_myid": return show_myid(chat_id, msg_id, uid, u, lang)
    if data == "menu_rank": return show_rank(chat_id, msg_id, uid, lang)
    if data == "menu_referral": return show_referral(chat_id, msg_id, uid, lang)
    if data == "menu_purchases": return show_purchases(chat_id, msg_id, uid, lang)

    # ============ المكافآت ============
    if data == "menu_daily": return claim_daily(chat_id, msg_id, uid, lang)
    if data == "menu_quests": return show_quests(chat_id, msg_id, uid, lang)
    if data == "menu_redeem":
        m = bot.send_message(chat_id, "🎁 " + t(lang, "ticket_write").replace("message", "code"))
        bot.register_next_step_handler(m, process_redeem)
        return

    # ============ الترفيه ============
    if data == "menu_lootbox": return show_lootbox(chat_id, msg_id, lang)
    if data == "menu_wheel": return show_wheel(chat_id, msg_id, lang)

    # ============ الدعم ============
    if data == "menu_open_ticket":
        m = bot.send_message(chat_id, t(lang, "ticket_write"))
        bot.register_next_step_handler(m, process_support_ticket)
        return
    if data == "menu_my_tickets": return show_my_tickets(chat_id, msg_id, uid, lang)
    if data == "menu_request_product":
        m = bot.send_message(chat_id, t(lang, "product_request_write"))
        bot.register_next_step_handler(m, process_product_request)
        return

    # ============ الإعدادات ============
    if data == "menu_lang":
        try: bot.edit_message_text(t(lang, "welcome"), chat_id, msg_id,
            reply_markup=get_lang_inline(), parse_mode="HTML")
        except: pass
        return

    # ============ الألعاب ============
    if data == "game_buy_lootbox":
        price = bot_config.get("lootbox_price", 50)
        if (u.get("points", 0) or 0) < price:
            return bot.answer_callback_query(call.id, t(lang, "insufficient_balance"), show_alert=True)
        update_user_data(uid, points=-price)
        if random.randint(1, 100) <= bot_config.get("lootbox_chance", 25):
            win = random.randint(100, 500)
            update_user_data(uid, points=win, accumulated_points=win)
            msg = f"🎊 <b>WIN!</b>\n\n🎁 <b>+{win}</b> pts"
        else:
            msg = "😔 <b>Empty!</b>\n\n💪 Try again!"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        update_user_rank_and_quests(uid)
        return

    if data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if (u.get("points", 0) or 0) < price:
            return bot.answer_callback_query(call.id, t(lang, "insufficient_balance"), show_alert=True)
        update_user_data(uid, points=-price)
        for f in ["🎰 [🔁]", "🎡 [🔄]", "🎰 [🔁]"]:
            try:
                bot.edit_message_text(f, chat_id, msg_id)
                time.sleep(0.5)
            except: pass
        if random.randint(1, 100) <= bot_config.get("wheel_chance", 5):
            win = 1000
            update_user_data(uid, points=win, accumulated_points=win)
            msg = f"🏆 <b>GRAND PRIZE!</b>\n\n👑 <b>+{win}</b> pts"
            try:
                bot.send_message(CHANNEL_ID, f"🎡 Big win! +{win} pts\n🤖 t.me/{bot.get_me().username}", parse_mode="HTML")
            except: pass
        else:
            result = random.choice([0, 10, 20, price])
            if result > 0:
                update_user_data(uid, points=result, accumulated_points=result)
                msg = f"🎡 <b>+{result} pts</b>"
            else:
                msg = "🎡 <b>0 pts</b> - Try again!"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        update_user_rank_and_quests(uid)
        return

    # ============ المتجر ============
    if data.startswith("select_prod_"):
        prod = data.split("_", 2)[2]
        if prod not in prices_config: return
        u_disc = u.get("rank_discount", 0.0) or 0.0
        info = t(lang, "product_details", prod=prod, disc=int(u_disc*100), points=u.get('points', 0))
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_p = prices_config[prod].get(plan, 0)
            disc = bot_config.get("discount", 0)
            final_p = int(base_p * (1 - disc/100) * (1 - u_disc))
            stock = len(keys_store.get(prod, {}).get(plan, []))
            emoji = "✅" if stock > 0 else "❌"
            markup.add(types.InlineKeyboardButton(f"{emoji} {plan} | {final_p} pts | 📊 {stock}", callback_data=f"buy_plan|{prod}|{plan}"))
        try: bot.edit_message_text(info, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("buy_plan|"):
        _, prod, plan = data.split("|")
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config.get("discount", 0)
        u_disc = u.get("rank_discount", 0.0) or 0.0
        final_p = int(base_p * (1 - disc/100) * (1 - u_disc))
        if (u.get("points", 0) or 0) < final_p:
            return bot.answer_callback_query(call.id, t(lang, "insufficient_balance"), show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, "⚠️ Out of stock!", show_alert=True)
        key = keys_store[prod][plan].pop(0)
        update_user_data(uid, points=-final_p)
        bot_config["total_sales"] = bot_config.get("total_sales", 0) + 1
        bot_config["total_earnings"] = bot_config.get("total_earnings", 0) + final_p
        if "sales_log" not in bot_config: bot_config["sales_log"] = []
        bot_config["sales_log"].append({"uid": uid, "username": u.get("username", ""),
            "product": prod, "plan": plan, "price": final_p, "key": key, "date": datetime.now().isoformat()})
        save_json(DB_KEYS, keys_store)
        save_json(DB_CONFIG, bot_config)
        update_user_rank_and_quests(uid)
        msg = t(lang, "purchase_success", prod=prod, plan=plan, price=final_p, key=key)
        try: bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except: pass
        try:
            bot.send_message(CHANNEL_ID, f"🔥 New sale!\n📦 {prod} | ⏱️ {plan} | 💰 {final_p} pts", parse_mode="HTML")
        except: pass
        return

    # ============ إعدادات الأدمن Inline ============
    if not is_admin(uid, u):
        return

    # المنتجات
    if data == "admp_add":
        m = bot.send_message(chat_id, "➕ اسم المنتج:")
        bot.register_next_step_handler(m, admin_add_product)
        return
    if data == "admp_del":
        m = bot.send_message(chat_id, "❌ اسم المنتج للحذف:")
        bot.register_next_step_handler(m, admin_del_product)
        return
    if data == "admp_prices":
        if not prices_config: return bot.answer_callback_query(call.id, "❌ لا منتجات")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"admprice_{prod}"))
        try: bot.edit_message_text("💵 اختر منتج:", chat_id, msg_id, reply_markup=markup)
        except: pass
        return

    if data.startswith("admprice_"):
        prod = data.split("_", 1)[1]
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            curr = prices_config.get(prod, {}).get(plan, 0)
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} ({curr})", callback_data=f"admpriceset_{prod}|{plan}"))
        try: bot.edit_message_text(f"📦 <b>{prod}</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admpriceset_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        m = bot.send_message(chat_id, f"💵 السعر الجديد لـ {prod}/{plan}:")
        bot.register_next_step_handler(m, lambda msg: admin_save_price(msg, prod, plan))
        return

    # المفاتيح
    if data == "admk_add":
        if not prices_config: return bot.answer_callback_query(call.id, "❌ لا منتجات")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"admkadd_{prod}"))
        try: bot.edit_message_text("🔑 اختر منتج:", chat_id, msg_id, reply_markup=markup)
        except: pass
        return

    if data.startswith("admkadd_"):
        prod = data.split("_", 1)[1]
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"admkaddp_{prod}|{plan}"))
        try: bot.edit_message_text(f"📦 <b>{prod}</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admkaddp_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        m = bot.send_message(chat_id, f"🔑 المفاتيح لـ {prod}/{plan} (كل واحد بسطر):")
        bot.register_next_step_handler(m, lambda msg: admin_save_keys(msg, prod, plan))
        return

    if data == "admk_view":
        if not keys_store: return bot.answer_callback_query(call.id, "📭 لا مفاتيح")
        status = "🔑 <b>═══ المفاتيح ═══</b>\n\n"
        for prod, plans in keys_store.items():
            status += f"📦 <b>{prod}</b>\n"
            for plan, lst in plans.items():
                status += f"   ├ {plan}: {len(lst)}\n"
            status += "\n"
        try: bot.edit_message_text(status, chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data == "admk_del":
        if not prices_config: return bot.answer_callback_query(call.id, "❌")
        markup = types.InlineKeyboardMarkup()
        for prod in prices_config.keys():
            markup.add(types.InlineKeyboardButton(f"📦 {prod}", callback_data=f"admkdel_{prod}"))
        try: bot.edit_message_text("🔢 اختر منتج:", chat_id, msg_id, reply_markup=markup)
        except: pass
        return

    if data.startswith("admkdel_"):
        prod = data.split("_", 1)[1]
        markup = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            count = len(keys_store.get(prod, {}).get(plan, []))
            markup.add(types.InlineKeyboardButton(f"⏱️ {plan} ({count})", callback_data=f"admkdelp_{prod}|{plan}"))
        try: bot.edit_message_text(f"📦 <b>{prod}</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admkdelp_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        keys = keys_store.get(prod, {}).get(plan, [])
        if not keys: return bot.answer_callback_query(call.id, "❌ لا مفاتيح", show_alert=True)
        m = bot.send_message(chat_id, f"🔢 المفتاح أو رقمه:")
        bot.register_next_step_handler(m, lambda msg: admin_del_key(msg, prod, plan))
        return

    if data == "admk_clear":
        keys_store.clear()
        for prod in prices_config.keys():
            keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
        save_json(DB_KEYS, keys_store)
        return bot.answer_callback_query(call.id, "🗑️ تم المسح!", show_alert=True)

    # الأعضاء
    if data == "admm_view":
        m = bot.send_message(chat_id, "👤 أرسل آيدي العضو:")
        bot.register_next_step_handler(m, admin_view_member)
        return
    if data == "admm_charge":
        m = bot.send_message(chat_id, "💰 <code>ID المبلغ</code>", parse_mode="HTML")
        bot.register_next_step_handler(m, admin_charge_member)
        return

    # المبيعات
    if data == "adms_code":
        m = bot.send_message(chat_id, "🎫 <code>CODE القيمة</code>", parse_mode="HTML")
        bot.register_next_step_handler(m, admin_create_code)
        return
    if data == "adms_discount":
        m = bot.send_message(chat_id, "🔥 نسبة الخصم (0-99):")
        bot.register_next_step_handler(m, admin_set_discount)
        return

    # التسويق
    if data == "admmk_broadcast":
        m = bot.send_message(chat_id, "📢 نص الإذاعة:")
        bot.register_next_step_handler(m, admin_broadcast)
        return
    if data == "admmk_prices":
        if not prices_config: return bot.answer_callback_query(call.id, "❌")
        pub = "📢 <b>═══ الأسعار ═══</b>\n\n"
        for prod, plans in prices_config.items():
            pub += f"📦 <b>{prod}</b>\n"
            for plan, bp in plans.items():
                fp = int(bp * (1 - bot_config.get("discount", 0)/100))
                pub += f"   ├ {plan} ➡️ {fp} pts\n"
            pub += "\n"
        try:
            pub += f"🤖 t.me/{bot.get_me().username}"
            bot.send_message(CHANNEL_ID, pub, parse_mode="HTML")
            bot.answer_callback_query(call.id, "✅ نُشر!", show_alert=True)
        except: bot.answer_callback_query(call.id, "❌", show_alert=True)
        return
    if data == "admmk_fake":
        m = bot.send_message(chat_id, "📣 اكتب <code>تأكيد</code>:", parse_mode="HTML")
        bot.register_next_step_handler(m, admin_fake_marketing)
        return

    # الألعاب
    if data == "admg_lootbox":
        return show_lootbox_settings(chat_id, msg_id)
    if data == "admg_wheel":
        return show_wheel_settings(chat_id, msg_id)
    if data == "admg_quests":
        return show_quests_settings(chat_id, msg_id)

    # النظام
    if data == "adsys_daily":
        m = bot.send_message(chat_id, f"✨ الحالي: {bot_config.get('daily_gift', 10)}\n\nالقيمة الجديدة:")
        bot.register_next_step_handler(m, admin_edit_daily)
        return
    if data == "adsys_invite":
        m = bot.send_message(chat_id, f"🔗 الحالي: {bot_config.get('invite_reward', 20)}\n\nالقيمة الجديدة:")
        bot.register_next_step_handler(m, admin_edit_invite)
        return

    # ============ إعدادات الألعاب ============
    if data.startswith("cfg_"):
        handle_cfg_callback(call, data, chat_id, msg_id, uid, u)
        return

    # ============ التذاكر (أدمن) ============
    if data.startswith("view_ticket_"):
        t_id = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if t_id not in tickets: return bot.answer_callback_query(call.id, "❌")
        t_info = tickets[t_id]
        msg = f"🎫 <b>#{t_id}</b>\n👤 {t_info['uid']}\n\n{t_info['text']}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💬 رد", callback_data=f"reply_ticket_{t_id}"),
                   types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"close_ticket_{t_id}"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    if data.startswith("reply_ticket_"):
        t_id = data.split("_")[2]
        m = bot.send_message(chat_id, f"✍️ ردك #{t_id}:")
        bot.register_next_step_handler(m, lambda msg: admin_reply_ticket(msg, t_id))
        return

    if data.startswith("close_ticket_"):
        t_id = data.split("_")[2]
        if t_id in bot_config.get("tickets", {}):
            bot_config["tickets"][t_id]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
            try: bot.send_message(int(bot_config["tickets"][t_id]["uid"]), f"🔒 تذكرتك #{t_id} أُغلقت")
            except: pass
            try: bot.edit_message_text(f"✅ #{t_id} أُغلقت", chat_id, msg_id)
            except: pass
        return

    # ============ إدارة الأعضاء ============
    if data.startswith("adm_"):
        parts = data.split("_")
        action, target_id = parts[1], parts[2]
        tgt_u = get_user(target_id)
        if not tgt_u: return bot.answer_callback_query(call.id, "❌", show_alert=True)
        if action == "promote": update_user_data(target_id, is_admin=True)
        elif action == "demote": update_user_data(target_id, is_admin=False)
        elif action == "ban": update_user_data(target_id, banned=True)
        elif action == "tempban":
            until = datetime.now() + timedelta(days=1)
            update_user_data(target_id, banned_until=until.isoformat())
        elif action == "unban": update_user_data(target_id, banned=False, banned_until=None)
        bot.answer_callback_query(call.id, "✅", show_alert=True)
        return

# =====================================================
# ⚙️ إعدادات الألعاب Callback
# =====================================================
def handle_cfg_callback(call, data, chat_id, msg_id, uid, u):
    if not is_admin(uid, u):
        return bot.answer_callback_query(call.id, "❌", show_alert=True)
    
    if data.startswith("cfg_q_"):
        parts = data.split("_")
        tt, ft, ac = parts[2], parts[3], parts[4]
        tk = "invite" if tt == "inv" else ("buy" if tt == "buy" else "points")
        fk = "target" if ft == "t" else "reward"
        step = 1
        if tk == "points" and fk == "target": step = 250
        elif tk == "points" and fk == "reward": step = 50
        elif fk == "reward": step = 10
        if ac == "up": bot_config["quests"][tk][fk] += step
        else: bot_config["quests"][tk][fk] = max(1, bot_config["quests"][tk][fk] - step)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅")
        return show_quests_settings(chat_id, msg_id)
    
    if data.startswith("cfg_box_") or data.startswith("cfg_wheel_"):
        if data == "cfg_box_price_up": bot_config["lootbox_price"] = bot_config.get("lootbox_price", 50) + 5
        elif data == "cfg_box_price_down": bot_config["lootbox_price"] = max(5, bot_config.get("lootbox_price", 50) - 5)
        elif data == "cfg_box_chance_up": bot_config["lootbox_chance"] = min(100, bot_config.get("lootbox_chance", 25) + 5)
        elif data == "cfg_box_chance_down": bot_config["lootbox_chance"] = max(1, bot_config.get("lootbox_chance", 25) - 5)
        elif data == "cfg_wheel_price_up": bot_config["wheel_price"] = bot_config.get("wheel_price", 40) + 5
        elif data == "cfg_wheel_price_down": bot_config["wheel_price"] = max(5, bot_config.get("wheel_price", 40) - 5)
        elif data == "cfg_wheel_chance_up": bot_config["wheel_chance"] = min(100, bot_config.get("wheel_chance", 5) + 1)
        elif data == "cfg_wheel_chance_down": bot_config["wheel_chance"] = max(1, bot_config.get("wheel_chance", 5) - 1)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅")
        if "box" in data:
            return show_lootbox_settings(chat_id, msg_id)
        else:
            return show_wheel_settings(chat_id, msg_id)

def show_lootbox_settings(chat_id, msg_id=None):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = f"🎰 <b>═══ صندوق الحظ ═══</b>\n\n💸 السعر: <b>{price}</b>\n📊 النسبة: <b>{chance}%</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ سعر", callback_data="cfg_box_price_up"),
               types.InlineKeyboardButton("➖ سعر", callback_data="cfg_box_price_down"))
    markup.row(types.InlineKeyboardButton("📈 نسبة", callback_data="cfg_box_chance_up"),
               types.InlineKeyboardButton("📉 نسبة", callback_data="cfg_box_chance_down"))
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")

def show_wheel_settings(chat_id, msg_id=None):
    price = bot_config.get("wheel_price", 40)
    chance = bot_config.get("wheel_chance", 5)
    msg = f"🎡 <b>═══ عجلة الحظ ═══</b>\n\n💸 السعر: <b>{price}</b>\n📊 الكبرى: <b>{chance}%</b>"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ سعر", callback_data="cfg_wheel_price_up"),
               types.InlineKeyboardButton("➖ سعر", callback_data="cfg_wheel_price_down"))
    markup.row(types.InlineKeyboardButton("📈 نسبة", callback_data="cfg_wheel_chance_up"),
               types.InlineKeyboardButton("📉 نسبة", callback_data="cfg_wheel_chance_down"))
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")

def show_quests_settings(chat_id, msg_id=None):
    q = bot_config.get("quests")
    msg = (f"🔥 <b>═══ المهام ═══</b>\n\n"
           f"1️⃣ 👥 دعوات: {q['invite']['target']} / +{q['invite']['reward']}\n"
           f"2️⃣ 🛒 مبيعات: {q['buy']['target']} / +{q['buy']['reward']}\n"
           f"3️⃣ 💎 نقاط: {q['points']['target']} / +{q['points']['reward']}")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("👥 -", callback_data="cfg_q_inv_t_down"), types.InlineKeyboardButton("👥 +", callback_data="cfg_q_inv_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_inv_r_down"), types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_inv_r_up"))
    markup.row(types.InlineKeyboardButton("🛒 -", callback_data="cfg_q_buy_t_down"), types.InlineKeyboardButton("🛒 +", callback_data="cfg_q_buy_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_buy_r_down"), types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_buy_r_up"))
    markup.row(types.InlineKeyboardButton("💎 -", callback_data="cfg_q_pts_t_down"), types.InlineKeyboardButton("💎 +", callback_data="cfg_q_pts_t_up"))
    markup.row(types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_pts_r_down"), types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_pts_r_up"))
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")

# =====================================================
# 📥 معالجات الإدخال
# =====================================================
def process_redeem(message):
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    code = message.text.strip()
    if code in redeem_codes:
        added = redeem_codes.pop(code)
        update_user_data(uid, points=added, accumulated_points=added)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id, f"🎉 +<b>{added}</b> pts!", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Invalid code")

def process_support_ticket(message):
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    txt = message.text.strip()
    if not txt: return
    tid = str(random.randint(10000, 99999))
    if "tickets" not in bot_config: bot_config["tickets"] = {}
    bot_config["tickets"][tid] = {"uid": uid, "text": txt, "status": "open"}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, t(lang, "ticket_created", tid=tid), parse_mode="HTML")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 رد", callback_data=f"reply_ticket_{tid}"),
               types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"close_ticket_{tid}"))
    try: bot.send_message(ADMIN_PRIMARY, f"🎫 <b>#{tid}</b>\n👤 {uid}\n📝 {txt}", reply_markup=markup, parse_mode="HTML")
    except: pass

def process_product_request(message):
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    txt = message.text.strip()
    if not txt: return
    rid = str(random.randint(10000, 99999))
    if "product_requests" not in bot_config: bot_config["product_requests"] = {}
    bot_config["product_requests"][rid] = {"uid": uid, "text": txt, "date": datetime.now().isoformat()}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, t(lang, "product_request_sent", rid=rid), parse_mode="HTML")
    try: bot.send_message(ADMIN_PRIMARY, f"💡 #{rid}\n{uid}\n{txt}")
    except: pass

def admin_add_product(message):
    prod = message.text.strip()
    if prod in prices_config: return bot.send_message(message.chat.id, "❌ موجود")
    prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
    keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"➕ أُضيف: {prod}")

def admin_del_product(message):
    prod = message.text.strip()
    if prod not in prices_config: return bot.send_message(message.chat.id, "❌")
    prices_config.pop(prod)
    keys_store.pop(prod, None)
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ حُذف: {prod}")

def admin_save_price(message, prod, plan):
    try:
        new_price = int(message.text.strip())
        prices_config[prod][plan] = new_price
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ {prod}/{plan} = {new_price}")
    except: bot.send_message(message.chat.id, "❌ أرقام")

def admin_save_keys(message, prod, plan):
    keys = message.text.strip().split('\n')
    added = 0
    if prod not in keys_store: keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ +{added} مفتاح")

def admin_del_key(message, prod, plan):
    val = message.text.strip()
    keys = keys_store.get(prod, {}).get(plan, [])
    if val.isdigit() and 0 < int(val) <= len(keys):
        rm = keys.pop(int(val) - 1)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ حُذف: {rm}")
    if val in keys:
        keys.remove(val)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ حُذف")
    bot.send_message(message.chat.id, "❌")

def admin_view_member(message):
    t_id = message.text.strip()
    u = get_user(t_id)
    if not u: return bot.send_message(message.chat.id, "❌")
    role = "مالك 👑" if int(t_id) == ADMIN_PRIMARY else ("أدمن 🛡️" if u.get("is_admin", False) else "عادي")
    ban = "محظور ⛔" if u.get("banned", False) else "نشط 🟢"
    msg = f"👤 <code>{t_id}</code>\n💰 {u.get('points', 0)}\n{role}\n{ban}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    if u.get("is_admin", False):
        markup.add(types.InlineKeyboardButton("❌ إزالة", callback_data=f"adm_demote_{t_id}"))
    else:
        markup.add(types.InlineKeyboardButton("🛡️ ترقية", callback_data=f"adm_promote_{t_id}"))
    markup.add(types.InlineKeyboardButton("⛔", callback_data=f"adm_ban_{t_id}"),
               types.InlineKeyboardButton("⏱️", callback_data=f"adm_tempban_{t_id}"))
    markup.add(types.InlineKeyboardButton("🟢 فك", callback_data=f"adm_unban_{t_id}"))
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="HTML")

def admin_charge_member(message):
    try:
        p = message.text.strip().split()
        t_id, pts = p[0], int(p[1])
        if get_user(t_id):
            update_user_data(t_id, points=pts, accumulated_points=pts)
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 شُحن {t_id} +{pts}")
            try: bot.send_message(int(t_id), f"🎉 +{pts} من الإدارة")
            except: pass
        else: bot.send_message(message.chat.id, "❌")
    except: bot.send_message(message.chat.id, "❌ ID مسافة القيمة")

def admin_create_code(message):
    try:
        p = message.text.strip().split()
        code, pts = p[0], int(p[1])
        redeem_codes[code] = pts
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 {code} = {pts}")
    except: bot.send_message(message.chat.id, "❌")

def admin_set_discount(message):
    try:
        d = int(message.text.strip())
        if 0 <= d < 100:
            bot_config["discount"] = d
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 خصم: {d}%")
    except: bot.send_message(message.chat.id, "❌")

def admin_broadcast(message):
    s = 0
    for u_id in get_all_user_ids():
        try:
            bot.send_message(int(u_id), message.text)
            s += 1
            time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"📢 أُذيع لـ {s}")

def admin_fake_marketing(message):
    if not message.text.strip(): return
    plan = random.choice(["1 Day", "7 Days", "30 Days"])
    fake = generate_fake_key()
    try:
        m = f"🔥 <b>مبيعات جديدة!</b>\n\n📦 <code>Flourite Cheat</code>\n⏱️ <b>{plan}</b>\n🔐 <code>{fake}</code>\n\n🛒 t.me/{bot.get_me().username}"
        bot.send_message(CHANNEL_ID, m, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ نُشر {plan}")
    except Exception as e: bot.send_message(message.chat.id, f"❌ {e}")

def admin_reply_ticket(message, tid):
    tickets = bot_config.get("tickets", {})
    if tid not in tickets: return bot.send_message(message.chat.id, "❌")
    try:
        bot.send_message(int(tickets[tid]["uid"]), f"💬 <b>رد #{tid}:</b>\n\n{message.text}", parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ أُرسل #{tid}")
    except Exception as e: bot.send_message(message.chat.id, f"❌ {e}")

def admin_edit_daily(message):
    try:
        v = int(message.text.strip())
        if v >= 0:
            bot_config["daily_gift"] = v
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ المكافأة: {v}")
    except: bot.send_message(message.chat.id, "❌")

def admin_edit_invite(message):
    try:
        v = int(message.text.strip())
        if v >= 0:
            bot_config["invite_reward"] = v
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ الإحالة: {v}")
    except: bot.send_message(message.chat.id, "❌")

if __name__ == "__main__":
    print("🚀 البوت يعمل بواجهة احترافية!")
    bot.infinity_polling(none_stop=True, timeout=60)
