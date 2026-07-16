"""
=====================================================
 bot10.py — Premium Visual Experience v3.0
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
from database import (bot_config, save_json, DB_CONFIG, get_user, update_user_data,
                      update_user_rank_and_quests, get_total_users, get_bot_stats)

# =====================================================
# 🎨 PREMIUM EMOJI SETS
# =====================================================

# Animated-style emoji combinations
SPARKLE = ["✦", "✧", "⋆", "˚", "°", "•"]
FIRE_ANIM = ["🔥", "🔥", "💥", "⚡", "✨", "💫"]
HEARTS = ["💜", "💙", "💚", "💛", "🧡", "❤️", "🤍"]
STARS = ["⭐", "🌟", "💫", "✨", "⚡"]
DIAMONDS = ["💎", "💠", "🔹", "🔷", "♦️"]
CROWNS = ["👑", "🏆", "🎖️", "🥇", "⚜️"]
GIFTS = ["🎁", "🎀", "🎊", "🎉", "🎈"]
MONEY = ["💰", "💵", "💴", "💶", "💷", "🪙", "💲"]

# Loading animation frames
LOADING_FRAMES = [
    "░░░░░░░░░░",
    "█░░░░░░░░░",
    "██░░░░░░░░",
    "███░░░░░░░",
    "████░░░░░░",
    "█████░░░░░",
    "██████░░░░",
    "███████░░░",
    "████████░░",
    "█████████░",
    "██████████",
]

LOADING_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PULSE_ANIM = ["○", "◔", "◑", "◕", "●", "◕", "◑", "◔"]

# Box drawing characters
BOX = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║", "ml": "╠", "mr": "╣",
    "tl2": "┏", "tr2": "┓", "bl2": "┗", "br2": "┛",
    "h2": "━", "v2": "┃",
    "tl3": "╭", "tr3": "╮", "bl3": "╰", "br3": "╯",
    "h3": "─", "v3": "│",
}

# =====================================================
# 🌍 MULTI-LANGUAGE UI
# =====================================================

UI = {
    "ar": {
        "loading": "جـاري التحمـيل",
        "checking": "جـاري الفحـص",
        "ready": "جـاهـز",
        "welcome": "أهـلاً وسهـلاً",
        "balance": "الرصيـد",
        "rank": "الرتبـة",
        "discount": "الخصـم",
        "streak": "السلسلـة",
        "invites": "الدعـوات",
        "earnings": "الأربـاح",
        "member_since": "عضـو منـذ",
        "total": "المجمـوع",
        "reward": "المكـافأة",
        "claimed": "تـم الاستـلام",
        "wait": "انتظـر",
        "hours": "سـاعة",
        "minutes": "دقيقـة",
        "days": "يـوم",
        "your_link": "رابطـك",
        "share": "شـارك",
        "per_invite": "لكـل دعـوة",
        "progress": "التقـدم",
        "completed": "مكتمـل",
        "locked": "مغلـق",
        "users": "مستخـدم",
        "sales": "مبيعـات",
        "products": "منتجـات",
        "version": "الإصـدار",
        "online": "متصـل",
        "vip": "مميـز",
        "new_member": "عضـو جديـد",
        "keep_streak": "حـافظ علـى سلسلتـك",
        "next_goal": "الهـدف التـالي",
        "congrats": "مبـروك",
        "bonus": "بونـص",
    },
    "en": {
        "loading": "Loading",
        "checking": "Checking",
        "ready": "Ready",
        "welcome": "Welcome",
        "balance": "Balance",
        "rank": "Rank",
        "discount": "Discount",
        "streak": "Streak",
        "invites": "Invites",
        "earnings": "Earnings",
        "member_since": "Member Since",
        "total": "Total",
        "reward": "Reward",
        "claimed": "Claimed",
        "wait": "Wait",
        "hours": "hours",
        "minutes": "minutes",
        "days": "days",
        "your_link": "Your Link",
        "share": "Share",
        "per_invite": "Per Invite",
        "progress": "Progress",
        "completed": "Completed",
        "locked": "Locked",
        "users": "Users",
        "sales": "Sales",
        "products": "Products",
        "version": "Version",
        "online": "Online",
        "vip": "VIP",
        "new_member": "New Member",
        "keep_streak": "Keep Your Streak",
        "next_goal": "Next Goal",
        "congrats": "Congrats",
        "bonus": "Bonus",
    },
    "fr": {
        "loading": "Chargement",
        "checking": "Vérification",
        "ready": "Prêt",
        "welcome": "Bienvenue",
        "balance": "Solde",
        "rank": "Rang",
        "discount": "Remise",
        "streak": "Série",
        "invites": "Invitations",
        "earnings": "Gains",
        "member_since": "Membre depuis",
        "total": "Total",
        "reward": "Récompense",
        "claimed": "Réclamé",
        "wait": "Attendre",
        "hours": "heures",
        "minutes": "minutes",
        "days": "jours",
        "your_link": "Votre lien",
        "share": "Partager",
        "per_invite": "Par invitation",
        "progress": "Progrès",
        "completed": "Terminé",
        "locked": "Verrouillé",
        "users": "Utilisateurs",
        "sales": "Ventes",
        "products": "Produits",
        "version": "Version",
        "online": "En ligne",
        "vip": "VIP",
        "new_member": "Nouveau",
        "keep_streak": "Gardez votre série",
        "next_goal": "Prochain objectif",
        "congrats": "Félicitations",
        "bonus": "Bonus",
    },
    "es": {
        "loading": "Cargando",
        "checking": "Verificando",
        "ready": "Listo",
        "welcome": "Bienvenido",
        "balance": "Saldo",
        "rank": "Rango",
        "discount": "Descuento",
        "streak": "Racha",
        "invites": "Invitaciones",
        "earnings": "Ganancias",
        "member_since": "Miembro desde",
        "total": "Total",
        "reward": "Recompensa",
        "claimed": "Reclamado",
        "wait": "Esperar",
        "hours": "horas",
        "minutes": "minutos",
        "days": "días",
        "your_link": "Tu enlace",
        "share": "Compartir",
        "per_invite": "Por invitación",
        "progress": "Progreso",
        "completed": "Completado",
        "locked": "Bloqueado",
        "users": "Usuarios",
        "sales": "Ventas",
        "products": "Productos",
        "version": "Versión",
        "online": "En línea",
        "vip": "VIP",
        "new_member": "Nuevo",
        "keep_streak": "Mantén tu racha",
        "next_goal": "Siguiente meta",
        "congrats": "Felicidades",
        "bonus": "Bono",
    },
    "vi": {
        "loading": "Đang tải",
        "checking": "Đang kiểm tra",
        "ready": "Sẵn sàng",
        "welcome": "Chào mừng",
        "balance": "Số dư",
        "rank": "Cấp",
        "discount": "Giảm giá",
        "streak": "Chuỗi",
        "invites": "Lời mời",
        "earnings": "Thu nhập",
        "member_since": "Thành viên từ",
        "total": "Tổng",
        "reward": "Phần thưởng",
        "claimed": "Đã nhận",
        "wait": "Đợi",
        "hours": "giờ",
        "minutes": "phút",
        "days": "ngày",
        "your_link": "Liên kết",
        "share": "Chia sẻ",
        "per_invite": "Mỗi lời mời",
        "progress": "Tiến độ",
        "completed": "Hoàn thành",
        "locked": "Khóa",
        "users": "Người dùng",
        "sales": "Bán hàng",
        "products": "Sản phẩm",
        "version": "Phiên bản",
        "online": "Trực tuyến",
        "vip": "VIP",
        "new_member": "Mới",
        "keep_streak": "Giữ chuỗi",
        "next_goal": "Mục tiêu tiếp",
        "congrats": "Chúc mừng",
        "bonus": "Thưởng",
    },
}


def ui(lang, key):
    return UI.get(lang, UI["en"]).get(key, UI["en"].get(key, key))


# =====================================================
# 🔧 HELPER FUNCTIONS
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
    """Format numbers: 1500 → 1.5K, 1500000 → 1.5M"""
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    elif n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def progress_bar(current, total, length=10):
    """Create visual progress bar"""
    if total <= 0:
        return "█" * length
    ratio = min(current / total, 1.0)
    filled = int(length * ratio)
    empty = length - filled
    return f"{'█' * filled}{'░' * empty}"


def progress_bar_detailed(current, total, length=10):
    """Create detailed progress bar with percentage"""
    if total <= 0:
        return f"{'█' * length} 100%"
    ratio = min(current / total, 1.0)
    filled = int(length * ratio)
    empty = length - filled
    percent = int(ratio * 100)
    return f"{'█' * filled}{'░' * empty} {percent}%"


def streak_visual(streak_days):
    """Create 7-day streak visualization"""
    day_in_week = streak_days % 7
    result = ""
    for i in range(7):
        if i < day_in_week:
            result += "🟢"
        elif i == day_in_week:
            result += "🟡"
        else:
            result += "⚫"
    return result


def random_sparkle():
    """Get random sparkle decoration"""
    return random.choice(SPARKLE)


def decorate(text):
    """Add sparkle decorations to text"""
    s = random_sparkle()
    return f"{s} {text} {s}"


def get_rank_emoji(rank_name):
    """Get emoji for rank"""
    if "legend" in rank_name.lower() or "أسطورة" in rank_name:
        return "🏆"
    elif "master" in rank_name.lower() or "ماستر" in rank_name:
        return "👑"
    elif "hero" in rank_name.lower() or "هيرو" in rank_name:
        return "⚡"
    elif "diamond" in rank_name.lower() or "ماسي" in rank_name:
        return "💎"
    elif "gold" in rank_name.lower() or "ذهبي" in rank_name:
        return "🥇"
    elif "silver" in rank_name.lower() or "فضي" in rank_name:
        return "🥈"
    return "🔹"


# =====================================================
# 🎬 ANIMATION ENGINE
# =====================================================

def animate_loading(chat_id, msg_id, steps=5, delay=0.25):
    """Animate loading bar"""
    for i in range(0, 11, max(1, 11 // steps)):
        try:
            frame = LOADING_FRAMES[min(i, 10)]
            bot.edit_message_text(
                f"⏳ {frame}",
                chat_id, msg_id
            )
            time.sleep(delay)
        except:
            pass


def animate_text(chat_id, msg_id, frames, delay=0.3):
    """Animate through text frames"""
    for frame in frames:
        try:
            bot.edit_message_text(frame, chat_id, msg_id, parse_mode="HTML")
            time.sleep(delay)
        except:
            pass


# =====================================================
# 💰 PREMIUM WALLET DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_balance")
def premium_wallet(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # ═══ Animation Sequence ═══
    frames = [
        f"✨ {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[2]}",
        f"💫 {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[5]}",
        f"🔮 {ui(lang, 'checking')}...\n\n{LOADING_FRAMES[8]}",
        f"✅ {ui(lang, 'ready')}!\n\n{LOADING_FRAMES[10]}",
    ]
    animate_text(chat_id, msg_id, frames, 0.25)
    time.sleep(0.2)

    # ═══ Get User Data ═══
    points = u.get("points", 0) or 0
    rank = u.get("rank", ui(lang, "new_member"))
    discount = u.get("rank_discount", 0) or 0
    invites = u.get("invite_count", 0) or 0
    acc = u.get("accumulated_points", 0) or 0
    streak = u.get("streak_days", 0) or 0
    vip = u.get("vip", False)
    join_date = (u.get("join_date") or "")[:10]
    rank_emoji = get_rank_emoji(rank)

    # ═══ Build Message ═══
    vip_badge = ""
    if vip:
        vip_badge = f"\n   👑 {ui(lang, 'vip').upper()} 👑"

    streak_bar = streak_visual(streak)

    msg = f"""
