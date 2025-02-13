#!/usr/bin/env python3
import time, random
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_speed(speed):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"{speed} Mbps"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), text, fill=(0, 255, 0), font=font)
    return image

try:
    while True:
        speed = random.randint(10, 100)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_speed(speed)))
        time.sleep(1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
