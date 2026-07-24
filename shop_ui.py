"""
=====================================================
 shop_ui.py — Shop rendering, translations & animation
=====================================================
 🛍️ Builds every shop screen (catalogue / product / receipt)
 🎬 Frame based animation engine used by the shop flow
 🌍 AR / EN / FR / ES / VI
 🧪 Pure helpers: no Telegram token required to import,
    so the screens can be unit tested without network.
=====================================================
"""

import hashlib
import time

from telebot import types

# =====================================================
# 📦 Plans handled by the store (order matters in the UI)
# =====================================================
PLANS = ["1 Day", "7 Days", "30 Days"]
PLAN_KEYS = {"1 Day": "days_1", "7 Days": "days_7", "30 Days": "days_30"}

# Animation bars
LOADING_BARS = [
    "▰▱▱▱▱▱",
    "▰▰▱▱▱▱",
    "▰▰▰▱▱▱",
    "▰▰▰▰▱▱",
    "▰▰▰▰▰▱",
    "▰▰▰▰▰▰",
]

SHOP_TRANSLATIONS = {
    "ar": {
        "title": "🛍️ <b>━━ السوق المركزي ━━</b>",
        "subtitle": "✨ <i>أفضل الأدوات بأرخص الأسعار حصرياً لك</i>",
        "wallet": "💳 المحفظة",
        "rank_disc": "🛡️ خصم الرتبة",
        "flash": "⚡ عرض خاطف جنوني:",
        "off": "خصم",
        "select_prod": "👇 <b>اختر منتجاً لاستعراض التفاصيل:</b>",
        "prod_info": "📦 <b>━━ معلومات المنتج ━━</b>",
        "prod_name": "📌 <b>الاسم:</b>",
        "prod_desc_text": "🔥 <i>أقوى أداة في السوق، تحديثات مستمرة وأمان عالي جداً! لا تفوت الفرصة.</i>",
        "balance": "💰 رصيدك",
        "duration": "⏱️ <b>اختر باقة الاشتراك المناسبة لك:</b>",
        "days_1": "1 يوم", "days_7": "7 أيام", "days_30": "30 يوم",
        "stock": "المخزون", "price": "السعر", "available": "متوفر", "out": "نفد",
        "btn_buy": "🛒 شراء الآن", "btn_back": "🔙 العودة للمتجر",
        "empty": "📭 المتجر فارغ حالياً.",
        "out_alert": "⚠️ نفدت الكمية من هذا المنتج!",
        "buy_error": "❌ حدث خطأ أثناء الشراء. يرجى التواصل مع الدعم.",
        # ── جديد ──
        "opening": "جاري فتح المتجر",
        "loading_prod": "جاري تحميل المنتج",
        "processing": "جاري تجهيز طلبك",
        "ready": "جاهز",
        "btn_refresh": "🔄 تحديث المتجر",
        "btn_home": "🏠 القائمة الرئيسية",
        "products_count": "🗂️ عدد المنتجات",
        "starts_from": "🏷️ تبدأ الأسعار من",
        "flash_ends": "⏰ ينتهي خلال",
        "soldout_hint": "⚠️ <i>نفدت كل الباقات في هذا المنتج، سيتم التزويد قريباً.</i>",
        "empty_hint": "🔔 <i>لم يتم إضافة أي منتج بعد. فعّل الإشعارات لتكون أول من يعلم!</i>",
        "prod_missing": "❌ هذا المنتج لم يعد متوفراً في المتجر.",
        "plan_out_alert": "⚠️ هذه الباقة نفدت! جرّب باقة أخرى.",
        "price_error": "⚠️ سعر هذه الباقة غير مضبوط. تواصل مع الدعم.",
        "purchase_done": "🎉 <b>━━ تمت عملية الشراء ━━</b> 🎉",
        "your_key": "🔐 <b>مفتاحك:</b>",
        "save_key": "⚠️ <i>احفظ المفتاح في مكان آمن!</i>",
        "delivered": "✅ <b>تم التسليم بنجاح!</b>",
        "paid": "💰 المدفوع",
        "product": "📦 المنتج",
        "plan": "⏱️ المدة",
        "you_save": "🎯 وفّرت",
        "total_disc": "🏷️ إجمالي الخصم",
    },
    "en": {
        "title": "🛍️ <b>━━ CENTRAL SHOP ━━</b>",
        "subtitle": "✨ <i>Best tools at the lowest prices exclusively for you</i>",
        "wallet": "💳 Wallet",
        "rank_disc": "🛡️ Rank Discount",
        "flash": "⚡ CRAZY FLASH SALE:",
        "off": "OFF",
        "select_prod": "👇 <b>Select a product to view details:</b>",
        "prod_info": "📦 <b>━━ Product Info ━━</b>",
        "prod_name": "📌 <b>Name:</b>",
        "prod_desc_text": "🔥 <i>Top tier tool in the market, constant updates & very high security!</i>",
        "balance": "💰 Balance",
        "duration": "⏱️ <b>Choose your subscription plan:</b>",
        "days_1": "1 Day", "days_7": "7 Days", "days_30": "30 Days",
        "stock": "Stock", "price": "Price", "available": "Available", "out": "Out of stock",
        "btn_buy": "🛒 Buy Now", "btn_back": "🔙 Back to Shop",
        "empty": "📭 Shop is currently empty.",
        "out_alert": "⚠️ This product is out of stock!",
        "buy_error": "❌ Error during purchase. Please contact support.",
        # ── new ──
        "opening": "Opening the shop",
        "loading_prod": "Loading product",
        "processing": "Preparing your order",
        "ready": "Ready",
        "btn_refresh": "🔄 Refresh Shop",
        "btn_home": "🏠 Main Menu",
        "products_count": "🗂️ Products",
        "starts_from": "🏷️ Starting from",
        "flash_ends": "⏰ Ends in",
        "soldout_hint": "⚠️ <i>Every plan is sold out, restock is coming soon.</i>",
        "empty_hint": "🔔 <i>No product added yet. Enable notifications to be the first to know!</i>",
        "prod_missing": "❌ This product is no longer available.",
        "plan_out_alert": "⚠️ This plan is sold out! Try another one.",
        "price_error": "⚠️ Price is not configured for this plan. Contact support.",
        "purchase_done": "🎉 <b>━━ PURCHASE COMPLETE ━━</b> 🎉",
        "your_key": "🔐 <b>Your key:</b>",
        "save_key": "⚠️ <i>Save your key in a safe place!</i>",
        "delivered": "✅ <b>Delivered successfully!</b>",
        "paid": "💰 Paid",
        "product": "📦 Product",
        "plan": "⏱️ Duration",
        "you_save": "🎯 You saved",
        "total_disc": "🏷️ Total discount",
    },
    "fr": {
        "title": "🛍️ <b>━━ BOUTIQUE CENTRALE ━━</b>",
        "subtitle": "✨ <i>Les meilleurs outils aux prix les plus bas pour vous</i>",
        "wallet": "💳 Portefeuille",
        "rank_disc": "🛡️ Réduction Rang",
        "flash": "⚡ VENTE ÉCLAIR DE FOLIE:",
        "off": "RÉDUCTION",
        "select_prod": "👇 <b>Sélectionnez un produit pour voir les détails:</b>",
        "prod_info": "📦 <b>━━ Info Produit ━━</b>",
        "prod_name": "📌 <b>Nom:</b>",
        "prod_desc_text": "🔥 <i>Meilleur outil du marché, mises à jour constantes et haute sécurité!</i>",
        "balance": "💰 Solde",
        "duration": "⏱️ <b>Choisissez votre forfait d'abonnement:</b>",
        "days_1": "1 Jour", "days_7": "7 Jours", "days_30": "30 Jours",
        "stock": "Stock", "price": "Prix", "available": "Disponible", "out": "Épuisé",
        "btn_buy": "🛒 Acheter", "btn_back": "🔙 Retour Boutique",
        "empty": "📭 La boutique est actuellement vide.",
        "out_alert": "⚠️ Ce produit est en rupture de stock!",
        "buy_error": "❌ Erreur lors de l'achat. Veuillez contacter le support.",
        # ── nouveau ──
        "opening": "Ouverture de la boutique",
        "loading_prod": "Chargement du produit",
        "processing": "Préparation de la commande",
        "ready": "Prêt",
        "btn_refresh": "🔄 Actualiser",
        "btn_home": "🏠 Menu Principal",
        "products_count": "🗂️ Produits",
        "starts_from": "🏷️ À partir de",
        "flash_ends": "⏰ Fin dans",
        "soldout_hint": "⚠️ <i>Tous les forfaits sont épuisés, réapprovisionnement bientôt.</i>",
        "empty_hint": "🔔 <i>Aucun produit pour le moment. Activez les notifications!</i>",
        "prod_missing": "❌ Ce produit n'est plus disponible.",
        "plan_out_alert": "⚠️ Ce forfait est épuisé! Essayez un autre.",
        "price_error": "⚠️ Prix non configuré pour ce forfait. Contactez le support.",
        "purchase_done": "🎉 <b>━━ ACHAT TERMINÉ ━━</b> 🎉",
        "your_key": "🔐 <b>Votre clé:</b>",
        "save_key": "⚠️ <i>Conservez votre clé en lieu sûr!</i>",
        "delivered": "✅ <b>Livré avec succès!</b>",
        "paid": "💰 Payé",
        "product": "📦 Produit",
        "plan": "⏱️ Durée",
        "you_save": "🎯 Économisé",
        "total_disc": "🏷️ Réduction totale",
    },
    "es": {
        "title": "🛍️ <b>━━ TIENDA CENTRAL ━━</b>",
        "subtitle": "✨ <i>Las mejores herramientas a los precios más bajos</i>",
        "wallet": "💳 Billetera",
        "rank_disc": "🛡️ Descuento Rango",
        "flash": "⚡ OFERTA RELÁMPAGO:",
        "off": "DESCUENTO",
        "select_prod": "👇 <b>Selecciona un producto para ver detalles:</b>",
        "prod_info": "📦 <b>━━ Info de Producto ━━</b>",
        "prod_name": "📌 <b>Nombre:</b>",
        "prod_desc_text": "🔥 <i>¡La mejor herramienta, actualizaciones constantes y alta seguridad!</i>",
        "balance": "💰 Saldo",
        "duration": "⏱️ <b>Elige tu plan de suscripción:</b>",
        "days_1": "1 Día", "days_7": "7 Días", "days_30": "30 Días",
        "stock": "Stock", "price": "Precio", "available": "Disponible", "out": "Agotado",
        "btn_buy": "🛒 Comprar", "btn_back": "🔙 Volver a Tienda",
        "empty": "📭 La tienda está vacía.",
        "out_alert": "⚠️ ¡Este producto está agotado!",
        "buy_error": "❌ Error durante la compra. Por favor, contacte al soporte.",
        # ── nuevo ──
        "opening": "Abriendo la tienda",
        "loading_prod": "Cargando producto",
        "processing": "Preparando tu pedido",
        "ready": "Listo",
        "btn_refresh": "🔄 Actualizar",
        "btn_home": "🏠 Menú Principal",
        "products_count": "🗂️ Productos",
        "starts_from": "🏷️ Desde",
        "flash_ends": "⏰ Termina en",
        "soldout_hint": "⚠️ <i>Todos los planes están agotados, pronto habrá reposición.</i>",
        "empty_hint": "🔔 <i>Aún no hay productos. ¡Activa las notificaciones!</i>",
        "prod_missing": "❌ Este producto ya no está disponible.",
        "plan_out_alert": "⚠️ ¡Este plan está agotado! Prueba otro.",
        "price_error": "⚠️ Precio no configurado para este plan. Contacta al soporte.",
        "purchase_done": "🎉 <b>━━ COMPRA COMPLETADA ━━</b> 🎉",
        "your_key": "🔐 <b>Tu clave:</b>",
        "save_key": "⚠️ <i>¡Guarda tu clave en un lugar seguro!</i>",
        "delivered": "✅ <b>¡Entregado con éxito!</b>",
        "paid": "💰 Pagado",
        "product": "📦 Producto",
        "plan": "⏱️ Duración",
        "you_save": "🎯 Ahorraste",
        "total_disc": "🏷️ Descuento total",
    },
    "vi": {
        "title": "🛍️ <b>━━ CỬA HÀNG TRUNG TÂM ━━</b>",
        "subtitle": "✨ <i>Công cụ tốt nhất với giá rẻ nhất dành cho bạn</i>",
        "wallet": "💳 Ví",
        "rank_disc": "🛡️ Giảm giá Hạng",
        "flash": "⚡ SIÊU GIẢM GIÁ:",
        "off": "GIẢM",
        "select_prod": "👇 <b>Chọn sản phẩm để xem chi tiết:</b>",
        "prod_info": "📦 <b>━━ Thông tin Sản phẩm ━━</b>",
        "prod_name": "📌 <b>Tên:</b>",
        "prod_desc_text": "🔥 <i>Công cụ tốt nhất thị trường, cập nhật liên tục & bảo mật rất cao!</i>",
        "balance": "💰 Số dư",
        "duration": "⏱️ <b>Chọn gói đăng ký của bạn:</b>",
        "days_1": "1 Ngày", "days_7": "7 Ngày", "days_30": "30 Ngày",
        "stock": "Kho", "price": "Giá", "available": "Có sẵn", "out": "Hết hàng",
        "btn_buy": "🛒 Mua ngay", "btn_back": "🔙 Trở lại Cửa hàng",
        "empty": "📭 Cửa hàng hiện đang trống.",
        "out_alert": "⚠️ Sản phẩm này đã hết hàng!",
        "buy_error": "❌ Lỗi trong quá trình mua. Vui lòng liên hệ hỗ trợ.",
        # ── mới ──
        "opening": "Đang mở cửa hàng",
        "loading_prod": "Đang tải sản phẩm",
        "processing": "Đang chuẩn bị đơn hàng",
        "ready": "Sẵn sàng",
        "btn_refresh": "🔄 Làm mới",
        "btn_home": "🏠 Menu chính",
        "products_count": "🗂️ Sản phẩm",
        "starts_from": "🏷️ Giá từ",
        "flash_ends": "⏰ Kết thúc sau",
        "soldout_hint": "⚠️ <i>Tất cả các gói đã hết, sẽ sớm nhập thêm.</i>",
        "empty_hint": "🔔 <i>Chưa có sản phẩm nào. Bật thông báo để biết sớm nhất!</i>",
        "prod_missing": "❌ Sản phẩm này không còn nữa.",
        "plan_out_alert": "⚠️ Gói này đã hết! Hãy thử gói khác.",
        "price_error": "⚠️ Giá của gói này chưa được cài đặt. Liên hệ hỗ trợ.",
        "purchase_done": "🎉 <b>━━ MUA THÀNH CÔNG ━━</b> 🎉",
        "your_key": "🔐 <b>Key của bạn:</b>",
        "save_key": "⚠️ <i>Hãy lưu key ở nơi an toàn!</i>",
        "delivered": "✅ <b>Đã giao thành công!</b>",
        "paid": "💰 Đã trả",
        "product": "📦 Sản phẩm",
        "plan": "⏱️ Thời hạn",
        "you_save": "🎯 Tiết kiệm",
        "total_disc": "🏷️ Tổng giảm giá",
    },
}


