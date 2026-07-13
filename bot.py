import telebot
from telebot import types
import random, os, time
from datetime import datetime, timedelta

from config import (bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK,
                    LOCALES, RANKS, TICKET_CATEGORIES, t)
from database import (engine, text, init_db, get_user, update_user_data, register_user,
                      keys_store, redeem_codes, prices_config, bot_config, save_json,
                      DB_USERS, DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG,
                      update_user_rank_and_quests, get_bot_stats, search_user)
from utils import (check_spam, is_user_banned, check_channel_join, generate_fake_key,
                   trigger_captcha, is_captcha_pending, verify_captcha, require_verification_on_start,
                   active_ticket_chats, admin_ticket_chats, animate_message, can_check_join,
                   publish_sale_to_channel, publish_fake_marketing, publish_prices_to_channel,
                   publish_flash_sale_to_channel, publish_maintenance_notice,
                   get_active_flash_sale, create_flash_sale, format_time_remaining,
                   send_typing_action)
from keyboards import *
import bot3
import bot4
import bot5
import bot6
import bot7
# 🎁 استيراد bot2 (نظام Giveaway ورسائل القناة)
from bot2 import (create_giveaway, get_giveaway, is_giveaway_valid, has_user_claimed_giveaway,
                  claim_giveaway, publish_giveaway_to_channel, start_giveaway_captcha,
                  verify_giveaway_captcha, process_giveaway_claim, get_all_giveaways,
                  cancel_giveaway, send_custom_channel_message, send_raw_channel_message,
                  delete_channel_message, format_giveaway_win_message, format_giveaway_error,
                  get_giveaways_stats)

# =====================================================
# 🚀 تهيئة قاعدة البيانات
# =====================================================
init_db()

# متغير مؤقت لتخزين إعدادات giveaway قيد الإنشاء
temp_giveaway_setup = {}

# متغير مؤقت لتخزين آخر رسائل القناة
last_channel_msgs = {}

# =====================================================
# 🔧 دوال مساعدة
# =====================================================
def is_admin(uid, u=None):
    if u is None:
        u = get_user(uid) or {}
    return int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False)

def get_all_user_ids():
    with engine.connect() as conn:
        return [str(r[0]) for r in conn.execute(text("SELECT uid FROM users")).fetchall()]

def enforce_subscription(message, lang="ar"):
    uid = str(message.from_user.id)
    if not check_channel_join(uid):
        msg = (
            f"╔═══════════════════╗\n"
            f"║ 🔐 <b>JOIN REQUIRED</b> 🔐 ║\n"
            f"╚═══════════════════╝\n\n"
            f"⚠️ You must join our channel to use this bot!\n\n"
            f"📢 <b>Simple Steps:</b>\n"
            f"1️⃣ Click <b>«Join Our Channel»</b> below\n"
            f"2️⃣ Press <b>«Join»</b> in Telegram\n"
            f"3️⃣ Come back & press <b>«Verify»</b>\n\n"
            f"🎁 <i>Unlock all features after joining!</i>"
        )
        try:
            bot.send_message(message.chat.id, msg,
                reply_markup=get_join_inline(lang), parse_mode="HTML")
        except: pass
        return False
    return True

# =====================================================
# 🎯 معالج الأوامر
# =====================================================
@bot.message_handler(commands=['start', 'id', 'close', 'end', 'help'])
def handle_commands(message):
    uid = str(message.from_user.id)
    allowed, shield_msg, needs_captcha = bot6.shield_check(uid, "command")
    if not allowed:
        return bot.send_message(message.chat.id, shield_msg, parse_mode="HTML")
    if needs_captcha:
        u = get_user(uid) or {}
        return bot6.send_shield_captcha(message.chat.id, uid, u.get("lang", "ar"))
    if check_spam(uid):
        return
    register_user(message.from_user)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    # ═══════════════════════════
    # 🔒 إغلاق دردشة التذكرة
    # ═══════════════════════════
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
                        bot.send_message(int(adm_uid),
                            f"🔒 <b>Ticket #{tid} closed by user</b>", parse_mode="HTML")
                    except: pass
            bot.send_message(message.chat.id,
                f"╔═══════════════════╗\n"
                f"║  🔒 <b>CHAT ENDED</b>  ║\n"
                f"╚═══════════════════╝\n\n"
                f"✅ Ticket <code>#{tid}</code> closed successfully!\n"
                f"💬 <i>Thank you for contacting us!</i>", parse_mode="HTML")
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
                    f"╔═══════════════════╗\n"
                    f"║ 🔒 <b>SUPPORT ENDED</b> ║\n"
                    f"╚═══════════════════╝\n\n"
                    f"✅ Ticket <code>#{tid}</code> closed\n"
                    f"⭐ <i>Thank you!</i>", parse_mode="HTML")
            except: pass
            return bot.send_message(message.chat.id, f"✅ Ticket #{tid} closed")
        
        return bot.send_message(message.chat.id, "ℹ️ No active chat to close.")
    
    # ═══════════════════════════
    # 📖 المساعدة
    # ═══════════════════════════
    if message.text.startswith('/help'):
        help_msg = (
            f"╔═══════════════════╗\n"
            f"║  📖 <b>HELP MENU</b>  ║\n"
            f"╚═══════════════════╝\n\n"
            f"🔹 /start - Main menu\n"
            f"🔹 /id - Your Telegram ID\n"
            f"🔹 /close - End ticket chat\n"
            f"🔹 /help - This menu\n\n"
            f"💻 <b>Developer:</b> @fkLJh00302"
        )
        return bot.send_message(message.chat.id, help_msg, parse_mode="HTML")

    if is_user_banned(uid):
        return bot.send_message(message.chat.id, t(lang, "banned"), parse_mode="HTML")

    if message.text.startswith('/id'):
        if not enforce_subscription(message, lang): return
        return bot.send_message(message.chat.id,
            f"🆔 <b>Your Info:</b>\n\n"
            f"👤 ID: <code>{uid}</code>\n"
            f"📝 Username: @{u.get('username', 'N/A')}", parse_mode="HTML")

    # ═══════════════════════════
    # 🎁 نظام الإحالة و Giveaway
    # ═══════════════════════════
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        # 🎁 رابط Giveaway
        if param.startswith("gw_"):
            gw_code = param[3:]  # حذف "gw_"
            
            if not enforce_subscription(message, lang): return
            
            if not u.get("verified", False):
                require_verification_on_start(uid)
                return
            
            # فحص صلاحية العرض
            valid, reason = is_giveaway_valid(gw_code)
            if not valid:
                error_msg = format_giveaway_error(reason, lang)
                return bot.send_message(message.chat.id, error_msg, parse_mode="HTML")
            
            # فحص إذا استلم من قبل
            if has_user_claimed_giveaway(gw_code, uid):
                return bot.send_message(message.chat.id,
                    t(lang, "gw_already_claimed"), parse_mode="HTML")
            
            # بدء كابتشا الـ giveaway
            gw = get_giveaway(gw_code)
            remaining = gw["max_users"] - len(gw.get("claimed_by", []))
            time_left = format_time_remaining(gw["expires"])
            
            bot.send_message(message.chat.id,
                t(lang, "gw_welcome_claim",
                  reward=gw["reward"], remaining=remaining,
                  max=gw["max_users"], time=time_left),
                parse_mode="HTML")
            
            # إرسال الكابتشا
            time.sleep(0.5)
            start_giveaway_captcha(uid, gw_code)
            return
        
        # 🔗 نظام الإحالة العادي
        if u.get("invited_by") is None:
            inv_id = param
            if get_user(inv_id) and inv_id != uid:
                update_user_data(uid, invited_by=inv_id)
                reward = bot_config.get("invite_reward", 20)
                update_user_data(inv_id, points=reward, accumulated_points=reward,
                               invite_count=1, referral_earnings=reward)
                update_user_rank_and_quests(inv_id)
                try:
                    bot.send_message(int(inv_id),
                        f"╔═══════════════════╗\n"
                        f"║ 🎊 <b>NEW REFERRAL!</b> ║\n"
                        f"╚═══════════════════╝\n\n"
                        f"🎉 Someone joined using your link!\n"
                        f"🎁 <b>Reward:</b> +{reward} 💎\n\n"
                        f"💡 <i>Keep inviting for more!</i>", parse_mode="HTML")
                except: pass

    if not enforce_subscription(message, lang): return

    if not u.get("verified", False):
        require_verification_on_start(uid)
        return

    if not u.get("lang_selected", False):
        return bot.send_message(message.chat.id, t("ar", "welcome"),
            reply_markup=get_lang_inline(), parse_mode="HTML")

    show_main_menu(message.chat.id, uid, lang)

# =====================================================
# 🏠 عرض القائمة الرئيسية
# =====================================================
def show_main_menu(chat_id, uid, lang):
    u = get_user(uid) or {}
    name = u.get("username") or "User"
    
    welcome_frames = [
        f"⏳ <i>Loading...</i>",
        f"✨ <i>Welcome back...</i>",
        f"🎊 <b>Ready!</b>",
        t(lang, "main_menu_title", name=name)
    ]
    
    try:
        msg = bot.send_message(chat_id, welcome_frames[0], parse_mode="HTML")
        for frame in welcome_frames[1:]:
            time.sleep(0.3)
            try:
                bot.edit_message_text(frame, chat_id, msg.message_id, parse_mode="HTML")
            except: pass
    except: pass
    
    fs = get_active_flash_sale()
    if fs:
        try:
            remaining = format_time_remaining(fs["expires"])
            fs_msg = (
                f"⚡⚡⚡ <b>ACTIVE FLASH SALE!</b> ⚡⚡⚡\n\n"
                f"🔥 <b>{fs['discount']}%</b> OFF on <b>{fs['product']}</b>\n"
                f"⏰ Ends in: <b>{remaining}</b>\n\n"
                f"💨 <i>Grab it before it's gone!</i>"
            )
            bot.send_message(chat_id, fs_msg, parse_mode="HTML")
        except: pass
    
    bot.send_message(chat_id, "👇", reply_markup=get_main_keyboard(uid, lang))

