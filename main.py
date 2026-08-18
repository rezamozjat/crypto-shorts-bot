import os
import asyncio
import feedparser
import edge_tts
import requests
from groq import Groq
from moviepy.editor import VideoFileClip, AudioFileClip

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

RSS_URL = "https://cointelegraph.com/rss"
VOICE = "fa-IR-FaridNeural"
OUTPUT_AUDIO = "voice.mp3"
OUTPUT_BG_VIDEO = "bg_video.mp4"
FINAL_OUTPUT = "output.mp4"

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

def download_background_video(query="cryptocurrency"):
    print(f"\n🎬 در حال دریافت ویدیو پس‌زمینه...")
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=1"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['videos']:
            video_files = data['videos'][0]['video_files']
            download_url = video_files[0]['link']
            
            video_data = requests.get(download_url).content
            with open(OUTPUT_BG_VIDEO, "wb") as f:
                f.write(video_data)
            print(f"✅ ویدیوی پس‌زمینه ذخیره شد: {OUTPUT_BG_VIDEO}")
        else:
            print("❌ ویدیویی یافت نشد.")
    else:
        print(f"❌ خطا در اتصال به Pexels: {response.status_code}")

def render_final_video():
    print("\n🎞️ در حال ترکیب صدا و ویدیو (رندر نهایی)...")
    audio_clip = AudioFileClip(OUTPUT_AUDIO)
    video_clip = VideoFileClip(OUTPUT_BG_VIDEO)

    # اگر ویدیو کوتاه‌تر از صدا بود، اونو تکرار می‌کنه
    if video_clip.duration < audio_clip.duration:
        video_clip = video_clip.loop(duration=audio_clip.duration)
    else:
        video_clip = video_clip.subclip(0, audio_clip.duration)

    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(FINAL_OUTPUT, codec="libx264", audio_codec="aac", fps=24)
    print(f"🎉 ویدیوی نهایی ساخته شد: {FINAL_OUTPUT}")

if __name__ == "__main__":
    script_text = get_script()
    if script_text:
        asyncio.run(make_audio(script_text))
        download_background_video("cryptocurrency")
        render_final_video()
