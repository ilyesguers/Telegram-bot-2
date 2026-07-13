"""
══════════════════════════════════════════════════════════════════════════════
║                         EVE Store Bot v3.0 - COMPLETE                       ║
║                    🚀 Full Integration with bot2-7                          ║
══════════════════════════════════════════════════════════════════════════════
║  Developer: @fkLJh00302                                                     ║
══════════════════════════════════════════════════════════════════════════════
"""

import telebot
from telebot import types
import random, os, time
from datetime import datetime, timedelta
from config import (bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, LOCALES, RANKS, TICKET_CATEGORIES, t)
from database import (engine, text, init_db, get_user, update_user_data, register_user, keys_store, redeem_codes, prices_config, bot_config, save_json, DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG, update_user_rank_and_quests, get_bot_stats, search_user)
from utils import (check_spam, is_user_banned, check_channel_join, generate_fake_key, trigger_captcha, is_captcha_pending, verify_captcha, require_verification_on_start, active_ticket_chats, admin_ticket_chats, animate_message, can_check_join, publish_sale_to_channel, publish_fake_marketing, publish_prices_to_channel, publish_flash_sale_to_channel, publish_maintenance_notice, get_active_flash_sale, create_flash_sale, format_time_remaining, send_typing_action)
from keyboards import *

# ═══════════════════════════════════════════════════════════════════════════
# 📦 استيراد جميع الوحدات
# ═══════════════════════════════════════════════════════════════════════════
import bot3
import bot4

# 🔒 bot5 - نظام حماية البيانات
try:
    import bot5
    from bot5 import init_data_fortress, save_setting, get_setting, save_product_db, get_all_products_db
    BOT5_LOADED = True
except ImportError as e:
    print(f"⚠️ bot5.py not loaded: {e}")
    BOT5_LOADED = False

# 🛡️ bot6 - نظام الحماية الذكي
try:
    import bot6
    from bot6 import (shield_check, shield_referral_check, shield_daily_bonus_check, 
                      send_shield_captcha, get_shield_stats, show_shield_panel,
                      smart_ban, smart_unban, get_trust_score, modify_trust_score)
    BOT6_LOADED = True
except ImportError as e:
    print(f"⚠️ bot6.py not loaded: {e}")
    BOT6_LOADED = False

# 🎨 bot7 - واجهة Premium
try:
    import bot7
    from bot7 import (show_premium_main_menu, show_premium_account, show_premium_shop,
                      show_premium_rewards, show_premium_entertainment, show_premium_support,
                      show_premium_settings, build_premium_main_menu, create_premium_main_keyboard,
                      pt, PREMIUM_UI_TEXT, THEMES, get_user_theme)
    BOT7_LOADED = True
except ImportError as e:
    print(f"⚠️ bot7.py not loaded: {e}")
    BOT7_LOADED = False

# 🎁 bot2 - نظام Giveaway ورسائل القناة
from bot2 import (create_giveaway, get_giveaway, is_giveaway_valid, has_user_claimed_giveaway,
                  claim_giveaway, publish_giveaway_to_channel, start_giveaway_captcha,
                  verify_giveaway_captcha, process_giveaway_claim, get_all_giveaways,
                  cancel_giveaway, send_custom_channel_message, send_raw_channel_message,
                  delete_channel_message, format_giveaway_win_message, format_giveaway_error,
                  get_giveaways_stats, show_vip_menu, show_stars_menu, is_vip_active,
                  show_admin_vip_menu, show_admin_restock_menu)

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 تهيئة قاعدة البيانات والأنظمة
# ═══════════════════════════════════════════════════════════════════════════
init_db()

# تهيئة نظام حماية البيانات (bot5)
if BOT5_LOADED:
    try:
        init_data_fortress()
        print("✅ Data Fortress initialized")
    except Exception as e:
        print(f"⚠️ Data Fortress init error: {e}")

# متغير مؤقت لتخزين إعدادات giveaway قيد الإنشاء
temp_giveaway_setup = {}

# متغير مؤقت لتخزين آخر رسائل القناة
last_channel_msgs = {}

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 دوال مساعدة
# ═══════════════════════════════════════════════════════════════════════════

def is_admin(uid, u=None):
    """التحقق من صلاحيات الأدمن"""
    if u is None:
        u = get_user(uid) or {}
    return int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)

def get_all_user_ids():
    """جلب جميع معرفات المستخدمين"""
    with engine.connect() as conn:
        return [str(r[0]) for r in conn.execute(text("SELECT uid FROM users")).fetchall()]

def enforce_subscription(message, lang="ar"):
    """فرض الاشتراك في القناة"""
    uid = str(message.from_user.id)
    if not check_channel_join(uid):
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ 🔐 JOIN REQUIRED 🔐 ║\n"
            f"╚═══════════════════════╝\n\n"
            f"⚠️ You must join our channel to use this bot!\n\n"
            f"📢 Simple Steps:\n"
            f"1️⃣ Click «Join Our Channel» below\n"
            f"2️⃣ Press «Join» in Telegram\n"
            f"3️⃣ Come back & press «Verify»\n\n"
            f"🎁 Unlock all features after joining!"
        )
        try:
            bot.send_message(message.chat.id, msg, reply_markup=get_join_inline(lang), parse_mode="HTML")
        except:
            pass
        return False
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 معالج الأوامر الرئيسية
# ═══════════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start', 'id', 'close', 'end', 'help'])
def handle_commands(message):
    uid = str(message.from_user.id)
    
    # 🛡️ فحص نظام الحماية الذكي (bot6)
    if BOT6_LOADED:
        allowed, shield_msg, needs_captcha = shield_check(uid, "command")
        if not allowed:
            return bot.send_message(message.chat.id, shield_msg, parse_mode="HTML")
        if needs_captcha:
            u = get_user(uid) or {}
            return send_shield_captcha(message.chat.id, uid, u.get("lang", "ar"))
    
    if check_spam(uid):
        return
    
    register_user(message.from_user)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔒 إغلاق دردشة التذكرة
    # ═══════════════════════════════════════════════════════════════════════
    if message.text.startswith('/close') or message.text.startswith('/end'):
        if uid in active_ticket_chats:
            tid = active_ticket_chats.pop(uid)
            tickets = bot_config.get("tickets", {})
            if tid in tickets:
                tickets[tid]["status"] = "closed"
                save_json(DB_CONFIG, bot_config)
            
            for adm_uid, info in list(admin_ticket_chats.items()):
                if info.get("ticket_id") == tid:
                    admin_ticket_chats.pop(adm_uid, None)
                    try:
                        bot.send_message(int(adm_uid), f"🔒 Ticket #{tid} closed by user", parse_mode="HTML")
                    except:
                        pass
            
            bot.send_message(message.chat.id,
                f"╔═══════════════════════╗\n"
                f"║ 🔒 CHAT ENDED ║\n"
                f"╚═══════════════════════╝\n\n"
                f"✅ Ticket #{tid} closed successfully!\n"
                f"💬 Thank you for contacting us!",
                parse_mode="HTML")
            show_main_menu(message.chat.id, uid, lang)
            return
        
        if uid in admin_ticket_chats:
            info = admin_ticket_chats.pop(uid)
            tid = info["ticket_id"]
            user_uid = info["user_uid"]
            tickets = bot_config.get("tickets", {})
            if tid in tickets:
                tickets[tid]["status"] = "closed"
                save_json(DB_CONFIG, bot_config)
            active_ticket_chats.pop(user_uid, None)
            try:
                u_lang = (get_user(user_uid) or {}).get("lang", "ar")
                bot.send_message(int(user_uid),
                    f"╔═══════════════════════╗\n"
                    f"║ 🔒 SUPPORT ENDED ║\n"
                    f"╚═══════════════════════╝\n\n"
                    f"✅ Ticket #{tid} closed\n"
                    f"⭐ Thank you!",
                    parse_mode="HTML")
            except:
                pass
            return bot.send_message(message.chat.id, f"✅ Ticket #{tid} closed")
        
        return bot.send_message(message.chat.id, "ℹ️ No active chat to close.")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📖 المساعدة
    # ═══════════════════════════════════════════════════════════════════════
    if message.text.startswith('/help'):
        help_msg = (
            f"╔═══════════════════════╗\n"
            f"║ 📖 HELP MENU ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🔹 /start - Main menu\n"
            f"🔹 /id - Your Telegram ID\n"
            f"🔹 /close - End ticket chat\n"
            f"🔹 /help - This menu\n\n"
            f"💻 Developer: @fkLJh00302"
        )
        return bot.send_message(message.chat.id, help_msg, parse_mode="HTML")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, t(lang, "banned"), parse_mode="HTML")
    
    if message.text.startswith('/id'):
        if not enforce_subscription(message, lang):
            return
        return bot.send_message(message.chat.id,
            f"🆔 Your Info:\n\n"
            f"👤 ID: <code>{uid}</code>\n"
            f"📝 Username: @{u.get('username', 'N/A')}",
            parse_mode="HTML")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎁 نظام الإحالة و Giveaway
    # ═══════════════════════════════════════════════════════════════════════
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        # 🎁 رابط Giveaway
        if param.startswith("gw_"):
            gw_code = param[3:]
            if not enforce_subscription(message, lang):
                return
            if not u.get("verified", False):
                require_verification_on_start(uid)
                return
            
            valid, reason = is_giveaway_valid(gw_code)
            if not valid:
                error_msg = format_giveaway_error(reason, lang)
                return bot.send_message(message.chat.id, error_msg, parse_mode="HTML")
            
            if has_user_claimed_giveaway(gw_code, uid):
                return bot.send_message(message.chat.id, t(lang, "gw_already_claimed"), parse_mode="HTML")
            
            gw = get_giveaway(gw_code)
            remaining = gw["max_users"] - len(gw.get("claimed_by", []))
            time_left = format_time_remaining(gw["expires"])
            
            bot.send_message(message.chat.id,
                t(lang, "gw_welcome_claim", reward=gw["reward"], remaining=remaining, max=gw["max_users"], time=time_left),
                parse_mode="HTML")
            time.sleep(0.5)
            start_giveaway_captcha(uid, gw_code)
            return
        
        # 🔗 نظام الإحالة العادي
        if u.get("invited_by") is None:
            inv_id = param
            
            # 🛡️ فحص الإحالة (bot6)
            if BOT6_LOADED:
                ref_allowed, ref_msg = shield_referral_check(inv_id, message.from_user)
                if not ref_allowed:
                    # سجل المحاولة لكن لا تمنع المستخدم الجديد
                    pass
            
            if get_user(inv_id) and inv_id != uid:
                update_user_data(uid, invited_by=inv_id)
                reward = bot_config.get("invite_reward", 20)
                update_user_data(inv_id, points=reward, accumulated_points=reward, invite_count=1, referral_earnings=reward)
                update_user_rank_and_quests(inv_id)
                try:
                    bot.send_message(int(inv_id),
                        f"╔═══════════════════════╗\n"
                        f"║ 🎊 NEW REFERRAL! ║\n"
                        f"╚═══════════════════════╝\n\n"
                        f"🎉 Someone joined using your link!\n"
                        f"🎁 Reward: +{reward} 💎\n\n"
                        f"💡 Keep inviting for more!",
                        parse_mode="HTML")
                except:
                    pass
    
    if not enforce_subscription(message, lang):
        return
    
    if not u.get("verified", False):
        require_verification_on_start(uid)
        return
    
    if not u.get("lang_selected", False):
        return bot.send_message(message.chat.id, t("ar", "welcome"), reply_markup=get_lang_inline(), parse_mode="HTML")
    
    show_main_menu(message.chat.id, uid, lang)