# =====================================================
# 💬 معالجات دردشة التذاكر
# =====================================================
def handle_user_ticket_message(message, uid):
    tid = active_ticket_chats[uid]
    tickets = bot_config.get("tickets", {})
    
    if tid not in tickets:
        active_ticket_chats.pop(uid, None)
        return
    
    if "messages" not in tickets[tid]:
        tickets[tid]["messages"] = []
    tickets[tid]["messages"].append({
        "from": "user", "text": message.text or "[media]",
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
            f"╔═══════════════════╗\n"
            f"║  📨 <b>NEW MESSAGE</b>  ║\n"
            f"╚═══════════════════╝\n\n"
            f"🎫 <b>Ticket:</b> <code>#{tid}</code>\n"
            f"👤 <b>From:</b> @{u.get('username', 'N/A')}\n"
            f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
            f"💬 <b>Message:</b>\n<i>{message.text}</i>",
            reply_markup=m, parse_mode="HTML")
    except: pass
    
    bot.send_message(message.chat.id,
        f"✅ <b>Message Sent</b> 📨\n\n"
        f"⏳ <i>Support will reply soon...</i>\n"
        f"🔒 Type /close to end chat", parse_mode="HTML")

def handle_admin_ticket_message(message, admin_uid):
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
                f"╔═══════════════════╗\n"
                f"║  🔒 <b>SUPPORT ENDED</b>  ║\n"
                f"╚═══════════════════╝\n\n"
                f"✅ Ticket <code>#{tid}</code> closed\n"
                f"⭐ <i>Thank you for choosing us!</i>", parse_mode="HTML")
        except: pass
        return bot.send_message(message.chat.id, f"✅ Ticket #{tid} closed")
    
    info = admin_ticket_chats[admin_uid]
    tid = info["ticket_id"]
    user_uid = info["user_uid"]
    
    tickets = bot_config.get("tickets", {})
    if tid in tickets:
        if "messages" not in tickets[tid]:
            tickets[tid]["messages"] = []
        tickets[tid]["messages"].append({
            "from": "admin", "text": message.text or "[media]",
            "time": datetime.now().isoformat()
        })
        save_json(DB_CONFIG, bot_config)
    
    try:
        bot.send_message(int(user_uid),
            f"╔═══════════════════╗\n"
            f"║  💬 <b>SUPPORT REPLY</b>  ║\n"
            f"╚═══════════════════╝\n\n"
            f"👨‍💻 <b>Support Team:</b>\n\n"
            f"<i>{message.text}</i>\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Reply anytime | Type /close to end</i>", parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ Reply sent to user")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

# =====================================================
# 🎯 الموجّه الرئيسي
# =====================================================
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
                    f"✅ <b>تم النشر بنجاح!</b>\n\n"
                    f"📋 <b>Message ID:</b> <code>{msg_id}</code>\n"
                    f"💡 <i>احفظ الـ ID للحذف لاحقاً</i>", parse_mode="HTML")
            else:
                return bot.send_message(message.chat.id, "❌ فشل الإرسال")
        
        elif action == "send_raw":
            msg_id = send_raw_channel_message(message.text)
            if msg_id:
                return bot.send_message(message.chat.id,
                    f"✅ <b>تم النشر بنجاح!</b>\n\n"
                    f"📋 <b>Message ID:</b> <code>{msg_id}</code>", parse_mode="HTML")
            else:
                return bot.send_message(message.chat.id, "❌ فشل الإرسال")
        
        elif action == "delete_msg":
            try:
                msg_id = int(message.text.strip())
                if delete_channel_message(msg_id):
                    return bot.send_message(message.chat.id,
                        f"✅ <b>تم حذف الرسالة!</b>\n\n📋 ID: <code>{msg_id}</code>", parse_mode="HTML")
                else:
                    return bot.send_message(message.chat.id,
                        "❌ فشل الحذف - تأكد من ID الرسالة")
            except:
                return bot.send_message(message.chat.id, "❌ ID غير صحيح")
    
    if check_spam(uid): return
    register_user(message.from_user)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    if is_user_banned(uid):
        return bot.send_message(message.chat.id, t(lang, "banned"), parse_mode="HTML")
    
    if is_captcha_pending(uid):
        return bot.send_message(message.chat.id,
            "🛡️ <b>Solve captcha first!</b>", parse_mode="HTML")
    
    txt = message.text.strip() if message.text else ""
    admin_flag = is_admin(uid, u)

    if not enforce_subscription(message, lang): return

    if bot_config.get("maintenance", False) and not admin_flag:
        return bot.send_message(message.chat.id,
            f"╔═══════════════════╗\n"
            f"║ 🛠️ <b>MAINTENANCE</b> 🛠️ ║\n"
            f"╚═══════════════════╝\n\n"
            f"⚠️ Bot is temporarily offline\n"
            f"⏳ <i>We'll be back soon!</i>", parse_mode="HTML")

    # 🟢 أزرار المستخدم
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
            reply_markup=get_settings_menu(lang, u), parse_mode="HTML")
    
    if txt == t(lang, "btn_admin") and admin_flag:
        return bot.send_message(message.chat.id,
            f"╔═══════════════════╗\n"
            f"║  👑 <b>ADMIN PANEL</b>  ║\n"
            f"╚═══════════════════╝\n\n"
            f"⚡ <i>Full control at your fingertips</i>",
            reply_markup=get_admin_keyboard(), parse_mode="HTML")

    # 🔴 أزرار الأدمن
    if admin_flag:
        if txt == "📦 المنتجات":
            return bot.send_message(message.chat.id, "📦 <b>إدارة المنتجات</b>",
                reply_markup=admin_products_menu(), parse_mode="HTML")
        if txt == "🔑 المفاتيح":
            return bot.send_message(message.chat.id, "🔑 <b>إدارة المفاتيح</b>",
                reply_markup=admin_keys_menu(), parse_mode="HTML")
        if txt == "👥 الأعضاء":
            return bot.send_message(message.chat.id, "👥 <b>إدارة الأعضاء</b>",
                reply_markup=admin_members_menu(), parse_mode="HTML")
        if txt == "🎫 التذاكر":
            return admin_show_tickets(message)
        if txt == "💰 المبيعات":
            return bot.send_message(message.chat.id, "💰 <b>المبيعات والأكواد</b>",
                reply_markup=admin_sales_menu(), parse_mode="HTML")
        if txt == "📢 التسويق":
            return bot.send_message(message.chat.id, "📢 <b>التسويق</b>",
                reply_markup=admin_marketing_menu(), parse_mode="HTML")
        if txt == "⚡ عروض خاطفة":
            fs = get_active_flash_sale()
            status = ""
            if fs:
                status = f"\n\n⚡ <b>Active:</b> {fs['product']} ({fs['discount']}% OFF)"
            return bot.send_message(message.chat.id,
                f"⚡ <b>العروض الخاطفة</b>{status}",
                reply_markup=admin_flash_menu(), parse_mode="HTML")
        
        # 🎁 قائمة Giveaway
        if txt == "🎁 Giveaway":
            stats = get_giveaways_stats()
            return bot.send_message(message.chat.id,
                f"╔═══════════════════╗\n"
                f"║  🎁 <b>GIVEAWAY</b>  ║\n"
                f"╚═══════════════════╝\n\n"
                f"📊 <b>الإحصائيات:</b>\n"
                f"├ الكل: {stats['total']}\n"
                f"├ نشط: {stats['active']}\n"
                f"├ منتهي: {stats['expired']}\n"
                f"└ ممتلئ: {stats['full']}",
                reply_markup=admin_giveaway_menu(), parse_mode="HTML")
        
        # 📨 قائمة رسائل القناة
        if txt == "📨 رسائل القناة":
            return bot.send_message(message.chat.id,
                f"╔═══════════════════╗\n"
                f"║ 📨 <b>CHANNEL MSGS</b> ║\n"
                f"╚═══════════════════╝\n\n"
                f"📢 اختر الإجراء:",
                reply_markup=admin_channel_menu(), parse_mode="HTML")
        
        if txt == "🎮 الألعاب":
            return bot.send_message(message.chat.id, "🎮 <b>إعدادات الألعاب</b>",
                reply_markup=admin_games_menu(), parse_mode="HTML")
        if txt == "⚙️ النظام":
            return bot.send_message(message.chat.id, "⚙️ <b>النظام</b>",
                reply_markup=admin_system_menu(), parse_mode="HTML")
        if txt == "📊 الإحصائيات":
            return admin_show_stats(message)
        if txt == "💡 الطلبات":
            return admin_show_product_requests(message)
        
        if txt == "🛠️ وضع الصيانة":
            current = bot_config.get("maintenance", False)
            new_state = not current
            bot_config["maintenance"] = new_state
            save_json(DB_CONFIG, bot_config)
            if new_state:
                msg = (f"╔═══════════════════╗\n"
                       f"║ 🛠️ <b>MAINTENANCE ON</b> ║\n"
                       f"╚═══════════════════╝\n\n"
                       f"⚠️ Bot is now <b>OFFLINE</b> for users")
                publish_maintenance_notice(True)
            else:
                msg = (f"╔═══════════════════╗\n"
                       f"║ ✅ <b>MAINTENANCE OFF</b> ║\n"
                       f"╚═══════════════════╝\n\n"
                       f"🎉 Bot is now <b>ONLINE</b>")
                publish_maintenance_notice(False)
            return bot.send_message(message.chat.id, msg, parse_mode="HTML")
        
        if txt == "🔙 العودة":
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
        acc=u.get('accumulated_points', 0),
        streak=u.get('streak_days', 0))
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_myid(chat_id, msg_id, uid, u, lang):
    join_date = u.get("join_date", "")[:10] if u.get("join_date") else "N/A"
    msg = (f"🆔 <b>━━ My Info ━━</b>\n\n"
           f"┃ 👤 <b>ID:</b> <code>{uid}</code>\n"
           f"┃ 📝 <b>Username:</b> @{u.get('username', 'N/A')}\n"
           f"┃ 📅 <b>Joined:</b> {join_date}\n"
           f"┃ 🌐 <b>Language:</b> {u.get('lang', 'ar').upper()}\n"
           f"╰━━━━━━━━━━━━╯")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_rank(chat_id, msg_id, uid, lang):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    msg = f"🏆 <b>━━ My Rank ━━</b>\n\n"
    msg += f"┃ 🎖️ <b>Current:</b> {u.get('rank', '🔹')}\n"
    msg += f"┃ 🎯 <b>Discount:</b> {int((u.get('rank_discount', 0) or 0)*100)}%\n"
    msg += f"┃ 📊 <b>Points:</b> <code>{u.get('accumulated_points', 0)}</code>\n"
    msg += f"╰━━━━━━━━━━━━╯\n\n"
    msg += f"📋 <b>All Ranks:</b>\n"
    for rk in ["silver", "gold", "diamond", "hero", "master", "legend"]:
        r = RANKS[rk]
        name = r.get(f"name_{lang}", r.get("name_en", ""))
        acc = u.get('accumulated_points', 0) or 0
        icon = "✅" if acc >= r['points_needed'] else "🔒"
        msg += f"{icon} {name} - {r['points_needed']} 💎 ({int(r['discount']*100)}%)\n"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_referral(chat_id, msg_id, uid, lang):
    try: bu = bot.get_me().username
    except: bu = "your_bot"
    link = f"https://t.me/{bu}?start={uid}"
    u = get_user(uid) or {}
    invites = u.get("invite_count", 0) or 0
    reward = bot_config.get("invite_reward", 20)
    total = invites * reward
    msg = t(lang, "referral_msg", invites=invites, reward=reward, total=total, link=link)
    m = types.InlineKeyboardMarkup()
    share = f"https://t.me/share/url?url={link}&text=🔥%20Join%20the%20best%20store%20bot!"
    m.add(types.InlineKeyboardButton("📤 Share Link", url=share))
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_purchases(chat_id, msg_id, uid, lang):
    sales = [x for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid]
    if not sales:
        msg = "📭 <b>No purchases yet</b>\n\n💡 <i>Visit the shop to start!</i>"
    else:
        msg = f"📜 <b>━━ My Purchases ━━</b>\n\n📊 <b>Total:</b> {len(sales)}\n\n"
        for s in sales[-10:]:
            msg += f"┃ 📦 <b>{s['product']}</b>\n"
            msg += f"┃ ⏱️ {s['plan']} | 💰 {s['price']} 💎\n"
            msg += f"┃ 📅 {s.get('date','')[:10]}\n"
            msg += f"┃ ━━━━━━━━━\n"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_account"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def claim_daily(chat_id, msg_id, uid, lang):
    u = get_user(uid) or {}
    now = datetime.now()
    lc = u.get("last_claim")
    streak = u.get("streak_days", 0) or 0
    
    if lc:
        try:
            last = datetime.fromisoformat(lc)
            nxt = last + timedelta(days=1)
            if now < nxt:
                r = nxt - now
                h = r.seconds // 3600
                mi = (r.seconds % 3600) // 60
                msg = t(lang, "daily_wait", hours=h, mins=mi, streak=streak)
                mk = types.InlineKeyboardMarkup()
                mk.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
                try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=mk, parse_mode="HTML")
                except: pass
                return
        except: pass
    
    gift = bot_config.get("daily_gift", 10)
    update_user_data(uid, last_claim=now.isoformat())
    update_user_data(uid, points=gift, accumulated_points=gift)
    update_user_rank_and_quests(uid)
    u_new = get_user(uid) or {}
    
    frames = [
        "🎁 <b>Opening...</b>",
        "✨ <b>Opening...</b> ✨",
        "💫 <b>Almost there...</b> 💫",
        "🎉 <b>Success!</b> 🎊"
    ]
    for f in frames:
        try:
            bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
            time.sleep(0.3)
        except: pass
    
    msg = t(lang, "daily_success", gift=gift, balance=u_new.get('points', 0), streak=streak)
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=mk, parse_mode="HTML")
    except: pass

