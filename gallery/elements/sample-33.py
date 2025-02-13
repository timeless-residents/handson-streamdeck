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

# SOS: ... --- ... を、短点（0.2秒）と長点（0.6秒）で再現
pattern = [0.2, 0.2, 0.2, 0.6, 0.6, 0.6, 0.2, 0.2, 0.2]
for duration in pattern:
    color = (255, 255, 255) if duration < 0.5 else (0, 0, 0)
    image = Image.new("RGB", (w, h), color=color)
    deck.set_key_image(0, PILHelper.to_native_format(deck, image))
    time.sleep(duration)

deck.reset()
deck.close()
