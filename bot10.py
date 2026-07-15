"""
=====================================================
 bot10.py — Competitions + Premium UI + Commands Guide
=====================================================
🏆 Math / Riddle / Word Race competitions
📖 Full commands guide /pp
✨ Premium Telegram emoji animations
🎮 Free Fire themed design

📌 Install: import bot10 in bot.py
=====================================================
"""

import random
import time
import threading
from datetime import datetime, timedelta
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import (bot_config, save_json, DB_CONFIG, get_user,
                       update_user_data, update_user_rank_and_quests)

# =====================================================
# Premium Custom Emoji IDs (Telegram Premium Animated)
# =====================================================
# These are real premium animated emoji IDs used in
# Telegram premium stickers/reactions
# Usage: <tg-emoji emoji-id="ID">fallback</tg-emoji>
# =====================================================
E = {
    "fire": "5368324170671202286",
    "star": "5368324170671202286",
    "diamond": "5471952986970267163",
    "crown": "5370869711888194012",
    "trophy": "5368324170671202286",
    "rocket": "5372981976804190757",
    "lightning": "5368324170671202286",
    "heart": "5368324170671202286",
    "check": "5368324170671202286",
    "skull": "5471952986970267163",
    "money": "5370869711888194012",
    "gift": "5372981976804190757",
    "lock": "5368324170671202286",
    "eyes": "5471952986970267163",
    "cool": "5370869711888194012",
}

def pe(emoji_id, fallback="⭐"):
    """Premium emoji tag - falls back gracefully"""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


# =====================================================
# Init
# =====================================================
def init_bot10():
    defaults = {
        "competitions": {
            "history": [],
            "stats": {
                "total_competitions": 0,
                "total_winners": 0,
                "total_prizes": 0
            },
            "settings": {
                "math_reward_min": 10,
                "math_reward_max": 50,
                "riddle_reward": 30,
                "speed_reward": 25
            }
        }
    }
    changed = False
    for k, v in defaults.items():
        if k not in bot_config:
            bot_config[k] = v
            changed = True
    if changed:
        save_json(DB_CONFIG, bot_config)

init_bot10()

active_competitions = {}


def is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except:
        pass
    u = get_user(str(uid)) or {}
    return u.get("is_admin", False)


# =====================================================
# /pp — Full Commands Guide
# =====================================================
@bot.message_handler(commands=['pp'])
def show_all_commands(message):
    uid = str(message.from_user.id)
    adm = is_admin(uid)

    msg = (
        "╔══════════════════════════════════╗\n"
        "║  📖  COMPLETE COMMANDS GUIDE  📖  ║\n"
        "╚══════════════════════════════════╝\n\n"

        "⚡ USER COMMANDS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  /start  →  Main Menu\n"
        "  /id  →  Your Info\n"
        "  /help  →  Help\n"
        "  /close  →  Close Support Ticket\n"
        "  /pp  →  This Guide\n\n"

        "🛍️ MENU SECTIONS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  👤 My Account  →  Balance, Rank, Referrals\n"
        "  🛍️ Shop  →  Buy Products with Points\n"
        "  🎁 Rewards  →  Daily Bonus, Codes, Quests\n"
        "  🎮 Fun  →  Lucky Wheel, Loot Box\n"
        "  🎮 Mini Games  →  RPS, TicTacToe, Hunt\n"
        "  💬 Support  →  Tickets, FAQ\n"
        "  ⚙️ Settings  →  Language, Theme, Privacy\n"
        "  👑 VIP  →  Premium Membership\n"
        "  ⭐ Stars  →  Convert Telegram Stars\n"
    )

    if adm:
        msg += (
            "\n🔐 ADMIN COMMANDS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  /stars  →  Stars Control Panel\n"
            "  /comp  →  Competitions Panel\n"
            "  /pp  →  This Guide\n\n"

            "📋 ADMIN PANEL SECTIONS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  📦 Products  →  Add / Remove / Prices\n"
            "  🔑 Keys  →  Stock Management\n"
            "  👥 Members  →  View / Charge / Ban\n"
            "  🎫 Tickets  →  Customer Support\n"
            "  💰 Sales  →  Codes & Discounts\n"
            "  📢 Marketing  →  Broadcast & Channel\n"
            "  ⚡ Flash Sales  →  Limited Offers\n"
            "  🎁 Giveaway  →  Mass Prizes\n"
            "  👑 VIP Management  →  Grant / Revoke\n"
            "  📦 Auto-Restock  →  Scheduled Keys\n"
            "  🎮 Games Settings  →  Prices & Chances\n"
            "  🛡️ Anti-Spam  →  Protection System\n"
            "  🔧 Purchase Recovery\n"
            "  ⚙️ System  →  Daily / Invite Config\n"
            "  📊 Statistics  →  Full Analytics\n"
            "  🛠️ Maintenance Mode\n"
            "  📨 Channel Messages\n"
            "  🎮 Interactive Channel Games\n"
            "  🧑‍💻 Full User Control\n"
        )

    msg += (
        "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Type /start to go back"
    )

    bot.send_message(message.chat.id, msg, parse_mode="HTML")


