"""
══════════════════════════════════════════════════════════════════════════════
║                    keyboards.py - COMPLETE KEYBOARDS v3.0                   ║
║            🎹 جميع الكيبوردات + 5 لغات كاملة (ar/en/fr/es/vi)              ║
══════════════════════════════════════════════════════════════════════════════
║  Developer: @fkLJh00302                                                     ║
║  المستودع الأصلي: ilyesguers/Telegram-bot-2                                 ║
║  يتوافق مع: bot.py, bot2.py, bot3.py, bot4.py, bot5.py, bot6.py, bot7.py  ║
══════════════════════════════════════════════════════════════════════════════
"""

from telebot import types
from config import LOCALES, CHANNEL_LINK, CHANNEL_ID, ADMIN_PRIMARY, ADMIN_SECONDARY, t, TICKET_CATEGORIES
from database import get_user


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     🌐 كيبورد اختيار اللغة                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_lang_inline():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="setlang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="setlang_vi")
    )
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     📢 كيبورد الانضمام للقناة                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_join_inline(lang):
    join_texts = {
        "ar": ("📢 اشترك في القناة", "✅ تحققت - تحقق"),
        "en": ("📢 Join Our Channel", "✅ I've Joined - Verify"),
        "fr": ("📢 Rejoindre la chaîne", "✅ Rejoint - Vérifier"),
        "es": ("📢 Únete al Canal", "✅ Me uní - Verificar"),
        "vi": ("📢 Tham gia Kênh", "✅ Đã tham gia - Xác minh")
    }
    join_txt, verify_txt = join_texts.get(lang, join_texts["en"])
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(join_txt, url=CHANNEL_LINK))
    m.add(types.InlineKeyboardButton(verify_txt, callback_data="check_join"))
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     🏠 الكيبورد الرئيسي للمستخدم                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_main_keyboard(uid, lang):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton(t(lang, "btn_account")))
    m.add(
        types.KeyboardButton(t(lang, "btn_shop")),
        types.KeyboardButton(t(lang, "btn_rewards"))
    )
    m.add(
        types.KeyboardButton(t(lang, "btn_entertainment")),
        types.KeyboardButton(t(lang, "btn_support"))
    )
    m.add(
        types.KeyboardButton("👑 VIP"),
        types.KeyboardButton("⭐ Stars")
    )
    # 🎮 Mini Games
    m.add(types.KeyboardButton("🎮 Mini Games"))
    m.add(types.KeyboardButton(t(lang, "btn_settings")))
    u = get_user(str(uid)) or {}
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin", False):
        m.add(types.KeyboardButton(t(lang, "btn_admin")))
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     👤 قائمة الحساب                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_account_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_balance"), callback_data="menu_balance"),
        types.InlineKeyboardButton(t(lang, "btn_my_id"), callback_data="menu_myid")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_my_rank"), callback_data="menu_rank"),
        types.InlineKeyboardButton(t(lang, "btn_referral"), callback_data="menu_referral")
    )
    m.add(types.InlineKeyboardButton(t(lang, "btn_my_purchases"), callback_data="menu_purchases"))
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     🎁 قائمة المكافآت                                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_rewards_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_daily_bonus"), callback_data="menu_daily"),
        types.InlineKeyboardButton(t(lang, "btn_redeem_code"), callback_data="menu_redeem")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_quests"), callback_data="menu_quests"),
        types.InlineKeyboardButton(t(lang, "btn_flash_sale"), callback_data="menu_flash")
    )
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     🎮 قائمة الترفيه                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_entertainment_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_lootbox"), callback_data="menu_lootbox"),
        types.InlineKeyboardButton(t(lang, "btn_wheel"), callback_data="menu_wheel")
    )
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     💬 قائمة الدعم                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_support_menu(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_new_ticket"), callback_data="menu_new_ticket"),
        types.InlineKeyboardButton(t(lang, "btn_my_tickets"), callback_data="menu_my_tickets")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_request_product"), callback_data="menu_request_product"),
        types.InlineKeyboardButton(t(lang, "btn_faq"), callback_data="menu_faq")
    )
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     ⚙️ قائمة الإعدادات                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_settings_menu(lang, u):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(t(lang, "btn_change_lang"), callback_data="menu_lang"))
    notif_status = u.get("notifications_on", True)
    notif_labels = {
        "ar": ("🔔 الإشعارات: مفعّلة", "🔕 الإشعارات: معطّلة"),
        "en": ("🔔 Notifications: ON", "🔕 Notifications: OFF"),
        "fr": ("🔔 Notifications: ON", "🔕 Notifications: OFF"),
        "es": ("🔔 Notificaciones: ON", "🔕 Notificaciones: OFF"),
        "vi": ("🔔 Thông báo: BẬT", "🔕 Thông báo: TẮT"),
    }
    on_txt, off_txt = notif_labels.get(lang, notif_labels["en"])
    notif_text = on_txt if notif_status else off_txt
    m.add(
        types.InlineKeyboardButton(notif_text, callback_data="menu_notif"),
        types.InlineKeyboardButton(t(lang, "btn_theme"), callback_data="menu_theme")
    )
    m.add(
        types.InlineKeyboardButton(t(lang, "btn_privacy"), callback_data="menu_privacy"),
        types.InlineKeyboardButton(t(lang, "btn_about"), callback_data="menu_about")
    )
    m.add(types.InlineKeyboardButton("💻 " + t(lang, "btn_bot_dev"), url="https://t.me/fkLJh00302"))
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     🎫 قائمة أنواع التذاكر                                ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_ticket_categories(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_key, cat_names in TICKET_CATEGORIES.items():
        name = cat_names.get(lang, cat_names.get("en", cat_key))
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"tcat_{cat_key}"))
    m.add(*buttons)
    m.add(types.InlineKeyboardButton(t(lang, "btn_back"), callback_data="back_support"))
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║                    🔴🔴🔴 كيبوردات الأدمن 🔴🔴🔴                         ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


