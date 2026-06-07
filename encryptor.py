import base64
import zlib
import os

def protect_code():
    input_file = "bot.py"         # اسم ملفك الأصلي
    output_file = "bot_protected.py" # اسم الملف المحمي الذي سيتم إنشاؤه
    
    if not os.path.exists(input_file):
        print("❌ لم يتم العثور على ملف bot.py")
        return

    print("⏳ جاري ضغط وتشفير الكود...")
    with open(input_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    # 1. ضغط الكود لتقليل حجمه وصعوبة قراءته
    compressed_code = zlib.compress(source_code.encode('utf-8'))
    # 2. تشفير الكود باستخدام Base64
    encoded_code = base64.b64encode(compressed_code)

    # 3. كتابة الكود المحمي الذي يفك تشفير نفسه عند التشغيل
    protected_content = f"""# ملف محمي ومشفّر 🔒
import base64, zlib
try:
    exec(zlib.decompress(base64.b64decode({encoded_code})).decode('utf-8'))
except Exception as e:
    print("❌ حدث خطأ في تشغيل الكود المحمي:", str(e))
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(protected_content)

    print(f"✅ تم التشفير بنجاح! يمكنك الآن تشغيل أو رفع الملف: {output_file}")

if __name__ == "__main__":
    protect_code()
