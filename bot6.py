"""
══════════════════════════════════════════════════════════════════════════════
║                bot6.py - SMART SHIELD SYSTEM v3.0                           ║
║           🛡️ نظام الحماية الذكي من الراشقين والحسابات الوهمية                ║
║              AI-Powered Anti-Abuse Detection System                         ║
══════════════════════════════════════════════════════════════════════════════
║  Developer: @fkLJh00302                                                     ║
║  Features:                                                                   ║
║   ✅ كشف الحسابات الوهمية بذكاء (لا ظلم للمستخدمين الحقيقيين)                 ║
║   ✅ تحليل أنماط السلوك المشبوه                                               ║
║   ✅ حماية من الرشق (Multi-Account Abuse)                                    ║
║   ✅ حماية من الـ Bot Spam                                                   ║
║   ✅ نظام نقاط الثقة (Trust Score)                                           ║
║   ✅ حظر ذكي تلقائي مع إمكانية الاستئناف                                      ║
══════════════════════════════════════════════════════════════════════════════
"""

import time
import re
import hashlib
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, t
from database import (engine, text, get_user, update_user_data, bot_config, 
                     save_json, DB_CONFIG)

# ═══════════════════════════════════════════════════════════════════════════
# 📊 التكوين والثوابت
# ═══════════════════════════════════════════════════════════════════════════

# عتبات الكشف (قابلة للتعديل)
DETECTION_CONFIG = {
    # حدود السلوك
    "max_actions_per_minute": 30,        # الحد الأقصى للأفعال في الدقيقة
    "max_daily_bonus_attempts": 3,       # محاولات المكافأة اليومية
    "max_failed_captcha": 5,             # محاولات الكابتشا الفاشلة
    "min_account_age_days": 0,           # عمر الحساب الأدنى (0 = لا قيود)
    "suspicious_username_patterns": [    # أنماط أسماء مشبوهة
        r"^user\d{6,}$",
        r"^[a-z]{2,3}\d{8,}$",
        r"^\d{10,}$"
    ],
    
    # نقاط الثقة
    "initial_trust_score": 50,           # النقاط الابتدائية
    "trust_threshold_low": 20,           # عتبة الثقة المنخفضة
    "trust_threshold_ban": 10,           # عتبة الحظر التلقائي
    
    # العقوبات
    "warning_cooldown_minutes": 5,       # مدة التهدئة بعد التحذير
    "temp_ban_hours": 24,                # مدة الحظر المؤقت
    "permanent_ban_threshold": 3,        # عدد الحظورات للحظر الدائم
    
    # الإحالات
    "max_referrals_per_hour": 5,         # الحد الأقصى للإحالات في الساعة
    "referral_cooldown_seconds": 60,     # التهدئة بين الإحالات
    "same_device_referral_block": True,  # منع الإحالة من نفس الجهاز
}

# ═══════════════════════════════════════════════════════════════════════════
# 🗄️ تخزين مؤقت للتتبع
# ═══════════════════════════════════════════════════════════════════════════

# تتبع الأفعال
user_actions = defaultdict(list)           # {uid: [(action, timestamp), ...]}
user_warnings = defaultdict(int)           # {uid: warning_count}
user_trust_scores = {}                      # {uid: score}
user_fingerprints = {}                      # {uid: fingerprint}
referral_timestamps = defaultdict(list)    # {uid: [timestamps]}
suspicious_patterns = defaultdict(list)    # {uid: [patterns]}
captcha_failures = defaultdict(int)        # {uid: count}
device_fingerprints = defaultdict(set)     # {fingerprint: set(uids)}

# ذاكرة التخزين المؤقت للحظر
ban_cache = {}                              # {uid: {"until": datetime, "reason": str}}

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 دوال مساعدة
# ═══════════════════════════════════════════════════════════════════════════

