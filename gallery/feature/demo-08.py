#!/usr/bin/env python3
import time, psutil
from datetime import timedelta
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

try:
    import psutil
except ImportError:
    print("psutil モジュールが必要です。pip install psutil")
    exit()

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def get_uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    return str(timedelta(seconds=int(uptime_seconds)))

def draw_uptime(uptime_text):
    image = Image.new("RGB", (w, h), color=(0,0,0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), uptime_text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), uptime_text, fill=(0,255,0), font=font)
    return image

try:
    while True:
        uptime_text = get_uptime()
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_uptime(uptime_text)))
        time.sleep(1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
