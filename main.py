import os
import time
import re
from datetime import datetime
import pytz
import feedparser
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
RSS_URL = os.environ.get("RSS_URL")

POSTED_FILE = "posted_urls.txt"

# ব্র্যান্ড চিহ্নিত করার তালিকা
BRANDS = [
    "VIVO", "OPPO", "REALME", "XIAOMI", "REDMI", "POCO", 
    "SAMSUNG", "ONEPLUS", "TECNO", "INFINIX", "ITEL", "MOTOROLA", "NOKIA"
]

def get_posted_urls():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_posted_urls(urls):
    with open(POSTED_FILE, "a") as f:
        for url in urls:
            f.write(url + "\n")

def clean_url(url):
    # Google Search Prefix মুছে ফেলা
    prefix = "https://www.google.com/search?q="
    if url.startswith(prefix):
        url = url[len(prefix):]
    return url.strip()

def detect_brand(title):
    title_upper = title.upper()
    for brand in BRANDS:
        if re.search(r'\b' + brand + r'\b', title_upper):
            return brand
    return "OTHER"

def send_telegram_message(html_text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def check_rss():
    posted = get_posted_urls()
    feed = feedparser.parse(RSS_URL)
    
    new_entries = []
    for entry in feed.entries:
        raw_link = entry.get("link", "")
        link = clean_url(raw_link)
        if link and link not in posted:
            new_entries.append((entry.get("title", "").strip(), link))
            
    if not new_entries:
        return

    # ব্র্যান্ড অনুযায়ী ফাইল আলাদা করা
    grouped_files = {}
    new_posted_urls = []

    for title, link in reversed(new_entries):
        brand = detect_brand(title)
        if brand not in grouped_files:
            grouped_files[brand] = []
        grouped_files[brand].append((title, link))
        new_posted_urls.append(link)

    # বর্তমান তারিখ ও সময় (Asia/Dhaka)
    bd_tz = pytz.timezone("Asia/Dhaka")
    now = datetime.now(bd_tz)
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")

    # টেলিগ্রাম Quote ফরম্যাটের জন্য blockquote ব্যবহার
    message_lines = ["<blockquote>"] # Quote ব্লক শুরু
    message_lines.append(f"📅 Today's Update: {date_str} | ⏰ {time_str}")
    message_lines.append("🌐 Official Website: https://firmwareworld.com/\n")

    for brand, files in grouped_files.items():
        message_lines.append(f"--- 📱 {brand} FIRMWARE ---\n")
        for title, link in files:
            message_lines.append(f"🔥 File Name:")
            message_lines.append(f"{title}")
            message_lines.append(f"🔗 File Link: {link}\n")

    message_lines.append("</blockquote>") # Quote ব্লক শেষ

    full_message = "\n".join(message_lines)

    if send_telegram_message(full_message):
        print("Successfully posted update using Quote format.")
        save_posted_urls(new_posted_urls)

if __name__ == "__main__":
    print("RSS Auto-Poster Bot Started...")
    while True:
        try:
            check_rss()
        except Exception as e:
            print(f"Error in loop: {e}")
        time.sleep(300) # প্রতি ৫ মিনিট পর পর RSS চেক করবে