def generate_fingerprint(user) -> str:
    """
    إنشاء بصمة فريدة للمستخدم بناءً على معلوماته
    (لا تعتمد على IP لأنها غير متاحة في Bot API)
    """
    data = f"{user.id}:{user.first_name}:{user.last_name}:{user.language_code}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def get_trust_score(uid: str) -> int:
    """جلب نقاط الثقة للمستخدم"""
    uid = str(uid)
    if uid not in user_trust_scores:
        # حساب النقاط الابتدائية
        u = get_user(uid)
        if u:
            score = DETECTION_CONFIG["initial_trust_score"]
            
            # زيادة للحسابات القديمة
            join_date = u.get("join_date")
            if join_date:
                try:
                    days = (datetime.now() - datetime.fromisoformat(join_date)).days
                    score += min(days * 2, 30)  # +2 لكل يوم، حد أقصى 30
                except:
                    pass
            
            # زيادة للمشتريات
            purchases = u.get("purchases_count", 0) or 0
            score += min(purchases * 5, 25)  # +5 لكل شراء، حد أقصى 25
            
            # زيادة للنقاط التراكمية
            acc_points = u.get("accumulated_points", 0) or 0
            if acc_points > 1000:
                score += 10
            
            user_trust_scores[uid] = min(score, 100)
        else:
            user_trust_scores[uid] = DETECTION_CONFIG["initial_trust_score"]
    
    return user_trust_scores[uid]

def modify_trust_score(uid: str, change: int, reason: str = ""):
    """تعديل نقاط الثقة"""
    uid = str(uid)
    current = get_trust_score(uid)
    new_score = max(0, min(100, current + change))
    user_trust_scores[uid] = new_score
    
    # تسجيل التغيير
    if reason:
        suspicious_patterns[uid].append({
            "action": "trust_change",
            "change": change,
            "reason": reason,
            "time": datetime.now().isoformat()
        })
    
    return new_score

def is_suspicious_username(username: str) -> bool:
    """فحص إذا كان اسم المستخدم مشبوه"""
    if not username:
        return False
    
    for pattern in DETECTION_CONFIG["suspicious_username_patterns"]:
        if re.match(pattern, username.lower()):
            return True
    return False

def clean_old_actions(uid: str, minutes: int = 5):
    """تنظيف الأفعال القديمة"""
    uid = str(uid)
    cutoff = time.time() - (minutes * 60)
    user_actions[uid] = [
        (action, ts) for action, ts in user_actions[uid] 
        if ts > cutoff
    ]

# ═══════════════════════════════════════════════════════════════════════════
# 🔍 نظام الكشف الذكي
# ═══════════════════════════════════════════════════════════════════════════

def analyze_user_behavior(uid: str, action: str) -> dict:
    """
    تحليل سلوك المستخدم وإرجاع تقرير
    Returns: {
        "safe": bool,
        "risk_level": "low"|"medium"|"high"|"critical",
        "reasons": [str],
        "action": "allow"|"warn"|"captcha"|"temp_ban"|"ban"
    }
    """
    uid = str(uid)
    now = time.time()
    result = {
        "safe": True,
        "risk_level": "low",
        "reasons": [],
        "action": "allow"
    }
    
    # تسجيل الفعل
    user_actions[uid].append((action, now))
    clean_old_actions(uid)
    
    # 1️⃣ فحص معدل الأفعال
    recent_actions = len(user_actions[uid])
    if recent_actions > DETECTION_CONFIG["max_actions_per_minute"]:
        result["reasons"].append(f"High action rate: {recent_actions}/min")
        result["risk_level"] = "high"
        modify_trust_score(uid, -5, "high_action_rate")
    
    # 2️⃣ فحص نقاط الثقة
    trust = get_trust_score(uid)
    if trust < DETECTION_CONFIG["trust_threshold_ban"]:
        result["safe"] = False
        result["risk_level"] = "critical"
        result["action"] = "ban"
        result["reasons"].append(f"Trust score critical: {trust}")
    elif trust < DETECTION_CONFIG["trust_threshold_low"]:
        result["risk_level"] = "high"
        result["action"] = "captcha"
        result["reasons"].append(f"Trust score low: {trust}")
    
    # 3️⃣ فحص عدد التحذيرات
    warnings = user_warnings[uid]
    if warnings >= DETECTION_CONFIG["permanent_ban_threshold"]:
        result["safe"] = False
        result["risk_level"] = "critical"
        result["action"] = "ban"
        result["reasons"].append(f"Too many warnings: {warnings}")
    elif warnings >= 2:
        result["risk_level"] = "high"
        result["action"] = "temp_ban"
    
    # 4️⃣ فحص أنماط مشبوهة محددة
    patterns = suspicious_patterns[uid]
    recent_suspicious = [
        p for p in patterns 
        if datetime.fromisoformat(p["time"]) > datetime.now() - timedelta(hours=1)
    ]
    if len(recent_suspicious) >= 3:
        result["risk_level"] = "medium" if result["risk_level"] == "low" else result["risk_level"]
        result["reasons"].append(f"Multiple suspicious patterns: {len(recent_suspicious)}")
    
    # تحديد النتيجة النهائية
    if result["risk_level"] == "low":
        result["safe"] = True
        result["action"] = "allow"
    elif result["risk_level"] == "medium":
        result["safe"] = True
        result["action"] = "warn"
    
    return result

