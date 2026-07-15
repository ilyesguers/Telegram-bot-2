"""
=====================================================================
 bot6.py - Interactive channel/group games
=====================================================================
Features:
- Reaction games.
- Comment race games.
- Full English bot messages.
- Supports answers written as replies/comments under channel posts in a
  linked discussion group.
- Sends a private winner message.
- Sends detailed winner reports to admins.

Install in bot.py without changing anything else:
    import bot6

Important Telegram note:
Telegram does not expose the identity of users who react to pure channel
posts through anonymous reaction counters. For identifiable winners, use
the linked discussion group or publish the game inside a group/supergroup.
=====================================================================
"""

import random
import string
from datetime import datetime

from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import (
    bot_config,
    save_json,
    DB_CONFIG,
    get_user,
    update_user_data,
    update_user_rank_and_quests,
)


# =====================================================================
# Polling patch: make sure reaction updates and normal messages arrive
# even if the main bot.py calls infinity_polling without allowed_updates.
# =====================================================================
_original_infinity_polling = bot.infinity_polling


def _patched_infinity_polling(*args, **kwargs):
    kwargs.setdefault(
        "allowed_updates",
        [
            "message",
            "edited_message",
            "callback_query",
            "message_reaction",
            "message_reaction_count",
            "chat_member",
        ],
    )
    return _original_infinity_polling(*args, **kwargs)


bot.infinity_polling = _patched_infinity_polling

_original_polling = bot.polling


def _patched_polling(*args, **kwargs):
    kwargs.setdefault(
        "allowed_updates",
        [
            "message",
            "edited_message",
            "callback_query",
            "message_reaction",
            "message_reaction_count",
            "chat_member",
        ],
    )
    return _original_polling(*args, **kwargs)


bot.polling = _patched_polling


# =====================================================================
# Storage initialization
# =====================================================================
def _init_defaults():
    ig = bot_config.setdefault("interactive_games", {})
    ig.setdefault("games_chat_id", None)
    ig.setdefault("reaction_games", {})
    ig.setdefault("race_games", {})
    ig.setdefault("admin_reports", True)
    save_json(DB_CONFIG, bot_config)


_init_defaults()

# Temporary admin setup state.
temp_setup = {}


def _is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except Exception:
        pass
    u = get_user(str(uid)) or {}
    return bool(u.get("is_admin", False))


def _admin_ids():
    ids = []
    for uid in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        try:
            if uid and int(uid) not in ids:
                ids.append(int(uid))
        except Exception:
            pass
    return ids


def _is_games_chat(message):
    try:
        ig = bot_config.get("interactive_games", {})
        return (
            message.chat.id == ig.get("games_chat_id")
            and message.chat.type in ("group", "supergroup")
        )
    except Exception:
        return False


def _new_game_id(prefix):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{prefix}_{stamp}_{rand}"


def _display_user(user):
    username = getattr(user, "username", None)
    full_name = " ".join(
        p for p in [getattr(user, "first_name", None), getattr(user, "last_name", None)] if p
    ).strip()
    if username:
        return f"@{username}"
    if full_name:
        return full_name
    return str(getattr(user, "id", "Unknown"))


def _normalize_answer(text):
    return (text or "").strip().casefold()


def _extract_message_text(message):
    return (getattr(message, "text", None) or getattr(message, "caption", None) or "").strip()


def _message_link(chat_id, message_id):
    # Public username links are not always available, so generate a private
    # supergroup link when possible. Telegram uses the ID without -100.
    try:
        raw = str(chat_id)
        if raw.startswith("-100"):
            return f"https://t.me/c/{raw[4:]}/{message_id}"
    except Exception:
        pass
    return "Unavailable"


def _safe_send(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"bot6 send error: {e}")
        return None


def _safe_reply(message, text, **kwargs):
    try:
        return bot.reply_to(message, text, **kwargs)
    except Exception as e:
        print(f"bot6 reply error: {e}")
        return None


def _try_react_to_answer(message):
    # Available only on newer pyTelegramBotAPI/Bot API versions.
    try:
        reaction = [types.ReactionTypeEmoji("🏆")]
        bot.set_message_reaction(message.chat.id, message.message_id, reaction=reaction)
    except Exception:
        pass


