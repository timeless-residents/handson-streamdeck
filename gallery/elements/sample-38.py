#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

def red_square():
    return Image.new("RGB", (w, h), color=(255, 0, 0))

def blue_square():
    return Image.new("RGB", (w, h), color=(0, 0, 255))

images = [red_square, blue_square]
current = [0]

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        current[0] = (current[0] + 1) % len(images)
        deck.set_key_image(0, PILHelper.to_native_format(deck, images[current[0]]()))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, red_square()))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
