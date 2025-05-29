import requests
import os

# === CONFIG ===
SUNSETHUE_API_KEY = os.environ.get("SUNSETHUE_API_KEY")
LAT = 63.4305
LON = 10.3950 # Trondheim, Norway

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def check_sunset():
    url = f"https://api.sunsethue.com/v1/forecast?lat={LAT}&lng={LON}"
    headers = f"x-api-key: {SUNSETHUE_API_KEY}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return "yes"  # e.g., "poor", "fair", "good", "great"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def main():
    log_message = "Sunset bot started"
    try:
        quality = check_sunset()
        print(f"Sunset quality: {quality}")
        #if quality in ["good", "great"]:
        #    send_telegram_message(f"🌇 Sunset quality is *{quality.upper()}* today!\nCheck the sky tonight 🌤")
    except Exception as e:
        log_message = f"Error checking sunset quality: {str(e)}"
    #    send_telegram_message(f"Sunset bot error: {str(e)}")

if __name__ == "__main__":
    main()
