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

def draw_key_index(index):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"Key {index}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 255), font=font)
    return image

def key_callback(deck, key, state_pressed):
    if state_pressed:
        image = draw_key_index(key)
        deck.set_key_image(key, PILHelper.to_native_format(deck, image))

deck.set_key_callback(key_callback)
# 各キーを初期化（黒背景）
for i in range(deck.key_count()):
    blank = Image.new("RGB", (w, h), color=(0, 0, 0))
    deck.set_key_image(i, PILHelper.to_native_format(deck, blank))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
