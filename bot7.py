"""
══════════════════════════════════════════════════════════════════════════════
║                  bot7.py - PREMIUM UI SYSTEM v3.0                           ║
║            🎨 واجهة مستخدم فاخرة مع إيموجيات Premium                         ║
║              Beautiful Keyboards + Premium Custom Emojis                    ║
══════════════════════════════════════════════════════════════════════════════
║  Developer: @fkLJh00302                                                     ║
║  Features:                                                                   ║
║   ✅ إيموجيات Telegram Premium المتحركة                                      ║
║   ✅ كيبورد ملون ومتناسق تلقائياً                                            ║
║   ✅ تصاميم مذهلة للقوائم والرسائل                                           ║
║   ✅ 5 لغات كاملة (ar/en/fr/es/vi)                                          ║
║   ✅ ثيمات متعددة قابلة للتخصيص                                              ║
══════════════════════════════════════════════════════════════════════════════
"""

from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_LINK, t
from database import get_user, bot_config, prices_config, keys_store

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 Premium Custom Emoji IDs
# ═══════════════════════════════════════════════════════════════════════════
# ملاحظة: لاستخدام custom emoji، يجب أن يكون مالك البوت لديه Telegram Premium
# هذه الإيموجيات تعمل فقط إذا كان البوت يملكه حساب Premium

PREMIUM_EMOJIS = {
    # ⭐ نجوم وتألق
    "star_animated": "5368324170671202286",      # نجمة متحركة
    "sparkles": "5424972841220607283",           # تألق
    "shine": "5447644880824181073",              # لمعان
    "glow": "5443038326535759644",               # توهج
    
    # 🔥 نار وطاقة
    "fire_animated": "5404870433939922908",      # نار متحركة
    "fire_blue": "5417915203100613993",          # نار زرقاء
    "energy": "5424728541650494040",             # طاقة
    "lightning": "5449683594425410115",          # برق
    
    # 💎 جواهر وفخامة
    "diamond": "5443038326535759644",            # ماسة
    "gem_purple": "5424903347626147015",         # جوهرة بنفسجية
    "crystal": "5424728541650494040",            # كريستال
    "crown": "5445284980978621387",              # تاج
    
    # ✅ نجاح وموافقة
    "check_green": "5447644880824181073",        # علامة خضراء
    "check_animated": "5424903347626147015",     # علامة متحركة
    "success": "5368324170671202286",            # نجاح
    "done": "5424972841220607283",               # تم
    
    # 🎁 هدايا ومكافآت
    "gift_animated": "5449683594425410115",      # هدية متحركة
    "gift_box": "5445284980978621387",           # صندوق هدية
    "reward": "5417915203100613993",             # مكافأة
    "bonus": "5404870433939922908",              # بونص
    
    # 🛒 تسوق ومال
    "cart": "5424728541650494040",               # عربة تسوق
    "money_bag": "5443038326535759644",          # كيس نقود
    "coin": "5424903347626147015",               # عملة
    "wallet": "5447644880824181073",             # محفظة
    
    # 🎮 ألعاب وترفيه
    "game": "5449683594425410115",               # لعبة
    "dice": "5445284980978621387",               # نرد
    "wheel": "5417915203100613993",              # عجلة
    "trophy": "5368324170671202286",             # كأس
    
    # 👤 مستخدم وحساب
    "user": "5424972841220607283",               # مستخدم
    "vip": "5443038326535759644",                # VIP
    "premium": "5445284980978621387",            # Premium
    "verified": "5424903347626147015",           # موثق
    
    # 🔔 إشعارات وتنبيهات
    "bell": "5447644880824181073",               # جرس
    "alert": "5449683594425410115",              # تنبيه
    "warning": "5417915203100613993",            # تحذير
    "info": "5424728541650494040",               # معلومات
    
    # 💬 دعم وتواصل
    "chat": "5368324170671202286",               # دردشة
    "support": "5424972841220607283",            # دعم
    "ticket": "5443038326535759644",             # تذكرة
    "message": "5445284980978621387",            # رسالة
    
    # ⚙️ إعدادات
    "settings": "5424903347626147015",           # إعدادات
    "config": "5447644880824181073",             # تكوين
    "tools": "5449683594425410115",              # أدوات
    "admin": "5417915203100613993",              # أدمن
    
    # 🏆 رتب
    "rank_silver": "5424728541650494040",        # فضي
    "rank_gold": "5443038326535759644",          # ذهبي
    "rank_diamond": "5445284980978621387",       # ماسي
    "rank_legend": "5368324170671202286",        # أسطورة
    
    # 🎯 أخرى
    "rocket": "5404870433939922908",             # صاروخ
    "heart": "5424903347626147015",              # قلب
    "lock": "5447644880824181073",               # قفل
    "key": "5449683594425410115",                # مفتاح
    "time": "5417915203100613993",               # وقت
    "calendar": "5424728541650494040",           # تقويم
}

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 ثيمات الألوان
# ═══════════════════════════════════════════════════════════════════════════

