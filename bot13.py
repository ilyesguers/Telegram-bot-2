"""
=====================================================================
 bot13.py — مركز قيادة الأدمن (Admin Command Center) — المرحلة 2
=====================================================================
👑 كل ما يحتاجه الأدمن في مكان واحد، بدون حذف أو تعطيل أي أداة قديمة:

 1) 🏠 لوحة القيادة      — كل الأرقام المهمة في رسالة واحدة تتحدّث
 2) ⚠️ تنبيه المخزون     — يخبرك فور نزول أي منتج تحت الحد الأدنى
 3) 🔎 البحث الشامل      — عضو / تذكرة / عملية بيع / مفتاح من مكان واحد
 4) 📜 سجل التدقيق       — من فعل ماذا ومتى (كل إجراء إداري)
 5) 📢 إذاعة مستهدفة     — الكل / VIP / نشط / حسب اللغة / حسب الرتبة
 6) 📤 تصدير CSV         — المبيعات والأعضاء كملف جاهز

📌 التركيب: import bot13 داخل bot.py
📌 الأوامر: /dash — الأزرار: «🏠 لوحة القيادة» و«🔎 بحث شامل»
=====================================================================
"""

import csv
import html
import io
import threading
import time
from datetime import datetime, timedelta

from telebot import types

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import (bot_config, save_json, DB_CONFIG, get_user, update_user_data,
                      get_bot_stats, get_total_users, get_active_users_today,
                      search_user, keys_store, prices_config, engine, text as sql_text)

PLANS = ["1 Day", "7 Days", "30 Days"]


# =====================================================================
# ⚙️ الإعدادات الافتراضية
# =====================================================================
def _init_config():
    defaults = {
        "low_stock_threshold": 3,      # الحد الذي يُنبَّه عنده الأدمن
        "audit_log": [],               # سجل الإجراءات الإدارية
        "low_stock_notified": {},      # منع تكرار التنبيه لنفس المنتج
        "broadcast_history": [],
    }
    changed = False
    for key, value in defaults.items():
        if key not in bot_config:
            bot_config[key] = value
            changed = True
    if changed:
        save_json(DB_CONFIG, bot_config)


_init_config()

# تخزين مؤقت لخطوات الأدمن
_pending = {}


# =====================================================================
# 🔧 أدوات
# =====================================================================
def _esc(value):
    try:
        return html.escape(str(value))
    except Exception:
        return str(value)


def is_admin(uid):
    try:
        if int(uid) in (ADMIN_PRIMARY, ADMIN_SECONDARY):
            return True
    except (TypeError, ValueError):
        pass
    return bool((get_user(str(uid)) or {}).get("is_admin", False))


def _admin_ids():
    ids = {ADMIN_PRIMARY, ADMIN_SECONDARY}
    try:
        with engine.connect() as conn:
            for row in conn.execute(sql_text("SELECT uid FROM users WHERE is_admin = TRUE")).fetchall():
                ids.add(int(row[0]))
    except Exception:
        pass
    return ids


