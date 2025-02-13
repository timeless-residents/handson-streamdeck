#!/usr/bin/env python3
import time, math
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

try:
    while True:
        for i in range(deck.key_count()):
            r = int((math.sin(time.time() + i) + 1) * 127)
            g = int((math.sin(time.time() + i + 2) + 1) * 127)
            b = int((math.sin(time.time() + i + 4) + 1) * 127)
            image = Image.new("RGB", (w, h), color=(r, g, b))
            deck.set_key_image(i, PILHelper.to_native_format(deck, image))
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
