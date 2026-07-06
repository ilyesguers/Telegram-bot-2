import json
import os
from config import *

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

users = load_json(DB_USERS, {})
keys_store = load_json(DB_KEYS, {})
redeem_codes = load_json(DB_REDEEM, {})
prices_config = load_json(DB_PRICES, {})
bot_config = load_json(DB_CONFIG, {
    "maintenance": False, 
    "discount": 0, 
    "invite_reward": 5, 
    "daily_bonus": 10,
    "total_sales": 0,
    "total_earnings": 0,
    "sales_log": [],
    "tickets": {},
    "product_requests": {},
    "temp_req": {}
})

# تفعيل الإعدادات التلقائية للميزات الجديدة والمهام الديناميكية بقاعدة البيانات
if "lootbox_price" not in bot_config: bot_config["lootbox_price"] = 50
if "lootbox_chance" not in bot_config: bot_config["lootbox_chance"] = 25
if "wheel_price" not in bot_config: bot_config["wheel_price"] = 40
if "wheel_chance" not in bot_config: bot_config["wheel_chance"] = 5
if "quests" not in bot_config:
    bot_config["quests"] = {
        "invite": {"target": 15, "reward": 150},
        "buy": {"target": 7, "reward": 200},
        "points": {"target": 5000, "reward": 350}
    }
save_json(DB_CONFIG, bot_config)

def register_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "username": user.username or f"User_{uid}",
            "points": 0,
            "invited_by": None,
            "invite_count": 0,
            "last_claim": None,
            "lang": "ar",
            "banned": False,
            "banned_until": None,
            "is_admin": uid in [str(ADMIN_PRIMARY), str(ADMIN_SECONDARY)],
            "rank": "عضو عادي 🔹",
            "rank_discount": 0.0,
            "accumulated_points": 0,
            "completed_quests": []
        }
        save_json(DB_USERS, users)
    else:
        updated = False
        if "rank" not in users[uid]:
            users[uid]["rank"] = "عضو عادي 🔹"
            users[uid]["rank_discount"] = 0.0
            updated = True
        if "accumulated_points" not in users[uid]:
            users[uid]["accumulated_points"] = users[uid].get("points", 0)
            updated = True
        if "completed_quests" not in users[uid]:
            users[uid]["completed_quests"] = []
            updated = True
        if updated: save_json(DB_USERS, users)

def update_user_rank_and_quests(uid):
    uid = str(uid)
    if uid not in users: return
    u = users[uid]
    
    acc_pts = u.get("accumulated_points", 0)
    current_rank = "عضو عادي 🔹"
    current_discount = 0.0
    for r_key, r_val in RANKS.items():
        if acc_pts >= r_val["points_needed"]:
            current_rank = r_val["name"]
            current_discount = r_val["discount"]
    u["rank"] = current_rank
    u["rank_discount"] = current_discount
    
    completed = u.get("completed_quests", [])
    q = bot_config.get("quests")
    
    if "quest_invite" not in completed and u.get("invite_count", 0) >= q["invite"]["target"]:
        completed.append("quest_invite")
        u["points"] += q["invite"]["reward"]
        u["accumulated_points"] += q["invite"]["reward"]
        try: bot.send_message(int(uid), f"🎉 تهانينا! لقد أنجزت مهمة الدعوات بنجاح:\n👥 دعوة {q['invite']['target']} صديق\n🎁 تم إضافة مكافأتك: <b>+{q['invite']['reward']} نقطة!</b>", parse_mode="HTML")
        except: pass
        
    user_buys = sum(1 for x in bot_config.get("sales_log", []) if str(x.get("uid")) == uid)
    if "quest_buy" not in completed and user_buys >= q["buy"]["target"]:
        completed.append("quest_buy")
        u["points"] += q["buy"]["reward"]
        u["accumulated_points"] += q["buy"]["reward"]
        try: bot.send_message(int(uid), f"🎉 تهانينا! لقد أنجزت مهمة المشتريات بنجاح:\n🛒 إتمام {q['buy']['target']} عمليات شراء\n🎁 تم إضافة مكافأتك: <b>+{q['buy']['reward']} نقطة!</b>", parse_mode="HTML")
        except: pass
        
    if "quest_points" not in completed and acc_pts >= q["points"]["target"]:
        completed.append("quest_points")
        u["points"] += q["points"]["reward"]
        u["accumulated_points"] += q["points"]["reward"]
        try: bot.send_message(int(uid), f"🎉 تهانينا! لقد أنجزت مهمة النقاط التراكمية بنجاح:\n💎 تجميع {q['points']['target']} نقطة\n🎁 تم إضافة مكافأتك: <b>+{q['points']['reward']} نقطة!</b>", parse_mode="HTML")
        except: pass
        
    u["completed_quests"] = completed
    save_json(DB_USERS, users)
