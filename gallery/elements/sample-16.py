#!/usr/bin/env python3
import time, requests, os
from dotenv import load_dotenv
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITY = os.getenv("WEATHER_CITY", "Tokyo")  # Tokyo as default if not specified
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"


deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def fetch_weather():
    try:
        response = requests.get(URL)
        data = response.json()
        temp = data["main"]["temp"]
        return f"{temp}°C"
    except Exception as e:
        return "N/A"

def draw_weather(text):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(0, 255, 255), font=font)
    return image

try:
    while True:
        weather_text = fetch_weather()
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_weather(weather_text)))
        time.sleep(60)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
