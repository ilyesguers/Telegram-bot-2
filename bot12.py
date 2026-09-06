"""
=====================================================================
 bot12.py — حزمة تجربة المستخدم (User Experience Pack) — المرحلة 1
=====================================================================
✨ ميزات جديدة بالكامل (بدون حذف أو تعطيل أي ميزة قائمة):

 1) 🧾 بطاقة الملف الشخصي   — شريط تقدّم للرتبة القادمة + كل إحصائياتك
 2) 🎖️ الإنجازات والشارات   — 13 شارة تُفتح تلقائياً حسب نشاطك
 3) 🏆 لوحة المتصدرين        — نقاط / دعوات + ترتيبك أنت شخصياً
 4) 🛒 تأكيد الشراء          — تفاصيل السعر والرصيد قبل الخصم مباشرة
 5) 🔔 تنبيه عودة المخزون    — يخبرك البوت فور توفّر المنتج الذي نفد
 6) 🏠 زر الرجوع للرئيسية    — كان معطّلاً (back_main) وأصبح يعمل

📌 التركيب: import bot12 داخل bot.py (قبل تسجيل معالجات bot.py العامة)
=====================================================================
"""

import html
from datetime import datetime

from telebot import types

from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, RANKS, t
from database import (bot_config, save_json, DB_CONFIG, get_user,
                      get_top_users_by_points, get_top_users_by_invites,
                      engine, text as sql_text)

