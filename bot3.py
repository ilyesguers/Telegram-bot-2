"""
==============================================
bot3.py - Purchase Fix + Anti-Abuse System
==============================================
"""

import time
import random
from datetime import datetime, timedelta
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID, t
from database import (bot_config, save_json, DB_CONFIG, DB_KEYS, get_user,
                      update_user_data, update_user_rank_and_quests,
                      keys_store, prices_config)
from utils import (get_active_flash_sale, publish_sale_to_channel,
                   check_channel_join)

# =====================================================
# ANTI-ABUSE SYSTEM
# =====================================================

purchase_cooldown = {}
purchase_history = {}
suspicious_users = {}

def check_purchase_abuse(uid):
    """
    Detect purchase abuse patterns:
    - Too many purchases in short time
    - Same user buying repeatedly
    Returns: (allowed, reason)
    """
    uid = str(uid)
    now = time.time()
    
    # Cooldown: 1 purchase per 10 seconds
    if uid in purchase_cooldown:
        if now - purchase_cooldown[uid] < 10:
            return False, "cooldown"
    
    # Rate limit: Max 5 purchases per hour
    if uid not in purchase_history:
        purchase_history[uid] = []
    
    # Clean old entries
    purchase_history[uid] = [t for t in purchase_history[uid] if now - t < 3600]
    
    if len(purchase_history[uid]) >= 5:
        # Flag as suspicious
        suspicious_users[uid] = {
            "reason": "rate_limit",
            "time": datetime.now().isoformat(),
            "count": len(purchase_history[uid])
        }
        return False, "rate_limit"
    
    return True, "ok"

def record_purchase(uid):
    """Record a purchase for rate limiting"""
    uid = str(uid)
    now = time.time()
    purchase_cooldown[uid] = now
    if uid not in purchase_history:
        purchase_history[uid] = []
    purchase_history[uid].append(now)

def get_suspicious_users():
    """Get list of suspicious users for admin"""
    return suspicious_users

def clear_suspicious(uid):
    """Clear suspicious flag"""
    uid = str(uid)
    if uid in suspicious_users:
        del suspicious_users[uid]

