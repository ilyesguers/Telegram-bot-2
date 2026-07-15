"""
=====================================================
 bot10.py — Premium Visual Experience
=====================================================
✨ Advanced animations on every action
🎬 Welcome animation sequence
🎨 Premium-style formatting
🌍 Multi-language support

📌 Install: import bot10 in bot.py
=====================================================
"""

import random
import time
import threading
from datetime import datetime
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, t
from database import (bot_config, save_json, DB_CONFIG, get_user,
                       update_user_data, update_user_rank_and_quests,
                       get_total_users, get_bot_stats)

# =====================================================
# 🎨 Premium Design System
# =====================================================
# Using Unicode symbols that look premium on Telegram
# These work for ALL users, no Fragment needed
# =====================================================

# Box drawing characters for clean frames
L = {
    "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
    "h": "━", "v": "┃", "ml": "┣", "mr": "┫",
    "dot": "•", "arrow": "›", "line": "─",
    "bar_full": "▓", "bar_empty": "░",
}

# Animated-feel emoji sets (standard Unicode but premium look)
FIRE_SET = ["🔥", "⚡", "💥", "✨", "🌟", "💫"]
RANK_ICONS = ["🥉", "🥈", "🥇", "💎", "👑", "🏆"]
STATUS_ICONS = {"online": "🟢", "away": "🟡", "busy": "🔴", "vip": "👑"}

# Multi-language UI texts
UI = {
    "ar": {
        "welcome_loading": "⚡ جاري التحميل",
        "welcome_security": "🛡️ فحص الأمان",
        "welcome_profile": "📊 تحميل الملف الشخصي",
        "welcome_ready": "✅ جاهز",
        "welcome_final": "مرحباً بك",
        "balance": "الرصيد",
        "rank": "الرتبة",
        "streak": "السلسلة",
        "invites": "الدعوات",
        "member_since": "عضو منذ",
        "today_bonus": "مكافأة اليوم",
        "shop_ready": "المتجر جاهز",
        "vip_badge": "عضو مميز",
        "level": "المستوى",
    },
    "en": {
        "welcome_loading": "⚡ Loading",
        "welcome_security": "🛡️ Security Check",
        "welcome_profile": "📊 Loading Profile",
        "welcome_ready": "✅ Ready",
        "welcome_final": "Welcome",
        "balance": "Balance",
        "rank": "Rank",
        "streak": "Streak",
        "invites": "Invites",
        "member_since": "Member Since",
        "today_bonus": "Today's Bonus",
        "shop_ready": "Shop Ready",
        "vip_badge": "Premium Member",
        "level": "Level",
    },
    "fr": {
        "welcome_loading": "⚡ Chargement",
        "welcome_security": "🛡️ Vérification",
        "welcome_profile": "📊 Chargement du profil",
        "welcome_ready": "✅ Prêt",
        "welcome_final": "Bienvenue",
        "balance": "Solde",
        "rank": "Rang",
        "streak": "Série",
        "invites": "Invitations",
        "member_since": "Membre depuis",
        "today_bonus": "Bonus du jour",
        "shop_ready": "Boutique prête",
        "vip_badge": "Membre Premium",
        "level": "Niveau",
    },
    "es": {
        "welcome_loading": "⚡ Cargando",
        "welcome_security": "🛡️ Verificación",
        "welcome_profile": "📊 Cargando perfil",
        "welcome_ready": "✅ Listo",
        "welcome_final": "Bienvenido",
        "balance": "Saldo",
        "rank": "Rango",
        "streak": "Racha",
        "invites": "Invitaciones",
        "member_since": "Miembro desde",
        "today_bonus": "Bono de hoy",
        "shop_ready": "Tienda lista",
        "vip_badge": "Miembro Premium",
        "level": "Nivel",
    },
    "vi": {
        "welcome_loading": "⚡ Đang tải",
        "welcome_security": "🛡️ Kiểm tra",
        "welcome_profile": "📊 Tải hồ sơ",
        "welcome_ready": "✅ Sẵn sàng",
        "welcome_final": "Chào mừng",
        "balance": "Số dư",
        "rank": "Cấp",
        "streak": "Chuỗi",
        "invites": "Lời mời",
        "member_since": "Thành viên từ",
        "today_bonus": "Thưởng hôm nay",
        "shop_ready": "Cửa hàng sẵn sàng",
        "vip_badge": "Thành viên cao cấp",
        "level": "Cấp độ",
    },
}