THEMES = {
    "emerald": {
        "name": "🌿 Emerald",
        "primary": "🟢",
        "secondary": "💚",
        "accent": "✨",
        "border_top": "╔═══════════════════════╗",
        "border_mid": "╠═══════════════════════╣",
        "border_bot": "╚═══════════════════════╝",
        "bullet": "◈",
        "arrow": "➤",
        "separator": "━━━━━━━━━━━━━━━━━━━━━"
    },
    "ocean": {
        "name": "🌊 Ocean",
        "primary": "🔵",
        "secondary": "💙",
        "accent": "🌟",
        "border_top": "┏━━━━━━━━━━━━━━━━━━━━━┓",
        "border_mid": "┣━━━━━━━━━━━━━━━━━━━━━┫",
        "border_bot": "┗━━━━━━━━━━━━━━━━━━━━━┛",
        "bullet": "●",
        "arrow": "▸",
        "separator": "─────────────────────"
    },
    "sunset": {
        "name": "🌅 Sunset",
        "primary": "🟠",
        "secondary": "🧡",
        "accent": "⭐",
        "border_top": "╭───────────────────────╮",
        "border_mid": "├───────────────────────┤",
        "border_bot": "╰───────────────────────╯",
        "bullet": "◆",
        "arrow": "→",
        "separator": "• • • • • • • • • • •"
    },
    "royal": {
        "name": "👑 Royal",
        "primary": "🟣",
        "secondary": "💜",
        "accent": "💎",
        "border_top": "╔══════════════════════╗",
        "border_mid": "║══════════════════════║",
        "border_bot": "╚══════════════════════╝",
        "bullet": "♦",
        "arrow": "»",
        "separator": "══════════════════════"
    },
    "neon": {
        "name": "💫 Neon",
        "primary": "🔴",
        "secondary": "❤️",
        "accent": "🔥",
        "border_top": "▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄",
        "border_mid": "▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀",
        "border_bot": "▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄",
        "bullet": "✦",
        "arrow": "⟫",
        "separator": "⋆ ⋆ ⋆ ⋆ ⋆ ⋆ ⋆ ⋆ ⋆ ⋆"
    }
}

def get_user_theme(uid: str) -> dict:
    """جلب ثيم المستخدم"""
    u = get_user(uid)
    theme_name = u.get("theme", "emerald") if u else "emerald"
    return THEMES.get(theme_name, THEMES["emerald"])

# ═══════════════════════════════════════════════════════════════════════════
# 📝 نصوص متعددة اللغات - Premium UI
# ═══════════════════════════════════════════════════════════════════════════