def _send(chat_id, body, markup=None, msg_id=None):
    if msg_id:
        try:
            return bot.edit_message_text(body, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass
    try:
        return bot.send_message(chat_id, body, reply_markup=markup, parse_mode="HTML")
    except Exception:
        return None


def _ack(call, body=None, alert=False):
    try:
        bot.answer_callback_query(call.id, body, show_alert=alert)
    except Exception:
        pass


def _num(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return str(value)


# =====================================================================
# 📜 سجل التدقيق
# =====================================================================
def log_action(admin_uid, action, details=""):
    """تسجيل أي إجراء إداري — يُستدعى من بقية الملفات أيضاً."""
    try:
        entry = {
            "uid": str(admin_uid),
            "username": (get_user(str(admin_uid)) or {}).get("username", ""),
            "action": action,
            "details": str(details)[:300],
            "at": datetime.now().isoformat(timespec="seconds"),
        }
        log = bot_config.setdefault("audit_log", [])
        log.append(entry)
        bot_config["audit_log"] = log[-500:]
        save_json(DB_CONFIG, bot_config)
        return entry
    except Exception as e:
        print(f"⚠️ audit log error: {e}")
        return None


# =====================================================================
# 📊 حساب الأرقام
# =====================================================================
def _sales_window(hours):
    since = datetime.now() - timedelta(hours=hours)
    count, revenue = 0, 0
    for sale in bot_config.get("sales_log", []) or []:
        try:
            if datetime.fromisoformat(sale.get("date", "")) >= since:
                count += 1
                revenue += int(sale.get("price", 0) or 0)
        except Exception:
            continue
    return count, revenue


def low_stock_items(threshold=None):
    """كل منتج/باقة وصل مخزونه للحد الأدنى أو أقل."""
    if threshold is None:
        threshold = int(bot_config.get("low_stock_threshold", 3) or 3)
    items = []
    for product in prices_config.keys():
        for plan in PLANS:
            stock = len(keys_store.get(product, {}).get(plan, []) or [])
            if stock <= threshold:
                items.append((product, plan, stock))
    return items


def dashboard_text():
    stats = get_bot_stats()
    today_count, today_revenue = _sales_window(24)
    week_count, week_revenue = _sales_window(24 * 7)
    low = low_stock_items()

    try:
        from bot2 import get_giveaways_stats
        gw = get_giveaways_stats()
        gw_line = f"│ 🎁 مسابقات نشطة: <b>{gw.get('active', 0)}</b>\n"
    except Exception:
        gw_line = ""

    vip_count = len(bot_config.get("vip_subscribers", {}) or {})
    watchers = sum(len(v or []) for v in (bot_config.get("stock_watchers", {}) or {}).values())

    from utils import get_active_flash_sale
    flash = get_active_flash_sale()
    flash_line = (f"│ ⚡ عرض خاطف: <b>{_esc(flash['product'])}</b> ({flash['discount']}%)\n"
                  if flash else "│ ⚡ عرض خاطف: —\n")

    state = "🛠️ صيانة" if stats.get("maintenance") else "🟢 يعمل"

    body = (
        f"╔═══════════════════════════╗\n"
        f"║   👑 <b>لوحة القيادة</b>   ║\n"
        f"╚═══════════════════════════╝\n"
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}   •   {state}\n\n"
        f"┌── 👥 <b>الأعضاء</b>\n"
        f"│ الإجمالي: <b>{_num(stats.get('total_users', 0))}</b>\n"
        f"│ نشط اليوم: <b>{_num(stats.get('active_today', 0))}</b>\n"
        f"│ 👑 VIP: <b>{vip_count}</b>\n"
        f"├── 💰 <b>المبيعات</b>\n"
        f"│ اليوم: <b>{today_count}</b> عملية — <b>{_num(today_revenue)}</b> 💎\n"
        f"│ آخر 7 أيام: <b>{week_count}</b> عملية — <b>{_num(week_revenue)}</b> 💎\n"
        f"│ الإجمالي: <b>{_num(stats.get('total_sales', 0))}</b> — "
        f"<b>{_num(stats.get('total_earnings', 0))}</b> 💎\n"
        f"├── 📦 <b>المتجر</b>\n"
        f"│ المنتجات: <b>{stats.get('total_products', 0)}</b>\n"
        f"│ ⚠️ مخزون منخفض: <b>{len(low)}</b>\n"
        f"│ 🔔 بانتظار التوفر: <b>{watchers}</b>\n"
        f"{flash_line}"
        f"{gw_line}"
        f"├── 🎫 <b>الدعم</b>\n"
        f"│ تذاكر مفتوحة: <b>{stats.get('open_tickets', 0)}</b> / {stats.get('total_tickets', 0)}\n"
        f"│ 💡 طلبات منتجات: <b>{stats.get('total_requests', 0)}</b>\n"
        f"└──────────────────────\n"
    )

    if low:
        body += "\n⚠️ <b>يحتاج تجديد:</b>\n"
        for product, plan, stock in low[:6]:
            body += f"• {_esc(product)} — {plan}: <b>{stock}</b>\n"
        if len(low) > 6:
            body += f"… و {len(low) - 6} عنصر آخر\n"

    return body


def dashboard_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🔎 بحث شامل", callback_data="dash_search"),
        types.InlineKeyboardButton("⚠️ المخزون المنخفض", callback_data="dash_lowstock"),
    )
    m.add(
        types.InlineKeyboardButton("📢 إذاعة مستهدفة", callback_data="dash_bc"),
        types.InlineKeyboardButton("📜 سجل التدقيق", callback_data="dash_audit"),
    )
    m.add(
        types.InlineKeyboardButton("📤 تصدير المبيعات", callback_data="dash_csv_sales"),
        types.InlineKeyboardButton("📤 تصدير الأعضاء", callback_data="dash_csv_users"),
    )
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="dash_refresh"))
    return m