╔══════════════════════════════╗
║  💎  {ui(lang, 'balance').upper()}  💎  ║
╚══════════════════════════════╝
{vip_badge}

┌─────────────────────────────┐
│
│  💰 {ui(lang, 'balance')}: {format_number(points)} 💎
│  {rank_emoji} {ui(lang, 'rank')}: {rank}
│  🎯 {ui(lang, 'discount')}: {int(discount * 100)}%
│
│  🔥 {ui(lang, 'streak')}: {streak} {ui(lang, 'days')}
│     {streak_bar}
│
│  👥 {ui(lang, 'invites')}: {invites}
│  📊 {ui(lang, 'total')}: {format_number(acc)}
│  📅 {ui(lang, 'member_since')}: {join_date}
│
└─────────────────────────────┘

    ✨ {decorate(ui(lang, 'welcome'))} ✨
"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🏆 PREMIUM RANK DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_rank")
def premium_rank(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # ═══ Animation ═══
    frames = [
        f"🏆 {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[3]}",
        f"⭐ {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[7]}",
        f"✅ {ui(lang, 'ready')}!\n\n{LOADING_FRAMES[10]}",
    ]
    animate_text(chat_id, msg_id, frames, 0.25)
    time.sleep(0.2)

    acc = u.get("accumulated_points", 0) or 0

    # Rank levels
    ranks = [
        (200, "🥈 Silver", 1),
        (600, "🥇 Gold", 2),
        (1500, "💎 Diamond", 3),
        (3500, "⚡ Hero", 4),
        (7000, "👑 Master", 4.5),
        (12000, "🏆 Legend", 5),
    ]

    # Find current rank
    current_rank = "🔹 " + ui(lang, "new_member")
    current_discount = 0
    for pts, name, disc in ranks:
        if acc >= pts:
            current_rank = name
            current_discount = disc

    msg = f"""
╔══════════════════════════════╗
║  🏆  {ui(lang, 'rank').upper()}  🏆  ║
╚══════════════════════════════╝

   ⭐ {current_rank}
   📊 {format_number(acc)} {ui(lang, 'total')}
   🎯 {ui(lang, 'discount')}: {current_discount}%

┌─────────────────────────────┐
│  📈 {ui(lang, 'progress')}
│
"""

    for needed, rank_name, disc in ranks:
        if acc >= needed:
            status = "✅"
            bar = progress_bar(1, 1, 8)
        else:
            status = "🔒"
            bar = progress_bar(acc, needed, 8)

        msg += f"""│  {status} {rank_name}
│     {bar}
│     {format_number(acc)}/{format_number(needed)} • {disc}%
│
"""

    msg += """└─────────────────────────────┘

   💪 Keep earning points!"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🔗 PREMIUM REFERRAL DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_referral")
def premium_referral(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # ═══ Animation ═══
    frames = [
        f"🔗 {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[4]}",
        f"✅ {ui(lang, 'ready')}!\n\n{LOADING_FRAMES[10]}",
    ]
    animate_text(chat_id, msg_id, frames, 0.3)
    time.sleep(0.2)

    invites = u.get("invite_count", 0) or 0
    ref_earnings = u.get("referral_earnings", 0) or 0
    reward = bot_config.get("invite_reward", 20)

    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    link = f"https://t.me/{bot_user}?start={uid}"

    # Milestones
    milestones = [5, 10, 25, 50, 100]
    next_ms = 0
    for ms in milestones:
        if invites < ms:
            next_ms = ms
            break

    # Trophy based on invites
    if invites >= 100:
        trophy = "🏆"
    elif invites >= 50:
        trophy = "👑"
    elif invites >= 25:
        trophy = "💎"
    elif invites >= 10:
        trophy = "🥇"
    elif invites >= 5:
        trophy = "🥈"
    else:
        trophy = "🥉"

    milestone_bar = ""
    if next_ms > 0:
        milestone_bar = f"""
│  🎯 {ui(lang, 'next_goal')}: {next_ms}
│     {progress_bar_detailed(invites, next_ms, 10)}
│"""
    else:
        milestone_bar = f"""
│  🏆 MAX LEVEL REACHED!
│"""

    msg = f"""
╔══════════════════════════════╗
║  🔗  REFERRAL  🔗  ║
╚══════════════════════════════╝

   {trophy} Level: {invites} {ui(lang, 'invites')}

┌─────────────────────────────┐
│
│  👥 {ui(lang, 'invites')}: {invites}
│  🎁 {ui(lang, 'per_invite')}: {reward} 💎
│  💰 {ui(lang, 'earnings')}: {format_number(ref_earnings)} 💎
│
{milestone_bar}
└─────────────────────────────┘

📎 {ui(lang, 'your_link')}:
<code>{link}</code>

💡 {ui(lang, 'share')} & {ui(lang, 'earnings')} {reward} 💎!
"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# ℹ️ PREMIUM ABOUT DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_about")
def premium_about(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # ═══ Animation ═══
    frames = [
        f"ℹ️ {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[3]}",
        f"⚙️ {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[6]}",
        f"✅ {ui(lang, 'ready')}!\n\n{LOADING_FRAMES[10]}",
    ]
    animate_text(chat_id, msg_id, frames, 0.25)
    time.sleep(0.2)

    stats = get_bot_stats()
    uptime_date = bot_config.get("bot_launch_date", "")[:10]

    msg = f"""
╔══════════════════════════════╗
║  ℹ️  ABOUT  ℹ️  ║
╚══════════════════════════════╝

   🤖 EVE Store Bot
   📦 {ui(lang, 'version')}: 3.0
   📅 Since: {uptime_date}

┌─────────────────────────────┐
│  📊 Statistics
│
│  👥 {ui(lang, 'users')}: {format_number(stats.get('total_users', 0))}
│  🟢 {ui(lang, 'online')}: {stats.get('active_today', 0)}
│  🛒 {ui(lang, 'sales')}: {format_number(stats.get('total_sales', 0))}
│  📦 {ui(lang, 'products')}: {stats.get('total_products', 0)}
│  🎫 Tickets: {stats.get('total_tickets', 0)}
│
└─────────────────────────────┘

   ⚡ Powered by Latest Tech
   🔒 Secure Transactions
   🌍 Multi-Language Support
"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🎁 PREMIUM DAILY BONUS
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_daily")
def premium_daily(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    last_claim = u.get("last_claim")
    streak = u.get("streak_days", 0) or 0
    can_claim = True
    hours = 0
    mins = 0

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
        # ═══ Claim Animation ═══
        frames = [
            f"🎁 {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[2]}",
            f"✨ {ui(lang, 'checking')}...\n\n{LOADING_FRAMES[5]}",
            f"🎊 Opening...\n\n{LOADING_FRAMES[8]}",
            f"🎉 {ui(lang, 'congrats')}!\n\n{LOADING_FRAMES[10]}",
        ]
        animate_text(chat_id, msg_id, frames, 0.35)
        time.sleep(0.3)

        # Process claim
        gift = bot_config.get("daily_gift", 10)
        vip_active = u.get("vip", False)
        if vip_active:
            gift *= 2

        # Streak logic
        last_streak = u.get("last_streak_date")
        now = datetime.now()
        if last_streak:
            try:
                last_s = datetime.fromisoformat(last_streak)
                diff_days = (now.date() - last_s.date()).days
                if diff_days == 1:
                    streak += 1
                elif diff_days > 1:
                    streak = 1
            except:
                streak = 1
        else:
            streak = 1

        # Streak bonus
        streak_bonus = 0
        if streak >= 7:
            streak_bonus = gift
        elif streak >= 3:
            streak_bonus = int(gift * 0.5)

        total_gift = gift + streak_bonus
        update_user_data(uid,
                         points=total_gift,
                         accumulated_points=total_gift,
                         last_claim=now.isoformat(),
                         last_streak_date=now.isoformat())
        if streak > 1:
            update_user_data(uid, streak_days=streak - u.get("streak_days", 0))
        update_user_rank_and_quests(uid)
        u_new = get_user(uid) or {}

        streak_line = ""
        if streak_bonus > 0:
            streak_line = f"│  🔥 {ui(lang, 'bonus')}: +{streak_bonus} 💎\n"

        vip_line = ""
        if vip_active:
            vip_line = f"│  👑 VIP 2x {ui(lang, 'bonus')}!\n"

        streak_bar = streak_visual(streak)

        msg = f"""
╔══════════════════════════════╗
║  🎁  DAILY {ui(lang, 'bonus').upper()}  🎁  ║
╚══════════════════════════════╝

   🎉 {ui(lang, 'congrats')}!

┌─────────────────────────────┐
│
│  💎 {ui(lang, 'reward')}: +{total_gift} 💎
{vip_line}{streak_line}│
│  🔥 {ui(lang, 'streak')}: {streak} {ui(lang, 'days')}
│     {streak_bar}
│
│  💰 {ui(lang, 'balance')}: {u_new.get('points', 0)} 💎
│
└─────────────────────────────┘

   ⏰ Next in 24 {ui(lang, 'hours')}
"""
    else:
        # Already claimed
        streak_bar = streak_visual(streak)

        msg = f"""
╔══════════════════════════════╗
║  ⏰  {ui(lang, 'wait').upper()}  ⏰  ║
╚══════════════════════════════╝

   ⏳ {hours}h {mins}m remaining

┌─────────────────────────────┐
│
│  🔥 {ui(lang, 'streak')}: {streak} {ui(lang, 'days')}
│     {streak_bar}
│
└─────────────────────────────┘

   💡 {ui(lang, 'keep_streak')}!
"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🔥 PREMIUM QUESTS DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_quests")
def premium_quests(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # ═══ Animation ═══
    frames = [
        f"🔥 {ui(lang, 'loading')}...\n\n{LOADING_FRAMES[4]}",
        f"✅ {ui(lang, 'ready')}!\n\n{LOADING_FRAMES[10]}",
    ]
    animate_text(chat_id, msg_id, frames, 0.3)
    time.sleep(0.2)

    completed = u.get("completed_quests", "") or ""
    invites = u.get("invite_count", 0) or 0
    acc_pts = u.get("accumulated_points", 0) or 0
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)

    quests = bot_config.get("quests", {})
    q_invite = quests.get("invite", {"target": 5, "reward": 100})
    q_buy = quests.get("buy", {"target": 3, "reward": 150})
    q_points = quests.get("points", {"target": 1000, "reward": 200})

    invite_done = "quest_invite" in completed
    buy_done = "quest_buy" in completed
    points_done = "quest_points" in completed

    total_done = sum([invite_done, buy_done, points_done])
    overall = progress_bar_detailed(total_done, 3, 10)

    def quest_line(icon, name, current, target, reward, done):
        if done:
            return f"""│  ✅ {icon} {name}
│     {ui(lang, 'completed')} • +{reward} 💎
│
"""
        else:
            bar = progress_bar_detailed(min(current, target), target, 8)
            return f"""│  🔒 {icon} {name}
│     {bar}
│     {current}/{target} • 🎁 {reward} 💎
│
"""

    msg = f"""
╔══════════════════════════════╗
║  🔥  QUESTS  🔥  ║
╚══════════════════════════════╝

   {overall}
   {total_done}/3 {ui(lang, 'completed')}

┌─────────────────────────────┐
│
{quest_line("👥", "Invite Friends", invites, q_invite['target'], q_invite['reward'], invite_done)}{quest_line("🛒", "Make Purchases", user_buys, q_buy['target'], q_buy['reward'], buy_done)}{quest_line("💎", "Earn Points", acc_pts, q_points['target'], q_points['reward'], points_done)}└─────────────────────────────┘

   💪 Complete quests for rewards!
"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# ❓ FAQ DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_faq")
def premium_faq(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    faqs = {
        "ar": [
            ("كيف أحصل على نقاط؟", "المكافأة اليومية + الإحالة + المهام"),
            ("كيف أشتري منتج؟", "المتجر ← المنتج ← المدة ← شراء"),
            ("كيف أرفع رتبتي؟", "اجمع نقاط أكثر = رتبة أعلى تلقائياً"),
            ("ما هو خصم الرتبة؟", "كل رتبة تعطيك خصم ثابت على المشتريات"),
        ],
        "en": [
            ("How to earn points?", "Daily bonus + Referrals + Quests"),
            ("How to buy a product?", "Shop → Product → Duration → Buy"),
            ("How to rank up?", "Earn more points = Higher rank auto"),
            ("What's rank discount?", "Each rank gives fixed discount"),
        ],
        "fr": [
            ("Comment gagner des points?", "Bonus quotidien + Parrainages + Quêtes"),
            ("Comment acheter?", "Boutique → Produit → Durée → Acheter"),
            ("Comment monter en rang?", "Plus de points = Rang supérieur"),
            ("Qu'est-ce que la remise?", "Chaque rang donne une remise fixe"),
        ],
        "es": [
            ("¿Cómo ganar puntos?", "Bono diario + Referidos + Misiones"),
            ("¿Cómo comprar?", "Tienda → Producto → Duración → Comprar"),
            ("¿Cómo subir de rango?", "Más puntos = Rango superior auto"),
            ("¿Qué es el descuento?", "Cada rango da descuento fijo"),
        ],
        "vi": [
            ("Cách kiếm điểm?", "Thưởng hàng ngày + Giới thiệu + Nhiệm vụ"),
            ("Cách mua sản phẩm?", "Cửa hàng → Sản phẩm → Thời hạn → Mua"),
            ("Cách lên cấp?", "Nhiều điểm hơn = Cấp cao hơn tự động"),
            ("Giảm giá cấp?", "Mỗi cấp có giảm giá cố định"),
        ],
    }

    items = faqs.get(lang, faqs["en"])
    nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

    faq_text = ""
    for i, (q, a) in enumerate(items):
        faq_text += f"""│