# ───────────────────────── 👑 اللوحة الرئيسية ─────────────────────────

def get_admin_keyboard():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(
        types.KeyboardButton("📦 المنتجات"),
        types.KeyboardButton("🔑 المفاتيح")
    )
    m.add(
        types.KeyboardButton("👥 الأعضاء"),
        types.KeyboardButton("🎫 التذاكر")
    )
    m.add(
        types.KeyboardButton("💰 المبيعات"),
        types.KeyboardButton("📢 التسويق")
    )
    m.add(
        types.KeyboardButton("⚡ عروض خاطفة"),
        types.KeyboardButton("🎁 Giveaway")
    )
    m.add(
        types.KeyboardButton("👑 إدارة VIP"),
        types.KeyboardButton("📦 التجديد التلقائي")
    )
    m.add(
        types.KeyboardButton("📨 رسائل القناة"),
        types.KeyboardButton("🎮 الألعاب")
    )
    m.add(
        types.KeyboardButton("🛡️ مكافحة الرشق"),
        types.KeyboardButton("🔧 استعادة المشتريات")
    )
    m.add(
        types.KeyboardButton("⚙️ النظام"),
        types.KeyboardButton("📊 الإحصائيات")
    )
    m.add(
        types.KeyboardButton("💡 الطلبات"),
        types.KeyboardButton("🛠️ وضع الصيانة")
    )
    m.add(types.KeyboardButton("🔙 العودة"))
    return m


# ───────────────────────── 📦 المنتجات ─────────────────────────

def admin_products_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("➕ إضافة", callback_data="admp_add"),
        types.InlineKeyboardButton("❌ حذف", callback_data="admp_del")
    )
    m.add(types.InlineKeyboardButton("💵 الأسعار", callback_data="admp_prices"))
    return m


# ───────────────────────── 🔑 المفاتيح ─────────────────────────

def admin_keys_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🔑 إضافة", callback_data="admk_add"),
        types.InlineKeyboardButton("👁️ عرض", callback_data="admk_view")
    )
    m.add(
        types.InlineKeyboardButton("🔢 حذف واحد", callback_data="admk_del"),
        types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="admk_clear")
    )
    return m