def show_dashboard(chat_id, msg_id=None):
    _send(chat_id, dashboard_text(), dashboard_kb(), msg_id)


# =====================================================================
# 🚪 المداخل
# =====================================================================
@bot.message_handler(commands=["dash", "dashboard"])
def _dash_command(message):
    if not is_admin(message.from_user.id):
        return
    show_dashboard(message.chat.id)


@bot.message_handler(func=lambda m: m.text == "🏠 لوحة القيادة")
def _dash_button(message):
    if not is_admin(message.from_user.id):
        return
    show_dashboard(message.chat.id)


@bot.message_handler(func=lambda m: m.text == "🔎 بحث شامل")
def _search_button(message):
    if not is_admin(message.from_user.id):
        return
    _start_search(message.chat.id, str(message.from_user.id))


# =====================================================================
# 🔎 البحث الشامل
# =====================================================================
def _start_search(chat_id, admin_uid):
    prompt = _send(chat_id,
                   "🔎 <b>البحث الشامل</b>\n\n"
                   "أرسل أياً مما يلي:\n"
                   "• 🆔 معرّف عضو أو @يوزرنيم\n"
                   "• 🎫 رقم تذكرة\n"
                   "• 🔑 جزء من مفتاح\n"
                   "• 📦 اسم منتج\n\n"
                   "<i>أرسل /cancel للإلغاء</i>")
    if prompt:
        bot.register_next_step_handler(prompt, _run_search)


def _run_search(message):
    admin_uid = str(message.from_user.id)
    if not is_admin(admin_uid):
        return
    query = (message.text or "").strip()
    if not query:
        return _send(message.chat.id, "❌ بحث فارغ")

    parts = [f"🔎 <b>نتائج البحث عن:</b> <code>{_esc(query)}</code>\n"]
    markup = types.InlineKeyboardMarkup(row_width=1)

    # 1) عضو
    user = search_user(query.lstrip("@"))
    if user:
        parts.append(
            f"\n👤 <b>عضو</b>\n"
            f"├ الاسم: @{_esc(user.get('username', '—'))}\n"
            f"├ ID: <code>{_esc(user.get('uid'))}</code>\n"
            f"├ النقاط: <b>{user.get('points', 0)}</b> 💎\n"
            f"├ الرتبة: {_esc(user.get('rank', '—'))}\n"
            f"├ المشتريات: {user.get('purchases_count', 0)}\n"
            f"└ محظور: {'نعم ⛔' if user.get('banned') else 'لا ✅'}"
        )
        markup.add(types.InlineKeyboardButton(
            f"🧑‍💻 إدارة @{user.get('username', user.get('uid'))}",
            callback_data=f"ucp_open_{user.get('uid')}"))

    # 2) تذكرة
    tickets = bot_config.get("tickets", {}) or {}
    ticket = tickets.get(query) or tickets.get(query.lstrip("#"))
    if ticket:
        parts.append(
            f"\n🎫 <b>تذكرة #{_esc(query)}</b>\n"
            f"├ صاحبها: <code>{_esc(ticket.get('uid'))}</code>\n"
            f"├ الحالة: {_esc(ticket.get('status', 'open'))}\n"
            f"└ النص: {_esc(str(ticket.get('text', ''))[:120])}"
        )

    # 3) مبيعات (مفتاح / منتج / عضو)
    hits = []
    for sale in reversed(bot_config.get("sales_log", []) or []):
        blob = f"{sale.get('key','')} {sale.get('product','')} {sale.get('uid','')} {sale.get('username','')}"
        if query.lower() in blob.lower():
            hits.append(sale)
        if len(hits) >= 5:
            break
    if hits:
        parts.append("\n💰 <b>عمليات بيع مطابقة</b>")
        for sale in hits:
            parts.append(
                f"• {_esc(sale.get('product'))}/{_esc(sale.get('plan'))} — "
                f"{sale.get('price', 0)}💎 — <code>{_esc(sale.get('uid'))}</code> — "
                f"{_esc(str(sale.get('date', ''))[:16])}"
            )

    # 4) مخزون المنتج
    for product in prices_config.keys():
        if query.lower() in product.lower():
            stocks = " | ".join(f"{plan}: {len(keys_store.get(product, {}).get(plan, []) or [])}"
                                for plan in PLANS)
            parts.append(f"\n📦 <b>{_esc(product)}</b>\n└ {stocks}")

    if len(parts) == 1:
        parts.append("\n📭 لا توجد أي نتيجة مطابقة.")

    markup.add(types.InlineKeyboardButton("🏠 لوحة القيادة", callback_data="dash_refresh"))
    _send(message.chat.id, "\n".join(parts), markup)