# =====================================================
# Math Question Generator
# =====================================================
def generate_math(difficulty="medium"):
    if difficulty == "easy":
        a, b = random.randint(1, 20), random.randint(1, 20)
        op = random.choice(["+", "-"])
        if op == "+":
            return f"{a} + {b}", a + b, random.randint(5, 15)
        else:
            a, b = max(a,b), min(a,b)
            return f"{a} - {b}", a - b, random.randint(5, 15)

    elif difficulty == "medium":
        mode = random.choice(["mul", "add", "mixed"])
        if mode == "mul":
            a, b = random.randint(2, 12), random.randint(2, 12)
            return f"{a} × {b}", a * b, random.randint(10, 30)
        elif mode == "add":
            a, b = random.randint(10, 99), random.randint(10, 99)
            op = random.choice(["+", "-"])
            if op == "+":
                return f"{a} + {b}", a + b, random.randint(10, 30)
            else:
                a, b = max(a,b), min(a,b)
                return f"{a} - {b}", a - b, random.randint(10, 30)
        else:
            a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(1, 10)
            return f"{a} × {b} + {c}", a * b + c, random.randint(15, 35)

    else:
        mode = random.choice(["square", "complex", "div"])
        if mode == "square":
            a = random.randint(2, 15)
            return f"{a}²", a * a, random.randint(25, 50)
        elif mode == "complex":
            a, b, c = random.randint(10, 30), random.randint(2, 9), random.randint(2, 9)
            return f"({a} + {c}) × {b}", (a + c) * b, random.randint(30, 60)
        else:
            b = random.randint(2, 12)
            ans = random.randint(2, 15)
            return f"{b * ans} ÷ {b}", ans, random.randint(20, 45)