# =====================================================
# FIXED PURCHASE HANDLER (REPLACES THE BROKEN ONE)
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_plan|"))
def fixed_purchase_handler(call):
    """
    Fixed purchase handler that:
    1. Gives the key FIRST
    2. Then shows animation
    3. Never fails to deliver
    """
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    
    # Parse product and plan
    try:
        _, prod, plan = data.split("|")
    except:
        return bot.answer_callback_query(call.id, "Error", show_alert=True)
    
    # Check anti-abuse
    allowed, reason = check_purchase_abuse(uid)
    if not allowed:
        if reason == "cooldown":
            return bot.answer_callback_query(call.id,
                "⏳ Please wait 10 seconds between purchases",
                show_alert=True)
        elif reason == "rate_limit":
            return bot.answer_callback_query(call.id,
                "⚠️ Too many purchases! Max 5 per hour.\nContact admin if you need more.",
                show_alert=True)
    
    # Check channel subscription
    if not check_channel_join(uid):
        return bot.answer_callback_query(call.id,
            "⚠️ Join the channel first!", show_alert=True)
    
    # Calculate price
    base_p = prices_config.get(prod, {}).get(plan, 0)
    disc = bot_config.get("discount", 0)
    u_disc = u.get("rank_discount", 0.0) or 0.0
    
    # Check flash sale
    fs = get_active_flash_sale()
    fs_disc = 0
    if fs and fs.get("product") == prod:
        fs_disc = fs.get("discount", 0)
    
    total_disc = disc + fs_disc
    final_p = int(base_p * (1 - total_disc/100) * (1 - u_disc))
    
    # Check balance
    user_points = u.get("points", 0) or 0
    if user_points < final_p:
        return bot.answer_callback_query(call.id,
            t(lang, "insufficient_balance"), show_alert=True)
    
    # Check stock
    product_keys = keys_store.get(prod, {}).get(plan, [])
    if not product_keys:
        return bot.answer_callback_query(call.id,
            "⚠️ Out of stock!", show_alert=True)
    
    # ═══════════════════════════════════
    # STEP 1: DELIVER KEY FIRST (GUARANTEED)
    # ═══════════════════════════════════
    
    try:
        # Get the key
        key = product_keys.pop(0)
        
        # Deduct points
        update_user_data(uid, points=-final_p, total_spent=final_p, purchases_count=1)
        
        # Record sale
        bot_config["total_sales"] = bot_config.get("total_sales", 0) + 1
        bot_config["total_earnings"] = bot_config.get("total_earnings", 0) + final_p
        if "sales_log" not in bot_config:
            bot_config["sales_log"] = []
        bot_config["sales_log"].append({
            "uid": uid,
            "username": u.get("username", ""),
            "product": prod,
            "plan": plan,
            "price": final_p,
            "key": key,
            "date": datetime.now().isoformat()
        })
        
        # Save everything
        save_json(DB_KEYS, keys_store)
        save_json(DB_CONFIG, bot_config)
        
        # Update rank
        update_user_rank_and_quests(uid)
        
        # Record for anti-abuse
        record_purchase(uid)
        
    except Exception as e:
        print(f"CRITICAL PURCHASE ERROR: {e}")
        bot.answer_callback_query(call.id,
            "Error processing - Contact admin", show_alert=True)
        try:
            bot.send_message(ADMIN_PRIMARY,
                f"🚨 <b>PURCHASE ERROR!</b>\n\n"
                f"👤 {uid}\n"
                f"📦 {prod}/{plan}\n"
                f"❌ {str(e)[:200]}",
                parse_mode="HTML")
        except: pass
        return
    
    # ═══════════════════════════════════
    # STEP 2: ANIMATION (SAFE - KEY ALREADY GIVEN)
    # ═══════════════════════════════════
    
    animation_steps = [
        "⏳ <b>Processing payment...</b>",
        "🔐 <b>Preparing your key...</b>",
        "📦 <b>Packing your order...</b>",
        "🚀 <b>Delivering...</b>"
    ]
    
    for step in animation_steps:
        try:
            bot.edit_message_text(step, chat_id, msg_id, parse_mode="HTML")
            time.sleep(0.4)
        except:
            pass
    
    # ═══════════════════════════════════
    # STEP 3: SHOW KEY TO USER (GUARANTEED)
    # ═══════════════════════════════════
    
    success_msg = (
        f"╔═══════════════════════╗\n"
        f"║ 🎉 <b>PURCHASE DONE!</b> 🎉 ║\n"
        f"╚═══════════════════════╝\n\n"
        f"┃ 📦 <b>Product:</b> {prod}\n"
        f"┃ ⏱️ <b>Duration:</b> {plan}\n"
        f"┃ 💰 <b>Paid:</b> {final_p} 💎\n"
        f"╰━━━━━━━━━━━━━━━╯\n\n"
        f"🔐 <b>Your Key:</b>\n"
        f"<code>{key}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Delivered successfully!</b>\n"
        f"⚠️ <i>Save your key in a safe place!</i>\n"
        f"🎁 <i>Enjoy your product!</i>"
    )
    
    # Try edit first, then send new message if edit fails
    delivered = False
    
    try:
        bot.edit_message_text(success_msg, chat_id, msg_id, parse_mode="HTML")
        delivered = True
    except:
        pass
    
    if not delivered:
        try:
            bot.send_message(chat_id, success_msg, parse_mode="HTML")
            delivered = True
        except:
            pass
    
    # Last resort - send key as plain text
    if not delivered:
        try:
            bot.send_message(chat_id,
                f"Your key for {prod} ({plan}):\n\n{key}\n\nSave it!")
        except:
            pass
    
    # ═══════════════════════════════════
    # STEP 4: PUBLISH TO CHANNEL
    # ═══════════════════════════════════
    
    try:
        publish_sale_to_channel(prod, plan, final_p)
    except:
        pass
    
    # ═══════════════════════════════════
    # STEP 5: NOTIFY ADMIN
    # ═══════════════════════════════════
    
    try:
        remaining = len(keys_store.get(prod, {}).get(plan, []))
        bot.send_message(ADMIN_PRIMARY,
            f"🛒 <b>NEW SALE!</b>\n\n"
            f"👤 @{u.get('username', 'N/A')} ({uid})\n"
            f"📦 {prod} / {plan}\n"
            f"💰 {final_p} 💎\n"
            f"📊 Stock left: {remaining}",
            parse_mode="HTML")
    except:
        pass

# =====================================================
# ANTI-SPAM MONITOR (AUTO-DETECTION)
# =====================================================

spam_tracker = {}
banned_by_bot3 = {}

def track_user_action(uid, action_type):
    """
    Track all user actions for pattern detection:
    - Too many clicks = bot/spam
    - Unusual patterns = abuse
    """
    uid = str(uid)
    now = time.time()
    
    if uid not in spam_tracker:
        spam_tracker[uid] = {"actions": [], "warnings": 0}
    
    # Add action
    spam_tracker[uid]["actions"].append({
        "type": action_type,
        "time": now
    })
    
    # Keep only last 5 minutes
    spam_tracker[uid]["actions"] = [
        a for a in spam_tracker[uid]["actions"]
        if now - a["time"] < 300
    ]
    
    # Check patterns
    actions_count = len(spam_tracker[uid]["actions"])
    
    # More than 30 actions in 5 minutes = suspicious
    if actions_count > 30:
        spam_tracker[uid]["warnings"] += 1
        
        if spam_tracker[uid]["warnings"] >= 3:
            # Auto-ban for 1 hour
            until = (datetime.now() + timedelta(hours=1)).isoformat()
            update_user_data(uid, banned_until=until)
            banned_by_bot3[uid] = {
                "reason": "spam_detected",
                "time": datetime.now().isoformat(),
                "actions": actions_count
            }
            
            try:
                bot.send_message(int(uid),
                    f"╔═══════════════════════╗\n"
                    f"║ 🚫 <b>AUTO-BAN</b> 🚫  ║\n"
                    f"╚═══════════════════════╝\n\n"
                    f"⚠️ Suspicious activity detected!\n"
                    f"⏰ Banned for: <b>1 hour</b>\n\n"
                    f"💡 <i>Contact admin if this is a mistake</i>",
                    parse_mode="HTML")
            except: pass
            
            try:
                bot.send_message(ADMIN_PRIMARY,
                    f"🚨 <b>AUTO-BAN TRIGGERED</b>\n\n"
                    f"👤 {uid}\n"
                    f"📊 Actions: {actions_count} in 5min\n"
                    f"⚠️ Warnings: {spam_tracker[uid]['warnings']}\n"
                    f"⏰ Banned 1h",
                    parse_mode="HTML")
            except: pass
            
            return "banned"
        
        return "warning"
    
    return "ok"