# =====================================================================
# ⚠️ المخزون المنخفض + التنبيه التلقائي
# =====================================================================
def low_stock_text():
    threshold = int(bot_config.get("low_stock_threshold", 3) or 3)
    items = low_stock_items(threshold)
    body = [f"⚠️ <b>المخزون المنخفض</b>  (الحد: {threshold})\n"]
    if not items:
        body.append("✅ كل المنتجات بمخزون كافٍ.")
    else:
        for product, plan, stock in items:
            waiting = len((bot_config.get("stock_watchers", {}) or {}).get(f"{product}||{plan}", []))
            extra = f" — 🔔 {waiting} بانتظاره" if waiting else ""
            body.append(f"• <b>{_esc(product)}</b> — {plan}: <b>{stock}</b>{extra}")
    return "\n".join(body)


def _low_stock_kb():
    threshold = int(bot_config.get("low_stock_threshold", 3) or 3)
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("➖", callback_data="dash_thr_down"),
        types.InlineKeyboardButton(f"الحد: {threshold}", callback_data="dash_lowstock"),
        types.InlineKeyboardButton("➕", callback_data="dash_thr_up"),
    )
    m.add(types.InlineKeyboardButton("🏠 لوحة القيادة", callback_data="dash_refresh"))
    return m


def check_low_stock_and_alert():
    """تنبيه الأدمن مرة واحدة لكل منتج ينزل تحت الحد (يُعاد ضبطه عند التجديد)."""
    threshold = int(bot_config.get("low_stock_threshold", 3) or 3)
    notified = bot_config.setdefault("low_stock_notified", {})
    changed = False

    current = {f"{p}||{pl}": s for p, pl, s in low_stock_items(threshold)}
    for key, stock in current.items():
        if notified.get(key):
            continue
        product, plan = key.split("||")
        notified[key] = True
        changed = True
        message = (f"⚠️ <b>تنبيه مخزون منخفض</b>\n\n"
                   f"📦 <b>{_esc(product)}</b> — {plan}\n"
                   f"🔑 المتبقي: <b>{stock}</b> (الحد: {threshold})\n\n"
                   f"💡 <i>أضف مفاتيح جديدة أو اجدول تجديداً تلقائياً.</i>")
        for admin_id in _admin_ids():
            try:
                bot.send_message(admin_id, message, parse_mode="HTML")
            except Exception:
                pass

    for key in list(notified.keys()):
        if key not in current:
            notified.pop(key, None)
            changed = True

    if changed:
        bot_config["low_stock_notified"] = notified
        save_json(DB_CONFIG, bot_config)


def _low_stock_worker():
    while True:
        try:
            check_low_stock_and_alert()
        except Exception as e:
            print(f"⚠️ low stock worker: {e}")
        time.sleep(600)  # كل 10 دقائق


threading.Thread(target=_low_stock_worker, daemon=True).start()