# ───────────────────────── 👥 الأعضاء ─────────────────────────

def admin_members_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("👤 عرض عضو", callback_data="admm_view"))
    m.add(types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admm_charge"))
    return m


# ───────────────────────── 💰 المبيعات ─────────────────────────

def admin_sales_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎫 كود شحن", callback_data="adms_code"))
    m.add(types.InlineKeyboardButton("🔥 خصم عام", callback_data="adms_discount"))
    return m


# ───────────────────────── 📢 التسويق ─────────────────────────

def admin_marketing_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 إذاعة للمستخدمين", callback_data="admmk_broadcast"))
    m.add(types.InlineKeyboardButton("📤 نشر الأسعار بالقناة", callback_data="admmk_prices"))
    m.add(types.InlineKeyboardButton("📣 تسويق وهمي", callback_data="admmk_fake"))
    return m


# ───────────────────────── ⚡ العروض الخاطفة ─────────────────────────

def admin_flash_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚡ إنشاء عرض", callback_data="admf_create"))
    m.add(types.InlineKeyboardButton("❌ إلغاء العرض الحالي", callback_data="admf_cancel"))
    return m


# ───────────────────────── 🎁 Giveaway ─────────────────────────

def admin_giveaway_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("➕ إنشاء Giveaway جديد", callback_data="admgw_create"))
    m.add(types.InlineKeyboardButton("📋 عرض النشطة", callback_data="admgw_list"))
    m.add(types.InlineKeyboardButton("❌ إلغاء Giveaway", callback_data="admgw_cancel"))
    return m

def giveaway_reward_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("10 💎", callback_data="gwrew_10"),
        types.InlineKeyboardButton("25 💎", callback_data="gwrew_25"),
        types.InlineKeyboardButton("50 💎", callback_data="gwrew_50")
    )
    m.add(
        types.InlineKeyboardButton("100 💎", callback_data="gwrew_100"),
        types.InlineKeyboardButton("250 💎", callback_data="gwrew_250"),
        types.InlineKeyboardButton("500 💎", callback_data="gwrew_500")
    )
    m.add(types.InlineKeyboardButton("✏️ مخصص", callback_data="gwrew_custom"))
    return m

def giveaway_users_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("5 👥", callback_data="gwusr_5"),
        types.InlineKeyboardButton("10 👥", callback_data="gwusr_10"),
        types.InlineKeyboardButton("25 👥", callback_data="gwusr_25")
    )
    m.add(
        types.InlineKeyboardButton("50 👥", callback_data="gwusr_50"),
        types.InlineKeyboardButton("100 👥", callback_data="gwusr_100"),
        types.InlineKeyboardButton("∞ 👥", callback_data="gwusr_99999")
    )
    m.add(types.InlineKeyboardButton("✏️ مخصص", callback_data="gwusr_custom"))
    return m

def giveaway_hours_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1h", callback_data="gwhr_1"),
        types.InlineKeyboardButton("3h", callback_data="gwhr_3"),
        types.InlineKeyboardButton("6h", callback_data="gwhr_6")
    )
    m.add(
        types.InlineKeyboardButton("12h", callback_data="gwhr_12"),
        types.InlineKeyboardButton("24h", callback_data="gwhr_24"),
        types.InlineKeyboardButton("48h", callback_data="gwhr_48")
    )
    m.add(types.InlineKeyboardButton("72h", callback_data="gwhr_72"))
    return m


# ───────────────────────── 📨 رسائل القناة ─────────────────────────

def admin_channel_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📝 رسالة منسّقة", callback_data="admch_styled"))
    m.add(types.InlineKeyboardButton("📄 رسالة خام (HTML)", callback_data="admch_raw"))
    m.add(types.InlineKeyboardButton("🗑️ حذف رسالة", callback_data="admch_delete"))
    return m


# ───────────────────────── 🎮 إعدادات الألعاب ─────────────────────────

def admin_games_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎰 صندوق الحظ", callback_data="admg_lootbox"))
    m.add(types.InlineKeyboardButton("🎡 عجلة الحظ", callback_data="admg_wheel"))
    m.add(types.InlineKeyboardButton("🔥 المهام", callback_data="admg_quests"))
    return m


