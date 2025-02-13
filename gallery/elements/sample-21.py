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

def draw_text(text, bg_color):
    image = Image.new("RGB", (w, h), color=bg_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 255), font=font)
    return image

# キー0: "Yes"、キー1: "No" を表示
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_text("Yes", (0, 128, 0))))
deck.set_key_image(1, PILHelper.to_native_format(deck, draw_text("No", (128, 0, 0))))

def key_callback(deck, key, state_pressed):
    if state_pressed:
        if key == 0:
            deck.set_key_image(key, PILHelper.to_native_format(deck, draw_text("Shutting Down", (0, 0, 0))))
        elif key == 1:
            deck.set_key_image(key, PILHelper.to_native_format(deck, draw_text("Cancelled", (0, 0, 0))))

deck.set_key_callback(key_callback)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