def show_quests(chat_id, msg_id, uid, lang):
    update_user_rank_and_quests(uid)
    u = get_user(uid) or {}
    completed = u.get("completed_quests", "") or ""
    inv_cnt = u.get("invite_count", 0) or 0
    buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    acc = u.get("accumulated_points", 0) or 0
    q = bot_config.get("quests")
    
    msg = "🔥 <b>━━ Quests ━━</b>\n\n"
    for i, (key, name, cur, tgt, rw) in enumerate([
        ("quest_invite", "👥 Invite Friends", inv_cnt, q['invite']['target'], q['invite']['reward']),
        ("quest_buy", "🛒 Make Purchases", buys, q['buy']['target'], q['buy']['reward']),
        ("quest_points", "💎 Collect Points", acc, q['points']['target'], q['points']['reward'])
    ], 1):
        if key in completed:
            prog, st = "🟩🟩🟩🟩🟩", "✅ <b>DONE</b>"
        else:
            p = min(100, (cur / tgt) * 100) if tgt > 0 else 0
            fl = int(p / 20)
            prog = "🟩" * fl + "⬜" * (5 - fl)
            st = f"{cur}/{tgt}"
        msg += f"┃ {i}️⃣ <b>{name}</b>\n┃ 🎁 +{rw} 💎\n┃ {prog} {st}\n┃━━━━━━━━━\n"
    
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=mk, parse_mode="HTML")
    except: pass

def show_flash_sale(chat_id, msg_id, uid, lang):
    fs = get_active_flash_sale()
    if not fs:
        msg = t(lang, "no_flash_sale")
    else:
        remaining = format_time_remaining(fs["expires"])
        msg = t(lang, "flash_sale_active",
                discount=fs["discount"], product=fs["product"], remaining=remaining)
    mk = types.InlineKeyboardMarkup()
    if fs:
        mk.add(types.InlineKeyboardButton(
            f"🛒 Buy Now ({fs['discount']}% OFF)",
            callback_data=f"select_prod_{fs['product']}"))
    mk.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_rewards"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=mk, parse_mode="HTML")
    except: pass

def show_lootbox(chat_id, msg_id, lang):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = (f"🎰 <b>━━ Loot Box ━━</b>\n\n"
           f"┃ 💸 <b>Price:</b> {price} 💎\n"
           f"┃ 📊 <b>Win Chance:</b> {chance}%\n"
           f"┃ 🏆 <b>Prize:</b> +100 to +500 💎\n"
           f"╰━━━━━━━━━━━━╯\n\n"
           f"🍀 <i>Feeling lucky?</i>")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(f"🎁 Open Box ({price} 💎)", callback_data="game_buy_lootbox"))
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_wheel(chat_id, msg_id, lang):
    price = bot_config.get("wheel_price", 40)
    chance = bot_config.get("wheel_chance", 5)
    msg = (f"🎡 <b>━━ Lucky Wheel ━━</b>\n\n"
           f"┃ 💸 <b>Spin:</b> {price} 💎\n"
           f"┃ 📊 <b>Grand Prize:</b> {chance}%\n"
           f"┃ 🏆 <b>Max Win:</b> +1000 💎\n"
           f"╰━━━━━━━━━━━━╯\n\n"
           f"🎯 <i>Spin to win big!</i>")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(f"💫 Spin ({price} 💎)", callback_data="game_spin_wheel"))
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_shop(message, uid, u, lang):
    if not prices_config:
        return bot.send_message(message.chat.id, t(lang, "shop_empty"), parse_mode="HTML")
    u_disc = u.get("rank_discount", 0.0) or 0.0
    header = t(lang, "shop_header",
               points=u.get('points', 0), rank=u.get('rank', '🔹'), disc=int(u_disc*100))
    
    fs = get_active_flash_sale()
    if fs:
        header += f"\n\n⚡ <b>Flash Sale:</b> {fs['discount']}% OFF on {fs['product']}!"
    
    m = types.InlineKeyboardMarkup(row_width=1)
    for prod in prices_config.keys():
        stock = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        emoji = "🔥" if fs and fs["product"] == prod else ("✅" if stock > 0 else "⚠️")
        m.add(types.InlineKeyboardButton(f"{emoji} 📦 {prod}  |  📊 {stock}",
                                         callback_data=f"select_prod_{prod}"))
    bot.send_message(message.chat.id, header, reply_markup=m, parse_mode="HTML")

# قوائم أخرى
def show_new_ticket_categories(chat_id, msg_id, lang):
    try:
        bot.edit_message_text(t(lang, "ticket_categories"), chat_id, msg_id,
            reply_markup=get_ticket_categories(lang), parse_mode="HTML")
    except: pass

def show_my_tickets(chat_id, msg_id, uid, lang):
    tickets = bot_config.get("tickets", {})
    my_t = {k: v for k, v in tickets.items() if str(v.get("uid")) == uid}
    if not my_t:
        msg = t(lang, "no_tickets") + "\n\n💡 <i>Open a new ticket if you need help!</i>"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return
    msg = t(lang, "my_tickets_title") + f"\n\n📊 <b>Total:</b> {len(my_t)}\n\n"
    m = types.InlineKeyboardMarkup(row_width=1)
    for tid, info in list(my_t.items())[-10:]:
        status = "🟢 Open" if info.get("status", "open") == "open" else "🔴 Closed"
        cat_key = info.get("category", "other")
        cat_name = TICKET_CATEGORIES.get(cat_key, {}).get(lang, "Other")
        m.add(types.InlineKeyboardButton(f"#{tid} • {cat_name} • {status}",
                                         callback_data=f"myticket_{tid}"))
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_faq(chat_id, msg_id, lang):
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
    try: bot.edit_message_text(t(lang, "faq_title"), chat_id, msg_id,
        reply_markup=m, parse_mode="HTML")
    except: pass

def show_notifications(chat_id, msg_id, uid, lang):
    """تبديل الإشعارات مع رسالة واضحة"""
    u = get_user(uid) or {}
    current = u.get("notifications_on", True)
    new_val = not current
    update_user_data(uid, notifications_on=new_val)
    
    if new_val:
        msg = t(lang, "notif_updated_on")
    else:
        msg = t(lang, "notif_updated_off")
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_settings"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_theme(chat_id, msg_id, uid, lang):
    u = get_user(uid) or {}
    current = u.get("theme", "dark").title()
    msg = (f"🎨 <b>━━ Theme ━━</b>\n\n"
           f"🎯 <b>Current:</b> {current}\n\n"
           f"✨ <b>Available:</b>\n"
           f"🌙 <b>Dark</b> - Cool & modern\n"
           f"☀️ <b>Light</b> - Bright & fresh\n"
           f"🎨 <b>Neon</b> - Vibrant colors\n"
           f"🌸 <b>Sakura</b> - Pink & pretty")
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🌙 Dark", callback_data="settheme_dark"),
        types.InlineKeyboardButton("☀️ Light", callback_data="settheme_light")
    )
    m.add(
        types.InlineKeyboardButton("🎨 Neon", callback_data="settheme_neon"),
        types.InlineKeyboardButton("🌸 Sakura", callback_data="settheme_sakura")
    )
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_settings"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_privacy(chat_id, msg_id, lang):
    msg = (f"🔒 <b>━━ Privacy Policy ━━</b>\n\n"
           f"🛡️ <b>Your data is safe with us</b>\n\n"
           f"✅ We DO: Encrypt all transactions\n"
           f"❌ We DON'T: Share your info\n\n"
           f"📜 <i>By using this bot, you agree to our Terms</i>")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_settings"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def show_about(chat_id, msg_id, lang):
    stats = get_bot_stats()
    msg = t(lang, "about_title", users=stats["total_users"], sales=stats["total_sales"])
    msg += f"\n\n💻 <b>Developer:</b> @fkLJh00302"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK))
    m.add(types.InlineKeyboardButton("💻 Contact Developer", url="https://t.me/fkLJh00302"))
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_settings"))
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