# ───────────────────────── ⚙️ النظام ─────────────────────────

def admin_system_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✨ المكافأة اليومية", callback_data="adsys_daily"))
    m.add(types.InlineKeyboardButton("🔗 مكافأة الإحالة", callback_data="adsys_invite"))
    return m


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║              🎨🎨🎨 كيبوردات إضافية متعددة اللغات 🎨🎨🎨               ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# النصوص المترجمة لجميع الكيبوردات
_TEXTS = {
    "back":     {"ar": "🔙 رجوع", "en": "🔙 Back", "fr": "🔙 Retour", "es": "🔙 Atrás", "vi": "🔙 Quay lại"},
    "confirm":  {"ar": "✅ تأكيد", "en": "✅ Confirm", "fr": "✅ Confirmer", "es": "✅ Confirmar", "vi": "✅ Xác nhận"},
    "cancel":   {"ar": "❌ إلغاء", "en": "❌ Cancel", "fr": "❌ Annuler", "es": "❌ Cancelar", "vi": "❌ Hủy"},
    # VIP
    "vip_stock":   {"ar": "📊 تفاصيل المخزون", "en": "📊 Stock Details", "fr": "📊 Détails Stock", "es": "📊 Detalles Stock", "vi": "📊 Chi tiết Kho"},
    "vip_weekly":  {"ar": "🎫 كود أسبوعي", "en": "🎫 Weekly Code", "fr": "🎫 Code Hebdomadaire", "es": "🎫 Código Semanal", "vi": "🎫 Mã tuần"},
    "vip_convert": {"ar": "⭐ تحويل Stars", "en": "⭐ Convert Stars", "fr": "⭐ Convertir Stars", "es": "⭐ Convertir Stars", "vi": "⭐ Đổi Stars"},
    "vip_renew":   {"ar": "🔄 تجديد VIP", "en": "🔄 Renew VIP", "fr": "🔄 Renouveler VIP", "es": "🔄 Renovar VIP", "vi": "🔄 Gia hạn VIP"},
    "vip_sub":     {"ar": "👑 اشتراك ({p} ⭐)", "en": "👑 Subscribe ({p} ⭐)", "fr": "👑 S'abonner ({p} ⭐)", "es": "👑 Suscribirse ({p} ⭐)", "vi": "👑 Đăng ký ({p} ⭐)"},
    "vip_convert_btn": {"ar": "⭐ تحويل Stars إلى نقاط", "en": "⭐ Stars to Points", "fr": "⭐ Stars en Points", "es": "⭐ Stars a Puntos", "vi": "⭐ Stars → Điểm"},
    # Games
    "rps":  {"ar": "✂️ حجرة ورقة مقص", "en": "✂️ Rock Paper Scissors", "fr": "✂️ Pierre Papier Ciseaux", "es": "✂️ Piedra Papel Tijeras", "vi": "✂️ Kéo Búa Bao"},
    "ttt":  {"ar": "⭕ X و O", "en": "⭕ Tic Tac Toe", "fr": "⭕ Morpion", "es": "⭕ Tres en Raya", "vi": "⭕ Cờ Caro"},
    "hunt": {"ar": "🐾 صيد الحيوانات", "en": "🐾 Animal Hunt", "fr": "🐾 Chasse Animaux", "es": "🐾 Caza Animales", "vi": "🐾 Săn Thú"},
    "my_stats": {"ar": "📊 إحصائياتي", "en": "📊 My Stats", "fr": "📊 Mes Stats", "es": "📊 Mis Stats", "vi": "📊 Thống kê"},
    "leaderboard": {"ar": "🏆 المتصدرون", "en": "🏆 Leaderboard", "fr": "🏆 Classement", "es": "🏆 Ranking", "vi": "🏆 BXH"},
    "mode_ai":  {"ar": "🤖 ضد الذكاء الاصطناعي", "en": "🤖 Play vs AI", "fr": "🤖 vs IA", "es": "🤖 vs IA", "vi": "🤖 vs AI"},
    "mode_pvp": {"ar": "👥 ضد لاعب حقيقي", "en": "👥 vs Player", "fr": "👥 vs Joueur", "es": "👥 vs Jugador", "vi": "👥 vs Người"},
    "rock":     {"ar": "🪨 حجرة", "en": "🪨 Rock", "fr": "🪨 Pierre", "es": "🪨 Piedra", "vi": "🪨 Đá"},
    "paper":    {"ar": "📄 ورقة", "en": "📄 Paper", "fr": "📄 Papier", "es": "📄 Papel", "vi": "📄 Giấy"},
    "scissors": {"ar": "✂️ مقص", "en": "✂️ Scissors", "fr": "✂️ Ciseaux", "es": "✂️ Tijeras", "vi": "✂️ Kéo"},
    # Leaderboard types
    "lb_points":   {"ar": "💎 بالنقاط", "en": "💎 By Points", "fr": "💎 Par Points", "es": "💎 Por Puntos", "vi": "💎 Theo Điểm"},
    "lb_invites":  {"ar": "👥 بالدعوات", "en": "👥 By Invites", "fr": "👥 Par Invitations", "es": "👥 Por Invitaciones", "vi": "👥 Theo Lời mời"},
    "lb_purchases":{"ar": "🛒 بالمشتريات", "en": "🛒 By Purchases", "fr": "🛒 Par Achats", "es": "🛒 Por Compras", "vi": "🛒 Theo Mua"},
    # Plan labels
    "1 Day":  {"ar": "يوم واحد", "en": "1 Day", "fr": "1 Jour", "es": "1 Día", "vi": "1 Ngày"},
    "7 Days": {"ar": "7 أيام", "en": "7 Days", "fr": "7 Jours", "es": "7 Días", "vi": "7 Ngày"},
    "30 Days":{"ar": "30 يوم", "en": "30 Days", "fr": "30 Jours", "es": "30 Días", "vi": "30 Ngày"},
}

