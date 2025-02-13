#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def create_gradient():
    image = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(image)
    for i in range(h):
        color = int(255 * (i / h))
        draw.line([(0, i), (w, i)], fill=(color, color, 255))
    return image

image = create_gradient()
deck.set_key_image(0, PILHelper.to_native_format(deck, image))
time.sleep(5)
deck.reset()
deck.close()