PREMIUM_UI_TEXT = {
    "ar": {
        # القائمة الرئيسية
        "main_menu_header": "🏠 مرحباً بك يا {name}!",
        "main_menu_subtitle": "✨ اختر من القائمة أدناه",
        "main_menu_balance": "💰 رصيدك: {points} 💎",
        "main_menu_rank": "🏆 رتبتك: {rank}",
        
        # أزرار القائمة الرئيسية
        "btn_account": "👤 حسابي",
        "btn_shop": "🛍️ المتجر",
        "btn_rewards": "🎁 المكافآت",
        "btn_entertainment": "🎮 الترفيه",
        "btn_support": "💬 الدعم",
        "btn_settings": "⚙️ الإعدادات",
        "btn_vip": "👑 VIP",
        "btn_stars": "⭐ Stars",
        "btn_games": "🎯 الألعاب",
        "btn_admin": "🔐 الإدارة",
        
        # الحساب
        "account_header": "👤 ━━ حسابك الشخصي ━━",
        "account_id": "🆔 المعرف",
        "account_username": "📝 اليوزر",
        "account_balance": "💰 الرصيد",
        "account_rank": "🏆 الرتبة",
        "account_discount": "🎯 الخصم",
        "account_invites": "👥 الدعوات",
        "account_purchases": "🛒 المشتريات",
        "account_streak": "🔥 السلسلة",
        "account_joined": "📅 الانضمام",
        
        # المتجر
        "shop_header": "🛍️ ━━ المتجر الرسمي ━━",
        "shop_subtitle": "🔥 أفضل المنتجات بأفضل الأسعار",
        "shop_your_balance": "💳 رصيدك",
        "shop_your_discount": "🎯 خصمك",
        "shop_empty": "📭 لا توجد منتجات حالياً",
        "shop_select_product": "👇 اختر المنتج",
        "shop_select_plan": "⏱️ اختر المدة",
        "shop_confirm": "✅ تأكيد الشراء",
        "shop_success": "🎉 تم الشراء بنجاح!",
        "shop_key": "🔐 مفتاحك",
        
        # المكافآت
        "rewards_header": "🎁 ━━ مركز المكافآت ━━",
        "rewards_subtitle": "✨ احصل على مكافآتك المجانية",
        "btn_daily": "✨ المكافأة اليومية",
        "btn_redeem": "🎫 استرداد كود",
        "btn_quests": "🔥 المهام",
        "btn_referral": "🔗 الإحالة",
        
        # الترفيه
        "entertainment_header": "🎮 ━━ مركز الترفيه ━━",
        "entertainment_subtitle": "🎲 العب واربح النقاط",
        "btn_lootbox": "🎰 صندوق الحظ",
        "btn_wheel": "🎡 عجلة الحظ",
        "btn_minigames": "🎯 ألعاب صغيرة",
        "btn_leaderboard": "🏆 المتصدرون",
        
        # الدعم
        "support_header": "💬 ━━ مركز الدعم ━━",
        "support_subtitle": "🤝 فريقنا جاهز لمساعدتك",
        "btn_new_ticket": "🎫 تذكرة جديدة",
        "btn_my_tickets": "📋 تذاكري",
        "btn_faq": "❓ الأسئلة الشائعة",
        
        # الإعدادات
        "settings_header": "⚙️ ━━ الإعدادات ━━",
        "settings_subtitle": "🎨 خصص تجربتك",
        "btn_language": "🌐 اللغة",
        "btn_notifications": "🔔 الإشعارات",
        "btn_theme": "🎨 الثيم",
        "btn_privacy": "🔒 الخصوصية",
        "btn_about": "ℹ️ حول البوت",
        
        # VIP
        "vip_header": "👑 ━━ عضوية VIP ━━",
        "vip_benefits": "✨ مزايا حصرية",
        "vip_active": "🌟 أنت عضو VIP!",
        "vip_days_left": "⏰ متبقي: {days} يوم",
        
        # رسائل عامة
        "back": "🔙 رجوع",
        "cancel": "❌ إلغاء",
        "confirm": "✅ تأكيد",
        "loading": "⏳ جاري التحميل...",
        "error": "❌ حدث خطأ",
        "success": "✅ تمت العملية بنجاح",
    },
    "en": {
        "main_menu_header": "🏠 Welcome {name}!",
        "main_menu_subtitle": "✨ Choose from the menu below",
        "main_menu_balance": "💰 Balance: {points} 💎",
        "main_menu_rank": "🏆 Rank: {rank}",
        
        "btn_account": "👤 Account",
        "btn_shop": "🛍️ Shop",
        "btn_rewards": "🎁 Rewards",
        "btn_entertainment": "🎮 Entertainment",
        "btn_support": "💬 Support",
        "btn_settings": "⚙️ Settings",
        "btn_vip": "👑 VIP",
        "btn_stars": "⭐ Stars",
        "btn_games": "🎯 Games",
        "btn_admin": "🔐 Admin",
        
        "account_header": "👤 ━━ Your Account ━━",
        "account_id": "🆔 ID",
        "account_username": "📝 Username",
        "account_balance": "💰 Balance",
        "account_rank": "🏆 Rank",
        "account_discount": "🎯 Discount",
        "account_invites": "👥 Invites",
        "account_purchases": "🛒 Purchases",
        "account_streak": "🔥 Streak",
        "account_joined": "📅 Joined",
        
        "shop_header": "🛍️ ━━ Official Store ━━",
        "shop_subtitle": "🔥 Best products at best prices",
        "shop_your_balance": "💳 Your balance",
        "shop_your_discount": "🎯 Your discount",
        "shop_empty": "📭 No products available",
        "shop_select_product": "👇 Select product",
        "shop_select_plan": "⏱️ Select duration",
        "shop_confirm": "✅ Confirm purchase",
        "shop_success": "🎉 Purchase successful!",
        "shop_key": "🔐 Your key",
        
        "rewards_header": "🎁 ━━ Rewards Center ━━",
        "rewards_subtitle": "✨ Get your free rewards",
        "btn_daily": "✨ Daily Bonus",
        "btn_redeem": "🎫 Redeem Code",
        "btn_quests": "🔥 Quests",
        "btn_referral": "🔗 Referral",
        
        "entertainment_header": "🎮 ━━ Entertainment ━━",
        "entertainment_subtitle": "🎲 Play and win points",
        "btn_lootbox": "🎰 Loot Box",
        "btn_wheel": "🎡 Lucky Wheel",
        "btn_minigames": "🎯 Mini Games",
        "btn_leaderboard": "🏆 Leaderboard",
        
        "support_header": "💬 ━━ Support Center ━━",
        "support_subtitle": "🤝 Our team is ready to help",
        "btn_new_ticket": "🎫 New Ticket",
        "btn_my_tickets": "📋 My Tickets",
        "btn_faq": "❓ FAQ",
        
        "settings_header": "⚙️ ━━ Settings ━━",
        "settings_subtitle": "🎨 Customize your experience",
        "btn_language": "🌐 Language",
        "btn_notifications": "🔔 Notifications",
        "btn_theme": "🎨 Theme",
        "btn_privacy": "🔒 Privacy",
        "btn_about": "ℹ️ About",
        
        "vip_header": "👑 ━━ VIP Membership ━━",
        "vip_benefits": "✨ Exclusive benefits",
        "vip_active": "🌟 You are VIP!",
        "vip_days_left": "⏰ Days left: {days}",
        
        "back": "🔙 Back",
        "cancel": "❌ Cancel",
        "confirm": "✅ Confirm",
        "loading": "⏳ Loading...",
        "error": "❌ Error occurred",
        "success": "✅ Operation successful",
    },
    "fr": {
        "main_menu_header": "🏠 Bienvenue {name}!",
        "main_menu_subtitle": "✨ Choisissez dans le menu",
        "main_menu_balance": "💰 Solde: {points} 💎",
        "main_menu_rank": "🏆 Rang: {rank}",
        
        "btn_account": "👤 Compte",
        "btn_shop": "🛍️ Boutique",
        "btn_rewards": "🎁 Récompenses",
        "btn_entertainment": "🎮 Divertissement",
        "btn_support": "💬 Support",
        "btn_settings": "⚙️ Paramètres",
        "btn_vip": "👑 VIP",
        "btn_stars": "⭐ Stars",
        "btn_games": "🎯 Jeux",
        "btn_admin": "🔐 Admin",
        
        "account_header": "👤 ━━ Votre Compte ━━",
        "account_id": "🆔 ID",
        "account_username": "📝 Nom",
        "account_balance": "💰 Solde",
        "account_rank": "🏆 Rang",
        "account_discount": "🎯 Remise",
        "account_invites": "👥 Invitations",
        "account_purchases": "🛒 Achats",
        "account_streak": "🔥 Série",
        "account_joined": "📅 Inscription",
        
        "shop_header": "🛍️ ━━ Boutique Officielle ━━",
        "shop_subtitle": "🔥 Meilleurs produits",
        "shop_your_balance": "💳 Votre solde",
        "shop_your_discount": "🎯 Votre remise",
        "shop_empty": "📭 Aucun produit",
        "shop_select_product": "👇 Sélectionnez",
        "shop_select_plan": "⏱️ Durée",
        "shop_confirm": "✅ Confirmer",
        "shop_success": "🎉 Achat réussi!",
        "shop_key": "🔐 Votre clé",
        
        "rewards_header": "🎁 ━━ Récompenses ━━",
        "rewards_subtitle": "✨ Réclamez vos récompenses",
        "btn_daily": "✨ Bonus Quotidien",
        "btn_redeem": "🎫 Code",
        "btn_quests": "🔥 Quêtes",
        "btn_referral": "🔗 Parrainage",
        
        "entertainment_header": "🎮 ━━ Divertissement ━━",
        "entertainment_subtitle": "🎲 Jouez et gagnez",
        "btn_lootbox": "🎰 Coffre",
        "btn_wheel": "🎡 Roue",
        "btn_minigames": "🎯 Mini Jeux",
        "btn_leaderboard": "🏆 Classement",
        
        "support_header": "💬 ━━ Support ━━",
        "support_subtitle": "🤝 Nous sommes là pour vous",
        "btn_new_ticket": "🎫 Nouveau Ticket",
        "btn_my_tickets": "📋 Mes Tickets",
        "btn_faq": "❓ FAQ",
        
        "settings_header": "⚙️ ━━ Paramètres ━━",
        "settings_subtitle": "🎨 Personnalisez",
        "btn_language": "🌐 Langue",
        "btn_notifications": "🔔 Notifications",
        "btn_theme": "🎨 Thème",
        "btn_privacy": "🔒 Vie privée",
        "btn_about": "ℹ️ À propos",
        
        "vip_header": "👑 ━━ Membre VIP ━━",
        "vip_benefits": "✨ Avantages exclusifs",
        "vip_active": "🌟 Vous êtes VIP!",
        "vip_days_left": "⏰ Jours restants: {days}",
        
        "back": "🔙 Retour",
        "cancel": "❌ Annuler",
        "confirm": "✅ Confirmer",
        "loading": "⏳ Chargement...",
        "error": "❌ Erreur",
        "success": "✅ Succès",
    },
    "es": {
        "main_menu_header": "🏠 ¡Bienvenido {name}!",
        "main_menu_subtitle": "✨ Elige del menú abajo",
        "main_menu_balance": "💰 Saldo: {points} 💎",
        "main_menu_rank": "🏆 Rango: {rank}",
        
        "btn_account": "👤 Cuenta",
        "btn_shop": "🛍️ Tienda",
        "btn_rewards": "🎁 Recompensas",
        "btn_entertainment": "🎮 Entretenimiento",
        "btn_support": "💬 Soporte",
        "btn_settings": "⚙️ Ajustes",
        "btn_vip": "👑 VIP",
        "btn_stars": "⭐ Stars",
        "btn_games": "🎯 Juegos",
        "btn_admin": "🔐 Admin",
        
        "account_header": "👤 ━━ Tu Cuenta ━━",
        "account_id": "🆔 ID",
        "account_username": "📝 Usuario",
        "account_balance": "💰 Saldo",
        "account_rank": "🏆 Rango",
        "account_discount": "🎯 Descuento",
        "account_invites": "👥 Invitaciones",
        "account_purchases": "🛒 Compras",
        "account_streak": "🔥 Racha",
        "account_joined": "📅 Registro",
        
        "shop_header": "🛍️ ━━ Tienda Oficial ━━",
        "shop_subtitle": "🔥 Los mejores productos",
        "shop_your_balance": "💳 Tu saldo",
        "shop_your_discount": "🎯 Tu descuento",
        "shop_empty": "📭 Sin productos",
        "shop_select_product": "👇 Selecciona",
        "shop_select_plan": "⏱️ Duración",
        "shop_confirm": "✅ Confirmar",
        "shop_success": "🎉 ¡Compra exitosa!",
        "shop_key": "🔐 Tu clave",
        
        "rewards_header": "🎁 ━━ Recompensas ━━",
        "rewards_subtitle": "✨ Obtén tus recompensas gratis",
        "btn_daily": "✨ Bono Diario",
        "btn_redeem": "🎫 Canjear Código",
        "btn_quests": "🔥 Misiones",
        "btn_referral": "🔗 Referidos",
        
        "entertainment_header": "🎮 ━━ Entretenimiento ━━",
        "entertainment_subtitle": "🎲 Juega y gana puntos",
        "btn_lootbox": "🎰 Caja de Botín",
        "btn_wheel": "🎡 Ruleta",
        "btn_minigames": "🎯 Mini Juegos",
        "btn_leaderboard": "🏆 Ranking",
        
        "support_header": "💬 ━━ Soporte ━━",
        "support_subtitle": "🤝 Estamos para ayudarte",
        "btn_new_ticket": "🎫 Nuevo Ticket",
        "btn_my_tickets": "📋 Mis Tickets",
        "btn_faq": "❓ Preguntas",
        
        "settings_header": "⚙️ ━━ Ajustes ━━",
        "settings_subtitle": "🎨 Personaliza tu experiencia",
        "btn_language": "🌐 Idioma",
        "btn_notifications": "🔔 Notificaciones",
        "btn_theme": "🎨 Tema",
        "btn_privacy": "🔒 Privacidad",
        "btn_about": "ℹ️ Acerca de",
        
        "vip_header": "👑 ━━ Membresía VIP ━━",
        "vip_benefits": "✨ Beneficios exclusivos",
        "vip_active": "🌟 ¡Eres VIP!",
        "vip_days_left": "⏰ Días restantes: {days}",
        
        "back": "🔙 Atrás",
        "cancel": "❌ Cancelar",
        "confirm": "✅ Confirmar",
        "loading": "⏳ Cargando...",
        "error": "❌ Error",
        "success": "✅ ¡Éxito!",
    },
    "vi": {
        "main_menu_header": "🏠 Xin chào {name}!",
        "main_menu_subtitle": "✨ Chọn từ menu bên dưới",
        "main_menu_balance": "💰 Số dư: {points} 💎",
        "main_menu_rank": "🏆 Cấp: {rank}",
        
        "btn_account": "👤 Tài khoản",
        "btn_shop": "🛍️ Cửa hàng",
        "btn_rewards": "🎁 Phần thưởng",
        "btn_entertainment": "🎮 Giải trí",
        "btn_support": "💬 Hỗ trợ",
        "btn_settings": "⚙️ Cài đặt",
        "btn_vip": "👑 VIP",
        "btn_stars": "⭐ Stars",
        "btn_games": "🎯 Trò chơi",
        "btn_admin": "🔐 Quản trị",
        
        "account_header": "👤 ━━ Tài khoản ━━",
        "account_id": "🆔 ID",
        "account_username": "📝 Tên",
        "account_balance": "💰 Số dư",
        "account_rank": "🏆 Cấp",
        "account_discount": "🎯 Giảm giá",
        "account_invites": "👥 Lời mời",
        "account_purchases": "🛒 Mua hàng",
        "account_streak": "🔥 Chuỗi",
        "account_joined": "📅 Tham gia",
        
        "shop_header": "🛍️ ━━ Cửa hàng ━━",
        "shop_subtitle": "🔥 Sản phẩm tốt nhất",
        "shop_your_balance": "💳 Số dư của bạn",
        "shop_your_discount": "🎯 Giảm giá của bạn",
        "shop_empty": "📭 Không có sản phẩm",
        "shop_select_product": "👇 Chọn sản phẩm",
        "shop_select_plan": "⏱️ Chọn thời hạn",
        "shop_confirm": "✅ Xác nhận",
        "shop_success": "🎉 Mua thành công!",
        "shop_key": "🔐 Key của bạn",
        
        "rewards_header": "🎁 ━━ Phần thưởng ━━",
        "rewards_subtitle": "✨ Nhận phần thưởng miễn phí",
        "btn_daily": "✨ Thưởng hàng ngày",
        "btn_redeem": "🎫 Đổi mã",
        "btn_quests": "🔥 Nhiệm vụ",
        "btn_referral": "🔗 Giới thiệu",
        
        "entertainment_header": "🎮 ━━ Giải trí ━━",
        "entertainment_subtitle": "🎲 Chơi và thắng điểm",
        "btn_lootbox": "🎰 Hộp may mắn",
        "btn_wheel": "🎡 Vòng quay",
        "btn_minigames": "🎯 Mini Games",
        "btn_leaderboard": "🏆 BXH",
        
        "support_header": "💬 ━━ Hỗ trợ ━━",
        "support_subtitle": "🤝 Đội ngũ sẵn sàng giúp đỡ",
        "btn_new_ticket": "🎫 Ticket mới",
        "btn_my_tickets": "📋 Ticket của tôi",
        "btn_faq": "❓ Câu hỏi",
        
        "settings_header": "⚙️ ━━ Cài đặt ━━",
        "settings_subtitle": "🎨 Tùy chỉnh trải nghiệm",
        "btn_language": "🌐 Ngôn ngữ",
        "btn_notifications": "🔔 Thông báo",
        "btn_theme": "🎨 Giao diện",
        "btn_privacy": "🔒 Riêng tư",
        "btn_about": "ℹ️ Giới thiệu",
        
        "vip_header": "👑 ━━ Thành viên VIP ━━",
        "vip_benefits": "✨ Quyền lợi đặc biệt",
        "vip_active": "🌟 Bạn là VIP!",
        "vip_days_left": "⏰ Còn lại: {days} ngày",
        
        "back": "🔙 Quay lại",
        "cancel": "❌ Hủy",
        "confirm": "✅ Xác nhận",
        "loading": "⏳ Đang tải...",
        "error": "❌ Lỗi",
        "success": "✅ Thành công!",
    }
}

