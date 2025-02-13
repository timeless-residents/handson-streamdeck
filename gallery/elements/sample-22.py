#!/usr/bin/env python3
import time
from datetime import datetime
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_date():
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), date_str, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), date_str, fill=(255, 255, 255), font=font)
    return image

deck.set_key_image(0, PILHelper.to_native_format(deck, draw_date()))
time.sleep(5)
deck.reset()
deck.close()