│  {nums[i]} {q}
│     └ {a}
"""

    msg = f"""
╔══════════════════════════════╗
║  ❓  FAQ  ❓  ║
╚══════════════════════════════╝

┌─────────────────────────────┐
{faq_text}│
└─────────────────────────────┘

   💬 Need more help? Open a ticket!
"""

    try:
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="HTML")
    except:
        bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 📖 /pp COMMAND GUIDE
# =====================================================

@bot.message_handler(commands=['pp'])
def show_commands_guide(message):
    uid = str(message.from_user.id)
    adm = is_admin(uid)

    msg = """
╔══════════════════════════════╗
║  📖  COMMANDS GUIDE  📖  ║
╚══════════════════════════════╝

⚡ USER COMMANDS
┌─────────────────────────────┐
│  /start  › Main Menu
│  /id     › Your Info
│  /help   › Help Center
│  /close  › Close Ticket
│  /pp     › This Guide
└─────────────────────────────┘

🛍️ SECTIONS
┌─────────────────────────────┐
│  👤 Account  › Balance, Rank
│  🛍️ Shop     › Buy Products
│  🎁 Rewards  › Daily, Codes, Quests
│  🎮 Fun      › Wheel, Lootbox
│  🎮 Games    › RPS, TTT, Hunt
│  💬 Support  › Tickets
│  ⚙️ Settings › Language, Theme
│  👑 VIP      › Premium Features
│  ⭐ Stars    › Convert Stars
└─────────────────────────────┘
"""

    if adm:
        msg += """