def pt(lang: str, key: str, **kwargs) -> str:
    """Premium Text - جلب النص المترجم"""
    if lang not in PREMIUM_UI_TEXT:
        lang = "en"
    text = PREMIUM_UI_TEXT[lang].get(key, PREMIUM_UI_TEXT["en"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

# ═══════════════════════════════════════════════════════════════════════════
# 🎹 كيبوردات Premium
# ═══════════════════════════════════════════════════════════════════════════

def create_premium_main_keyboard(uid: str, lang: str) -> types.ReplyKeyboardMarkup:
    """إنشاء كيبورد رئيسي فاخر"""
    u = get_user(uid) or {}
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # الصف الأول - الأهم
    m.add(
        types.KeyboardButton(pt(lang, "btn_account")),
        types.KeyboardButton(pt(lang, "btn_shop"))
    )
    
    # الصف الثاني - المكافآت والترفيه
    m.add(
        types.KeyboardButton(pt(lang, "btn_rewards")),
        types.KeyboardButton(pt(lang, "btn_entertainment"))
    )
    
    # الصف الثالث - VIP و Stars
    m.add(
        types.KeyboardButton(pt(lang, "btn_vip")),
        types.KeyboardButton(pt(lang, "btn_stars"))
    )
    
    # الصف الرابع - الألعاب والدعم
    m.add(
        types.KeyboardButton(pt(lang, "btn_games")),
        types.KeyboardButton(pt(lang, "btn_support"))
    )
    
    # الصف الخامس - الإعدادات
    m.add(types.KeyboardButton(pt(lang, "btn_settings")))
    
    # زر الأدمن (إذا كان مشرف)
    if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY] or u.get("is_admin"):
        m.add(types.KeyboardButton(pt(lang, "btn_admin")))
    
    return m

def create_premium_account_inline(lang: str) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد الحساب"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    m.add(
        types.InlineKeyboardButton("💰 الرصيد", callback_data="pui_balance"),
        types.InlineKeyboardButton("🏆 الرتبة", callback_data="pui_rank")
    )
    m.add(
        types.InlineKeyboardButton("🔗 الإحالة", callback_data="pui_referral"),
        types.InlineKeyboardButton("📜 المشتريات", callback_data="pui_purchases")
    )
    m.add(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="pui_stats")
    )
    
    return m