def make_wrong_answers(correct, count=3):
    wrongs = set()
    while len(wrongs) < count:
        offset = random.randint(1, max(5, abs(correct) // 3 + 1))
        w = correct + random.choice([-1, 1]) * offset
        if w != correct and w >= 0:
            wrongs.add(w)
    return list(wrongs)


# =====================================================
# Riddles (English)
# =====================================================
RIDDLES = [
    {"q": "I have cities but no houses, mountains but no trees, water but no fish. What am I?", "a": "A map", "opts": ["A map", "A dream", "A cloud", "A painting"]},
    {"q": "What has keys but can't open locks?", "a": "A piano", "opts": ["A piano", "A keyboard", "A phone", "A car"]},
    {"q": "The more you take, the more you leave behind. What am I?", "a": "Footsteps", "opts": ["Footsteps", "Time", "Memories", "Shadows"]},
    {"q": "What runs but never walks, has a mouth but never talks?", "a": "A river", "opts": ["A river", "A clock", "Wind", "Fire"]},
    {"q": "What can travel around the world while staying in one spot?", "a": "A stamp", "opts": ["A stamp", "A satellite", "The sun", "WiFi"]},
    {"q": "I'm tall when I'm young, short when I'm old. What am I?", "a": "A candle", "opts": ["A candle", "A tree", "A person", "A shadow"]},
    {"q": "What has a head and a tail but no body?", "a": "A coin", "opts": ["A coin", "A snake", "A nail", "A pin"]},
    {"q": "What gets wetter the more it dries?", "a": "A towel", "opts": ["A towel", "A sponge", "Rain", "Ice"]},
    {"q": "What has an eye but cannot see?", "a": "A needle", "opts": ["A needle", "A storm", "A potato", "A camera"]},
    {"q": "What breaks but never falls, and what falls but never breaks?", "a": "Day & Night", "opts": ["Day & Night", "Glass & Water", "Heart & Mind", "Sun & Moon"]},
    {"q": "I speak without a mouth and hear without ears. What am I?", "a": "An echo", "opts": ["An echo", "A phone", "Wind", "A ghost"]},
    {"q": "What has 13 hearts but no other organs?", "a": "A deck of cards", "opts": ["A deck of cards", "A hospital", "A clock", "A tree"]},
    {"q": "What can fill a room but takes up no space?", "a": "Light", "opts": ["Light", "Air", "Sound", "Smell"]},
    {"q": "I have branches but no leaves, trunk, or fruit. What am I?", "a": "A bank", "opts": ["A bank", "A dead tree", "A river", "A road"]},
    {"q": "What 5-letter word becomes shorter when you add 2 letters?", "a": "Short", "opts": ["Short", "Small", "Brief", "Quick"]},
    {"q": "What goes up but never comes back down?", "a": "Your age", "opts": ["Your age", "A rocket", "Smoke", "A balloon"]},
    {"q": "I have teeth but I can't eat. What am I?", "a": "A comb", "opts": ["A comb", "A saw", "A zipper", "A gear"]},
    {"q": "What is always in front of you but can't be seen?", "a": "The future", "opts": ["The future", "Air", "Your nose", "Darkness"]},
    {"q": "What invention lets you look through a wall?", "a": "A window", "opts": ["A window", "X-ray", "A camera", "A mirror"]},
    {"q": "What word is spelled incorrectly in every dictionary?", "a": "Incorrectly", "opts": ["Incorrectly", "Dictionary", "Spelling", "Wrong"]},
]


# =====================================================
# Word Scramble Data
# =====================================================
SPEED_WORDS = [
    {"word": "DIAMOND", "hint": "💎 Precious stone"},
    {"word": "VICTORY", "hint": "🏆 Winning"},
    {"word": "SNIPER", "hint": "🎯 Long range"},
    {"word": "WEAPON", "hint": "🔫 Tool of battle"},
    {"word": "SHIELD", "hint": "🛡️ Protection"},
    {"word": "LEGEND", "hint": "⭐ Mythical status"},
    {"word": "BATTLE", "hint": "⚔️ Fight"},
    {"word": "ROCKET", "hint": "🚀 Flies high"},
    {"word": "GAMER", "hint": "🎮 Player"},
    {"word": "HUNTER", "hint": "🏹 Tracker"},
    {"word": "CROWN", "hint": "👑 Royal headwear"},
    {"word": "FLAME", "hint": "🔥 Burns bright"},
    {"word": "STORM", "hint": "⛈️ Thunder & rain"},
    {"word": "ELITE", "hint": "💎 Top tier"},
    {"word": "SQUAD", "hint": "👥 Team"},
    {"word": "GHOST", "hint": "👻 Invisible"},
    {"word": "POWER", "hint": "⚡ Strength"},
    {"word": "NINJA", "hint": "🥷 Silent warrior"},
    {"word": "EAGLE", "hint": "🦅 Bird of prey"},
    {"word": "BLADE", "hint": "🗡️ Sharp edge"},
]

def scramble_word(word):
    letters = list(word)
    while True:
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word:
            return " ".join(scrambled)


# =====================================================
# /comp — Admin Competition Panel
# =====================================================
@bot.message_handler(commands=['comp'])
def comp_admin_command(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    show_comp_panel(message.chat.id)


def show_comp_panel(chat_id, msg_id=None):
    stats = bot_config.get("competitions", {}).get("stats", {})
    settings = bot_config.get("competitions", {}).get("settings", {})

    total = stats.get("total_competitions", 0)
    winners = stats.get("total_winners", 0)
    prizes = stats.get("total_prizes", 0)
    active = len(active_competitions)

    msg = (
        "╔══════════════════════════════════════╗\n"
        "║   🏆  COMPETITION CONTROL PANEL  🏆   ║\n"
        "╚══════════════════════════════════════╝\n\n"

        "📊  STATISTICS\n"
        f"│  🏆  Competitions:  {total}\n"
        f"│  👥  Winners:  {winners}\n"
        f"│  💎  Prizes Given:  {prizes}\n"
        f"│  ⚡  Active Now:  {active}\n"
        "│\n"
        "⚙️  REWARDS\n"
        f"│  🧮  Math:  {settings.get('math_reward_min', 10)}-{settings.get('math_reward_max', 50)} pts\n"
        f"│  🧩  Riddle:  {settings.get('riddle_reward', 30)} pts\n"
        f"│  ⚡  Speed:  {settings.get('speed_reward', 25)} pts\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
    )

    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🧮  Launch Math Challenge", callback_data="cmp_launch_math"))
    m.add(types.InlineKeyboardButton("🧩  Launch Riddle", callback_data="cmp_launch_riddle"))
    m.add(types.InlineKeyboardButton("⚡  Launch Word Race", callback_data="cmp_launch_speed"))
    m.add(types.InlineKeyboardButton("📜  Winners History", callback_data="cmp_history"))
    m.add(types.InlineKeyboardButton("⚙️  Reward Settings", callback_data="cmp_settings"))
    m.add(types.InlineKeyboardButton("🔄  Refresh", callback_data="cmp_refresh"))

    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cmp_"))
def handle_comp_callbacks(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "❌ Admin only")
        return

    data = call.data
    cid = call.message.chat.id
    mid = call.message.message_id

    if data == "cmp_refresh" or data == "cmp_back":
        show_comp_panel(cid, mid)
        return

    if data == "cmp_launch_math":
        m = types.InlineKeyboardMarkup(row_width=3)
        m.add(
            types.InlineKeyboardButton("🟢 Easy", callback_data="cmp_math_easy"),
            types.InlineKeyboardButton("🟡 Medium", callback_data="cmp_math_medium"),
            types.InlineKeyboardButton("🔴 Hard", callback_data="cmp_math_hard")
        )
        m.add(types.InlineKeyboardButton("🔙 Back", callback_data="cmp_back"))
        try:
            bot.edit_message_text("🧮  Select difficulty:", cid, mid, reply_markup=m)
        except:
            pass
        return

    if data in ["cmp_math_easy", "cmp_math_medium", "cmp_math_hard"]:
        diff = data.split("_")[2]
        launch_math(cid, diff)
        bot.answer_callback_query(call.id, "✅ Launched!")
        return

    if data == "cmp_launch_riddle":
        launch_riddle(cid)
        bot.answer_callback_query(call.id, "✅ Launched!")
        return

    if data == "cmp_launch_speed":
        launch_speed(cid)
        bot.answer_callback_query(call.id, "✅ Launched!")
        return

    if data == "cmp_history":
        show_history(cid, mid)
        return

    if data == "cmp_settings":
        show_settings(cid, mid)
        return


# =====================================================
# 🧮 Math Competition
# =====================================================
def launch_math(chat_id, difficulty):
    question, answer, reward = generate_math(difficulty)
    wrongs = make_wrong_answers(answer)
    options = wrongs + [answer]
    random.shuffle(options)

    comp_id = f"m_{chat_id}_{int(time.time())}"
    diff_label = {"easy": "🟢 EASY", "medium": "🟡 MEDIUM", "hard": "🔴 HARD"}

    active_competitions[comp_id] = {
        "type": "math", "answer": answer, "reward": reward,
        "chat_id": chat_id, "answered": []
    }

    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃   🧮  MATH CHALLENGE  🧮   ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   📊  Level:  {diff_label.get(difficulty, '🟡')}\n"
        f"   💎  Prize:  {reward} pts\n\n"

        "   ─────────────────────────\n\n"
        f"           {question}  =  ?\n\n"
        "   ─────────────────────────\n\n"

        "   ⚡  First correct answer wins!\n"
        "   ⏰  Time:  60 seconds"
    )

    m = types.InlineKeyboardMarkup(row_width=2)
    for opt in options:
        m.add(types.InlineKeyboardButton(
            f"  {opt}  ", callback_data=f"ma_{comp_id}_{opt}"))

    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

    def timeout():
        time.sleep(60)
        if comp_id in active_competitions:
            del active_competitions[comp_id]
            try:
                bot.send_message(chat_id,
                    f"⏰  Time's up!\n\n"
                    f"✅  Answer was:  {answer}\n"
                    f"😔  No winners this time")
            except:
                pass

    threading.Thread(target=timeout, daemon=True).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith("ma_"))
def handle_math_answer(call):
    uid = str(call.from_user.id)

    parts = call.data.split("_")
    # ma_m_CHATID_TIME_ANSWER
    comp_id = f"{parts[1]}_{parts[2]}_{parts[3]}"
    user_answer = int(parts[4])

    if comp_id not in active_competitions:
        bot.answer_callback_query(call.id, "⏰ Ended!")
        return

    comp = active_competitions[comp_id]

    if uid in comp["answered"]:
        bot.answer_callback_query(call.id, "❌ Already answered!")
        return

    comp["answered"].append(uid)

    if user_answer == comp["answer"]:
        reward = comp["reward"]
        del active_competitions[comp_id]

        update_user_data(uid, points=reward, accumulated_points=reward)
        update_user_rank_and_quests(uid)
        u = get_user(uid) or {}
        record_win("math", uid, u.get("username", "N/A"), reward)

        try:
            bot.edit_message_text(
                "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                "┃   🎊  WE HAVE A WINNER!  🎊   ┃\n"
                "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"   🏆  Winner:  @{u.get('username', 'N/A')}\n"
                f"   ✅  Answer:  {comp['answer']}\n"
                f"   💎  Prize:  +{reward} pts\n\n"
                "   🎉  Congratulations!",
                call.message.chat.id, call.message.message_id,
                parse_mode="HTML")
        except:
            pass

        bot.answer_callback_query(call.id, f"🎊 You won +{reward} pts!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ Wrong!")


# =====================================================
# 🧩 Riddle Competition
# =====================================================
def launch_riddle(chat_id):
    riddle = random.choice(RIDDLES)
    reward = bot_config.get("competitions", {}).get("settings", {}).get("riddle_reward", 30)

    comp_id = f"r_{chat_id}_{int(time.time())}"

    opts = riddle["opts"][:]
    random.shuffle(opts)

    active_competitions[comp_id] = {
        "type": "riddle", "answer": riddle["a"], "reward": reward,
        "chat_id": chat_id, "answered": []
    }

    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃    🧩  RIDDLE TIME  🧩    ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   💎  Prize:  {reward} pts\n\n"
        "   ─────────────────────────\n\n"
        f"   ❓  {riddle['q']}\n\n"
        "   ─────────────────────────\n\n"
        "   ⚡  First correct answer wins!\n"
        "   ⏰  Time:  90 seconds"
    )

    m = types.InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(opts):
        labels = ["🅰️", "🅱️", "🅲", "🅳"]
        m.add(types.InlineKeyboardButton(
            f"{labels[i]}  {opt}",
            callback_data=f"ra_{comp_id}_{i}"))

    # Store option mapping
    active_competitions[comp_id]["options"] = opts

    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

    def timeout():
        time.sleep(90)
        if comp_id in active_competitions:
            ans = active_competitions[comp_id]["answer"]
            del active_competitions[comp_id]
            try:
                bot.send_message(chat_id,
                    f"⏰  Time's up!\n✅  Answer:  {ans}")
            except:
                pass

    threading.Thread(target=timeout, daemon=True).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith("ra_"))
