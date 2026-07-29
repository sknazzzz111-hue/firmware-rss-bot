import os
import time
import feedparser
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
RSS_URL = os.environ.get("RSS_URL")

POSTED_FILE = "posted_urls.txt"

def get_posted_urls():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_posted_url(url):
    with open(POSTED_FILE, "a") as f:
        f.write(url + "\n")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
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
    
    for entry in reversed(feed.entries):
        link = entry.get("link", "")
        title = entry.get("title", "")
        
        if link and link not in posted:
            message = (
                "```\n"
                f"NEW FILE RELEASED\n\n"
                f"Title: {title}\n"
                f"Link: {link}\n"
                "```"
            )
            
            if send_telegram_message(message):
                print(f"Posted: {title}")
                save_posted_url(link)
                time.sleep(3)

if __name__ == "__main__":
    print("RSS Auto-Poster Bot Started...")
    while True:
        try:
            check_rss()
        except Exception as e:
            print(f"Error in loop: {e}")
        time.sleep(300)