def ui(lang, key):
    return UI.get(lang, UI["en"]).get(key, UI["en"].get(key, key))


# =====================================================
# 📊 Helper Functions
# =====================================================
def is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except:
        pass
    u = get_user(str(uid)) or {}
    return u.get("is_admin", False)


def format_number(n):
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    elif n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def progress_bar(current, total, length=10):
    if total <= 0:
        return L["bar_empty"] * length
    filled = min(int((current / total) * length), length)
    return L["bar_full"] * filled + L["bar_empty"] * (length - filled)


def get_level(points):
    levels = [
        (0, "Rookie", "🔰"),
        (100, "Starter, "Fighter", "⚔️"),
        (600, "Warrior", "🛡️"),
        (1000, "Elite", "💠"),
        (2000, "Master", "🔱"),
        (4000, "Champion", "🏅"),
        (7000, "Legend", "🌟"),
        (12000, "Mythic", "💎"),
        (20000, "Immortal", "👑"),
    ]
    result = levels[0]
    for threshold, name, icon in levels:
        if points >= threshold:
            result = (threshold, name, icon)
    
    idx = next((i for i, l in enumerate(levels) if l[0] == result[0]), 0)
    
    if idx < len(levels) - 1:
        next_threshold = levels[idx + 1][0]
        progress = points - result[0]
        needed = next_threshold - result[0]
    else:
        progress = 1
        needed = 1
    
    return {
        "name": result[1],
        "icon": result[2],
        "level": idx + 1,
        "progress": progress,
        "needed": needed,
        "next": levels[idx + 1][1] if idx < len(levels) - 1 else "MAX"
    }


def is_vip(uid):
    uid = str(uid)
    vip_data = bot_config.get("vip_subscribers", {}).get(uid)
    if not vip_data:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(vip_data.get("expires", "2000-01-01"))
    except:
        return False


def get_time_greeting(lang):
    hour = datetime.now().hour
    if lang == "ar":
        if hour < 12:
            return "صباح الخير ☀️"
        elif hour < 18:
            return "مساء الخير 🌤️"
        else:
            return "مساء النور 🌙"
    else:
        if hour < 12:
            return "Good Morning ☀️"
        elif hour < 18:
            return "Good Afternoon 🌤️"
        else:
            return "Good Evening 🌙"


# =====================================================
# 🎬 Welcome Animation System
# =====================================================
def play_welcome_animation(chat_id, uid):
    """Premium welcome animation sequence"""
    u = get_user(uid)
    if not u:
        return
    
    lang = u.get("lang", "en")
    name = u.get("username") or "User"
    points = u.get("points", 0)
    acc_pts = u.get("accumulated_points", 0)
    rank_name = u.get("rank", "Member")
    streak = u.get("streak_days", 0)
    invite_count = u.get("invite_count", 0)
    join_date = u.get("join_date", "")[:10]
    vip_status = is_vip(uid)
    level_info = get_level(acc_pts)
    greeting = get_time_greeting(lang)
    
    vip_tag = "  👑 VIP" if vip_status else ""
    
    # Frame 1: Loading
    frame1 = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  {ui(lang, 'welcome_loading')}           ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"   ░░░░░░░░░░  10%"
    )
    
    # Frame 2: Security
    frame2 = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  {ui(lang, 'welcome_security')}       ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"   ▓▓▓▓░░░░░░  40%"
    )
    
    # Frame 3: Profile
    frame3 = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  {ui(lang, 'welcome_profile')}     ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"   ▓▓▓▓▓▓▓░░░  70%"
    )
    
    # Frame 4: Ready
    frame4 = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  {ui(lang, 'welcome_ready')}             ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"   ▓▓▓▓▓▓▓▓▓▓  100%"
    )
    
    # Frame 5: Final Welcome
    level_bar = progress_bar(level_info["progress"], level_info["needed"], 8)
    
    frame5 = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  {greeting}                   ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   👤  @{name}{vip_tag}\n\n"

        f"   {level_info['icon']}  {level_info['name']}  ›  Lv.{level_info['level']}\n"
        f"   {level_bar}  › {level_info['next']}\n\n"

        f"   ┌─────────────────────┐\n"
        f"   │ 💎  {ui(lang, 'balance')}:  {format_number(points)}\n"
        f"   │ 🏆  {ui(lang, 'rank')}:  {rank_name}\n"
        f"   │ 🔥  {ui(lang, 'streak')}:  {streak} days\n"
        f"   │ 👥  {ui(lang, 'invites')}:  {invite_count}\n"
        f"   │ 📅  {ui(lang, 'member_since')}:  {join_date}\n"
        f"   └─────────────────────┘"
    )
    
    # Play animation
    try:
        msg = bot.send_message(chat_id, frame1, parse_mode="HTML")
        time.sleep(0.4)
        
        for frame in [frame2, frame3, frame4]:
            try:
                bot.edit_message_text(frame, chat_id, msg.message_id, parse_mode="HTML")
                time.sleep(0.35)
            except:
                pass
        
        time.sleep(0.3)
        try:
            bot.edit_message_text(frame5, chat_id, msg.message_id, parse_mode="HTML")
        except:
            pass
        
    except Exception as e:
        print(f"⚠️ Welcome animation error: {e}")