def check_referral_abuse(inviter_uid: str, new_user) -> dict:
    """
    فحص إساءة استخدام نظام الإحالة
    Returns: {"allowed": bool, "reason": str}
    """
    inviter_uid = str(inviter_uid)
    new_uid = str(new_user.id)
    now = time.time()
    
    # 1️⃣ فحص معدل الإحالات
    hour_ago = now - 3600
    recent_referrals = [ts for ts in referral_timestamps[inviter_uid] if ts > hour_ago]
    
    if len(recent_referrals) >= DETECTION_CONFIG["max_referrals_per_hour"]:
        modify_trust_score(inviter_uid, -10, "referral_spam")
        return {
            "allowed": False,
            "reason": "referral_rate_limit",
            "message": "Too many referrals per hour"
        }
    
    # 2️⃣ فحص التهدئة
    if recent_referrals:
        last_referral = max(recent_referrals)
        if now - last_referral < DETECTION_CONFIG["referral_cooldown_seconds"]:
            return {
                "allowed": False,
                "reason": "cooldown",
                "message": "Referral cooldown active"
            }
    
    # 3️⃣ فحص البصمة (نفس الجهاز/الشخص)
    if DETECTION_CONFIG["same_device_referral_block"]:
        new_fingerprint = generate_fingerprint(new_user)
        inviter_fp = user_fingerprints.get(inviter_uid)
        
        # فحص إذا كانت البصمة مشابهة جداً
        if inviter_fp and new_fingerprint[:8] == inviter_fp[:8]:
            modify_trust_score(inviter_uid, -20, "self_referral_attempt")
            return {
                "allowed": False,
                "reason": "same_device",
                "message": "Self-referral detected"
            }
        
        # فحص إذا كانت البصمة مستخدمة من قبل
        if new_fingerprint in device_fingerprints:
            existing_uids = device_fingerprints[new_fingerprint]
            if len(existing_uids) >= 2:
                modify_trust_score(inviter_uid, -15, "multi_account_referral")
                return {
                    "allowed": False,
                    "reason": "multi_account",
                    "message": "Multiple accounts from same device"
                }
    
    # 4️⃣ فحص اسم المستخدم المشبوه
    if is_suspicious_username(new_user.username):
        modify_trust_score(inviter_uid, -5, "suspicious_referral")
        # نسمح لكن مع تخفيض النقاط
    
    # ✅ مسموح
    referral_timestamps[inviter_uid].append(now)
    new_fingerprint = generate_fingerprint(new_user)
    device_fingerprints[new_fingerprint].add(new_uid)
    user_fingerprints[new_uid] = new_fingerprint
    
    return {
        "allowed": True,
        "reason": "ok",
        "message": "Referral allowed"
    }

def check_daily_bonus_abuse(uid: str) -> dict:
    """
    فحص إساءة استخدام المكافأة اليومية
    Returns: {"allowed": bool, "reason": str}
    """
    uid = str(uid)
    
    # جلب سجل المحاولات اليوم
    today = datetime.now().date().isoformat()
    attempts_key = f"daily_attempts_{today}"
    
    if attempts_key not in suspicious_patterns[uid]:
        suspicious_patterns[uid].append({
            "action": attempts_key,
            "count": 0,
            "time": datetime.now().isoformat()
        })
    
    # البحث عن سجل اليوم
    for pattern in suspicious_patterns[uid]:
        if pattern.get("action") == attempts_key:
            pattern["count"] = pattern.get("count", 0) + 1
            
            if pattern["count"] > DETECTION_CONFIG["max_daily_bonus_attempts"]:
                modify_trust_score(uid, -3, "daily_bonus_spam")
                return {
                    "allowed": False,
                    "reason": "rate_limit",
                    "message": "Too many attempts today"
                }
            break
    
    return {
        "allowed": True,
        "reason": "ok",
        "message": "Allowed"
    }

# ═══════════════════════════════════════════════════════════════════════════
# 🚫 نظام الحظر الذكي
# ═══════════════════════════════════════════════════════════════════════════

