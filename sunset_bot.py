import requests
import os
from datetime import datetime

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

def check_sunset():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://api.sunsethue.com/event?latitude={lat}&longitude={lon}&date={today}&type=sunset"
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
    print(f"Sent message: {message}")

def get_location_name(lat, lon):
    """Get city/region name from coordinates using Nominatim (OpenStreetMap)"""
    print(f"Getting location name for {lat}, {lon}")  # Debug print
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
        headers = {"User-Agent": "SunsetBot/1.0"}  # Required by Nominatim
        print(f"Requesting: {url}")  # Debug print
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Response status: {response.status_code}")  # Debug print
        
        data = response.json()
        print(f"Response data: {data}")  # Debug print
        address = data.get("address", {})
        
        # Try to get city, town, or village
        city = (address.get("city") or 
                address.get("town") or 
                address.get("village") or 
                address.get("municipality"))
        
        country = address.get("country")
        print(f"Found city: {city}, country: {country}")  # Debug print
        
        if city and country:
            return f"{city}, {country}"
        elif city:
            return city
        elif country:
            return country
        else:
            return "Unknown location"
            
    except Exception as e:
        print(f"Error getting location name: {e}")
        return "Unknown location"

def main():
    try:
        quality_text, sunset_info = check_sunset()

        if quality_text is None:
            send_telegram_message("⚠️ No sunset prediction available for today at this location.")
            return
        
        if quality_text.lower() in ["poor","good", "great", "fair"]:
            sunset_time_raw = sunset_info.get("time", "Unknown")
            if sunset_time_raw != "Unknown":
                sunset_time = datetime.fromisoformat(sunset_time_raw.replace('Z', '+00:00')).strftime("%H:%M")
            else:
                sunset_time = "Unknown"
            cloud_cover = sunset_info.get("cloud_cover", None)
            cloud_cover_str = f"{cloud_cover:.0%}" if cloud_cover is not None else "N/A"
            quality_percentage = sunset_info.get("quality", "N/A")
            
            print("About to get location name...")  # Debug print
            location_name = get_location_name(lat, lon)
            print(f"Got location name: {location_name}")  # Debug print
            
            msg = (
                f"🌇 Sunset quality is *{quality_text.upper()}* today, {quality_percentage:.0%}\n"
                f"🕒 Sunset time: `{sunset_time}`\n"
                f"☁️ Cloud cover: {cloud_cover_str}\n"
                f"📍 Location: {location_name} ({lat:.4f}, {lon:.4f})"
            )
            send_telegram_message(msg)
    except Exception as e:
        send_telegram_message(f"🚨 Sunset bot error:\n`{str(e)}`")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