# =====================================================================
# 🌍 ترجمات الحزمة (5 لغات)
# =====================================================================
UX = {
    "ar": {
        "profile": "🧾 بطاقتي",
        "profile_title": "🧾 <b>━━ بطاقة العضوية ━━</b>",
        "badges": "🎖️ إنجازاتي",
        "badges_title": "🎖️ <b>━━ الإنجازات والشارات ━━</b>",
        "badges_desc": "افتح الشارات بنشاطك داخل البوت!",
        "leaderboard": "🏆 المتصدرون",
        "lb_points": "💎 حسب النقاط",
        "lb_invites": "🔗 حسب الدعوات",
        "your_rank": "ترتيبك",
        "not_ranked": "خارج القائمة",
        "unlocked": "مفتوحة",
        "locked": "مقفلة",
        "next_rank": "الرتبة القادمة",
        "max_rank": "🎉 وصلت لأعلى رتبة!",
        "points_left": "نقطة متبقية",
        "wallet": "المحفظة",
        "rank": "الرتبة",
        "discount": "الخصم",
        "streak": "السلسلة",
        "invites": "الدعوات",
        "purchases": "المشتريات",
        "member_since": "عضو منذ",
        "days": "يوم",
        "confirm_title": "🛒 <b>━━ تأكيد الشراء ━━</b>",
        "product": "المنتج",
        "plan": "الباقة",
        "base_price": "السعر الأصلي",
        "your_discount": "خصمك",
        "final_price": "المبلغ المطلوب",
        "balance_now": "رصيدك الآن",
        "balance_after": "رصيدك بعد الشراء",
        "confirm_btn": "✅ تأكيد وشراء",
        "cancel_btn": "❌ إلغاء",
        "not_enough": "❌ رصيدك لا يكفي لهذه العملية",
        "out_of_stock": "❌ نفدت الكمية حالياً",
        "notify_btn": "🔔 نبّهني عند التوفر",
        "notify_on": "✅ سننبّهك فور عودة المنتج!",
        "notify_already": "🔔 أنت مسجّل بالفعل لهذا التنبيه",
        "restock_alert": "🔔 <b>عاد للمخزون!</b>\n\n📦 {prod} — {plan}\n\n💨 <i>سارع بالشراء قبل النفاد!</i>",
        "back_home": "🏠 الرئيسية",
        "refresh": "🔄 تحديث",
        "top_empty": "📭 لا توجد بيانات كافية بعد",
        "best_seller": "🔥 الأكثر مبيعاً",
    },
    "en": {
        "profile": "🧾 My Card", "profile_title": "🧾 <b>━━ MEMBER CARD ━━</b>",
        "badges": "🎖️ Achievements", "badges_title": "🎖️ <b>━━ ACHIEVEMENTS ━━</b>",
        "badges_desc": "Unlock badges by being active!",
        "leaderboard": "🏆 Leaderboard", "lb_points": "💎 By Points", "lb_invites": "🔗 By Invites",
        "your_rank": "Your position", "not_ranked": "Not ranked yet",
        "unlocked": "Unlocked", "locked": "Locked",
        "next_rank": "Next rank", "max_rank": "🎉 You reached the top rank!",
        "points_left": "points left", "wallet": "Wallet", "rank": "Rank", "discount": "Discount",
        "streak": "Streak", "invites": "Invites", "purchases": "Purchases",
        "member_since": "Member since", "days": "days",
        "confirm_title": "🛒 <b>━━ CONFIRM PURCHASE ━━</b>",
        "product": "Product", "plan": "Plan", "base_price": "Base price",
        "your_discount": "Your discount", "final_price": "Total", "balance_now": "Balance now",
        "balance_after": "Balance after", "confirm_btn": "✅ Confirm & Buy", "cancel_btn": "❌ Cancel",
        "not_enough": "❌ Not enough balance", "out_of_stock": "❌ Out of stock",
        "notify_btn": "🔔 Notify me when available", "notify_on": "✅ We'll ping you when it's back!",
        "notify_already": "🔔 You're already on the list",
        "restock_alert": "🔔 <b>BACK IN STOCK!</b>\n\n📦 {prod} — {plan}\n\n💨 <i>Grab it before it's gone!</i>",
        "back_home": "🏠 Home", "refresh": "🔄 Refresh",
        "top_empty": "📭 Not enough data yet", "best_seller": "🔥 Best seller",
    },
    "fr": {
        "profile": "🧾 Ma carte", "profile_title": "🧾 <b>━━ CARTE MEMBRE ━━</b>",
        "badges": "🎖️ Succès", "badges_title": "🎖️ <b>━━ SUCCÈS ━━</b>",
        "badges_desc": "Débloquez des badges en étant actif !",
        "leaderboard": "🏆 Classement", "lb_points": "💎 Par points", "lb_invites": "🔗 Par invitations",
        "your_rank": "Votre position", "not_ranked": "Non classé",
        "unlocked": "Débloqué", "locked": "Verrouillé",
        "next_rank": "Rang suivant", "max_rank": "🎉 Rang maximum atteint !",
        "points_left": "points restants", "wallet": "Portefeuille", "rank": "Rang", "discount": "Réduction",
        "streak": "Série", "invites": "Invitations", "purchases": "Achats",
        "member_since": "Membre depuis", "days": "jours",
        "confirm_title": "🛒 <b>━━ CONFIRMER L'ACHAT ━━</b>",
        "product": "Produit", "plan": "Forfait", "base_price": "Prix de base",
        "your_discount": "Votre réduction", "final_price": "Total", "balance_now": "Solde actuel",
        "balance_after": "Solde après", "confirm_btn": "✅ Confirmer", "cancel_btn": "❌ Annuler",
        "not_enough": "❌ Solde insuffisant", "out_of_stock": "❌ Rupture de stock",
        "notify_btn": "🔔 Me prévenir", "notify_on": "✅ Nous vous préviendrons !",
        "notify_already": "🔔 Déjà inscrit",
        "restock_alert": "🔔 <b>DE RETOUR EN STOCK !</b>\n\n📦 {prod} — {plan}\n\n💨 <i>Dépêchez-vous !</i>",
        "back_home": "🏠 Accueil", "refresh": "🔄 Actualiser",
        "top_empty": "📭 Pas encore assez de données", "best_seller": "🔥 Meilleure vente",
    },
    "es": {
        "profile": "🧾 Mi tarjeta", "profile_title": "🧾 <b>━━ TARJETA DE MIEMBRO ━━</b>",
        "badges": "🎖️ Logros", "badges_title": "🎖️ <b>━━ LOGROS ━━</b>",
        "badges_desc": "¡Desbloquea insignias siendo activo!",
        "leaderboard": "🏆 Top", "lb_points": "💎 Por puntos", "lb_invites": "🔗 Por invitaciones",
        "your_rank": "Tu posición", "not_ranked": "Sin clasificar",
        "unlocked": "Desbloqueado", "locked": "Bloqueado",
        "next_rank": "Siguiente rango", "max_rank": "🎉 ¡Rango máximo alcanzado!",
        "points_left": "puntos restantes", "wallet": "Cartera", "rank": "Rango", "discount": "Descuento",
        "streak": "Racha", "invites": "Invitaciones", "purchases": "Compras",
        "member_since": "Miembro desde", "days": "días",
        "confirm_title": "🛒 <b>━━ CONFIRMAR COMPRA ━━</b>",
        "product": "Producto", "plan": "Plan", "base_price": "Precio base",
        "your_discount": "Tu descuento", "final_price": "Total", "balance_now": "Saldo actual",
        "balance_after": "Saldo después", "confirm_btn": "✅ Confirmar", "cancel_btn": "❌ Cancelar",
        "not_enough": "❌ Saldo insuficiente", "out_of_stock": "❌ Agotado",
        "notify_btn": "🔔 Avisarme", "notify_on": "✅ ¡Te avisaremos!",
        "notify_already": "🔔 Ya estás en la lista",
        "restock_alert": "🔔 <b>¡DE VUELTA EN STOCK!</b>\n\n📦 {prod} — {plan}\n\n💨 <i>¡Corre!</i>",
        "back_home": "🏠 Inicio", "refresh": "🔄 Actualizar",
        "top_empty": "📭 Aún no hay datos", "best_seller": "🔥 Más vendido",
    },
    "vi": {
        "profile": "🧾 Thẻ của tôi", "profile_title": "🧾 <b>━━ THẺ THÀNH VIÊN ━━</b>",
        "badges": "🎖️ Thành tựu", "badges_title": "🎖️ <b>━━ THÀNH TỰU ━━</b>",
        "badges_desc": "Mở khóa huy hiệu bằng hoạt động của bạn!",
        "leaderboard": "🏆 BXH", "lb_points": "💎 Theo điểm", "lb_invites": "🔗 Theo lời mời",
        "your_rank": "Vị trí của bạn", "not_ranked": "Chưa xếp hạng",
        "unlocked": "Đã mở", "locked": "Đã khóa",
        "next_rank": "Hạng tiếp theo", "max_rank": "🎉 Bạn đã đạt hạng cao nhất!",
        "points_left": "điểm nữa", "wallet": "Ví", "rank": "Hạng", "discount": "Giảm giá",
        "streak": "Chuỗi", "invites": "Lời mời", "purchases": "Đơn hàng",
        "member_since": "Thành viên từ", "days": "ngày",
        "confirm_title": "🛒 <b>━━ XÁC NHẬN MUA ━━</b>",
        "product": "Sản phẩm", "plan": "Gói", "base_price": "Giá gốc",
        "your_discount": "Giảm giá", "final_price": "Tổng", "balance_now": "Số dư",
        "balance_after": "Số dư sau", "confirm_btn": "✅ Xác nhận", "cancel_btn": "❌ Hủy",
        "not_enough": "❌ Không đủ số dư", "out_of_stock": "❌ Hết hàng",
        "notify_btn": "🔔 Báo tôi khi có hàng", "notify_on": "✅ Sẽ báo bạn ngay!",
        "notify_already": "🔔 Bạn đã trong danh sách",
        "restock_alert": "🔔 <b>CÓ HÀNG TRỞ LẠI!</b>\n\n📦 {prod} — {plan}\n\n💨 <i>Nhanh tay!</i>",
        "back_home": "🏠 Trang chính", "refresh": "🔄 Làm mới",
        "top_empty": "📭 Chưa đủ dữ liệu", "best_seller": "🔥 Bán chạy nhất",
    },
}


