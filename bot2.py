"""
==============================================
bot2.py - VIP + Stars + Auto-Restock + Giveaway
==============================================
"""

import random
import time
import threading
from datetime import datetime, timedelta
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, CHANNEL_LINK, t
from database import (bot_config, save_json, DB_CONFIG, DB_KEYS, get_user, 
                      update_user_data, update_user_rank_and_quests,
                      keys_store, prices_config)
from utils import (
    generate_captcha, broadcast_channel_message, get_publish_channels,
    publish_vip_purchase_to_channels, publish_stars_conversion_to_channels,
)

# =====================================================
# INITIALIZATION
# =====================================================

def init_all_configs():
    defaults = {
        "giveaways": {},
        "giveaway_captchas": {},
        "vip_price_stars": 100,
        "star_to_points_rate": 2,
        "vip_subscribers": {},
        "vip_last_weekly_code": {},
        "pending_restocks": {},
        "restock_history": [],
        "temp_admin_actions": {}
    }
    changed = False
    for k, v in defaults.items():
        if k not in bot_config:
            bot_config[k] = v
            changed = True
    if changed:
        save_json(DB_CONFIG, bot_config)

init_all_configs()

# Temporary storage
temp_restock_setup = {}
temp_admin_action = {}

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def is_admin_user(uid):
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        return True
    u = get_user(uid) or {}
    return u.get("is_admin", False)

def is_vip_active(uid):
    uid = str(uid)
    vip_data = bot_config.get("vip_subscribers", {}).get(uid)
    if not vip_data:
        return False
    try:
        if datetime.now() < datetime.fromisoformat(vip_data["expires"]):
            return True
        else:
            del bot_config["vip_subscribers"][uid]
            save_json(DB_CONFIG, bot_config)
            return False
    except:
        return False

def get_vip_days_left(uid):
    uid = str(uid)
    vip_data = bot_config.get("vip_subscribers", {}).get(uid)
    if not vip_data:
        return 0
    try:
        diff = datetime.fromisoformat(vip_data["expires"]) - datetime.now()
        return max(0, diff.days)
    except:
        return 0

def activate_vip(uid, days=30):
    uid = str(uid)
    expires = datetime.now() + timedelta(days=days)
    if "vip_subscribers" not in bot_config:
        bot_config["vip_subscribers"] = {}
    bot_config["vip_subscribers"][uid] = {
        "activated": datetime.now().isoformat(),
        "expires": expires.isoformat(),
        "days": days
    }
    save_json(DB_CONFIG, bot_config)
    return expires

def deactivate_vip(uid):
    uid = str(uid)
    if uid in bot_config.get("vip_subscribers", {}):
        del bot_config["vip_subscribers"][uid]
        save_json(DB_CONFIG, bot_config)
        return True
    return False

# =====================================================
# GIVEAWAY SYSTEM  —  Premium Multi-Type Engine v2.0
# =====================================================
# Supported campaign types (each boosts a different part of the channel):
#   link      -> Classic "first N to claim" via private link + captcha
#   draw      -> Random Winner Draw (enter, bot picks winners at the deadline)
#   react     -> React/Comment to enter (boosts post reach), winners at deadline
#   quiz      -> Answer a question correctly to enter the draw
#   milestone -> Auto-publishes a reward drop when the channel hits a subscriber goal
# =====================================================

import string as _string
import html as _html
from utils import check_channel_join

GW_TYPES = {
    "link":      {"label": "🔗 Classic Link Claim",   "short": "Link",
                  "desc": "First N users to open the link & solve a captcha win instantly."},
    "draw":      {"label": "🎲 Random Winner Draw",   "short": "Draw",
                  "desc": "Members enter the draw; the bot picks random winners when time ends."},
    "react":     {"label": "❤️ React-to-Enter",       "short": "React",
                  "desc": "Members react/comment on the channel post, then confirm to enter."},
    "quiz":      {"label": "🧠 Quiz Giveaway",        "short": "Quiz",
                  "desc": "Members must answer a question correctly to enter the draw."},
    "milestone": {"label": "📈 Subscriber Milestone", "short": "Milestone",
                  "desc": "Reward drop auto-publishes when the channel reaches a subscriber goal."},
}


def _esc(text):
    """HTML-escape admin/user supplied text."""
    try:
        return _html.escape(str(text))
    except Exception:
        return str(text)


def _now():
    return datetime.now()


def _notify_admins(text):
    """Send a live report to both admins (best-effort)."""
    for adm in (ADMIN_PRIMARY, ADMIN_SECONDARY):
        try:
            bot.send_message(adm, text, parse_mode="HTML")
        except Exception:
            pass


def generate_giveaway_code():
    chars = _string.ascii_uppercase + _string.digits
    return ''.join(random.choice(chars) for _ in range(8))


def create_giveaway(reward, max_users, hours, gw_type="link", created_by=None, **extra):
    """Create a giveaway of any type. Backward compatible with the classic signature."""
    code = generate_giveaway_code()
    if gw_type not in GW_TYPES:
        gw_type = "link"
    data = {
        "code": code,
        "type": gw_type,
        "reward": int(reward),
        "max_users": int(max_users),
        "hours": int(hours),
        "expires": (_now() + timedelta(hours=int(hours))).isoformat(),
        "created": _now().isoformat(),
        "created_by": str(created_by) if created_by else None,
        "claimed_by": [],
        "entrants": [],
        "winners": [],
        "status": "active",
        "published": False,
    }
    if gw_type == "quiz":
        data["quiz_question"] = extra.get("quiz_question", "")
        data["quiz_options"] = extra.get("quiz_options", [])
        data["quiz_answer"] = extra.get("quiz_answer", 0)  # index into quiz_options
    if gw_type == "milestone":
        data["milestone_target"] = int(extra.get("milestone_target", 0))
        data["status"] = "waiting"  # not published until the target is reached
    bot_config.setdefault("giveaways", {})[code] = data
    save_json(DB_CONFIG, bot_config)
    return code


def get_giveaway(code):
    return bot_config.get("giveaways", {}).get(code)


def get_all_giveaways():
    return bot_config.get("giveaways", {})


def _is_expired(gw):
    try:
        return _now() > datetime.fromisoformat(gw["expires"])
    except Exception:
        return False


def is_giveaway_valid(code):
    """Validity for CLAIM-style giveaways (link / milestone drops)."""
    gw = get_giveaway(code)
    if not gw:
        return False, "not_found"
    if gw.get("status") != "active":
        return False, gw.get("status", "inactive")
    if _is_expired(gw):
        gw["status"] = "expired"
        save_json(DB_CONFIG, bot_config)
        return False, "expired"
    if len(gw.get("claimed_by", [])) >= gw.get("max_users", 0):
        gw["status"] = "full"
        save_json(DB_CONFIG, bot_config)
        return False, "full"
    return True, "valid"


def has_user_claimed_giveaway(code, uid):
    gw = get_giveaway(code)
    if not gw:
        return False
    return str(uid) in gw.get("claimed_by", [])


def claim_giveaway(code, uid):
    gw = get_giveaway(code)
    if not gw:
        return False
    gw.setdefault("claimed_by", [])
    uid = str(uid)
    if uid not in gw["claimed_by"]:
        gw["claimed_by"].append(uid)
    if len(gw["claimed_by"]) >= gw.get("max_users", 0):
        gw["status"] = "full"
    save_json(DB_CONFIG, bot_config)
    return True


def has_user_entered(code, uid):
    gw = get_giveaway(code)
    if not gw:
        return False
    return str(uid) in gw.get("entrants", []) or str(uid) in gw.get("claimed_by", [])


def enter_giveaway(code, uid):
    """Register a participant for draw/react/quiz type giveaways."""
    gw = get_giveaway(code)
    if not gw:
        return False
    gw.setdefault("entrants", [])
    uid = str(uid)
    if uid in gw["entrants"]:
        return False
    gw["entrants"].append(uid)
    save_json(DB_CONFIG, bot_config)
    return True


def process_giveaway_claim(uid, code):
    """Classic instant-claim (link / milestone). Awards the reward immediately."""
    valid, reason = is_giveaway_valid(code)
    if not valid:
        return False, reason
    if has_user_claimed_giveaway(code, uid):
        return False, "already_claimed"
    gw = get_giveaway(code)
    reward = gw["reward"]
    update_user_data(uid, points=reward, accumulated_points=reward)
    update_user_rank_and_quests(uid)
    claim_giveaway(code, uid)
    if bot_config.get("gw_live_reports", True):
        u = get_user(str(uid)) or {}
        _notify_admins(
            "🎁 <b>Giveaway Claimed</b>\n"
            f"├ Code: <code>{code}</code> ({gw.get('type', 'link')})\n"
            f"├ User: @{_esc(u.get('username', 'N/A'))} (<code>{uid}</code>)\n"
            f"├ Reward: +{reward} pts\n"
            f"└ Progress: {len(gw.get('claimed_by', []))}/{gw.get('max_users', 0)}"
        )
    return True, reward


def pick_winners(code):
    """Randomly select winners among entrants for draw/react/quiz, award & record them."""
    gw = get_giveaway(code)
    if not gw:
        return []
    pool = list(dict.fromkeys(gw.get("entrants", []) + gw.get("claimed_by", [])))
    need = min(gw.get("max_users", 0), len(pool))
    winners = random.sample(pool, need) if need > 0 else []
    reward = gw.get("reward", 0)
    for w in winners:
        try:
            update_user_data(w, points=reward, accumulated_points=reward)
            update_user_rank_and_quests(w)
        except Exception:
            pass
    gw["winners"] = winners
    gw["claimed_by"] = list(set(gw.get("claimed_by", []) + winners))
    gw["status"] = "completed"
    save_json(DB_CONFIG, bot_config)
    return winners


# ----- Captcha (kept for the classic link claim flow used by bot.py) -----

