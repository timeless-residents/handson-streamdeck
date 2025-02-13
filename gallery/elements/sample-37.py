#!/usr/bin/env python3
import time, itertools
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

icons = ["sunny", "cloudy", "rainy"]
icon_cycle = itertools.cycle(icons)

def draw_icon(icon_type):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    if icon_type == "sunny":
        draw.ellipse([(w // 4, h // 4), (w * 3 // 4, h * 3 // 4)], fill=(255, 255, 0))
    elif icon_type == "cloudy":
        draw.ellipse([(w // 4, h // 3), (w // 2, h * 2 // 3)], fill=(200, 200, 200))
        draw.ellipse([(w // 3, h // 4), (w * 2 // 3, h // 2)], fill=(200, 200, 200))
    elif icon_type == "rainy":
        draw.ellipse([(w // 4, h // 3), (w // 2, h * 2 // 3)], fill=(180, 180, 180))
        for i in range(3):
            draw.line([(w // 2 + i * 5 - 5, h * 2 // 3), (w // 2 + i * 5 - 5, h - 5)], fill=(0, 0, 255), width=2)
    return image

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        icon_type = next(icon_cycle)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_icon(icon_type)))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_icon(next(icon_cycle))))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
