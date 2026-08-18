import os
import asyncio
import feedparser
import edge_tts
from groq import Groq

# دریافت کلید از گیت‌هاب
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

RSS_URL = "https://cointelegraph.com/rss"
VOICE = "fa-IR-FaridNeural"
OUTPUT_AUDIO = "voice.mp3"

def get_script():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("❌ خبری پیدا نشد.")
        return None
    
    entry = feed.entries[0]
    title = entry.title
    summary = entry.summary if 'summary' in entry else title
    
    prompt = f"""
تو یک گوینده حرفه‌ای اخبار کریپتو هستی.
خبر زیر را به یک سناریوی جذاب ۳۰ ثانیه‌ای به زبان فارسی روان تبدیل کن.
حتماً در ۳ ثانیه اول یک قلاب (Hook) جذاب داشته باشد.
فقط و فقط متن فارسی گوینده را خروجی بده و هیچ توضیح اضافه‌ای ننویس.

تیتر: {title}
خلاصه: {summary}
"""
    
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    
    script = completion.choices[0].message.content.strip()
    print("📝 متن سناریو ساخته شد:\n", script)
    return script

async def make_audio(text):
    print("\n🎙️ در حال تبدیل متن به صدا...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_AUDIO)
    print(f"✅ فایل صوتی ساخته شد: {OUTPUT_AUDIO}")

if __name__ == "__main__":
    script_text = get_script()
    if script_text:
        asyncio.run(make_audio(script_text))
