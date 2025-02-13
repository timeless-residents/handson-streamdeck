#!/usr/bin/env python3
import time, random
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_color(color):
    return Image.new("RGB", (w, h), color=color)

def key_callback(deck, key, state_pressed):
    if state_pressed:
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        deck.set_key_image(key, PILHelper.to_native_format(deck, draw_color(color)))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_color((0, 0, 0))))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