def handle_riddle_answer(call):
    uid = str(call.from_user.id)

    parts = call.data.split("_")
    # ra_r_CHATID_TIME_INDEX
    comp_id = f"{parts[1]}_{parts[2]}_{parts[3]}"
    opt_index = int(parts[4])

    if comp_id not in active_competitions:
        bot.answer_callback_query(call.id, "⏰ Ended!")
        return

    comp = active_competitions[comp_id]

    if uid in comp["answered"]:
        bot.answer_callback_query(call.id, "❌ Already answered!")
        return

    comp["answered"].append(uid)

    selected = comp["options"][opt_index]

    if selected == comp["answer"]:
        reward = comp["reward"]
        del active_competitions[comp_id]

        update_user_data(uid, points=reward, accumulated_points=reward)
        update_user_rank_and_quests(uid)
        u = get_user(uid) or {}
        record_win("riddle", uid, u.get("username", "N/A"), reward)

        try:
            bot.edit_message_text(
                "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                "┃   🎊  RIDDLE SOLVED!  🎊   ┃\n"
                "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"   🏆  Winner:  @{u.get('username', 'N/A')}\n"
                f"   ✅  Answer:  {comp['answer']}\n"
                f"   💎  Prize:  +{reward} pts\n\n"
                "   🎉  Well played!",
                call.message.chat.id, call.message.message_id,
                parse_mode="HTML")
        except:
            pass

        bot.answer_callback_query(call.id, f"🎊 You won +{reward} pts!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ Wrong!")