# =====================================================
# 🔌 Hook into /start command
# =====================================================
# We override the welcome message in bot.py's show_main_menu
# by monkey-patching it
# =====================================================

# Store reference to original show_main_menu from bot.py
_original_show_main_menu = None

def _find_and_patch():
    """Find show_main_menu in bot.py and enhance it"""
    import sys
    
    # Get the main bot module
    main_module = sys.modules.get("__main__")
    if not main_module:
        return
    
    global _original_show_main_menu
    
    if hasattr(main_module, "show_main_menu"):
        _original_show_main_menu = main_module.show_main_menu
        
        def enhanced_show_main_menu(chat_id, uid, lang):
            # Play welcome animation first
            play_welcome_animation(chat_id, uid)
            time.sleep(0.5)
            
            # Then show original menu
            if _original_show_main_menu:
                _original_show_main_menu(chat_id, uid, lang)
        
        main_module.show_main_menu = enhanced_show_main_menu
        print("✅ bot10: show_main_menu enhanced!")


# Delay patching to ensure bot.py is fully loaded
def _delayed_patch():
    time.sleep(3)
    _find_and_patch()

threading.Thread(target=_delayed_patch, daemon=True).start()


# =====================================================
# 💰 Enhanced Balance Display
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_balance")
def enhanced_balance(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    
    points = u.get("points", 0)
    acc = u.get("accumulated_points", 0)
    rank_name = u.get("rank", "Member")
    rank_disc = u.get("rank_discount", 0) or 0
    streak = u.get("streak_days", 0)
    invites = u.get("invite_count", 0)
    purchases = u.get("purchases_count", 0)
    spent = u.get("total_spent", 0)
    ref_earnings = u.get("referral_earnings", 0)
    vip_status = is_vip(uid)
    level_info = get_level(acc)
    
    vip_line = "   👑  VIP:  Active\n" if vip_status else ""
    
    level_bar = progress_bar(level_info["progress"], level_info["needed"], 12)
    
    # Animation
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # Loading frame
    try:
        bot.edit_message_text(
            "   💎 Loading wallet...",
            chat_id, msg_id, parse_mode="HTML")
        time.sleep(0.4)
    except:
        pass
    
    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃      💎  WALLET  💎          ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   {level_info['icon']}  {level_info['name']}  ›  Lv.{level_info['level']}\n"
        f"   {level_bar}\n"
        f"   {format_number(level_info['progress'])} / {format_number(level_info['needed'])}  ›  {level_info['next']}\n\n"

        f"   ┌─── 💰 ───────────────────┐\n"
        f"   │\n"
        f"   │  💎  {ui(lang, 'balance')}:  {format_number(points)}\n"
        f"   │  📊  Total:  {format_number(acc)}\n"
        f"   │  🏆  {ui(lang, 'rank')}:  {rank_name}\n"
        f"   │  🎯  Discount:  {int(rank_disc * 100)}%\n"
        f"{vip_line}"
        f"   │\n"
        f"   ├─── 📈 ───────────────────┤\n"
        f"   │\n"
        f"   │  🔥  {ui(lang, 'streak')}:  {streak} days\n"
        f"   │  👥  {ui(lang, 'invites')}:  {invites}\n"
        f"   │  💵  Referral:  {format_number(ref_earnings)}\n"
        f"   │  🛒  Orders:  {purchases}\n"
        f"   │  💸  Spent:  {format_number(spent)}\n"
        f"   │\n"
        f"   └─────────────────────────┘"
    )
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🏆 Enhanced Rank Display
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_rank")
def enhanced_rank(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    
    acc = u.get("accumulated_points", 0) or 0
    current_rank = u.get("rank", "Member")
    
    from config import RANKS
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    try:
        bot.edit_message_text("   🏆 Loading ranks...", chat_id, msg_id)
        time.sleep(0.3)
    except:
        pass
    
    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃      🏆  RANKS  🏆          ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"   📊  Your Points:  {format_number(acc)}\n"
        f"   🏅  Current:  {current_rank}\n\n"
        f"   ┌─────────────────────────┐\n"
    )
    
    rank_order = ["silver", "gold", "diamond", "hero", "master", "legend"]
    
    for rank_key in rank_order:
        rank_info = RANKS[rank_key]
        needed = rank_info["points_needed"]
        discount = int(rank_info["discount"] * 100)
        
        lang_key = f"name_{lang}" if f"name_{lang}" in rank_info else "name_en"
        rank_name = rank_info.get(lang_key, rank_info.get("name_en", rank_key))
        
        if acc >= needed:
            status = "✅"
            bar = progress_bar(1, 1, 6)
        else:
            status = "🔒"
            bar = progress_bar(acc, needed, 6)
        
        msg += (
            f"   │  {status}  {rank_name}\n"
            f"   │     {bar}  {format_number(acc)}/{format_number(needed)}\n"
            f"   │     🎯 Discount: {discount}%\n"
            f"   │\n"
        )
    
    msg += f"   └─────────────────────────┘"
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🔗 Enhanced Referral Display
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_referral")
def enhanced_referral(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    
    invites = u.get("invite_count", 0) or 0
    ref_earnings = u.get("referral_earnings", 0) or 0
    reward = bot_config.get("invite_reward", 20)
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    
    link = f"https://t.me/{bot_user}?start={uid}"
    
    # Milestones
    milestones = [5, 10, 25, 50, 100]
    next_milestone = 0
    for ms in milestones:
        if invites < ms:
            next_milestone = ms
            break
    
    if next_milestone > 0:
        ms_bar = progress_bar(invites, next_milestone, 8)
        ms_text = f"   │  🎯  Next:  {ms_bar}  {invites}/{next_milestone}\n"
    else:
        ms_text = f"   │  🎯  Status:  🏆 MAXED OUT\n"
    
    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃     🔗  REFERRAL  🔗        ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   ┌─────────────────────────┐\n"
        f"   │  👥  {ui(lang, 'invites')}:  {invites}\n"
        f"   │  🎁  Per Invite:  {reward} pts\n"
        f"   │  💵  Earnings:  {format_number(ref_earnings)}\n"
        f"{ms_text}"
        f"   └─────────────────────────┘\n\n"

        f"   📎  Your Link:\n"
        f"   <code>{link}</code>\n\n"

        f"   💡  Share & earn {reward} pts each!"
    )
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 📊 Enhanced About / Bot Info
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_about")
def enhanced_about(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    try:
        bot.edit_message_text("   ℹ️ Loading info...", chat_id, msg_id)
        time.sleep(0.3)
    except:
        pass
    
    stats = get_bot_stats()
    uptime_date = bot_config.get("bot_launch_date", "")[:10]
    
    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃      ℹ️  ABOUT  ℹ️          ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   🤖  EVE Store Bot\n"
        f"   📦  Version:  3.0\n"
        f"   📅  Since:  {uptime_date}\n\n"

        f"   ┌─── 📊 Stats ────────────┐\n"
        f"   │\n"
        f"   │  👥  Users:  {format_number(stats.get('total_users', 0))}\n"
        f"   │  🟢  Active Today:  {stats.get('active_today', 0)}\n"
        f"   │  🛒  Total Sales:  {format_number(stats.get('total_sales', 0))}\n"
        f"   │  📦  Products:  {stats.get('total_products', 0)}\n"
        f"   │  🎫  Tickets:  {stats.get('total_tickets', 0)}\n"
        f"   │\n"
        f"   └─────────────────────────┘\n\n"

        f"   ⚡  Powered by Latest Tech\n"
        f"   🔒  Secure Transactions\n"
        f"   🌍  Multi-Language"
    )
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# ✨ Enhanced Daily Bonus
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_daily")
def enhanced_daily(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    last_claim = u.get("last_claim")
    streak = u.get("streak_days", 0) or 0
    
    can_claim = True
    if last_claim:
        try:
            last = datetime.fromisoformat(last_claim)
            diff = datetime.now() - last
            if diff.total_seconds() < 86400:
                can_claim = False
                remaining = 86400 - diff.total_seconds()
                hours = int(remaining // 3600)
                mins = int((remaining % 3600) // 60)
        except:
            pass
    
    if can_claim:
        # Claim animation
        try:
            bot.edit_message_text("   🎁 Opening...", chat_id, msg_id)
            time.sleep(0.3)
            bot.edit_message_text("   🎁 ✨ ...", chat_id, msg_id)
            time.sleep(0.3)
        except:
            pass
        
        gift = bot_config.get("daily_gift", 10)
        vip_active = is_vip(uid)
        
        if vip_active:
            gift = gift * 2
        
        streak_bonus = 0
        
        # Check if streak continues
        if last_claim:
            try:
                last = datetime.fromisoformat(last_claim)
                diff = datetime.now() - last
                if diff.total_seconds() < 172800:  # 48h
                    streak += 1
                    if streak % 7 == 0:
                        streak_bonus = gift
                else:
                    streak = 1
            except:
                streak = 1
        else:
            streak = 1
        
        total = gift + streak_bonus
        
        update_user_data(uid,
            points=total,
            accumulated_points=total,
            streak_days=1 if streak == 1 else 0,
            last_claim=datetime.now().isoformat(),
            last_streak_date=datetime.now().isoformat())
        
        if streak > 1:
            update_user_data(uid, streak_days=streak - u.get("streak_days", 0))
        
        update_user_rank_and_quests(uid)
        u_new = get_user(uid) or {}
        
        streak_line = ""
        if streak_bonus > 0:
            streak_line = f"   │  🔥  Streak Bonus:  +{streak_bonus}\n"
        
        vip_line = ""
        if vip_active:
            vip_line = f"   │  👑  VIP 2x Bonus!\n"
        
        msg = (
            f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃     🎁  DAILY BONUS  🎁     ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

            f"   ┌─────────────────────────┐\n"
            f"   │  💎  Reward:  +{gift}\n"
            f"{vip_line}"
            f"{streak_line}"
            f"   │  🔥  Streak:  {streak} days\n"
            f"   │  💰  Balance:  {u_new.get('points', 0)}\n"
            f"   └─────────────────────────┘\n\n"

            f"   ⏰  Next in 24 hours"
        )
    else:
        # Already claimed
        streak_days_display = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        current_day = streak % 7
        
        streak_visual = ""
        for i in range(7):
            if i < current_day:
                streak_visual += "🟢 "
            elif i == current_day:
                streak_visual += "🟡 "
            else:
                streak_visual += "⚫ "
        
        msg = (
            f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃     ⏰  COME BACK LATER  ⏰  ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

            f"   ⏳  {hours}h {mins}m remaining\n\n"

            f"   🔥  Streak:  {streak} days\n"
            f"   {streak_visual}\n\n"

            f"   💡  Don't break your streak!"
        )
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🔥 Enhanced Quests Display
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_quests")
def enhanced_quests(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    completed = u.get("completed_quests", "") or ""
    invites = u.get("invite_count", 0) or 0
    acc_pts = u.get("accumulated_points", 0) or 0
    
    # Count user purchases
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    
    quests = bot_config.get("quests", {})
    
    q_invite = quests.get("invite", {"target": 5, "reward": 100})
    q_buy = quests.get("buy", {"target": 3, "reward": 150})
    q_points = quests.get("points", {"target": 1000, "reward": 200})
    
    invite_done = "quest_invite" in completed
    buy_done = "quest_buy" in completed
    points_done = "quest_points" in completed
    
    def quest_line(icon, name, current, target, reward, done):
        if done:
            return (
                f"   │  {icon}  {name}\n"
                f"   │     ✅  COMPLETED  │  +{reward} pts\n"
                f"   │\n"
            )
        else:
            bar = progress_bar(min(current, target), target, 8)
            return (
                f"   │  {icon}  {name}\n"
                f"   │     {bar}  {current}/{target}\n"
                f"   │     🎁  Reward:  {reward} pts\n"
                f"   │\n"
            )
    
    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃      🔥  QUESTS  🔥         ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   ┌─────────────────────────┐\n"
        f"{quest_line('👥', 'Invite Friends', invites, q_invite['target'], q_invite['reward'], invite_done)}"
        f"{quest_line('🛒', 'Make Purchases', user_buys, q_buy['target'], q_buy['reward'], buy_done)}"
        f"{quest_line('💎', 'Earn Points', acc_pts, q_points['target'], q_points['reward'], points_done)}"
        f"   └─────────────────────────┘"
    )
    
    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 📖 /pp Command Guide
# =====================================================
@bot.message_handler(commands=['pp'])
def show_commands_guide(message):
    uid = str(message.from_user.id)
    adm = is_admin(uid)
    
    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃   📖  COMMANDS GUIDE  📖    ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        "⚡  USER\n"
        "   /start  ›  Main Menu\n"
        "   /id  ›  Your Info\n"
        "   /help  ›  Help\n"
        "   /close  ›  Close Ticket\n"
        "   /pp  ›  This Guide\n\n"

        "🛍️  SECTIONS\n"
        "   👤 Account  ›  Balance, Rank\n"
        "   🛍️ Shop  ›  Buy Products\n"
        "   🎁 Rewards  ›  Daily, Codes, Quests\n"
        "   🎮 Fun  ›  Wheel, Lootbox\n"
        "   🎮 Mini Games  ›  RPS, TTT, Hunt\n"
        "   💬 Support  ›  Tickets\n"
        "   ⚙️ Settings  ›  Language, Theme\n"
        "   👑 VIP  ›  Premium\n"
        "   ⭐ Stars  ›  Convert Stars\n"
    )
    
    if adm:
        msg += (
            "\n🔐  ADMIN\n"
            "   /stars  ›  Stars Panel\n"
            "   /comp  ›  Competitions\n\n"

            "📋  ADMIN SECTIONS\n"
            "   📦 Products  ›  Add/Remove\n"
            "   🔑 Keys  ›  Stock\n"
            "   👥 Members  ›  Manage\n"
            "   🎫 Tickets  ›  Support\n"
            "   💰 Sales  ›  Codes/Discounts\n"
            "   📢 Marketing  ›  Broadcast\n"
            "   ⚡ Flash Sales\n"
            "   🎁 Giveaway\n"
            "   👑 VIP Mgmt\n"
            "   📦 Auto-Restock\n"
            "   🎮 Games Config\n"
            "   🛡️ Anti-Spam\n"
            "   🔧 Recovery\n"
            "   ⚙️ System\n"
            "   📊 Statistics\n"
            "   🛠️ Maintenance\n"
        )
    
    bot.send_message(message.chat.id, msg, parse_mode="HTML")


# =====================================================
# Done
# =====================================================
print("=" * 55)
print("✅ bot10.py v2.0 — Premium Visual Experience")
print("🎬 Welcome Animation: Active")
print("💎 Enhanced Wallet: Active")
print("🏆 Enhanced Ranks: Active")
print("🔥 Enhanced Quests: Active")
print("📖 Commands Guide: /pp")
print("=" * 55)
