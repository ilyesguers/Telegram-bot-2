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
from utils import generate_captcha

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
# GIVEAWAY SYSTEM
# =====================================================

def generate_giveaway_code():
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

def create_giveaway(reward, max_users, hours):
    code = generate_giveaway_code()
    expires = datetime.now() + timedelta(hours=hours)
    bot_config["giveaways"][code] = {
        "code": code, "reward": reward, "max_users": max_users, "hours": hours,
        "expires": expires.isoformat(), "created": datetime.now().isoformat(),
        "claimed_by": [], "status": "active"
    }
    save_json(DB_CONFIG, bot_config)
    return code

def get_giveaway(code):
    return bot_config.get("giveaways", {}).get(code)

def is_giveaway_valid(code):
    gw = get_giveaway(code)
    if not gw:
        return False, "not_found"
    if gw.get("status") != "active":
        return False, "inactive"
    try:
        if datetime.now() > datetime.fromisoformat(gw["expires"]):
            gw["status"] = "expired"
            save_json(DB_CONFIG, bot_config)
            return False, "expired"
    except:
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
    if "claimed_by" not in gw:
        gw["claimed_by"] = []
    gw["claimed_by"].append(str(uid))
    if len(gw["claimed_by"]) >= gw["max_users"]:
        gw["status"] = "full"
    save_json(DB_CONFIG, bot_config)
    return True

def publish_giveaway_to_channel(code):
    gw = get_giveaway(code)
    if not gw:
        return None
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    link = f"https://t.me/{bot_user}?start=gw_{code}"
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  🎁 GIVEAWAY! 🎁  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"🎊 FREE PRIZE! 🎊\n\n"
        f"💎 Prize: {gw['reward']} points\n"
        f"👥 Winners: {gw['max_users']}\n"
        f"⏰ Duration: {gw['hours']}h"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🎁 CLAIM NOW", url=link))
    try:
        sent = bot.send_message(CHANNEL_ID, msg, reply_markup=m, parse_mode="HTML")
        gw["channel_msg_id"] = sent.message_id
        save_json(DB_CONFIG, bot_config)
        return sent.message_id
    except:
        return None

def start_giveaway_captcha(uid, code):
    u = get_user(str(uid)) or {}
    lang = u.get("lang", "en")
    emoji, name, opts = generate_captcha(lang)
    bot_config["giveaway_captchas"][str(uid)] = {
        "code": code, "answer": emoji, "attempts": 0,
        "expires": (datetime.now() + timedelta(minutes=5)).isoformat()
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
    except: pass

def verify_giveaway_captcha(uid, answer):
    uid = str(uid)
    sessions = bot_config.get("giveaway_captchas", {})
    if uid not in sessions:
        return "no_session", None
    session = sessions[uid]
    try:
        if datetime.now() > datetime.fromisoformat(session["expires"]):
            del sessions[uid]
            save_json(DB_CONFIG, bot_config)
            return "expired", None
    except: pass
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

def process_giveaway_claim(uid, code):
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
    return True, reward

def get_all_giveaways():
    return bot_config.get("giveaways", {})

def cancel_giveaway(code):
    gw = get_giveaway(code)
    if not gw:
        return False
    gw["status"] = "cancelled"
    save_json(DB_CONFIG, bot_config)
    msg_id = gw.get("channel_msg_id")
    if msg_id:
        try: bot.delete_message(CHANNEL_ID, msg_id)
        except: pass
    return True

def get_giveaways_stats():
    gws = get_all_giveaways()
    return {
        "total": len(gws),
        "active": sum(1 for g in gws.values() if g.get("status") == "active"),
        "expired": sum(1 for g in gws.values() if g.get("status") == "expired"),
        "full": sum(1 for g in gws.values() if g.get("status") == "full"),
        "cancelled": sum(1 for g in gws.values() if g.get("status") == "cancelled"),
        "total_claimed": sum(len(g.get("claimed_by", [])) for g in gws.values()),
        "total_points_given": sum(g.get("reward", 0) * len(g.get("claimed_by", [])) for g in gws.values())
    }

# =====================================================
# CHANNEL MESSAGES
# =====================================================

def send_custom_channel_message(text):
    try:
        formatted = (
            f"╔═══════════════════════╗\n"
            f"║  📢 NOTICE 📢   ║\n"
            f"╚═══════════════════════╝\n\n"
            f"{text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 Official Announcement"
        )
        sent = bot.send_message(CHANNEL_ID, formatted, parse_mode="HTML")
        return sent.message_id
    except:
        return None

def send_raw_channel_message(text):
    try:
        sent = bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
        return sent.message_id
    except:
        return None

def delete_channel_message(msg_id):
    try:
        bot.delete_message(CHANNEL_ID, int(msg_id))
        return True
    except:
        return False

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

def publish_vip_purchase_to_channel():
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    hooks = [
        "👑 <b>NEW VIP MEMBER!</b>",
        "💎 <b>VIP UPGRADED!</b>",
        "⭐ <b>EXCLUSIVE MEMBER!</b>",
        "🎊 <b>ANOTHER HAPPY VIP!</b>"
    ]
    hook = random.choice(hooks)
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ {hook} \n"
        f"╚═══════════════════════╝\n\n"
        f"🎉 A user just joined VIP club!\n\n"
        f"💎 Exclusive Benefits:\n"
        f"├── 🎁 2x Daily bonus\n"
        f"├── 💰 15% off everything\n"
        f"├── 📊 Advanced stock info\n"
        f"├── 🎫 Weekly free code\n"
        f"├── ⚡ Priority support\n"
        f"└── 👑 VIP badge\n\n"
        f"🌟 <b>Join VIP now:</b>\n"
        f"🤖 t.me/{bot_user}"
    )
    try:
        bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
    except: pass

def publish_stars_conversion_to_channel(stars_amount, points_amount):
    try:
        bot_user = bot.get_me().username
    except:
        bot_user = "bot"
    hooks = [
        "⭐ <b>NEW CONVERSION!</b>",
        "💫 <b>STARS TO POINTS!</b>",
        "🌟 <b>SMART TRADE!</b>"
    ]
    hook = random.choice(hooks)
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ {hook} \n"
        f"╚═══════════════════════╝\n\n"
        f"⚡ Instant conversion completed!\n\n"
        f"⭐ Stars used: <b>{stars_amount}</b>\n"
        f"💎 Points received: <b>{points_amount}</b>\n"
        f"✅ Status: Delivered\n\n"
        f"🌟 <b>Convert now:</b>\n"
        f"🤖 t.me/{bot_user}"
    )
    try:
        bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
    except: pass

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
        publish_vip_purchase_to_channel()
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
        publish_stars_conversion_to_channel(stars, points)
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
print("=" * 50)