# 👑 دوال الأدمن
def admin_show_tickets(message):
    tickets = bot_config.get("tickets", {})
    open_t = {k: v for k, v in tickets.items() if v.get("status", "open") == "open"}
    if not open_t:
        return bot.send_message(message.chat.id, "🎉 لا تذاكر مفتوحة")
    m = types.InlineKeyboardMarkup()
    for tid, info in open_t.items():
        cat = TICKET_CATEGORIES.get(info.get("category", "other"), {}).get("ar", "أخرى")
        m.add(types.InlineKeyboardButton(f"🎫 #{tid} • {cat}",
                                         callback_data=f"admview_ticket_{tid}"))
    bot.send_message(message.chat.id,
        f"🎫 <b>التذاكر المفتوحة:</b> ({len(open_t)})",
        reply_markup=m, parse_mode="HTML")

def admin_show_product_requests(message):
    reqs = bot_config.get("product_requests", {})
    if not reqs:
        return bot.send_message(message.chat.id, "📭 لا طلبات")
    msg = f"💡 <b>طلبات المنتجات:</b> ({len(reqs)})\n\n"
    for rid, info in list(reqs.items())[-15:]:
        msg += f"🔹 <b>#{rid}</b>\n👤 {info['uid']}\n📦 {info['text']}\n━━━━━━\n"
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

