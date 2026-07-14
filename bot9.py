"""
=====================================================
 bot9.py — إصلاح مشكلة الدفع بالنجوم (Stars Payment Fix)
=====================================================
هذا الملف يصلح مشكلة تعليق زر الدفع عند الضغط عليه.

المشكلة: bot.infinity_polling() لا يستقبل pre_checkout_query افتراضياً
الحل: نغلّف الدالة لتشمل pre_checkout_query في allowed_updates

📌 طريقة التركيب:
   في bot.py، أضف هذا السطر بعد imports مباشرة:
   
        import bot9

=====================================================
"""

from config import bot, ADMIN_PRIMARY
from database import bot_config, save_json, DB_CONFIG, get_user, update_user_data, update_user_rank_and_quests
from datetime import datetime, timedelta

# =====================================================
# 🔧 إصلاح allowed_updates لاستقبال pre_checkout_query
# =====================================================
_original_infinity_polling = bot.infinity_polling

def _patched_infinity_polling(*args, **kwargs):
    """
    نضيف pre_checkout_query و successful_payment إلى allowed_updates
    بدون هذا، تليجرام لا ترسل هذه التحديثات للبوت أصلاً!
    """
    kwargs.setdefault("allowed_updates", [
        "message",
        "edited_message", 
        "callback_query",
        "pre_checkout_query",      # ← مهم جداً للدفع!
        "shipping_query",          # ← للشحن (اختياري)
        "message_reaction",
        "message_reaction_count",
        "chat_member"
    ])
    print("✅ bot9: allowed_updates patched - pre_checkout_query enabled!")
    return _original_infinity_polling(*args, **kwargs)

bot.infinity_polling = _patched_infinity_polling

# نفس الشيء لـ polling العادي
_original_polling = bot.polling

def _patched_polling(*args, **kwargs):
    kwargs.setdefault("allowed_updates", [
        "message",
        "edited_message",
        "callback_query", 
        "pre_checkout_query",
        "shipping_query",
        "message_reaction",
        "message_reaction_count",
        "chat_member"
    ])
    return _original_polling(*args, **kwargs)

bot.polling = _patched_polling


# =====================================================
# ✅ PRE-CHECKOUT HANDLER (احتياطي إضافي)
# =====================================================
# في حال لم يكن موجوداً في bot2.py
# =====================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def bot9_handle_pre_checkout(pre_checkout_query):
    """
    معالج التحقق المسبق من الدفع
    يُستدعى عندما يضغط المستخدم على زر "تأكيد ودفع"
    """
    try:
        uid = str(pre_checkout_query.from_user.id)
        payload = pre_checkout_query.invoice_payload
        
        print(f"🔔 bot9: Pre-checkout received from {uid}")
        print(f"📦 bot9: Payload = {payload}")
        
        # قبول كل الدفعات الصالحة
        valid_prefixes = ["vip_purchase_", "stars_convert_"]
        is_valid = any(payload.startswith(prefix) for prefix in valid_prefixes)
        
        if is_valid:
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=True
            )
            print(f"✅ bot9: Pre-checkout APPROVED for {uid}")
        else:
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="❌ طلب غير صالح"
            )
            print(f"❌ bot9: Pre-checkout REJECTED - invalid payload")
            
    except Exception as e:
        print(f"⚠️ bot9: Pre-checkout error: {e}")
        # في حالة خطأ، نوافق لتجنب تعليق المستخدم
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            print(f"✅ bot9: Pre-checkout approved (fallback)")
        except:
            pass


# =====================================================
# ✅ SUCCESSFUL PAYMENT HANDLER (احتياطي)  
# =====================================================
def activate_vip_bot9(uid, days=30):
    """تفعيل VIP للمستخدم"""
    uid = str(uid)
    expires = datetime.now() + timedelta(days=days)
    if "vip_subscribers" not in bot_config:
        bot_config["vip_subscribers"] = {}
    bot_config["vip_subscribers"][uid] = {
        "activated": datetime.now().isoformat(),
        "expires": expires.isoformat(),
        "days": days
    }
    save_json(DB_CONFIG, bot_config)
    return expires


@bot.message_handler(content_types=['successful_payment'])
def bot9_handle_successful_payment(message):
    """
    معالج الدفع الناجح
    يُستدعى بعد إتمام عملية الدفع بنجاح
    """
    try:
        uid = str(message.from_user.id)
        payment = message.successful_payment
        payload = payment.invoice_payload
        total_amount = payment.total_amount
        
        print(f"💰 bot9: Successful payment from {uid}")
        print(f"📦 bot9: Payload = {payload}, Amount = {total_amount}")
        
        if payload.startswith("vip_purchase_"):
            # تفعيل VIP
            expires = activate_vip_bot9(uid, 30)
            
            bot.send_message(message.chat.id,
                f"╔═══════════════════════╗\n"
                f"║ 🎊 VIP ACTIVATED! 🎊 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"👑 Welcome to VIP! \n\n"
                f"⏰ Valid until: {expires.strftime('%Y-%m-%d')}\n"
                f"💎 All benefits activated\n\n"
                f"✨ Enjoy! ", parse_mode="HTML")
            
            print(f"✅ bot9: VIP activated for {uid}")
            
            # إشعار الأدمن
            try:
                u = get_user(uid) or {}
                bot.send_message(ADMIN_PRIMARY,
                    f"💰 NEW VIP! \n\n"
                    f"👤 @{u.get('username', 'N/A')}\n"
                    f"🆔 {uid}\n"
                    f"⭐ Paid: {total_amount} stars", parse_mode="HTML")
            except:
                pass
                
        elif payload.startswith("stars_convert_"):
            # تحويل نجوم إلى نقاط
            parts = payload.split("_")
            stars = int(parts[2])
            points = int(parts[3])
            
            update_user_data(uid, points=points, accumulated_points=points)
            update_user_rank_and_quests(uid)
            
            u_new = get_user(uid) or {}
            bot.send_message(message.chat.id,
                f"╔═══════════════════════╗\n"
                f"║ 🎉 DONE! 🎉 ║\n"
                f"╚═══════════════════════╝\n\n"
                f"⭐ Stars: {stars} \n"
                f"💎 Points: +{points} \n"
                f"💰 Balance: {u_new.get('points', 0)} ", parse_mode="HTML")
            
            print(f"✅ bot9: Converted {stars} stars to {points} points for {uid}")
            
            # إشعار الأدمن
            try:
                u = get_user(uid) or {}
                bot.send_message(ADMIN_PRIMARY,
                    f"⭐ CONVERSION \n"
                    f"@{u.get('username', 'N/A')}\n"
                    f"{uid}\n"
                    f"⭐ {stars} → 💎 {points}", parse_mode="HTML")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ bot9: Successful payment error: {e}")


# =====================================================
# 🚀 تأكيد التحميل
# =====================================================
print("=" * 55)
print("✅ bot9.py — Stars Payment Fix loaded!")
print("💳 Pre-checkout handler: Active")
print("💰 Successful payment handler: Active")
print("🔧 allowed_updates: Patched")
print("=" * 55)