def gt_shop(lang, key):
    """Translate a shop key, always falling back to English then the key itself."""
    table = SHOP_TRANSLATIONS.get(lang) or SHOP_TRANSLATIONS["en"]
    if key in table:
        return table[key]
    return SHOP_TRANSLATIONS["en"].get(key, key)


# =====================================================
# 🔑 Stable short product ids (callback_data is limited to 64 bytes)
# =====================================================
def product_id(name):
    """Short deterministic id for a product name (safe inside callback_data)."""
    return hashlib.md5(str(name).encode("utf-8")).hexdigest()[:10]


def resolve_product(token, products):
    """Resolve a callback token back to a real product name.

    Accepts both the new short id and the legacy raw product name so buttons
    from older messages keep working.
    """
    if token is None:
        return None
    token = str(token)
    for name in products:
        if name == token or product_id(name) == token:
            return name
    return None


# =====================================================
# 📊 Stock helpers
# =====================================================
def plan_stock(keys_store, product, plan):
    try:
        return len(keys_store.get(product, {}).get(plan, []) or [])
    except Exception:
        return 0


def product_stock(keys_store, product):
    return sum(plan_stock(keys_store, product, plan) for plan in PLANS)


# =====================================================
# 💰 Price engine (single source of truth for the whole bot)
# =====================================================
def compute_price(base_price, global_discount=0, flash_discount=0, rank_discount=0.0):
    """Return the final price for a plan.

    ``global_discount`` / ``flash_discount`` are percentages (0-100) and
    ``rank_discount`` is a ratio (0.0-1.0). The result can never be negative
    and the combined percentage discount is capped at 95% so a misconfigured
    flash sale can never make the shop give products away for free.
    """
    try:
        base_price = int(base_price or 0)
    except (TypeError, ValueError):
        base_price = 0
    if base_price <= 0:
        return 0

    percent = (global_discount or 0) + (flash_discount or 0)
    percent = max(0, min(95, percent))

    try:
        rank_discount = float(rank_discount or 0.0)
    except (TypeError, ValueError):
        rank_discount = 0.0
    rank_discount = max(0.0, min(0.95, rank_discount))

    final = base_price * (1 - percent / 100.0) * (1 - rank_discount)
    return max(0, int(final))


