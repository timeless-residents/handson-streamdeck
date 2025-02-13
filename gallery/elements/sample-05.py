#!/usr/bin/env python3
import time, random
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_key(index):
    color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    image = Image.new("RGB", (w, h), color=color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"{index}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 255), font=font)
    return image

for i in range(deck.key_count()):
    deck.set_key_image(i, PILHelper.to_native_format(deck, draw_key(i)))

time.sleep(10)
deck.reset()
deck.close()
