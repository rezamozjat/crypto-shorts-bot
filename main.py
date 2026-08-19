import os
import asyncio
import feedparser
import edge_tts
import requests
from groq import Groq
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# دریافت کلیدها از تنظیمات گیت‌هاب
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

RSS_URL = "https://cointelegraph.com/rss"
VOICE = "fa-IR-FaridNeural"
OUTPUT_AUDIO = "voice.mp3"
FINAL_OUTPUT = "output.mp4"

def cleanup_old_files():
    """پاک کردن خروجی‌های قبلی برای اطمینان از ساخت ویدیو جدید"""
    for f in [OUTPUT_AUDIO, FINAL_OUTPUT]:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"🗑️ فایل قدیمی پاک شد: {f}")
            except Exception as e:
                print(f"⚠️ نتوانست فایل {f} را پاک کند: {e}")

def get_script():
    """دریافت خبر و ساخت سناریوی ۳۰ تا ۴۵ ثانیه‌ای توسط Groq"""
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("❌ خبری پیدا نشد.")
        return None
    
    entry = feed.entries[0]
    title = entry.title
    summary = entry.summary if 'summary' in entry else title
    
    prompt = f"""
تو یک گوینده حرفه‌ای اخبار کریپتو هستی.
خبر زیر را به یک سناریوی جذاب و سریع ۳۰ الی ۴۰ ثانیه‌ای به زبان فارسی روان تبدیل کن.
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
    """تبدیل متن به فایل صوتی گوینده"""
    print("\n🎙️ در حال تبدیل متن به صدا...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_AUDIO)
    print(f"✅ فایل صوتی ساخته شد: {OUTPUT_AUDIO}")

def fetch_and_build_video(target_duration):
    """دانلود چندین ویدیوی کوتاه از Pexels و چسباندن آن‌ها به اندازه طول صدا"""
    print(f"\n🎬 در حال دریافت ویدیوها تا رسیدن به زمان: {target_duration:.1f} ثانیه...")
    headers = {"Authorization": PEXELS_API_KEY}
    url = "https://api.pexels.com/videos/search?query=blockchain&orientation=portrait&per_page=30"
    
    response = requests.get(url, headers=headers)
    clips = []
    temp_files = []
    current_duration = 0.0

    if response.status_code == 200:
        videos = response.json().get('videos', [])
        if not videos:
            print("❌ هیچ ویدیویی یافت نشد.")
            return None, [], []

        idx = 0
        # دانلود ویدیوها تا زمانی که مجموع زمان آن‌ها از زمان صدا بیشتر شود
        while current_duration < target_duration:
            vid = videos[idx % len(videos)]
            video_url = vid['video_files'][0]['link']
            file_name = f"temp_bg_{len(temp_files)}.mp4"
            
            video_data = requests.get(video_url).content
            with open(file_name, "wb") as f:
                f.write(video_data)
            
            temp_files.append(file_name)
            clip = VideoFileClip(file_name)
            clips.append(clip)
            current_duration += clip.duration
            idx += 1

        # چسباندن تمام کلیپ‌های دانلود شده به هم
        full_bg = concatenate_videoclips(clips, method="compose")
        # قیچی کردن دقیقاً به اندازه طول فایل صوتی
        final_bg = full_bg.subclip(0, target_duration)
        return final_bg, clips, temp_files
    else:
        print(f"❌ خطا در دانلود ویدیو از Pexels (کد خطا: {response.status_code})")
        return None, [], []

def render_final_video():
    """ترکیب ویدیوی پس‌زمینه و فایل صوتی گوینده"""
    print("\n🎞️ در حال ترکیب صدا و ویدیو (رندر نهایی)...")
    audio_clip = AudioFileClip(OUTPUT_AUDIO)
    
    bg_video, clips_list, temp_files = fetch_and_build_video(audio_clip.duration)
    
    if bg_video:
        final_clip = bg_video.set_audio(audio_clip)
        final_clip.write_videofile(FINAL_OUTPUT, codec="libx264", audio_codec="aac", fps=24)
        print(f"🎉 ویدیوی نهایی ساخته شد: {FINAL_OUTPUT}")
        
        # بستن کلیپ‌ها جهت آزادسازی حافظه
        audio_clip.close()
        bg_video.close()
        final_clip.close()
        for c in clips_list:
            c.close()
            
        # پاک‌سازی فایل‌های ویدیویی موقت
        for tf in temp_files:
            if os.path.exists(tf):
                os.remove(tf)

if __name__ == "__main__":
    cleanup_old_files()
    script_text = get_script()
    if script_text:
        asyncio.run(make_audio(script_text))
        render_final_video()
