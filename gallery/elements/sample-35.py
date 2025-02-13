#!/usr/bin/env python3
import time, colorsys
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

for i in range(360):
    r, g, b = colorsys.hsv_to_rgb(i / 360.0, 1, 1)
    color = (int(r * 255), int(g * 255), int(b * 255))
    image = Image.new("RGB", (w, h), color=color)
    deck.set_key_image(0, PILHelper.to_native_format(deck, image))
    time.sleep(0.05)

deck.reset()
deck.close()
