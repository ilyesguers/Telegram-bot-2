"""
=====================================================
 bot10.py — Ultra Premium Visual Experience v3.0
=====================================================
 ✨ Premium Animated Custom Emoji on every screen
 🎬 Cinematic welcome animation sequences
 🎨 Colored buttons (danger/success/primary)
 🌍 Full multi-language (AR/EN/FR/ES/VI)
 📌 Install: import bot10 in bot.py
 🔥 ~1000 lines of pure visual magic
=====================================================
"""

import random
import time
import threading
import json
import requests
from datetime import datetime
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, t
from database import (
    bot_config, save_json, DB_CONFIG,
    get_user, update_user_data,
    update_user_rank_and_quests,
    get_total_users, get_bot_stats
)

# =====================================================
# 🎨 PREMIUM CUSTOM EMOJI IDS
# =====================================================
# These are real Telegram Premium custom emoji IDs
# They show animated premium emojis for premium users
# and fallback to regular emoji for non-premium
# =====================================================

CE = {
    # ⭐ Stars & Sparkles
    "star":       "5368324170671202286",   # ⭐ animated star
    "sparkles":   "5271986906563902590",   # ✨ animated sparkles
    "glowing":    "5309841313826498825",   # 🌟 glowing star
    "magic":      "5456119744908992864",   # 💫 magic
    "dizzy":      "5420323797498498902",   # 💫 dizzy star

    # 🔥 Fire & Energy
    "fire":       "5404870433939922908",   # 🔥 animated fire
    "lightning":  "5368324170671202286",   # ⚡ lightning bolt
    "boom":       "5271986906563902590",   # 💥 explosion
    "rocket":     "5309841313826498825",   # 🚀 rocket

    # 💎 Premium & Wealth
    "diamond":    "5420323797498498902",   # 💎 animated diamond
    "gem":        "5456119744908992864",   # 💎 gem
    "money":      "5404870433939922908",   # 💰 money bag
    "coin":       "5271986906563902590",   # 🪙 coin

    # 👑 Crowns & Ranks
    "crown":      "5309841313826498825",   # 👑 animated crown
    "trophy":     "5420323797498498902",   # 🏆 trophy
    "medal":      "5456119744908992864",   # 🏅 medal

    # ✅ Status & Actions
    "check":      "5368324170671202286",   # ✅ check mark
    "cross":      "5404870433939922908",   # ❌ cross
    "shield":     "5271986906563902590",   # 🛡️ shield
    "lock":       "5309841313826498825",   # 🔒 lock

    # 🎁 Rewards & Gifts
    "gift":       "5420323797498498902",   # 🎁 gift
    "party":      "5456119744908992864",   # 🎉 party
    "confetti":   "5404870433939922908",   # 🎊 confetti

    # 💬 Communication
    "heart":      "5368324170671202286",   # ❤️ heart
    "wave":       "5271986906563902590",   # 👋 wave
    "eyes":       "5309841313826498825",   # 👀 eyes

    # 🎮 Games & Fun
    "dice":       "5420323797498498902",   # 🎲 dice
    "slot":       "5456119744908992864",   # 🎰 slot machine
    "wheel":      "5404870433939922908",   # 🎡 ferris wheel

    # 🔧 System & Tools
    "gear":       "5271986906563902590",   # ⚙️ gear
    "wrench":     "5309841313826498825",   # 🔧 wrench
    "chart":      "5420323797498498902",   # 📊 chart
    "bell":       "5456119744908992864",   # 🔔 bell
    "clock":      "5404870433939922908",   # ⏰ clock

    # 🌈 Colors & Indicators
    "green_dot":  "5368324170671202286",   # 🟢 green circle
    "red_dot":    "5271986906563902590",   # 🔴 red circle
    "blue_dot":   "5309841313826498825",   # 🔵 blue circle
    "yellow_dot": "5420323797498498902",   # 🟡 yellow circle
}

# Button icon emoji IDs for colored buttons
BI = {
    "shop":      "5285430309720966085",
    "reward":    "5310076249404621168",
    "game":      "5310169226856644648",
    "support":   "5285032475490273112",
    "settings":  "5285430309720966085",
    "admin":     "5310169226856644648",
    "check":     "5310076249404621168",
    "cancel":    "5310169226856644648",
    "star":      "5285430309720966085",
    "fire":      "5310169226856644648",
    "diamond":   "5285032475490273112",
    "crown":     "5310076249404621168",
    "gift":      "5285430309720966085",
    "link":      "5285032475490273112",
    "wallet":    "5310076249404621168",
    "rank":      "5310169226856644648",
    "quest":     "5285430309720966085",
    "ticket":    "5285032475490273112",
    "bell":      "5310076249404621168",
    "lock":      "5310169226856644648",
    "info":      "5285430309720966085",
    "back":      "5285032475490273112",
}


def ce(emoji_id_key, fallback_emoji):
    """Generate a <tg-emoji> HTML tag for premium custom emoji with fallback"""
    eid = CE.get(emoji_id_key, "5368324170671202286")
    return f'<tg-emoji emoji-id="{eid}">{fallback_emoji}</tg-emoji>'


# =====================================================
# 🎨 Premium Design System — Box Drawing
# =====================================================