# =====================================================
# ⚡ Word Race Competition
# =====================================================
def launch_speed(chat_id):
    word_data = random.choice(SPEED_WORDS)
    word = word_data["word"]
    hint = word_data["hint"]
    scrambled = scramble_word(word)
    reward = bot_config.get("competitions", {}).get("settings", {}).get("speed_reward", 25)

    comp_id = f"s_{chat_id}_{int(time.time())}"

    active_competitions[comp_id] = {
        "type": "speed", "answer": word, "reward": reward,
        "chat_id": chat_id
    }

    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃    ⚡  WORD RACE  ⚡    ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"   💎  Prize:  {reward} pts\n"
        f"   💡  Hint:  {hint}\n\n"

        "   ─────────────────────────\n\n"
        f"   🔤  Unscramble:\n\n"
        f"      [  {scrambled}  ]\n\n"
        "   ─────────────────────────\n\n"

        "   ✍️  Type the correct word!\n"
        "   ⚡  First correct answer wins!\n"
        "   ⏰  Time:  45 seconds"
    )

    bot.send_message(chat_id, msg, parse_mode="HTML")

    def timeout():
        time.sleep(45)
        if comp_id in active_competitions:
            ans = active_competitions[comp_id]["answer"]
            del active_competitions[comp_id]
            try:
                bot.send_message(chat_id,
                    f"⏰  Time's up!\n🔤  Word:  {ans}")
            except:
                pass

    threading.Thread(target=timeout, daemon=True).start()