👑 ADMIN COMMANDS
┌─────────────────────────────┐
│  /stars › Stars Panel
│  /comp  › Competitions
└─────────────────────────────┘

📋 ADMIN SECTIONS
┌─────────────────────────────┐
│  📦 Products    🔑 Keys
│  👥 Members     🎫 Tickets
│  💰 Sales       📢 Marketing
│  ⚡ Flash Sales  🎁 Giveaway
│  👑 VIP Mgmt    📦 Auto-Restock
│  🎮 Games       🛡️ Anti-Spam
│  🔧 Recovery    ⚙️ System
│  📊 Statistics  🛠️ Maintenance
└─────────────────────────────┘
"""

    bot.send_message(message.chat.id, msg, parse_mode="HTML")


# =====================================================
# 🔔 NOTIFICATION HELPERS
# =====================================================

def send_rank_up_notification(uid, new_rank, discount, points):
    """Send beautiful rank-up notification"""
    msg = f"""
╔══════════════════════════════╗
║  🎊  RANK UP!  🎊  ║
╚══════════════════════════════╝

   🎉 Congratulations!

┌─────────────────────────────┐
│
│  🎖️ New Rank: {new_rank}
│  💎 Discount: {discount}%
│  📊 Points: {format_number(points)}
│
└─────────────────────────────┘

   🚀 Keep going for higher ranks!