def smart_ban(uid: str, reason: str, duration_hours: int = None) -> dict:
    """
    حظر ذكي مع إمكانية الاستئناف
    """
    uid = str(uid)
    
    # تحديد مدة الحظر
    if duration_hours is None:
        warnings = user_warnings[uid]
        if warnings >= DETECTION_CONFIG["permanent_ban_threshold"]:
            duration_hours = 0  # دائم
        else:
            duration_hours = DETECTION_CONFIG["temp_ban_hours"] * (warnings + 1)
    
    # تسجيل الحظر
    if duration_hours == 0:
        # حظر دائم
        update_user_data(uid, banned=True)
        ban_cache[uid] = {
            "until": None,
            "reason": reason,
            "permanent": True,
            "time": datetime.now().isoformat()
        }
    else:
        # حظر مؤقت
        until = datetime.now() + timedelta(hours=duration_hours)
        update_user_data(uid, banned_until=until.isoformat())
        ban_cache[uid] = {
            "until": until,
            "reason": reason,
            "permanent": False,
            "time": datetime.now().isoformat()
        }
    
    # زيادة عدد التحذيرات
    user_warnings[uid] += 1
    
    # تخفيض نقاط الثقة
    modify_trust_score(uid, -20, f"ban:{reason}")
    
    # إشعار الأدمن
    try:
        u = get_user(uid) or {}
        trust = get_trust_score(uid)
        duration_text = "Permanent" if duration_hours == 0 else f"{duration_hours}h"
        
        admin_msg = (
            f"╔═══════════════════════╗\n"
            f"║ 🚨 AUTO-BAN ALERT 🚨 ║\n"
            f"╚═══════════════════════╝\n\n"
            f"👤 User: @{u.get('username', 'N/A')}\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📊 Trust: {trust}/100\n"
            f"⚠️ Warnings: {user_warnings[uid]}\n"
            f"⏰ Duration: {duration_text}\n\n"
            f"📝 Reason:\n<code>{reason}</code>"
        )
        
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔓 Unban", callback_data=f"shield_unban_{uid}"))
        m.add(types.InlineKeyboardButton("📊 Details", callback_data=f"shield_details_{uid}"))
        
        bot.send_message(ADMIN_PRIMARY, admin_msg, reply_markup=m, parse_mode="HTML")
    except:
        pass
    
    return {
        "banned": True,
        "duration": duration_hours,
        "reason": reason,
        "warnings": user_warnings[uid]
    }

def smart_unban(uid: str) -> bool:
    """إلغاء الحظر"""
    uid = str(uid)
    try:
        update_user_data(uid, banned=False, banned_until=None)
        if uid in ban_cache:
            del ban_cache[uid]
        # استعادة بعض نقاط الثقة
        modify_trust_score(uid, 10, "unbanned")
        return True
    except:
        return False

def is_banned_smart(uid: str) -> tuple:
    """
    فحص الحظر الذكي
    Returns: (is_banned: bool, reason: str, remaining: str)
    """
    uid = str(uid)
    
    # فحص من الكاش أولاً
    if uid in ban_cache:
        cache = ban_cache[uid]
        if cache.get("permanent"):
            return True, cache.get("reason", "Banned"), "Permanent"
        
        until = cache.get("until")
        if until and datetime.now() < until:
            remaining = until - datetime.now()
            hours = remaining.seconds // 3600
            mins = (remaining.seconds % 3600) // 60
            return True, cache.get("reason", "Banned"), f"{hours}h {mins}m"
        else:
            # انتهى الحظر
            del ban_cache[uid]
            update_user_data(uid, banned_until=None)
    
    # فحص من قاعدة البيانات
    u = get_user(uid)
    if u:
        if u.get("banned"):
            return True, "Permanent ban", "Permanent"
        
        banned_until = u.get("banned_until")
        if banned_until:
            try:
                until = datetime.fromisoformat(banned_until)
                if datetime.now() < until:
                    remaining = until - datetime.now()
                    hours = remaining.seconds // 3600
                    mins = (remaining.seconds % 3600) // 60
                    return True, "Temporary ban", f"{hours}h {mins}m"
            except:
                pass
    
    return False, "", ""

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ كابتشا ذكية متقدمة
# ═══════════════════════════════════════════════════════════════════════════