def flash_discount_for(flash_sale, product):
    """Discount percentage of an active flash sale for this product (0 if none)."""
    if not flash_sale:
        return 0
    if flash_sale.get("product") != product:
        return 0
    try:
        return int(flash_sale.get("discount", 0) or 0)
    except (TypeError, ValueError):
        return 0


# =====================================================
# 🎬 Animation engine
# =====================================================
def loading_frames(lang, label_key="opening", steps=3):
    """Build a short progress-bar animation for the shop screens."""
    label = gt_shop(lang, label_key)
    steps = max(2, min(steps, len(LOADING_BARS)))
    picked = [LOADING_BARS[int(i * (len(LOADING_BARS) - 1) / (steps - 1))] for i in range(steps)]
    frames = [f"🛍️ <b>{label}...</b>\n\n<code>{bar}</code>" for bar in picked[:-1]]
    frames.append(f"✅ <b>{gt_shop(lang, 'ready')}!</b>\n\n<code>{LOADING_BARS[-1]}</code>")
    return frames


def purchase_frames(steps):
    """Animate the purchase pipeline with a percentage bar.

    ``steps`` is the list of already-localised step captions.
    """
    steps = [s for s in (steps or []) if s]
    if not steps:
        return []
    total = len(steps)
    frames = []
    for index, caption in enumerate(steps, start=1):
        filled = max(1, int(round(len(LOADING_BARS[0]) * index / total)))
        bar = "▰" * filled + "▱" * (len(LOADING_BARS[0]) - filled)
        percent = int(round(index * 100 / total))
        frames.append(f"{caption}\n\n<code>{bar}</code> {percent}%")
    return frames


