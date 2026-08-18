import asyncio
import edge_tts

# متنی که قرار است به صدا تبدیل شود
TEXT = "سلام! به خبرهای داغ کریپتو خوش آمدید. قیمت بیت‌کوین امروز رکورد جدیدی زد."

# صدای فارسی مایکروسافت (مرد: fa-IR-FaridNeural | زن: fa-IR-DilaraNeural)
VOICE = "fa-IR-FaridNeural"
OUTPUT_FILE = "voice.mp3"

async def generate_audio():
    print("🎙️ در حال تبدیل متن به صدا...")
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)
    print(f"✅ فایل صوتی با موفقیت ساخته شد: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_audio())
