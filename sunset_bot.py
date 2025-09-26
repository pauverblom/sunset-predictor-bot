import requests
import os
from datetime import datetime
from utils import process_sunset_params, send_telegram_message

# Only needed locally
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load variables from .env if it exists
except ImportError:
    pass  # dotenv not needed on GitHub Actions

GIST_ID = os.getenv("GIST_ID")
USERNAME = "pauverblom"

url = f"https://gist.githubusercontent.com/{USERNAME}/{GIST_ID}/raw/location.txt"
response = requests.get(url)

if response.ok:
    lat_str, lon_str = response.text.strip().split(",")
    lat = float(lat_str)
    lon = float(lon_str)
    print(f"Location: {lat}, {lon}")
else:
    print("Failed to fetch location:", response.status_code)
    
# === CONFIG ===
SUNSETHUE_API_KEY = os.getenv("SUNSETHUE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_sunset_data():
    """Fetch sunset data from SunsetHue API"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://api.sunsethue.com/event?latitude={lat}&longitude={lon}&date={today}&type=sunset"
    headers = {"x-api-key": SUNSETHUE_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"Sunset API response: {response.status_code} {response.text}")
    data = response.json()
    sunset_info = data.get("data", {})
    
    if not sunset_info.get("model_data", False):
        return None  # No valid model

    return sunset_info

def main():
    try:
        sunset_info = get_sunset_data()
        
        if sunset_info is None:
            send_telegram_message("⚠️ No sunset prediction available for today at this location.", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            return
        
        quality_text = sunset_info.get("quality_text")
        if not quality_text or quality_text == "Unknown":
            send_telegram_message("⚠️ No sunset quality data available for today at this location.", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            return
        
        if quality_text.lower() in ["poor","fair", "good", "great", "excellent"]: # Any quality is reported, but can be changed to set a threshold
            
            sunset_params = process_sunset_params(sunset_info, lat, lon)
            
            sunset_time = sunset_params['sunset_time']
            cloud_cover_str = sunset_params['cloud_cover_str']
            quality_percentage = sunset_params['quality_percentage']
            direction_str = sunset_params['direction_str']
            location_name = sunset_params['location_name']
            
            # Only include Blue Hour line if we have valid data
            blue_hour_line = ""
            golden_hour_line = ""
            
            if sunset_params['blue_hour_start'] != 'N/A' and sunset_params['blue_hour_end'] != 'N/A':
                blue_hour_line = f"🌌 Blue Hour: `{sunset_params['blue_hour_start']}` to `{sunset_params['blue_hour_end']}`"
            else:
                blue_hour_line = "🌌 Blue Hour: No Info"
                
            if sunset_params['golden_hour_start'] != 'N/A' and sunset_params['golden_hour_end'] != 'N/A':
                golden_hour_line = f"🌅 Golden Hour: `{sunset_params['golden_hour_start']}` to `{sunset_params['golden_hour_end']}`"
            else:
                golden_hour_line = "🌅 Golden Hour: No Info"
            
            msg = (
                f"🌇 Sunset quality is *{quality_text.upper()}* today, {quality_percentage:.0%}\n"
                f"🕒 Sunset time: `{sunset_time}`\n"
                f"☁️ Cloud cover: {cloud_cover_str}\n"
                f"📍 Location: {location_name} ({lat:.4f}, {lon:.4f})\n"
                f"🧭 Direction: {direction_str}\n"
                f"{golden_hour_line}\n"
                f"{blue_hour_line}"
            )
            send_telegram_message(msg, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            print(f"Message to send: {msg}")
    except Exception as e:
        send_telegram_message(f"🚨 Sunset bot error:\n`{str(e)}`", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()