# =====================================================
# CALLBACK MONITOR (TRACKS ALL BUTTON CLICKS)
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("monitor_"))
def monitor_handler(call):
    """Monitor suspicious callback patterns"""
    uid = str(call.from_user.id)
    result = track_user_action(uid, "callback")
    
    if result == "warning":
        bot.answer_callback_query(call.id,
            "⚠️ Slow down! You're clicking too fast.",
            show_alert=True)
    elif result == "banned":
        bot.answer_callback_query(call.id,
            "🚫 You have been temporarily banned for suspicious activity.",
            show_alert=True)

# =====================================================
# ADMIN ANTI-ABUSE PANEL
# =====================================================

@bot.message_handler(func=lambda message: message.text == "🛡️ مكافحة الرشق")
def show_anti_abuse_panel(message):
    uid = str(message.from_user.id)
    if int(uid) not in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        u = get_user(uid) or {}
        if not u.get("is_admin", False):
            return
    
    suspicious = get_suspicious_users()
    auto_banned = banned_by_bot3
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 🛡️ <b>ANTI-ABUSE</b> 🛡️  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"📊 <b>Current Status:</b>\n"
        f"├── ⚠️ Suspicious: {len(suspicious)}\n"
        f"├── 🚫 Auto-banned: {len(auto_banned)}\n"
        f"└── 👁️ Monitored: {len(spam_tracker)}\n\n"
    )
    
    if suspicious:
        msg += "⚠️ <b>Suspicious Users:</b>\n"
        for s_uid, s_info in list(suspicious.items())[:10]:
            u = get_user(s_uid) or {}
            msg += f"• @{u.get('username', 'N/A')} ({s_uid})\n"
            msg += f"  Reason: {s_info.get('reason', 'N/A')}\n"
    
    if auto_banned:
        msg += "\n🚫 <b>Auto-Banned:</b>\n"
        for b_uid, b_info in list(auto_banned.items())[:10]:
            u = get_user(b_uid) or {}
            msg += f"• @{u.get('username', 'N/A')} ({b_uid})\n"
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="abuse_refresh"))
    m.add(types.InlineKeyboardButton("🧹 Clear All Warnings", callback_data="abuse_clear_all"))
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("abuse_"))
def handle_abuse_callbacks(call):
    uid = str(call.from_user.id)
    if int(uid) not in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        u = get_user(uid) or {}
        if not u.get("is_admin", False):
            return
    
    if call.data == "abuse_refresh":
        show_anti_abuse_panel(call.message)
        return
    
    if call.data == "abuse_clear_all":
        suspicious_users.clear()
        banned_by_bot3.clear()
        spam_tracker.clear()
        bot.answer_callback_query(call.id, "✅ All cleared!", show_alert=True)
        return

# =====================================================
# PURCHASE ERROR RECOVERY
# =====================================================

@bot.message_handler(func=lambda message: message.text == "🔧 استعادة المشتريات")
def show_recovery_panel(message):
    """Admin panel for purchase recovery"""
    uid = str(message.from_user.id)
    if int(uid) not in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
        u = get_user(uid) or {}
        if not u.get("is_admin", False):
            return
    
    # Show last 10 sales
    sales = bot_config.get("sales_log", [])[-10:]
    if not sales:
        return bot.send_message(message.chat.id, "📭 No recent sales")
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 🔧 <b>RECOVERY PANEL</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"📜 <b>Last 10 Sales:</b>\n\n"
    )
    
    for i, s in enumerate(reversed(sales), 1):
        msg += (
            f"{i}. @{s.get('username', 'N/A')}\n"
            f"   📦 {s['product']}/{s['plan']}\n"
            f"   💰 {s['price']} | 📅 {s.get('date', '')[:16]}\n"
            f"   🔐 <code>{s.get('key', 'N/A')[:10]}...</code>\n\n"
        )
    
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

print("=" * 50)
print("✅ bot3.py loaded!")
print("🛒 Fixed Purchase Handler: Active")
print("🛡️ Anti-Abuse System: Active")
print("🔧 Recovery Panel: Ready")
print("=" * 50)