SMART_CAPTCHA_CHALLENGES = {
    "emoji_math": {
        "ar": "🧮 كم الناتج؟\n\n{q}",
        "en": "🧮 What's the result?\n\n{q}",
        "fr": "🧮 Quel est le résultat?\n\n{q}",
        "es": "🧮 ¿Cuál es el resultado?\n\n{q}",
        "vi": "🧮 Kết quả là gì?\n\n{q}"
    },
    "emoji_count": {
        "ar": "🔢 كم عدد {emoji}؟\n\n{grid}",
        "en": "🔢 How many {emoji}?\n\n{grid}",
        "fr": "🔢 Combien de {emoji}?\n\n{grid}",
        "es": "🔢 ¿Cuántos {emoji}?\n\n{grid}",
        "vi": "🔢 Có bao nhiêu {emoji}?\n\n{grid}"
    },
    "emoji_odd": {
        "ar": "🎯 أي إيموجي مختلف؟",
        "en": "🎯 Which emoji is different?",
        "fr": "🎯 Quel emoji est différent?",
        "es": "🎯 ¿Qué emoji es diferente?",
        "vi": "🎯 Emoji nào khác biệt?"
    }
}

smart_captcha_sessions = {}  # {uid: {"type": str, "answer": str, "expires": datetime, "attempts": int}}

def generate_smart_captcha(uid: str, lang: str = "ar") -> dict:
    """
    إنشاء كابتشا ذكية متعددة الأنواع
    """
    uid = str(uid)
    captcha_type = random.choice(["emoji_math", "emoji_count", "emoji_odd"])
    
    if captcha_type == "emoji_math":
        # كابتشا حسابية
        ops = ["+", "-", "×"]
        op = random.choice(ops)
        
        if op == "+":
            a, b = random.randint(1, 10), random.randint(1, 10)
            answer = a + b
        elif op == "-":
            a = random.randint(5, 15)
            b = random.randint(1, a)
            answer = a - b
        else:
            a, b = random.randint(1, 5), random.randint(1, 5)
            answer = a * b
        
        question = f"🔢 {a} {op} {b} = ❓"
        options = [str(answer)]
        while len(options) < 4:
            fake = answer + random.randint(-5, 5)
            if fake > 0 and str(fake) not in options:
                options.append(str(fake))
        random.shuffle(options)
        
        text = SMART_CAPTCHA_CHALLENGES["emoji_math"][lang].format(q=question)
        
    elif captcha_type == "emoji_count":
        # كابتشا عد الإيموجيات
        emojis = ["🍎", "🌟", "💎", "🔥", "⚡", "🎯", "🎁", "💰"]
        target = random.choice(emojis)
        count = random.randint(2, 5)
        
        grid_emojis = [target] * count
        other_emojis = [e for e in emojis if e != target]
        for _ in range(12 - count):
            grid_emojis.append(random.choice(other_emojis))
        random.shuffle(grid_emojis)
        
        grid = ""
        for i, e in enumerate(grid_emojis):
            grid += e
            if (i + 1) % 4 == 0:
                grid += "\n"
        
        answer = str(count)
        options = [str(count)]
        while len(options) < 4:
            fake = random.randint(1, 6)
            if str(fake) not in options:
                options.append(str(fake))
        random.shuffle(options)
        
        text = SMART_CAPTCHA_CHALLENGES["emoji_count"][lang].format(emoji=target, grid=grid)
        
    else:
        # كابتشا الإيموجي المختلف
        emojis = ["🍎", "🍎", "🍎", "🍊"]
        random.shuffle(emojis)
        answer = str(emojis.index("🍊") + 1)
        options = ["1", "2", "3", "4"]
        
        grid = "  ".join([f"{i+1}️⃣{e}" for i, e in enumerate(emojis)])
        text = SMART_CAPTCHA_CHALLENGES["emoji_odd"][lang] + f"\n\n{grid}"
    
    # حفظ الجلسة
    smart_captcha_sessions[uid] = {
        "type": captcha_type,
        "answer": answer,
        "expires": datetime.now() + timedelta(minutes=3),
        "attempts": 0,
        "options": options
    }
    
    return {
        "text": text,
        "options": options,
        "answer": answer
    }

def verify_smart_captcha(uid: str, user_answer: str) -> tuple:
    """
    التحقق من الكابتشا
    Returns: (success: bool, status: str)
    """
    uid = str(uid)
    
    if uid not in smart_captcha_sessions:
        return False, "no_session"
    
    session = smart_captcha_sessions[uid]
    
    # فحص الانتهاء
    if datetime.now() > session["expires"]:
        del smart_captcha_sessions[uid]
        return False, "expired"
    
    # فحص الإجابة
    if str(user_answer).strip() == session["answer"]:
        del smart_captcha_sessions[uid]
        modify_trust_score(uid, 5, "captcha_passed")
        captcha_failures[uid] = 0
        return True, "correct"
    
    # إجابة خاطئة
    session["attempts"] += 1
    captcha_failures[uid] += 1
    
    if session["attempts"] >= 3:
        del smart_captcha_sessions[uid]
        
        if captcha_failures[uid] >= DETECTION_CONFIG["max_failed_captcha"]:
            smart_ban(uid, "Multiple failed captcha attempts", 1)
            return False, "banned"
        
        return False, "max_attempts"
    
    modify_trust_score(uid, -2, "captcha_failed")
    return False, "wrong"

