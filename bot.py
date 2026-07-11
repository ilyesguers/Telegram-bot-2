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
    if check_spam(uid): return
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
            except: pass