def create_premium_shop_inline(lang: str) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد المتجر"""
    m = types.InlineKeyboardMarkup(row_width=1)
    
    for product in prices_config.keys():
        stock = sum(len(keys_store.get(product, {}).get(p, [])) 
                   for p in ["1 Day", "7 Days", "30 Days"])
        status = "✅" if stock > 0 else "❌"
        m.add(types.InlineKeyboardButton(
            f"{status} 📦 {product} ({stock})",
            callback_data=f"pshop_{product}"
        ))
    
    return m

def create_premium_product_plans_inline(product: str, lang: str, user_points: int, discount: float) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد خطط المنتج"""
    m = types.InlineKeyboardMarkup(row_width=1)
    plans = prices_config.get(product, {})
    
    for plan, price in plans.items():
        stock = len(keys_store.get(product, {}).get(plan, []))
        final_price = int(price * (1 - discount))
        
        if stock > 0:
            status = "✅"
            if user_points >= final_price:
                action = "buy"
            else:
                status = "💰"
                action = "nobuy"
        else:
            status = "❌"
            action = "nostock"
        
        btn_text = f"{status} ⏱️ {plan} → {final_price} 💎"
        if action == "buy":
            m.add(types.InlineKeyboardButton(btn_text, callback_data=f"pbuy_{product}|{plan}"))
        else:
            m.add(types.InlineKeyboardButton(btn_text, callback_data="pui_none"))
    
    m.add(types.InlineKeyboardButton(pt(lang, "back"), callback_data="pui_shop_back"))
    
    return m