def _t(lang, key, **kw):
    """جلب نص مترجم من _TEXTS"""
    txt = _TEXTS.get(key, {}).get(lang, _TEXTS.get(key, {}).get("en", key))
    if kw:
        try: txt = txt.format(**kw)
        except: pass
    return txt


# ───────────────────────── 🛍️ منتجات المتجر ─────────────────────────

def get_shop_products_inline(products, keys_st, lang):
    m = types.InlineKeyboardMarkup(row_width=1)
    for prod in products.keys():
        total = sum(len(keys_st.get(prod, {}).get(p, [])) for p in ["1 Day", "7 Days", "30 Days"])
        st = "✅" if total > 0 else "❌"
        m.add(types.InlineKeyboardButton(f"{st} 📦 {prod} ({total})", callback_data=f"shop_{prod}"))
    return m


# ───────────────────────── ⏱️ خطط المنتج ─────────────────────────

def get_product_plans_inline(prod, plans, keys_st, user_pts, rank_d, global_d, lang):
    m = types.InlineKeyboardMarkup(row_width=1)
    for plan, base in plans.items():
        final = int(base * (1 - global_d / 100) * (1 - rank_d))
        stock = len(keys_st.get(prod, {}).get(plan, []))
        label = _t(lang, plan)
        if stock > 0:
            st = "✅" if user_pts >= final else "💰"
            cb = f"buy_plan|{prod}|{plan}"
        else:
            st = "❌"
            cb = "shop_nostock"
        m.add(types.InlineKeyboardButton(f"{st} ⏱️ {label} → {final} 💎 ({stock})", callback_data=cb))
    m.add(types.InlineKeyboardButton(_t(lang, "back"), callback_data="shop_back"))
    return m


# ───────────────────────── ✅ تأكيد الشراء ─────────────────────────

def get_purchase_confirm_inline(prod, plan, price, lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(_t(lang, "confirm"), callback_data=f"buy_plan|{prod}|{plan}"),
        types.InlineKeyboardButton(_t(lang, "cancel"), callback_data="shop_back")
    )
    return m