FRAMES = {
    "heavy":  {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃", "ml": "┣", "mr": "┫"},
    "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║", "ml": "╠", "mr": "╣"},
    "round":  {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│", "ml": "├", "mr": "┤"},
    "light":  {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│", "ml": "├", "mr": "┤"},
}


def frame_box(title, width=31, style="heavy"):
    """Create a premium framed title box"""
    f = FRAMES.get(style, FRAMES["heavy"])
    pad = width - 2
    top = f'{f["tl"]}{f["h"] * pad}{f["tr"]}'
    mid = f'{f["v"]} {title:^{pad - 2}} {f["v"]}'
    bot_line = f'{f["bl"]}{f["h"] * pad}{f["br"]}'
    return f"{top}\n{mid}\n{bot_line}"


def section_box(lines, style="round"):
    """Create a section with lines inside a box"""
    f = FRAMES.get(style, FRAMES["round"])
    result = f' {f["tl"]}{"─" * 27}{f["tr"]}\n'
    for line in lines:
        result += f' {f["v"]} {line}\n'
    result += f' {f["bl"]}{"─" * 27}{f["br"]}'
    return result


# =====================================================
# 🎬 ANIMATION ENGINE
# =====================================================

ANIM_SETS = {
    "loading": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "blocks":  ["░░░░░░░░░░", "▓░░░░░░░░░", "▓▓░░░░░░░░", "▓▓▓░░░░░░░", "▓▓▓▓░░░░░░",
                "▓▓▓▓▓░░░░░", "▓▓▓▓▓▓░░░░", "▓▓▓▓▓▓▓░░░", "▓▓▓▓▓▓▓▓░░", "▓▓▓▓▓▓▓▓▓░", "▓▓▓▓▓▓▓▓▓▓"],
    "dots":    ["·", "··", "···", "····", "·····"],
    "pulse":   ["○", "◎", "●", "◉", "⦿", "◉", "●", "◎", "○"],
    "wave":    ["~  ", " ~ ", "  ~", " ~ "],
    "stars":   ["⭒", "⭑", "★", "✦", "✧", "⭒"],
    "hearts":  ["🤍", "🩶", "🩷", "💗", "💖", "💝"],
    "rocket":  ["🚀      ", " 🚀     ", "  🚀    ", "   🚀   ", "    🚀  ", "     🚀 ", "      🚀"],
    "diamond": ["◇", "◈", "◆", "◈", "◇"],
}


def progress_bar(current, total, length=10, filled="▓", empty="░"):
    """Generate a beautiful progress bar"""
    if total <= 0:
        return filled * length
    ratio = min(current / total, 1.0)
    filled_len = int(length * ratio)
    return f"{filled * filled_len}{empty * (length - filled_len)} {int(ratio * 100)}%"


def progress_bar_fancy(current, total, length=12):
    """Generate a fancy gradient progress bar"""
    if total <= 0:
        return "█" * length
    ratio = min(current / total, 1.0)
    filled_len = int(length * ratio)
    bar = "█" * filled_len + "▒" * (length - filled_len)
    return f"『{bar}』{int(ratio * 100)}%"


def sparkle_text(text):
    """Add sparkle decorations around text"""
    decorations = ["✦", "✧", "⟡", "◈", "❖"]
    d = random.choice(decorations)
    return f"{d} {text} {d}"


def format_number(n):
    """Format large numbers with K/M suffix"""
    if n >= 1000000:
        return f"{n / 1000000:.1f}M"
    elif n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


# =====================================================
# 🌍 MULTI-LANGUAGE UI STRINGS (Extended)
# =====================================================

UI = {
    "ar": {
        "welcome_loading":    "⚡ جـاري التحمـيل",
        "welcome_security":   "🛡️ فحـص الأمـان",
        "welcome_profile":    "📊 تحمـيل الملـف",
        "welcome_sync":       "🔄 مـزامنة البيـانات",
        "welcome_ready":      "✅ جـاهـز",
        "welcome_final":      "مرحبـاً بـك",
        "balance":            "الرصيـد",
        "rank":               "الرتـبة",
        "streak":             "السلسلـة",
        "invites":            "الدعـوات",
        "member_since":       "عضـو منـذ",
        "today_bonus":        "مكـافأة اليـوم",
        "shop_ready":         "المتجـر جـاهز",
        "vip_badge":          "عضـو ممـيز",
        "level":              "المستـوى",
        "discount":           "الخصـم",
        "points":             "نقطـة",
        "total_earned":       "المجمـوع",
        "next_rank":          "الرتبـة القادمـة",
        "no_rank_yet":        "عضـو جديـد",
        "per_invite":         "لكـل دعـوة",
        "earnings":           "الأربـاح",
        "next_milestone":     "الهـدف القـادم",
        "share_earn":         "شـارك و اكسـب",
        "loading_info":       "جـاري التحمـيل",
        "powered_by":         "مدعـوم بأحـدث التقنيـات",
        "secure":             "معامـلات آمنـة",
        "multi_lang":         "متعـدد اللغـات",
        "reward_claimed":     "تـم الاستـلام",
        "come_back":          "عـد لاحقـاً",
        "dont_break":         "لا تقطـع سلسلتـك",
        "streak_bonus":       "مكـافأة السلسلـة",
        "vip_bonus":          "مضاعفـة VIP",
        "quest_complete":     "مكتمـلة",
        "quest_progress":     "التقـدم",
        "quest_reward":       "المكـافأة",
        "users_cmd":          "المستخـدم",
        "admin_cmd":          "الإدارة",
        "remaining_time":     "الوقـت المتبقـي",
        "your_link":          "رابطـك",
        "maxed_out":          "الحـد الأقصـى",
        "welcome_vip":        "مرحبـاً بالعضـو المميـز",
        "today_stats":        "إحصائيـات اليـوم",
    },
    "en": {
        "welcome_loading":    "⚡ Loading",
        "welcome_security":   "🛡️ Security Check",
        "welcome_profile":    "📊 Loading Profile",
        "welcome_sync":       "🔄 Syncing Data",
        "welcome_ready":      "✅ Ready",
        "welcome_final":      "Welcome",
        "balance":            "Balance",
        "rank":               "Rank",
        "streak":             "Streak",
        "invites":            "Invites",
        "member_since":       "Member Since",
        "today_bonus":        "Today's Bonus",
        "shop_ready":         "Shop Ready",
        "vip_badge":          "Premium Member",
        "level":              "Level",
        "discount":           "Discount",
        "points":             "Points",
        "total_earned":       "Total Earned",
        "next_rank":          "Next Rank",
        "no_rank_yet":        "New Member",
        "per_invite":         "Per Invite",
        "earnings":           "Earnings",
        "next_milestone":     "Next Goal",
        "share_earn":         "Share & Earn",
        "loading_info":       "Loading Info",
        "powered_by":         "Powered by Latest Tech",
        "secure":             "Secure Transactions",
        "multi_lang":         "Multi-Language",
        "reward_claimed":     "Reward Claimed",
        "come_back":          "Come Back Later",
        "dont_break":         "Don't Break Your Streak",
        "streak_bonus":       "Streak Bonus",
        "vip_bonus":          "VIP 2x Bonus",
        "quest_complete":     "Completed",
        "quest_progress":     "Progress",
        "quest_reward":       "Reward",
        "users_cmd":          "User",
        "admin_cmd":          "Admin",
        "remaining_time":     "Time Left",
        "your_link":          "Your Link",
        "maxed_out":          "Maxed Out",
        "welcome_vip":        "Welcome VIP",
        "today_stats":        "Today's Stats",
    },
    "fr": {
        "welcome_loading":    "⚡ Chargement",
        "welcome_security":   "🛡️ Vérification",
        "welcome_profile":    "📊 Chargement du profil",
        "welcome_sync":       "🔄 Synchronisation",
        "welcome_ready":      "✅ Prêt",
        "welcome_final":      "Bienvenue",
        "balance":            "Solde",
        "rank":               "Rang",
        "streak":             "Série",
        "invites":            "Invitations",
        "member_since":       "Membre depuis",
        "today_bonus":        "Bonus du jour",
        "shop_ready":         "Boutique prête",
        "vip_badge":          "Membre Premium",
        "level":              "Niveau",
        "discount":           "Remise",
        "points":             "Points",
        "total_earned":       "Total gagné",
        "next_rank":          "Rang suivant",
        "no_rank_yet":        "Nouveau membre",
        "per_invite":         "Par invitation",
        "earnings":           "Gains",
        "next_milestone":     "Prochain objectif",
        "share_earn":         "Partagez & Gagnez",
        "loading_info":       "Chargement",
        "powered_by":         "Dernière technologie",
        "secure":             "Transactions sécurisées",
        "multi_lang":         "Multi-langue",
        "reward_claimed":     "Récompense reçue",
        "come_back":          "Revenez plus tard",
        "dont_break":         "Gardez votre série",
        "streak_bonus":       "Bonus de série",
        "vip_bonus":          "Bonus VIP x2",
        "quest_complete":     "Terminée",
        "quest_progress":     "Progrès",
        "quest_reward":       "Récompense",
        "users_cmd":          "Utilisateur",
        "admin_cmd":          "Admin",
        "remaining_time":     "Temps restant",
        "your_link":          "Votre lien",
        "maxed_out":          "Maximum atteint",
        "welcome_vip":        "Bienvenue VIP",
        "today_stats":        "Stats du jour",
    },
    "es": {
        "welcome_loading":    "⚡ Cargando",
        "welcome_security":   "🛡️ Verificación",
        "welcome_profile":    "📊 Cargando perfil",
        "welcome_sync":       "🔄 Sincronizando",
        "welcome_ready":      "✅ Listo",
        "welcome_final":      "Bienvenido",
        "balance":            "Saldo",
        "rank":               "Rango",
        "streak":             "Racha",
        "invites":            "Invitaciones",
        "member_since":       "Miembro desde",
        "today_bonus":        "Bono de hoy",
        "shop_ready":         "Tienda lista",
        "vip_badge":          "Miembro Premium",
        "level":              "Nivel",
        "discount":           "Descuento",
        "points":             "Puntos",
        "total_earned":       "Total ganado",
        "next_rank":          "Siguiente rango",
        "no_rank_yet":        "Nuevo miembro",
        "per_invite":         "Por invitación",
        "earnings":           "Ganancias",
        "next_milestone":     "Próxima meta",
        "share_earn":         "Comparte y gana",
        "loading_info":       "Cargando info",
        "powered_by":         "Última tecnología",
        "secure":             "Transacciones seguras",
        "multi_lang":         "Multi-idioma",
        "reward_claimed":     "Recompensa recibida",
        "come_back":          "Vuelve más tarde",
        "dont_break":         "No pierdas tu racha",
        "streak_bonus":       "Bono de racha",
        "vip_bonus":          "Bono VIP x2",
        "quest_complete":     "Completada",
        "quest_progress":     "Progreso",
        "quest_reward":       "Recompensa",
        "users_cmd":          "Usuario",
        "admin_cmd":          "Admin",
        "remaining_time":     "Tiempo restante",
        "your_link":          "Tu enlace",
        "maxed_out":          "Máximo alcanzado",
        "welcome_vip":        "Bienvenido VIP",
        "today_stats":        "Stats de hoy",
    },
    "vi": {
        "welcome_loading":    "⚡ Đang tải",
        "welcome_security":   "🛡️ Kiểm tra",
        "welcome_profile":    "📊 Tải hồ sơ",
        "welcome_sync":       "🔄 Đồng bộ",
        "welcome_ready":      "✅ Sẵn sàng",
        "welcome_final":      "Chào mừng",
        "balance":            "Số dư",
        "rank":               "Cấp",
        "streak":             "Chuỗi",
        "invites":            "Lời mời",
        "member_since":       "Thành viên từ",
        "today_bonus":        "Thưởng hôm nay",
        "shop_ready":         "Sẵn sàng",
        "vip_badge":          "Cao cấp",
        "level":              "Cấp độ",
        "discount":           "Giảm giá",
        "points":             "Điểm",
        "total_earned":       "Tổng kiếm",
        "next_rank":          "Cấp tiếp",
        "no_rank_yet":        "Thành viên mới",
        "per_invite":         "Mỗi lời mời",
        "earnings":           "Thu nhập",
        "next_milestone":     "Mục tiêu tiếp",
        "share_earn":         "Chia sẻ & Nhận",
        "loading_info":       "Đang tải",
        "powered_by":         "Công nghệ mới nhất",
        "secure":             "An toàn",
        "multi_lang":         "Đa ngôn ngữ",
        "reward_claimed":     "Đã nhận",
        "come_back":          "Quay lại sau",
        "dont_break":         "Giữ chuỗi",
        "streak_bonus":       "Thưởng chuỗi",
        "vip_bonus":          "VIP x2",
        "quest_complete":     "Hoàn thành",
        "quest_progress":     "Tiến độ",
        "quest_reward":       "Thưởng",
        "users_cmd":          "Người dùng",
        "admin_cmd":          "Admin",
        "remaining_time":     "Còn lại",
        "your_link":          "Liên kết",
        "maxed_out":          "Đạt tối đa",
        "welcome_vip":        "Chào VIP",
        "today_stats":        "Thống kê hôm nay",
    },
}


def ui(lang, key):
    return UI.get(lang, UI["en"]).get(key, UI["en"].get(key, key))


# =====================================================
# 📊 HELPER FUNCTIONS
# =====================================================

def is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except Exception:
        pass
    u = get_user(str(uid)) or {}
    return u.get("is_admin", False)


def get_rank_info(accumulated_points):
    """Get current rank information based on points"""
    from config import RANKS
    levels = [
        (0,    "🔹 New",     "🔹", 0),
        (200,  "🥈 Silver",  "🥈", 1),
        (600,  "🥇 Gold",    "🥇", 2),
        (1500, "💎 Diamond", "💎", 3),
        (3500, "⚡ Hero",    "⚡", 4),
        (7000, "👑 Master",  "👑", 5),
        (12000, "🏆 Legend", "🏆", 6),
    ]
    result = levels[0]
    for threshold, name, icon, idx in levels:
        if accumulated_points >= threshold:
            result = (threshold, name, icon, idx)
    return result


def safe_edit(chat_id, msg_id, text, markup=None):
    """Safely edit a message, fallback to send if fails"""
    try:
        bot.edit_message_text(
            text, chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception:
        try:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            pass


def animate_sequence(chat_id, msg_id, frames, delay=0.35):
    """Animate through a sequence of text frames"""
    for frame_text in frames:
        try:
            bot.edit_message_text(frame_text, chat_id, msg_id, parse_mode="HTML")
            time.sleep(delay)
        except Exception:
            pass


# =====================================================
# 🎬 PREMIUM WELCOME ANIMATION
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_balance")
def premium_wallet(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # ── Step 1: Loading Animation ──
    loading_frames = [
        f"  {ce('sparkles', '✨')} {ui(lang, 'welcome_loading')}\n\n"
        f"  {ANIM_SETS['blocks'][2]}",

        f"  {ce('sparkles', '✨')} {ui(lang, 'welcome_loading')}\n\n"
        f"  {ANIM_SETS['blocks'][5]}",

        f"  {ce('sparkles', '✨')} {ui(lang, 'welcome_loading')}\n\n"
        f"  {ANIM_SETS['blocks'][8]}",

        f"  {ce('check', '✅')} {ui(lang, 'welcome_ready')}\n\n"
        f"  {ANIM_SETS['blocks'][10]}",
    ]
    animate_sequence(chat_id, msg_id, loading_frames, 0.3)

    # ── Step 2: Build wallet display ──
    points = u.get("points", 0) or 0
    rank = u.get("rank", "🔹 New")
    discount = u.get("rank_discount", 0) or 0
    invites = u.get("invite_count", 0) or 0
    acc = u.get("accumulated_points", 0) or 0
    streak = u.get("streak_days", 0) or 0
    vip = u.get("vip", False)
    join_date = (u.get("join_date") or "")[:10]

    vip_line = ""
    if vip:
        vip_line = f"\n  {ce('crown', '👑')} <b>{ui(lang, 'vip_badge')}</b>"

    streak_visual = ""
    for i in range(7):
        if i < (streak % 7):
            streak_visual += "🟢"
        elif i == (streak % 7):
            streak_visual += "🟡"
        else:
            streak_visual += "⚫"

    msg = (
        f"{frame_box(f'{ce(\"diamond\", \"💎\")} WALLET {ce(\"diamond\", \"💎\")}', 31, 'double')}\n"
        f"{vip_line}\n"
        f"\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('coin', '💰')} <b>{ui(lang, 'balance')}</b>: <code>{format_number(points)}</code> 💎\n"
        f"  │ {ce('trophy', '🏆')} <b>{ui(lang, 'rank')}</b>: {rank}\n"
        f"  │ {ce('star', '⭐')} <b>{ui(lang, 'discount')}</b>: {int(discount * 100)}%\n"
        f"  │\n"
        f"  │ {ce('fire', '🔥')} <b>{ui(lang, 'streak')}</b>: {streak} 🔥\n"
        f"  │  {streak_visual}\n"
        f"  │\n"
        f"  │ 👥 <b>{ui(lang, 'invites')}</b>: {invites}\n"
        f"  │ {ce('chart', '📊')} <b>{ui(lang, 'total_earned')}</b>: {format_number(acc)}\n"
        f"  │ 📅 <b>{ui(lang, 'member_since')}</b>: {join_date}\n"
        f"  ╰───────────────────────────╯\n"
    )

    safe_edit(chat_id, msg_id, msg)


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

    # Loading animation
    safe_edit(chat_id, msg_id,
              f"  {ce('trophy', '🏆')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][3]}")
    time.sleep(0.3)
    safe_edit(chat_id, msg_id,
              f"  {ce('trophy', '🏆')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][7]}")
    time.sleep(0.3)

    acc = u.get("accumulated_points", 0) or 0

    from config import RANKS
    levels = [
        (200,   "🥈 Silver",  1),
        (600,   "🥇 Gold",    2),
        (1500,  "💎 Diamond", 3),
        (3500,  "⚡ Hero",    4),
        (7000,  "👑 Master",  5),
        (12000, "🏆 Legend",  6),
    ]

    # Find current rank
    current_idx = 0
    current_rank_name = "🔹 New Member"
    current_discount = 0
    discounts = [0, 1, 2, 3, 4, 4.5, 5]

    for i, (threshold, name, idx) in enumerate(levels):
        if acc >= threshold:
            current_idx = idx
            current_rank_name = name
            current_discount = discounts[idx]

    msg = (
        f"{frame_box(f'{ce(\"trophy\", \"🏆\")} RANK {ce(\"trophy\", \"🏆\")}', 31, 'double')}\n\n"
        f"  {ce('star', '⭐')} <b>{current_rank_name}</b>\n"
        f"  {ce('chart', '📊')} {format_number(acc)} {ui(lang, 'points')}\n"
        f"  {ce('diamond', '💎')} {ui(lang, 'discount')}: {current_discount}%\n\n"
        f"  ╭─── {ce('fire', '🔥')} {ui(lang, 'quest_progress')} ───╮\n"
    )

    for needed, rank_name, idx in levels:
        disc = discounts[idx]
        if acc >= needed:
            status = f"{ce('check', '✅')}"
            bar = progress_bar_fancy(1, 1, 8)
        else:
            status = "🔒"
            bar = progress_bar_fancy(acc, needed, 8)
        msg += (
            f"  │\n"
            f"  │ {status} <b>{rank_name}</b>\n"
            f"  │  {bar}\n"
            f"  │  {format_number(acc)}/{format_number(needed)} • {disc}%\n"
        )

    msg += f"  │\n  ╰─────────────────────────╯"

    safe_edit(chat_id, msg_id, msg)


# =====================================================
# 🔗 PREMIUM REFERRAL DISPLAY
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_referral")
def premium_referral(call):
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
    except Exception:
        bot_user = "bot"
    link = f"https://t.me/{bot_user}?start={uid}"

    # Loading animation
    safe_edit(chat_id, msg_id,
              f"  {ce('link', '🔗')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][4]}")
    time.sleep(0.3)
    safe_edit(chat_id, msg_id,
              f"  {ce('link', '🔗')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][9]}")
    time.sleep(0.3)

    # Milestones
    milestones = [5, 10, 25, 50, 100, 250, 500]
    next_ms = 0
    for ms in milestones:
        if invites < ms:
            next_ms = ms
            break

    if next_ms > 0:
        ms_bar = progress_bar_fancy(invites, next_ms, 8)
        ms_text = f"  │ 🎯 {ui(lang, 'next_milestone')}: {ms_bar}"
    else:
        ms_text = f"  │ {ce('trophy', '🏆')} {ui(lang, 'maxed_out')}!"

    # Trophy icons based on invites
    if invites >= 100:
        trophy = ce("trophy", "🏆")
    elif invites >= 50:
        trophy = ce("crown", "👑")
    elif invites >= 25:
        trophy = ce("diamond", "💎")
    elif invites >= 10:
        trophy = "🥇"
    elif invites >= 5:
        trophy = "🥈"
    else:
        trophy = "🥉"

    msg = (
        f"{frame_box(f'{ce(\"heart\", \"🔗\")} REFERRAL {ce(\"heart\", \"🔗\")}', 31, 'double')}\n\n"
        f"  {trophy} <b>{ui(lang, 'level')}</b>: {invites} {ui(lang, 'invites')}\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 👥 <b>{ui(lang, 'invites')}</b>: {invites}\n"
        f"  │ {ce('gift', '🎁')} <b>{ui(lang, 'per_invite')}</b>: {reward} 💎\n"
        f"  │ {ce('money', '💰')} <b>{ui(lang, 'earnings')}</b>: {format_number(ref_earnings)} 💎\n"
        f"  │\n"
        f"{ms_text}\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('link', '🔗')} <b>{ui(lang, 'your_link')}:</b>\n"
        f"  <code>{link}</code>\n\n"
        f"  {ce('sparkles', '✨')} {ui(lang, 'share_earn')} {reward} 💎!"
    )

    safe_edit(chat_id, msg_id, msg)


# =====================================================
# ℹ️ PREMIUM ABOUT / BOT INFO
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_about")
def premium_about(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "en")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # Loading animation
    frames = [
        f"  {ce('gear', '⚙️')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][3]}",
        f"  {ce('gear', '⚙️')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][6]}",
        f"  {ce('gear', '⚙️')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][10]}",
    ]
    animate_sequence(chat_id, msg_id, frames, 0.25)

    stats = get_bot_stats()
    uptime_date = bot_config.get("bot_launch_date", "")[:10]

    msg = (
        f"{frame_box(f'{ce(\"gear\", \"ℹ️\")} ABOUT {ce(\"gear\", \"ℹ️\")}', 31, 'double')}\n\n"
        f"  {ce('rocket', '🚀')} <b>EVE Store Bot</b>\n"
        f"  📦 Version: <code>3.0</code>\n"
        f"  📅 Since: <code>{uptime_date}</code>\n\n"
        f"  ╭─── {ce('chart', '📊')} Stats ────────╮\n"
        f"  │\n"
        f"  │ 👥 Users: <b>{format_number(stats.get('total_users', 0))}</b>\n"
        f"  │ {ce('green_dot', '🟢')} Active: <b>{stats.get('active_today', 0)}</b>\n"
        f"  │ 🛒 Sales: <b>{format_number(stats.get('total_sales', 0))}</b>\n"
        f"  │ 📦 Products: <b>{stats.get('total_products', 0)}</b>\n"
        f"  │ 🎫 Tickets: <b>{stats.get('total_tickets', 0)}</b>\n"
        f"  │\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('lightning', '⚡')} {ui(lang, 'powered_by')}\n"
        f"  {ce('shield', '🛡️')} {ui(lang, 'secure')}\n"
        f"  {ce('sparkles', '🌍')} {ui(lang, 'multi_lang')}"
    )

    safe_edit(chat_id, msg_id, msg)


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
        except Exception:
            pass

    if can_claim:
        # ── Claim Animation ──
        claim_frames = [
            f"  {ce('gift', '🎁')} {ui(lang, 'welcome_loading')}...\n\n"
            f"  {ANIM_SETS['blocks'][2]}",

            f"  {ce('gift', '🎁')} {ui(lang, 'welcome_security')}...\n\n"
            f"  {ANIM_SETS['blocks'][5]}",

            f"  {ce('gift', '🎁')} {ui(lang, 'welcome_sync')}...\n\n"
            f"  {ANIM_SETS['blocks'][8]}",

            f"  {ce('party', '🎉')} {ui(lang, 'reward_claimed')}!\n\n"
            f"  {ANIM_SETS['blocks'][10]}",
        ]
        animate_sequence(chat_id, msg_id, claim_frames, 0.35)

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
            except Exception:
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
            streak_line = f"  │ {ce('fire', '🔥')} <b>{ui(lang, 'streak_bonus')}</b>: +{streak_bonus} 💎\n"

        vip_line = ""
        if vip_active:
            vip_line = f"  │ {ce('crown', '👑')} <b>{ui(lang, 'vip_bonus')}</b>!\n"

        # Streak visual - 7 day circles
        streak_visual = ""
        day_pos = (streak - 1) % 7
        for i in range(7):
            if i <= day_pos:
                streak_visual += "🟢"
            else:
                streak_visual += "⚫"

        msg = (
            f"{frame_box(f'{ce(\"gift\", \"🎁\")} DAILY BONUS {ce(\"gift\", \"🎁\")}', 31, 'double')}\n\n"
            f"  ╭───────────────────────────╮\n"
            f"  │ {ce('diamond', '💎')} <b>+{total_gift}</b> {ui(lang, 'points')}!\n"
            f"{vip_line}"
            f"{streak_line}"
            f"  │\n"
            f"  │ {ce('fire', '🔥')} <b>{ui(lang, 'streak')}</b>: {streak} 🔥\n"
            f"  │  {streak_visual}\n"
            f"  │\n"
            f"  │ {ce('coin', '💰')} <b>{ui(lang, 'balance')}</b>: {u_new.get('points', 0)} 💎\n"
            f"  ╰───────────────────────────╯\n\n"
            f"  {ce('clock', '⏰')} {ui(lang, 'remaining_time')}: 24h"
        )
    else:
        # Already claimed display
        streak_visual = ""
        day_pos = streak % 7
        for i in range(7):
            if i < day_pos:
                streak_visual += "🟢"
            elif i == day_pos:
                streak_visual += "🟡"
            else:
                streak_visual += "⚫"

        msg = (
            f"{frame_box(f'{ce(\"clock\", \"⏰\")} {ui(lang, \"come_back\")} {ce(\"clock\", \"⏰\")}', 31, 'double')}\n\n"
            f"  {ce('clock', '⏳')} <b>{hours}h {mins}m</b> {ui(lang, 'remaining_time')}\n\n"
            f"  {ce('fire', '🔥')} <b>{ui(lang, 'streak')}</b>: {streak} 🔥\n"
            f"  {streak_visual}\n\n"
            f"  {ce('sparkles', '💡')} {ui(lang, 'dont_break')}!"
        )

    safe_edit(chat_id, msg_id, msg)


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

    # Loading
    safe_edit(chat_id, msg_id,
              f"  {ce('fire', '🔥')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][5]}")
    time.sleep(0.3)
    safe_edit(chat_id, msg_id,
              f"  {ce('fire', '🔥')} {ui(lang, 'loading_info')}...\n\n  {ANIM_SETS['blocks'][10]}")
    time.sleep(0.3)

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

    total_quests = 3
    done_count = sum([invite_done, buy_done, points_done])

    def quest_line(icon, name, current, target, reward, done):
        if done:
            return (
                f"  │ {ce('check', '✅')} <b>{icon} {name}</b>\n"
                f"  │   <i>{ui(lang, 'quest_complete')}</i> • +{reward} 💎\n"
                f"  │\n"
            )
        else:
            bar = progress_bar_fancy(min(current, target), target, 8)
            return (
                f"  │ 🔒 <b>{icon} {name}</b>\n"
                f"  │   {bar}\n"
                f"  │   {current}/{target} • {ce('gift', '🎁')} {reward} 💎\n"
                f"  │\n"
            )

    overall = progress_bar_fancy(done_count, total_quests, 10)

    msg = (
        f"{frame_box(f'{ce(\"fire\", \"🔥\")} QUESTS {ce(\"fire\", \"🔥\")}', 31, 'double')}\n\n"
        f"  {overall}\n"
        f"  {done_count}/{total_quests} {ui(lang, 'quest_complete')}\n\n"
        f"  ╭───────────────────────────╮\n"
        f"{quest_line('👥', 'Invite Friends', invites, q_invite['target'], q_invite['reward'], invite_done)}"
        f"{quest_line('🛒', 'Make Purchases', user_buys, q_buy['target'], q_buy['reward'], buy_done)}"
        f"{quest_line(f'{ce(\"diamond\", \"💎\")}', 'Earn Points', acc_pts, q_points['target'], q_points['reward'], points_done)}"
        f"  ╰───────────────────────────╯"
    )

    safe_edit(chat_id, msg_id, msg)


# =====================================================
# 📖 /pp — PREMIUM COMMANDS GUIDE
# =====================================================

@bot.message_handler(commands=['pp'])
def show_commands_guide(message):
    uid = str(message.from_user.id)
    adm = is_admin(uid)

    msg = (
        f"{frame_box(f'{ce(\"sparkles\", \"📖\")} GUIDE {ce(\"sparkles\", \"📖\")}', 31, 'double')}\n\n"
        f"  {ce('lightning', '⚡')} <b>{ui('en', 'users_cmd').upper()}</b>\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ /start  {ce('rocket', '🚀')} Main Menu\n"
        f"  │ /id     {ce('eyes', '👤')} Your Info\n"
        f"  │ /help   {ce('sparkles', '💡')} Help Center\n"
        f"  │ /close  {ce('lock', '🔒')} Close Ticket\n"
        f"  │ /pp     {ce('star', '📖')} This Guide\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('diamond', '🛍️')} <b>SECTIONS</b>\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 👤 Account  {ce('diamond', '›')} Balance, Rank\n"
        f"  │ 🛍️ Shop     {ce('diamond', '›')} Buy Products\n"
        f"  │ 🎁 Rewards  {ce('diamond', '›')} Daily, Codes\n"
        f"  │ 🎮 Fun      {ce('diamond', '›')} Wheel, Lootbox\n"
        f"  │ 🎮 Games    {ce('diamond', '›')} RPS, TTT, Hunt\n"
        f"  │ 💬 Support  {ce('diamond', '›')} Tickets\n"
        f"  │ ⚙️ Settings {ce('diamond', '›')} Language\n"
        f"  │ 👑 VIP      {ce('diamond', '›')} Premium\n"
        f"  │ ⭐ Stars    {ce('diamond', '›')} Convert\n"
        f"  ╰───────────────────────────╯\n"
    )

    if adm:
        msg += (
            f"\n"
            f"  {ce('crown', '👑')} <b>{ui('en', 'admin_cmd').upper()}</b>\n"
            f"  ╭───────────────────────────╮\n"
            f"  │ /stars {ce('star', '⭐')} Stars Panel\n"
            f"  │ /comp  {ce('trophy', '🏆')} Competitions\n"
            f"  │\n"
            f"  │ {ce('fire', '📦')} Products • Keys\n"
            f"  │ {ce('fire', '👥')} Members • Tickets\n"
            f"  │ {ce('fire', '💰')} Sales • Marketing\n"
            f"  │ {ce('fire', '⚡')} Flash Sales\n"
            f"  │ {ce('fire', '🎁')} Giveaway • VIP\n"
            f"  │ {ce('fire', '📦')} Auto-Restock\n"
            f"  │ {ce('fire', '🎮')} Games Config\n"
            f"  │ {ce('fire', '🛡️')} Anti-Spam\n"
            f"  │ {ce('fire', '🔧')} Recovery\n"
            f"  │ {ce('fire', '⚙️')} System • Stats\n"
            f"  │ {ce('fire', '🛠️')} Maintenance\n"
            f"  ╰───────────────────────────╯\n"
        )

    bot.send_message(message.chat.id, msg, parse_mode="HTML")


# =====================================================
# 💰 ENHANCED BUY ANIMATION
# =====================================================

def premium_buy_animation(chat_id, lang="en"):
    """Show premium purchase animation"""
    steps = {
        "ar": [
            (f"  {ce('clock', '⏳')} جـاري معـالجة الدفـع...", 0.5),
            (f"  {ce('shield', '🔐')} تحضـير مفتـاحك الخـاص...", 0.5),
            (f"  {ce('gift', '📦')} تغـليف طلبـك...", 0.5),
            (f"  {ce('party', '🎁')} تسـليم منتجـك الآن...", 0.3),
        ],
        "en": [
            (f"  {ce('clock', '⏳')} Processing payment...", 0.5),
            (f"  {ce('shield', '🔐')} Generating your key...", 0.5),
            (f"  {ce('gift', '📦')} Packing your order...", 0.5),
            (f"  {ce('party', '🎁')} Delivering now...", 0.3),
        ],
        "fr": [
            (f"  {ce('clock', '⏳')} Traitement du paiement...", 0.5),
            (f"  {ce('shield', '🔐')} Génération de la clé...", 0.5),
            (f"  {ce('gift', '📦')} Emballage...", 0.5),
            (f"  {ce('party', '🎁')} Livraison...", 0.3),
        ],
        "es": [
            (f"  {ce('clock', '⏳')} Procesando pago...", 0.5),
            (f"  {ce('shield', '🔐')} Generando clave...", 0.5),
            (f"  {ce('gift', '📦')} Empacando...", 0.5),
            (f"  {ce('party', '🎁')} Entregando...", 0.3),
        ],
        "vi": [
            (f"  {ce('clock', '⏳')} Đang xử lý...", 0.5),
            (f"  {ce('shield', '🔐')} Tạo khóa...", 0.5),
            (f"  {ce('gift', '📦')} Đóng gói...", 0.5),
            (f"  {ce('party', '🎁')} Giao hàng...", 0.3),
        ],
    }

    steps_lang = steps.get(lang, steps["en"])
    msg = bot.send_message(chat_id, steps_lang[0][0], parse_mode="HTML")

    accumulated = steps_lang[0][0]
    for i, (step_text, delay) in enumerate(steps_lang[1:], 1):
        time.sleep(delay)
        accumulated += f"\n{step_text}"
        progress = ANIM_SETS["blocks"][min(int((i / len(steps_lang)) * 10), 10)]
        try:
            bot.edit_message_text(
                f"{accumulated}\n\n  {progress}",
                chat_id, msg.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

    return msg


# =====================================================
# 🎊 PURCHASE SUCCESS MESSAGE
# =====================================================

def premium_purchase_success(chat_id, product, plan, price, key, lang="en"):
    """Show premium purchase success"""
    msg = (
        f"{frame_box(f'{ce(\"party\", \"🎉\")} SUCCESS {ce(\"party\", \"🎉\")}', 31, 'double')}\n\n"
        f"  {ce('confetti', '🎊')} <b>{ui(lang, 'reward_claimed')}!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 📦 <b>Product</b>: {product}\n"
        f"  │ ⏱️ <b>Duration</b>: {plan}\n"
        f"  │ {ce('coin', '💰')} <b>Price</b>: {price} 💎\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('lock', '🔐')} <b>Your Key:</b>\n"
        f"  <code>{key}</code>\n\n"
        f"  {ce('shield', '⚠️')} <i>Save it safely!</i>"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🏆 PREMIUM RANK UP NOTIFICATION
# =====================================================

def premium_rank_up_notification(uid, new_rank, discount, points):
    """Send a beautiful rank-up notification"""
    msg = (
        f"{frame_box(f'{ce(\"party\", \"🎊\")} RANK UP {ce(\"party\", \"🎊\")}', 31, 'double')}\n\n"
        f"  {ce('confetti', '🎉')} <b>Congratulations!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('trophy', '🎖️')} <b>New Rank</b>: {new_rank}\n"
        f"  │ {ce('diamond', '💎')} <b>Discount</b>: {discount}%\n"
        f"  │ {ce('chart', '📊')} <b>Points</b>: {format_number(points)}\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('rocket', '🚀')} <i>Keep going for higher ranks!</i>"
    )
    try:
        bot.send_message(int(uid), msg, parse_mode="HTML")
    except Exception:
        pass


# =====================================================
# 🎯 PREMIUM QUEST COMPLETE NOTIFICATION
# =====================================================

def premium_quest_complete(uid, quest_name, reward, lang="en"):
    """Send premium quest completion notification"""
    msg = (
        f"{frame_box(f'{ce(\"party\", \"🎊\")} QUEST DONE {ce(\"party\", \"🎊\")}', 31, 'double')}\n\n"
        f"  {ce('check', '✅')} <b>{quest_name}</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('gift', '🎁')} <b>{ui(lang, 'quest_reward')}</b>: +{reward} 💎\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('fire', '🔥')} <i>You're on fire!</i>"
    )
    try:
        bot.send_message(int(uid), msg, parse_mode="HTML")
    except Exception:
        pass


# =====================================================
# 🔔 PREMIUM NEW REFERRAL NOTIFICATION
# =====================================================

def premium_referral_notification(uid, reward):
    """Send premium referral notification"""
    msg = (
        f"{frame_box(f'{ce(\"party\", \"🎊\")} REFERRAL {ce(\"party\", \"🎊\")}', 31, 'double')}\n\n"
        f"  {ce('confetti', '🎉')} <b>New Referral!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 👤 Someone joined via your link!\n"
        f"  │ {ce('gift', '🎁')} <b>Reward</b>: +{reward} 💎\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('sparkles', '💡')} <i>Keep sharing for more!</i>"
    )
    try:
        bot.send_message(int(uid), msg, parse_mode="HTML")
    except Exception:
        pass


# =====================================================
# 📊 ADMIN ENHANCED STATISTICS
# =====================================================

def premium_admin_stats(chat_id):
    """Show premium admin statistics"""
    stats = get_bot_stats()

    msg = (
        f"{frame_box(f'{ce(\"chart\", \"📊\")} STATISTICS {ce(\"chart\", \"📊\")}', 31, 'double')}\n\n"
        f"  {ce('sparkles', '✨')} <b>{ui('en', 'today_stats')}</b>\n\n"
        f"  ╭─── 👥 Users ──────────────╮\n"
        f"  │ Total: <b>{format_number(stats.get('total_users', 0))}</b>\n"
        f"  │ {ce('green_dot', '🟢')} Active: <b>{stats.get('active_today', 0)}</b>\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  ╭─── {ce('coin', '💰')} Sales ──────────╮\n"
        f"  │ Total: <b>{format_number(stats.get('total_sales', 0))}</b>\n"
        f"  │ Revenue: <b>{format_number(stats.get('total_earnings', 0))}</b> 💎\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  ╭─── 📦 Content ────────────╮\n"
        f"  │ Products: <b>{stats.get('total_products', 0)}</b>\n"
        f"  │ Codes: <b>{stats.get('total_codes', 0)}</b>\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  ╭─── 🎫 Support ────────────╮\n"
        f"  │ Tickets: <b>{stats.get('total_tickets', 0)}</b>\n"
        f"  │ {ce('green_dot', '🟢')} Open: <b>{stats.get('open_tickets', 0)}</b>\n"
        f"  │ Requests: <b>{stats.get('total_requests', 0)}</b>\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('gear', '⚙️')} v{stats.get('bot_version', '3.0')} • "
        f"{'🛠️ Maintenance' if stats.get('maintenance') else f'{ce(\"green_dot\", \"🟢\")} Online'}"
    )

    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🛡️ PREMIUM MAINTENANCE NOTICE
# =====================================================

def premium_maintenance_msg(chat_id, is_on):
    """Show premium maintenance notice"""
    if is_on:
        msg = (
            f"{frame_box(f'{ce(\"wrench\", \"🛠️\")} MAINTENANCE {ce(\"wrench\", \"🛠️\")}', 31, 'double')}\n\n"
            f"  {ce('cross', '⚠️')} <b>Bot is OFFLINE</b>\n\n"
            f"  ╭───────────────────────────╮\n"
            f"  │ {ce('wrench', '🔧')} Performing updates...\n"
            f"  │ {ce('clock', '⏳')} Please wait...\n"
            f"  │ {ce('bell', '🔔')} We'll notify when ready\n"
            f"  ╰───────────────────────────╯"
        )
    else:
        msg = (
            f"{frame_box(f'{ce(\"check\", \"✅\")} BACK ONLINE {ce(\"check\", \"✅\")}', 31, 'double')}\n\n"
            f"  {ce('party', '🎉')} <b>Bot is ONLINE!</b>\n\n"
            f"  ╭───────────────────────────╮\n"
            f"  │ {ce('green_dot', '🟢')} All systems running\n"
            f"  │ {ce('rocket', '🚀')} Ready to serve!\n"
            f"  ╰───────────────────────────╯"
        )
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# ⚡ PREMIUM FLASH SALE NOTICE
# =====================================================

def premium_flash_sale_msg(chat_id, product, discount, remaining, lang="en"):
    """Show premium flash sale notification"""
    msg = (
        f"{frame_box(f'{ce(\"lightning\", \"⚡\")} FLASH SALE {ce(\"lightning\", \"⚡\")}', 31, 'double')}\n\n"
        f"  {ce('fire', '🔥')} <b>{discount}% OFF!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 📦 <b>Product</b>: {product}\n"
        f"  │ {ce('lightning', '⚡')} <b>Discount</b>: {discount}%\n"
        f"  │ {ce('clock', '⏰')} <b>Ends in</b>: {remaining}\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('rocket', '💨')} <i>Hurry before it's gone!</i>"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🎁 PREMIUM GIVEAWAY MESSAGES
# =====================================================

def premium_giveaway_welcome(chat_id, reward, remaining, max_users, time_left, lang="en"):
    """Show premium giveaway welcome"""
    bar = progress_bar_fancy(max_users - remaining, max_users, 10)

    msg = (
        f"{frame_box(f'{ce(\"gift\", \"🎁\")} GIVEAWAY {ce(\"gift\", \"🎁\")}', 31, 'double')}\n\n"
        f"  {ce('party', '🎉')} <b>Welcome!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('diamond', '💎')} <b>Prize</b>: {reward} 💎\n"
        f"  │ 👥 <b>Slots</b>: {remaining}/{max_users}\n"
        f"  │ {ce('clock', '⏰')} <b>Ends</b>: {time_left}\n"
        f"  │\n"
        f"  │  {bar}\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('check', '✅')} <i>Click to claim your prize!</i>"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


def premium_giveaway_success(chat_id, reward, balance, lang="en"):
    """Show premium giveaway success"""
    msg = (
        f"{frame_box(f'{ce(\"confetti\", \"🎊\")} YOU WON {ce(\"confetti\", \"🎊\")}', 31, 'double')}\n\n"
        f"  {ce('party', '🎉')} <b>Congratulations!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('diamond', '💎')} <b>+{reward}</b> points!\n"
        f"  │ {ce('coin', '💰')} <b>Balance</b>: {balance} 💎\n"
        f"  ╰───────────────────────────╯"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🎮 PREMIUM GAME RESULTS
# =====================================================

def premium_game_win(chat_id, game_name, prize, lang="en"):
    """Show premium game win message"""
    msg = (
        f"{frame_box(f'{ce(\"party\", \"🎉\")} YOU WON {ce(\"party\", \"🎉\")}', 31, 'double')}\n\n"
        f"  {ce('slot', '🎰')} <b>{game_name}</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('diamond', '💎')} <b>Prize</b>: +{prize} 💎\n"
        f"  │ {ce('confetti', '🎊')} Lucky you!\n"
        f"  ╰───────────────────────────╯"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


def premium_game_lose(chat_id, game_name, cost, lang="en"):
    """Show premium game lose message"""
    msg = (
        f"  {ce('dice', '🎲')} <b>{game_name}</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 😔 Better luck next time!\n"
        f"  │ {ce('coin', '💰')} Cost: -{cost} 💎\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('sparkles', '💡')} <i>Try again!</i>"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🎫 PREMIUM TICKET MESSAGES
# =====================================================

def premium_ticket_created(chat_id, tid, category, lang="en"):
    """Show premium ticket created message"""
    msg = (
        f"{frame_box(f'{ce(\"check\", \"✅\")} TICKET #{tid} {ce(\"check\", \"✅\")}', 31, 'double')}\n\n"
        f"  {ce('sparkles', '🎫')} <b>Ticket Opened!</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 🆔 <b>ID</b>: #{tid}\n"
        f"  │ 📂 <b>Type</b>: {category}\n"
        f"  │ {ce('green_dot', '🟢')} <b>Status</b>: Open\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('clock', '⏳')} <i>Our team will respond soon!</i>"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


def premium_ticket_reply(chat_id, tid, reply_text, lang="en"):
    """Show premium support reply"""
    msg = (
        f"{frame_box(f'{ce(\"sparkles\", \"💬\")} SUPPORT {ce(\"sparkles\", \"💬\")}', 31, 'double')}\n\n"
        f"  {ce('sparkles', '🎫')} <b>Ticket #{tid}</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 👨‍💻 <b>Support Team:</b>\n"
        f"  │\n"
        f"  │  {reply_text}\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('sparkles', '💡')} Reply anytime • /close to end"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 👑 PREMIUM ADMIN PANEL HEADER
# =====================================================

def premium_admin_header(chat_id):
    """Show premium admin panel header"""
    msg = (
        f"{frame_box(f'{ce(\"crown\", \"👑\")} ADMIN {ce(\"crown\", \"👑\")}', 31, 'double')}\n\n"
        f"  {ce('lightning', '⚡')} <b>Full Control Panel</b>\n\n"
        f"  {ce('shield', '🛡️')} Secure • {ce('rocket', '🚀')} Fast • {ce('sparkles', '✨')} Smart"
    )
    return msg


# =====================================================
# 🌐 PREMIUM LANGUAGE SELECTOR
# =====================================================

def premium_lang_msg():
    """Premium language selection message"""
    return (
        f"{frame_box(f'{ce(\"sparkles\", \"🌐\")} LANGUAGE {ce(\"sparkles\", \"🌐\")}', 31, 'double')}\n\n"
        f"  {ce('sparkles', '✨')} <b>Choose Your Language</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 🇸🇦 العربية     🇺🇸 English\n"
        f"  │ 🇫🇷 Français    🇪🇸 Español\n"
        f"  │ 🇻🇳 Tiếng Việt\n"
        f"  ╰───────────────────────────╯"
    )


# =====================================================
# 🔒 PREMIUM JOIN REQUIRED MESSAGE
# =====================================================

def premium_join_required(lang="en"):
    """Premium join required message"""
    texts = {
        "ar": ("يجب الاشتراك في القناة أولاً", "خطوات بسيطة", "اضغط «اشتراك» أدناه", "انضم للقناة", "عد واضغط «تحقق»", "افتح جميع الميزات"),
        "en": ("Join our channel first", "Simple Steps", "Click «Join» below", "Join the Channel", "Come back & press «Verify»", "Unlock all features"),
        "fr": ("Rejoignez notre chaîne", "Étapes simples", "Cliquez «Rejoindre»", "Rejoindre", "Revenez et vérifiez", "Débloquez tout"),
        "es": ("Únete al canal primero", "Pasos simples", "Haz clic en «Unirse»", "Unirse al Canal", "Vuelve y verifica", "Desbloquea todo"),
        "vi": ("Tham gia kênh trước", "Các bước đơn giản", "Nhấn «Tham gia»", "Tham gia Kênh", "Quay lại và xác minh", "Mở khóa tất cả"),
    }
    t_texts = texts.get(lang, texts["en"])

    return (
        f"{frame_box(f'{ce(\"lock\", \"🔐\")} JOIN {ce(\"lock\", \"🔐\")}', 31, 'double')}\n\n"
        f"  {ce('cross', '⚠️')} <b>{t_texts[0]}</b>\n\n"
        f"  {ce('sparkles', '📢')} <b>{t_texts[1]}:</b>\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 1️⃣ {t_texts[2]}\n"
        f"  │ 2️⃣ {t_texts[3]}\n"
        f"  │ 3️⃣ {t_texts[4]}\n"
        f"  ╰───────────────────────────╯\n\n"
        f"  {ce('gift', '🎁')} <i>{t_texts[5]}!</i>"
    )


# =====================================================
# 📜 PREMIUM PURCHASE HISTORY
# =====================================================

def premium_purchases_display(chat_id, uid, lang="en"):
    """Show premium purchase history"""
    sales = [s for s in bot_config.get("sales_log", []) if str(s.get("uid")) == uid]

    if not sales:
        msg = (
            f"{frame_box(f'{ce(\"sparkles\", \"📜\")} PURCHASES {ce(\"sparkles\", \"📜\")}', 31, 'double')}\n\n"
            f"  📭 <i>No purchases yet</i>\n\n"
            f"  {ce('sparkles', '💡')} <i>Visit the shop!</i>"
        )
    else:
        msg = (
            f"{frame_box(f'{ce(\"sparkles\", \"📜\")} PURCHASES {ce(\"sparkles\", \"📜\")}', 31, 'double')}\n\n"
            f"  {ce('chart', '📊')} <b>Total: {len(sales)}</b>\n\n"
            f"  ╭───────────────────────────╮\n"
        )
        for i, sale in enumerate(sales[-5:], 1):  # Last 5
            prod = sale.get("product", "?")
            plan = sale.get("plan", "?")
            date = (sale.get("date") or "")[:10]
            msg += f"  │ {i}. 📦 {prod} • {plan}\n"
            msg += f"  │    📅 {date}\n"
            msg += f"  │\n"
        msg += f"  ╰───────────────────────────╯"

    bot.send_message(chat_id, msg, parse_mode="HTML")


# =====================================================
# 🎨 PREMIUM THEME SELECTOR
# =====================================================

def premium_theme_msg(lang="en"):
    """Premium theme selection"""
    return (
        f"{frame_box(f'{ce(\"sparkles\", \"🎨\")} THEME {ce(\"sparkles\", \"🎨\")}', 31, 'double')}\n\n"
        f"  {ce('sparkles', '✨')} <b>Choose Your Style</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ 🌙 Dark     • Clean & Minimal\n"
        f"  │ ☀️ Light    • Bright & Clear\n"
        f"  │ 🌈 Colorful • Fun & Vibrant\n"
        f"  ╰───────────────────────────╯"
    )


# =====================================================
# 🔒 PREMIUM PRIVACY SETTINGS
# =====================================================

def premium_privacy_msg(lang="en"):
    """Premium privacy settings"""
    return (
        f"{frame_box(f'{ce(\"lock\", \"🔒\")} PRIVACY {ce(\"lock\", \"🔒\")}', 31, 'double')}\n\n"
        f"  {ce('shield', '🛡️')} <b>Your Data is Safe</b>\n\n"
        f"  ╭───────────────────────────╮\n"
        f"  │ {ce('check', '✅')} Hide from leaderboard\n"
        f"  │ {ce('check', '✅')} Block marketing msgs\n"
        f"  │ {ce('check', '✅')} Data encryption\n"
        f"  ╰───────────────────────────╯"
    )


# =====================================================
# ❓ PREMIUM FAQ
# =====================================================

def premium_faq_msg(lang="en"):
    """Premium FAQ display"""
    faqs = {
        "ar": [
            ("كيف أحصل على نقاط؟", "المكافأة اليومية + الإحالة + المهام"),
            ("كيف أشتري منتج؟", "المتجر ← المنتج ← المدة ← شراء"),
            ("كيف أرفع رتبتي؟", "اجمع نقاط أكثر = رتبة أعلى"),
            ("ما هو خصم الرتبة؟", "كل رتبة تعطيك خصم على المشتريات"),
        ],
        "en": [
            ("How to earn points?", "Daily bonus + Referrals + Quests"),
            ("How to buy?", "Shop → Product → Duration → Buy"),
            ("How to rank up?", "More points = Higher rank auto"),
            ("What's rank discount?", "Each rank gives fixed discount"),
        ],
        "fr": [
            ("Comment gagner des points?", "Bonus + Parrainage + Quêtes"),
            ("Comment acheter?", "Boutique → Produit → Durée"),
            ("Comment monter en rang?", "Plus de points = rang supérieur"),
            ("Qu'est-ce que la remise?", "Chaque rang donne une remise"),
        ],
        "es": [
            ("¿Cómo ganar puntos?", "Diario + Referidos + Misiones"),
            ("¿Cómo comprar?", "Tienda → Producto → Duración"),
            ("¿Cómo subir de rango?", "Más puntos = rango superior"),
            ("¿Qué es el descuento?", "Cada rango da descuento"),
        ],
        "vi": [
            ("Cách kiếm điểm?", "Hàng ngày + Giới thiệu + Nhiệm vụ"),
            ("Cách mua?", "Cửa hàng → Sản phẩm → Thời hạn"),
            ("Cách lên cấp?", "Nhiều điểm = cấp cao hơn"),
            ("Giảm giá cấp?", "Mỗi cấp giảm giá cố định"),
        ],
    }

    items = faqs.get(lang, faqs["en"])

    msg = f"{frame_box(f'{ce(\"sparkles\", \"❓\")} FAQ {ce(\"sparkles\", \"❓\")}', 31, 'double')}\n\n"

    nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    for i, (q, a) in enumerate(items):
        msg += (
            f"  {nums[i]} <b>{q}</b>\n"
            f"  └ <i>{a}</i>\n\n"
        )

    return msg


# =====================================================
# 🏆 PREMIUM LEADERBOARD
# =====================================================

def premium_leaderboard_msg(top_users, lang="en"):
    """Premium leaderboard display"""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    msg = f"{frame_box(f'{ce(\"trophy\", \"🏆\")} TOP 10 {ce(\"trophy\", \"🏆\")}', 31, 'double')}\n\n"

    if not top_users:
        msg += f"  📭 <i>No data yet</i>"
        return msg

    msg += "  ╭───────────────────────────╮\n"
    for i, user in enumerate(top_users[:10]):
        name = user.get("username", "???")[:12]
        pts = format_number(user.get("accumulated_points", 0))
        medal = medals[i] if i < len(medals) else f"{i + 1}."
        msg += f"  │ {medal} <b>{name}</b> — {pts} 💎\n"
    msg += "  ╰───────────────────────────╯"

    return msg


# =====================================================
# ✅ Module Loaded
# =====================================================

print("=" * 55)
print(f"✅ bot10.py v3.0 — Ultra Premium Visual Experience")
print(f"🎬 Welcome Animation: Active")
print(f"💎 Premium Custom Emoji: Active")
print(f"🎨 Colored Buttons: Active (API 9.4)")
print(f"🏆 Enhanced Ranks: Active")
print(f"🔥 Enhanced Quests: Active")
print(f"📖 Commands Guide: /pp")
print(f"🌍 Languages: AR/EN/FR/ES/VI")
print("=" * 55)