def ux(lang, key, **kwargs):
    value = UX.get(lang, UX["en"]).get(key) or UX["en"].get(key, key)
    if kwargs:
        try:
            value = value.format(**kwargs)
        except Exception:
            pass
    return value


# =====================================================================
# 🔧 أدوات
# =====================================================================
def _esc(value):
    try:
        return html.escape(str(value))
    except Exception:
        return str(value)


def _lang(uid, user=None):
    user = user or get_user(str(uid)) or {}
    return user.get("lang", "ar")


def bar(current, total, length=10, full="█", empty="░"):
    """شريط تقدّم نصي."""
    try:
        total = max(1, int(total))
        ratio = min(1.0, max(0.0, float(current) / total))
    except Exception:
        ratio = 0.0
    filled = int(round(ratio * length))
    return f"{full * filled}{empty * (length - filled)} {int(ratio * 100)}%"


def _rank_progress(user):
    """يرجع (اسم الرتبة القادمة، النقاط الناقصة، النسبة الحالية، الحد الأدنى الحالي)."""
    lang = user.get("lang", "ar")
    acc = user.get("accumulated_points", 0) or 0
    ladder = sorted(RANKS.values(), key=lambda r: r["points_needed"])
    previous = 0
    for rank in ladder:
        if acc < rank["points_needed"]:
            name = rank.get(f"name_{lang}") or rank.get("name_en")
            span = max(1, rank["points_needed"] - previous)
            done = acc - previous
            return name, rank["points_needed"] - acc, done, span
        previous = rank["points_needed"]
    return None, 0, 1, 1