def animate_frames(bot, chat_id, msg_id, frames, delay=0.22, parse_mode="HTML"):
    """Play frames on an existing message.

    Never raises: a failed edit (flood limit, identical text, deleted message)
    must never block the shop flow or a delivery.
    """
    if not frames or msg_id is None:
        return False
    played = False
    for frame in frames:
        try:
            bot.edit_message_text(frame, chat_id, msg_id, parse_mode=parse_mode)
            played = True
        except Exception:
            pass
        if delay:
            time.sleep(delay)
    return played


# =====================================================
# 🖼️ Screen builders
# =====================================================
def _line(label, value):
    return f"│ {label}: <b>{value}</b>\n"


def build_shop_view(lang, user, prices_config, keys_store, bot_config,
                    flash_sale=None, flash_remaining=None):
    """Catalogue screen → (text, markup)."""
    user = user or {}
    prices_config = prices_config or {}
    keys_store = keys_store or {}
    bot_config = bot_config or {}

    points = user.get("points", 0) or 0
    rank = user.get("rank") or "🔹"
    rank_discount = user.get("rank_discount", 0.0) or 0.0
    global_discount = bot_config.get("discount", 0) or 0

    markup = types.InlineKeyboardMarkup(row_width=1)

    if not prices_config:
        text = (
            f"{gt_shop(lang, 'title')}\n"
            f"{gt_shop(lang, 'subtitle')}\n\n"
            f"{gt_shop(lang, 'empty')}\n\n"
            f"{gt_shop(lang, 'empty_hint')}"
        )
        markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_refresh"), callback_data="shop_refresh"))
        markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_home"), callback_data="shop_home"))
        return text, markup

    cheapest = None
    for product, plans in prices_config.items():
        flash = flash_discount_for(flash_sale, product)
        for plan in PLANS:
            price = compute_price((plans or {}).get(plan, 0), global_discount, flash, rank_discount)
            if price > 0 and (cheapest is None or price < cheapest):
                cheapest = price

    header = f"{gt_shop(lang, 'title')}\n{gt_shop(lang, 'subtitle')}\n\n"
    header += "┌────────────────────────────\n"
    header += _line(gt_shop(lang, "wallet"), f"{points} 💎")
    header += f"│ {gt_shop(lang, 'rank_disc')}: {rank} (-{int(rank_discount * 100)}%)\n"
    header += _line(gt_shop(lang, "products_count"), len(prices_config))
    if cheapest is not None:
        header += _line(gt_shop(lang, "starts_from"), f"{cheapest} 💎")
    if global_discount:
        header += _line(gt_shop(lang, "total_disc"), f"{global_discount}%")

    if flash_sale:
        header += "├────────────────────────────\n"
        header += f"│ {gt_shop(lang, 'flash')}\n"
        header += (f"│ 🔥 {flash_sale.get('discount', 0)}% {gt_shop(lang, 'off')} ➝ "
                   f"<b>{flash_sale.get('product', '')}</b>\n")
        if flash_remaining:
            header += _line(gt_shop(lang, "flash_ends"), flash_remaining)
    header += "└────────────────────────────\n\n"
    header += gt_shop(lang, "select_prod")

    for product in prices_config.keys():
        stock = product_stock(keys_store, product)
        status = gt_shop(lang, "available") if stock > 0 else gt_shop(lang, "out")
        if flash_discount_for(flash_sale, product):
            emoji = "🔥"
        elif stock > 0:
            emoji = "✅"
        else:
            emoji = "⚠️"
        label = f"{emoji} {product} | {status}: {stock}"
        markup.add(types.InlineKeyboardButton(
            label, callback_data=f"select_prod_{product_id(product)}"))

    markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_refresh"), callback_data="shop_refresh"))
    markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_home"), callback_data="shop_home"))
    return header, markup