def start_giveaway_captcha(uid, code):
    u = get_user(str(uid)) or {}
    lang = u.get("lang", "en")
    emoji, name, opts = generate_captcha(lang)
    bot_config.setdefault("giveaway_captchas", {})[str(uid)] = {
        "code": code, "answer": emoji, "attempts": 0,
        "expires": (_now() + timedelta(minutes=5)).isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    m = types.InlineKeyboardMarkup(row_width=2)
    random.shuffle(opts)
    m.add(*[types.InlineKeyboardButton(o, callback_data=f"gwcap_{o}") for o in opts])
    gw = get_giveaway(code)
    reward = gw["reward"] if gw else 0
    try:
        bot.send_message(int(uid),
            f"🎁 <b>GIVEAWAY CLAIM</b>\n\n"
            f"💎 Prize: {reward} points\n\n"
            f"🛡️ Press: <b>{name}</b> {emoji}",
            reply_markup=m, parse_mode="HTML")
    except Exception:
        pass


def verify_giveaway_captcha(uid, answer):
    uid = str(uid)
    sessions = bot_config.get("giveaway_captchas", {})
    if uid not in sessions:
        return "no_session", None
    session = sessions[uid]
    try:
        if _now() > datetime.fromisoformat(session["expires"]):
            del sessions[uid]
            save_json(DB_CONFIG, bot_config)
            return "expired", None
    except Exception:
        pass
    if str(answer) == session["answer"]:
        code = session["code"]
        del sessions[uid]
        save_json(DB_CONFIG, bot_config)
        return "correct", code
    session["attempts"] = session.get("attempts", 0) + 1
    if session["attempts"] >= 3:
        del sessions[uid]
        save_json(DB_CONFIG, bot_config)
        return "banned", None
    save_json(DB_CONFIG, bot_config)
    return "wrong", None


# ----- Channel publishing (type-aware) -----

def _bot_username():
    try:
        return bot.get_me().username
    except Exception:
        return "bot"


def _time_left_text(gw):
    try:
        delta = datetime.fromisoformat(gw["expires"]) - _now()
        secs = int(delta.total_seconds())
        if secs <= 0:
            return "Ended"
        h, rem = divmod(secs, 3600)
        mnt, _ = divmod(rem, 60)
        if h >= 24:
            return f"{h // 24}d {h % 24}h"
        return f"{h}h {mnt}m"
    except Exception:
        return f"{gw.get('hours', 0)}h"


def build_giveaway_post(code):
    """Returns (text, keyboard) for the channel post, tailored to the giveaway type."""
    gw = get_giveaway(code)
    if not gw:
        return None, None
    gtype = gw.get("type", "link")
    reward = gw.get("reward", 0)
    slots = gw.get("max_users", 0)
    tleft = _time_left_text(gw)
    bot_user = _bot_username()
    link = f"https://t.me/{bot_user}?start=gw_{code}"

    header = (
        "╔═══════════════════════╗\n"
        "║   🎁  GIVEAWAY TIME  🎁   ║\n"
        "╚═══════════════════════╝\n\n"
    )
    m = types.InlineKeyboardMarkup()

    if gtype == "link":
        text = (
            f"{header}"
            f"🎊 <b>FREE REWARD DROP!</b> 🎊\n\n"
            f"💎 Prize: <b>{reward} points</b>\n"
            f"👥 Winners: <b>First {slots}</b> to claim\n"
            f"⏰ Ends in: <b>{tleft}</b>\n\n"
            f"⚡ <i>Fastest fingers win — tap below!</i>"
        )
        m.add(types.InlineKeyboardButton("🎁 CLAIM NOW", url=link))

    elif gtype == "draw":
        entered = len(gw.get("entrants", []))
        text = (
            f"{header}"
            f"🎲 <b>RANDOM WINNER DRAW</b> 🎲\n\n"
            f"💎 Prize: <b>{reward} points</b> each\n"
            f"🏆 Winners: <b>{slots} lucky members</b>\n"
            f"⏰ Draw closes in: <b>{tleft}</b>\n"
            f"👥 Entered so far: <b>{entered}</b>\n\n"
            f"🍀 <i>Enter now — winners are picked randomly live!</i>"
        )
        m.add(types.InlineKeyboardButton("🎲 ENTER THE DRAW", url=link))

    elif gtype == "react":
        text = (
            f"{header}"
            f"❤️ <b>REACT &amp; WIN</b> ❤️\n\n"
            f"💎 Prize: <b>{reward} points</b> each\n"
            f"🏆 Winners: <b>{slots} members</b>\n"
            f"⏰ Closes in: <b>{tleft}</b>\n\n"
            f"📌 <b>How to enter:</b>\n"
            f"1️⃣ React to this post with any emoji\n"
            f"2️⃣ Tap the button below to confirm\n\n"
            f"🔥 <i>More reactions = more reach for our channel!</i>"
        )
        m.add(types.InlineKeyboardButton("✅ I REACTED — ENTER", url=link))

    elif gtype == "quiz":
        entered = len(gw.get("entrants", []))
        q = _esc(gw.get("quiz_question", "Trivia time!"))
        text = (
            f"{header}"
            f"🧠 <b>QUIZ GIVEAWAY</b> 🧠\n\n"
            f"❓ <b>{q}</b>\n\n"
            f"💎 Prize: <b>{reward} points</b> each\n"
            f"🏆 Winners: <b>{slots} correct members</b>\n"
            f"⏰ Closes in: <b>{tleft}</b>\n"
            f"✍️ Entered: <b>{entered}</b>\n\n"
            f"🎯 <i>Answer correctly below to enter the draw!</i>"
        )
        m.add(types.InlineKeyboardButton("🧠 ANSWER & ENTER", url=link))

    elif gtype == "milestone":
        target = gw.get("milestone_target", 0)
        text = (
            f"{header}"
            f"📈 <b>MILESTONE REACHED!</b> 🎉\n\n"
            f"🎊 We hit <b>{target} subscribers</b>! 🎊\n\n"
            f"💎 Reward: <b>{reward} points</b>\n"
            f"👥 First <b>{slots}</b> to claim win\n\n"
            f"🙏 <i>Thank you for being part of the family!</i>"
        )
        m.add(types.InlineKeyboardButton("🎁 CLAIM REWARD", url=link))

    return text, m


def _as_channel_target(channel_id):
    try:
        return int(channel_id)
    except (TypeError, ValueError):
        return channel_id


def publish_giveaway_to_channel(code):
    """Publish (or re-publish) a giveaway post in every added channel."""
    gw = get_giveaway(code)
    if not gw:
        return None
    text, keyboard = build_giveaway_post(code)
    if not text:
        return None

    delivered = broadcast_channel_message(
        text, reply_markup=keyboard, parse_mode="HTML"
    )
    if not delivered:
        return None

    # Keep the legacy key for existing giveaway records/callers and retain the
    # full map so counter updates and cancellation apply to every channel.
    gw["channel_messages"] = delivered
    gw["channel_msg_id"] = next(iter(delivered.values()))
    gw["published"] = True
    if gw.get("status") == "waiting":
        gw["status"] = "active"
    save_json(DB_CONFIG, bot_config)
    return gw["channel_msg_id"]


def _giveaway_channel_messages(gw):
    """Return stored multi-channel IDs, including records from the old format."""
    messages = gw.get("channel_messages") or {}
    if messages:
        return messages
    if gw.get("channel_msg_id"):
        return {str(CHANNEL_ID): gw["channel_msg_id"]}
    return {}


def update_channel_post(code):
    """Refresh live giveaway counters in every published channel post."""
    gw = get_giveaway(code)
    channel_messages = _giveaway_channel_messages(gw or {})
    if not gw or not channel_messages:
        return False
    text, keyboard = build_giveaway_post(code)
    updated = False
    for channel_id, message_id in channel_messages.items():
        try:
            bot.edit_message_text(
                text, _as_channel_target(channel_id), message_id,
                reply_markup=keyboard, parse_mode="HTML"
            )
            updated = True
        except Exception:
            pass
    return updated


def cancel_giveaway(code):
    gw = get_giveaway(code)
    if not gw:
        return False
    gw["status"] = "cancelled"
    for channel_id, message_id in _giveaway_channel_messages(gw).items():
        try:
            bot.delete_message(_as_channel_target(channel_id), message_id)
        except Exception:
            pass
    save_json(DB_CONFIG, bot_config)
    return True


def get_giveaways_stats():
    gws = get_all_giveaways()
    by_type = {}
    for g in gws.values():
        k = g.get("type", "link")
        by_type[k] = by_type.get(k, 0) + 1
    return {
        "total": len(gws),
        "active": sum(1 for g in gws.values() if g.get("status") == "active"),
        "waiting": sum(1 for g in gws.values() if g.get("status") == "waiting"),
        "expired": sum(1 for g in gws.values() if g.get("status") == "expired"),
        "full": sum(1 for g in gws.values() if g.get("status") == "full"),
        "completed": sum(1 for g in gws.values() if g.get("status") == "completed"),
        "cancelled": sum(1 for g in gws.values() if g.get("status") == "cancelled"),
        "total_claimed": sum(len(g.get("claimed_by", [])) for g in gws.values()),
        "total_entrants": sum(len(g.get("entrants", [])) for g in gws.values()),
        "total_winners": sum(len(g.get("winners", [])) for g in gws.values()),
        "total_points_given": sum(
            g.get("reward", 0) * max(len(g.get("winners", [])), len(g.get("claimed_by", [])))
            for g in gws.values()
        ),
        "by_type": by_type,
    }


def get_channel_member_count():
    """Use the largest added channel for the existing milestone feature."""
    counts = []
    for channel in get_publish_channels():
        try:
            counts.append(bot.get_chat_member_count(channel["id"]))
        except Exception:
            pass
    return max(counts, default=0)


# ----- Background worker: expiry, draw finishing, milestone watching -----

def _announce_winners(code, winners):
    gw = get_giveaway(code)
    if not gw:
        return
    reward = gw.get("reward", 0)
    for w in winners:
        try:
            bot.send_message(int(w),
                "🏆 <b>YOU WON THE GIVEAWAY!</b> 🏆\n\n"
                f"💎 Prize: <b>+{reward} points</b>\n"
                f"🎁 Code: <code>{code}</code>\n\n"
                f"✨ Points were added to your balance. Congrats!",
                parse_mode="HTML")
        except Exception:
            pass
    lines = []
    for w in winners:
        u = get_user(str(w)) or {}
        lines.append(f"• @{_esc(u.get('username', 'N/A'))} (<code>{w}</code>)")
    _notify_admins(
        "🏆 <b>Giveaway Finished — Winners</b>\n"
        f"├ Code: <code>{code}</code> ({gw.get('type', 'draw')})\n"
        f"├ Reward: +{reward} pts each\n"
        f"├ Entrants: {len(gw.get('entrants', []))}\n"
        f"└ Winners ({len(winners)}):\n" + ("\n".join(lines) if lines else "• (no participants)")
    )


def _giveaway_maintenance_cycle():
    gws = get_all_giveaways()
    changed = False
    for code, gw in list(gws.items()):
        status = gw.get("status")
        gtype = gw.get("type", "link")

        # Milestone watching (not time based)
        if status == "waiting" and gtype == "milestone":
            target = gw.get("milestone_target", 0)
            if target and get_channel_member_count() >= target:
                publish_giveaway_to_channel(code)
                if bot_config.get("gw_live_reports", True):
                    _notify_admins(
                        "📈 <b>Milestone Reached!</b>\n"
                        f"├ Goal: {target} subscribers\n"
                        f"└ Reward drop <code>{code}</code> published to the channel 🎉"
                    )
                changed = True
            continue

        if status != "active":
            continue

        if _is_expired(gw):
            if gtype in ("draw", "react", "quiz"):
                winners = pick_winners(code)
                update_channel_post(code)
                _announce_winners(code, winners)
            else:
                gw["status"] = "expired"
                update_channel_post(code)
            changed = True
    if changed:
        save_json(DB_CONFIG, bot_config)


def _start_giveaway_worker():
    def worker():
        while True:
            try:
                _giveaway_maintenance_cycle()
            except Exception as e:
                print(f"⚠️ Giveaway worker: {e}")
            time.sleep(30)
    threading.Thread(target=worker, daemon=True).start()


_start_giveaway_worker()


# =====================================================
# CHANNEL MESSAGES
# =====================================================

def _first_delivered_message_id(deliveries):
    """Keep the old integer return contract for legacy callers."""
    return next(iter(deliveries.values()), None)


def send_custom_channel_message(text):
    """Publish a styled channel message in every configured channel."""
    formatted = (
        f"╔═══════════════════════╗\n"
        f"║  📢 NOTICE 📢   ║\n"
        f"╚═══════════════════════╝\n\n"
        f"{text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 Official Announcement"
    )
    return _first_delivered_message_id(
        broadcast_channel_message(formatted, parse_mode="HTML")
    )


def send_raw_channel_message(text):
    """Publish a raw HTML channel message in every configured channel."""
    return _first_delivered_message_id(
        broadcast_channel_message(text, parse_mode="HTML")
    )


def delete_channel_message(msg_id):
    """Delete the supplied message ID from all configured channels when present."""
    deleted = False
    for channel in get_publish_channels():
        try:
            bot.delete_message(channel["id"], int(msg_id))
            deleted = True
        except Exception:
            pass
    return deleted

def format_giveaway_win_message(reward, lang="ar"):
    return f"🎊 <b>Congrats! +{reward} pts</b>"

def format_giveaway_error(reason, lang="ar"):
    errors = {
        "not_found": "❌ Invalid link!",
        "expired": "⏰ Expired!",
        "full": "😢 Full!",
        "already_claimed": "⚠️ Already claimed!",
        "inactive": "❌ Inactive",
        "cancelled": "❌ Cancelled"
    }
    return errors.get(reason, "❌ Error")

# =====================================================
# VIP CHANNEL MARKETING
# =====================================================

def publish_vip_purchase_to_channel(stars_amount=0, charge_id=None):
    """Compatibility wrapper for the all-channel VIP announcement."""
    return publish_vip_purchase_to_channels(stars_amount, charge_id)


def publish_stars_conversion_to_channel(stars_amount, points_amount, charge_id=None):
    """Compatibility wrapper for the all-channel Stars conversion notice."""
    return publish_stars_conversion_to_channels(stars_amount, points_amount, charge_id)

# =====================================================
# AUTO RESTOCK SYSTEM (NEW - USER CONTROLLED)
# =====================================================

def create_pending_restock(product, plan, keys_list, hours):
    """
    Admin creates a scheduled restock:
    - keys will be added to stock after X hours
    """
    import string
    restock_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    scheduled_time = datetime.now() + timedelta(hours=hours)
    
    if "pending_restocks" not in bot_config:
        bot_config["pending_restocks"] = {}
    
    bot_config["pending_restocks"][restock_id] = {
        "id": restock_id,
        "product": product,
        "plan": plan,
        "keys": keys_list,
        "hours": hours,
        "scheduled_at": scheduled_time.isoformat(),
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    save_json(DB_CONFIG, bot_config)
    return restock_id, scheduled_time

def cancel_pending_restock(restock_id):
    """Cancel a scheduled restock before it happens"""
    if restock_id in bot_config.get("pending_restocks", {}):
        del bot_config["pending_restocks"][restock_id]
        save_json(DB_CONFIG, bot_config)
        return True
    return False

def get_pending_restocks():
    """Get all pending restocks"""
    return bot_config.get("pending_restocks", {})

def check_and_execute_restocks():
    """Check pending restocks and execute if time is due"""
    pending = bot_config.get("pending_restocks", {})
    now = datetime.now()
    
    for restock_id, config in list(pending.items()):
        try:
            if config.get("status") != "pending":
                continue
            
            scheduled = datetime.fromisoformat(config["scheduled_at"])
            
            if now >= scheduled:
                product = config["product"]
                plan = config["plan"]
                keys = config.get("keys", [])
                
                # Add keys to stock
                if product not in keys_store:
                    keys_store[product] = {"1 Day": [], "7 Days": [], "30 Days": []}
                if plan not in keys_store[product]:
                    keys_store[product][plan] = []
                
                added = 0
                for k in keys:
                    keys_store[product][plan].append(k)
                    added += 1
                
                save_json(DB_KEYS, keys_store)
                
                # Log to history
                if "restock_history" not in bot_config:
                    bot_config["restock_history"] = []
                bot_config["restock_history"].append({
                    "id": restock_id,
                    "product": product,
                    "plan": plan,
                    "qty": added,
                    "executed_at": now.isoformat()
                })
                bot_config["restock_history"] = bot_config["restock_history"][-100:]
                
                # Delete from pending
                del bot_config["pending_restocks"][restock_id]
                save_json(DB_CONFIG, bot_config)
                
                # Notify admin
                try:
                    bot.send_message(ADMIN_PRIMARY,
                        f"✅ <b>Auto-Restock Executed!</b>\n\n"
                        f"📦 {product}/{plan}\n"
                        f"🔑 Added: {added} keys\n"
                        f"🆔 ID: {restock_id}",
                        parse_mode="HTML")
                except: pass
                
                print(f"✅ Executed restock {restock_id}: {product}/{plan} = {added} keys")
        except Exception as e:
            print(f"⚠️ Restock error for {restock_id}: {e}")

def start_restock_thread():
    def worker():
        while True:
            try:
                check_and_execute_restocks()
            except Exception as e:
                print(f"⚠️ Restock thread: {e}")
            time.sleep(30)  # Check every 30 seconds
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print("✅ Auto-restock thread started")

start_restock_thread()
# =====================================================
# ✅ PRE-CHECKOUT HANDLER - إصلاح مشكلة تعليق الدفع
# =====================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(pre_checkout_query):
    try:
        payload = pre_checkout_query.invoice_payload
        if payload.startswith("vip_purchase_") or payload.startswith("stars_convert_"):
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            print(f"✅ Pre-checkout approved")
        else:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="❌ Invalid")
    except Exception as e:
        print(f"⚠️ Pre-checkout error: {e}")
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except:
            pass

# =====================================================
# VIP USER MENUS
# =====================================================

def show_vip_menu(chat_id, uid, msg_id=None):
    is_vip = is_vip_active(uid)
    price = bot_config.get("vip_price_stars", 100)
    
    if is_vip:
        days_left = get_vip_days_left(uid)
        msg = (
            f"╔═══════════════════════╗\n"
            f"║  👑 <b>VIP MEMBER</b> 👑  ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🌟 <b>You are a VIP!</b>\n\n"
            f"⏰ <b>Days remaining:</b> {days_left}\n\n"
            f"✨ <b>Your Benefits:</b>\n"
            f"├── 🎁 2x Daily bonus\n"
            f"├── 💰 15% discount on ALL\n"
            f"├── 📊 Advanced stock info\n"
            f"├── 🎫 Weekly free code\n"
            f"├── ⚡ Priority support\n"
            f"├── 🎰 50% off games\n"
            f"└── 👑 VIP badge"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📊 View Stock Details", callback_data="vip_stock"))
        m.add(types.InlineKeyboardButton("🎫 Get Weekly Code", callback_data="vip_weekly_code"))
        m.add(types.InlineKeyboardButton("⭐ Convert Stars", callback_data="vip_convert_stars"))
        m.add(types.InlineKeyboardButton("🔄 Renew VIP", callback_data="vip_buy"))
    else:
        msg = (
            f"╔═══════════════════════╗\n"
            f"║ 👑 <b>VIP MEMBERSHIP</b> 👑 ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🌟 <b>Become a VIP Member!</b>\n\n"
            f"💎 <b>Exclusive Benefits:</b>\n"
            f"├── 🎁 2x Daily bonus\n"
            f"├── 💰 15% discount on ALL\n"
            f"├── 📊 Advanced stock info\n"
            f"├── 🎫 Weekly free code\n"
            f"├── ⚡ Priority support\n"
            f"├── 🎰 50% off games\n"
            f"└── 👑 VIP badge\n\n"
            f"💳 <b>Monthly:</b> {price} ⭐\n"
            f"⏰ <b>Duration:</b> 30 days"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(f"👑 Subscribe ({price} ⭐)", callback_data="vip_buy"))
        m.add(types.InlineKeyboardButton("⭐ Convert Stars to Points", callback_data="vip_convert_stars"))
    
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_stars_menu(chat_id, uid, msg_id=None):
    rate = bot_config.get("star_to_points_rate", 2)
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ ⭐ <b>STARS TO POINTS</b> ⭐ ║\n"
        f"╚═══════════════════════╝\n\n"
        f"💫 <b>Convert Telegram Stars!</b>\n\n"
        f"⭐ <b>Rate:</b> 1 ⭐ = {rate} 💎\n"
        f"⚡ <b>Delivery:</b> Instant\n"
        f"🔒 <b>Secure:</b> 100%\n\n"
        f"👇 <b>Choose amount:</b>"
    )
    m = types.InlineKeyboardMarkup(row_width=2)
    for stars in [1, 5, 10, 25, 50, 100]:
        m.add(types.InlineKeyboardButton(
            f"⭐ {stars} = {stars * rate} 💎",
            callback_data=f"star_buy_{stars}"))
    
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_vip_stock_details(chat_id, uid, msg_id=None):
    if not is_vip_active(uid):
        return
    if not prices_config:
        bot.send_message(chat_id, "📭 No products")
        return
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 👑 <b>VIP STOCK INFO</b> 👑 ║\n"
        f"╚═══════════════════════╝\n\n"
    )
    for prod in prices_config.keys():
        total = sum(len(keys_store.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        msg += f"📦 <b>{prod}</b>\n"
        msg += f"┃ 📊 Total: <b>{total}</b> keys\n"
        for plan in ["1 Day", "7 Days", "30 Days"]:
            stock = len(keys_store.get(prod, {}).get(plan, []))
            icon = "✅" if stock > 5 else ("⚠️" if stock > 0 else "❌")
            msg += f"┃ {icon} {plan}: <b>{stock}</b>\n"
        msg += "╰━━━━━━━━━━━\n\n"
    
    # Show pending restocks
    pending = get_pending_restocks()
    if pending:
        msg += f"\n🔄 <b>Upcoming Restocks:</b>\n"
        for rid, cfg in list(pending.items())[:5]:
            try:
                sched = datetime.fromisoformat(cfg["scheduled_at"])
                diff = sched - datetime.now()
                if diff.total_seconds() > 0:
                    hrs = int(diff.total_seconds() // 3600)
                    mins = int((diff.total_seconds() % 3600) // 60)
                    msg += f"• {cfg['product']}/{cfg['plan']}: {len(cfg['keys'])} keys in {hrs}h {mins}m\n"
            except: pass
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="vip_stock"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="vip_back"))
    
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

# =====================================================
# ADMIN VIP/RESTOCK MENUS
# =====================================================

def show_admin_vip_menu(chat_id, msg_id=None):
    price = bot_config.get("vip_price_stars", 100)
    rate = bot_config.get("star_to_points_rate", 2)
    vip_count = len([u for u in bot_config.get("vip_subscribers", {}) if is_vip_active(u)])
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 👑 <b>VIP ADMIN PANEL</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"💳 VIP Price: <b>{price} ⭐</b>\n"
        f"⭐ Star Rate: <b>1 ⭐ = {rate} 💎</b>\n"
        f"👥 Active VIPs: <b>{vip_count}</b>"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("💰 Change VIP Price", callback_data="adm_vip_price"))
    m.add(types.InlineKeyboardButton("⭐ Change Star Rate", callback_data="adm_vip_rate"))
    m.add(types.InlineKeyboardButton("👥 List VIP Members", callback_data="adm_vip_list"))
    m.add(types.InlineKeyboardButton("👤 Manage User (VIP/Admin/Ban)", callback_data="adm_manage_user"))
    m.add(types.InlineKeyboardButton("➕ Grant VIP", callback_data="adm_vip_grant"))
    m.add(types.InlineKeyboardButton("❌ Revoke VIP", callback_data="adm_vip_revoke"))
    
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_admin_restock_menu(chat_id, msg_id=None):
    pending = get_pending_restocks()
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 📦 <b>AUTO-RESTOCK</b> 📦  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"📊 Pending: <b>{len(pending)}</b>\n\n"
        f"💡 <b>How it works:</b>\n"
        f"1. Select product & plan\n"
        f"2. Add keys (one per line)\n"
        f"3. Set delay in hours\n"
        f"4. Keys added automatically when time comes!"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("➕ Schedule New Restock", callback_data="adm_restock_new"))
    m.add(types.InlineKeyboardButton("📋 View Pending Restocks", callback_data="adm_restock_list"))
    m.add(types.InlineKeyboardButton("❌ Cancel Pending Restock", callback_data="adm_restock_cancel"))
    m.add(types.InlineKeyboardButton("📜 Restock History", callback_data="adm_restock_history"))
    
    if msg_id:
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