def create_premium_rewards_inline(lang: str) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد المكافآت"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_daily"), callback_data="pui_daily"),
        types.InlineKeyboardButton(pt(lang, "btn_redeem"), callback_data="pui_redeem")
    )
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_quests"), callback_data="pui_quests"),
        types.InlineKeyboardButton(pt(lang, "btn_referral"), callback_data="pui_referral")
    )
    
    return m

def create_premium_entertainment_inline(lang: str) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد الترفيه"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_lootbox"), callback_data="pui_lootbox"),
        types.InlineKeyboardButton(pt(lang, "btn_wheel"), callback_data="pui_wheel")
    )
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_minigames"), callback_data="pui_minigames"),
        types.InlineKeyboardButton(pt(lang, "btn_leaderboard"), callback_data="pui_leaderboard")
    )
    
    return m

def create_premium_support_inline(lang: str) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد الدعم"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_new_ticket"), callback_data="pui_new_ticket"),
        types.InlineKeyboardButton(pt(lang, "btn_my_tickets"), callback_data="pui_my_tickets")
    )
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_faq"), callback_data="pui_faq")
    )
    
    return m

def create_premium_settings_inline(lang: str, u: dict) -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد الإعدادات"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    notif_status = "🔔 ON" if u.get("notifications_on", True) else "🔕 OFF"
    
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_language"), callback_data="pui_language"),
        types.InlineKeyboardButton(notif_status, callback_data="pui_notifications")
    )
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_theme"), callback_data="pui_theme"),
        types.InlineKeyboardButton(pt(lang, "btn_privacy"), callback_data="pui_privacy")
    )
    m.add(
        types.InlineKeyboardButton(pt(lang, "btn_about"), callback_data="pui_about")
    )
    m.add(
        types.InlineKeyboardButton("💻 Developer: @fkLJh00302", url="https://t.me/fkLJh00302")
    )
    
    return m

