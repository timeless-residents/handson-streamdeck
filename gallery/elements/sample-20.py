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
num_keys = deck.key_count()

slider_value = 0

def draw_slider(value):
    for i in range(num_keys):
        color = (0, 255, 0) if i == value else (50, 50, 50)
        image = Image.new("RGB", (w, h), color=color)
        deck.set_key_image(i, PILHelper.to_native_format(deck, image))

def key_callback(deck, key, state_pressed):
    global slider_value
    if state_pressed:
        slider_value = key
        draw_slider(slider_value)

deck.set_key_callback(key_callback)
draw_slider(slider_value)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