def admin_show_stats(message):
    stats = get_bot_stats()
    msg = (f"╔═══════════════════╗\n"
           f"║  📊 <b>STATISTICS</b>  ║\n"
           f"╚═══════════════════╝\n\n"
           f"👥 <b>المستخدمين:</b> {stats['total_users']}\n"
           f"🟢 <b>نشط اليوم:</b> {stats['active_today']}\n"
           f"🛒 <b>المبيعات:</b> {stats['total_sales']}\n"
           f"💰 <b>الأرباح:</b> {stats['total_earnings']} 💎\n"
           f"📦 <b>المنتجات:</b> {stats['total_products']}\n"
           f"🎫 <b>الأكواد:</b> {stats['total_codes']}\n"
           f"🎟️ <b>التذاكر:</b> {stats['total_tickets']}\n"
           f"💡 <b>الطلبات:</b> {stats['total_requests']}\n"
           f"🛠️ <b>الصيانة:</b> {'ON' if stats['maintenance'] else 'OFF'}")
    bot.send_message(message.chat.id, msg, parse_mode="HTML")
    for f in [DB_KEYS, DB_REDEEM, DB_PRICES, DB_CONFIG]:
        if os.path.exists(f):
            try:
                with open(f, "rb") as d: bot.send_document(message.chat.id, d)
            except: pass# =====================================================
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

    # ═══════════════════════════════════
    # 🎁 كابتشا Giveaway
    # ═══════════════════════════════════
    if data.startswith("gwcap_"):
        answer = data.split("_", 1)[1]
        result, code = verify_giveaway_captcha(uid, answer)
        
        if result == "correct":
            # منح الجائزة!
            success, reward_or_reason = process_giveaway_claim(uid, code)
            if success:
                u_new = get_user(uid) or {}
                new_balance = u_new.get("points", 0)
                
                # 🎬 أنيميشن الفوز
                frames = [
                    "🎁 <b>Verifying...</b>",
                    "✨ <b>Processing prize...</b>",
                    "💫 <b>Almost there...</b>",
                    "🎊 <b>YOU WON!</b> 🎊"
                ]
                for f in frames:
                    try:
                        bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
                        time.sleep(0.4)
                    except: pass
                
                # رسالة الفوز النهائية
                win_msg = t(lang, "gw_success", reward=reward_or_reason, balance=new_balance)
                try: bot.edit_message_text(win_msg, chat_id, msg_id, parse_mode="HTML")
                except: pass
            else:
                error_msg = format_giveaway_error(reward_or_reason, lang)
                try: bot.edit_message_text(error_msg, chat_id, msg_id, parse_mode="HTML")
                except: pass
        elif result == "wrong":
            bot.answer_callback_query(call.id, t(lang, "captcha_wrong"), show_alert=True)
        elif result == "banned":
            try:
                bot.edit_message_text(
                    "🚫 <b>Too many wrong attempts!</b>\n\n⏰ Banned for 1 hour",
                    chat_id, msg_id, parse_mode="HTML")
            except: pass
        elif result == "expired":
            try:
                bot.edit_message_text("⏰ <b>Captcha expired!</b>",
                    chat_id, msg_id, parse_mode="HTML")
            except: pass
        return

    # ═══════════════════════════════════
    # 🛡️ كابتشا عادية
    # ═══════════════════════════════════
    if data.startswith("captcha_ans_"):
        ans = data.split("_", 2)[2]
        r = verify_captcha(uid, ans)
        if r == "correct":
            update_user_data(uid, verified=True)
            try:
                bot.edit_message_text(t(lang, "captcha_correct"), chat_id, msg_id, parse_mode="HTML")
            except: pass
            show_main_menu(chat_id, uid, lang)
        elif r == "wrong":
            bot.answer_callback_query(call.id, t(lang, "captcha_wrong"), show_alert=True)
        elif r == "banned":
            try:
                bot.edit_message_text(t(lang, "captcha_banned"), chat_id, msg_id, parse_mode="HTML")
            except: pass
        return

    # ═══════════════════════════════════
    # 🌐 تغيير اللغة
    # ═══════════════════════════════════
    if data.startswith("setlang_"):
        new_lang = data.split("_")[1]
        update_user_data(uid, lang=new_lang, lang_selected=True)
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        bot.send_message(chat_id, t(new_lang, "lang_changed"), parse_mode="HTML")
        show_main_menu(chat_id, uid, new_lang)
        return

    # ═══════════════════════════════════
    # ✅ فحص الاشتراك
    # ═══════════════════════════════════
    if data == "check_join":
        if not can_check_join(uid):
            bot.answer_callback_query(call.id,
                "⏳ Please wait 3 seconds before checking again", show_alert=True)
            return
        if check_channel_join(uid):
            try: bot.delete_message(chat_id, msg_id)
            except: pass
            bot.answer_callback_query(call.id, "✅ Verified!", show_alert=False)
            welcome_msg = (
                f"╔═══════════════════╗\n"
                f"║  🎉 <b>WELCOME!</b> 🎉  ║\n"
                f"╚═══════════════════╝\n\n"
                f"✅ You're now verified!\n"
                f"🎁 <i>Enjoy all features</i>"
            )
            bot.send_message(chat_id, welcome_msg, parse_mode="HTML")
            show_main_menu(chat_id, uid, lang)
        else:
            bot.answer_callback_query(call.id,
                "❌ You haven't joined yet!", show_alert=True)
        return

    if not check_channel_join(uid):
        bot.answer_callback_query(call.id, "⚠️ Join the channel first!", show_alert=True)
        return

    # ═══════════════════════════════════
    # 🔙 أزرار الرجوع
    # ═══════════════════════════════════
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

    if data == "back_settings":
        try: bot.edit_message_text(
            f"{t(lang, 'settings_title')}\n\n<i>{t(lang, 'settings_desc')}</i>",
            chat_id, msg_id, reply_markup=get_settings_menu(lang, u), parse_mode="HTML")
        except: pass
        return

    # ═══════════════════════════════════
    # 👤 قوائم فرعية
    # ═══════════════════════════════════
    if data == "menu_balance": return show_balance(chat_id, msg_id, uid, lang)
    if data == "menu_myid": return show_myid(chat_id, msg_id, uid, u, lang)
    if data == "menu_rank": return show_rank(chat_id, msg_id, uid, lang)
    if data == "menu_referral": return show_referral(chat_id, msg_id, uid, lang)
    if data == "menu_purchases": return show_purchases(chat_id, msg_id, uid, lang)
    if data == "menu_daily": return claim_daily(chat_id, msg_id, uid, lang)
    if data == "menu_quests": return show_quests(chat_id, msg_id, uid, lang)
    if data == "menu_flash": return show_flash_sale(chat_id, msg_id, uid, lang)
    if data == "menu_lootbox": return show_lootbox(chat_id, msg_id, lang)
    if data == "menu_wheel": return show_wheel(chat_id, msg_id, lang)
    if data == "menu_new_ticket": return show_new_ticket_categories(chat_id, msg_id, lang)
    if data == "menu_my_tickets": return show_my_tickets(chat_id, msg_id, uid, lang)
    if data == "menu_faq": return show_faq(chat_id, msg_id, lang)
    if data == "menu_notif": return show_notifications(chat_id, msg_id, uid, lang)
    if data == "menu_theme": return show_theme(chat_id, msg_id, uid, lang)
    if data == "menu_privacy": return show_privacy(chat_id, msg_id, lang)
    if data == "menu_about": return show_about(chat_id, msg_id, lang)

    if data == "menu_redeem":
        m = bot.send_message(chat_id,
            "🎁 <b>━━ Redeem Code ━━</b>\n\n✍️ Enter your code:", parse_mode="HTML")
        bot.register_next_step_handler(m, process_redeem)
        return

    if data == "menu_request_product":
        m = bot.send_message(chat_id,
            "💡 <b>━━ Request Product ━━</b>\n\n✍️ Write product name & details:", parse_mode="HTML")
        bot.register_next_step_handler(m, process_product_request)
        return

    if data == "menu_lang":
        try:
            bot.edit_message_text(t(lang, "welcome"), chat_id, msg_id,
                reply_markup=get_lang_inline(), parse_mode="HTML")
        except: pass
        return

    # ═══════════════════════════════════
    # 🎫 التذاكر
    # ═══════════════════════════════════
    if data.startswith("tcat_"):
        cat_key = data.split("_")[1]
        cat_name = TICKET_CATEGORIES.get(cat_key, {}).get(lang, "Other")
        if "temp_ticket_cat" not in bot_config:
            bot_config["temp_ticket_cat"] = {}
        bot_config["temp_ticket_cat"][uid] = cat_key
        save_json(DB_CONFIG, bot_config)
        try:
            bot.edit_message_text(
                f"🎫 <b>Category:</b> {cat_name}\n\n{t(lang, 'ticket_write')}",
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        m = bot.send_message(chat_id, "💬 <i>Type your message...</i>", parse_mode="HTML")
        bot.register_next_step_handler(m, process_new_ticket)
        return

    if data.startswith("myticket_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid not in tickets: return
        info = tickets[tid]
        status = "🟢 Open" if info.get("status", "open") == "open" else "🔴 Closed"
        cat_key = info.get("category", "other")
        cat = TICKET_CATEGORIES.get(cat_key, {}).get(lang, "Other")
        msg = (f"╔═══════════════════╗\n"
               f"║  🎫 <b>Ticket #{tid}</b>  ║\n"
               f"╚═══════════════════╝\n\n"
               f"┃ 📂 <b>Type:</b> {cat}\n"
               f"┃ 📊 <b>Status:</b> {status}\n"
               f"┃ 📅 <b>Date:</b> {info.get('date', '')[:16]}\n"
               f"╰━━━━━━━━━━━━╯\n\n"
               f"💬 <b>Original:</b>\n{info.get('text', '')}")
        messages = info.get("messages", [])
        if messages:
            msg += "\n\n📜 <b>Conversation:</b>\n"
            for m_item in messages[-5:]:
                who = "👤 You" if m_item["from"] == "user" else "👨‍💻 Support"
                msg += f"\n{who}: {m_item['text'][:100]}"
        m = types.InlineKeyboardMarkup()
        if info.get("status", "open") == "open":
            m.add(types.InlineKeyboardButton("💬 Open Live Chat", callback_data=f"opentchat_{tid}"))
            m.add(types.InlineKeyboardButton("🔒 Close Ticket", callback_data=f"closetickuser_{tid}"))
        m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="menu_my_tickets"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("opentchat_"):
        tid = data.split("_")[1]
        active_ticket_chats[uid] = tid
        try:
            bot.edit_message_text(t(lang, "ticket_chat_started"),
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data.startswith("closetickuser_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid in tickets:
            tickets[tid]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
            active_ticket_chats.pop(uid, None)
        try:
            bot.edit_message_text(t(lang, "ticket_closed", tid=tid),
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    # ═══════════════════════════════════
    # 🎨 الثيمات
    # ═══════════════════════════════════
    if data.startswith("settheme_"):
        theme = data.split("_")[1]
        update_user_data(uid, theme=theme)
        bot.answer_callback_query(call.id, f"✅ {theme.title()} theme activated!", show_alert=True)
        return show_theme(chat_id, msg_id, uid, lang)

    # ═══════════════════════════════════
    # 🎰 صندوق الحظ
    # ═══════════════════════════════════
    if data == "game_buy_lootbox":
        price = bot_config.get("lootbox_price", 50)
        if (u.get("points", 0) or 0) < price:
            return bot.answer_callback_query(call.id, t(lang, "insufficient_balance"), show_alert=True)
        update_user_data(uid, points=-price)
        
        frames = [
            "🎁 <b>Opening the box...</b>",
            "✨ <b>Almost there...</b> ✨",
            "💫 <b>Revealing...</b> 💫",
            "🎊 <b>Result!</b>"
        ]
        for f in frames:
            try:
                bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
                time.sleep(0.35)
            except: pass
        
        if random.randint(1, 100) <= bot_config.get("lootbox_chance", 25):
            win = random.randint(100, 500)
            update_user_data(uid, points=win, accumulated_points=win)
            msg = (f"╔═══════════════════╗\n"
                   f"║  🎊 <b>YOU WON!</b> 🎊  ║\n"
                   f"╚═══════════════════╝\n\n"
                   f"💎 <b>+{win}</b> points added!\n\n"
                   f"✨ <i>Luck is on your side!</i>")
        else:
            msg = (f"╔═══════════════════╗\n"
                   f"║  😔 <b>EMPTY BOX</b>  ║\n"
                   f"╚═══════════════════╝\n\n"
                   f"💔 Better luck next time!\n\n"
                   f"💪 <i>Try again!</i>")
        
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔄 Try Again", callback_data="game_buy_lootbox"))
        mk.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=mk, parse_mode="HTML")
        except: pass
        update_user_rank_and_quests(uid)
        return

    # ═══════════════════════════════════
    # 🎡 عجلة الحظ
    # ═══════════════════════════════════
    if data == "game_spin_wheel":
        price = bot_config.get("wheel_price", 40)
        if (u.get("points", 0) or 0) < price:
            return bot.answer_callback_query(call.id, t(lang, "insufficient_balance"), show_alert=True)
        update_user_data(uid, points=-price)
        
        frames = [
            "🎡 <b>[ 🔴 ]</b>\n<i>Spinning...</i>",
            "🎡 <b>[ 🟡 ]</b>\n<i>Spinning...</i>",
            "🎡 <b>[ 🟢 ]</b>\n<i>Fast!</i>",
            "🎡 <b>[ 🔵 ]</b>\n<i>Slowing...</i>",
            "🎡 <b>[ 🟣 ]</b>\n<i>Almost...</i>",
            "🎡 <b>[ ⚪ ]</b>\n<i>Stopping...</i>"
        ]
        for f in frames:
            try:
                bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
                time.sleep(0.35)
            except: pass
        
        if random.randint(1, 100) <= bot_config.get("wheel_chance", 5):
            win = 1000
            update_user_data(uid, points=win, accumulated_points=win)
            msg = (f"╔═══════════════════╗\n"
                   f"║ 🏆 <b>GRAND PRIZE!</b> 🏆 ║\n"
                   f"╚═══════════════════╝\n\n"
                   f"👑 <b>+{win} 💎</b>\n\n"
                   f"🎊 <i>You're a legend!</i>")
            try:
                bot.send_message(CHANNEL_ID,
                    f"🎡 <b>WHEEL EXPLOSION!</b>\n🏆 +1000 💎 WON!\n🤖 t.me/{bot.get_me().username}",
                    parse_mode="HTML")
            except: pass
        else:
            result = random.choice([0, 10, 20, price])
            if result > 0:
                update_user_data(uid, points=result, accumulated_points=result)
                msg = f"🎡 <b>+{result}</b> 💎"
            else:
                msg = "🎡 <b>0</b> pts\n💪 Try again!"
        
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔄 Spin Again", callback_data="game_spin_wheel"))
        mk.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_entertainment"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=mk, parse_mode="HTML")
        except: pass
        update_user_rank_and_quests(uid)
        return

    # ═══════════════════════════════════
    # 🛍️ اختيار منتج
    # ═══════════════════════════════════
    if data.startswith("select_prod_"):
        prod = data.split("_", 2)[2]
        if prod not in prices_config: return
        u_disc = u.get("rank_discount", 0.0) or 0.0
        fs = get_active_flash_sale()
        flash_active = fs and fs["product"] == prod
        info = f"📦 <b>━━ {prod} ━━</b>\n\n"
        info += f"┃ 💎 Your Discount: <b>{int(u_disc*100)}%</b>\n"
        info += f"┃ 💰 Balance: <b>{u.get('points', 0)}</b>\n"
        if flash_active:
            info += f"┃ ⚡ <b>FLASH SALE:</b> {fs['discount']}% OFF!\n"
        info += "╰━━━━━━━━━━━━╯\n\n⏱️ <b>Choose duration:</b>"
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            base_p = prices_config[prod].get(plan, 0)
            disc = bot_config.get("discount", 0)
            fs_disc = fs["discount"] if flash_active else 0
            total_disc = disc + fs_disc
            final_p = int(base_p * (1 - total_disc/100) * (1 - u_disc))
            stock = len(keys_store.get(prod, {}).get(plan, []))
            emoji = "✅" if stock > 0 else "❌"
            btn_txt = f"{emoji} {plan} | {final_p} 💎 | 📊 {stock}"
            if flash_active: btn_txt = f"⚡ {btn_txt}"
            m.add(types.InlineKeyboardButton(btn_txt, callback_data=f"buy_plan|{prod}|{plan}"))
        m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="menu_shop_back"))
        try: bot.edit_message_text(info, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: bot.send_message(chat_id, info, reply_markup=m, parse_mode="HTML")
        return

    if data == "menu_shop_back":
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        return show_shop(call.message, uid, u, lang)

    # ═══════════════════════════════════
    # 🛒 الشراء (مُصلح - يعطي المفتاح!)
    # ═══════════════════════════════════
    if data.startswith("buy_plan|"):
        _, prod, plan = data.split("|")
        base_p = prices_config.get(prod, {}).get(plan, 0)
        disc = bot_config.get("discount", 0)
        u_disc = u.get("rank_discount", 0.0) or 0.0
        fs = get_active_flash_sale()
        fs_disc = fs["discount"] if fs and fs["product"] == prod else 0
        total_disc = disc + fs_disc
        final_p = int(base_p * (1 - total_disc/100) * (1 - u_disc))
        
        if (u.get("points", 0) or 0) < final_p:
            return bot.answer_callback_query(call.id, t(lang, "insufficient_balance"), show_alert=True)
        if not keys_store.get(prod, {}).get(plan, []):
            return bot.answer_callback_query(call.id, "⚠️ Out of stock!", show_alert=True)
        
        # 🎬 أنيميشن مراحل الشراء
        steps = [
            t(lang, "buy_step_1"),
            t(lang, "buy_step_2"),
            t(lang, "buy_step_3"),
            t(lang, "buy_step_4")
        ]
        for step in steps:
            try:
                bot.edit_message_text(step, chat_id, msg_id, parse_mode="HTML")
                time.sleep(0.5)
            except: pass
        
        # ✅ إعطاء المفتاح فعلياً بعد الأنيميشن
        try:
            key = keys_store[prod][plan].pop(0)
            update_user_data(uid, points=-final_p, total_spent=final_p, purchases_count=1)
            bot_config["total_sales"] = bot_config.get("total_sales", 0) + 1
            bot_config["total_earnings"] = bot_config.get("total_earnings", 0) + final_p
            if "sales_log" not in bot_config: bot_config["sales_log"] = []
            bot_config["sales_log"].append({
                "uid": uid, "username": u.get("username", ""),
                "product": prod, "plan": plan, "price": final_p,
                "key": key, "date": datetime.now().isoformat()
            })
            save_json(DB_KEYS, keys_store)
            save_json(DB_CONFIG, bot_config)
            update_user_rank_and_quests(uid)
            
            # 🎁 رسالة الشراء النهائية الجميلة
            msg = t(lang, "purchase_success", prod=prod, plan=plan, price=final_p, key=key)
            msg += f"\n\n{t(lang, 'buy_gift_msg')}"
            
            try: bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
            except: bot.send_message(chat_id, msg, parse_mode="HTML")
            
            # نشر بالقناة
            publish_sale_to_channel(prod, plan, final_p)
        except Exception as e:
            print(f"⚠️ Error in purchase: {e}")
            bot.send_message(chat_id, f"❌ خطأ في الشراء - راجع الأدمن")
        return

    # ═══════════════════════════════════
    # 🎫 التذاكر (الأدمن)
    # ═══════════════════════════════════
    if data.startswith("admview_ticket_"):
        tid = data.split("_")[2]
        tickets = bot_config.get("tickets", {})
        if tid not in tickets: return bot.answer_callback_query(call.id, "❌")
        info = tickets[tid]
        cat = TICKET_CATEGORIES.get(info.get("category", "other"), {}).get("ar", "أخرى")
        msg = (f"╔═══════════════════╗\n"
               f"║  🎫 <b>Ticket #{tid}</b>  ║\n"
               f"╚═══════════════════╝\n\n"
               f"👤 UID: <code>{info['uid']}</code>\n"
               f"📂 النوع: {cat}\n"
               f"📊 الحالة: {info.get('status', 'open')}\n\n"
               f"💬 {info['text']}")
        messages = info.get("messages", [])
        if messages:
            msg += "\n\n📜 <b>المحادثة:</b>\n"
            for m_item in messages[-5:]:
                who = "👤" if m_item["from"] == "user" else "👨‍💻"
                msg += f"\n{who}: {m_item['text'][:100]}"
        m = types.InlineKeyboardMarkup(row_width=2)
        m.add(types.InlineKeyboardButton("💬 دردشة مباشرة", callback_data=f"admchat_{tid}"))
        m.add(
            types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"admclosetick_{tid}"),
            types.InlineKeyboardButton("⚠️ حظر مؤقت", callback_data=f"admbanuser_{info['uid']}_temp")
        )
        m.add(types.InlineKeyboardButton("⛔ حظر دائم", callback_data=f"admbanuser_{info['uid']}_perm"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admchat_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid not in tickets: return bot.answer_callback_query(call.id, "❌")
        user_uid = tickets[tid]["uid"]
        admin_ticket_chats[uid] = {"ticket_id": tid, "user_uid": user_uid}
        active_ticket_chats[user_uid] = tid
        try:
            bot.edit_message_text(
                f"╔═══════════════════╗\n"
                f"║ 💬 <b>LIVE CHAT ON</b> ║\n"
                f"╚═══════════════════╝\n\n"
                f"🎫 Ticket: #{tid}\n"
                f"👤 User: <code>{user_uid}</code>\n\n"
                f"✅ Your messages go to user\n"
                f"⚠️ Type <code>/close</code> to end",
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        try:
            u_lang = (get_user(user_uid) or {}).get("lang", "ar")
            bot.send_message(int(user_uid),
                f"╔═══════════════════╗\n"
                f"║ 💬 <b>SUPPORT ONLINE</b> ║\n"
                f"╚═══════════════════╝\n\n"
                f"✅ An agent is chatting with you!\n"
                f"📝 Send your messages\n"
                f"🔒 Type /close to end", parse_mode="HTML")
        except: pass
        return

    if data.startswith("admclosetick_"):
        tid = data.split("_")[1]
        tickets = bot_config.get("tickets", {})
        if tid in tickets:
            tickets[tid]["status"] = "closed"
            save_json(DB_CONFIG, bot_config)
            user_uid = tickets[tid]["uid"]
            active_ticket_chats.pop(user_uid, None)
            try:
                u_lang = (get_user(user_uid) or {}).get("lang", "ar")
                bot.send_message(int(user_uid),
                    t(u_lang, "ticket_closed", tid=tid), parse_mode="HTML")
            except: pass
        try: bot.edit_message_text(f"✅ التذكرة #{tid} أُغلقت", chat_id, msg_id)
        except: pass
        return

    if data.startswith("admbanuser_"):
        parts = data.split("_")
        target = parts[1]
        ban_type = parts[2]
        if ban_type == "temp":
            until = (datetime.now() + timedelta(days=1)).isoformat()
            update_user_data(target, banned_until=until)
            bot.answer_callback_query(call.id, "⚠️ حظر مؤقت 24س", show_alert=True)
        elif ban_type == "demote":
            update_user_data(target, is_admin=False)
            bot.answer_callback_query(call.id, "⬇️ إزالة الإدارة", show_alert=True)
        else:
            update_user_data(target, banned=True)
            bot.answer_callback_query(call.id, "⛔ حظر دائم", show_alert=True)
        return

    # ═══════════════════════════════════
    # 🎁 GIVEAWAY - الأدمن
    # ═══════════════════════════════════
    if not is_admin(uid, u): return

    if data == "admgw_create":
        temp_giveaway_setup[uid] = {"step": "reward"}
        try:
            bot.edit_message_text(
                f"🎁 <b>━━ Create Giveaway ━━</b>\n\n"
                f"💎 <b>Step 1/3:</b> اختر الجائزة",
                chat_id, msg_id, reply_markup=giveaway_reward_menu(), parse_mode="HTML")
        except: pass
        return

    if data.startswith("gwset_reward_"):
        val = data.split("_")[2]
        if val == "custom":
            m = bot.send_message(chat_id, "💎 أرسل قيمة الجائزة (رقم):")
            bot.register_next_step_handler(m, lambda msg: process_gw_custom_reward(msg, uid, chat_id))
            return
        temp_giveaway_setup[uid] = {"step": "users", "reward": int(val)}
        try:
            bot.edit_message_text(
                f"🎁 <b>━━ Create Giveaway ━━</b>\n\n"
                f"💎 <b>Reward:</b> {val} 💎\n\n"
                f"👥 <b>Step 2/3:</b> عدد المستخدمين",
                chat_id, msg_id, reply_markup=giveaway_users_menu(), parse_mode="HTML")
        except: pass
        return

    if data.startswith("gwset_users_"):
        val = data.split("_")[2]
        if val == "custom":
            m = bot.send_message(chat_id, "👥 أرسل عدد المستخدمين (رقم):")
            bot.register_next_step_handler(m, lambda msg: process_gw_custom_users(msg, uid, chat_id))
            return
        setup = temp_giveaway_setup.get(uid, {})
        setup["step"] = "hours"
        setup["users"] = int(val)
        temp_giveaway_setup[uid] = setup
        try:
            bot.edit_message_text(
                f"🎁 <b>━━ Create Giveaway ━━</b>\n\n"
                f"💎 <b>Reward:</b> {setup['reward']} 💎\n"
                f"👥 <b>Users:</b> {val}\n\n"
                f"⏰ <b>Step 3/3:</b> المدة",
                chat_id, msg_id, reply_markup=giveaway_hours_menu(), parse_mode="HTML")
        except: pass
        return

    if data.startswith("gwset_hours_"):
        hours = int(data.split("_")[2])
        setup = temp_giveaway_setup.get(uid, {})
        reward = setup.get("reward", 100)
        users = setup.get("users", 10)
        
        # إنشاء الـ giveaway
        code = create_giveaway(reward, users, hours)
        
        # نشره في القناة
        msg_id_channel = publish_giveaway_to_channel(code)
        
        # مسح البيانات المؤقتة
        temp_giveaway_setup.pop(uid, None)
        
        try:
            bot.get_me().username
            bot_user = bot.get_me().username
        except:
            bot_user = "bot"
        
        try:
            bot.edit_message_text(
                f"╔═══════════════════╗\n"
                f"║ ✅ <b>GIVEAWAY CREATED!</b> ║\n"
                f"╚═══════════════════╝\n\n"
                f"🎁 <b>Code:</b> <code>{code}</code>\n"
                f"💎 <b>Reward:</b> {reward} 💎\n"
                f"👥 <b>Max Users:</b> {users}\n"
                f"⏰ <b>Duration:</b> {hours}h\n\n"
                f"🔗 <b>Link:</b>\n<code>https://t.me/{bot_user}?start=gw_{code}</code>\n\n"
                f"📢 <i>تم النشر بالقناة!</i>",
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data == "admgw_list":
        gws = get_all_giveaways()
        if not gws:
            try: bot.edit_message_text("📭 لا يوجد giveaways", chat_id, msg_id)
            except: pass
            return
        msg = "🎁 <b>━━ All Giveaways ━━</b>\n\n"
        for code, gw in list(gws.items())[-10:]:
            status_icon = {"active": "🟢", "expired": "🔴", "full": "🟡", "cancelled": "⚫"}.get(gw.get("status"), "⚪")
            claimed = len(gw.get("claimed_by", []))
            msg += f"{status_icon} <code>{code}</code>\n"
            msg += f"   💎 {gw['reward']} | 👥 {claimed}/{gw['max_users']}\n"
            msg += f"   📅 {gw.get('created', '')[:10]}\n\n"
        m = types.InlineKeyboardMarkup()
        for code in list(gws.keys())[-5:]:
            m.add(types.InlineKeyboardButton(f"❌ Cancel {code}", callback_data=f"admgw_cancel_{code}"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admgw_cancel_"):
        code = data.split("_")[2]
        if cancel_giveaway(code):
            bot.answer_callback_query(call.id, f"✅ Cancelled {code}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Failed", show_alert=True)
        return

    if data == "admgw_stats":
        stats = get_giveaways_stats()
        msg = (f"╔═══════════════════╗\n"
               f"║ 📊 <b>GIVEAWAY STATS</b> ║\n"
               f"╚═══════════════════╝\n\n"
               f"📊 <b>Total:</b> {stats['total']}\n"
               f"🟢 <b>Active:</b> {stats['active']}\n"
               f"🔴 <b>Expired:</b> {stats['expired']}\n"
               f"🟡 <b>Full:</b> {stats['full']}\n"
               f"⚫ <b>Cancelled:</b> {stats['cancelled']}\n\n"
               f"👥 <b>Total Claimed:</b> {stats['total_claimed']}\n"
               f"💎 <b>Points Given:</b> {stats['total_points_given']}")
        try: bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    # ═══════════════════════════════════
    # 📨 رسائل القناة
    # ═══════════════════════════════════
    if data == "admch_send_styled":
        last_channel_msgs[uid] = "send_styled"
        try:
            bot.edit_message_text(
                f"📝 <b>━━ رسالة مزخرفة ━━</b>\n\n"
                f"✍️ أرسل نص الرسالة الآن\n"
                f"💡 <i>سيتم زخرفتها تلقائياً</i>",
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data == "admch_send_raw":
        last_channel_msgs[uid] = "send_raw"
        try:
            bot.edit_message_text(
                f"✏️ <b>━━ رسالة خام ━━</b>\n\n"
                f"✍️ أرسل نص الرسالة الآن\n"
                f"💡 <i>ستُنشر كما هي بدون تعديل</i>\n"
                f"📝 <i>يدعم HTML tags</i>",
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data == "admch_delete":
        last_channel_msgs[uid] = "delete_msg"
        try:
            bot.edit_message_text(
                f"🗑️ <b>━━ حذف رسالة ━━</b>\n\n"
                f"✍️ أرسل Message ID للحذف\n"
                f"💡 <i>احصل عليه عند الإرسال</i>",
                chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    # ═══════════════════════════════════
    # المنتجات والمفاتيح
    # ═══════════════════════════════════
    if data == "admp_add":
        m = bot.send_message(chat_id, "➕ اسم المنتج:")
        bot.register_next_step_handler(m, admin_add_product)
        return
    if data == "admp_del":
        m = bot.send_message(chat_id, "❌ اسم المنتج:")
        bot.register_next_step_handler(m, admin_del_product)
        return
    if data == "admp_prices":
        if not prices_config: return bot.answer_callback_query(call.id, "❌")
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admprice_{p}"))
        try: bot.edit_message_text("💵 اختر منتج:", chat_id, msg_id, reply_markup=m)
        except: pass
        return

    if data.startswith("admprice_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            curr = prices_config.get(prod, {}).get(plan, 0)
            m.add(types.InlineKeyboardButton(f"⏱️ {plan} ({curr})",
                                             callback_data=f"admpricest_{prod}|{plan}"))
        try: bot.edit_message_text(f"📦 <b>{prod}</b>",
            chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admpricest_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        m = bot.send_message(chat_id, f"💵 السعر الجديد لـ {prod}/{plan}:")
        bot.register_next_step_handler(m, lambda msg: admin_save_price(msg, prod, plan))
        return

    if data == "admk_add":
        if not prices_config: return bot.answer_callback_query(call.id, "❌")
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admkadd_{p}"))
        try: bot.edit_message_text("🔑 اختر منتج:", chat_id, msg_id, reply_markup=m)
        except: pass
        return

    if data.startswith("admkadd_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            m.add(types.InlineKeyboardButton(f"⏱️ {plan}",
                                             callback_data=f"admkaddp_{prod}|{plan}"))
        try: bot.edit_message_text(f"📦 <b>{prod}</b>",
            chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admkaddp_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        m = bot.send_message(chat_id, f"🔑 المفاتيح لـ {prod}/{plan}\n(كل مفتاح بسطر):")
        bot.register_next_step_handler(m, lambda msg: admin_save_keys(msg, prod, plan))
        return

    if data == "admk_view":
        if not keys_store: return bot.answer_callback_query(call.id, "📭")
        s = "🔑 <b>━━ المفاتيح ━━</b>\n\n"
        for prod, plans in keys_store.items():
            s += f"📦 <b>{prod}</b>\n"
            for plan, lst in plans.items():
                s += f"   ├ {plan}: {len(lst)}\n"
            s += "\n"
        try: bot.edit_message_text(s, chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data == "admk_del":
        if not prices_config: return bot.answer_callback_query(call.id, "❌")
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admkdel_{p}"))
        try: bot.edit_message_text("🔢 اختر منتج:", chat_id, msg_id, reply_markup=m)
        except: pass
        return

    if data.startswith("admkdel_"):
        prod = data.split("_", 1)[1]
        m = types.InlineKeyboardMarkup()
        for plan in ["1 Day", "7 Days", "30 Days"]:
            cnt = len(keys_store.get(prod, {}).get(plan, []))
            m.add(types.InlineKeyboardButton(f"⏱️ {plan} ({cnt})",
                                             callback_data=f"admkdelp_{prod}|{plan}"))
        try: bot.edit_message_text(f"📦 <b>{prod}</b>",
            chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admkdelp_"):
        _, rest = data.split("_", 1)
        prod, plan = rest.split("|")
        keys = keys_store.get(prod, {}).get(plan, [])
        if not keys: return bot.answer_callback_query(call.id, "❌", show_alert=True)
        m = bot.send_message(chat_id, "🔢 المفتاح أو رقمه:")
        bot.register_next_step_handler(m, lambda msg: admin_del_key(msg, prod, plan))
        return

    if data == "admk_clear":
        keys_store.clear()
        for p in prices_config.keys():
            keys_store[p] = {"1 Day": [], "7 Days": [], "30 Days": []}
        save_json(DB_KEYS, keys_store)
        return bot.answer_callback_query(call.id, "🗑️ تم!", show_alert=True)

    if data == "admm_view":
        m = bot.send_message(chat_id, "👤 آيدي العضو:")
        bot.register_next_step_handler(m, admin_view_member)
        return
    if data == "admm_charge":
        m = bot.send_message(chat_id, "💰 <code>ID المبلغ</code>", parse_mode="HTML")
        bot.register_next_step_handler(m, admin_charge_member)
        return

    if data == "adms_code":
        m = bot.send_message(chat_id, "🎫 <code>CODE القيمة</code>", parse_mode="HTML")
        bot.register_next_step_handler(m, admin_create_code)
        return
    if data == "adms_discount":
        m = bot.send_message(chat_id, "🔥 نسبة الخصم (0-99):")
        bot.register_next_step_handler(m, admin_set_discount)
        return

    if data == "admmk_broadcast":
        m = bot.send_message(chat_id, "📢 نص الإذاعة:")
        bot.register_next_step_handler(m, admin_broadcast)
        return

    if data == "admmk_prices":
        if not prices_config: return bot.answer_callback_query(call.id, "❌", show_alert=True)
        if publish_prices_to_channel(prices_config, bot_config.get("discount", 0)):
            bot.answer_callback_query(call.id, "✅ نُشر!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌", show_alert=True)
        return

    if data == "admmk_fake":
        if publish_fake_marketing():
            bot.answer_callback_query(call.id, "✅ نُشر!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌", show_alert=True)
        return

    # عروض خاطفة
    if data == "admf_create":
        if not prices_config: return bot.answer_callback_query(call.id, "❌", show_alert=True)
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"admfsel_{p}"))
        try: bot.edit_message_text("⚡ اختر المنتج:", chat_id, msg_id, reply_markup=m)
        except: pass
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
        try: bot.edit_message_text(f"⚡ <b>{prod}</b>\nنسبة الخصم:",
            chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
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
        try: bot.edit_message_text(f"⚡ {prod} - {discount}%\nالمدة:",
            chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

    if data.startswith("admfhr_"):
        _, rest = data.split("_", 1)
        parts = rest.split("|")
        prod, discount, hours = parts[0], int(parts[1]), int(parts[2])
        expires = create_flash_sale(prod, discount, hours)
        publish_flash_sale_to_channel(prod, discount, hours)
        sent = 0
        for u_id in get_all_user_ids():
            try:
                u_info = get_user(u_id) or {}
                if u_info.get("notifications_on", True):
                    u_lang = u_info.get("lang", "ar")
                    bot.send_message(int(u_id),
                        t(u_lang, "flash_sale_active",
                          discount=discount, product=prod, remaining=f"{hours}h"),
                        parse_mode="HTML")
                    sent += 1
                    time.sleep(0.05)
            except: pass
        try: bot.edit_message_text(
            f"✅ <b>FLASH SALE ON!</b>\n📦 {prod}\n🔥 {discount}%\n⏰ {hours}h\n🔔 {sent} مستخدم",
            chat_id, msg_id, parse_mode="HTML")
        except: pass
        return

    if data == "admf_cancel":
        if "flash_sales" in bot_config:
            bot_config["flash_sales"]["current"] = None
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ ألغي", show_alert=True)
        return

    if data == "admg_lootbox": return show_lootbox_settings(chat_id, msg_id)
    if data == "admg_wheel": return show_wheel_settings(chat_id, msg_id)
    if data == "admg_quests": return show_quests_settings(chat_id, msg_id)

    if data == "adsys_daily":
        m = bot.send_message(chat_id,
            f"✨ الحالي: {bot_config.get('daily_gift', 10)}\n\nالقيمة الجديدة:")
        bot.register_next_step_handler(m, admin_edit_daily)
        return
    if data == "adsys_invite":
        m = bot.send_message(chat_id,
            f"🔗 الحالي: {bot_config.get('invite_reward', 20)}\n\nالقيمة الجديدة:")
        bot.register_next_step_handler(m, admin_edit_invite)
        return

    if data.startswith("cfg_"):
        return handle_cfg_callback(call, data, chat_id, msg_id, uid, u)

# =====================================================
# معالجات giveaway custom
# =====================================================
def process_gw_custom_reward(message, uid, chat_id):
    try:
        val = int(message.text.strip())
        if val <= 0: raise ValueError
        temp_giveaway_setup[uid] = {"step": "users", "reward": val}
        bot.send_message(chat_id,
            f"💎 <b>Reward:</b> {val}\n\n👥 اختر عدد المستخدمين:",
            reply_markup=giveaway_users_menu(), parse_mode="HTML")
    except:
        bot.send_message(chat_id, "❌ أرقام فقط")

def process_gw_custom_users(message, uid, chat_id):
    try:
        val = int(message.text.strip())
        if val <= 0: raise ValueError
        setup = temp_giveaway_setup.get(uid, {})
        setup["step"] = "hours"
        setup["users"] = val
        temp_giveaway_setup[uid] = setup
        bot.send_message(chat_id,
            f"👥 <b>Users:</b> {val}\n\n⏰ اختر المدة:",
            reply_markup=giveaway_hours_menu(), parse_mode="HTML")
    except:
        bot.send_message(chat_id, "❌ أرقام فقط")

# =====================================================
# ⚙️ إعدادات الألعاب
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
        if "box" in data: return show_lootbox_settings(chat_id, msg_id)
        else: return show_wheel_settings(chat_id, msg_id)

def show_lootbox_settings(chat_id, msg_id=None):
    price = bot_config.get("lootbox_price", 50)
    chance = bot_config.get("lootbox_chance", 25)
    msg = f"🎰 <b>━━ صندوق الحظ ━━</b>\n\n💸 السعر: <b>{price}</b>\n📊 النسبة: <b>{chance}%</b>"
    m = types.InlineKeyboardMarkup()
    m.row(types.InlineKeyboardButton("➕ سعر", callback_data="cfg_box_price_up"),
          types.InlineKeyboardButton("➖ سعر", callback_data="cfg_box_price_down"))
    m.row(types.InlineKeyboardButton("📈 نسبة", callback_data="cfg_box_chance_up"),
          types.InlineKeyboardButton("📉 نسبة", callback_data="cfg_box_chance_down"))
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
    else: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_wheel_settings(chat_id, msg_id=None):
    price = bot_config.get("wheel_price", 40)
    chance = bot_config.get("wheel_chance", 5)
    msg = f"🎡 <b>━━ عجلة الحظ ━━</b>\n\n💸 السعر: <b>{price}</b>\n📊 الكبرى: <b>{chance}%</b>"
    m = types.InlineKeyboardMarkup()
    m.row(types.InlineKeyboardButton("➕ سعر", callback_data="cfg_wheel_price_up"),
          types.InlineKeyboardButton("➖ سعر", callback_data="cfg_wheel_price_down"))
    m.row(types.InlineKeyboardButton("📈 نسبة", callback_data="cfg_wheel_chance_up"),
          types.InlineKeyboardButton("📉 نسبة", callback_data="cfg_wheel_chance_down"))
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
    else: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_quests_settings(chat_id, msg_id=None):
    q = bot_config.get("quests")
    msg = (f"🔥 <b>━━ المهام ━━</b>\n\n"
           f"1️⃣ 👥 دعوات: {q['invite']['target']} / +{q['invite']['reward']}\n"
           f"2️⃣ 🛒 مبيعات: {q['buy']['target']} / +{q['buy']['reward']}\n"
           f"3️⃣ 💎 نقاط: {q['points']['target']} / +{q['points']['reward']}")
    m = types.InlineKeyboardMarkup()
    m.row(types.InlineKeyboardButton("👥 -", callback_data="cfg_q_inv_t_down"),
          types.InlineKeyboardButton("👥 +", callback_data="cfg_q_inv_t_up"))
    m.row(types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_inv_r_down"),
          types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_inv_r_up"))
    m.row(types.InlineKeyboardButton("🛒 -", callback_data="cfg_q_buy_t_down"),
          types.InlineKeyboardButton("🛒 +", callback_data="cfg_q_buy_t_up"))
    m.row(types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_buy_r_down"),
          types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_buy_r_up"))
    m.row(types.InlineKeyboardButton("💎 -", callback_data="cfg_q_pts_t_down"),
          types.InlineKeyboardButton("💎 +", callback_data="cfg_q_pts_t_up"))
    m.row(types.InlineKeyboardButton("🎁 -", callback_data="cfg_q_pts_r_down"),
          types.InlineKeyboardButton("🎁 +", callback_data="cfg_q_pts_r_up"))
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
    else: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

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
        bot.send_message(message.chat.id,
            f"╔═══════════════════╗\n"
            f"║  🎉 <b>CODE VALID!</b>  ║\n"
            f"╚═══════════════════╝\n\n"
            f"💎 <b>+{added}</b> points!", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Invalid or used code")

def process_new_ticket(message):
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    txt = message.text.strip() if message.text else ""
    if not txt: return
    temp = bot_config.get("temp_ticket_cat", {})
    cat_key = temp.get(uid, "other")
    cat_name = TICKET_CATEGORIES.get(cat_key, {}).get(lang, "Other")
    tid = str(random.randint(10000, 99999))
    if "tickets" not in bot_config: bot_config["tickets"] = {}
    bot_config["tickets"][tid] = {
        "uid": uid, "text": txt, "status": "open",
        "category": cat_key, "date": datetime.now().isoformat(), "messages": []
    }
    if uid in temp: temp.pop(uid)
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id,
        t(lang, "ticket_created", tid=tid, category=cat_name), parse_mode="HTML")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("💬 دردشة مباشرة", callback_data=f"admchat_{tid}"))
    m.add(types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"admclosetick_{tid}"))
    try:
        bot.send_message(ADMIN_PRIMARY,
            f"╔═══════════════════╗\n"
            f"║ 🎫 <b>NEW TICKET</b> ║\n"
            f"╚═══════════════════╝\n\n"
            f"🆔 #{tid}\n"
            f"📂 {TICKET_CATEGORIES.get(cat_key, {}).get('ar', 'أخرى')}\n"
            f"👤 <code>{uid}</code> (@{u.get('username', 'N/A')})\n\n"
            f"💬 {txt}",
            reply_markup=m, parse_mode="HTML")
    except: pass

def process_product_request(message):
    uid = str(message.from_user.id)
    txt = message.text.strip() if message.text else ""
    if not txt: return
    rid = str(random.randint(10000, 99999))
    if "product_requests" not in bot_config: bot_config["product_requests"] = {}
    bot_config["product_requests"][rid] = {"uid": uid, "text": txt, "date": datetime.now().isoformat()}
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id,
        f"✅ <b>Request Sent!</b>\n\n🎫 ID: <code>#{rid}</code>", parse_mode="HTML")
    try: bot.send_message(ADMIN_PRIMARY, f"💡 <b>#{rid}</b>\n{uid}\n{txt}", parse_mode="HTML")
    except: pass

def admin_add_product(message):
    prod = message.text.strip()
    if prod in prices_config: return bot.send_message(message.chat.id, "❌ موجود")
    prices_config[prod] = {"1 Day": 20, "7 Days": 100, "30 Days": 300}
    keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"➕ أُضيف: <b>{prod}</b>", parse_mode="HTML")

def admin_del_product(message):
    prod = message.text.strip()
    if prod not in prices_config: return bot.send_message(message.chat.id, "❌")
    prices_config.pop(prod)
    keys_store.pop(prod, None)
    save_json(DB_PRICES, prices_config)
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ حُذف: <b>{prod}</b>", parse_mode="HTML")

def admin_save_price(message, prod, plan):
    try:
        p = int(message.text.strip())
        prices_config[prod][plan] = p
        save_json(DB_PRICES, prices_config)
        bot.send_message(message.chat.id, f"✅ {prod}/{plan} = <b>{p}</b>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ أرقام فقط")

def admin_save_keys(message, prod, plan):
    keys = message.text.strip().split('\n')
    added = 0
    if prod not in keys_store: keys_store[prod] = {"1 Day": [], "7 Days": [], "30 Days": []}
    for k in keys:
        if k.strip():
            keys_store[prod][plan].append(k.strip())
            added += 1
    save_json(DB_KEYS, keys_store)
    bot.send_message(message.chat.id, f"✅ +<b>{added}</b> مفتاح", parse_mode="HTML")

def admin_del_key(message, prod, plan):
    val = message.text.strip()
    keys = keys_store.get(prod, {}).get(plan, [])
    if val.isdigit() and 0 < int(val) <= len(keys):
        rm = keys.pop(int(val) - 1)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, f"✅ حُذف: <code>{rm}</code>", parse_mode="HTML")
    if val in keys:
        keys.remove(val)
        save_json(DB_KEYS, keys_store)
        return bot.send_message(message.chat.id, "✅ حُذف")
    bot.send_message(message.chat.id, "❌")

def admin_view_member(message):
    t_id = message.text.strip()
    u = get_user(t_id)
    if not u: return bot.send_message(message.chat.id, "❌")
    role = "مالك 👑" if int(t_id) == ADMIN_PRIMARY else ("أدمن 🛡️" if u.get("is_admin", False) else "عادي")
    ban = "محظور ⛔" if u.get("banned", False) else "نشط 🟢"
    msg = (f"👤 <code>{t_id}</code>\n📝 @{u.get('username', 'N/A')}\n"
           f"💰 {u.get('points', 0)} 💎\n🏆 {u.get('rank', 'عادي')}\n"
           f"🎖️ {role}\n🔴 {ban}")
    m = types.InlineKeyboardMarkup(row_width=2)
    if u.get("is_admin", False):
        m.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"admbanuser_{t_id}_demote"))
    m.add(
        types.InlineKeyboardButton("⛔ حظر دائم", callback_data=f"admbanuser_{t_id}_perm"),
        types.InlineKeyboardButton("⏱️ 24 ساعة", callback_data=f"admbanuser_{t_id}_temp")
    )
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

def admin_charge_member(message):
    try:
        p = message.text.strip().split()
        t_id, pts = p[0], int(p[1])
        if get_user(t_id):
            update_user_data(t_id, points=pts, accumulated_points=pts)
            update_user_rank_and_quests(t_id)
            bot.send_message(message.chat.id, f"💰 +<b>{pts}</b> إلى {t_id}", parse_mode="HTML")
            try:
                bot.send_message(int(t_id), f"🎉 <b>+{pts} 💎</b> من الإدارة!", parse_mode="HTML")
            except: pass
        else: bot.send_message(message.chat.id, "❌")
    except: bot.send_message(message.chat.id, "❌ ID مسافة المبلغ")

def admin_create_code(message):
    try:
        p = message.text.strip().split()
        code, pts = p[0], int(p[1])
        redeem_codes[code] = pts
        save_json(DB_REDEEM, redeem_codes)
        bot.send_message(message.chat.id, f"🎫 <code>{code}</code> = <b>{pts}</b> 💎", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌")

def admin_set_discount(message):
    try:
        d = int(message.text.strip())
        if 0 <= d < 100:
            bot_config["discount"] = d
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"🔥 خصم عام: <b>{d}%</b>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌")

def admin_broadcast(message):
    s = 0
    for u_id in get_all_user_ids():
        try:
            u_info = get_user(u_id) or {}
            if u_info.get("notifications_on", True):
                bot.send_message(int(u_id), message.text)
                s += 1
                time.sleep(0.04)
        except: pass
    bot.send_message(message.chat.id, f"📢 أُذيع لـ <b>{s}</b>", parse_mode="HTML")

def admin_edit_daily(message):
    try:
        v = int(message.text.strip())
        if v >= 0:
            bot_config["daily_gift"] = v
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ المكافأة: <b>{v}</b>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌")

def admin_edit_invite(message):
    try:
        v = int(message.text.strip())
        if v >= 0:
            bot_config["invite_reward"] = v
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ الإحالة: <b>{v}</b>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌")

# =====================================================
# 🚀 التشغيل
# =====================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 EVE Store Bot v3.0 - Starting...")
    print("=" * 50)
    print("✅ Database initialized")
    print("✅ bot2.py loaded (Giveaway + Channel)")
    print("💻 Developer: @fkLJh00302")
    print("=" * 50)
    print("🤖 Bot is now RUNNING!")
    print("=" * 50)
    bot.infinity_polling(none_stop=True, timeout=60)
