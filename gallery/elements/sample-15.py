#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def create_image(text, bg_color):
    image = Image.new("RGB", (w, h), color=bg_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 255), font=font)
    return image

def key_callback(deck, key, state_pressed):
    if state_pressed:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        image = create_image(f"Key {key}", colors[key % len(colors)])
        deck.set_key_image(key, PILHelper.to_native_format(deck, image))

deck.set_key_callback(key_callback)
# 各キーを初期化
for i in range(deck.key_count()):
    deck.set_key_image(i, PILHelper.to_native_format(deck, create_image(str(i), (50, 50, 50))))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
