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

def draw_dice(number):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"{number}"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), text, fill=(255, 255, 255), font=font)
    return image

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        number = random.randint(1, 6)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_dice(number)))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_dice(0)))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