# ═══════════════════════════════════════════════════════════════════════════
# 🏠 عرض القائمة الرئيسية
# ═══════════════════════════════════════════════════════════════════════════

def show_main_menu(chat_id, uid, lang):
    """عرض القائمة الرئيسية مع الأنيميشن"""
    u = get_user(uid) or {}
    name = u.get("username") or "User"
    
    # 🎨 استخدام واجهة Premium إذا كانت متاحة
    if BOT7_LOADED:
        try:
            show_premium_main_menu(chat_id, uid)
            return
        except Exception as e:
            print(f"⚠️ Premium UI error: {e}")
    
    # الواجهة الافتراضية
    welcome_frames = [
        f"⏳ Loading...",
        f"✨ Welcome back...",
        f"🎊 Ready!",
        t(lang, "main_menu_title", name=name)
    ]
    
    try:
        msg = bot.send_message(chat_id, welcome_frames[0], parse_mode="HTML")
        for frame in welcome_frames[1:]:
            time.sleep(0.3)
            try:
                bot.edit_message_text(frame, chat_id, msg.message_id, parse_mode="HTML")
            except:
                pass
    except:
        pass
    
    # عرض العروض الخاطفة النشطة
    fs = get_active_flash_sale()
    if fs:
        try:
            remaining = format_time_remaining(fs["expires"])
            fs_msg = (
                f"⚡⚡⚡ ACTIVE FLASH SALE! ⚡⚡⚡\n\n"
                f"🔥 {fs['discount']}% OFF on {fs['product']}\n"
                f"⏰ Ends in: {remaining}\n\n"
                f"💨 Grab it before it's gone!"
            )
            bot.send_message(chat_id, fs_msg, parse_mode="HTML")
        except:
            pass
    
    bot.send_message(chat_id, "👇", reply_markup=get_main_keyboard(uid, lang))

# ═══════════════════════════════════════════════════════════════════════════
# 💬 معالجات دردشة التذاكر
# ═══════════════════════════════════════════════════════════════════════════

def handle_user_ticket_message(message, uid):
    """معالجة رسائل المستخدم في التذكرة"""
    tid = active_ticket_chats[uid]
    tickets = bot_config.get("tickets", {})
    
    if tid not in tickets:
        active_ticket_chats.pop(uid, None)
        return
    
    if "messages" not in tickets[tid]:
        tickets[tid]["messages"] = []
    
    tickets[tid]["messages"].append({
        "from": "user",
        "text": message.text or "[media]",
        "time": datetime.now().isoformat()
    })
    save_json(DB_CONFIG, bot_config)
    
    u = get_user(uid) or {}
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💬 Reply Now", callback_data=f"admchat_{tid}"),
        types.InlineKeyboardButton("🔒 Close", callback_data=f"admclosetick_{tid}")
    )
    
    try:
        bot.send_message(ADMIN_PRIMARY,
            f"╔═══════════════════════╗\n"
            f"║ 📨 NEW MESSAGE ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🎫 Ticket: #{tid}\n"
            f"👤 From: @{u.get('username', 'N/A')}\n"
            f"🆔 ID: <code>{uid}</code>\n\n"
            f"💬 Message:\n<code>{message.text}</code>",
            reply_markup=m, parse_mode="HTML")
    except:
        pass
    
    bot.send_message(message.chat.id,
        f"✅ Message Sent 📨\n\n"
        f"⏳ Support will reply soon...\n"
        f"🔒 Type /close to end chat",
        parse_mode="HTML")

def handle_admin_ticket_message(message, admin_uid):
    """معالجة رسائل الأدمن في التذكرة"""
    if message.text and (message.text.startswith('/close') or message.text.startswith('/end')):
        info = admin_ticket_chats.pop(admin_uid)
        tid = info["ticket_id"]
        user_uid = info["user_uid"]
        tickets = bot_config.get("tickets", {})
        if tid in tickets:
            tickets[tid]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
        active_ticket_chats.pop(user_uid, None)
        try:
            bot.send_message(int(user_uid),
                f"╔═══════════════════════╗\n"
                f"║ 🔒 SUPPORT ENDED ║\n"
                f"╚═══════════════════════╝\n\n"
                f"✅ Ticket #{tid} closed\n"
                f"⭐ Thank you for choosing us!",
                parse_mode="HTML")
        except:
            pass
        return bot.send_message(message.chat.id, f"✅ Ticket #{tid} closed")
    
    info = admin_ticket_chats[admin_uid]
    tid = info["ticket_id"]
    user_uid = info["user_uid"]
    tickets = bot_config.get("tickets", {})
    
    if tid in tickets:
        if "messages" not in tickets[tid]:
            tickets[tid]["messages"] = []
        tickets[tid]["messages"].append({
            "from": "admin",
            "text": message.text or "[media]",
            "time": datetime.now().isoformat()
        })
        save_json(DB_CONFIG, bot_config)
    
    try:
        bot.send_message(int(user_uid),
            f"╔═══════════════════════╗\n"
            f"║ 💬 SUPPORT REPLY ║\n"
            f"╚═══════════════════════╝\n\n"
            f"👨‍💻 Support Team:\n\n"
            f"<code>{message.text}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💡 Reply anytime | Type /close to end",
            parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ Reply sent to user")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# 🛍️ عرض المتجر
# ═══════════════════════════════════════════════════════════════════════════

def show_shop(message, uid, u, lang):
    """عرض المتجر"""
    # 🎨 استخدام واجهة Premium إذا كانت متاحة
    if BOT7_LOADED:
        try:
            show_premium_shop(message.chat.id, uid)
            return
        except:
            pass
    
    if not prices_config:
        return bot.send_message(message.chat.id, t(lang, "shop_empty"), parse_mode="HTML")
    
    points = u.get("points", 0) or 0
    rank_disc = u.get("rank_discount", 0.0) or 0.0
    global_disc = bot_config.get("discount", 0)
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 🛍️ {t(lang, 'shop_title')} ║\n"
        f"╚═══════════════════════╝\n\n"
        f"💰 {t(lang, 'your_balance')}: {points} 💎\n"
        f"🎯 {t(lang, 'your_discount')}: {int(rank_disc * 100)}%\n"
    )
    
    if global_disc > 0:
        msg += f"🔥 {t(lang, 'global_discount')}: {global_disc}%\n"
    
    msg += f"\n👇 {t(lang, 'choose_product')}:"
    
    m = types.InlineKeyboardMarkup(row_width=1)
    for prod in prices_config.keys():
        total_stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        status = "✅" if total_stock > 0 else "❌"
        m.add(types.InlineKeyboardButton(f"{status} 📦 {prod} ({total_stock})", callback_data=f"shop_{prod}"))
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 🎫 إدارة التذاكر (للأدمن)
# ═══════════════════════════════════════════════════════════════════════════

def admin_show_tickets(message):
    """عرض التذاكر للأدمن"""
    tickets = bot_config.get("tickets", {})
    open_tickets = {k: v for k, v in tickets.items() if v.get("status") == "open"}
    
    if not open_tickets:
        return bot.send_message(message.chat.id, "📭 لا توجد تذاكر مفتوحة")
    
    msg = f"🎫 ━━ التذاكر المفتوحة ({len(open_tickets)}) ━━\n\n"
    m = types.InlineKeyboardMarkup(row_width=1)
    
    for tid, tdata in list(open_tickets.items())[:20]:
        u = get_user(tdata.get("uid", "")) or {}
        cat = tdata.get("category", "other")
        cat_name = TICKET_CATEGORIES.get(cat, {}).get("ar", "أخرى")
        msg += f"🎫 #{tid} | @{u.get('username', 'N/A')} | {cat_name}\n"
        m.add(types.InlineKeyboardButton(f"🎫 #{tid} - {cat_name}", callback_data=f"admviewtick_{tid}"))
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 📊 عرض الإحصائيات (للأدمن)
# ═══════════════════════════════════════════════════════════════════════════

def admin_show_stats(message):
    """عرض الإحصائيات للأدمن"""
    stats = get_bot_stats()
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 📊 STATISTICS ║\n"
        f"╚═══════════════════════╝\n\n"
        f"👥 Users: {stats.get('total_users', 0)}\n"
        f"🟢 Active (24h): {stats.get('active_today', 0)}\n"
        f"💰 Total Points: {stats.get('total_points', 0)}\n"
        f"🛒 Total Sales: {stats.get('total_sales', 0)}\n"
        f"🔑 Total Keys: {stats.get('total_keys', 0)}\n"
        f"🎫 Open Tickets: {stats.get('open_tickets', 0)}\n"
        f"👑 VIP Members: {stats.get('vip_count', 0)}\n"
    )
    
    # إضافة إحصائيات Shield إذا كان متاحاً
    if BOT6_LOADED:
        try:
            shield_stats = get_shield_stats()
            msg += f"\n🛡️ Shield Stats:\n"
            msg += f"├── 🚫 Bans: {shield_stats.get('active_bans', 0)}\n"
            msg += f"├── ⚠️ Warnings: {shield_stats.get('total_warnings', 0)}\n"
            msg += f"└── 📈 Avg Trust: {shield_stats.get('avg_trust', 0):.1f}\n"
        except:
            pass
    
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 💡 عرض طلبات المنتجات (للأدمن)
# ═══════════════════════════════════════════════════════════════════════════