# ═══════════════════════════════════════════════════════════════════════════
# 📊 لوحة تحكم الأدمن
# ═══════════════════════════════════════════════════════════════════════════

SHIELD_TRANSLATIONS = {
    "ar": {
        "panel_title": "╔═══════════════════════╗\n║ 🛡️ SMART SHIELD 🛡️ ║\n╚═══════════════════════╝",
        "stats_title": "📊 إحصائيات الحماية",
        "active_bans": "🚫 حظورات نشطة",
        "warnings_issued": "⚠️ تحذيرات صادرة",
        "avg_trust": "📈 متوسط الثقة",
        "blocked_referrals": "🔗 إحالات محظورة",
        "btn_view_bans": "🚫 عرض المحظورين",
        "btn_view_suspicious": "🔍 المشبوهين",
        "btn_settings": "⚙️ الإعدادات",
        "btn_logs": "📜 السجلات"
    },
    "en": {
        "panel_title": "╔═══════════════════════╗\n║ 🛡️ SMART SHIELD 🛡️ ║\n╚═══════════════════════╝",
        "stats_title": "📊 Protection Stats",
        "active_bans": "🚫 Active Bans",
        "warnings_issued": "⚠️ Warnings Issued",
        "avg_trust": "📈 Average Trust",
        "blocked_referrals": "🔗 Blocked Referrals",
        "btn_view_bans": "🚫 View Banned",
        "btn_view_suspicious": "🔍 Suspicious",
        "btn_settings": "⚙️ Settings",
        "btn_logs": "📜 Logs"
    }
}

def get_shield_stats() -> dict:
    """إحصائيات نظام الحماية"""
    return {
        "active_bans": len(ban_cache),
        "total_warnings": sum(user_warnings.values()),
        "avg_trust": sum(user_trust_scores.values()) / max(len(user_trust_scores), 1),
        "tracked_users": len(user_actions),
        "suspicious_users": len([
            uid for uid, score in user_trust_scores.items()
            if score < DETECTION_CONFIG["trust_threshold_low"]
        ]),
        "captcha_failures": sum(captcha_failures.values())
    }

def show_shield_panel(chat_id, lang="ar"):
    """عرض لوحة تحكم الحماية"""
    tr = SHIELD_TRANSLATIONS.get(lang, SHIELD_TRANSLATIONS["en"])
    stats = get_shield_stats()
    
    msg = (
        f"{tr['panel_title']}\n\n"
        f"{tr['stats_title']}:\n\n"
        f"├ {tr['active_bans']}: {stats['active_bans']}\n"
        f"├ {tr['warnings_issued']}: {stats['total_warnings']}\n"
        f"├ {tr['avg_trust']}: {stats['avg_trust']:.1f}/100\n"
        f"├ 🔍 Tracked: {stats['tracked_users']}\n"
        f"├ ⚠️ Suspicious: {stats['suspicious_users']}\n"
        f"└ ❌ Captcha Fails: {stats['captcha_failures']}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(tr["btn_view_bans"], callback_data="shield_bans"),
        types.InlineKeyboardButton(tr["btn_view_suspicious"], callback_data="shield_suspicious")
    )
    m.add(
        types.InlineKeyboardButton(tr["btn_settings"], callback_data="shield_settings"),
        types.InlineKeyboardButton(tr["btn_logs"], callback_data="shield_logs")
    )
    
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 معالجات الأحداث
# ═══════════════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text in ["🛡️ Smart Shield", "🛡️ الحماية الذكية"])
def handle_shield_button(message):
    uid = str(message.from_user.id)
    u = get_user(uid) or {}
    
    if int(uid) not in [ADMIN_PRIMARY, ADMIN_SECONDARY] and not u.get("is_admin"):
        return
    
    lang = u.get("lang", "ar")
    show_shield_panel(message.chat.id, lang)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shield_"))
