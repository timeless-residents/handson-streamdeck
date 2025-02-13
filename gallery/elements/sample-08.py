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

def draw_cpu_usage(usage):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    text = f"CPU {usage}%"
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 0), font=font)
    return image

try:
    while True:
        usage = random.randint(0, 100)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_cpu_usage(usage)))
        time.sleep(1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
