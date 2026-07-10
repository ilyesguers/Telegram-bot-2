import os
import telebot

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

RANKS = {
    "silver":  {"name_ar": "🥈 الفضي", "name_en": "🥈 Silver", "points_needed": 200, "discount": 0.01},
    "gold":    {"name_ar": "🥇 الذهبي", "name_en": "🥇 Gold", "points_needed": 600, "discount": 0.02},
    "diamond": {"name_ar": "💎 الماسي", "name_en": "💎 Diamond", "points_needed": 1500, "discount": 0.03},
    "hero":    {"name_ar": "⚡ الهيرو", "name_en": "⚡ Hero", "points_needed": 3500, "discount": 0.04},
    "master":  {"name_ar": "👑 الماستر", "name_en": "👑 Master", "points_needed": 7000, "discount": 0.045},
    "legend":  {"name_ar": "🏆 الأسطورة", "name_en": "🏆 Legend", "points_needed": 12000, "discount": 0.05}
}

# =====================================================
# 🌐 نظام الترجمة الشامل
# =====================================================
LOCALES = {
    "ar": {
        # === القائمة الرئيسية ===
        "welcome": "🌐 <b>مرحباً بك!</b>\n\n🇸🇦 اختر لغتك المفضلة:",
        "must_join": "🔐 <b>الاشتراك إجباري!</b>\n\n⚠️ يجب الاشتراك بقناتنا لاستخدام البوت",
        "check_btn": "✅ تحقق من الاشتراك",
        "join_channel": "📢 اشترك في القناة",
        "main_menu_title": "🏠 <b>القائمة الرئيسية</b>\n\n<i>مرحباً {name}! اختر ما تريده:</i>",
        
        # === أزرار القائمة الرئيسية ===
        "btn_account": "👤 حسابي",
        "btn_shop": "🛍️ المتجر",
        "btn_rewards": "🎁 المكافآت",
        "btn_entertainment": "🎮 الترفيه",
        "btn_support": "💬 الدعم",
        "btn_settings": "⚙️ الإعدادات",
        "btn_admin": "👑 لوحة الإدارة",
        "btn_back": "🔙 رجوع",
        
        # === قسم حسابي ===
        "account_title": "👤 <b>حسابي الشخصي</b>",
        "account_desc": "جميع معلومات حسابك في مكان واحد",
        "btn_balance": "💰 رصيدي",
        "btn_my_id": "🆔 معلوماتي",
        "btn_my_rank": "🏆 رتبتي",
        "btn_referral": "🔗 نظام الإحالة",
        "btn_my_purchases": "📜 مشترياتي",
        
        # === قسم المكافآت ===
        "rewards_title": "🎁 <b>مركز المكافآت</b>",
        "rewards_desc": "احصل على نقاط مجانية يومياً!",
        "btn_daily_bonus": "✨ المكافأة اليومية",
        "btn_redeem_code": "🎫 استرداد كود",
        "btn_quests": "🔥 المهام والإنجازات",
        
        # === قسم الترفيه ===
        "entertainment_title": "🎮 <b>مركز الترفيه</b>",
        "entertainment_desc": "العب واكسب المزيد من النقاط!",
        "btn_lootbox": "🎰 صندوق الحظ",
        "btn_wheel": "🎡 عجلة الحظ",
        
        # === قسم الدعم ===
        "support_title": "💬 <b>مركز الدعم</b>",
        "support_desc": "فريقنا هنا لمساعدتك!",
        "btn_open_ticket": "🎫 فتح تذكرة دعم",
        "btn_my_tickets": "📋 تذاكري",
        "btn_request_product": "💡 طلب منتج جديد",
        
        # === قسم الإعدادات ===
        "settings_title": "⚙️ <b>الإعدادات</b>",
        "settings_desc": "خصص تجربتك",
        "btn_change_lang": "🌐 تغيير اللغة",
        "btn_notifications": "🔔 الإشعارات",
        
        # === رسائل عامة ===
        "banned": "🚫 <b>حسابك محظور!</b>",
        "maint_msg": "🛠️ <b>البوت تحت الصيانة</b>\n⏳ نعود قريباً!",
        "invalid_input": "❌ إدخال غير صحيح",
        "success": "✅ تم بنجاح!",
        "cancelled": "❌ تم الإلغاء",
        "loading": "⏳ جاري التحميل...",
        "insufficient_balance": "❌ رصيدك غير كافٍ!",
        
        # === الرصيد ===
        "balance_display": "💰 <b>محفظتي</b>\n\n━━━━━━━━━━━━━\n👤 الآيدي: <code>{uid}</code>\n💵 الرصيد: <b>{points}</b> نقطة\n🏆 الرتبة: {rank}\n💎 الخصم: {discount}%\n👥 الدعوات: {invites}\n📊 التراكمية: {acc}\n━━━━━━━━━━━━━",
        
        # === المكافأة اليومية ===
        "daily_success": "🎁 <b>مكافأة يومية!</b>\n\n━━━━━━━━━━━━━\n✨ حصلت على: <b>+{gift}</b> نقطة\n💰 رصيدك: <b>{balance}</b>\n⏰ المكافأة القادمة: 24 ساعة\n━━━━━━━━━━━━━",
        "daily_wait": "⏰ <b>عد بعد:</b> {hours}س {mins}د\n\n💡 استمر يومياً لتجميع النقاط!",
        
        # === الإحالة ===
        "referral_msg": "🔗 <b>نظام الإحالة</b>\n\n━━━━━━━━━━━━━\n👥 دعواتك: <b>{invites}</b>\n🎁 لكل دعوة: <b>{reward}</b> نقطة\n💵 أرباحك: <b>{total}</b>\n━━━━━━━━━━━━━\n\n📎 <b>رابطك:</b>\n<code>{link}</code>",
        "invite_reward": "🎊 <b>دعوة جديدة!</b>\n\n🎁 مكافأتك: <b>+{reward}</b> نقطة",
        
        # === المتجر ===
        "shop_empty": "📭 <b>المتجر فارغ حالياً</b>",
        "shop_header": "🛍️ <b>المتجر</b>\n\n━━━━━━━━━━━━━\n💰 رصيدك: <b>{points}</b>\n🏆 رتبتك: {rank}\n💎 خصمك: <b>{disc}%</b>\n━━━━━━━━━━━━━\n\n👇 اختر المنتج:",
        "product_details": "📦 <b>{prod}</b>\n\n💎 خصمك: <b>{disc}%</b>\n💰 رصيدك: <b>{points}</b>\n\n⏱️ اختر المدة:",
        "purchase_success": "🎉 <b>تم الشراء!</b>\n\n━━━━━━━━━━━━━\n📦 {prod}\n⏱️ {plan}\n💰 {price} نقطة\n━━━━━━━━━━━━━\n\n🔐 <b>مفتاحك:</b>\n<code>{key}</code>\n\n⚠️ احفظه في مكان آمن!",
        
        # === التذاكر ===
        "ticket_write": "💬 اكتب رسالتك للدعم:",
        "ticket_created": "✅ <b>تم فتح تذكرة #{tid}</b>\n\n⏳ سيرد عليك الفريق قريباً",
        "my_tickets_title": "📋 <b>تذاكري</b>",
        "no_tickets": "📭 لا توجد تذاكر مفتوحة",
        
        # === طلب منتج ===
        "product_request_write": "💡 اكتب اسم المنتج وتفاصيله:",
        "product_request_sent": "✅ <b>تم إرسال طلبك!</b>\n🎫 رقم: <code>#{rid}</code>",
        
        # === الكابتشا ===
        "captcha_title": "🛡️ <b>تحقق أمني</b>\n\n⚠️ اضغط على: <b>{name}</b> {emoji}",
        "captcha_correct": "✅ <b>تم التحقق بنجاح!</b>",
        "captcha_wrong": "❌ إجابة خاطئة!",
        "captcha_banned": "🚫 تم حظرك ساعة",
        
        # === الرتب ===
        "rank_title": "🏆 <b>رتبتي</b>\n\n━━━━━━━━━━━━━\n🎖️ الحالية: {rank}\n💎 الخصم: <b>{disc}%</b>\n📊 النقاط: <code>{acc}</code>\n━━━━━━━━━━━━━",
        
        # === المهام ===
        "quests_title": "🔥 <b>المهام والإنجازات</b>",
        
        # === تغيير اللغة ===
        "lang_changed": "✅ <b>تم تغيير اللغة!</b>",
    },
    
    "en": {
        "welcome": "🌐 <b>Welcome!</b>\n\n🇺🇸 Please select your language:",
        "must_join": "🔐 <b>Subscription Required!</b>\n\n⚠️ You must join our channel to use the bot",
        "check_btn": "✅ Check Subscription",
        "join_channel": "📢 Join Channel",
        "main_menu_title": "🏠 <b>Main Menu</b>\n\n<i>Welcome {name}! Choose what you want:</i>",
        
        "btn_account": "👤 My Account",
        "btn_shop": "🛍️ Shop",
        "btn_rewards": "🎁 Rewards",
        "btn_entertainment": "🎮 Entertainment",
        "btn_support": "💬 Support",
        "btn_settings": "⚙️ Settings",
        "btn_admin": "👑 Admin Panel",
        "btn_back": "🔙 Back",
        
        "account_title": "👤 <b>My Account</b>",
        "account_desc": "All your account info in one place",
        "btn_balance": "💰 My Balance",
        "btn_my_id": "🆔 My Info",
        "btn_my_rank": "🏆 My Rank",
        "btn_referral": "🔗 Referral System",
        "btn_my_purchases": "📜 My Purchases",
        
        "rewards_title": "🎁 <b>Rewards Center</b>",
        "rewards_desc": "Get free points daily!",
        "btn_daily_bonus": "✨ Daily Bonus",
        "btn_redeem_code": "🎫 Redeem Code",
        "btn_quests": "🔥 Quests & Achievements",
        
        "entertainment_title": "🎮 <b>Entertainment Center</b>",
        "entertainment_desc": "Play and win more points!",
        "btn_lootbox": "🎰 Loot Box",
        "btn_wheel": "🎡 Lucky Wheel",
        
        "support_title": "💬 <b>Support Center</b>",
        "support_desc": "Our team is here to help you!",
        "btn_open_ticket": "🎫 Open Ticket",
        "btn_my_tickets": "📋 My Tickets",
        "btn_request_product": "💡 Request Product",
        
        "settings_title": "⚙️ <b>Settings</b>",
        "settings_desc": "Customize your experience",
        "btn_change_lang": "🌐 Change Language",
        "btn_notifications": "🔔 Notifications",
        
        "banned": "🚫 <b>Your account is banned!</b>",
        "maint_msg": "🛠️ <b>Bot is under maintenance</b>\n⏳ Back soon!",
        "invalid_input": "❌ Invalid input",
        "success": "✅ Success!",
        "cancelled": "❌ Cancelled",
        "loading": "⏳ Loading...",
        "insufficient_balance": "❌ Insufficient balance!",
        
        "balance_display": "💰 <b>My Wallet</b>\n\n━━━━━━━━━━━━━\n👤 ID: <code>{uid}</code>\n💵 Balance: <b>{points}</b> pts\n🏆 Rank: {rank}\n💎 Discount: {discount}%\n👥 Invites: {invites}\n📊 Total: {acc}\n━━━━━━━━━━━━━",
        
        "daily_success": "🎁 <b>Daily Bonus!</b>\n\n━━━━━━━━━━━━━\n✨ You got: <b>+{gift}</b> pts\n💰 Balance: <b>{balance}</b>\n⏰ Next bonus: 24 hours\n━━━━━━━━━━━━━",
        "daily_wait": "⏰ <b>Come back in:</b> {hours}h {mins}m",
        
        "referral_msg": "🔗 <b>Referral System</b>\n\n━━━━━━━━━━━━━\n👥 Invites: <b>{invites}</b>\n🎁 Per invite: <b>{reward}</b> pts\n💵 Earnings: <b>{total}</b>\n━━━━━━━━━━━━━\n\n📎 <b>Your link:</b>\n<code>{link}</code>",
        "invite_reward": "🎊 <b>New invite!</b>\n\n🎁 Reward: <b>+{reward}</b> pts",
        
        "shop_empty": "📭 <b>Shop is empty</b>",
        "shop_header": "🛍️ <b>Shop</b>\n\n━━━━━━━━━━━━━\n💰 Balance: <b>{points}</b>\n🏆 Rank: {rank}\n💎 Discount: <b>{disc}%</b>\n━━━━━━━━━━━━━\n\n👇 Select product:",
        "product_details": "📦 <b>{prod}</b>\n\n💎 Your discount: <b>{disc}%</b>\n💰 Balance: <b>{points}</b>\n\n⏱️ Choose duration:",
        "purchase_success": "🎉 <b>Purchase Complete!</b>\n\n━━━━━━━━━━━━━\n📦 {prod}\n⏱️ {plan}\n💰 {price} pts\n━━━━━━━━━━━━━\n\n🔐 <b>Your key:</b>\n<code>{key}</code>\n\n⚠️ Save it safely!",
        
        "ticket_write": "💬 Write your support message:",
        "ticket_created": "✅ <b>Ticket #{tid} opened</b>\n\n⏳ Team will reply soon",
        "my_tickets_title": "📋 <b>My Tickets</b>",
        "no_tickets": "📭 No open tickets",
        
        "product_request_write": "💡 Write product name and details:",
        "product_request_sent": "✅ <b>Request sent!</b>\n🎫 ID: <code>#{rid}</code>",
        
        "captcha_title": "🛡️ <b>Security Check</b>\n\n⚠️ Press on: <b>{name}</b> {emoji}",
        "captcha_correct": "✅ <b>Verified successfully!</b>",
        "captcha_wrong": "❌ Wrong answer!",
        "captcha_banned": "🚫 Banned for 1 hour",
        
        "rank_title": "🏆 <b>My Rank</b>\n\n━━━━━━━━━━━━━\n🎖️ Current: {rank}\n💎 Discount: <b>{disc}%</b>\n📊 Points: <code>{acc}</code>\n━━━━━━━━━━━━━",
        
        "quests_title": "🔥 <b>Quests & Achievements</b>",
        
        "lang_changed": "✅ <b>Language changed!</b>",
    },
    
    "fr": {
        "welcome": "🌐 <b>Bienvenue!</b>\n\n🇫🇷 Sélectionnez votre langue:",
        "must_join": "🔐 <b>Abonnement Requis!</b>\n\n⚠️ Rejoignez notre chaîne pour utiliser le bot",
        "check_btn": "✅ Vérifier",
        "join_channel": "📢 Rejoindre",
        "main_menu_title": "🏠 <b>Menu Principal</b>\n\n<i>Bienvenue {name}!</i>",
        
        "btn_account": "👤 Mon Compte",
        "btn_shop": "🛍️ Boutique",
        "btn_rewards": "🎁 Récompenses",
        "btn_entertainment": "🎮 Divertissement",
        "btn_support": "💬 Support",
        "btn_settings": "⚙️ Paramètres",
        "btn_admin": "👑 Admin",
        "btn_back": "🔙 Retour",
        
        "account_title": "👤 <b>Mon Compte</b>",
        "account_desc": "Toutes vos infos ici",
        "btn_balance": "💰 Mon Solde",
        "btn_my_id": "🆔 Mes Infos",
        "btn_my_rank": "🏆 Mon Rang",
        "btn_referral": "🔗 Parrainage",
        "btn_my_purchases": "📜 Mes Achats",
        
        "rewards_title": "🎁 <b>Récompenses</b>",
        "rewards_desc": "Points gratuits chaque jour!",
        "btn_daily_bonus": "✨ Bonus Quotidien",
        "btn_redeem_code": "🎫 Utiliser Code",
        "btn_quests": "🔥 Quêtes",
        
        "entertainment_title": "🎮 <b>Divertissement</b>",
        "entertainment_desc": "Jouez et gagnez!",
        "btn_lootbox": "🎰 Coffre",
        "btn_wheel": "🎡 Roue",
        
        "support_title": "💬 <b>Support</b>",
        "support_desc": "Notre équipe est là!",
        "btn_open_ticket": "🎫 Ouvrir Ticket",
        "btn_my_tickets": "📋 Mes Tickets",
        "btn_request_product": "💡 Demander Produit",
        
        "settings_title": "⚙️ <b>Paramètres</b>",
        "settings_desc": "Personnalisez",
        "btn_change_lang": "🌐 Langue",
        "btn_notifications": "🔔 Notifications",
        
        "banned": "🚫 <b>Compte banni!</b>",
        "maint_msg": "🛠️ <b>Maintenance</b>",
        "invalid_input": "❌ Entrée invalide",
        "success": "✅ Succès!",
        "cancelled": "❌ Annulé",
        "loading": "⏳ Chargement...",
        "insufficient_balance": "❌ Solde insuffisant!",
        
        "balance_display": "💰 <b>Portefeuille</b>\n\n━━━━━━━━━━━━━\n👤 ID: <code>{uid}</code>\n💵 Solde: <b>{points}</b>\n🏆 Rang: {rank}\n💎 Remise: {discount}%\n👥 Invitations: {invites}\n📊 Total: {acc}\n━━━━━━━━━━━━━",
        
        "daily_success": "🎁 <b>Bonus Quotidien!</b>\n\n✨ +{gift} pts\n💰 Solde: {balance}",
        "daily_wait": "⏰ Revenez dans: {hours}h {mins}m",
        
        "referral_msg": "🔗 <b>Parrainage</b>\n\n👥 {invites} invitations\n💵 Gains: {total}\n\n📎 <code>{link}</code>",
        "invite_reward": "🎊 Nouvelle invitation!\n🎁 +{reward} pts",
        
        "shop_empty": "📭 Boutique vide",
        "shop_header": "🛍️ <b>Boutique</b>\n\n💰 {points} | 💎 {disc}%\n\n👇 Choisissez:",
        "product_details": "📦 <b>{prod}</b>\n💎 {disc}% | 💰 {points}\n\n⏱️ Durée:",
        "purchase_success": "🎉 <b>Achat!</b>\n\n📦 {prod}\n⏱️ {plan}\n💰 {price}\n\n🔐 <code>{key}</code>",
        
        "ticket_write": "💬 Votre message:",
        "ticket_created": "✅ Ticket #{tid} ouvert",
        "my_tickets_title": "📋 <b>Mes Tickets</b>",
        "no_tickets": "📭 Aucun ticket",
        
        "product_request_write": "💡 Nom du produit:",
        "product_request_sent": "✅ Envoyé! #{rid}",
        
        "captcha_title": "🛡️ <b>Vérification</b>\n\nCliquez: <b>{name}</b> {emoji}",
        "captcha_correct": "✅ Vérifié!",
        "captcha_wrong": "❌ Faux!",
        "captcha_banned": "🚫 Banni 1h",
        
        "rank_title": "🏆 <b>Mon Rang</b>\n\n🎖️ {rank}\n💎 {disc}%\n📊 {acc}",
        
        "quests_title": "🔥 <b>Quêtes</b>",
        "lang_changed": "✅ Langue changée!",
    },
    
    "es": {
        "welcome": "🌐 <b>¡Bienvenido!</b>\n\n🇪🇸 Selecciona tu idioma:",
        "must_join": "🔐 <b>¡Suscripción Requerida!</b>",
        "check_btn": "✅ Verificar",
        "join_channel": "📢 Unirse",
        "main_menu_title": "🏠 <b>Menú Principal</b>\n\n<i>¡Bienvenido {name}!</i>",
        
        "btn_account": "👤 Mi Cuenta",
        "btn_shop": "🛍️ Tienda",
        "btn_rewards": "🎁 Recompensas",
        "btn_entertainment": "🎮 Entretenimiento",
        "btn_support": "💬 Soporte",
        "btn_settings": "⚙️ Ajustes",
        "btn_admin": "👑 Admin",
        "btn_back": "🔙 Atrás",
        
        "account_title": "👤 <b>Mi Cuenta</b>",
        "account_desc": "Toda tu info aquí",
        "btn_balance": "💰 Saldo",
        "btn_my_id": "🆔 Info",
        "btn_my_rank": "🏆 Rango",
        "btn_referral": "🔗 Referidos",
        "btn_my_purchases": "📜 Compras",
        
        "rewards_title": "🎁 <b>Recompensas</b>",
        "rewards_desc": "¡Puntos gratis diarios!",
        "btn_daily_bonus": "✨ Bono Diario",
        "btn_redeem_code": "🎫 Canjear",
        "btn_quests": "🔥 Misiones",
        
        "entertainment_title": "🎮 <b>Entretenimiento</b>",
        "entertainment_desc": "¡Juega y gana!",
        "btn_lootbox": "🎰 Caja",
        "btn_wheel": "🎡 Ruleta",
        
        "support_title": "💬 <b>Soporte</b>",
        "support_desc": "¡Estamos aquí!",
        "btn_open_ticket": "🎫 Abrir Ticket",
        "btn_my_tickets": "📋 Mis Tickets",
        "btn_request_product": "💡 Solicitar",
        
        "settings_title": "⚙️ <b>Ajustes</b>",
        "settings_desc": "Personaliza",
        "btn_change_lang": "🌐 Idioma",
        "btn_notifications": "🔔 Notificaciones",
        
        "banned": "🚫 <b>¡Baneado!</b>",
        "maint_msg": "🛠️ Mantenimiento",
        "invalid_input": "❌ Inválido",
        "success": "✅ ¡Éxito!",
        "cancelled": "❌ Cancelado",
        "loading": "⏳ Cargando...",
        "insufficient_balance": "❌ ¡Saldo insuficiente!",
        
        "balance_display": "💰 <b>Cartera</b>\n\n👤 <code>{uid}</code>\n💵 {points} pts\n🏆 {rank}\n💎 {discount}%\n👥 {invites}\n📊 {acc}",
        
        "daily_success": "🎁 <b>¡Bono!</b>\n\n✨ +{gift} pts\n💰 {balance}",
        "daily_wait": "⏰ Vuelve en: {hours}h {mins}m",
        
        "referral_msg": "🔗 <b>Referidos</b>\n\n👥 {invites}\n💵 {total}\n\n<code>{link}</code>",
        "invite_reward": "🎊 ¡Nueva invitación!\n🎁 +{reward}",
        
        "shop_empty": "📭 Tienda vacía",
        "shop_header": "🛍️ <b>Tienda</b>\n💰 {points} | 💎 {disc}%",
        "product_details": "📦 <b>{prod}</b>\n💎 {disc}% | 💰 {points}",
        "purchase_success": "🎉 <b>¡Comprado!</b>\n\n📦 {prod}\n⏱️ {plan}\n💰 {price}\n\n🔐 <code>{key}</code>",
        
        "ticket_write": "💬 Tu mensaje:",
        "ticket_created": "✅ Ticket #{tid}",
        "my_tickets_title": "📋 <b>Mis Tickets</b>",
        "no_tickets": "📭 Sin tickets",
        
        "product_request_write": "💡 Producto:",
        "product_request_sent": "✅ ¡Enviado! #{rid}",
        
        "captcha_title": "🛡️ <b>Verificación</b>\n\nToca: <b>{name}</b> {emoji}",
        "captcha_correct": "✅ ¡Verificado!",
        "captcha_wrong": "❌ ¡Incorrecto!",
        "captcha_banned": "🚫 Baneado 1h",
        
        "rank_title": "🏆 <b>Rango</b>\n\n🎖️ {rank}\n💎 {disc}%\n📊 {acc}",
        
        "quests_title": "🔥 <b>Misiones</b>",
        "lang_changed": "✅ ¡Idioma cambiado!",
    },
    
    "vi": {
        "welcome": "🌐 <b>Chào mừng!</b>\n\n🇻🇳 Chọn ngôn ngữ:",
        "must_join": "🔐 <b>Yêu cầu đăng ký!</b>",
        "check_btn": "✅ Kiểm tra",
        "join_channel": "📢 Tham gia",
        "main_menu_title": "🏠 <b>Menu chính</b>\n\n<i>Chào {name}!</i>",
        
        "btn_account": "👤 Tài khoản",
        "btn_shop": "🛍️ Cửa hàng",
        "btn_rewards": "🎁 Phần thưởng",
        "btn_entertainment": "🎮 Giải trí",
        "btn_support": "💬 Hỗ trợ",
        "btn_settings": "⚙️ Cài đặt",
        "btn_admin": "👑 Admin",
        "btn_back": "🔙 Quay lại",
        
        "account_title": "👤 <b>Tài khoản</b>",
        "account_desc": "Thông tin của bạn",
        "btn_balance": "💰 Số dư",
        "btn_my_id": "🆔 Thông tin",
        "btn_my_rank": "🏆 Cấp bậc",
        "btn_referral": "🔗 Giới thiệu",
        "btn_my_purchases": "📜 Đơn hàng",
        
        "rewards_title": "🎁 <b>Phần thưởng</b>",
        "rewards_desc": "Điểm miễn phí hàng ngày!",
        "btn_daily_bonus": "✨ Hàng ngày",
        "btn_redeem_code": "🎫 Đổi mã",
        "btn_quests": "🔥 Nhiệm vụ",
        
        "entertainment_title": "🎮 <b>Giải trí</b>",
        "entertainment_desc": "Chơi và thắng!",
        "btn_lootbox": "🎰 Hộp quà",
        "btn_wheel": "🎡 Vòng quay",
        
        "support_title": "💬 <b>Hỗ trợ</b>",
        "support_desc": "Chúng tôi ở đây!",
        "btn_open_ticket": "🎫 Mở vé",
        "btn_my_tickets": "📋 Vé của tôi",
        "btn_request_product": "💡 Yêu cầu",
        
        "settings_title": "⚙️ <b>Cài đặt</b>",
        "settings_desc": "Tùy chỉnh",
        "btn_change_lang": "🌐 Ngôn ngữ",
        "btn_notifications": "🔔 Thông báo",
        
        "banned": "🚫 <b>Bị cấm!</b>",
        "maint_msg": "🛠️ Bảo trì",
        "invalid_input": "❌ Không hợp lệ",
        "success": "✅ Thành công!",
        "cancelled": "❌ Đã hủy",
        "loading": "⏳ Đang tải...",
        "insufficient_balance": "❌ Không đủ!",
        
        "balance_display": "💰 <b>Ví</b>\n\n👤 <code>{uid}</code>\n💵 {points}\n🏆 {rank}\n💎 {discount}%\n👥 {invites}\n📊 {acc}",
        
        "daily_success": "🎁 <b>Thưởng!</b>\n\n✨ +{gift}\n💰 {balance}",
        "daily_wait": "⏰ Quay lại: {hours}h {mins}p",
        
        "referral_msg": "🔗 <b>Giới thiệu</b>\n\n👥 {invites}\n💵 {total}\n\n<code>{link}</code>",
        "invite_reward": "🎊 Lời mời mới!\n🎁 +{reward}",
        
        "shop_empty": "📭 Trống",
        "shop_header": "🛍️ <b>Cửa hàng</b>\n💰 {points} | 💎 {disc}%",
        "product_details": "📦 <b>{prod}</b>\n💎 {disc}% | 💰 {points}",
        "purchase_success": "🎉 <b>Mua!</b>\n\n📦 {prod}\n⏱️ {plan}\n\n🔐 <code>{key}</code>",
        
        "ticket_write": "💬 Tin nhắn:",
        "ticket_created": "✅ Vé #{tid}",
        "my_tickets_title": "📋 <b>Vé</b>",
        "no_tickets": "📭 Không có vé",
        
        "product_request_write": "💡 Sản phẩm:",
        "product_request_sent": "✅ Đã gửi! #{rid}",
        
        "captcha_title": "🛡️ <b>Xác thực</b>\n\nBấm: <b>{name}</b> {emoji}",
        "captcha_correct": "✅ Xác thực!",
        "captcha_wrong": "❌ Sai!",
        "captcha_banned": "🚫 Cấm 1h",
        
        "rank_title": "🏆 <b>Cấp</b>\n\n🎖️ {rank}\n💎 {disc}%\n📊 {acc}",
        
        "quests_title": "🔥 <b>Nhiệm vụ</b>",
        "lang_changed": "✅ Đã đổi!",
    }
}

def t(lang, key, **kwargs):
    """دالة الترجمة الذكية"""
    if lang not in LOCALES:
        lang = "en"
    text = LOCALES[lang].get(key, LOCALES["en"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text