def handle_shield_callbacks(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    
    if int(uid) not in [ADMIN_PRIMARY, ADMIN_SECONDARY] and not u.get("is_admin"):
        return
    
    data = call.data
    chat_id = call.message.chat.id
    
    if data == "shield_bans":
        if not ban_cache:
            bot.answer_callback_query(call.id, "📭 No active bans", show_alert=True)
            return
        
        msg = "🚫 ━━ BANNED USERS ━━\n\n"
        for uid, info in list(ban_cache.items())[:15]:
            u = get_user(uid) or {}
            duration = "Permanent" if info.get("permanent") else str(info.get("until", ""))[:16]
            msg += f"• @{u.get('username', 'N/A')} ({uid})\n"
            msg += f"  └ {info.get('reason', 'N/A')[:30]} | {duration}\n"
        
        bot.send_message(chat_id, msg, parse_mode="HTML")
    
    elif data == "shield_suspicious":
        suspicious = [
            (uid, score) for uid, score in user_trust_scores.items()
            if score < DETECTION_CONFIG["trust_threshold_low"]
        ]
        
        if not suspicious:
            bot.answer_callback_query(call.id, "✅ No suspicious users", show_alert=True)
            return
        
        msg = "🔍 ━━ SUSPICIOUS USERS ━━\n\n"
        for uid, score in sorted(suspicious, key=lambda x: x[1])[:15]:
            u = get_user(uid) or {}
            warnings = user_warnings.get(uid, 0)
            msg += f"• @{u.get('username', 'N/A')}\n"
            msg += f"  └ Trust: {score} | Warnings: {warnings}\n"
        
        bot.send_message(chat_id, msg, parse_mode="HTML")
    
    elif data == "shield_settings":
        msg = (
            "⚙️ ━━ SHIELD SETTINGS ━━\n\n"
            f"├ Max actions/min: {DETECTION_CONFIG['max_actions_per_minute']}\n"
            f"├ Trust threshold: {DETECTION_CONFIG['trust_threshold_low']}\n"
            f"├ Ban threshold: {DETECTION_CONFIG['trust_threshold_ban']}\n"
            f"├ Temp ban hours: {DETECTION_CONFIG['temp_ban_hours']}\n"
            f"├ Max referrals/h: {DETECTION_CONFIG['max_referrals_per_hour']}\n"
            f"└ Captcha attempts: {DETECTION_CONFIG['max_failed_captcha']}"
        )
        bot.send_message(chat_id, msg, parse_mode="HTML")
    
    elif data == "shield_logs":
        # آخر 10 أحداث
        all_patterns = []
        for uid, patterns in suspicious_patterns.items():
            for p in patterns[-3:]:
                p["uid"] = uid
                all_patterns.append(p)
        
        all_patterns.sort(key=lambda x: x.get("time", ""), reverse=True)
        
        if not all_patterns:
            bot.answer_callback_query(call.id, "📭 No logs", show_alert=True)
            return
        
        msg = "📜 ━━ RECENT LOGS ━━\n\n"
        for p in all_patterns[:10]:
            time_str = p.get("time", "")[:16]
            msg += f"• {p.get('uid', '?')}: {p.get('reason', p.get('action', '?'))}\n"
            msg += f"  └ {time_str}\n"
        
        bot.send_message(chat_id, msg, parse_mode="HTML")
    
    elif data.startswith("shield_unban_"):
        target = data.replace("shield_unban_", "")
        if smart_unban(target):
            bot.answer_callback_query(call.id, f"✅ Unbanned {target}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Failed", show_alert=True)
    
    elif data.startswith("shield_details_"):
        target = data.replace("shield_details_", "")
        u = get_user(target) or {}
        trust = get_trust_score(target)
        warnings = user_warnings.get(target, 0)
        patterns = suspicious_patterns.get(target, [])
        
        msg = (
            f"👤 ━━ USER DETAILS ━━\n\n"
            f"🆔 ID: <code>{target}</code>\n"
            f"📝 @{u.get('username', 'N/A')}\n"
            f"📊 Trust Score: {trust}/100\n"
            f"⚠️ Warnings: {warnings}\n"
            f"💰 Balance: {u.get('points', 0)}\n"
            f"🛒 Purchases: {u.get('purchases_count', 0)}\n\n"
            f"📜 Recent Patterns:\n"
        )
        
        for p in patterns[-5:]:
            msg += f"• {p.get('reason', p.get('action', '?'))}\n"
        
        m = types.InlineKeyboardMarkup()
        m.add(
            types.InlineKeyboardButton("🔓 Unban", callback_data=f"shield_unban_{target}"),
            types.InlineKeyboardButton("📈 +10 Trust", callback_data=f"shield_trust_add_{target}")
        )
        m.add(
            types.InlineKeyboardButton("📉 -10 Trust", callback_data=f"shield_trust_sub_{target}"),
            types.InlineKeyboardButton("🗑️ Clear Warnings", callback_data=f"shield_clear_{target}")
        )
        
        bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")
    
    elif data.startswith("shield_trust_add_"):
        target = data.replace("shield_trust_add_", "")
        new_score = modify_trust_score(target, 10, "admin_boost")
        bot.answer_callback_query(call.id, f"✅ Trust: {new_score}", show_alert=True)
    
    elif data.startswith("shield_trust_sub_"):
        target = data.replace("shield_trust_sub_", "")
        new_score = modify_trust_score(target, -10, "admin_penalty")
        bot.answer_callback_query(call.id, f"✅ Trust: {new_score}", show_alert=True)
    
    elif data.startswith("shield_clear_"):
        target = data.replace("shield_clear_", "")
        user_warnings[target] = 0
        bot.answer_callback_query(call.id, "✅ Warnings cleared", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("scaptcha_"))
def handle_smart_captcha(call):
    uid = str(call.from_user.id)
    answer = call.data.replace("scaptcha_", "")
    
    success, status = verify_smart_captcha(uid, answer)
    
    if success:
        bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        # يمكن إضافة استمرار للعملية هنا
    else:
        if status == "banned":
            bot.answer_callback_query(call.id, "🚫 Banned for abuse!", show_alert=True)
        elif status == "max_attempts":
            bot.answer_callback_query(call.id, "❌ Too many attempts! Try again later.", show_alert=True)
        elif status == "expired":
            bot.answer_callback_query(call.id, "⏰ Captcha expired! Try again.", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Wrong! Try again.", show_alert=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🔌 دوال التكامل مع البوت الرئيسي
# ═══════════════════════════════════════════════════════════════════════════

def shield_check(uid: str, action: str = "general") -> tuple:
    """
    فحص الحماية - يُستدعى قبل أي عملية مهمة
    Returns: (allowed: bool, message: str, needs_captcha: bool)
    """
    uid = str(uid)
    
    # فحص الحظر
    is_banned, reason, remaining = is_banned_smart(uid)
    if is_banned:
        return False, f"🚫 Banned: {reason}\n⏰ Remaining: {remaining}", False
    
    # تحليل السلوك
    analysis = analyze_user_behavior(uid, action)
    
    if analysis["action"] == "ban":
        smart_ban(uid, "; ".join(analysis["reasons"]))
        return False, "🚫 Account suspended for suspicious activity", False
    
    if analysis["action"] == "temp_ban":
        smart_ban(uid, "; ".join(analysis["reasons"]), DETECTION_CONFIG["temp_ban_hours"])
        return False, "⏰ Temporarily suspended", False
    
    if analysis["action"] == "captcha":
        return True, "Captcha required", True
    
    if analysis["action"] == "warn":
        user_warnings[uid] += 1
        return True, "⚠️ Warning issued", False
    
    return True, "OK", False

def shield_referral_check(inviter_uid: str, new_user) -> tuple:
    """
    فحص الإحالة
    Returns: (allowed: bool, message: str)
    """
    result = check_referral_abuse(inviter_uid, new_user)
    return result["allowed"], result["message"]

def shield_daily_bonus_check(uid: str) -> tuple:
    """
    فحص المكافأة اليومية
    Returns: (allowed: bool, message: str)
    """
    result = check_daily_bonus_abuse(uid)
    return result["allowed"], result["message"]

def send_shield_captcha(chat_id: int, uid: str, lang: str = "ar"):
    """إرسال كابتشا ذكية"""
    captcha = generate_smart_captcha(uid, lang)
    
    m = types.InlineKeyboardMarkup(row_width=2)
    for opt in captcha["options"]:
        m.add(types.InlineKeyboardButton(opt, callback_data=f"scaptcha_{opt}"))
    
    msg = (
        "╔═══════════════════════╗\n"
        "║ 🛡️ SECURITY CHECK 🛡️ ║\n"
        "╚═══════════════════════╝\n\n"
        f"{captcha['text']}\n\n"
        "⏰ 3 minutes | 3 attempts"
    )
    
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 التهيئة
# ═══════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("✅ bot6.py loaded!")
print("🛡️ Smart Shield System: ACTIVE")
print("🔍 Behavior Analysis: ENABLED")
print("🚫 Anti-Abuse: ACTIVE")
print("🔗 Referral Protection: ENABLED")
print("🎯 Smart Captcha: READY")
print("📊 Trust Score System: RUNNING")
print("=" * 60)