# ───────────────────────── 🏆 المتصدرين ─────────────────────────

def get_leaderboard_inline(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(_t(lang, "lb_points"), callback_data="lb_points"),
        types.InlineKeyboardButton(_t(lang, "lb_invites"), callback_data="lb_invites")
    )
    m.add(types.InlineKeyboardButton(_t(lang, "lb_purchases"), callback_data="lb_purchases"))
    return m


# ───────────────────────── 👑 VIP للمستخدم ─────────────────────────

def get_vip_user_inline(is_vip, lang, price=100):
    m = types.InlineKeyboardMarkup(row_width=1)
    if is_vip:
        m.add(types.InlineKeyboardButton(_t(lang, "vip_stock"), callback_data="vip_stock"))
        m.add(types.InlineKeyboardButton(_t(lang, "vip_weekly"), callback_data="vip_weekly_code"))
        m.add(types.InlineKeyboardButton(_t(lang, "vip_convert"), callback_data="vip_convert_stars"))
        m.add(types.InlineKeyboardButton(_t(lang, "vip_renew"), callback_data="vip_buy"))
    else:
        m.add(types.InlineKeyboardButton(_t(lang, "vip_sub", p=price), callback_data="vip_buy"))
        m.add(types.InlineKeyboardButton(_t(lang, "vip_convert_btn"), callback_data="vip_convert_stars"))
    return m


# ───────────────────────── ⭐ Stars ─────────────────────────

def get_stars_inline(rate, lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    for stars in [1, 5, 10, 25, 50, 100]:
        m.add(types.InlineKeyboardButton(f"⭐ {stars} = {stars * rate} 💎", callback_data=f"star_buy_{stars}"))
    return m


# ───────────────────────── 🎮 Mini Games ─────────────────────────

def get_games_inline(lang):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(_t(lang, "rps"), callback_data="game_rps"))
    m.add(types.InlineKeyboardButton(_t(lang, "ttt"), callback_data="game_ttt"))
    m.add(types.InlineKeyboardButton(_t(lang, "hunt"), callback_data="game_hunt"))
    m.add(
        types.InlineKeyboardButton(_t(lang, "my_stats"), callback_data="game_stats"),
        types.InlineKeyboardButton(_t(lang, "leaderboard"), callback_data="game_leaderboard")
    )
    return m

def get_game_mode_inline(game_type, lang):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(_t(lang, "mode_ai"), callback_data=f"mode_ai_{game_type}"))
    m.add(types.InlineKeyboardButton(_t(lang, "mode_pvp"), callback_data=f"mode_pvp_{game_type}"))
    m.add(types.InlineKeyboardButton(_t(lang, "back"), callback_data="game_back"))
    return m

def get_bet_inline(lang):
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1 💎", callback_data="bet_1"),
        types.InlineKeyboardButton("2 💎", callback_data="bet_2"),
        types.InlineKeyboardButton("3 💎", callback_data="bet_3")
    )
    m.add(types.InlineKeyboardButton(_t(lang, "back"), callback_data="game_back"))
    return m

def get_rps_inline(game_id, lang):
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton(_t(lang, "rock"), callback_data=f"rps_r_{game_id}"),
        types.InlineKeyboardButton(_t(lang, "paper"), callback_data=f"rps_p_{game_id}"),
        types.InlineKeyboardButton(_t(lang, "scissors"), callback_data=f"rps_s_{game_id}")
    )
    return m


# ───────────────────────── 🎨 الثيم ─────────────────────────

def get_theme_inline(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🌿 Emerald", callback_data="theme_emerald"),
        types.InlineKeyboardButton("🌊 Ocean", callback_data="theme_ocean")
    )
    m.add(
        types.InlineKeyboardButton("🌅 Sunset", callback_data="theme_sunset"),
        types.InlineKeyboardButton("👑 Royal", callback_data="theme_royal")
    )
    m.add(types.InlineKeyboardButton("💫 Neon", callback_data="theme_neon"))
    m.add(types.InlineKeyboardButton(_t(lang, "back"), callback_data="settings_back"))
    return m


