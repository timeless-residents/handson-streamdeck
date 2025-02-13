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

def draw_usage(cpu, mem):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"CPU: {cpu}%\nMEM: {mem}%"
    draw.multiline_text((5, 5), text, fill=(255, 255, 0), font=font, spacing=2)
    return image

try:
    while True:
        cpu = random.randint(0, 100)
        mem = random.randint(0, 100)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_usage(cpu, mem)))
        time.sleep(1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