def admin_show_product_requests(message):
    """عرض طلبات المنتجات"""
    requests = bot_config.get("product_requests", {})
    
    if not requests:
        return bot.send_message(message.chat.id, "📭 لا توجد طلبات")
    
    msg = f"💡 ━━ طلبات المنتجات ({len(requests)}) ━━\n\n"
    
    for rid, rdata in list(requests.items())[:20]:
        u = get_user(rdata.get("uid", "")) or {}
        msg += f"🆔 #{rid}\n"
        msg += f"👤 @{u.get('username', 'N/A')}\n"
        msg += f"📝 {rdata.get('text', '')[:50]}...\n\n"
    
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 الموجّه الرئيسي للرسائل
# ═══════════════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda message: True)
def main_router(message):
    uid = str(message.from_user.id)
    
    # دردشة التذاكر
    if uid in active_ticket_chats:
        return handle_user_ticket_message(message, uid)
    
    if uid in admin_ticket_chats:
        return handle_admin_ticket_message(message, uid)
    
    # 📨 معالجة إرسال رسائل القناة (للأدمن)
    if uid in last_channel_msgs:
        action = last_channel_msgs[uid]
        del last_channel_msgs[uid]
        
        if action == "send_styled":
            msg_id = send_custom_channel_message(message.text)
            if msg_id:
                return bot.send_message(message.chat.id,
                    f"✅ تم النشر بنجاح!\n\n"
                    f"📋 Message ID: <code>{msg_id}</code>\n"
                    f"💡 احفظ الـ ID للحذف لاحقاً",
                    parse_mode="HTML")
            else:
                return bot.send_message(message.chat.id, "❌ فشل الإرسال")
        
        elif action == "send_raw":
            msg_id = send_raw_channel_message(message.text)
            if msg_id:
                return bot.send_message(message.chat.id,
                    f"✅ تم النشر بنجاح!\n\n"
                    f"📋 Message ID: <code>{msg_id}</code>",
                    parse_mode="HTML")
            else:
                return bot.send_message(message.chat.id, "❌ فشل الإرسال")
        
        elif action == "delete_msg":
            try:
                msg_id = int(message.text.strip())
                if delete_channel_message(msg_id):
                    return bot.send_message(message.chat.id,
                        f"✅ تم حذف الرسالة!\n\n📋 ID: {msg_id}",
                        parse_mode="HTML")
                else:
                    return bot.send_message(message.chat.id, "❌ فشل الحذف - تأكد من ID الرسالة")
            except:
                return bot.send_message(message.chat.id, "❌ ID غير صحيح")
    
    # 🛡️ فحص الحماية الذكية (bot6)
    if BOT6_LOADED:
        allowed, shield_msg, needs_captcha = shield_check(uid, "message")
        if not allowed:
            return bot.send_message(message.chat.id, shield_msg, parse_mode="HTML")
        if needs_captcha:
            u = get_user(uid) or {}
            return send_shield_captcha(message.chat.id, uid, u.get("lang", "ar"))
    
    if check_spam(uid):
        return
    
    register_user(message.from_user)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, t(lang, "banned"), parse_mode="HTML")
    
    if is_captcha_pending(uid):
        return bot.send_message(message.chat.id, "🛡️ Solve captcha first!", parse_mode="HTML")
    
    txt = message.text.strip() if message.text else ""
    admin_flag = is_admin(uid, u)
    
    if not enforce_subscription(message, lang):
        return
    
    if bot_config.get("maintenance", False) and not admin_flag:
        return bot.send_message(message.chat.id,
            f"╔═══════════════════════╗\n"
            f"║ 🛠️ MAINTENANCE 🛠️ ║\n"
            f"╚═══════════════════════╝\n\n"
            f"⚠️ Bot is temporarily offline\n"
            f"⏳ We'll be back soon!",
            parse_mode="HTML")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🟢 أزرار المستخدم
    # ═══════════════════════════════════════════════════════════════════════
    
    if txt == t(lang, "btn_account"):
        if BOT7_LOADED:
            try:
                return show_premium_account(message.chat.id, uid)
            except:
                pass
        return bot.send_message(message.chat.id,
            f"{t(lang, 'account_title')}\n\n{t(lang, 'account_desc')}",
            reply_markup=get_account_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_shop"):
        return show_shop(message, uid, u, lang)
    
    if txt == t(lang, "btn_rewards"):
        if BOT7_LOADED:
            try:
                return show_premium_rewards(message.chat.id, uid)
            except:
                pass
        return bot.send_message(message.chat.id,
            f"{t(lang, 'rewards_title')}\n\n{t(lang, 'rewards_desc')}",
            reply_markup=get_rewards_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_entertainment"):
        if BOT7_LOADED:
            try:
                return show_premium_entertainment(message.chat.id, uid)
            except:
                pass
        return bot.send_message(message.chat.id,
            f"{t(lang, 'entertainment_title')}\n\n{t(lang, 'entertainment_desc')}",
            reply_markup=get_entertainment_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_support"):
        if BOT7_LOADED:
            try:
                return show_premium_support(message.chat.id, uid)
            except:
                pass
        return bot.send_message(message.chat.id,
            f"{t(lang, 'support_title')}\n\n{t(lang, 'support_desc')}",
            reply_markup=get_support_menu(lang), parse_mode="HTML")
    
    if txt == t(lang, "btn_settings"):
        if BOT7_LOADED:
            try:
                return show_premium_settings(message.chat.id, uid)
            except:
                pass
        return bot.send_message(message.chat.id,
            f"{t(lang, 'settings_title')}\n\n{t(lang, 'settings_desc')}",
            reply_markup=get_settings_menu(lang, u), parse_mode="HTML")
    
    # 👑 VIP
    if txt == "👑 VIP":
        return show_vip_menu(message.chat.id, uid)
    
    # ⭐ Stars
    if txt == "⭐ Stars":
        return show_stars_menu(message.chat.id, uid)
    
    # 🎮 Mini Games
    if txt == "🎮 Mini Games":
        return bot4.show_games_menu(message)
    
    # 🔐 زر الأدمن
    if txt == t(lang, "btn_admin") and admin_flag:
        return bot.send_message(message.chat.id,
            f"╔═══════════════════════╗\n"
            f"║ 👑 ADMIN PANEL ║\n"
            f"╚═══════════════════════╝\n\n"
            f"⚡ Full control at your fingertips",
            reply_markup=get_admin_keyboard(), parse_mode="HTML")
    
    # 🔙 زر العودة (للأدمن)
    if txt == "🔙 العودة" and admin_flag:
        return show_main_menu(message.chat.id, uid, lang)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أزرار الأدمن
    # ═══════════════════════════════════════════════════════════════════════
    
    if admin_flag:
        
        if txt == "📦 المنتجات":
            return bot.send_message(message.chat.id,
                "📦 إدارة المنتجات",
                reply_markup=admin_products_menu(), parse_mode="HTML")
        
        if txt == "🔑 المفاتيح":
            return bot.send_message(message.chat.id,
                "🔑 إدارة المفاتيح",
                reply_markup=admin_keys_menu(), parse_mode="HTML")
        
        if txt == "👥 الأعضاء":
            return bot.send_message(message.chat.id,
                "👥 إدارة الأعضاء",
                reply_markup=admin_members_menu(), parse_mode="HTML")
        
        if txt == "🎫 التذاكر":
            return admin_show_tickets(message)
        
        if txt == "💰 المبيعات":
            return bot.send_message(message.chat.id,
                "💰 المبيعات والأكواد",
                reply_markup=admin_sales_menu(), parse_mode="HTML")
        
        if txt == "📢 التسويق":
            return bot.send_message(message.chat.id,
                "📢 التسويق",
                reply_markup=admin_marketing_menu(), parse_mode="HTML")
        
        if txt == "⚡ عروض خاطفة":
            fs = get_active_flash_sale()
            status = ""
            if fs:
                status = f"\n\n⚡ Active: {fs['product']} ({fs['discount']}% OFF)"
            return bot.send_message(message.chat.id,
                f"⚡ العروض الخاطفة{status}",
                reply_markup=admin_flash_menu(), parse_mode="HTML")
        
        # 🎁 قائمة Giveaway
        if txt == "🎁 Giveaway":
            stats = get_giveaways_stats()
            return bot.send_message(message.chat.id,
                f"╔═══════════════════════╗\n"
                f"║ 🎁 GIVEAWAY ║\n"
                f"╚═══════════════════════╝\n\n"
                f"📊 الإحصائيات:\n"
                f"├ الكل: {stats['total']}\n"
                f"├ نشط: {stats['active']}\n"
                f"├ منتهي: {stats['expired']}\n"
                f"└ ممتلئ: {stats['full']}",
                reply_markup=admin_giveaway_menu(), parse_mode="HTML")
        
        # 👑 إدارة VIP
        if txt == "👑 إدارة VIP":
            return show_admin_vip_menu(message.chat.id)
        
        # 📦 التجديد التلقائي
        if txt == "📦 التجديد التلقائي":
            return show_admin_restock_menu(message.chat.id)
        
        # 📨 قائمة رسائل القناة
        if txt == "📨 رسائل القناة":
            return bot.send_message(message.chat.id,
                f"╔═══════════════════════╗\n"
                f"║ 📨 CHANNEL MSGS ║\n"
                f"╚═══════════════════════╝\n\n"
                f"📢 اختر الإجراء:",
                reply_markup=admin_channel_menu(), parse_mode="HTML")
        
        if txt == "🎮 الألعاب":
            return bot.send_message(message.chat.id,
                "🎮 إعدادات الألعاب",
                reply_markup=admin_games_menu(), parse_mode="HTML")
        
        if txt == "⚙️ النظام":
            return bot.send_message(message.chat.id,
                "⚙️ النظام",
                reply_markup=admin_system_menu(), parse_mode="HTML")
        
        if txt == "📊 الإحصائيات":
            return admin_show_stats(message)
        
        if txt == "💡 الطلبات":
            return admin_show_product_requests(message)
        
        # 🛡️ لوحة الحماية (bot6)
        if txt == "🛡️ مكافحة الرشق":
            if BOT6_LOADED:
                return show_shield_panel(message.chat.id)
            else:
                return bot.send_message(message.chat.id, "⚠️ نظام الحماية غير محمّل")
        
        if txt == "🛠️ وضع الصيانة":
            current = bot_config.get("maintenance", False)
            new_state = not current
            bot_config["maintenance"] = new_state
            save_json(DB_CONFIG, bot_config)
            
            if new_state:
                msg = (f"╔═══════════════════════╗\n"
                       f"║ 🛠️ MAINTENANCE ON ║\n"
                       f"╚═══════════════════════╝\n\n"
                       f"⚠️ Bot is now OFFLINE for users")
                publish_maintenance_notice(True)
            else:
                msg = (f"╔═══════════════════════╗\n"
                       f"║ ✅ MAINTENANCE OFF ║\n"
                       f"╚═══════════════════════╝\n\n"
                       f"✅ Bot is now ONLINE")
                publish_maintenance_notice(False)
            
            return bot.send_message(message.chat.id, msg, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 🔘 معالج الأزرار التفاعلية (Callback Query)
# ═══════════════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🌐 اختيار اللغة
    # ═══════════════════════════════════════════════════════════════════════
    if data.startswith("setlang_"):
        new_lang = data.split("_")[1]
        update_user_data(uid, lang=new_lang, lang_selected=True)
        bot.answer_callback_query(call.id, f"✅ {LOCALES.get(new_lang, new_lang)}")
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        show_main_menu(chat_id, uid, new_lang)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # ✅ التحقق من الانضمام
    # ═══════════════════════════════════════════════════════════════════════
    if data == "check_join":
        if can_check_join(uid):
            if check_channel_join(uid):
                bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass
                if not u.get("verified", False):
                    update_user_data(uid, verified=True)
                show_main_menu(chat_id, uid, lang)
            else:
                bot.answer_callback_query(call.id, "❌ Join channel first!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⏳ Wait 5 seconds", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 👤 قائمة الحساب
    # ═══════════════════════════════════════════════════════════════════════
    if data == "menu_balance":
        points = u.get("points", 0) or 0
        acc = u.get("accumulated_points", 0) or 0
        bot.answer_callback_query(call.id, f"💰 Balance: {points} 💎\n📊 Total: {acc}", show_alert=True)
        return
    
    if data == "menu_myid":
        bot.answer_callback_query(call.id, f"🆔 Your ID: {uid}", show_alert=True)
        return
    
    if data == "menu_rank":
        rank = u.get("rank", "Member")
        disc = int((u.get("rank_discount", 0) or 0) * 100)
        bot.answer_callback_query(call.id, f"🏆 Rank: {rank}\n🎯 Discount: {disc}%", show_alert=True)
        return
    
    if data == "menu_referral":
        try:
            bot_user = bot.get_me().username
        except:
            bot_user = "bot"
        
        link = f"https://t.me/{bot_user}?start={uid}"
        invite_count = u.get("invite_count", 0) or 0
        earnings = u.get("referral_earnings", 0) or 0
        reward = bot_config.get("invite_reward", 20)
        
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ 🔗 REFERRAL LINK ║\n"
            f"╚═══════════════════════╝\n\n"
            f"📎 Your link:\n<code>{link}</code>\n\n"
            f"👥 Invites: {invite_count}\n"
            f"💰 Earned: {earnings} 💎\n"
            f"🎁 Per invite: +{reward} 💎"
        )
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    if data == "menu_purchases":
        sales = bot_config.get("sales_log", [])
        user_sales = [s for s in sales if str(s.get("uid")) == uid][-10:]
        
        if not user_sales:
            bot.answer_callback_query(call.id, "📭 No purchases yet", show_alert=True)
            return
        
        msg = f"📜 ━━ Your Purchases ━━\n\n"
        for s in reversed(user_sales):
            msg += f"• {s['product']} / {s['plan']} - {s.get('date', '')[:10]}\n"
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎁 قائمة المكافآت
    # ═══════════════════════════════════════════════════════════════════════
    if data == "menu_daily":
        # 🛡️ فحص إساءة استخدام المكافأة اليومية (bot6)
        if BOT6_LOADED:
            daily_allowed, daily_msg = shield_daily_bonus_check(uid)
            if not daily_allowed:
                bot.answer_callback_query(call.id, daily_msg, show_alert=True)
                return
        
        last_daily = u.get("last_daily")
        if last_daily:
            try:
                last_time = datetime.fromisoformat(last_daily)
                if (datetime.now() - last_time).total_seconds() < 86400:
                    remaining = 86400 - (datetime.now() - last_time).total_seconds()
                    hours = int(remaining // 3600)
                    mins = int((remaining % 3600) // 60)
                    bot.answer_callback_query(call.id, f"⏰ Come back in {hours}h {mins}m", show_alert=True)
                    return
            except:
                pass
        
        # إعطاء المكافأة
        daily_amount = bot_config.get("daily_gift", 10)
        
        # مضاعفة لـ VIP
        if is_vip_active(uid):
            daily_amount *= 2
        
        # مكافأة إضافية للسلسلة
        streak = u.get("streak_days", 0) or 0
        yesterday = datetime.now() - timedelta(days=1)
        if last_daily:
            try:
                last_time = datetime.fromisoformat(last_daily)
                if last_time.date() == yesterday.date():
                    streak += 1
                else:
                    streak = 1
            except:
                streak = 1
        else:
            streak = 1
        
        streak_bonus = min(streak * 2, 20)
        total = daily_amount + streak_bonus
        
        update_user_data(uid, points=total, accumulated_points=total, last_daily=datetime.now().isoformat(), streak_days=streak)
        update_user_rank_and_quests(uid)
        
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ 🎁 DAILY BONUS! ║\n"
            f"╚═══════════════════════╝\n\n"
            f"💎 Base: +{daily_amount}\n"
            f"🔥 Streak ({streak} days): +{streak_bonus}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💰 Total: +{total} 💎\n\n"
            f"✨ Come back tomorrow!"
        )
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    if data == "menu_redeem":
        msg = bot.send_message(chat_id, "🎫 Enter your code:")
        bot.register_next_step_handler(msg, process_redeem)
        return
    
    if data == "menu_quests":
        quests = bot_config.get("quests", {})
        invite_q = quests.get("invite", {"target": 5, "reward": 50})
        buy_q = quests.get("buy", {"target": 3, "reward": 100})
        points_q = quests.get("points", {"target": 500, "reward": 150})
        
        inv_count = u.get("invite_count", 0) or 0
        buy_count = u.get("purchases_count", 0) or 0
        acc_points = u.get("accumulated_points", 0) or 0
        
        completed_quests = u.get("completed_quests", []) or []
        
        def quest_status(qid, current, target):
            if qid in completed_quests:
                return "✅"
            return f"{current}/{target}"
        
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ 🔥 QUESTS ║\n"
            f"╚═══════════════════════╝\n\n"
            f"1️⃣ 👥 Invite {invite_q['target']} friends\n"
            f"   Progress: {quest_status('invite', inv_count, invite_q['target'])}\n"
            f"   🎁 Reward: {invite_q['reward']} 💎\n\n"
            f"2️⃣ 🛒 Make {buy_q['target']} purchases\n"
            f"   Progress: {quest_status('buy', buy_count, buy_q['target'])}\n"
            f"   🎁 Reward: {buy_q['reward']} 💎\n\n"
            f"3️⃣ 💎 Earn {points_q['target']} points\n"
            f"   Progress: {quest_status('points', acc_points, points_q['target'])}\n"
            f"   🎁 Reward: {points_q['reward']} 💎"
        )
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    if data == "menu_flash":
        fs = get_active_flash_sale()
        if fs:
            remaining = format_time_remaining(fs["expires"])
            msg = (
                f"⚡⚡⚡ FLASH SALE ACTIVE! ⚡⚡⚡\n\n"
                f"📦 Product: {fs['product']}\n"
                f"🔥 Discount: {fs['discount']}% OFF!\n"
                f"⏰ Ends in: {remaining}\n\n"
                f"💨 Don't miss it!"
            )
        else:
            msg = "📭 No active flash sales right now.\n\n💡 Check back later!"
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎮 قائمة الترفيه
    # ═══════════════════════════════════════════════════════════════════════
    if data == "menu_lootbox":
        price = bot_config.get("lootbox_price", 50)
        chance = bot_config.get("lootbox_chance", 25)
        points = u.get("points", 0) or 0
        
        if points < price:
            bot.answer_callback_query(call.id, f"❌ Need {price} 💎", show_alert=True)
            return
        
        update_user_data(uid, points=-price)
        
        # لعب اللعبة
        animation = ["🎰 Rolling...", "🎲 ...", "⚡ ..."]
        for frame in animation:
            try:
                bot.edit_message_text(frame, chat_id, msg_id, parse_mode="HTML")
                time.sleep(0.4)
            except:
                pass
        
        if random.randint(1, 100) <= chance:
            win = random.choice([50, 100, 150, 200, 300, 500])
            update_user_data(uid, points=win, accumulated_points=win)
            update_user_rank_and_quests(uid)
            msg = (
                f"╔═══════════════════════╗\n"
                f"║ 🎉 YOU WON! 🎉 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"💎 Prize: +{win}\n"
                f"💰 New balance: {u.get('points', 0) - price + win}"
            )
        else:
            msg = (
                f"╔═══════════════════════╗\n"
                f"║ 😔 NO LUCK ║\n"
                f"╚═══════════════════════╝\n\n"
                f"💔 Better luck next time!\n"
                f"💰 Balance: {u.get('points', 0) - price}"
            )
        
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(f"🔄 Try Again ({price} 💎)", callback_data="menu_lootbox"))
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "menu_wheel":
        price = bot_config.get("wheel_price", 40)
        points = u.get("points", 0) or 0
        
        if points < price:
            bot.answer_callback_query(call.id, f"❌ Need {price} 💎", show_alert=True)
            return
        
        update_user_data(uid, points=-price)
        
        # أنيميشن العجلة
        wheel_frames = ["🎡", "🎰", "⭐", "🔥", "💎", "🎁"]
        for frame in wheel_frames:
            try:
                bot.edit_message_text(f"{frame} Spinning...", chat_id, msg_id, parse_mode="HTML")
                time.sleep(0.3)
            except:
                pass
        
        # النتائج المحتملة
        outcomes = [
            (5, "5 💎", 40),
            (10, "10 💎", 25),
            (25, "25 💎", 15),
            (50, "50 💎", 10),
            (100, "100 💎", 5),
            (0, "💔 Nothing", 5)
        ]
        
        # اختيار النتيجة
        roll = random.randint(1, 100)
        cumulative = 0
        win_amount = 0
        win_text = ""
        
        for amount, text, prob in outcomes:
            cumulative += prob
            if roll <= cumulative:
                win_amount = amount
                win_text = text
                break
        
        if win_amount > 0:
            update_user_data(uid, points=win_amount, accumulated_points=win_amount)
            update_user_rank_and_quests(uid)
        
        new_balance = (u.get("points", 0) or 0) - price + win_amount
        
        if win_amount > 0:
            msg = (
                f"╔═══════════════════════╗\n"
                f"║ 🎡 WHEEL RESULT 🎡 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"🎁 You won: {win_text}\n"
                f"💰 Balance: {new_balance}"
            )
        else:
            msg = (
                f"╔═══════════════════════╗\n"
                f"║ 🎡 WHEEL RESULT 🎡 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"😔 {win_text}\n"
                f"💰 Balance: {new_balance}"
            )
        
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(f"🔄 Spin Again ({price} 💎)", callback_data="menu_wheel"))
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 💬 قائمة الدعم
    # ═══════════════════════════════════════════════════════════════════════
    if data == "menu_new_ticket":
        try:
            bot.edit_message_text(
                f"🎫 {t(lang, 'select_category')}",
                chat_id, msg_id,
                reply_markup=get_ticket_categories(lang), parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("tcat_"):
        cat = data.split("_")[1]
        if "temp_ticket_cat" not in bot_config:
            bot_config["temp_ticket_cat"] = {}
        bot_config["temp_ticket_cat"][uid] = cat
        save_json(DB_CONFIG, bot_config)
        
        cat_name = TICKET_CATEGORIES.get(cat, {}).get(lang, "Other")
        msg = bot.send_message(chat_id, f"📝 {t(lang, 'describe_issue', category=cat_name)}")
        bot.register_next_step_handler(msg, process_new_ticket)
        return
    
    if data == "back_support":
        try:
            bot.edit_message_text(
                f"{t(lang, 'support_title')}\n\n{t(lang, 'support_desc')}",
                chat_id, msg_id,
                reply_markup=get_support_menu(lang), parse_mode="HTML")
        except:
            pass
        return
    
    if data == "menu_my_tickets":
        tickets = bot_config.get("tickets", {})
        user_tickets = {k: v for k, v in tickets.items() if v.get("uid") == uid}
        
        if not user_tickets:
            bot.answer_callback_query(call.id, "📭 No tickets", show_alert=True)
            return
        
        msg = f"📋 ━━ Your Tickets ━━\n\n"
        for tid, tdata in list(user_tickets.items())[:10]:
            status = "🟢 Open" if tdata.get("status") == "open" else "🔴 Closed"
            cat = TICKET_CATEGORIES.get(tdata.get("category", "other"), {}).get(lang, "Other")
            msg += f"🎫 #{tid} | {status} | {cat}\n"
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    if data == "menu_request_product":
        msg = bot.send_message(chat_id, "📝 What product would you like us to add?")
        bot.register_next_step_handler(msg, process_product_request)
        return
    
    if data == "menu_faq":
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ ❓ FAQ ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🔹 How to earn points?\n"
            f"   • Daily bonus ✨\n"
            f"   • Invite friends 👥\n"
            f"   • Complete quests 🔥\n\n"
            f"🔹 How to buy?\n"
            f"   • Go to Shop 🛒\n"
            f"   • Select product\n"
            f"   • Pay with points\n\n"
            f"🔹 Need help?\n"
            f"   • Open a ticket 🎫"
        )
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, parse_mode="HTML")
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # ⚙️ قائمة الإعدادات
    # ═══════════════════════════════════════════════════════════════════════
    if data == "menu_lang":
        try:
            bot.edit_message_text(
                "🌐 Select Language:",
                chat_id, msg_id,
                reply_markup=get_lang_inline(), parse_mode="HTML")
        except:
            pass
        return
    
    if data == "menu_notif":
        current = u.get("notifications_on", True)
        update_user_data(uid, notifications_on=not current)
        new_status = "OFF" if current else "ON"
        bot.answer_callback_query(call.id, f"🔔 Notifications: {new_status}", show_alert=True)
        # تحديث الكيبورد
        try:
            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=get_settings_menu(lang, get_user(uid) or {}))
        except:
            pass
        return
    
    if data == "menu_theme":
        if BOT7_LOADED:
            from bot7 import create_theme_selector_inline
            try:
                bot.edit_message_text(
                    "🎨 Select Theme:",
                    chat_id, msg_id,
                    reply_markup=create_theme_selector_inline(), parse_mode="HTML")
            except:
                pass
        else:
            bot.answer_callback_query(call.id, "🎨 Themes coming soon!", show_alert=True)
        return
    
    if data == "menu_privacy":
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ 🔒 PRIVACY ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🔹 We only store:\n"
            f"   • Your Telegram ID\n"
            f"   • Username (public)\n"
            f"   • Points & purchases\n\n"
            f"🔹 We never share your data\n"
            f"🔹 You can delete your data anytime"
        )
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "menu_about":
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ ℹ️ ABOUT ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🤖 EVE Store Bot v3.0\n\n"
            f"💻 Developer: @fkLJh00302\n"
            f"📅 Version: 3.0\n\n"
            f"🔧 Features:\n"
            f"├── 🛍️ Digital Store\n"
            f"├── 🎮 Mini Games\n"
            f"├── 👑 VIP System\n"
            f"├── 🛡️ Smart Shield\n"
            f"└── 🎨 Premium UI"
        )
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            pass
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🛍️ المتجر
    # ═══════════════════════════════════════════════════════════════════════
    if data.startswith("shop_"):
        prod = data.split("_", 1)[1]
        if prod not in prices_config:
            bot.answer_callback_query(call.id, "❌ Product not found", show_alert=True)
            return
        
        points = u.get("points", 0) or 0
        rank_disc = u.get("rank_discount", 0.0) or 0.0
        global_disc = bot_config.get("discount", 0)
        
        # فحص العروض الخاطفة
        fs = get_active_flash_sale()
        fs_disc = 0
        if fs and fs.get("product") == prod:
            fs_disc = fs.get("discount", 0)
        
        total_disc = global_disc + fs_disc
        
        msg = (
            f"📦 ━━ {prod} ━━\n\n"
            f"💰 Your balance: {points} 💎\n"
            f"🎯 Your discount: {int(rank_disc * 100)}%\n"
        )
        
        if total_disc > 0:
            msg += f"🔥 Sale discount: {total_disc}%\n"
        
        msg += "\n⏱️ Select duration:"
        
        m = types.InlineKeyboardMarkup(row_width=1)
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_price = prices_config[prod].get(plan, 0)
            final_price = int(base_price * (1 - total_disc/100) * (1 - rank_disc))
            stock = len(keys_store.get(prod, {}).get(plan, []))
            
            if stock > 0:
                status = "✅"
                cb = f"buy_plan|{prod}|{plan}"
            else:
                status = "❌"
                cb = "shop_nostock"
            
            btn_text = f"{status} ⏱️ {plan} → {final_price} 💎 ({stock})"
            m.add(types.InlineKeyboardButton(btn_text, callback_data=cb))
        
        m.add(types.InlineKeyboardButton("🔙 Back", callback_data="shop_back"))
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "shop_back":
        show_shop_inline(chat_id, msg_id, uid, u, lang)
        return
    
    if data == "shop_nostock":
        bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎁 Giveaway - كابتشا
    # ═══════════════════════════════════════════════════════════════════════
    if data.startswith("gwcap_"):
        answer = data.replace("gwcap_", "")
        status, code = verify_giveaway_captcha(uid, answer)
        
        if status == "correct":
            success, result = process_giveaway_claim(uid, code)
            if success:
                bot.answer_callback_query(call.id, "✅ Correct!", show_alert=False)
                msg = format_giveaway_win_message(result, lang)
                try:
                    bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
                except:
                    bot.send_message(chat_id, msg, parse_mode="HTML")
            else:
                error_msg = format_giveaway_error(result, lang)
                try:
                    bot.edit_message_text(error_msg, chat_id, msg_id, parse_mode="HTML")
                except:
                    bot.send_message(chat_id, error_msg, parse_mode="HTML")
        elif status == "wrong":
            bot.answer_callback_query(call.id, "❌ Wrong! Try again", show_alert=True)
        elif status == "banned":
            bot.answer_callback_query(call.id, "🚫 Too many attempts!", show_alert=True)
        elif status == "expired":
            bot.answer_callback_query(call.id, "⏰ Expired! Try again", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - المنتجات
    # ═══════════════════════════════════════════════════════════════════════
    if not is_admin(uid, u):
        # باقي الـ callbacks خاصة بالأدمن
        return
    
    if data == "admp_add":
        msg = bot.send_message(chat_id, "📦 Enter product name:")
        bot.register_next_step_handler(msg, admin_add_product)
        return
    
    if data == "admp_del":
        if not prices_config:
            bot.answer_callback_query(call.id, "❌ No products", show_alert=True)
            return
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"❌ {p}", callback_data=f"admpd_{p}"))
        try:
            bot.edit_message_text("🗑️ Select product to delete:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("admpd_"):
        prod = data.split("_", 1)[1]
        if prod in prices_config:
            del prices_config[prod]
            save_json(DB_PRICES, prices_config)
        if prod in keys_store:
            del keys_store[prod]
            save_json(DB_KEYS, keys_store)
        bot.answer_callback_query(call.id, f"✅ Deleted: {prod}", show_alert=True)
        return
    
    if data == "admp_prices":
        if not prices_config:
            bot.answer_callback_query(call.id, "❌ No products", show_alert=True)
            return
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"💵 {p}", callback_data=f"admppr_{p}"))
        try:
            bot.edit_message_text("💵 Select product:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("admppr_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            current = prices_config.get(prod, {}).get(plan, 0)
            m.add(types.InlineKeyboardButton(f"⏱️ {plan} = {current}", callback_data=f"admppl_{prod}|{plan}"))
        try:
            bot.edit_message_text(f"📦 {prod}\n\nSelect plan to edit:", chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admppl_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        msg = bot.send_message(chat_id, f"💵 New price for {prod} / {plan}:")
        bot.register_next_step_handler(msg, lambda m: admin_save_price(m, prod, plan))
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - المفاتيح
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admk_add":
        if not prices_config:
            bot.answer_callback_query(call.id, "❌ Add products first", show_alert=True)
            return
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admkp_{p}"))
        try:
            bot.edit_message_text("🔑 Select product:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("admkp_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            m.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"admkpl_{prod}|{plan}"))
        try:
            bot.edit_message_text(f"📦 {prod}\n\nSelect plan:", chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admkpl_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        msg = bot.send_message(chat_id, f"🔑 Send keys (one per line) for {prod} / {plan}:")
        bot.register_next_step_handler(msg, lambda m: admin_save_keys(m, prod, plan))
        return
    
    if data == "admk_view":
        if not keys_store:
            return bot.answer_callback_query(call.id, "📭 No keys", show_alert=True)
        
        msg = "🔑 ━━ Keys Stock ━━\n\n"
        for prod, plans in keys_store.items():
            msg += f"📦 {prod}\n"
            for plan, keys in plans.items():
                msg += f"   ├ {plan}: {len(keys)}\n"
            msg += "\n"
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "admk_del":
        if not prices_config:
            return bot.answer_callback_query(call.id, "❌ No products", show_alert=True)
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admkdel_{p}"))
        try:
            bot.edit_message_text("🔢 Select product:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("admkdel_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            cnt = len(keys_store.get(prod, {}).get(plan, []))
            m.add(types.InlineKeyboardButton(f"⏱️ {plan} ({cnt})", callback_data=f"admkdelp_{prod}|{plan}"))
        try:
            bot.edit_message_text(f"📦 {prod}", chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admkdelp_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        keys = keys_store.get(prod, {}).get(plan, [])
        if not keys:
            return bot.answer_callback_query(call.id, "❌ No keys", show_alert=True)
        msg = bot.send_message(chat_id, "🔢 Key or number to delete:")
        bot.register_next_step_handler(msg, lambda m: admin_del_key(m, prod, plan))
        return
    
    if data == "admk_clear":
        keys_store.clear()
        for p in prices_config.keys():
            keys_store[p] = {"1 Day": [], "7 Days": [], "30 Days": []}
        save_json(DB_KEYS, keys_store)
        return bot.answer_callback_query(call.id, "🗑️ All keys cleared!", show_alert=True)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - الأعضاء
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admm_view":
        msg = bot.send_message(chat_id, "👤 Enter user ID:")
        bot.register_next_step_handler(msg, admin_view_member)
        return
    
    if data == "admm_charge":
        msg = bot.send_message(chat_id, "💰 Send: <code>ID AMOUNT</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, admin_charge_member)
        return
    
    if data.startswith("admbanuser_"):
        parts = data.split("_")
        target = parts[1]
        action = parts[2]
        
        if action == "perm":
            update_user_data(target, banned=True)
            bot.answer_callback_query(call.id, f"⛔ Banned permanently!", show_alert=True)
        elif action == "temp":
            until = (datetime.now() + timedelta(hours=24)).isoformat()
            update_user_data(target, banned_until=until)
            bot.answer_callback_query(call.id, f"⏱️ Banned for 24h!", show_alert=True)
        elif action == "demote":
            update_user_data(target, is_admin=False)
            bot.answer_callback_query(call.id, f"⬇️ Admin removed!", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - المبيعات
    # ═══════════════════════════════════════════════════════════════════════
    if data == "adms_code":
        msg = bot.send_message(chat_id, "🎫 Send: <code>CODE VALUE</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, admin_create_code)
        return
    
    if data == "adms_discount":
        msg = bot.send_message(chat_id, "🔥 Discount percentage (0-99):")
        bot.register_next_step_handler(msg, admin_set_discount)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - التسويق
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admmk_broadcast":
        msg = bot.send_message(chat_id, "📢 Enter broadcast message:")
        bot.register_next_step_handler(msg, admin_broadcast)
        return
    
    if data == "admmk_prices":
        if not prices_config:
            return bot.answer_callback_query(call.id, "❌ No products", show_alert=True)
        if publish_prices_to_channel(prices_config, bot_config.get("discount", 0)):
            bot.answer_callback_query(call.id, "✅ Published!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Failed", show_alert=True)
        return
    
    if data == "admmk_fake":
        if publish_fake_marketing():
            bot.answer_callback_query(call.id, "✅ Published!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Failed", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - العروض الخاطفة
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admf_create":
        if not prices_config:
            return bot.answer_callback_query(call.id, "❌ No products", show_alert=True)
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admfsel_{p}"))
        try:
            bot.edit_message_text("⚡ Select product:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("admfsel_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup(row_width=3)
        m.add(
            types.InlineKeyboardButton("20%", callback_data=f"admfdisc_{prod}|20"),
            types.InlineKeyboardButton("30%", callback_data=f"admfdisc_{prod}|30"),
            types.InlineKeyboardButton("50%", callback_data=f"admfdisc_{prod}|50")
        )
        m.add(
            types.InlineKeyboardButton("60%", callback_data=f"admfdisc_{prod}|60"),
            types.InlineKeyboardButton("70%", callback_data=f"admfdisc_{prod}|70"),
            types.InlineKeyboardButton("80%", callback_data=f"admfdisc_{prod}|80")
        )
        try:
            bot.edit_message_text(f"⚡ {prod}\nSelect discount:", chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admfdisc_"):
        _, rest = data.split("_", 1)
        prod, discount = rest.split("|")
        m = types.InlineKeyboardMarkup(row_width=3)
        m.add(
            types.InlineKeyboardButton("1h", callback_data=f"admfhr_{prod}|{discount}|1"),
            types.InlineKeyboardButton("3h", callback_data=f"admfhr_{prod}|{discount}|3"),
            types.InlineKeyboardButton("6h", callback_data=f"admfhr_{prod}|{discount}|6")
        )
        m.add(
            types.InlineKeyboardButton("12h", callback_data=f"admfhr_{prod}|{discount}|12"),
            types.InlineKeyboardButton("24h", callback_data=f"admfhr_{prod}|{discount}|24")
        )
        try:
            bot.edit_message_text(f"⚡ {prod} - {discount}%\nSelect duration:", chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admfhr_"):
        _, rest = data.split("_", 1)
        parts = rest.split("|")
        prod, discount, hours = parts[0], int(parts[1]), int(parts[2])
        
        expires = create_flash_sale(prod, discount, hours)
        publish_flash_sale_to_channel(prod, discount, hours)
        
        # إرسال للمستخدمين
        sent = 0
        for u_id in get_all_user_ids():
            try:
                u_info = get_user(u_id) or {}
                if u_info.get("notifications_on", True):
                    u_lang = u_info.get("lang", "ar")
                    bot.send_message(int(u_id),
                        t(u_lang, "flash_sale_active", discount=discount, product=prod, remaining=f"{hours}h"),
                        parse_mode="HTML")
                    sent += 1
                    time.sleep(0.05)
            except:
                pass
        
        try:
            bot.edit_message_text(
                f"✅ FLASH SALE ON!\n📦 {prod}\n🔥 {discount}%\n⏰ {hours}h\n🔔 {sent} users notified",
                chat_id, msg_id, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "admf_cancel":
        if "flash_sales" in bot_config:
            bot_config["flash_sales"]["current"] = None
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ Cancelled", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - Giveaway
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admgw_create":
        m = giveaway_reward_menu()
        try:
            bot.edit_message_text("🎁 Select reward amount:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("gwrew_"):
        val = data.split("_")[1]
        if val == "custom":
            msg = bot.send_message(chat_id, "💎 Enter custom reward:")
            bot.register_next_step_handler(msg, lambda m: process_gw_custom_reward(m, uid, chat_id))
            return
        
        temp_giveaway_setup[uid] = {"reward": int(val)}
        m = giveaway_users_menu()
        try:
            bot.edit_message_text(f"🎁 Reward: {val}\n\n👥 Select max winners:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("gwusr_"):
        val = data.split("_")[1]
        if val == "custom":
            msg = bot.send_message(chat_id, "👥 Enter max users:")
            bot.register_next_step_handler(msg, lambda m: process_gw_custom_users(m, uid, chat_id))
            return
        
        if uid not in temp_giveaway_setup:
            return
        temp_giveaway_setup[uid]["max_users"] = int(val)
        m = giveaway_hours_menu()
        try:
            bot.edit_message_text(
                f"🎁 Reward: {temp_giveaway_setup[uid]['reward']}\n"
                f"👥 Winners: {val}\n\n"
                f"⏰ Select duration:",
                chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("gwhr_"):
        val = data.split("_")[1]
        if uid not in temp_giveaway_setup:
            return
        
        hours = int(val)
        setup = temp_giveaway_setup[uid]
        reward = setup["reward"]
        max_users = setup["max_users"]
        
        code = create_giveaway(reward, max_users, hours)
        msg_id_channel = publish_giveaway_to_channel(code)
        
        del temp_giveaway_setup[uid]
        
        try:
            bot_user = bot.get_me().username
        except:
            bot_user = "bot"
        
        link = f"https://t.me/{bot_user}?start=gw_{code}"
        
        try:
            bot.edit_message_text(
                f"╔═══════════════════════╗\n"
                f"║ ✅ GIVEAWAY CREATED! ║\n"
                f"╚═══════════════════════╝\n\n"
                f"🔗 Code: <code>{code}</code>\n"
                f"💎 Reward: {reward}\n"
                f"👥 Winners: {max_users}\n"
                f"⏰ Duration: {hours}h\n\n"
                f"📎 Link:\n<code>{link}</code>",
                chat_id, msg_id, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "admgw_list":
        gws = get_all_giveaways()
        active = {k: v for k, v in gws.items() if v.get("status") == "active"}
        
        if not active:
            bot.answer_callback_query(call.id, "📭 No active giveaways", show_alert=True)
            return
        
        msg = "🎁 ━━ Active Giveaways ━━\n\n"
        for code, gw in active.items():
            claimed = len(gw.get("claimed_by", []))
            msg += f"🔗 {code}\n"
            msg += f"   💎 {gw['reward']} | 👥 {claimed}/{gw['max_users']}\n\n"
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "admgw_cancel":
        gws = get_all_giveaways()
        active = {k: v for k, v in gws.items() if v.get("status") == "active"}
        
        if not active:
            bot.answer_callback_query(call.id, "📭 No active giveaways", show_alert=True)
            return
        
        m = types.InlineKeyboardMarkup()
        for code in active.keys():
            m.add(types.InlineKeyboardButton(f"❌ {code}", callback_data=f"gwcancel_{code}"))
        
        try:
            bot.edit_message_text("Select giveaway to cancel:", chat_id, msg_id, reply_markup=m)
        except:
            pass
        return
    
    if data.startswith("gwcancel_"):
        code = data.split("_")[1]
        if cancel_giveaway(code):
            bot.answer_callback_query(call.id, f"✅ Cancelled: {code}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Not found", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - رسائل القناة
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admch_styled":
        last_channel_msgs[uid] = "send_styled"
        msg = bot.send_message(chat_id, "📝 Enter styled message:")
        return
    
    if data == "admch_raw":
        last_channel_msgs[uid] = "send_raw"
        msg = bot.send_message(chat_id, "📝 Enter raw message (with HTML):")
        return
    
    if data == "admch_delete":
        last_channel_msgs[uid] = "delete_msg"
        msg = bot.send_message(chat_id, "🆔 Enter message ID to delete:")
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - الألعاب
    # ═══════════════════════════════════════════════════════════════════════
    if data == "admg_lootbox":
        return show_lootbox_settings(chat_id, msg_id)
    
    if data == "admg_wheel":
        return show_wheel_settings(chat_id, msg_id)
    
    if data == "admg_quests":
        return show_quests_settings(chat_id, msg_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - النظام
    # ═══════════════════════════════════════════════════════════════════════
    if data == "adsys_daily":
        msg = bot.send_message(chat_id, f"✨ Current: {bot_config.get('daily_gift', 10)}\n\nNew value:")
        bot.register_next_step_handler(msg, admin_edit_daily)
        return
    
    if data == "adsys_invite":
        msg = bot.send_message(chat_id, f"🔗 Current: {bot_config.get('invite_reward', 20)}\n\nNew value:")
        bot.register_next_step_handler(msg, admin_edit_invite)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - التذاكر
    # ═══════════════════════════════════════════════════════════════════════
    if data.startswith("admviewtick_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid not in tickets:
            return bot.answer_callback_query(call.id, "❌ Not found", show_alert=True)
        
        tdata = tickets[tid]
        tu = get_user(tdata.get("uid", "")) or {}
        
        msg = (
            f"🎫 ━━ Ticket #{tid} ━━\n\n"
            f"👤 User: @{tu.get('username', 'N/A')}\n"
            f"🆔 ID: {tdata.get('uid')}\n"
            f"📂 Category: {tdata.get('category')}\n"
            f"📝 Message:\n{tdata.get('text', '')}\n"
        )
        
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💬 Start Chat", callback_data=f"admchat_{tid}"))
        m.add(types.InlineKeyboardButton("🔒 Close", callback_data=f"admclosetick_{tid}"))
        
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admchat_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid not in tickets:
            return bot.answer_callback_query(call.id, "❌ Not found", show_alert=True)
        
        user_uid = tickets[tid].get("uid")
        admin_ticket_chats[uid] = {"ticket_id": tid, "user_uid": user_uid}
        active_ticket_chats[user_uid] = tid
        
        bot.answer_callback_query(call.id, "💬 Chat started! Type to reply.", show_alert=True)
        
        try:
            bot.send_message(int(user_uid),
                f"╔═══════════════════════╗\n"
                f"║ 💬 LIVE SUPPORT ║\n"
                f"╚═══════════════════════╝\n\n"
                f"🎫 Ticket #{tid}\n"
                f"👨‍💻 Admin is now responding\n\n"
                f"💡 Type your message\n"
                f"🔒 /close to end chat",
                parse_mode="HTML")
        except:
            pass
        return
    
    if data.startswith("admclosetick_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid in tickets:
            tickets[tid]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
            
            user_uid = tickets[tid].get("uid")
            active_ticket_chats.pop(user_uid, None)
            
            try:
                bot.send_message(int(user_uid),
                    f"🔒 Ticket #{tid} closed by admin",
                    parse_mode="HTML")
            except:
                pass
        
        bot.answer_callback_query(call.id, f"✅ Ticket #{tid} closed", show_alert=True)
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔴 أدمن - إعدادات الألعاب
    # ═══════════════════════════════════════════════════════════════════════
    if data.startswith("cfg_"):
        return handle_cfg_callback(call, data, chat_id, msg_id, uid, u)

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ إعدادات الألعاب
# ═══════════════════════════════════════════════════════════════════════════

def handle_cfg_callback(call, data, chat_id, msg_id, uid, u):
    """معالجة إعدادات الألعاب"""
    if not is_admin(uid, u):
        return bot.answer_callback_query(call.id, "❌", show_alert=True)
    
    if data.startswith("cfg_q_"):
        parts = data.split("_")
        tt, ft, ac = parts[2], parts[3], parts[4]
        tk = "invite" if tt == "inv" else ("buy" if tt == "buy" else "points")
        fk = "target" if ft == "t" else "reward"
        
        step = 1
        if tk == "points" and fk == "target":
            step = 250
        elif tk == "points" and fk == "reward":
            step = 50
        elif fk == "reward":
            step = 10
        
        if ac == "up":
            bot_config["quests"][tk][fk] += step
        else:
            bot_config["quests"][tk][fk] = max(1, bot_config["quests"][tk][fk] - step)
        
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅")
        return show_quests_settings(chat_id, msg_id)
    
    if data.startswith("cfg_box_") or data.startswith("cfg_wheel_"):
        if data == "cfg_box_price_up":
            bot_config["lootbox_price"] = bot_config.get("lootbox_price", 50) + 5
        elif data == "cfg_box_price_down":
            bot_config["lootbox_price"] = max(5, bot_config.get("lootbox_price", 50) - 5)
        elif data == "cfg_box_chance_up":
            bot_config["lootbox_chance"] = min(100, bot_config.get("lootbox_chance", 25) + 5)
        elif data == "cfg_box_chance_down":
            bot_config["lootbox_chance"] = max(1, bot_config.get("lootbox_chance", 25) - 5)
        elif data == "cfg_wheel_price_up":
            bot_config["wheel_price"] = bot_config.get("wheel_price", 40) + 5
        elif data == "cfg_wheel_price_down":
            bot_config["wheel_price"] = max(5, bot_config.get("wheel_price", 40) - 5)
        elif data == "cfg_wheel_chance_up":
            bot_config["wheel_chance"] = min(100, bot_config.get("wheel_chance", 5) + 1)
        elif data == "cfg_wheel_chance_down":
            bot_config["wheel_chance"] = max(1, bot_config.get("wheel_chance", 5) - 1)
        
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅")
        
        if "box" in data:
            return show_lootbox_settings(chat_id, msg_id)
        else:
            return show_wheel_settings(chat_id, msg_id)

def show_lootbox_settings(chat_id, msg_id=None):
    """عرض إعدادات صندوق الحظ"""
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    
    msg = f"🎰 ━━ Loot Box Settings ━━\n\n💸 Price: {price}\n📊 Chance: {chance}%"
    
    m = types.InlineKeyboardMarkup()
    m.row(
        types.InlineKeyboardButton("➕ Price", callback_data="cfg_box_price_up"),
        types.InlineKeyboardButton("➖ Price", callback_data="cfg_box_price_down")
    )
    m.row(
        types.InlineKeyboardButton("📈 Chance", callback_data="cfg_box_chance_up"),
        types.InlineKeyboardButton("📉 Chance", callback_data="cfg_box_chance_down")
    )
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_wheel_settings(chat_id, msg_id=None):
    """عرض إعدادات عجلة الحظ"""
    price = bot_config.get("wheel_price", 40)
    chance = bot_config.get("wheel_chance", 5)
    
    msg = f"🎡 ━━ Wheel Settings ━━\n\n💸 Price: {price}\n📊 Jackpot: {chance}%"
    
    m = types.InlineKeyboardMarkup()
    m.row(
        types.InlineKeyboardButton("➕ Price", callback_data="cfg_wheel_price_up"),
        types.InlineKeyboardButton("➖ Price", callback_data="cfg_wheel_price_down")
    )
    m.row(
        types.InlineKeyboardButton("📈 Chance", callback_data="cfg_wheel_chance_up"),
        types.InlineKeyboardButton("📉 Chance", callback_data="cfg_wheel_chance_down")
    )
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_quests_settings(chat_id, msg_id=None):
    """عرض إعدادات المهام"""
    q = bot_config.get("quests", {
        "invite": {"target": 5, "reward": 50},
        "buy": {"target": 3, "reward": 100},
        "points": {"target": 500, "reward": 150}
    })
    
    msg = (
        f"🔥 ━━ Quests Settings ━━\n\n"
        f"1️⃣ 👥 Invites: {q['invite']['target']} / +{q['invite']['reward']}\n"
        f"2️⃣ 🛒 Purchases: {q['buy']['target']} / +{q['buy']['reward']}\n"
        f"3️⃣ 💎 Points: {q['points']['target']} / +{q['points']['reward']}"
    )
    
    m = types.InlineKeyboardMarkup()
    m.row(
        types.InlineKeyboardButton("👥 -", callback_data="cfg_q_inv_t_down"),
        types.InlineKeyboardButton("👥 +", callback_data="cfg_q_inv_t_up")
    )
    m.row(
        types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_inv_r_down"),
        types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_inv_r_up")
    )
    m.row(
        types.InlineKeyboardButton("🛒 -", callback_data="cfg_q_buy_t_down"),
        types.InlineKeyboardButton("🛒 +", callback_data="cfg_q_buy_t_up")
    )
    m.row(
        types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_buy_r_down"),
        types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_buy_r_up")
    )
    m.row(
        types.InlineKeyboardButton("💎 -", callback_data="cfg_q_pts_t_down"),
        types.InlineKeyboardButton("💎 +", callback_data="cfg_q_pts_t_up")
    )
    m.row(
        types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_pts_r_down"),
        types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_pts_r_up")
    )
    
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 📝 دوال المعالجة
# ═══════════════════════════════════════════════════════════════════════════

def show_shop_inline(chat_id, msg_id, uid, u, lang):
    """عرض المتجر inline"""
    if not prices_config:
        return
    
    points = u.get("points", 0) or 0
    rank_disc = u.get("rank_discount", 0.0) or 0.0
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 🛍️ SHOP ║\n"
        f"╚═══════════════════════╝\n\n"
        f"💰 Balance: {points} 💎\n\n"
        f"👇 Select product:"
    )
    
    m = types.InlineKeyboardMarkup(row_width=1)
    for prod in prices_config.keys():
        total_stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        status = "✅" if total_stock > 0 else "❌"
        m.add(types.InlineKeyboardButton(f"{status} 📦 {prod} ({total_stock})", callback_data=f"shop_{prod}"))
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except:
        pass

def process_redeem(message):
    """معالجة استرداد الكود"""
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    code = message.text.strip()
    
    if code in redeem_codes:
        added = redeem_codes.pop(code)
        update_user_data(uid, points=added, accumulated_points=added)
        save_json(DB_REDEEM, redeem_codes)
        update_user_rank_and_quests(uid)
        bot.send_message(message.chat.id,
            f"╔═══════════════════════╗\n"
            f"║ 🎉 CODE VALID! ║\n"
            f"╚═══════════════════════╝\n\n"
            f"💎 +{added} points!",
            parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Invalid or used code")

def process_new_ticket(message):
    """معالجة تذكرة جديدة"""
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    txt = message.text.strip() if message.text else ""
    
    if not txt:
        return
    
    temp = bot_config.get("temp_ticket_cat", {})
    cat_key = temp.get(uid, "other")
    cat_name = TICKET_CATEGORIES.get(cat_key, {}).get(lang, "Other")
    
    tid = str(random.randint(10000, 99999))
    
    if "tickets" not in bot_config:
        bot_config["tickets"] = {}
    
    bot_config["tickets"][tid] = {
        "uid": uid,
        "text": txt,
        "status": "open",
        "category": cat_key,
        "date": datetime.now().isoformat(),
        "messages": []
    }
    
    if uid in temp:
        temp.pop(uid)
    
    save_json(DB_CONFIG, bot_config)
    
    bot.send_message(message.chat.id,
        t(lang, "ticket_created", tid=tid, category=cat_name),
        parse_mode="HTML")
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("💬 Chat", callback_data=f"admchat_{tid}"))
    m.add(types.InlineKeyboardButton("🔒 Close", callback_data=f"admclosetick_{tid}"))
    
    try:
        bot.send_message(ADMIN_PRIMARY,
            f"╔═══════════════════════╗\n"
            f"║ 🎫 NEW TICKET ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🆔 #{tid}\n"
            f"📂 {TICKET_CATEGORIES.get(cat_key, {}).get('ar', 'Other')}\n"
            f"👤 {uid} (@{u.get('username', 'N/A')})\n\n"
            f"💬 {txt}",
            reply_markup=m, parse_mode="HTML")
    except:
        pass

def process_product_request(message):
    """معالجة طلب منتج"""
    uid = str(message.from_user.id)
    txt = message.text.strip() if message.text else ""
    
    if not txt:
        return
    
    rid = str(random.randint(10000, 99999))
    
    if "product_requests" not in bot_config:
        bot_config["product_requests"] = {}
    
    bot_config["product_requests"][rid] = {
        "uid": uid,
        "text": txt,
        "date": datetime.now().isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    
    bot.send_message(message.chat.id,
        f"✅ Request Sent!\n\n🎫 ID: #{rid}",
        parse_mode="HTML")
    
    try:
        bot.send_message(ADMIN_PRIMARY,
            f"💡 Product Request #{rid}\n{uid}\n{txt}",
            parse_mode="HTML")
    except:
        pass

def process_gw_custom_reward(message, uid, chat_id):
    """معالجة مكافأة Giveaway مخصصة"""
    try:
        val = int(message.text.strip())
        if val <= 0:
            raise ValueError
        temp_giveaway_setup[uid] = {"reward": val}
        bot.send_message(chat_id,
            f"🎁 Reward: {val}\n\n👥 Select max winners:",
            reply_markup=giveaway_users_menu(), parse_mode="HTML")
    except:
        bot.send_message(chat_id, "❌ Numbers only")

def process_gw_custom_users(message, uid, chat_id):
    """معالجة عدد مستخدمين Giveaway مخصص"""
    try:
        val = int(message.text.strip())
        if val <= 0:
            raise ValueError
        if uid not in temp_giveaway_setup:
            return
        temp_giveaway_setup[uid]["max_users"] = val
        bot.send_message(chat_id,
            f"🎁 Reward: {temp_giveaway_setup[uid]['reward']}\n"
            f"👥 Winners: {val}\n\n"
            f"⏰ Select duration:",
            reply_markup=giveaway_hours_menu(), parse_mode="HTML")
    except:
        bot.send_message(chat_id, "❌ Numbers only")

# ═══════════════════════════════════════════════════════════════════════════
# 🔴 دوال الأدمن
# ═══════════════════════════════════════════════════════════════════════════

def admin_add_product(message):
    """إضافة منتج جديد"""
    prod = message.text.strip()
    if prod in prices_config:
        return bot.send_message(message.chat.id, "❌ Already exists")
    
    prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
    keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    
    # حفظ في PostgreSQL (bot5)
    if BOT5_LOADED:
        try:
            save_product_db(prod, prices_config[prod])
        except:
            pass
    
    bot.send_message(message.chat.id, f"➕ Added: {prod}", parse_mode="HTML")

def admin_save_price(message, prod, plan):
    """حفظ سعر جديد"""
    try:
        p = int(message.text.strip())
        prices_config[prod][plan] = p
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ {prod}/{plan} = {p}", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Numbers only")

def admin_save_keys(message, prod, plan):
    """حفظ مفاتيح جديدة"""
    keys = message.text.strip().split('\n')
    added = 0
    
    if prod not in keys_store:
        keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ +{added} keys", parse_mode="HTML")

def admin_del_key(message, prod, plan):
    """حذف مفتاح"""
    val = message.text.strip()
    keys = keys_store.get(prod, {}).get(plan, [])
    
    if val.isdigit() and 0 < int(val) <= len(keys):
        rm = keys.pop(int(val) - 1)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ Deleted: {rm}", parse_mode="HTML")
    
    if val in keys:
        keys.remove(val)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, "✅ Deleted")
    
    bot.send_message(message.chat.id, "❌ Not found")

def admin_view_member(message):
    """عرض معلومات عضو"""
    t_id = message.text.strip()
    u = get_user(t_id)
    
    if not u:
        return bot.send_message(message.chat.id, "❌ User not found")
    
    role = "👑 Owner" if int(t_id) == ADMIN_PRIMARY else ("🛡️ Admin" if u.get("is_admin", False) else "👤 User")
    ban = "⛔ Banned" if u.get("banned", False) else "🟢 Active"
    
    # نقاط الثقة (bot6)
    trust = "N/A"
    if BOT6_LOADED:
        try:
            trust = get_trust_score(t_id)
        except:
            pass
    
    msg = (
        f"👤 <code>{t_id}</code>\n"
        f"📝 @{u.get('username', 'N/A')}\n"
        f"💰 {u.get('points', 0)} 💎\n"
        f"🏆 {u.get('rank', 'Member')}\n"
        f"🎖️ {role}\n"
        f"🔴 {ban}\n"
        f"🛡️ Trust: {trust}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    
    if u.get("is_admin", False):
        m.add(types.InlineKeyboardButton("❌ Remove Admin", callback_data=f"admbanuser_{t_id}_demote"))
    
    m.add(
        types.InlineKeyboardButton("⛔ Ban", callback_data=f"admbanuser_{t_id}_perm"),
        types.InlineKeyboardButton("⏱️ 24h", callback_data=f"admbanuser_{t_id}_temp")
    )
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

def admin_charge_member(message):
    """شحن رصيد عضو"""
    try:
        p = message.text.strip().split()
        t_id, pts = p[0], int(p[1])
        
        if get_user(t_id):
            update_user_data(t_id, points=pts, accumulated_points=pts)
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 +{pts} to {t_id}", parse_mode="HTML")
            try:
                bot.send_message(int(t_id), f"🎉 +{pts} 💎 from admin!", parse_mode="HTML")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ User not found")
    except:
        bot.send_message(message.chat.id, "❌ Format: ID AMOUNT")

def admin_create_code(message):
    """إنشاء كود شحن"""
    try:
        p = message.text.strip().split()
        code, pts = p[0], int(p[1])
        redeem_codes[code] = pts
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 {code} = {pts} 💎", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Format: CODE VALUE")

def admin_set_discount(message):
    """تعيين خصم عام"""
    try:
        d = int(message.text.strip())
        if 0 <= d < 100:
            bot_config["discount"] = d
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 Discount → {d}%", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Invalid")

def admin_broadcast(message):
    """إرسال رسالة جماعية"""
    s = 0
    for u_id in get_all_user_ids():
        try:
            u_info = get_user(u_id) or {}
            if u_info.get("notifications_on", True):
                bot.send_message(int(u_id), message.text)
                s += 1
                time.sleep(0.04)
        except:
            pass
    
    bot.send_message(message.chat.id, f"📢 Sent to {s} users", parse_mode="HTML")

def admin_edit_daily(message):
    """تعديل المكافأة اليومية"""
    try:
        v = int(message.text.strip())
        if v >= 0:
            bot_config["daily_gift"] = v
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ Daily: {v}", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Invalid")

def admin_edit_invite(message):
    """تعديل مكافأة الإحالة"""
    try:
        v = int(message.text.strip())
        if v >= 0:
            bot_config["invite_reward"] = v
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ Invite: {v}", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Invalid")

# ═══════════════════════════════════════════════════════════════════════════
# 🎹 قوائم Giveaway
# ═══════════════════════════════════════════════════════════════════════════

def giveaway_reward_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("10", callback_data="gwrew_10"),
        types.InlineKeyboardButton("25", callback_data="gwrew_25"),
        types.InlineKeyboardButton("50", callback_data="gwrew_50")
    )
    m.add(
        types.InlineKeyboardButton("100", callback_data="gwrew_100"),
        types.InlineKeyboardButton("250", callback_data="gwrew_250"),
        types.InlineKeyboardButton("500", callback_data="gwrew_500")
    )
    m.add(types.InlineKeyboardButton("✏️ Custom", callback_data="gwrew_custom"))
    return m

def giveaway_users_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("5", callback_data="gwusr_5"),
        types.InlineKeyboardButton("10", callback_data="gwusr_10"),
        types.InlineKeyboardButton("25", callback_data="gwusr_25")
    )
    m.add(
        types.InlineKeyboardButton("50", callback_data="gwusr_50"),
        types.InlineKeyboardButton("100", callback_data="gwusr_100"),
        types.InlineKeyboardButton("∞", callback_data="gwusr_99999")
    )
    m.add(types.InlineKeyboardButton("✏️ Custom", callback_data="gwusr_custom"))
    return m

def giveaway_hours_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1h", callback_data="gwhr_1"),
        types.InlineKeyboardButton("3h", callback_data="gwhr_3"),
        types.InlineKeyboardButton("6h", callback_data="gwhr_6")
    )
    m.add(
        types.InlineKeyboardButton("12h", callback_data="gwhr_12"),
        types.InlineKeyboardButton("24h", callback_data="gwhr_24"),
        types.InlineKeyboardButton("48h", callback_data="gwhr_48")
    )
    m.add(types.InlineKeyboardButton("72h", callback_data="gwhr_72"))
    return m

def admin_giveaway_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("➕ Create New", callback_data="admgw_create"))
    m.add(types.InlineKeyboardButton("📋 View Active", callback_data="admgw_list"))
    m.add(types.InlineKeyboardButton("❌ Cancel", callback_data="admgw_cancel"))
    return m

def admin_channel_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📝 Styled Message", callback_data="admch_styled"))
    m.add(types.InlineKeyboardButton("📄 Raw Message", callback_data="admch_raw"))
    m.add(types.InlineKeyboardButton("🗑️ Delete Message", callback_data="admch_delete"))
    return m

def admin_system_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✨ Daily Bonus", callback_data="adsys_daily"))
    m.add(types.InlineKeyboardButton("🔗 Invite Reward", callback_data="adsys_invite"))
    return m

def admin_games_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎰 Loot Box", callback_data="admg_lootbox"))
    m.add(types.InlineKeyboardButton("🎡 Lucky Wheel", callback_data="admg_wheel"))
    m.add(types.InlineKeyboardButton("🔥 Quests", callback_data="admg_quests"))
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 التشغيل
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 EVE Store Bot v3.0 - Starting...")
    print("=" * 60)
    print("✅ Database initialized")
    print("✅ bot2.py loaded (Giveaway + VIP + Stars)")
    print("✅ bot3.py loaded (Purchase Fix + Anti-Abuse)")
    print("✅ bot4.py loaded (Mini Games)")
    
    if BOT5_LOADED:
        print("✅ bot5.py loaded (Data Fortress)")
    else:
        print("⚠️ bot5.py not loaded")
    
    if BOT6_LOADED:
        print("✅ bot6.py loaded (Smart Shield)")
    else:
        print("⚠️ bot6.py not loaded")
    
    if BOT7_LOADED:
        print("✅ bot7.py loaded (Premium UI)")
    else:
        print("⚠️ bot7.py not loaded")
    
    print("=" * 60)
    print("💻 Developer: @fkLJh00302")
    print("=" * 60)
    print("🤖 Bot is now RUNNING!")
    print("=" * 60)
    
    bot.infinity_polling(none_stop=True, timeout=60)