# =====================================================
# MESSAGE HANDLER - LISTENS FOR BUTTON TEXT
# =====================================================

@bot.message_handler(func=lambda message: message.text in [
    "👑 VIP", "⭐ Stars", "👑 إدارة VIP", "📦 التجديد التلقائي"
])
def handle_vip_stars_buttons(message):
    uid = str(message.from_user.id)
    txt = message.text
    
    if txt == "👑 VIP":
        show_vip_menu(message.chat.id, uid)
    elif txt == "⭐ Stars":
        show_stars_menu(message.chat.id, uid)
    elif txt == "👑 إدارة VIP":
        if is_admin_user(uid):
            show_admin_vip_menu(message.chat.id)
    elif txt == "📦 التجديد التلقائي":
        if is_admin_user(uid):
            show_admin_restock_menu(message.chat.id)

# =====================================================
# CALLBACK HANDLERS - VIP USER
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("vip_"))
def handle_vip_callbacks(call):
    uid = str(call.from_user.id)
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "vip_back":
        show_vip_menu(chat_id, uid, msg_id)
        return
    
    if data == "vip_buy":
        price = bot_config.get("vip_price_stars", 100)
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title="👑 VIP Membership",
                description=f"Get VIP for 30 days!\n\n✨ Benefits:\n• 2x Daily bonus\n• 15% discount\n• Weekly free code\n• Priority support",
                invoice_payload=f"vip_purchase_{uid}",
                provider_token="",
                currency="XTR",
                prices=[types.LabeledPrice(label="VIP Monthly", amount=price)]
            )
            bot.answer_callback_query(call.id, "💳 Payment invoice sent!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)
        return
    
    if data == "vip_convert_stars":
        show_stars_menu(chat_id, uid, msg_id)
        return
    
    if data == "vip_stock":
        show_vip_stock_details(chat_id, uid, msg_id)
        return
    
    if data == "vip_weekly_code":
        if not is_vip_active(uid):
            bot.answer_callback_query(call.id, "❌ VIP Only!", show_alert=True)
            return
        last_claims = bot_config.get("vip_last_weekly_code", {})
        last_claim = last_claims.get(uid)
        if last_claim:
            try:
                last_time = datetime.fromisoformat(last_claim)
                if (datetime.now() - last_time).days < 7:
                    days_left = 7 - (datetime.now() - last_time).days
                    bot.answer_callback_query(call.id, f"⏰ Come back in {days_left} days!", show_alert=True)
                    return
            except: pass
        reward = 50
        update_user_data(uid, points=reward, accumulated_points=reward)
        update_user_rank_and_quests(uid)
        if "vip_last_weekly_code" not in bot_config:
            bot_config["vip_last_weekly_code"] = {}
        bot_config["vip_last_weekly_code"][uid] = datetime.now().isoformat()
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, f"🎉 Weekly VIP bonus! +{reward} 💎", show_alert=True)
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("star_buy_"))
def handle_star_purchase(call):
    uid = str(call.from_user.id)
    stars = int(call.data.split("_")[2])
    rate = bot_config.get("star_to_points_rate", 2)
    points = stars * rate
    chat_id = call.message.chat.id
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title=f"⭐ {stars} = {points} 💎",
            description=f"Convert {stars} Stars to {points} points!\n\n⚡ Instant delivery",
            invoice_payload=f"stars_convert_{uid}_{stars}_{points}",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label=f"{stars} Stars", amount=stars)]
        )
        bot.answer_callback_query(call.id, "💳 Payment invoice sent!")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