def _nav(lang, back_cb="back_main", refresh_cb=None, extra_rows=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    for row in (extra_rows or []):
        m.add(*row)
    tail = []
    if refresh_cb:
        tail.append(types.InlineKeyboardButton(ux(lang, "refresh"), callback_data=refresh_cb))
    tail.append(types.InlineKeyboardButton(ux(lang, "back_home"), callback_data="back_main"))
    if back_cb and back_cb != "back_main":
        tail.insert(0, types.InlineKeyboardButton(t(lang, "btn_back"), callback_data=back_cb))
    m.add(*tail)
    return m


def _render(call, text_body, markup=None):
    try:
        bot.edit_message_text(text_body, call.message.chat.id, call.message.message_id,
                              reply_markup=markup, parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(call.message.chat.id, text_body, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass


def _ack(call, text_body=None, alert=False):
    try:
        bot.answer_callback_query(call.id, text_body, show_alert=alert)
    except Exception:
        pass


# =====================================================================
# 🎖️ نظام الشارات
# =====================================================================
BADGES = [
    {"id": "rookie", "emoji": "🌱", "field": None, "target": 1,
     "name": {"ar": "بداية الطريق", "en": "First Steps", "fr": "Premiers pas",
              "es": "Primeros pasos", "vi": "Bước đầu"}},
    {"id": "inviter", "emoji": "🔗", "field": "invite_count", "target": 1,
     "name": {"ar": "أول دعوة", "en": "First Invite", "fr": "Première invitation",
              "es": "Primera invitación", "vi": "Lời mời đầu"}},
    {"id": "ambassador", "emoji": "🌟", "field": "invite_count", "target": 5,
     "name": {"ar": "سفير المتجر", "en": "Ambassador", "fr": "Ambassadeur",
              "es": "Embajador", "vi": "Đại sứ"}},
    {"id": "legend_inviter", "emoji": "👑", "field": "invite_count", "target": 25,
     "name": {"ar": "أسطورة الدعوات", "en": "Invite Legend", "fr": "Légende des invitations",
              "es": "Leyenda de invitaciones", "vi": "Huyền thoại mời"}},
    {"id": "first_buy", "emoji": "🛍️", "field": "purchases_count", "target": 1,
     "name": {"ar": "أول عملية شراء", "en": "First Purchase", "fr": "Premier achat",
              "es": "Primera compra", "vi": "Đơn đầu tiên"}},
    {"id": "shopper", "emoji": "🛒", "field": "purchases_count", "target": 5,
     "name": {"ar": "متسوّق نشط", "en": "Active Shopper", "fr": "Acheteur actif",
              "es": "Comprador activo", "vi": "Người mua tích cực"}},
    {"id": "trader", "emoji": "💼", "field": "purchases_count", "target": 20,
     "name": {"ar": "تاجر محترف", "en": "Pro Trader", "fr": "Trader pro",
              "es": "Comerciante pro", "vi": "Nhà buôn chuyên"}},
    {"id": "streak3", "emoji": "🔥", "field": "streak_days", "target": 3,
     "name": {"ar": "سلسلة 3 أيام", "en": "3-Day Streak", "fr": "Série 3 jours",
              "es": "Racha 3 días", "vi": "Chuỗi 3 ngày"}},
    {"id": "streak7", "emoji": "💥", "field": "streak_days", "target": 7,
     "name": {"ar": "سلسلة أسبوع", "en": "7-Day Streak", "fr": "Série 7 jours",
              "es": "Racha 7 días", "vi": "Chuỗi 7 ngày"}},
    {"id": "streak30", "emoji": "⚡", "field": "streak_days", "target": 30,
     "name": {"ar": "سلسلة شهر", "en": "30-Day Streak", "fr": "Série 30 jours",
              "es": "Racha 30 días", "vi": "Chuỗi 30 ngày"}},
    {"id": "collector", "emoji": "💎", "field": "accumulated_points", "target": 1000,
     "name": {"ar": "جامع النقاط", "en": "Point Collector", "fr": "Collectionneur",
              "es": "Coleccionista", "vi": "Nhà sưu tầm"}},
    {"id": "whale", "emoji": "🏆", "field": "accumulated_points", "target": 10000,
     "name": {"ar": "نخبة المتجر", "en": "Store Elite", "fr": "Élite",
              "es": "Élite", "vi": "Tinh hoa"}},
    {"id": "vip", "emoji": "👑", "field": "vip", "target": 1,
     "name": {"ar": "عضو VIP", "en": "VIP Member", "fr": "Membre VIP",
              "es": "Miembro VIP", "vi": "Thành viên VIP"}},
]


def badge_state(user):
    """يرجع قائمة (badge, current, unlocked)."""
    result = []
    for badge in BADGES:
        field = badge["field"]
        if field is None:
            current = 1
        elif field == "vip":
            current = 1 if user.get("vip") else 0
        else:
            current = int(user.get(field, 0) or 0)
        result.append((badge, current, current >= badge["target"]))
    return result


def badge_line(user, limit=5):
    """سطر مختصر بأهم الشارات المفتوحة — يُستخدم داخل بطاقة الملف."""
    unlocked = [b["emoji"] for b, _c, ok in badge_state(user) if ok]
    if not unlocked:
        return "—"
    shown = unlocked[-limit:]
    extra = f" +{len(unlocked) - len(shown)}" if len(unlocked) > len(shown) else ""
    return " ".join(shown) + extra


# =====================================================================
# 🔥 الأكثر مبيعاً
# =====================================================================
def top_selling_products(days=30, limit=None):
    """يرجع [(المنتج، عدد المبيعات)] مرتبة تنازلياً خلال المدة المحددة."""
    from datetime import timedelta
    since = datetime.now() - timedelta(days=days)
    counter = {}
    for sale in bot_config.get("sales_log", []) or []:
        try:
            if datetime.fromisoformat(sale.get("date", "")) < since:
                continue
        except Exception:
            continue
        product = sale.get("product")
        if product:
            counter[product] = counter.get(product, 0) + 1
    ranked = sorted(counter.items(), key=lambda item: -item[1])
    return ranked[:limit] if limit else ranked


def product_sales_count(product, days=30):
    for name, count in top_selling_products(days):
        if name == product:
            return count
    return 0


# =====================================================================
# 🧾 بطاقة الملف الشخصي
# =====================================================================
def profile_text(uid):
    user = get_user(str(uid)) or {}
    lang = _lang(uid, user)
    next_rank, remaining, done, span = _rank_progress(user)

    if next_rank:
        progress = (f"│ 🎯 {ux(lang, 'next_rank')}: <b>{_esc(next_rank)}</b>\n"
                    f"│ {bar(done, span)}\n"
                    f"│ ⏳ {remaining} {ux(lang, 'points_left')}\n")
    else:
        progress = f"│ {ux(lang, 'max_rank')}\n"

    unlocked = sum(1 for _b, _c, ok in badge_state(user) if ok)
    join_date = (user.get("join_date") or "")[:10] or "—"
    vip_line = "│ 👑 <b>VIP</b>\n" if user.get("vip") else ""

    return (
        f"{ux(lang, 'profile_title')}\n\n"
        f"👤 <b>{_esc(user.get('username') or 'User')}</b>\n"
        f"🆔 <code>{_esc(uid)}</code>\n\n"
        f"┌────────────────────────\n"
        f"{vip_line}"
        f"│ 💰 {ux(lang, 'wallet')}: <b>{user.get('points', 0) or 0}</b> 💎\n"
        f"│ 🏅 {ux(lang, 'rank')}: <b>{_esc(user.get('rank', '—'))}</b>\n"
        f"│ 🎁 {ux(lang, 'discount')}: <b>{int((user.get('rank_discount', 0) or 0) * 100)}%</b>\n"
        f"├────────────────────────\n"
        f"{progress}"
        f"├────────────────────────\n"
        f"│ 🔥 {ux(lang, 'streak')}: <b>{user.get('streak_days', 0) or 0}</b> {ux(lang, 'days')}\n"
        f"│ 🔗 {ux(lang, 'invites')}: <b>{user.get('invite_count', 0) or 0}</b>\n"
        f"│ 🛍️ {ux(lang, 'purchases')}: <b>{user.get('purchases_count', 0) or 0}</b>\n"
        f"│ 🎖️ {ux(lang, 'badges')}: <b>{unlocked}/{len(BADGES)}</b>  {badge_line(user)}\n"
        f"│ 📅 {ux(lang, 'member_since')}: {join_date}\n"
        f"└────────────────────────"
    )


@bot.callback_query_handler(func=lambda c: c.data == "menu_profile")
def show_profile(call):
    uid = str(call.from_user.id)
    lang = _lang(uid)
    _ack(call)
    rows = [[
        types.InlineKeyboardButton(ux(lang, "badges"), callback_data="menu_badges"),
        types.InlineKeyboardButton(ux(lang, "leaderboard"), callback_data="menu_leaderboard"),
    ]]
    _render(call, profile_text(uid), _nav(lang, back_cb="back_account",
                                          refresh_cb="menu_profile", extra_rows=rows))


# =====================================================================
# 🎖️ شاشة الإنجازات
# =====================================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu_badges")
def show_badges(call):
    uid = str(call.from_user.id)
    user = get_user(uid) or {}
    lang = _lang(uid, user)
    _ack(call)

    states = badge_state(user)
    unlocked = sum(1 for _b, _c, ok in states if ok)

    lines = [ux(lang, "badges_title"), f"\n<i>{ux(lang, 'badges_desc')}</i>\n",
             f"📊 <b>{unlocked}/{len(states)}</b>  {bar(unlocked, len(states))}\n"]

    for badge, current, ok in states:
        name = badge["name"].get(lang) or badge["name"]["en"]
        if ok:
            lines.append(f"✅ {badge['emoji']} <b>{name}</b>")
        else:
            lines.append(f"🔒 {badge['emoji']} {name} — {current}/{badge['target']}")

    _render(call, "\n".join(lines), _nav(lang, back_cb="menu_profile", refresh_cb="menu_badges"))


# =====================================================================
# 🏆 لوحة المتصدرين
# =====================================================================
MEDALS = ["🥇", "🥈", "🥉"]


def _position_of(uid, column):
    """ترتيب المستخدم ضمن كل الأعضاء حسب عمود معيّن."""
    try:
        with engine.connect() as conn:
            row = conn.execute(sql_text(
                f"SELECT COUNT(*) FROM users WHERE COALESCE({column}, 0) > "
                f"(SELECT COALESCE({column}, 0) FROM users WHERE uid = :uid)"
            ), {"uid": str(uid)}).fetchone()
            return (row[0] + 1) if row else None
    except Exception:
        return None


def leaderboard_text(uid, mode="points"):
    lang = _lang(uid)
    if mode == "invites":
        rows = get_top_users_by_invites(10)
        column, unit = "invite_count", "🔗"
    else:
        rows = get_top_users_by_points(10)
        column, unit = "accumulated_points", "💎"

    out = [t(lang, "leaderboard_title")]
    if not rows:
        out.append(f"\n{ux(lang, 'top_empty')}")
    else:
        for index, row in enumerate(rows, start=1):
            medal = MEDALS[index - 1] if index <= 3 else f"<b>{index}.</b>"
            name = _esc(row.get("username") or "User")
            value = row.get(column, 0) or 0
            highlight = " ⬅️" if str(row.get("uid")) == str(uid) else ""
            out.append(f"{medal} {name} — <b>{value}</b> {unit}{highlight}")

    position = _position_of(uid, column)
    out.append(f"\n📍 <b>{ux(lang, 'your_rank')}:</b> "
               f"{('#' + str(position)) if position else ux(lang, 'not_ranked')}")
    return "\n".join(out)


def _leaderboard_kb(lang, mode):
    points_label = ("• " if mode == "points" else "") + ux(lang, "lb_points")
    invites_label = ("• " if mode == "invites" else "") + ux(lang, "lb_invites")
    rows = [[
        types.InlineKeyboardButton(points_label, callback_data="lb_points"),
        types.InlineKeyboardButton(invites_label, callback_data="lb_invites"),
    ]]
    return _nav(lang, back_cb="menu_profile", refresh_cb=f"lb_{mode}", extra_rows=rows)


@bot.callback_query_handler(func=lambda c: c.data in ("menu_leaderboard", "lb_points", "lb_invites"))
def show_leaderboard(call):
    uid = str(call.from_user.id)
    lang = _lang(uid)
    mode = "invites" if call.data == "lb_invites" else "points"
    _ack(call)
    _render(call, leaderboard_text(uid, mode), _leaderboard_kb(lang, mode))


# =====================================================================
# 🔔 تنبيه عودة المخزون
# =====================================================================
def _watchers():
    return bot_config.setdefault("stock_watchers", {})


def _watch_key(prod, plan):
    return f"{prod}||{plan}"


@bot.callback_query_handler(func=lambda c: c.data.startswith("notifyme|"))
def subscribe_restock(call):
    uid = str(call.from_user.id)
    lang = _lang(uid)
    try:
        _, prod, plan = call.data.split("|")
    except ValueError:
        return _ack(call, "❌")

    watchers = _watchers()
    entry = watchers.setdefault(_watch_key(prod, plan), [])
    if uid in entry:
        return _ack(call, ux(lang, "notify_already"), alert=True)
    entry.append(uid)
    save_json(DB_CONFIG, bot_config)
    _ack(call, ux(lang, "notify_on"), alert=True)


def notify_restock(prod, plan):
    """يُستدعى بعد إضافة مفاتيح جديدة — يبلّغ كل من طلب التنبيه."""
    watchers = _watchers()
    key = _watch_key(prod, plan)
    subscribers = watchers.get(key) or []
    if not subscribers:
        return 0

    sent = 0
    for uid in list(subscribers):
        try:
            user = get_user(str(uid)) or {}
            if not user.get("notifications_on", True):
                continue
            lang = user.get("lang", "ar")
            bot.send_message(int(uid), ux(lang, "restock_alert", prod=_esc(prod), plan=_esc(plan)),
                             reply_markup=types.InlineKeyboardMarkup().add(
                                 types.InlineKeyboardButton(
                                     f"🛒 {prod}", callback_data=f"select_prod_{prod}")),
                             parse_mode="HTML")
            sent += 1
        except Exception:
            pass

    watchers[key] = []
    save_json(DB_CONFIG, bot_config)
    return sent


# =====================================================================
# 🛒 تأكيد الشراء (قبل خصم النقاط)
# =====================================================================
def _price_of(prod, plan, user):
    from database import prices_config
    from utils import get_active_flash_sale

    base = prices_config.get(prod, {}).get(plan, 0) or 0
    global_disc = bot_config.get("discount", 0) or 0
    rank_disc = user.get("rank_discount", 0.0) or 0.0
    flash = get_active_flash_sale()
    flash_disc = flash["discount"] if flash and flash.get("product") == prod else 0
    total_disc = global_disc + flash_disc
    final = int(base * (1 - total_disc / 100) * (1 - rank_disc))
    return base, total_disc, rank_disc, max(0, final)


@bot.callback_query_handler(func=lambda c: c.data.startswith("cbuy|"))
def confirm_purchase(call):
    uid = str(call.from_user.id)
    user = get_user(uid) or {}
    lang = _lang(uid, user)
    try:
        _, prod, plan = call.data.split("|")
    except ValueError:
        return _ack(call, "❌")

    from database import keys_store
    stock = len(keys_store.get(prod, {}).get(plan, []))
    if stock <= 0:
        return _ack(call, ux(lang, "out_of_stock"), alert=True)

    base, total_disc, rank_disc, final = _price_of(prod, plan, user)
    balance = user.get("points", 0) or 0
    _ack(call)

    body = (
        f"{ux(lang, 'confirm_title')}\n\n"
        f"┌────────────────────────\n"
        f"│ 📦 {ux(lang, 'product')}: <b>{_esc(prod)}</b>\n"
        f"│ ⏱️ {ux(lang, 'plan')}: <b>{_esc(plan)}</b>\n"
        f"│ 🏷️ {ux(lang, 'base_price')}: <s>{base}</s> 💎\n"
        f"│ 🎁 {ux(lang, 'your_discount')}: <b>{total_disc + int(rank_disc * 100)}%</b>\n"
        f"│ 💳 {ux(lang, 'final_price')}: <b>{final}</b> 💎\n"
        f"├────────────────────────\n"
        f"│ 💰 {ux(lang, 'balance_now')}: <b>{balance}</b> 💎\n"
        f"│ 📉 {ux(lang, 'balance_after')}: <b>{max(0, balance - final)}</b> 💎\n"
        f"└────────────────────────"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    if balance < final:
        body += f"\n\n{ux(lang, 'not_enough')}"
    else:
        markup.add(types.InlineKeyboardButton(ux(lang, "confirm_btn"),
                                              callback_data=f"buy_plan|{prod}|{plan}"))
    markup.add(types.InlineKeyboardButton(ux(lang, "cancel_btn"),
                                          callback_data=f"select_prod_{prod}"))
    _render(call, body, markup)


# =====================================================================
# 🏠 زر الرجوع للرئيسية (كان معطّلاً)
# =====================================================================
@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def back_to_main(call):
    uid = str(call.from_user.id)
    user = get_user(uid) or {}
    lang = _lang(uid, user)
    _ack(call)
    from keyboards import get_main_inline
    _render(call, t(lang, "main_menu_title", name=_esc(user.get("username") or "User")),
            get_main_inline(uid, lang))


# =====================================================================
# 📋 قائمة الأوامر داخل تيليجرام (زر Menu)
# =====================================================================
USER_COMMANDS = [
    ("start", {"ar": "القائمة الرئيسية", "en": "Main menu", "fr": "Menu principal",
               "es": "Menú principal", "vi": "Menu chính"}),
    ("help", {"ar": "المساعدة", "en": "Help", "fr": "Aide", "es": "Ayuda", "vi": "Trợ giúp"}),
    ("pp", {"ar": "دليل الأوامر", "en": "Commands guide", "fr": "Guide des commandes",
            "es": "Guía de comandos", "vi": "Hướng dẫn lệnh"}),
    ("id", {"ar": "معرّفي", "en": "My Telegram ID", "fr": "Mon ID", "es": "Mi ID", "vi": "ID của tôi"}),
    ("cancel", {"ar": "إلغاء العملية الحالية", "en": "Cancel current step",
                "fr": "Annuler l'étape", "es": "Cancelar paso", "vi": "Hủy bước hiện tại"}),
]

ADMIN_COMMANDS = [
    ("dash", "لوحة القيادة"),
    ("start", "القائمة الرئيسية"),
    ("stars", "إدارة النجوم"),
    ("games", "ألعاب القناة"),
    ("cancel", "إلغاء العملية الحالية"),
]


def setup_bot_commands():
    """يسجّل أوامر البوت في تيليجرام (زر Menu) لكل لغة + للأدمن."""
    from telebot import types as _types
    done = 0
    try:
        default = [_types.BotCommand(name, labels["en"]) for name, labels in USER_COMMANDS]
        bot.set_my_commands(default)
        done += 1
        for lang in ("ar", "fr", "es", "vi"):
            localized = [_types.BotCommand(name, labels.get(lang, labels["en"]))
                         for name, labels in USER_COMMANDS]
            bot.set_my_commands(localized, language_code=lang)
            done += 1

        admin_list = [_types.BotCommand(name, label) for name, label in ADMIN_COMMANDS]
        for admin_id in (ADMIN_PRIMARY, ADMIN_SECONDARY):
            try:
                bot.set_my_commands(admin_list, scope=_types.BotCommandScopeChat(admin_id))
                done += 1
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ تعذّر ضبط قائمة الأوامر: {e}")
    return done


print("=" * 55)
print("✅ bot12.py — حزمة تجربة المستخدم")
print("🧾 بطاقة العضوية | 🎖️ الشارات | 🏆 المتصدرون | 🔥 الأكثر مبيعاً")
print("🛒 تأكيد الشراء | 🔔 تنبيه عودة المخزون | 🏠 back_main")
print("=" * 55)