def _award_points(uid, points):
    update_user_data(str(uid), points=points, accumulated_points=points)
    try:
        update_user_rank_and_quests(str(uid))
    except Exception as e:
        print(f"bot6 rank/quest update error: {e}")


def _send_winner_dm(uid, points, game_title, answer_text, game_id):
    text = (
        "Congratulations!\n\n"
        f"You won {points} points in the comment race.\n"
        f"Game: {game_title}\n"
        f"Your answer: {answer_text}\n"
        f"Game ID: {game_id}\n\n"
        "Your points were added to your account automatically."
    )
    return _safe_send(uid, text)


def _send_admin_report(game, message, points, dm_sent):
    ig = bot_config.get("interactive_games", {})
    if not ig.get("admin_reports", True):
        return

    user = message.from_user
    u = get_user(str(user.id)) or {}
    link = _message_link(message.chat.id, message.message_id)
    text = (
        "New comment race winner\n\n"
        f"Game ID: {game.get('id')}\n"
        f"Game title: {game.get('title', 'Comment race')}\n"
        f"User: {_display_user(user)}\n"
        f"User ID: {user.id}\n"
        f"Database username: @{u.get('username', 'N/A')}\n"
        f"Answer: {_extract_message_text(message)}\n"
        f"Points awarded: {points}\n"
        f"Total current points: {u.get('points', 'Unknown')}\n"
        f"DM delivered: {'Yes' if dm_sent else 'No'}\n"
        f"Chat ID: {message.chat.id}\n"
        f"Message ID: {message.message_id}\n"
        f"Message link: {link}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    recipients = set(_admin_ids())
    creator = game.get("created_by")
    try:
        if creator:
            recipients.add(int(creator))
    except Exception:
        pass

    for admin_id in recipients:
        _safe_send(admin_id, text)


# =====================================================================
# Admin panel
# =====================================================================
def _show_games_panel(chat_id, msg_id=None):
    ig = bot_config.get("interactive_games", {})
    gcid = ig.get("games_chat_id")
    active_r = sum(
        1 for g in ig.get("reaction_games", {}).values() if g.get("status") == "active"
    )
    active_c = sum(
        1 for g in ig.get("race_games", {}).values() if g.get("status") == "active"
    )
    reports = "On" if ig.get("admin_reports", True) else "Off"
    txt = (
        "Interactive Games Panel\n\n"
        f"Games discussion group: {gcid if gcid else 'Not set'}\n"
        f"Active reaction games: {active_r}\n"
        f"Active comment races: {active_c}\n"
        f"Admin winner reports: {reports}\n\n"
        "Choose an action:"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("Set games discussion group", callback_data="igadm_setchat"))
    m.add(types.InlineKeyboardButton("Create reaction game", callback_data="igadm_newreact"))
    m.add(types.InlineKeyboardButton("Create comment race", callback_data="igadm_newrace"))
    m.add(types.InlineKeyboardButton("List/manage active games", callback_data="igadm_list"))
    m.add(types.InlineKeyboardButton("Toggle admin reports", callback_data="igadm_reports"))
    m.add(types.InlineKeyboardButton("Refresh", callback_data="igadm_refresh"))

    if msg_id:
        try:
            bot.edit_message_text(txt, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except Exception:
            pass
    bot.send_message(chat_id, txt, reply_markup=m, parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text in ("🎮 ألعاب القناة التفاعلية", "Interactive Games"))
def _open_games_panel(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return
    _show_games_panel(message.chat.id)


@bot.message_handler(commands=["games", "interactive_games"])
def _open_games_panel_cmd(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return
    _show_games_panel(message.chat.id)


# =====================================================================
# Admin callbacks
# =====================================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("igadm_"))
def _games_admin_cb(call):
    uid = str(call.from_user.id)
    if not _is_admin(uid):
        return bot.answer_callback_query(call.id, "Admin access only", show_alert=True)

    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if data == "igadm_refresh":
        return _show_games_panel(chat_id, msg_id)

    if data == "igadm_reports":
        ig = bot_config.setdefault("interactive_games", {})
        ig["admin_reports"] = not ig.get("admin_reports", True)
        save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, f"Admin reports: {'On' if ig['admin_reports'] else 'Off'}")
        return _show_games_panel(chat_id, msg_id)

    if data == "igadm_setchat":
        msg = bot.send_message(
            chat_id,
            "Send a forwarded message from the linked discussion group, "
            "or send the numeric group ID. The group ID is usually negative.",
        )
        bot.register_next_step_handler(msg, _process_set_chat)
        return

    if data == "igadm_newreact":
        temp_setup[uid] = {"type": "react"}
        msg = bot.send_message(chat_id, "Write the reaction game announcement text:")
        bot.register_next_step_handler(msg, _process_react_text)
        return

    if data == "igadm_newrace":
        temp_setup[uid] = {"type": "race"}
        msg = bot.send_message(
            chat_id,
            "Send the correct word, number, or phrase that users must write in comments:",
        )
        bot.register_next_step_handler(msg, _process_race_keyword)
        return

    if data == "igadm_list":
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_end_r_"):
        gid = data.split("igadm_end_r_", 1)[1]
        g = bot_config.get("interactive_games", {}).get("reaction_games", {}).get(gid)
        if g:
            g["status"] = "ended"
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "Reaction game ended")
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_cancel_r_"):
        gid = data.split("igadm_cancel_r_", 1)[1]
        g = bot_config.get("interactive_games", {}).get("reaction_games", {}).get(gid)
        if g:
            for wuid, w in list(g.get("winners", {}).items()):
                pts = int(w.get("points", 0) or 0)
                if pts:
                    update_user_data(wuid, points=-pts, accumulated_points=-pts)
            g["status"] = "cancelled"
            g["winners"] = {}
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "Reaction game cancelled and points reverted", show_alert=True)
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_end_c_"):
        gid = data.split("igadm_end_c_", 1)[1]
        g = bot_config.get("interactive_games", {}).get("race_games", {}).get(gid)
        if g:
            g["status"] = "ended"
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "Comment race ended")
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_cancel_c_"):
        gid = data.split("igadm_cancel_c_", 1)[1]
        g = bot_config.get("interactive_games", {}).get("race_games", {}).get(gid)
        if g:
            for wuid, w in list(g.get("winners", {}).items()):
                pts = int(w.get("points", 0) or 0)
                if pts:
                    update_user_data(wuid, points=-pts, accumulated_points=-pts)
            g["status"] = "cancelled"
            g["winners"] = {}
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "Comment race cancelled and points reverted", show_alert=True)
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_winners_r_"):
        gid = data.split("igadm_winners_r_", 1)[1]
        return _show_winners(chat_id, msg_id, "reaction", gid)

    if data.startswith("igadm_winners_c_"):
        gid = data.split("igadm_winners_c_", 1)[1]
        return _show_winners(chat_id, msg_id, "race", gid)


