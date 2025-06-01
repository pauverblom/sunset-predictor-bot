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

def get_sunset_data():
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

def format_time(time_str):
    """Format time string from ISO format to HH:MM"""
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00')).strftime("%H:%M")
    except ValueError:
        return "Invalid time"

def process_sunset_params(sunset_info, lat, lon):
    """Process sunset information and return formatted parameters"""
    sunset_time_raw = sunset_info.get("time")
    if sunset_time_raw and sunset_time_raw != "Unknown":
        sunset_time = format_time(sunset_time_raw)
    else:
        sunset_time = "Unknown"
    
    cloud_cover = sunset_info.get("cloud_cover")
    cloud_cover_str = f"{cloud_cover:.0%}" if cloud_cover is not None else "N/A"
    quality_percentage = sunset_info.get("quality", "N/A")
    direction = sunset_info.get("direction")
    
    if direction is not None:
        # Convert degrees to cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        cardinal = directions[round(direction / 45) % 8]
        direction_str = f"{cardinal} ({direction:.0f}º)"
    else:
        direction_str = "N/A"
    
    magics = sunset_info.get("magics", {})
    golden_hour_info = magics.get("golden_hour", [])
    blue_hour_info = magics.get("blue_hour", [])
    
    if (golden_hour_info and len(golden_hour_info) >= 2 and 
        golden_hour_info[0] is not None and golden_hour_info[1] is not None):
        golden_hour_start = format_time(golden_hour_info[0])
        golden_hour_end = format_time(golden_hour_info[1])
    else:
        golden_hour_start = "N/A"
        golden_hour_end = "N/A"
    
    if (blue_hour_info and len(blue_hour_info) >= 2 and 
        blue_hour_info[0] is not None and blue_hour_info[1] is not None):
        blue_hour_start = format_time(blue_hour_info[0])
        blue_hour_end = format_time(blue_hour_info[1])
    else:
        blue_hour_start = "N/A"
        blue_hour_end = "N/A"
    
    location_name = get_location_name(lat, lon)
    
    return {
        'sunset_time': sunset_time,
        'cloud_cover_str': cloud_cover_str,
        'quality_percentage': quality_percentage,
        'direction_str': direction_str,
        'golden_hour_start': golden_hour_start,
        'golden_hour_end': golden_hour_end,
        'blue_hour_start': blue_hour_start,
        'blue_hour_end': blue_hour_end,
        'location_name': location_name
    }
                
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
        #print(f"Requesting: {url}")  # Debug print
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        #print(f"Response status: {response.status_code}")  # Debug print
        
        data = response.json()
        #print(f"Response data: {data}")  # Debug print
        address = data.get("address", {})
        
        # Try to get city, town, or village
        city = (address.get("city") or 
                address.get("town") or 
                address.get("village") or 
                address.get("municipality"))
        
        country = address.get("country")
        #print(f"Found city: {city}, country: {country}")  # Debug print
        
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
        sunset_info = get_sunset_data()
        
        if sunset_info is None:
            send_telegram_message("⚠️ No sunset prediction available for today at this location.")
            return
        
        quality_text = sunset_info.get("quality_text")
        if not quality_text or quality_text == "Unknown":
            send_telegram_message("⚠️ No sunset quality data available for today at this location.")
            return
        
        if quality_text.lower() in ["poor","fair", "good", "great", "excellent"]: #Any quality is reported, but can be changed to set a threshold
            
            sunset_params = process_sunset_params(sunset_info, lat, lon)
            
            sunset_time = sunset_params['sunset_time']
            cloud_cover_str = sunset_params['cloud_cover_str']
            quality_percentage = sunset_params['quality_percentage']
            direction_str = sunset_params['direction_str']
            location_name = sunset_params['location_name']
            #print(f"Got location name: {location_name}")  # Debug print
            #TODO GENERATE AN AI SUMMARY (BRIEF PHRASE) OF THE SUNSET QUALITY, ADD TEMPERATURE AND HUMIDITY INFO
            # Only include Blue Hour line if we have valid data
            blue_hour_line = ""
            golden_hour_line = ""
            
            if sunset_params['blue_hour_start'] != 'N/A' and sunset_params['blue_hour_end'] != 'N/A':
                blue_hour_line = f"🌌 Blue Hour: `{sunset_params['blue_hour_start']}` to `{sunset_params['blue_hour_end']}`"
            else:
                blue_hour_line = "🌌 Blue Hour: No Info"
                
            if sunset_params['golden_hour_start'] != 'N/A' and sunset_params['golden_hour_start'] != 'N/A':
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
            #send_telegram_message(msg)
            print(f"Message to send: {msg}")
    except Exception as e:
        send_telegram_message(f"🚨 Sunset bot error:\n`{str(e)}`")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