@bot.message_handler(func=lambda m: any(
    c["type"] == "speed" and c["chat_id"] == m.chat.id
    for c in active_competitions.values()
))
def handle_speed_answer(message):
    uid = str(message.from_user.id)
    text = message.text.strip().upper()
    chat_id = message.chat.id

    target_id = None
    target_comp = None
    for cid, comp in active_competitions.items():
        if comp["type"] == "speed" and comp["chat_id"] == chat_id:
            target_id = cid
            target_comp = comp
            break

    if not target_comp:
        return

    if text == target_comp["answer"]:
        reward = target_comp["reward"]
        del active_competitions[target_id]

        update_user_data(uid, points=reward, accumulated_points=reward)
        update_user_rank_and_quests(uid)
        u = get_user(uid) or {}
        record_win("speed", uid, u.get("username", "N/A"), reward)

        bot.reply_to(message,
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃   🎊  CORRECT!  🎊   ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"   🏆  Winner:  @{u.get('username', 'N/A')}\n"
            f"   🔤  Word:  {target_comp['answer']}\n"
            f"   💎  Prize:  +{reward} pts\n\n"
            "   ⚡  Lightning fast!",
            parse_mode="HTML")


# =====================================================
# Record + History + Settings
# =====================================================
def record_win(comp_type, uid, username, reward):
    history = bot_config.get("competitions", {}).get("history", [])
    history.append({
        "type": comp_type, "winner": uid,
        "username": username, "reward": reward,
        "time": datetime.now().isoformat()
    })
    bot_config["competitions"]["history"] = history[-50:]
    bot_config["competitions"]["stats"]["total_competitions"] += 1
    bot_config["competitions"]["stats"]["total_winners"] += 1
    bot_config["competitions"]["stats"]["total_prizes"] += reward
    save_json(DB_CONFIG, bot_config)