# =====================================================================
# Setup steps
# =====================================================================
def _process_set_chat(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return

    chat_id = None
    if getattr(message, "forward_from_chat", None):
        chat_id = message.forward_from_chat.id
    elif getattr(message, "forward_origin", None):
        origin = message.forward_origin
        chat = getattr(origin, "chat", None)
        if chat:
            chat_id = chat.id
    else:
        txt = (message.text or "").strip()
        try:
            chat_id = int(txt)
        except Exception:
            chat_id = None

    if not chat_id:
        bot.send_message(message.chat.id, "Could not read the group ID. Please try again.")
        return

    ig = bot_config.setdefault("interactive_games", {})
    ig["games_chat_id"] = chat_id
    save_json(DB_CONFIG, bot_config)
    bot.send_message(
        message.chat.id,
        f"Games discussion group saved successfully.\nGroup ID: {chat_id}",
    )


def _process_react_text(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    temp_setup[uid]["text"] = _extract_message_text(message)
    msg = bot.send_message(message.chat.id, "Which emoji should users react with? Example: ❤️")
    bot.register_next_step_handler(msg, _process_react_emoji)


def _process_react_emoji(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    temp_setup[uid]["emoji"] = _extract_message_text(message)[:8]
    msg = bot.send_message(message.chat.id, "How many points should each winner receive?")
    bot.register_next_step_handler(msg, _process_react_points)


def _process_react_points(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    try:
        pts = int((message.text or "").strip())
        if pts <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "Please send a valid positive number.")
        bot.register_next_step_handler(msg, _process_react_points)
        return
    temp_setup[uid]["points"] = pts
    msg = bot.send_message(message.chat.id, "How many winners are allowed? Send 0 for unlimited.")
    bot.register_next_step_handler(msg, _finish_react_game)


def _finish_react_game(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    try:
        max_winners = int((message.text or "0").strip())
        if max_winners < 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "Please send a valid number. Use 0 for unlimited.")
        bot.register_next_step_handler(msg, _finish_react_game)
        return

    ig = bot_config.setdefault("interactive_games", {})
    games_chat_id = ig.get("games_chat_id")
    if not games_chat_id:
        temp_setup.pop(uid, None)
        bot.send_message(message.chat.id, "Set the games discussion group first.")
        return

    setup = temp_setup.pop(uid)
    gid = _new_game_id("react")
    announcement = (
        f"{setup['text']}\n\n"
        f"React with: {setup['emoji']}\n"
        f"Reward: {setup['points']} points"
    )
    sent = _safe_send(games_chat_id, announcement)
    if not sent:
        bot.send_message(message.chat.id, "Could not publish the game. Check bot permissions.")
        return


    ig.setdefault("reaction_games", {})[gid] = {
        "id": gid,
        "status": "active",
        "text": setup["text"],
        "emoji": setup["emoji"],
        "points": setup["points"],
        "max_winners": max_winners,
        "chat_id": games_chat_id,
        "message_id": sent.message_id,
        "created_by": uid,
        "created_at": datetime.now().isoformat(),
        "winners": {},
    }
    save_json(DB_CONFIG, bot_config)
    bot.send_message(
        message.chat.id,
        f"Reaction game published.\nGame ID: {gid}\nMessage ID: {sent.message_id}",
    )


def _process_race_keyword(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    keyword = _extract_message_text(message)
    if not keyword:
        msg = bot.send_message(message.chat.id, "The answer cannot be empty. Send it again:")
        bot.register_next_step_handler(msg, _process_race_keyword)
        return
    temp_setup[uid]["keyword"] = keyword
    msg = bot.send_message(message.chat.id, "How many points should the correct answer receive?")
    bot.register_next_step_handler(msg, _process_race_points)


def _process_race_points(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    try:
        pts = int((message.text or "").strip())
        if pts <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "Please send a valid positive number.")
        bot.register_next_step_handler(msg, _process_race_points)
        return
    temp_setup[uid]["points"] = pts
    msg = bot.send_message(message.chat.id, "How many winners are allowed? Send 1 for first correct answer only.")
    bot.register_next_step_handler(msg, _process_race_winners)


def _process_race_winners(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    try:
        max_winners = int((message.text or "1").strip())
        if max_winners <= 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "Please send a valid positive number.")
        bot.register_next_step_handler(msg, _process_race_winners)
        return
    temp_setup[uid]["max_winners"] = max_winners
    msg = bot.send_message(
        message.chat.id,
        "Send the public race title/announcement.\n"
        "Tip: do not include the secret answer unless you want users to see it.",
    )
    bot.register_next_step_handler(msg, _process_race_title)


def _process_race_title(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return
    title = _extract_message_text(message) or "Comment Race"
    temp_setup[uid]["title"] = title
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("Publish race message in discussion group", callback_data="igrace_pub"))
    m.add(types.InlineKeyboardButton("Bind race to an existing channel post comments", callback_data="igrace_bind"))
    bot.send_message(
        message.chat.id,
        "Choose where the bot should watch for correct answers:",
        reply_markup=m,
    )


@bot.callback_query_handler(func=lambda c: c.data in ("igrace_pub", "igrace_bind"))
def _race_publish_mode_cb(call):
    uid = str(call.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return bot.answer_callback_query(call.id, "No pending race setup", show_alert=True)

    if call.data == "igrace_pub":
        bot.answer_callback_query(call.id, "Publishing race")
        return _finish_race_game(call.message, publish=True)

    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "Now go to the linked discussion group and forward/copy the channel post message "
        "as it appears there, or send its discussion message ID.\n\n"
        "The bot will accept correct replies/comments under that exact message.",
    )
    bot.register_next_step_handler(msg, _process_race_target_message)


def _process_race_target_message(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return

    ig = bot_config.get("interactive_games", {})
    games_chat_id = ig.get("games_chat_id")
    if not games_chat_id:
        temp_setup.pop(uid, None)
        bot.send_message(message.chat.id, "Set the games discussion group first.")
        return

    target_message_id = None
    target_chat_id = games_chat_id

    if message.forward_from_chat or getattr(message, "forward_origin", None):
        # If the admin forwards the automatic channel post from the discussion
        # group, Telegram often keeps the forwarded message ID in this message.
        target_message_id = getattr(message, "forward_from_message_id", None)
    if not target_message_id and message.reply_to_message:
        target_message_id = message.reply_to_message.message_id
        target_chat_id = message.chat.id
    if not target_message_id:
        try:
            target_message_id = int((message.text or "").strip())
        except Exception:
            target_message_id = None

    if not target_message_id:
        msg = bot.send_message(
            message.chat.id,
            "Could not detect the target message. Send the discussion message ID only, or reply to the target message.",
        )
        bot.register_next_step_handler(msg, _process_race_target_message)
        return

    temp_setup[uid]["target_chat_id"] = target_chat_id
    temp_setup[uid]["target_message_id"] = target_message_id
    _finish_race_game(message, publish=False)


def _finish_race_game(message, publish=False):
    uid = str(message.from_user.id)
    if not _is_admin(uid) or uid not in temp_setup:
        return

    ig = bot_config.setdefault("interactive_games", {})
    games_chat_id = ig.get("games_chat_id")
    if not games_chat_id:
        temp_setup.pop(uid, None)
        bot.send_message(message.chat.id, "Set the games discussion group first.")
        return

    setup = temp_setup.pop(uid)
    gid = _new_game_id("race")
    target_chat_id = setup.get("target_chat_id") or games_chat_id
    target_message_id = setup.get("target_message_id")
    sent = None

    if publish:
        public_text = (
            f"{setup['title']}\n\n"
            "Write the correct answer in a reply/comment under this message.\n"
            f"Reward: {setup['points']} points\n"
            f"Winners: {setup['max_winners']}"
        )
        sent = _safe_send(games_chat_id, public_text)
        if not sent:
            bot.send_message(message.chat.id, "Could not publish the race. Check bot permissions.")
            return
        target_chat_id = games_chat_id
        target_message_id = sent.message_id

    ig.setdefault("race_games", {})[gid] = {
        "id": gid,
        "status": "active",
        "title": setup["title"],
        "keyword": setup["keyword"],
        "keyword_norm": _normalize_answer(setup["keyword"]),
        "points": setup["points"],
        "max_winners": setup["max_winners"],
        "chat_id": target_chat_id,
        "message_id": target_message_id,
        "created_by": uid,
        "created_at": datetime.now().isoformat(),
        "mode": "published" if publish else "bound_channel_comments",
        "winners": {},
        "winner_order": [],
    }
    save_json(DB_CONFIG, bot_config)

    bot.send_message(
        message.chat.id,
        "Comment race is active.\n"
        f"Game ID: {gid}\n"
        f"Watching chat ID: {target_chat_id}\n"
        f"Watching replies to message ID: {target_message_id}",
    )


# =====================================================================
# Lists and winner views
# =====================================================================
def _show_active_list(chat_id, msg_id=None):
    ig = bot_config.get("interactive_games", {})
    m = types.InlineKeyboardMarkup(row_width=1)
    lines = ["Active games", ""]

    has_games = False
    for gid, g in ig.get("reaction_games", {}).items():
        if g.get("status") != "active":
            continue
        has_games = True
        lines.append(
            f"Reaction: {gid}\nEmoji: {g.get('emoji')} | Points: {g.get('points')} | Winners: {len(g.get('winners', {}))}"
        )
        m.add(types.InlineKeyboardButton(f"Winners reaction {gid}", callback_data=f"igadm_winners_r_{gid}"))
        m.add(
            types.InlineKeyboardButton(f"End reaction {gid}", callback_data=f"igadm_end_r_{gid}"),
            types.InlineKeyboardButton(f"Cancel reaction {gid}", callback_data=f"igadm_cancel_r_{gid}"),
        )

    for gid, g in ig.get("race_games", {}).items():
        if g.get("status") != "active":
            continue
        has_games = True
        lines.append(
            f"Race: {gid}\nTitle: {g.get('title')} | Points: {g.get('points')} | Winners: {len(g.get('winners', {}))}/{g.get('max_winners')}"
        )
        m.add(types.InlineKeyboardButton(f"Winners race {gid}", callback_data=f"igadm_winners_c_{gid}"))
        m.add(
            types.InlineKeyboardButton(f"End race {gid}", callback_data=f"igadm_end_c_{gid}"),
            types.InlineKeyboardButton(f"Cancel race {gid}", callback_data=f"igadm_cancel_c_{gid}"),
        )

    if not has_games:
        lines.append("No active games right now.")
    m.add(types.InlineKeyboardButton("Back", callback_data="igadm_refresh"))
    txt = "\n\n".join(lines)

    if msg_id:
        try:
            bot.edit_message_text(txt, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except Exception:
            pass
    bot.send_message(chat_id, txt, reply_markup=m, parse_mode="HTML")


def _show_winners(chat_id, msg_id, game_type, gid):
    ig = bot_config.get("interactive_games", {})
    group = "reaction_games" if game_type == "reaction" else "race_games"
    g = ig.get(group, {}).get(gid)
    if not g:
        bot.send_message(chat_id, "Game not found.")
        return

    lines = [f"Winners for {gid}", ""]
    winners = g.get("winners", {})
    order = g.get("winner_order", list(winners.keys()))
    if not winners:
        lines.append("No winners yet.")
    else:
        for idx, wuid in enumerate(order, start=1):
            w = winners.get(str(wuid), {})
            lines.append(
                f"{idx}. {w.get('display', wuid)}\n"
                f"ID: {wuid}\n"
                f"Points: {w.get('points')}\n"
                f"Answer: {w.get('answer', '-')}\n"
                f"Time: {w.get('time', '-')}"
            )

    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("Back", callback_data="igadm_list"))
    txt = "\n\n".join(lines)
    try:
        bot.edit_message_text(txt, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, txt, reply_markup=m, parse_mode="HTML")


# =====================================================================
# Comment race answer handler
# =====================================================================
def _is_potential_race_answer(message):
    try:
        if not getattr(message, "from_user", None):
            return False
        if _is_admin(message.from_user.id):
            return False
        if not _is_games_chat(message):
            return False
        if not getattr(message, "reply_to_message", None):
            return False
        if not _extract_message_text(message):
            return False

        reply_to_id = message.reply_to_message.message_id
        chat_id = message.chat.id
        races = bot_config.get("interactive_games", {}).get("race_games", {})
        for game in races.values():
            if game.get("status") != "active":
                continue
            if int(game.get("chat_id")) == int(chat_id) and int(game.get("message_id")) == int(reply_to_id):
                return True
    except Exception:
        return False
    return False


@bot.message_handler(
    content_types=["text", "photo", "video", "document", "animation", "sticker"],
    func=_is_potential_race_answer,
)
def _handle_comment_race_answer(message):
    if not getattr(message, "from_user", None):
        return
    if _is_admin(message.from_user.id):
        # Admin answers should not accidentally win their own setup.
        return
    if not _is_games_chat(message):
        return
    if not getattr(message, "reply_to_message", None):
        return

    answer = _extract_message_text(message)
    if not answer:
        return
    answer_norm = _normalize_answer(answer)
    reply_to_id = message.reply_to_message.message_id
    chat_id = message.chat.id

    ig = bot_config.setdefault("interactive_games", {})
    races = ig.setdefault("race_games", {})
    changed = False

    for gid, game in list(races.items()):
        if game.get("status") != "active":
            continue
        if int(game.get("chat_id")) != int(chat_id):
            continue
        if int(game.get("message_id")) != int(reply_to_id):
            continue
        if answer_norm != game.get("keyword_norm", _normalize_answer(game.get("keyword"))):
            continue

        uid = str(message.from_user.id)
        if uid in game.get("winners", {}):
            _safe_reply(message, "You already won this race. Your points were already added.")
            return

        winners = game.setdefault("winners", {})
        winner_order = game.setdefault("winner_order", [])
        max_winners = int(game.get("max_winners", 1) or 1)
        if len(winners) >= max_winners:
            game["status"] = "ended"
            changed = True
            continue

        points = int(game.get("points", 0) or 0)
        _award_points(uid, points)

        dm = _send_winner_dm(uid, points, game.get("title", "Comment race"), answer, gid)
        dm_sent = bool(dm)
        _try_react_to_answer(message)

        winners[uid] = {
            "uid": uid,
            "display": _display_user(message.from_user),
            "username": getattr(message.from_user, "username", None),
            "points": points,
            "answer": answer,
            "message_id": message.message_id,
            "chat_id": chat_id,
            "dm_sent": dm_sent,
            "time": datetime.now().isoformat(),
        }
        winner_order.append(uid)

        _safe_reply(
            message,
            "Correct answer!\n"
            f"Congratulations {_display_user(message.from_user)}.\n"
            f"You received {points} points.",
        )
        _send_admin_report(game, message, points, dm_sent)

        if len(winners) >= max_winners:
            game["status"] = "ended"
            _safe_send(
                chat_id,
                f"The comment race is now finished. Winners reached: {len(winners)}/{max_winners}.",
            )

        changed = True
        break

    if changed:
        save_json(DB_CONFIG, bot_config)


# =====================================================================
# Reaction game handler
# =====================================================================
@bot.message_reaction_handler(func=lambda r: True)
def _handle_reaction_game(reaction):
    try:
        chat_id = reaction.chat.id
        message_id = reaction.message_id
        user = reaction.user
    except Exception:
        return

    if not user or _is_admin(user.id):
        return

    ig = bot_config.setdefault("interactive_games", {})
    games = ig.setdefault("reaction_games", {})
    changed = False

    for gid, game in list(games.items()):
        if game.get("status") != "active":
            continue
        if int(game.get("chat_id")) != int(chat_id):
            continue
        if int(game.get("message_id")) != int(message_id):
            continue

        new_reactions = getattr(reaction, "new_reaction", []) or []
        wanted = game.get("emoji")
        matched = False
        for r in new_reactions:
            emoji = getattr(r, "emoji", None)
            if emoji == wanted:
                matched = True
                break
        if not matched:
            return

        uid = str(user.id)
        winners = game.setdefault("winners", {})
        if uid in winners:
            return

        max_winners = int(game.get("max_winners", 0) or 0)
        if max_winners and len(winners) >= max_winners:
            game["status"] = "ended"
            changed = True
            break

        points = int(game.get("points", 0) or 0)
        _award_points(uid, points)
        dm = _send_winner_dm(uid, points, "Reaction game", wanted, gid)

        winners[uid] = {
            "uid": uid,
            "display": _display_user(user),
            "username": getattr(user, "username", None),
            "points": points,
            "answer": wanted,
            "message_id": message_id,
            "chat_id": chat_id,
            "dm_sent": bool(dm),
            "time": datetime.now().isoformat(),
        }

        if max_winners and len(winners) >= max_winners:
            game["status"] = "ended"

        changed = True
        break

    if changed:
        save_json(DB_CONFIG, bot_config)


print("=" * 55)
print("bot6.py loaded: interactive games are active")
print("Comment races watch replies under linked discussion messages")
print("All user/admin messages in this module are English")
print("=" * 55)
