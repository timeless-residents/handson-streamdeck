#!/usr/bin/env python3
import time, math
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

for angle in range(0, 360, 15):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    center = (w // 2, h // 2)
    length = min(w, h) // 2 - 5
    end = (int(center[0] + length * math.cos(math.radians(angle))),
           int(center[1] + length * math.sin(math.radians(angle))))
    draw.line([center, end], fill=(255, 255, 255), width=3)
    deck.set_key_image(0, PILHelper.to_native_format(deck, image))
    time.sleep(0.1)

deck.reset()
deck.close()
