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

image = Image.new("RGB", (w, h), color=(255, 255, 255))
draw = ImageDraw.Draw(image)
# 円を描画（余白を10ピクセル確保）
draw.ellipse([(10, 10), (w - 10, h - 10)], outline=(255, 0, 0), width=3)
deck.set_key_image(0, PILHelper.to_native_format(deck, image))
time.sleep(5)
deck.reset()
deck.close()
