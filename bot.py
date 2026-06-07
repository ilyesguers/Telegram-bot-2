import telebot
from telebot import types

# وضع التوكن الخاص بك مباشرة
API_TOKEN = "8868383649:AAEVxFynrH7u_M8e9-wjxo6h8-NP8dtWNUQ"
bot = telebot.TeleBot(API_TOKEN)

# 1️⃣ قائمة اختيار اللغات (أزرار إنلاين تظهر أولاً)
def get_language_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    btn_ar = types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")
    btn_en = types.InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")
    keyboard.add(btn_ar, btn_en)
    return keyboard

# 2️⃣ كيبورد أسفل الشاشة تظهر فوراً بعد اختيار اللغة (تحتوي على خانة واحدة فقط)
def get_main_keyboard(lang):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ar":
        btn_id = types.KeyboardButton("عرض الآيدي الخاص بي 🆔")
    else:
        btn_id = types.KeyboardButton("show my id 🆔")
    keyboard.add(btn_id)
    return keyboard

# عندما يرسل المستخدم أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "🌐 Please select your language / يرجى تحديد لغتك:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_language_keyboard())

# معالج الضغط على أزرار اللغة
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_choice(call):
    # معرفة اللغة المختارة
    selected_lang = call.data.split("_")[1]
    
    # حذف رسالة اختيار اللغة لتنظيف المحادثة
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    # تخصيص نص الترحيب بناءً على اللغة وتفعيل الكيبورد السفلية مباشرة
    if selected_lang == "ar":
        reply_text = "✅ تم اختيار اللغة العربية بنجاح!\n\nيمكنك الآن الضغط على الزر بالأسفل لمعرفة الآيدي الخاص بك."
    else:
        reply_text = "✅ Language set to English successfully!\n\nYou can now press the button below to see your ID."

    # إرسال الرسالة وظهور الكيبورد السفلية فوراً
    bot.send_message(call.message.chat.id, reply_text, reply_markup=get_main_keyboard(selected_lang))

# معالج الضغط على زر "show my id" أو "عرض الآيدي" في الكيبورد السفلية
@bot.message_handler(func=lambda message: message.text in ["show my id 🆔", "عرض الآيدي الخاص بي 🆔"])
def show_user_id(message):
    user_id = message.from_user.id
    response_text = f"👤 Your Telegram ID is: <code>{user_id}</code>"
    bot.reply_to(message, response_text, parse_mode="HTML")

# تشغيل البوت بشكل مستمر
if __name__ == "__main__":
    print("🤖 البوت يعمل الآن من نقطة الصفر بنجاح...")
    bot.infinity_polling()
