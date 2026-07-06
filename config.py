import os
import telebot

# 1️⃣ الإعدادات الأساسية والتوكن
API_TOKEN = os.getenv("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

ADMIN_PRIMARY = 5145154527
ADMIN_SECONDARY = 8878290572

CHANNEL_ID = -1003763276411  
CHANNEL_LINK = "https://t.me/evee7x"

DB_USERS = "users_data.json"
DB_KEYS = "keys_store.json"
DB_REDEEM = "redeem_codes.json"
DB_PRICES = "prices_config.json"
DB_CONFIG = "bot_config.json"

# ✨ إعداد الرتب الثابتة
RANKS = {
    "silver":  {"name": "🥈 رتبة الفضي",     "points_needed": 200,   "discount": 0.01},
    "gold":    {"name": "🥇 رتبة الذهبي",     "points_needed": 600,   "discount": 0.02},
    "diamond": {"name": "💎 رتبة الماسي",     "points_needed": 1500,  "discount": 0.03},
    "hero":    {"name": "⚡ رتبة الهيرو",     "points_needed": 3500,  "discount": 0.04},
    "master":  {"name": "👑 رتبة الماستر",    "points_needed": 7000,  "discount": 0.045},
    "legend":  {"name": "🏆 رتبة الأسطورة",   "points_needed": 12000, "discount": 0.05}
}

LOCALES = {
    "ar": {
        "welcome": "🌐 الرجاء اختيار لغة البوت لتفعيل حسابك / Please select language:",
        "must_join": f"⚠️ يجب عليك الاشتراك في قناتنا أولاً لاستخدام البوت!\nاشترك هنا: {CHANNEL_LINK}",
        "check_btn": "🔄 تحقق من الاشتراك",
        "main_menu": "🏠 القائمة الرئيسية للمتجر:",
        "id_btn": "🆔 إظهار الآيدي",
        "balance_btn": "💰 رصيدي",
        "shop_btn": "🛍️ متجر المنتجات",
        "redeem_btn": "🎁 أكواد الشحن",
        "invite_btn": "🔗 نظام الدعوات",
        "bonus_btn": "✨ مكافأة يومية",
        "support_btn": "💬 الدعم الفني",
        "req_prod_btn": "💡 طلب منتج جديد",
        "lang_btn": "🌐 تغيير اللغة",
        "admin_btn": "👑 ميزات الإدارة",
        "maint_msg": "🛠️ وضع الصيانة مفعل حالياً، نعتذر عن الإزعاج."
    },
    "en": {
        "welcome": "🌐 Please select your language to activate account:",
        "must_join": f"⚠️ You must subscribe to our channel first!\nJoin here: {CHANNEL_LINK}",
        "check_btn": "🔄 Check Subscription",
        "main_menu": "🏠 Store Main Menu:",
        "id_btn": "🆔 Show ID",
        "balance_btn": "💰 My Balance",
        "shop_btn": "🛍️ Product Shop",
        "redeem_btn": "🎁 Redeem Codes",
        "invite_btn": "🔗 Referral System",
        "bonus_btn": "✨ Daily Bonus",
        "support_btn": "💬 Technical Support",
        "req_prod_btn": "💡 Request Product",
        "lang_btn": "🌐 Change Language",
        "admin_btn": "👑 Admin Features",
        "maint_msg": "🛠️ Maintenance mode is currently active."
    },
    "fr": {
        "welcome": "🌐 Veuillez sélectionner votre langue:",
        "must_join": f"⚠️ Vous devez d'abord vous abonner à la chaîne!\nRejoignez: {CHANNEL_LINK}",
        "check_btn": "🔄 Vérifier l'abonnement",
        "main_menu": "🏠 Menu Principal de la Boutique:",
        "id_btn": "🆔 Afficher l'ID",
        "balance_btn": "💰 Mon Solde",
        "shop_btn": "🛍️ Boutique de Produits",
        "redeem_btn": "🎁 Codes de Recharge",
        "invite_btn": "🔗 Système de Parrainage",
        "bonus_btn": "✨ Bonus Quotidien",
        "support_btn": "💬 Support Technique",
        "req_prod_btn": "💡 Demander produit",
        "lang_btn": "🌐 Changer de Langue",
        "admin_btn": "👑 Fonctions Admin",
        "maint_msg": "🛠️ Le mode maintenance est activé."
    },
    "vi": {
        "welcome": "🌐 Vui lòng chọn ngôn ngữ của bạn:",
        "must_join": f"⚠️ Bạn phải đăng ký kênh trước!\nTham gia tại: {CHANNEL_LINK}",
        "check_btn": "🔄 Kiểm tra đăng ký",
        "main_menu": "🏠 Danh Mục Chính Cửa Hàng:",
        "id_btn": "🆔 Hiển thị ID",
        "balance_btn": "💰 Số dư của tôi",
        "shop_btn": "🛍️ Cửa hàng sản phẩm",
        "redeem_btn": "🎁 Nạp mã giảm giá",
        "invite_btn": "🔗 Hệ thống giới thiệu",
        "bonus_btn": "✨ Phần thưởng hàng ngày",
        "support_btn": "💬 Hỗ trợ kỹ thuật",
        "req_prod_btn": "💡 Yêu cầu sản phẩm",
        "lang_btn": "🌐 Thay đổi ngôn ngữ",
        "admin_btn": "👑 Tính năng Admin",
        "maint_msg": "🛠️ Bot hiện đang được bảo trì."
    },
    "es": {
        "welcome": "🌐 Por favor, seleccione el idioma del bot para activar su cuenta:",
        "must_join": f"⚠️ ¡Debe suscribirse a nuestro canal primero para usar el bot!\nÚnase aquí: {CHANNEL_LINK}",
        "check_btn": "🔄 Verificar Suscripción",
        "main_menu": "🏠 Menú Principal de la Tienda:",
        "id_btn": "🆔 Mostrar ID",
        "balance_btn": "💰 Mi Saldo",
        "shop_btn": "🛍️ Tienda de Productos",
        "redeem_btn": "🎁 Canjear Códigos",
        "invite_btn": "🔗 Sistema de Referidos",
        "bonus_btn": "✨ Bono Diario",
        "support_btn": "💬 Soporte Técnico",
        "req_prod_btn": "💡 Solicitar Producto",
        "lang_btn": "🌐 Cambiar Idioma",
        "admin_btn": "👑 Funciones de Admin",
        "maint_msg": "🛠️ El mode de mantenimiento está activo actualmente."
    }
}