def build_product_view(lang, user, product, prices_config, keys_store, bot_config,
                       flash_sale=None, flash_remaining=None):
    """Product screen → (text, markup)."""
    user = user or {}
    prices_config = prices_config or {}
    keys_store = keys_store or {}
    bot_config = bot_config or {}

    rank_discount = user.get("rank_discount", 0.0) or 0.0
    global_discount = bot_config.get("discount", 0) or 0
    flash = flash_discount_for(flash_sale, product)
    total_percent = min(95, global_discount + flash)

    info = f"{gt_shop(lang, 'prod_info')}\n\n"
    info += "┌────────────────────────────\n"
    info += f"│ {gt_shop(lang, 'prod_name')} <b>{product}</b>\n"
    info += _line(gt_shop(lang, "rank_disc"), f"{int(rank_discount * 100)}%")
    info += _line(gt_shop(lang, "balance"), f"{user.get('points', 0) or 0} 💎")
    if total_percent:
        info += _line(gt_shop(lang, "total_disc"), f"{total_percent}%")
    if flash:
        info += f"│ {gt_shop(lang, 'flash')} 🔥 {flash}% {gt_shop(lang, 'off')}!\n"
        if flash_remaining:
            info += _line(gt_shop(lang, "flash_ends"), flash_remaining)
    info += "└────────────────────────────\n\n"
    info += f"{gt_shop(lang, 'prod_desc_text')}\n\n"

    markup = types.InlineKeyboardMarkup(row_width=1)
    plans = prices_config.get(product) or {}
    total_stock = 0

    for plan in PLANS:
        base = plans.get(plan, 0)
        price = compute_price(base, global_discount, flash, rank_discount)
        stock = plan_stock(keys_store, product, plan)
        total_stock += stock
        emoji = "✅" if stock > 0 else "❌"
        label = (f"{emoji} {gt_shop(lang, PLAN_KEYS[plan])} | "
                 f"{gt_shop(lang, 'price')} {price} 💎 | {gt_shop(lang, 'stock')} {stock}")
        if flash and stock > 0:
            label = f"⚡ {label}"
        markup.add(types.InlineKeyboardButton(
            label, callback_data=f"buy_plan|{product}|{plan}"))

    info += gt_shop(lang, "duration") if total_stock else gt_shop(lang, "soldout_hint")

    markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_back"), callback_data="menu_shop_back"))
    return info, markup


def build_success_view(lang, product, plan, price, key, base_price=None):
    """Delivery receipt → (text, markup)."""
    plan_label = gt_shop(lang, PLAN_KEYS.get(plan, plan))
    text = f"{gt_shop(lang, 'purchase_done')}\n\n"
    text += "┌────────────────────────────\n"
    text += _line(gt_shop(lang, "product"), product)
    text += _line(gt_shop(lang, "plan"), plan_label)
    text += _line(gt_shop(lang, "paid"), f"{price} 💎")
    try:
        if base_price and int(base_price) > int(price):
            text += _line(gt_shop(lang, "you_save"), f"{int(base_price) - int(price)} 💎")
    except (TypeError, ValueError):
        pass
    text += "└────────────────────────────\n\n"
    text += f"{gt_shop(lang, 'your_key')}\n<code>{key}</code>\n\n"
    text += f"{gt_shop(lang, 'delivered')}\n{gt_shop(lang, 'save_key')}"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_back"), callback_data="menu_shop_back"))
    markup.add(types.InlineKeyboardButton(gt_shop(lang, "btn_home"), callback_data="shop_home"))
    return text, markup