# =====================================================
# TELEGRAM STARS PAYMENT HANDLERS
# =====================================================

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_handler(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        print(f"⚠️ Pre-checkout: {e}")

@bot.message_handler(content_types=['successful_payment'])
def payment_success_handler(message):
    uid = str(message.from_user.id)
    payment = message.successful_payment
    payload = payment.invoice_payload
    total_amount = payment.total_amount
    charge_id = getattr(payment, "telegram_payment_charge_id", None)
    
    if payload.startswith("vip_purchase_"):
        expires = activate_vip(uid, 30)
        bot.send_message(message.chat.id,
            f"╔═══════════════════════╗\n"
            f"║ 🎊 <b>VIP ACTIVATED!</b> 🎊 ║\n"
            f"╚═══════════════════════╝\n\n"
            f"👑 <b>Welcome to VIP!</b>\n\n"
            f"⏰ Valid until: {expires.strftime('%Y-%m-%d')}\n"
            f"💎 All benefits activated\n\n"
            f"✨ <i>Enjoy!</i>",
            parse_mode="HTML")
        # Every paid VIP purchase is announced in all added channels.
        publish_vip_purchase_to_channel(total_amount, charge_id)
        try:
            u = get_user(uid) or {}
            bot.send_message(ADMIN_PRIMARY,
                f"💰 <b>NEW VIP!</b>\n\n"
                f"👤 @{u.get('username', 'N/A')}\n"
                f"🆔 {uid}\n"
                f"⭐ Paid: {total_amount} stars",
                parse_mode="HTML")
        except: pass
    
    elif payload.startswith("stars_convert_"):
        parts = payload.split("_")
        stars = int(parts[2])
        points = int(parts[3])
        update_user_data(uid, points=points, accumulated_points=points)
        update_user_rank_and_quests(uid)
        u_new = get_user(uid) or {}
        bot.send_message(message.chat.id,
            f"╔═══════════════════════╗\n"
            f"║ 🎉 <b>DONE!</b> 🎉 ║\n"
            f"╚═══════════════════════╝\n\n"
            f"⭐ Stars used: <b>{stars}</b>\n"
            f"💎 Points: <b>+{points}</b>\n"
            f"💰 New balance: <b>{u_new.get('points', 0)}</b>",
            parse_mode="HTML")
        publish_stars_conversion_to_channel(stars, points, charge_id)
        try:
            u = get_user(uid) or {}
            bot.send_message(ADMIN_PRIMARY,
                f"⭐ <b>CONVERSION</b>\n@{u.get('username', 'N/A')}\n{uid}\n⭐ {stars} → 💎 {points}",
                parse_mode="HTML")
        except: pass

# =====================================================
# ADMIN VIP CALLBACKS
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_vip_") or call.data == "adm_manage_user")
def handle_admin_vip(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        bot.answer_callback_query(call.id, "❌ Admin only")
        return
    data = call.data
    chat_id = call.message.chat.id
    
    if data == "adm_vip_price":
        msg = bot.send_message(chat_id,
            f"💰 Current: {bot_config.get('vip_price_stars', 100)} ⭐\n\nSend new price:")
        bot.register_next_step_handler(msg, process_new_vip_price)
    
    elif data == "adm_vip_rate":
        msg = bot.send_message(chat_id,
            f"⭐ Current: 1 ⭐ = {bot_config.get('star_to_points_rate', 2)} 💎\n\nSend new rate:")
        bot.register_next_step_handler(msg, process_new_star_rate)
    
    elif data == "adm_vip_list":
        vips = bot_config.get("vip_subscribers", {})
        active_vips = {k: v for k, v in vips.items() if is_vip_active(k)}
        if not active_vips:
            bot.send_message(chat_id, "📭 No active VIPs")
            return
        msg = f"👑 <b>Active VIPs:</b> ({len(active_vips)})\n\n"
        for vuid, vdata in list(active_vips.items())[:20]:
            days = get_vip_days_left(vuid)
            u = get_user(vuid) or {}
            msg += f"• @{u.get('username', 'N/A')} ({vuid}) - {days}d\n"
        bot.send_message(chat_id, msg, parse_mode="HTML")
    
    elif data == "adm_vip_grant":
        msg = bot.send_message(chat_id, "Send: <code>USER_ID DAYS</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_vip_grant)
    
    elif data == "adm_vip_revoke":
        msg = bot.send_message(chat_id, "Send user ID to revoke VIP:")
        bot.register_next_step_handler(msg, process_vip_revoke)
    
    elif data == "adm_manage_user":
        msg = bot.send_message(chat_id, "Send user ID to manage:")
        bot.register_next_step_handler(msg, process_manage_user)

def process_new_vip_price(message):
    try:
        price = int(message.text.strip())
        if price > 0:
            bot_config["vip_price_stars"] = price
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ VIP price: {price} ⭐")
    except:
        bot.send_message(message.chat.id, "❌ Invalid")

def process_new_star_rate(message):
    try:
        rate = int(message.text.strip())
        if rate > 0:
            bot_config["star_to_points_rate"] = rate
            save_json(DB_CONFIG, bot_config)
            bot.send_message(message.chat.id, f"✅ Rate: 1 ⭐ = {rate} 💎")
    except:
        bot.send_message(message.chat.id, "❌ Invalid")

def process_vip_grant(message):
    try:
        parts = message.text.strip().split()
        target = parts[0]
        days = int(parts[1])
        if get_user(target):
            expires = activate_vip(target, days)
            bot.send_message(message.chat.id, f"✅ VIP granted to {target} for {days} days")
            try:
                bot.send_message(int(target),
                    f"🎉 <b>You received VIP!</b>\n\n👑 Duration: {days} days\n⏰ Until: {expires.strftime('%Y-%m-%d')}",
                    parse_mode="HTML")
            except: pass
    except:
        bot.send_message(message.chat.id, "❌ Format: ID DAYS")

def process_vip_revoke(message):
    target = message.text.strip()
    if deactivate_vip(target):
        bot.send_message(message.chat.id, f"✅ VIP revoked from {target}")
    else:
        bot.send_message(message.chat.id, "❌ User not VIP")

def process_manage_user(message):
    """Show user management panel with all options"""
    target = message.text.strip()
    u = get_user(target)
    if not u:
        bot.send_message(message.chat.id, "❌ User not found")
        return
    
    is_vip = is_vip_active(target)
    is_adm = u.get("is_admin", False)
    is_banned = u.get("banned", False)
    
    role = "👑 Owner" if int(target) == ADMIN_PRIMARY else ("🛡️ Admin" if is_adm else "👤 User")
    vip_status = f"👑 VIP ({get_vip_days_left(target)}d)" if is_vip else "❌ Not VIP"
    ban_status = "⛔ Banned" if is_banned else "🟢 Active"
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 👤 <b>USER MANAGEMENT</b> ║\n"
        f"╚═══════════════════════╝\n\n"
        f"🆔 ID: <code>{target}</code>\n"
        f"📝 @{u.get('username', 'N/A')}\n"
        f"💰 Balance: {u.get('points', 0)}\n"
        f"🎖️ Role: {role}\n"
        f"👑 VIP: {vip_status}\n"
        f"🔴 Status: {ban_status}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # VIP controls
    if is_vip:
        m.add(types.InlineKeyboardButton("❌ Remove VIP", callback_data=f"userctrl_removevip_{target}"))
    else:
        m.add(types.InlineKeyboardButton("👑 Grant VIP (30d)", callback_data=f"userctrl_grantvip_{target}"))
    
    # Admin controls
    if is_adm and int(target) != ADMIN_PRIMARY:
        m.add(types.InlineKeyboardButton("⬇️ Remove Admin", callback_data=f"userctrl_removeadmin_{target}"))
    elif not is_adm:
        m.add(types.InlineKeyboardButton("🛡️ Make Admin", callback_data=f"userctrl_makeadmin_{target}"))
    
    # Ban controls
    if is_banned:
        m.add(types.InlineKeyboardButton("🟢 Unban", callback_data=f"userctrl_unban_{target}"))
    else:
        m.add(
            types.InlineKeyboardButton("⛔ Ban Permanent", callback_data=f"userctrl_banperm_{target}"),
            types.InlineKeyboardButton("⏱️ Ban 24h", callback_data=f"userctrl_bantemp_{target}")
        )
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("userctrl_"))
def handle_user_control(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        return
    
    parts = call.data.split("_")
    action = parts[1]
    target = parts[2]
    
    if action == "grantvip":
        activate_vip(target, 30)
        bot.answer_callback_query(call.id, "✅ VIP granted!", show_alert=True)
        try:
            bot.send_message(int(target), "🎊 <b>You received VIP for 30 days!</b>", parse_mode="HTML")
        except: pass
    
    elif action == "removevip":
        deactivate_vip(target)
        bot.answer_callback_query(call.id, "✅ VIP removed!", show_alert=True)
    
    elif action == "makeadmin":
        update_user_data(target, is_admin=True)
        bot.answer_callback_query(call.id, "✅ Made admin!", show_alert=True)
        try:
            bot.send_message(int(target), "🛡️ <b>You're now an Admin!</b>", parse_mode="HTML")
        except: pass
    
    elif action == "removeadmin":
        update_user_data(target, is_admin=False)
        bot.answer_callback_query(call.id, "✅ Removed admin!", show_alert=True)
    
    elif action == "banperm":
        update_user_data(target, banned=True)
        bot.answer_callback_query(call.id, "⛔ Banned permanently!", show_alert=True)
    
    elif action == "bantemp":
        until = (datetime.now() + timedelta(days=1)).isoformat()
        update_user_data(target, banned_until=until)
        bot.answer_callback_query(call.id, "⏱️ Banned for 24h!", show_alert=True)
    
    elif action == "unban":
        update_user_data(target, banned=False, banned_until=None)
        bot.answer_callback_query(call.id, "🟢 Unbanned!", show_alert=True)

# =====================================================
# ADMIN RESTOCK CALLBACKS
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_restock_"))
def handle_admin_restock(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        return
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "adm_restock_new":
        if not prices_config:
            bot.send_message(chat_id, "❌ No products first!")
            return
        m = types.InlineKeyboardMarkup()
        for p in prices_config.keys():
            m.add(types.InlineKeyboardButton(f"📦 {p}", callback_data=f"rsprod_{p}"))
        try:
            bot.edit_message_text("📦 <b>Select product:</b>",
                chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
    
    elif data == "adm_restock_list":
        pending = get_pending_restocks()
        if not pending:
            bot.send_message(chat_id, "📭 No pending restocks")
            return
        msg = f"📦 <b>Pending Restocks:</b> ({len(pending)})\n\n"
        for rid, cfg in pending.items():
            try:
                sched = datetime.fromisoformat(cfg["scheduled_at"])
                diff = sched - datetime.now()
                if diff.total_seconds() > 0:
                    hrs = int(diff.total_seconds() // 3600)
                    mins = int((diff.total_seconds() % 3600) // 60)
                    msg += f"🆔 <code>{rid}</code>\n"
                    msg += f"📦 {cfg['product']}/{cfg['plan']}\n"
                    msg += f"🔑 {len(cfg['keys'])} keys\n"
                    msg += f"⏰ In: {hrs}h {mins}m\n\n"
            except: pass
        bot.send_message(chat_id, msg, parse_mode="HTML")
    
    elif data == "adm_restock_cancel":
        pending = get_pending_restocks()
        if not pending:
            bot.send_message(chat_id, "📭 No pending")
            return
        m = types.InlineKeyboardMarkup()
        for rid, cfg in pending.items():
            m.add(types.InlineKeyboardButton(
                f"❌ {rid} - {cfg['product']}/{cfg['plan']}",
                callback_data=f"rscancel_{rid}"))
        bot.send_message(chat_id, "Choose to cancel:", reply_markup=m)
    
    elif data == "adm_restock_history":
        history = bot_config.get("restock_history", [])
        if not history:
            bot.send_message(chat_id, "📭 No history")
            return
        msg = "📜 <b>Restock History (last 10):</b>\n\n"
        for h in history[-10:]:
            msg += f"• {h['product']}/{h['plan']}: +{h['qty']} @ {h.get('executed_at', '')[:16]}\n"
        bot.send_message(chat_id, msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsprod_"))
def handle_restock_product(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        return
    prod = call.data.split("_", 1)[1]
    m = types.InlineKeyboardMarkup()
    for plan in ["1 Day", "7 Days", "30 Days"]:
        m.add(types.InlineKeyboardButton(f"⏱️ {plan}", callback_data=f"rsplan_{prod}|{plan}"))
    try:
        bot.edit_message_text(f"📦 <b>{prod}</b>\n\n⏱️ Select plan:",
            call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsplan_"))
def handle_restock_plan(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        return
    prod, plan = call.data.split("_", 1)[1].split("|")
    
    # Store temporary
    temp_restock_setup[uid] = {"product": prod, "plan": plan, "step": "keys"}
    
    try:
        bot.edit_message_text(
            f"📦 <b>{prod} / {plan}</b>\n\n"
            f"✍️ <b>Send the keys</b> (one per line):\n\n"
            f"Example:\n"
            f"<code>KEY-ABC-123\n"
            f"KEY-DEF-456\n"
            f"KEY-GHI-789</code>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except: pass
    
    msg = bot.send_message(call.message.chat.id, "🔑 Send keys now:")
    bot.register_next_step_handler(msg, process_restock_keys)

def process_restock_keys(message):
    uid = str(message.from_user.id)
    if uid not in temp_restock_setup:
        return
    
    keys = [k.strip() for k in message.text.strip().split('\n') if k.strip()]
    if not keys:
        bot.send_message(message.chat.id, "❌ No keys provided")
        del temp_restock_setup[uid]
        return
    
    temp_restock_setup[uid]["keys"] = keys
    temp_restock_setup[uid]["step"] = "hours"
    
    # Show hours menu
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1h", callback_data="rshr_1"),
        types.InlineKeyboardButton("3h", callback_data="rshr_3"),
        types.InlineKeyboardButton("6h", callback_data="rshr_6")
    )
    m.add(
        types.InlineKeyboardButton("12h", callback_data="rshr_12"),
        types.InlineKeyboardButton("24h", callback_data="rshr_24"),
        types.InlineKeyboardButton("48h", callback_data="rshr_48")
    )
    m.add(
        types.InlineKeyboardButton("72h", callback_data="rshr_72"),
        types.InlineKeyboardButton("168h (7d)", callback_data="rshr_168"),
        types.InlineKeyboardButton("✏️ Custom", callback_data="rshr_custom")
    )
    
    bot.send_message(message.chat.id,
        f"✅ <b>{len(keys)} keys received!</b>\n\n"
        f"⏰ <b>When should they be added to stock?</b>",
        reply_markup=m, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rshr_"))
def handle_restock_hours(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        return
    if uid not in temp_restock_setup:
        bot.answer_callback_query(call.id, "❌ Session expired")
        return
    
    val = call.data.split("_")[1]
    
    if val == "custom":
        msg = bot.send_message(call.message.chat.id, "⏰ Send hours (number):")
        bot.register_next_step_handler(msg, process_custom_hours)
        return
    
    hours = int(val)
    setup = temp_restock_setup[uid]
    prod = setup["product"]
    plan = setup["plan"]
    keys = setup["keys"]
    
    restock_id, scheduled_time = create_pending_restock(prod, plan, keys, hours)
    del temp_restock_setup[uid]
    
    try:
        bot.edit_message_text(
            f"╔═══════════════════════╗\n"
            f"║ ✅ <b>RESTOCK SCHEDULED!</b> ║\n"
            f"╚═══════════════════════╝\n\n"
            f"🆔 <b>ID:</b> <code>{restock_id}</code>\n"
            f"📦 <b>Product:</b> {prod}\n"
            f"⏱️ <b>Plan:</b> {plan}\n"
            f"🔑 <b>Keys:</b> {len(keys)}\n"
            f"⏰ <b>Adds in:</b> {hours}h\n"
            f"📅 <b>At:</b> {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"✨ <i>Keys will be added automatically!</i>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except: pass

def process_custom_hours(message):
    uid = str(message.from_user.id)
    if uid not in temp_restock_setup:
        return
    try:
        hours = int(message.text.strip())
        if hours <= 0:
            raise ValueError
        setup = temp_restock_setup[uid]
        prod = setup["product"]
        plan = setup["plan"]
        keys = setup["keys"]
        restock_id, scheduled_time = create_pending_restock(prod, plan, keys, hours)
        del temp_restock_setup[uid]
        bot.send_message(message.chat.id,
            f"✅ <b>Scheduled!</b>\n\n"
            f"🆔 {restock_id}\n"
            f"📦 {prod}/{plan}\n"
            f"🔑 {len(keys)} keys\n"
            f"⏰ In {hours}h",
            parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ Invalid hours")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rscancel_"))
def handle_restock_cancel(call):
    uid = str(call.from_user.id)
    if not is_admin_user(uid):
        return
    rid = call.data.split("_")[1]
    if cancel_pending_restock(rid):
        bot.answer_callback_query(call.id, f"✅ Cancelled {rid}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ Not found", show_alert=True)

print("=" * 50)
print("✅ bot2.py v2.1 loaded!")
print("👑 VIP System: Ready")
print("⭐ Stars Payment: Ready")
print("📦 Auto-Restock: Running")
print("👤 User Management: Ready")

# =====================================================
# 🎁 GIVEAWAY ADMIN STUDIO (inserted)
# =====================================================

# =====================================================
# 🎁 GIVEAWAY ADMIN STUDIO  —  Professional Panel v2.0
# =====================================================
# A complete English admin dashboard for running giveaways that grow the
# channel. Self-contained inside bot2.py. Intercepted BEFORE bot.py's main
# router because bot2 is imported first, so the classic "🎁 Giveaway" admin
# button now opens this studio.
# =====================================================

gw2_setup = {}   # uid -> in-progress creation state


def _gw2_is_admin(uid):
    try:
        if int(uid) in (ADMIN_PRIMARY, ADMIN_SECONDARY):
            return True
    except Exception:
        pass
    u = get_user(str(uid)) or {}
    return u.get("is_admin", False)


def _edit_or_send(chat_id, msg_id, text, kb=None):
    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")


def _back_kb():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🏠 Dashboard", callback_data="gw2_home"))
    return m


# ---------- Dashboard ----------

def _gw2_dashboard_text():
    s = get_giveaways_stats()
    live = "🟢 ON" if bot_config.get("gw_live_reports", True) else "🔴 OFF"
    return (
        "╔═══════════════════════╗\n"
        "║  🎁 <b>GIVEAWAY STUDIO</b> 🎁  ║\n"
        "╚═══════════════════════╝\n\n"
        "<i>Your professional suite for running giveaways that grow the channel.</i>\n\n"
        "📊 <b>Overall Performance</b>\n"
        f"├ 🗂 Total campaigns: <b>{s['total']}</b>\n"
        f"├ ⚡ Active now: <b>{s['active']}</b>\n"
        f"├ ⏳ Pending milestone: <b>{s['waiting']}</b>\n"
        f"├ 🏆 Winners crowned: <b>{s['total_winners']}</b>\n"
        f"├ 👥 Members engaged: <b>{s['total_entrants'] + s['total_claimed']}</b>\n"
        f"└ 💎 Points distributed: <b>{s['total_points_given']}</b>\n\n"
        f"🔔 Live admin reports: <b>{live}</b>"
    )


def _gw2_dashboard_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("➕ New Giveaway", callback_data="gw2_create"))
    m.add(types.InlineKeyboardButton("📋 Manage Campaigns", callback_data="gw2_list"))
    m.add(types.InlineKeyboardButton("📊 Detailed Stats", callback_data="gw2_stats"))
    m.add(types.InlineKeyboardButton("💡 Growth Ideas", callback_data="gw2_ideas"))
    rep = "🔔 Live Reports: ON" if bot_config.get("gw_live_reports", True) else "🔕 Live Reports: OFF"
    m.add(types.InlineKeyboardButton(rep, callback_data="gw2_reports"))
    m.add(types.InlineKeyboardButton("ℹ️ Help", callback_data="gw2_help"))
    return m


def gw2_open_dashboard(chat_id, msg_id=None):
    _edit_or_send(chat_id, msg_id, _gw2_dashboard_text(), _gw2_dashboard_kb())


# ---------- Entry: intercept the "🎁 Giveaway" admin button ----------

@bot.message_handler(func=lambda m: m.text == "🎁 Giveaway")
def gw2_entry_button(message):
    uid = str(message.from_user.id)
    if not _gw2_is_admin(uid):
        return bot.send_message(message.chat.id, "🔒 <b>Admins only.</b>", parse_mode="HTML")
    gw2_open_dashboard(message.chat.id)


# ---------- Entry: deep-link for NEW giveaway types (draw/react/quiz) ----------

def _gw2_start_param(message):
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2 and parts[1].startswith("gw_"):
            return parts[1][3:]
    except Exception:
        pass
    return None


def _gw2_is_entry_type(message):
    if not (message.text or "").startswith("/start"):
        return False
    code = _gw2_start_param(message)
    if not code:
        return False
    gw = get_giveaway(code)
    if not gw:
        return False
    return gw.get("type", "link") in ("draw", "react", "quiz") and gw.get("status") == "active"


@bot.message_handler(func=lambda m: _gw2_is_entry_type(m))
def gw2_entry_start(message):
    code = _gw2_start_param(message)
    uid = str(message.from_user.id)
    gw = get_giveaway(code)
    gtype = gw.get("type")
    chat_id = message.chat.id

    if not check_channel_join(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        return bot.send_message(chat_id,
            "🔒 <b>You must join our channel to enter the giveaway!</b>\n\n"
            "Join, then open the link again.",
            reply_markup=kb, parse_mode="HTML")

    if has_user_entered(code, uid):
        return bot.send_message(chat_id, "✅ <b>You're already entered!</b> Good luck 🍀",
                                parse_mode="HTML")

    if gtype == "quiz":
        return _gw2_send_quiz(chat_id, uid, code)

    # draw / react -> enter directly (react assumes the member reacted on the post)
    enter_giveaway(code, uid)
    update_channel_post(code)
    if bot_config.get("gw_live_reports", True):
        u = get_user(uid) or {}
        _notify_admins(
            "🙋 <b>New Giveaway Entry</b>\n"
            f"├ Code: <code>{code}</code> ({gtype})\n"
            f"├ User: @{_esc(u.get('username', 'N/A'))} (<code>{uid}</code>)\n"
            f"└ Entrants: {len(gw.get('entrants', []))}/{gw.get('max_users', 0)}"
        )
    bot.send_message(chat_id,
        "🎉 <b>You're in the draw!</b>\n\n"
        f"💎 Prize: <b>{gw.get('reward', 0)} pts</b> each\n"
        f"🏆 Winners: <b>{gw.get('max_users', 0)}</b>\n"
        f"⏰ Results in: <b>{_time_left_text(gw)}</b>\n\n"
        f"🍀 Good luck! Winners get a DM and their points automatically.",
        parse_mode="HTML")


def _gw2_send_quiz(chat_id, uid, code):
    gw = get_giveaway(code)
    opts = gw.get("quiz_options", [])
    m = types.InlineKeyboardMarkup(row_width=1)
    for i, o in enumerate(opts):
        m.add(types.InlineKeyboardButton(_esc(o), callback_data=f"gw2q_{code}_{i}"))
    bot.send_message(chat_id,
        f"🧠 <b>QUIZ GIVEAWAY</b>\n\n❓ {_esc(gw.get('quiz_question', ''))}\n\n"
        f"💎 Prize: <b>{gw.get('reward', 0)} pts</b> each · 🏆 {gw.get('max_users', 0)} winners\n\n"
        f"Pick the correct answer to enter:",
        reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data.startswith("gw2q_"))
def gw2_quiz_answer(call):
    uid = str(call.from_user.id)
    try:
        _, code, idx_s = call.data.split("_")
        idx = int(idx_s)
    except Exception:
        return bot.answer_callback_query(call.id, "Invalid", show_alert=True)
    gw = get_giveaway(code)
    chat_id = call.message.chat.id
    if not gw or gw.get("status") != "active":
        return bot.answer_callback_query(call.id, "⏰ This giveaway has ended.", show_alert=True)
    if has_user_entered(code, uid):
        return bot.answer_callback_query(call.id, "✅ Already entered!", show_alert=True)
    if idx == gw.get("quiz_answer", -1):
        enter_giveaway(code, uid)
        update_channel_post(code)
        if bot_config.get("gw_live_reports", True):
            u = get_user(uid) or {}
            _notify_admins(
                "🧠 <b>Quiz Entry (correct)</b>\n"
                f"├ Code: <code>{code}</code>\n"
                f"├ User: @{_esc(u.get('username', 'N/A'))} (<code>{uid}</code>)\n"
                f"└ Entrants: {len(gw.get('entrants', []))}"
            )
        bot.answer_callback_query(call.id, "✅ Correct! You're in the draw 🍀", show_alert=True)
        bot.send_message(chat_id,
            "🎉 <b>Correct answer — you're in!</b>\n\n"
            f"💎 Prize: <b>{gw.get('reward', 0)} pts</b> each · 🏆 {gw.get('max_users', 0)} winners\n"
            f"⏰ Results in: <b>{_time_left_text(gw)}</b>\n\n🍀 Good luck!",
            parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "❌ Wrong answer — better luck next time!", show_alert=True)


# ---------- Type chooser ----------

def gw2_show_types(chat_id, msg_id=None):
    text = (
        "╔═══════════════════════╗\n"
        "║  ➕ <b>NEW GIVEAWAY</b>  ║\n"
        "╚═══════════════════════╝\n\n"
        "Pick a campaign type — each one boosts a different part of your channel:\n"
    )
    for key, meta in GW_TYPES.items():
        text += f"\n{meta['label']}\n<i>{meta['desc']}</i>\n"
    m = types.InlineKeyboardMarkup(row_width=1)
    for key, meta in GW_TYPES.items():
        m.add(types.InlineKeyboardButton(meta['label'], callback_data=f"gw2_type_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="gw2_home"))
    _edit_or_send(chat_id, msg_id, text, m)


def gw2_begin_type(call, gtype):
    uid = str(call.from_user.id)
    chat_id = call.message.chat.id
    gw2_setup[uid] = {"type": gtype}
    bot.answer_callback_query(call.id)
    if gtype == "milestone":
        msg = bot.send_message(chat_id,
            "📈 <b>Step 1 — Subscriber Goal</b>\n\n"
            "At how many channel subscribers should the reward drop be published?\n\n"
            "<i>Send a number, e.g. 1000</i>", parse_mode="HTML")
        bot.register_next_step_handler(msg, _gw2_recv_milestone_target)
    elif gtype == "quiz":
        msg = bot.send_message(chat_id,
            "🧠 <b>Step 1 — Quiz Question</b>\n\n"
            "Send the question you want members to answer.\n\n"
            "<i>Example: What year did our store launch?</i>", parse_mode="HTML")
        bot.register_next_step_handler(msg, _gw2_recv_quiz_question)
    else:
        _gw2_ask_reward(chat_id, uid)


# ---------- Text input receivers ----------

def _gw2_recv_milestone_target(message):
    uid = str(message.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return
    try:
        target = int((message.text or "").strip())
        if target <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "❌ Please send a valid positive number:")
        bot.register_next_step_handler(msg, _gw2_recv_milestone_target)
        return
    st["milestone_target"] = target
    _gw2_ask_reward(message.chat.id, uid)


def _gw2_recv_quiz_question(message):
    uid = str(message.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return
    q = (message.text or "").strip()
    if not q:
        msg = bot.send_message(message.chat.id, "❌ Question can't be empty. Send it again:")
        bot.register_next_step_handler(msg, _gw2_recv_quiz_question)
        return
    st["quiz_question"] = q
    msg = bot.send_message(message.chat.id,
        "🧠 <b>Step 2 — Answer Options</b>\n\n"
        "Send 2–4 options separated by commas.\n\n"
        "<i>Example: 2021, 2022, 2023, 2024</i>", parse_mode="HTML")
    bot.register_next_step_handler(msg, _gw2_recv_quiz_options)


def _gw2_recv_quiz_options(message):
    uid = str(message.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return
    raw = (message.text or "").strip()
    opts = [o.strip() for o in raw.split(",") if o.strip()]
    if len(opts) < 2 or len(opts) > 4:
        msg = bot.send_message(message.chat.id, "❌ Send between 2 and 4 options separated by commas:")
        bot.register_next_step_handler(msg, _gw2_recv_quiz_options)
        return
    st["quiz_options"] = opts
    m = types.InlineKeyboardMarkup(row_width=1)
    for i, o in enumerate(opts):
        m.add(types.InlineKeyboardButton(f"✅ {_esc(o)}", callback_data=f"gw2_quizans_{i}"))
    bot.send_message(message.chat.id,
        "🎯 <b>Step 3 — Correct Answer</b>\n\nTap the correct option:",
        reply_markup=m, parse_mode="HTML")


def gw2_set_quiz_answer(call, idx):
    uid = str(call.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return bot.answer_callback_query(call.id, "Session expired", show_alert=True)
    st["quiz_answer"] = idx
    bot.answer_callback_query(call.id, f"Correct answer set: {st['quiz_options'][idx]}")
    _gw2_ask_reward(call.message.chat.id, uid)


# ---------- Numeric step menus ----------

def _gw2_ask_reward(chat_id, uid):
    m = types.InlineKeyboardMarkup(row_width=3)
    for v in [25, 50, 100, 250, 500, 1000]:
        m.add(types.InlineKeyboardButton(f"💎 {v}", callback_data=f"gw2_reward_{v}"))
    m.add(types.InlineKeyboardButton("✏️ Custom", callback_data="gw2_reward_custom"),
          types.InlineKeyboardButton("❌ Cancel", callback_data="gw2_abort"))
    bot.send_message(chat_id,
        "💎 <b>Step — Reward</b>\n\nPoints awarded to each winner:",
        reply_markup=m, parse_mode="HTML")


def gw2_set_reward(call, val):
    uid = str(call.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return bot.answer_callback_query(call.id, "Session expired", show_alert=True)
    if val == "custom":
        msg = bot.send_message(call.message.chat.id, "💎 Send reward amount (number):")
        bot.register_next_step_handler(msg, _gw2_recv_reward)
        return
    st["reward"] = int(val)
    bot.answer_callback_query(call.id)
    _gw2_ask_winners(call.message.chat.id, uid)


def _gw2_recv_reward(message):
    uid = str(message.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return
    try:
        v = int((message.text or "").strip())
        if v <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "❌ Send a valid positive number:")
        bot.register_next_step_handler(msg, _gw2_recv_reward)
        return
    st["reward"] = v
    _gw2_ask_winners(message.chat.id, uid)


def _gw2_ask_winners(chat_id, uid):
    m = types.InlineKeyboardMarkup(row_width=3)
    for v in [1, 3, 5, 10, 20, 50]:
        m.add(types.InlineKeyboardButton(f"👥 {v}", callback_data=f"gw2_winners_{v}"))
    m.add(types.InlineKeyboardButton("✏️ Custom", callback_data="gw2_winners_custom"),
          types.InlineKeyboardButton("❌ Cancel", callback_data="gw2_abort"))
    bot.send_message(chat_id,
        "👥 <b>Step — Winners</b>\n\nHow many winners / claim slots?",
        reply_markup=m, parse_mode="HTML")


def gw2_set_winners(call, val):
    uid = str(call.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return bot.answer_callback_query(call.id, "Session expired", show_alert=True)
    if val == "custom":
        msg = bot.send_message(call.message.chat.id, "👥 Send number of winners:")
        bot.register_next_step_handler(msg, _gw2_recv_winners)
        return
    st["max_users"] = int(val)
    bot.answer_callback_query(call.id)
    _gw2_ask_hours(call.message.chat.id, uid)


def _gw2_recv_winners(message):
    uid = str(message.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return
    try:
        v = int((message.text or "").strip())
        if v <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "❌ Send a valid positive number:")
        bot.register_next_step_handler(msg, _gw2_recv_winners)
        return
    st["max_users"] = v
    _gw2_ask_hours(message.chat.id, uid)


def _gw2_ask_hours(chat_id, uid):
    m = types.InlineKeyboardMarkup(row_width=3)
    for v in [1, 3, 6, 12, 24, 48]:
        m.add(types.InlineKeyboardButton(f"⏰ {v}h", callback_data=f"gw2_hours_{v}"))
    m.add(types.InlineKeyboardButton("📅 72h", callback_data="gw2_hours_72"),
          types.InlineKeyboardButton("🗓 168h", callback_data="gw2_hours_168"))
    m.add(types.InlineKeyboardButton("✏️ Custom", callback_data="gw2_hours_custom"),
          types.InlineKeyboardButton("❌ Cancel", callback_data="gw2_abort"))
    bot.send_message(chat_id,
        "⏰ <b>Step — Duration</b>\n\nHow long should the campaign run?",
        reply_markup=m, parse_mode="HTML")


def gw2_set_hours(call, val):
    uid = str(call.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return bot.answer_callback_query(call.id, "Session expired", show_alert=True)
    if val == "custom":
        msg = bot.send_message(call.message.chat.id, "⏰ Send duration in hours (number):")
        bot.register_next_step_handler(msg, _gw2_recv_hours)
        return
    st["hours"] = int(val)
    bot.answer_callback_query(call.id)
    _gw2_confirm(call.message.chat.id, uid)


def _gw2_recv_hours(message):
    uid = str(message.from_user.id)
    st = gw2_setup.get(uid)
    if not st:
        return
    try:
        v = int((message.text or "").strip())
        if v <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "❌ Send a valid positive number:")
        bot.register_next_step_handler(msg, _gw2_recv_hours)
        return
    st["hours"] = v
    _gw2_confirm(message.chat.id, uid)


# ---------- Review & launch ----------

def _gw2_confirm(chat_id, uid):
    st = gw2_setup.get(uid)
    if not st:
        return
    gtype = st["type"]
    meta = GW_TYPES[gtype]
    lines = [
        "╔═══════════════════════╗",
        "║  ✅ <b>REVIEW &amp; LAUNCH</b>  ║",
        "╚═══════════════════════╝", "",
        f"🎯 Type: <b>{meta['label']}</b>",
        f"💎 Reward: <b>{st['reward']} pts</b> each",
        f"👥 Winners: <b>{st['max_users']}</b>",
        f"⏰ Duration: <b>{st['hours']}h</b>",
    ]
    if gtype == "quiz":
        opts = st.get('quiz_options', ['?'])
        ans = opts[st.get('quiz_answer', 0)] if st.get('quiz_answer', 0) < len(opts) else '?'
        lines.append(f"🧠 Question: <b>{_esc(st.get('quiz_question', ''))}</b>")
        lines.append(f"🎯 Correct: <b>{_esc(ans)}</b>")
    if gtype == "milestone":
        lines.append(f"📈 Publishes at: <b>{st.get('milestone_target', 0)} subscribers</b>")
    lines += ["", "Launch this campaign now?"]
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🚀 Launch Now", callback_data="gw2_launch"),
          types.InlineKeyboardButton("❌ Cancel", callback_data="gw2_abort"))
    bot.send_message(chat_id, "\n".join(lines), reply_markup=m, parse_mode="HTML")


def gw2_launch(call):
    uid = str(call.from_user.id)
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    st = gw2_setup.get(uid)
    if not st:
        return bot.answer_callback_query(call.id, "Session expired", show_alert=True)
    gtype = st["type"]
    extra = {}
    if gtype == "quiz":
        extra = {"quiz_question": st.get("quiz_question", ""),
                 "quiz_options": st.get("quiz_options", []),
                 "quiz_answer": st.get("quiz_answer", 0)}
    if gtype == "milestone":
        extra = {"milestone_target": st.get("milestone_target", 0)}
    code = create_giveaway(st["reward"], st["max_users"], st["hours"],
                           gw_type=gtype, created_by=uid, **extra)
    gw2_setup.pop(uid, None)

    published = None
    if gtype != "milestone":
        published = publish_giveaway_to_channel(code)

    bot_user = _bot_username()
    link = f"https://t.me/{bot_user}?start=gw_{code}"
    summary = (
        "╔═══════════════════════╗\n"
        "║ 🎉 <b>CAMPAIGN LAUNCHED!</b> 🎉 ║\n"
        "╚═══════════════════════╝\n\n"
        f"🆔 Code: <code>{code}</code>\n"
        f"🎯 Type: <b>{GW_TYPES[gtype]['label']}</b>\n"
        f"💎 Reward: <b>{st['reward']} pts</b> × {st['max_users']}\n"
        f"⏰ Duration: <b>{st['hours']}h</b>\n"
    )
    if gtype == "milestone":
        summary += f"📈 <b>Waiting</b> for {st.get('milestone_target', 0)} subscribers — I'll auto-publish the drop!\n"
    else:
        summary += ("📢 <b>Published to channel!</b>\n" if published
                    else "⚠️ Could not publish (check the bot is a channel admin).\n")
        summary += f"🔗 Link: <code>{link}</code>\n"
    summary += "\n💡 Track it anytime from <b>Manage Campaigns</b>."

    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📋 Manage Campaigns", callback_data="gw2_list"),
          types.InlineKeyboardButton("🏠 Dashboard", callback_data="gw2_home"))
    _edit_or_send(chat_id, msg_id, summary, m)


# ---------- Manage / list / detail ----------

def gw2_show_list(chat_id, msg_id=None):
    gws = get_all_giveaways()
    if not gws:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Create your first", callback_data="gw2_create"),
              types.InlineKeyboardButton("🏠 Dashboard", callback_data="gw2_home"))
        _edit_or_send(chat_id, msg_id,
                      "📭 <b>No campaigns yet.</b>\n\nLaunch your first giveaway to start growing!", m)
        return
    status_icon = {"active": "🟢", "waiting": "⏳", "expired": "⏰",
                   "full": "✅", "completed": "🏆", "cancelled": "🗑"}
    items = sorted(gws.values(), key=lambda g: g.get("created", ""), reverse=True)
    text = (
        "╔═══════════════════════╗\n"
        "║  📋 <b>MANAGE CAMPAIGNS</b>  ║\n"
        "╚═══════════════════════╝\n\n"
        f"Total: <b>{len(items)}</b> — tap one for full details & controls.\n"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    for g in items[:15]:
        code = g["code"]
        icon = status_icon.get(g.get("status", "active"), "•")
        meta = GW_TYPES.get(g.get("type", "link"), {})
        m.add(types.InlineKeyboardButton(
            f"{icon} {code} · {meta.get('short', '?')} · {g.get('status', '?')}",
            callback_data=f"gw2_view_{code}"))
    m.add(types.InlineKeyboardButton("🏠 Dashboard", callback_data="gw2_home"))
    _edit_or_send(chat_id, msg_id, text, m)


def gw2_show_detail(chat_id, msg_id, code):
    gw = get_giveaway(code)
    if not gw:
        _edit_or_send(chat_id, msg_id, "❌ Campaign not found.", _back_kb())
        return
    meta = GW_TYPES.get(gw.get("type", "link"), {})
    s_icon = {"active": "🟢 Active", "waiting": "⏳ Waiting (milestone)", "expired": "⏰ Expired",
              "full": "✅ Full", "completed": "🏆 Completed", "cancelled": "🗑 Cancelled"}
    claimed = len(gw.get("claimed_by", []))
    entrants = len(gw.get("entrants", []))
    winners = gw.get("winners", [])
    text = (
        "╔═══════════════════════╗\n"
        f"║  🎁 <b>CAMPAIGN {code}</b>  ║\n"
        "╚═══════════════════════╝\n\n"
        f"🎯 Type: <b>{meta.get('label', '?')}</b>\n"
        f"📡 Status: <b>{s_icon.get(gw.get('status', 'active'), gw.get('status'))}</b>\n"
        f"💎 Reward: <b>{gw.get('reward', 0)} pts</b> each\n"
        f"👥 Slots: <b>{gw.get('max_users', 0)}</b>\n"
        f"⏰ Duration: <b>{gw.get('hours', 0)}h</b>\n"
        f"⌛ Time left: <b>{_time_left_text(gw)}</b>\n"
        f"🗓 Created: <code>{str(gw.get('created', ''))[:16].replace('T', ' ')}</code>\n"
    )
    if gw.get("type") in ("draw", "react", "quiz"):
        text += f"🙋 Entrants: <b>{entrants}</b>\n"
    if gw.get("type") in ("link", "milestone"):
        text += f"✅ Claimed: <b>{claimed}/{gw.get('max_users', 0)}</b>\n"
    if gw.get("type") == "quiz":
        text += f"🧠 Q: <i>{_esc(gw.get('quiz_question', ''))}</i>\n"
    if gw.get("type") == "milestone":
        cur = get_channel_member_count()
        text += f"📈 Subscribers: <b>{cur}/{gw.get('milestone_target', 0)}</b>\n"
    if winners:
        wlines = []
        for w in winners[:10]:
            u = get_user(str(w)) or {}
            wlines.append(f"@{_esc(u.get('username', 'N/A'))}")
        text += f"\n🏆 <b>Winners:</b> {', '.join(wlines)}\n"
    text += f"\n💎 Points committed: <b>{gw.get('reward', 0) * max(len(winners), claimed)}</b>"

    m = types.InlineKeyboardMarkup(row_width=2)
    status = gw.get("status")
    if not gw.get("published") and status == "active" and gw.get("type") != "milestone":
        m.add(types.InlineKeyboardButton("📢 Publish to Channel", callback_data=f"gw2_pub_{code}"))
    if status == "active":
        m.add(types.InlineKeyboardButton("🔁 Re-post", callback_data=f"gw2_repost_{code}"))
        if gw.get("type") in ("draw", "react", "quiz"):
            m.add(types.InlineKeyboardButton("🏁 End & Pick Winners", callback_data=f"gw2_end_{code}"))
        m.add(types.InlineKeyboardButton("🗑 Cancel", callback_data=f"gw2_cancel_{code}"))
    elif status == "waiting":
        m.add(types.InlineKeyboardButton("🗑 Cancel", callback_data=f"gw2_cancel_{code}"))
    m.add(types.InlineKeyboardButton("🔄 Refresh", callback_data=f"gw2_view_{code}"),
          types.InlineKeyboardButton("🔙 List", callback_data="gw2_list"))
    _edit_or_send(chat_id, msg_id, text, m)


def gw2_finish_now(call, code):
    gw = get_giveaway(code)
    if not gw:
        return bot.answer_callback_query(call.id, "Not found", show_alert=True)
    winners = pick_winners(code)
    update_channel_post(code)
    _announce_winners(code, winners)
    bot.answer_callback_query(call.id, f"🏆 Picked {len(winners)} winner(s)!", show_alert=True)
    gw2_show_detail(call.message.chat.id, call.message.message_id, code)


# ---------- Stats / ideas / help ----------

def gw2_show_stats(chat_id, msg_id=None):
    s = get_giveaways_stats()
    bt = s["by_type"]
    text = (
        "╔═══════════════════════╗\n"
        "║  📊 <b>DETAILED STATS</b>  ║\n"
        "╚═══════════════════════╝\n\n"
        "🗂 <b>Campaigns</b>\n"
        f"├ Total: <b>{s['total']}</b>\n"
        f"├ Active: <b>{s['active']}</b>\n"
        f"├ Waiting (milestone): <b>{s['waiting']}</b>\n"
        f"├ Completed: <b>{s['completed']}</b>\n"
        f"├ Expired: <b>{s['expired']}</b>\n"
        f"└ Cancelled: <b>{s['cancelled']}</b>\n\n"
        "👥 <b>Engagement</b>\n"
        f"├ Members engaged: <b>{s['total_entrants'] + s['total_claimed']}</b>\n"
        f"├ Winners crowned: <b>{s['total_winners']}</b>\n"
        f"└ Points distributed: <b>{s['total_points_given']}</b>\n\n"
        "🎯 <b>By Type</b>\n"
    )
    if bt:
        for k, v in bt.items():
            text += f"├ {GW_TYPES.get(k, {}).get('short', k)}: <b>{v}</b>\n"
    else:
        text += "└ <i>No data yet</i>\n"
    text += f"\n📣 Current channel subscribers: <b>{get_channel_member_count()}</b>"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="gw2_stats"),
          types.InlineKeyboardButton("🏠 Dashboard", callback_data="gw2_home"))
    _edit_or_send(chat_id, msg_id, text, m)


def gw2_show_ideas(chat_id, msg_id=None):
    text = (
        "╔═══════════════════════╗\n"
        "║  💡 <b>GROWTH IDEAS</b>  ║\n"
        "╚═══════════════════════╝\n\n"
        "Proven giveaway strategies to grow your channel:\n\n"
        "🎲 <b>Random Winner Draw</b>\n"
        "Builds anticipation — members stay subscribed waiting for the result. Great for re-engaging old members.\n\n"
        "❤️ <b>React-to-Enter</b>\n"
        "Every reaction boosts your post in Telegram's algorithm and shows visitors that the channel is active.\n\n"
        "📈 <b>Subscriber Milestone</b>\n"
        "Turns growth into an event. Members invite friends to unlock the reward — a viral loop!\n\n"
        "🧠 <b>Quiz Giveaway</b>\n"
        "Increases time spent on your channel and lets you highlight products/features inside the question.\n\n"
        "🔗 <b>Classic Link Claim</b>\n"
        "Urgency + speed. Perfect for flash bursts that drive instant traffic into the bot.\n\n"
        "💎 <b>Pro tips:</b>\n"
        "• Run draws on weekends (higher activity)\n"
        "• Pin the giveaway post for visibility\n"
        "• Announce winners publicly to build trust\n"
        "• Combine milestone + draw for maximum growth"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("➕ New Giveaway", callback_data="gw2_create"),
          types.InlineKeyboardButton("🏠 Dashboard", callback_data="gw2_home"))
    _edit_or_send(chat_id, msg_id, text, m)


def gw2_show_help(chat_id, msg_id=None):
    text = (
        "╔═══════════════════════╗\n"
        "║  ℹ️ <b>HOW IT WORKS</b>  ║\n"
        "╚═══════════════════════╝\n\n"
        "1️⃣ Tap <b>New Giveaway</b> and pick a type.\n"
        "2️⃣ Set the reward, winners and duration.\n"
        "3️⃣ Launch — the post goes live in your channel.\n"
        "4️⃣ Members join via the button (captcha-protected).\n"
        "5️⃣ Draws auto-pick winners when time ends; you get a full report.\n\n"
        "🔔 Keep <b>Live Reports</b> on to receive real-time claim & winner alerts.\n"
        "🛡 Anti-bot: every claimant solves a captcha.\n"
        "📢 Make sure the bot is an admin in the channel to publish & edit posts."
    )
    _edit_or_send(chat_id, msg_id, text, _back_kb())


# ---------- Main callback router ----------

@bot.callback_query_handler(func=lambda c: c.data.startswith("gw2_"))
def gw2_router(call):
    uid = str(call.from_user.id)
    if not _gw2_is_admin(uid):
        bot.answer_callback_query(call.id, "🔒 Admins only")
        return
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if data == "gw2_home":
        gw2_open_dashboard(chat_id, msg_id)
    elif data == "gw2_create":
        gw2_show_types(chat_id, msg_id)
    elif data.startswith("gw2_type_"):
        gw2_begin_type(call, data.split("gw2_type_", 1)[1])
    elif data == "gw2_list":
        gw2_show_list(chat_id, msg_id)
    elif data.startswith("gw2_view_"):
        gw2_show_detail(chat_id, msg_id, data.split("gw2_view_", 1)[1])
    elif data.startswith("gw2_pub_"):
        code = data.split("gw2_pub_", 1)[1]
        mid = publish_giveaway_to_channel(code)
        bot.answer_callback_query(call.id, "📢 Published to channel!" if mid else "❌ Publish failed", show_alert=True)
        gw2_show_detail(chat_id, msg_id, code)
    elif data.startswith("gw2_repost_"):
        code = data.split("gw2_repost_", 1)[1]
        mid = publish_giveaway_to_channel(code)
        bot.answer_callback_query(call.id, "🔁 Re-published!" if mid else "❌ Failed", show_alert=True)
        gw2_show_detail(chat_id, msg_id, code)
    elif data.startswith("gw2_end_"):
        gw2_finish_now(call, data.split("gw2_end_", 1)[1])
    elif data.startswith("gw2_cancel_"):
        code = data.split("gw2_cancel_", 1)[1]
        cancel_giveaway(code)
        bot.answer_callback_query(call.id, "🗑 Cancelled & post deleted", show_alert=True)
        gw2_show_list(chat_id, msg_id)
    elif data == "gw2_stats":
        gw2_show_stats(chat_id, msg_id)
    elif data == "gw2_ideas":
        gw2_show_ideas(chat_id, msg_id)
    elif data == "gw2_reports":
        cur = bot_config.get("gw_live_reports", True)
        bot_config["gw_live_reports"] = not cur
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, f"Live reports {'ON' if not cur else 'OFF'}")
        gw2_open_dashboard(chat_id, msg_id)
    elif data == "gw2_help":
        gw2_show_help(chat_id, msg_id)
    # creation step menus
    elif data.startswith("gw2_reward_"):
        gw2_set_reward(call, data.split("gw2_reward_", 1)[1])
    elif data.startswith("gw2_winners_"):
        gw2_set_winners(call, data.split("gw2_winners_", 1)[1])
    elif data.startswith("gw2_hours_"):
        gw2_set_hours(call, data.split("gw2_hours_", 1)[1])
    elif data.startswith("gw2_quizans_"):
        gw2_set_quiz_answer(call, int(data.split("gw2_quizans_", 1)[1]))
    elif data == "gw2_launch":
        gw2_launch(call)
    elif data == "gw2_abort":
        gw2_setup.pop(uid, None)
        bot.answer_callback_query(call.id, "Cancelled")
        gw2_open_dashboard(chat_id, msg_id)


print("✅ Giveaway Studio v2.0 loaded (5 campaign types + admin dashboard)")


print("=" * 50)
