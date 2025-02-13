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

# 初期状態は OFF
state = False

def draw_button(state):
    image = Image.new("RGB", (w, h), color=(50, 50, 50))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = "ON" if state else "OFF"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    color = (0, 255, 0) if state else (255, 0, 0)
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=color, font=font)
    return image

def key_callback(deck, key, state_pressed):
    global state
    if state_pressed:
        state = not state
        image = draw_button(state)
        deck.set_key_image(key, PILHelper.to_native_format(deck, image))

# 初期画像設定＆コールバック登録
deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_button(state)))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