# =====================================================================
# 📜 عرض سجل التدقيق
# =====================================================================
def audit_text(limit=15):
    log = (bot_config.get("audit_log", []) or [])[-limit:]
    if not log:
        return "📜 <b>سجل التدقيق</b>\n\n📭 لا توجد إجراءات مسجّلة بعد."
    lines = [f"📜 <b>سجل التدقيق</b> — آخر {len(log)} إجراء\n"]
    for entry in reversed(log):
        who = entry.get("username") or entry.get("uid")
        when = str(entry.get("at", ""))[5:16].replace("T", " ")
        lines.append(f"• <b>{_esc(entry.get('action'))}</b> — @{_esc(who)}\n"
                     f"  <i>{_esc(entry.get('details', ''))[:90]}</i>  ⏱ {when}")
    return "\n".join(lines)


# =====================================================================
# 📤 تصدير CSV
# =====================================================================
def _export_sales():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "uid", "username", "product", "plan", "price", "key"])
    for sale in bot_config.get("sales_log", []) or []:
        writer.writerow([sale.get("date", ""), sale.get("uid", ""), sale.get("username", ""),
                         sale.get("product", ""), sale.get("plan", ""), sale.get("price", 0),
                         sale.get("key", "")])
    data = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    data.name = f"sales_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return data


def _export_users():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    columns = ["uid", "username", "points", "accumulated_points", "rank", "invite_count",
               "purchases_count", "total_spent", "streak_days", "lang", "vip", "banned",
               "join_date", "last_active"]
    writer.writerow(columns)
    try:
        with engine.connect() as conn:
            for row in conn.execute(sql_text(f"SELECT {', '.join(columns)} FROM users")).fetchall():
                writer.writerow(list(row))
    except Exception as e:
        print(f"⚠️ users export: {e}")
    data = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
    data.name = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return data


# =====================================================================
# 📢 الإذاعة المستهدفة
# =====================================================================
SEGMENTS = {
    "all": "👥 كل الأعضاء",
    "vip": "👑 VIP فقط",
    "active7": "⚡ نشط آخر 7 أيام",
    "buyers": "🛍️ المشترون فقط",
    "ar": "🇸🇦 الناطقون بالعربية",
    "en": "🌍 الناطقون بالإنجليزية",
}


def segment_users(segment):
    """يرجع قائمة معرّفات حسب الشريحة المختارة."""
    query = "SELECT uid FROM users WHERE COALESCE(notifications_on, TRUE) = TRUE"
    if segment == "vip":
        query += " AND vip = TRUE"
    elif segment == "buyers":
        query += " AND COALESCE(purchases_count, 0) > 0"
    elif segment == "ar":
        query += " AND lang = 'ar'"
    elif segment == "en":
        query += " AND lang = 'en'"
    elif segment == "active7":
        since = (datetime.now() - timedelta(days=7)).isoformat()
        query += f" AND last_active >= '{since}'"
    try:
        with engine.connect() as conn:
            return [str(row[0]) for row in conn.execute(sql_text(query)).fetchall()]
    except Exception as e:
        print(f"⚠️ segment error: {e}")
        return []


