#!/usr/bin/env python3
import time, numpy as np
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

for _ in range(20):
    arr = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
    image = Image.fromarray(arr, "RGB")
    deck.set_key_image(0, PILHelper.to_native_format(deck, image))
    time.sleep(0.1)

deck.reset()
deck.close()
