#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

text = "Scrolling Text Animation!"
font = ImageFont.load_default()
dummy_img = Image.new("RGB", (1, 1))
draw_dummy = ImageDraw.Draw(dummy_img)
bbox = draw_dummy.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
big_image = Image.new("RGB", (text_width + w, h), color=(0, 0, 0))
draw_big = ImageDraw.Draw(big_image)
draw_big.text((w, (h - (bbox[3] - bbox[1])) // 2), text, fill=(255, 255, 255), font=font)

for offset in range(text_width + w):
    frame = big_image.crop((offset, 0, offset + w, h))
    deck.set_key_image(0, PILHelper.to_native_format(deck, frame))
    time.sleep(0.05)

deck.reset()
deck.close()