def create_theme_selector_inline() -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد اختيار الثيم"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    for theme_id, theme in THEMES.items():
        m.add(types.InlineKeyboardButton(
            theme["name"],
            callback_data=f"ptheme_{theme_id}"
        ))
    
    return m

def create_language_selector_inline() -> types.InlineKeyboardMarkup:
    """إنشاء كيبورد اختيار اللغة"""
    m = types.InlineKeyboardMarkup(row_width=2)
    
    m.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="plang_ar"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="plang_en")
    )
    m.add(
        types.InlineKeyboardButton("🇫🇷 Français", callback_data="plang_fr"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="plang_es")
    )
    m.add(
        types.InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="plang_vi")
    )
    
    return m

# ═══════════════════════════════════════════════════════════════════════════
# 📝 دوال بناء الرسائل الفاخرة
# ═══════════════════════════════════════════════════════════════════════════

def build_premium_main_menu(uid: str, lang: str) -> str:
    """بناء رسالة القائمة الرئيسية"""
    u = get_user(uid) or {}
    theme = get_user_theme(uid)
    name = u.get("username") or "User"
    points = u.get("points", 0) or 0
    rank = u.get("rank", "Member")
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'main_menu_header', name=name)}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"{theme['bullet']} {pt(lang, 'main_menu_balance', points=points)}\n"
        f"{theme['bullet']} {pt(lang, 'main_menu_rank', rank=rank)}\n\n"
        f"{theme['separator']}\n\n"
        f"✨ {pt(lang, 'main_menu_subtitle')}"
    )
    
    return msg

def build_premium_account(uid: str, lang: str) -> str:
    """بناء رسالة الحساب"""
    u = get_user(uid) or {}
    theme = get_user_theme(uid)
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'account_header')}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"┃ {pt(lang, 'account_id')}: <code>{uid}</code>\n"
        f"┃ {pt(lang, 'account_username')}: @{u.get('username', 'N/A')}\n"
        f"┃ {pt(lang, 'account_balance')}: {u.get('points', 0)} 💎\n"
        f"┃ {pt(lang, 'account_rank')}: {u.get('rank', 'Member')}\n"
        f"┃ {pt(lang, 'account_discount')}: {int((u.get('rank_discount', 0) or 0) * 100)}%\n"
        f"┃ {pt(lang, 'account_invites')}: {u.get('invite_count', 0)}\n"
        f"┃ {pt(lang, 'account_purchases')}: {u.get('purchases_count', 0)}\n"
        f"┃ {pt(lang, 'account_streak')}: {u.get('streak_days', 0)} 🔥\n"
        f"╰━━━━━━━━━━━━━━━━━━━╯"
    )
    
    return msg

def build_premium_shop(uid: str, lang: str) -> str:
    """بناء رسالة المتجر"""
    u = get_user(uid) or {}
    theme = get_user_theme(uid)
    points = u.get("points", 0) or 0
    discount = u.get("rank_discount", 0) or 0
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'shop_header')}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"🔥 {pt(lang, 'shop_subtitle')}\n\n"
        f"{theme['separator']}\n\n"
        f"💳 {pt(lang, 'shop_your_balance')}: {points} 💎\n"
        f"🎯 {pt(lang, 'shop_your_discount')}: {int(discount * 100)}%\n\n"
        f"{theme['separator']}\n\n"
        f"👇 {pt(lang, 'shop_select_product')}:"
    )
    
    return msg

def build_purchase_success(product: str, plan: str, price: int, key: str, lang: str) -> str:
    """بناء رسالة نجاح الشراء"""
    msg = (
        f"╔═══════════════════════╗\n"
        f"║ 🎉 {pt(lang, 'shop_success')} 🎉 ║\n"
        f"╚═══════════════════════╝\n\n"
        f"┃ 📦 Product: {product}\n"
        f"┃ ⏱️ Duration: {plan}\n"
        f"┃ 💰 Price: {price} 💎\n"
        f"╰━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🔐 {pt(lang, 'shop_key')}:\n"
        f"<code>{key}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Delivered successfully!\n"
        f"⚠️ Save your key safely!"
    )
    
    return msg

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 معالجات الأحداث
# ═══════════════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data.startswith("pui_"))
def handle_premium_ui_callbacks(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "pui_none":
        bot.answer_callback_query(call.id, "❌", show_alert=False)
        return
    
    if data == "pui_balance":
        points = u.get("points", 0) or 0
        acc = u.get("accumulated_points", 0) or 0
        bot.answer_callback_query(call.id, f"💰 Balance: {points} 💎\n📊 Total earned: {acc}", show_alert=True)
        return
    
    if data == "pui_rank":
        rank = u.get("rank", "Member")
        discount = int((u.get("rank_discount", 0) or 0) * 100)
        bot.answer_callback_query(call.id, f"🏆 Rank: {rank}\n🎯 Discount: {discount}%", show_alert=True)
        return
    
    if data == "pui_shop_back":
        msg = build_premium_shop(uid, lang)
        m = create_premium_shop_inline(lang)
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except:
            pass
        return
    
    if data == "pui_language":
        try:
            bot.edit_message_text(
                "🌐 ━━ Select Language ━━\n\nChoose your preferred language:",
                chat_id, msg_id,
                reply_markup=create_language_selector_inline(),
                parse_mode="HTML"
            )
        except:
            pass
        return
    
    if data == "pui_theme":
        try:
            bot.edit_message_text(
                "🎨 ━━ Select Theme ━━\n\nChoose your visual style:",
                chat_id, msg_id,
                reply_markup=create_theme_selector_inline(),
                parse_mode="HTML"
            )
        except:
            pass
        return
    
    if data == "pui_notifications":
        from database import update_user_data
        current = u.get("notifications_on", True)
        update_user_data(uid, notifications_on=not current)
        status = "🔕 OFF" if current else "🔔 ON"
        bot.answer_callback_query(call.id, f"Notifications: {status}", show_alert=True)
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("plang_"))
def handle_language_change(call):
    uid = str(call.from_user.id)
    new_lang = call.data.replace("plang_", "")
    
    from database import update_user_data
    update_user_data(uid, lang=new_lang, lang_selected=True)
    
    bot.answer_callback_query(call.id, "✅ Language changed!", show_alert=True)
    
    # إعادة عرض القائمة
    msg = build_premium_main_menu(uid, new_lang)
    bot.send_message(
        call.message.chat.id,
        msg,
        reply_markup=create_premium_main_keyboard(uid, new_lang),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("ptheme_"))