def _broadcast_menu(chat_id, msg_id=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, label in SEGMENTS.items():
        count = len(segment_users(key))
        buttons.append(types.InlineKeyboardButton(f"{label} ({count})", callback_data=f"dashbc_{key}"))
    m.add(*buttons)
    m.add(types.InlineKeyboardButton("🏠 لوحة القيادة", callback_data="dash_refresh"))
    _send(chat_id,
          "📢 <b>إذاعة مستهدفة</b>\n\n"
          "اختر الشريحة التي تريد مراسلتها، ثم أرسل نص الرسالة.\n"
          "<i>الأعضاء الذين أوقفوا الإشعارات مستثنون تلقائياً.</i>",
          m, msg_id)


def _run_broadcast(message):
    admin_uid = str(message.from_user.id)
    if not is_admin(admin_uid):
        return
    segment = _pending.pop(admin_uid, {}).get("segment", "all")
    body = message.text or ""
    if not body.strip():
        return _send(message.chat.id, "❌ نص فارغ — أُلغيت الإذاعة.")

    targets = segment_users(segment)
    status = _send(message.chat.id, f"📤 جارٍ الإرسال إلى <b>{len(targets)}</b> عضو…")

    sent, failed = 0, 0
    formatted = (f"╔═══════════════════╗\n"
                 f"║  📢 <b>إعلان</b>  ║\n"
                 f"╚═══════════════════╝\n\n{body}")
    for uid in targets:
        try:
            bot.send_message(int(uid), formatted, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        if sent % 20 == 0:
            time.sleep(1)  # احترام حدود تيليجرام

    bot_config.setdefault("broadcast_history", []).append({
        "segment": segment, "sent": sent, "failed": failed,
        "at": datetime.now().isoformat(timespec="seconds"),
    })
    bot_config["broadcast_history"] = bot_config["broadcast_history"][-100:]
    save_json(DB_CONFIG, bot_config)
    log_action(admin_uid, "إذاعة مستهدفة", f"{SEGMENTS.get(segment, segment)} — نجح {sent} / فشل {failed}")

    _send(message.chat.id,
          f"✅ <b>انتهت الإذاعة</b>\n\n"
          f"🎯 الشريحة: {SEGMENTS.get(segment, segment)}\n"
          f"📨 وصلت: <b>{sent}</b>\n"
          f"⚠️ فشلت: <b>{failed}</b>",
          dashboard_kb(),
          status.message_id if status else None)


# =====================================================================
# 🎛️ معالج أزرار اللوحة
# =====================================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("dash_") or c.data.startswith("dashbc_"))
def _dashboard_callbacks(call):
    uid = str(call.from_user.id)
    if not is_admin(uid):
        return _ack(call, "❌ للإدارة فقط", alert=True)

    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    if data in ("dash_refresh", "dash_open"):
        _ack(call, "🔄")
        return show_dashboard(chat_id, msg_id)

    if data == "dash_search":
        _ack(call)
        return _start_search(chat_id, uid)

    if data == "dash_lowstock":
        _ack(call)
        return _send(chat_id, low_stock_text(), _low_stock_kb(), msg_id)

    if data in ("dash_thr_up", "dash_thr_down"):
        threshold = int(bot_config.get("low_stock_threshold", 3) or 3)
        threshold = min(50, threshold + 1) if data == "dash_thr_up" else max(1, threshold - 1)
        bot_config["low_stock_threshold"] = threshold
        bot_config["low_stock_notified"] = {}
        save_json(DB_CONFIG, bot_config)
        _ack(call, f"الحد: {threshold}")
        return _send(chat_id, low_stock_text(), _low_stock_kb(), msg_id)

    if data == "dash_audit":
        _ack(call)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 لوحة القيادة", callback_data="dash_refresh"))
        return _send(chat_id, audit_text(), markup, msg_id)

    if data == "dash_bc":
        _ack(call)
        return _broadcast_menu(chat_id, msg_id)

    if data.startswith("dashbc_"):
        segment = data.split("_", 1)[1]
        _pending[uid] = {"segment": segment}
        _ack(call)
        prompt = _send(chat_id,
                       f"✍️ <b>اكتب نص الإذاعة</b>\n\n"
                       f"🎯 الشريحة: {SEGMENTS.get(segment, segment)} "
                       f"({len(segment_users(segment))} عضو)\n\n"
                       f"<i>يدعم HTML — أرسل /cancel للإلغاء</i>")
        if prompt:
            bot.register_next_step_handler(prompt, _run_broadcast)
        return

    if data in ("dash_csv_sales", "dash_csv_users"):
        _ack(call, "📤 جارٍ التصدير…")
        try:
            document = _export_sales() if data == "dash_csv_sales" else _export_users()
            bot.send_document(chat_id, document,
                              caption="📤 ملف CSV جاهز — افتحه بـ Excel أو Google Sheets")
            log_action(uid, "تصدير CSV", "المبيعات" if data == "dash_csv_sales" else "الأعضاء")
        except Exception as e:
            _send(chat_id, f"❌ فشل التصدير: {_esc(e)}")
        return

    _ack(call)


print("=" * 55)
print("✅ bot13.py — مركز قيادة الأدمن")
print("🏠 /dash | 🔎 بحث شامل | ⚠️ تنبيه المخزون")
print("📜 سجل التدقيق | 📢 إذاعة مستهدفة | 📤 تصدير CSV")
print("=" * 55)
