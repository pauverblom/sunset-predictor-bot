import requests
import os
from datetime import datetime

# Only needed locally
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load variables from .env if it exists
except ImportError:
    pass  # dotenv not needed on GitHub Actions

# === CONFIG ===
SUNSETHUE_API_KEY = os.getenv("SUNSETHUE_API_KEY")
LAT = 63.4305
LON = 10.3950 # Trondheim, Norway

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def check_sunset():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://api.sunsethue.com/event?latitude={LAT}&longitude={LON}&date={today}&type=sunset"
    headers = {"x-api-key": SUNSETHUE_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"Sunset API response: {response.status_code} {response.text}")
    data = response.json()
    sunset_info = data.get("data", {})
    if not sunset_info.get("model_data", False):
        return None, None  # No valid model

    quality_text = sunset_info.get("quality_text", "Unknown")
    return quality_text, sunset_info


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def main():
    try:
        quality_text, sunset_info = check_sunset()

        if quality_text is None:
            send_telegram_message("⚠️ No sunset prediction available for today at this location.")
            return
        
        if quality_text.lower() in ["good", "great", "fair"]:
            sunset_time_raw = sunset_info.get("time", "Unknown")
            if sunset_time_raw != "Unknown":
                sunset_time = datetime.fromisoformat(sunset_time_raw.replace('Z', '+00:00')).strftime("%H:%M")
            else:
                sunset_time = "Unknown"
            cloud_cover = sunset_info.get("cloud_cover", None)
            cloud_cover_str = f"{cloud_cover:.0%}" if cloud_cover is not None else "N/A"
            quality_percentage = sunset_info.get("quality", "N/A")
            msg = (
                f"🌇 Sunset quality is *{quality_text.  upper()}* today, {quality_percentage:.0%}\n"
                f"🕒 Sunset time: `{sunset_time}`\n"
                f"☁️ Cloud cover: {cloud_cover_str}\n"
                f"📍 Location: {LAT}, {LON}"
            )
            send_telegram_message(msg)
    except Exception as e:
        send_telegram_message(f"🚨 Sunset bot error:\n`{str(e)}`")

if __name__ == "__main__":
    main()