def handle_theme_change(call):
    uid = str(call.from_user.id)
    new_theme = call.data.replace("ptheme_", "")
    
    from database import update_user_data
    update_user_data(uid, theme=new_theme)
    
    theme = THEMES.get(new_theme, THEMES["emerald"])
    bot.answer_callback_query(call.id, f"✅ Theme: {theme['name']}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pshop_"))
def handle_shop_product(call):
    uid = str(call.from_user.id)
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    product = call.data.replace("pshop_", "")
    
    if product not in prices_config:
        bot.answer_callback_query(call.id, "❌ Product not found", show_alert=True)
        return
    
    user_points = u.get("points", 0) or 0
    discount = u.get("rank_discount", 0) or 0
    
    msg = (
        f"📦 ━━ {product} ━━\n\n"
        f"💳 Your balance: {user_points} 💎\n"
        f"🎯 Your discount: {int(discount * 100)}%\n\n"
        f"{pt(lang, 'shop_select_plan')}:"
    )
    
    m = create_premium_product_plans_inline(product, lang, user_points, discount)
    
    try:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, 
                             reply_markup=m, parse_mode="HTML")
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════
# 🔌 دوال التكامل مع البوت الرئيسي
# ═══════════════════════════════════════════════════════════════════════════

def show_premium_main_menu(chat_id: int, uid: str):
    """عرض القائمة الرئيسية الفاخرة"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    msg = build_premium_main_menu(uid, lang)
    m = create_premium_main_keyboard(uid, lang)
    
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_premium_account(chat_id: int, uid: str):
    """عرض صفحة الحساب الفاخرة"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    msg = build_premium_account(uid, lang)
    m = create_premium_account_inline(lang)
    
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_premium_shop(chat_id: int, uid: str):
    """عرض المتجر الفاخر"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    
    if not prices_config:
        bot.send_message(chat_id, pt(lang, "shop_empty"), parse_mode="HTML")
        return
    
    msg = build_premium_shop(uid, lang)
    m = create_premium_shop_inline(lang)
    
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_premium_rewards(chat_id: int, uid: str):
    """عرض صفحة المكافآت"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    theme = get_user_theme(uid)
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'rewards_header')}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"✨ {pt(lang, 'rewards_subtitle')}"
    )
    
    m = create_premium_rewards_inline(lang)
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_premium_entertainment(chat_id: int, uid: str):
    """عرض صفحة الترفيه"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    theme = get_user_theme(uid)
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'entertainment_header')}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"🎲 {pt(lang, 'entertainment_subtitle')}"
    )
    
    m = create_premium_entertainment_inline(lang)
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_premium_support(chat_id: int, uid: str):
    """عرض صفحة الدعم"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    theme = get_user_theme(uid)
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'support_header')}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"🤝 {pt(lang, 'support_subtitle')}"
    )
    
    m = create_premium_support_inline(lang)
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

def show_premium_settings(chat_id: int, uid: str):
    """عرض صفحة الإعدادات"""
    u = get_user(uid) or {}
    lang = u.get("lang", "ar")
    theme = get_user_theme(uid)
    
    msg = (
        f"{theme['border_top']}\n"
        f"║  {pt(lang, 'settings_header')}  ║\n"
        f"{theme['border_bot']}\n\n"
        f"🎨 {pt(lang, 'settings_subtitle')}"
    )
    
    m = create_premium_settings_inline(lang, u)
    bot.send_message(chat_id, msg, reply_markup=m, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 التهيئة
# ═══════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("✅ bot7.py loaded!")
print("🎨 Premium UI System: ACTIVE")
print("🌈 Themes Available: 5")
print("🌍 Languages: ar, en, fr, es, vi")
print("✨ Premium Emojis: READY")
print("🎹 Custom Keyboards: ENABLED")
print("=" * 60)