"""
    try:
        bot.send_message(int(uid), msg, parse_mode="HTML")
    except:
        pass


def send_quest_complete_notification(uid, quest_name, reward):
    """Send quest completion notification"""
    msg = f"""
╔══════════════════════════════╗
║  🎊  QUEST DONE!  🎊  ║
╚══════════════════════════════╝

   ✅ {quest_name}

┌─────────────────────────────┐
│
│  🎁 Reward: +{reward} 💎
│
└─────────────────────────────┘

   🔥 You're on fire!
"""
    try:
        bot.send_message(int(uid), msg, parse_mode="HTML")
    except:
        pass


def send_referral_notification(uid, reward):
    """Send new referral notification"""
    msg = f"""
╔══════════════════════════════╗
║  🎊  NEW REFERRAL!  🎊  ║
╚══════════════════════════════╝

   🎉 Someone joined via your link!

┌─────────────────────────────┐
│
│  🎁 Reward: +{reward} 💎
│
└─────────────────────────────┘

   💡 Keep sharing for more rewards!
"""
    try:
        bot.send_message(int(uid), msg, parse_mode="HTML")
    except:
        pass


# =====================================================
# ✅ MODULE LOADED
# =====================================================

print("=" * 55)
print("✅ bot10.py v3.0 — Premium Visual Experience")
print("🎬 Animations: Active")
print("💎 Enhanced Displays: Active")
print("🏆 Rank System: Active")
print("🔥 Quests: Active")
print("❓ FAQ: Active")
print("📖 Guide: /pp")
print("🌍 Languages: AR/EN/FR/ES/VI")
print("=" * 55)
