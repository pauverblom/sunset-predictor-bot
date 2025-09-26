import requests
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder

def format_time(time_str):
    """Format time string from ISO format to HH:MM"""
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00')).strftime("%H:%M")
    except ValueError:
        return "Invalid time"

def get_location_name(lat, lon):
    """Get city/region name from coordinates using Nominatim (OpenStreetMap)"""
    print(f"Getting location name for {lat}, {lon}")  # Debug print
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
        headers = {"User-Agent": "SunsetBot/1.0"}  # Required by Nominatim
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        address = data.get("address", {})
        
        # Try to get city, town, or village
        city = (address.get("city") or 
                address.get("town") or 
                address.get("village") or 
                address.get("municipality"))
        
        country = address.get("country")
        
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

def process_sunset_params(sunset_info, lat, lon):
    
        # Get timezone for the location
    timezone = get_timezone(lat, lon)

    """Process sunset information and return formatted parameters"""
    sunset_time_raw = sunset_info.get("time")
    if sunset_time_raw and sunset_time_raw != "Unknown":
        sunset_time = format_time_with_timezone(sunset_time_raw, timezone)
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
        golden_hour_start = format_time_with_timezone(golden_hour_info[0], timezone)
        golden_hour_end = format_time_with_timezone(golden_hour_info[1], timezone)
    else:
        golden_hour_start = "N/A"
        golden_hour_end = "N/A"

    if (blue_hour_info and len(blue_hour_info) >= 2 and 
        blue_hour_info[0] is not None and blue_hour_info[1] is not None):
        blue_hour_start = format_time_with_timezone(blue_hour_info[0], timezone)
        blue_hour_end = format_time_with_timezone(blue_hour_info[1], timezone)
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

def send_telegram_message(message, bot_token, chat_id):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)
    print(f"Sent message: {message}")
    
def get_timezone(lat, lon):
    """Get timezone for given coordinates"""
    try:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if timezone_str:
            return pytz.timezone(timezone_str)
        else:
            return pytz.UTC
    except Exception:
        return pytz.UTC

def format_time_with_timezone(time_str, timezone):
    """Format time string from ISO format to HH:MM in specified timezone"""
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        dt_tz = dt.astimezone(timezone)
        return dt_tz.strftime("%H:%M")
    except ValueError:
        return "Invalid time"