def show_history(chat_id, msg_id=None):
    history = bot_config.get("competitions", {}).get("history", [])

    if not history:
        msg = "📭  No winners yet"
    else:
        msg = (
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃    📜  WINNERS HISTORY  📜    ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        )
        icons = {"math": "🧮", "riddle": "🧩", "speed": "⚡"}
        for e in reversed(history[-10:]):
            icon = icons.get(e.get("type", ""), "🏆")
            msg += (
                f"  {icon}  @{e.get('username', '?')[:12]}"
                f"  │  +{e.get('reward', 0)} pts"
                f"  │  {e.get('time', '')[:10]}\n"
            )

    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="cmp_back"))

    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


def show_settings(chat_id, msg_id=None):
    s = bot_config.get("competitions", {}).get("settings", {})

    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃   ⚙️  REWARD SETTINGS  ⚙️   ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"  🧮  Math:  {s.get('math_reward_min', 10)} – {s.get('math_reward_max', 50)} pts\n"
        f"  🧩  Riddle:  {s.get('riddle_reward', 30)} pts\n"
        f"  ⚡  Speed:  {s.get('speed_reward', 25)} pts"
    )

    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🧮 ➕", callback_data="cmps_math_up"),
        types.InlineKeyboardButton("🧮 ➖", callback_data="cmps_math_down")
    )
    m.add(
        types.InlineKeyboardButton("🧩 ➕", callback_data="cmps_riddle_up"),
        types.InlineKeyboardButton("🧩 ➖", callback_data="cmps_riddle_down")
    )
    m.add(
        types.InlineKeyboardButton("⚡ ➕", callback_data="cmps_speed_up"),
        types.InlineKeyboardButton("⚡ ➖", callback_data="cmps_speed_down")
    )
    m.add(types.InlineKeyboardButton("🔙 Back", callback_data="cmp_back"))

    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except:
            pass
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cmps_"))
def handle_settings_cb(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return

    data = call.data
    s = bot_config.get("competitions", {}).get("settings", {})

    if "math_up" in data:
        s["math_reward_max"] = s.get("math_reward_max", 50) + 10
        s["math_reward_min"] = s.get("math_reward_min", 10) + 5
    elif "math_down" in data:
        s["math_reward_max"] = max(10, s.get("math_reward_max", 50) - 10)
        s["math_reward_min"] = max(5, s.get("math_reward_min", 10) - 5)
    elif "riddle_up" in data:
        s["riddle_reward"] = s.get("riddle_reward", 30) + 10
    elif "riddle_down" in data:
        s["riddle_reward"] = max(5, s.get("riddle_reward", 30) - 10)
    elif "speed_up" in data:
        s["speed_reward"] = s.get("speed_reward", 25) + 5
    elif "speed_down" in data:
        s["speed_reward"] = max(5, s.get("speed_reward", 25) - 5)

    bot_config["competitions"]["settings"] = s
    save_json(DB_CONFIG, bot_config)
    bot.answer_callback_query(call.id, "✅")
    show_settings(call.message.chat.id, call.message.message_id)


# =====================================================
# Done
# =====================================================
print("=" * 55)
print("✅ bot10.py — Competitions + Premium UI")
print("🧮 Math Challenge:  /comp")
print("🧩 Riddle:  Active")
print("⚡ Word Race:  Active")
print("📖 Commands Guide:  /pp")
print("=" * 55)