# ───────────────────────── 🔒 الخصوصية ─────────────────────────

def get_privacy_inline(lang, u):
    m = types.InlineKeyboardMarkup(row_width=1)
    hide = u.get("hide_leaderboard", False)
    lb_labels = {
        "ar": ("🏆 إظهاري في المتصدرين ✅", "🏆 إخفائي من المتصدرين ❌"),
        "en": ("🏆 Show on leaderboard ✅", "🏆 Hide from leaderboard ❌"),
        "fr": ("🏆 Me montrer ✅", "🏆 Me cacher ❌"),
        "es": ("🏆 Mostrar en ranking ✅", "🏆 Ocultar del ranking ❌"),
        "vi": ("🏆 Hiển thị BXH ✅", "🏆 Ẩn khỏi BXH ❌"),
    }
    show_txt, hide_txt = lb_labels.get(lang, lb_labels["en"])
    m.add(types.InlineKeyboardButton(show_txt if not hide else hide_txt, callback_data="privacy_toggle_lb"))
    m.add(types.InlineKeyboardButton(_t(lang, "back"), callback_data="settings_back"))
    return m


# ───────────────────────── 🔙 زر العودة ─────────────────────────

def get_back_button(lang, callback="main_back"):
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(_t(lang, "back"), callback_data=callback))
    return m


# ───────────────────────── ✅❌ تأكيد / إلغاء ─────────────────────────

def get_confirm_cancel_inline(confirm_cb, cancel_cb, lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(_t(lang, "confirm"), callback_data=confirm_cb),
        types.InlineKeyboardButton(_t(lang, "cancel"), callback_data=cancel_cb)
    )
    return m


# ───────────────────────── ⭐ تقييم الدعم ─────────────────────────

def get_rating_inline(tid, lang):
    m = types.InlineKeyboardMarkup(row_width=5)
    m.add(*[types.InlineKeyboardButton("⭐" * i, callback_data=f"rate_{tid}_{i}") for i in range(1, 6)])
    return m


# ───────────────────────── 🔔 إشعار التوفر ─────────────────────────

def get_notify_restock_inline(prod, lang):
    notify_texts = {
        "ar": "🔔 أبلغني عند التوفر",
        "en": "🔔 Notify when available",
        "fr": "🔔 Me notifier",
        "es": "🔔 Notificarme",
        "vi": "🔔 Thông báo khi có"
    }
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(notify_texts.get(lang, notify_texts["en"]), callback_data=f"notify_restock_{prod}"))
    return m


# ───────────────────────── 🎫 إجراءات التذكرة (أدمن) ─────────────────────────

def admin_ticket_actions(tid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💬 دردشة مباشرة", callback_data=f"admchat_{tid}"),
        types.InlineKeyboardButton("🔒 إغلاق", callback_data=f"admclosetick_{tid}")
    )
    return m


# ───────────────────────── 👤 إجراءات المستخدم (أدمن) ─────────────────────────

def admin_user_actions(uid, u):
    m = types.InlineKeyboardMarkup(row_width=2)
    if u.get("is_admin", False):
        m.add(types.InlineKeyboardButton("❌ إزالة الإدارة", callback_data=f"admbanuser_{uid}_demote"))
    m.add(
        types.InlineKeyboardButton("⛔ حظر دائم", callback_data=f"admbanuser_{uid}_perm"),
        types.InlineKeyboardButton("⏱️ 24 ساعة", callback_data=f"admbanuser_{uid}_temp")
    )
    return m


# ───────────────────────── 🛡️ نظام الحماية (أدمن) ─────────────────────────

def admin_shield_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🚫 المحظورين", callback_data="shield_bans"),
        types.InlineKeyboardButton("🔍 المشبوهين", callback_data="shield_suspicious")
    )
    m.add(
        types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="shield_settings"),
        types.InlineKeyboardButton("📜 السجلات", callback_data="shield_logs")
    )
    return m


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 نهاية الملف
# ═══════════════════════════════════════════════════════════════════════════

print("✅ keyboards.py v3.0 loaded!")
print("🎹 All keyboards ready (5 languages)")
