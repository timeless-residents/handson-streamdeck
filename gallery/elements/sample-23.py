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

for battery in range(100, -1, -5):
    image = Image.new("RGB", (w, h), color=(30, 30, 30))
    draw = ImageDraw.Draw(image)
    # バッテリー枠
    draw.rectangle([10, h // 2 - 10, w - 10, h // 2 + 10], outline=(255, 255, 255), width=2)
    fill_width = int((w - 20) * (battery / 100))
    draw.rectangle([10, h // 2 - 10, 10 + fill_width, h // 2 + 10], fill=(0, 255, 0))
    font = ImageFont.load_default()
    text = f"{battery}%"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), text, fill=(255, 255, 255), font=font)
    deck.set_key_image(0, PILHelper.to_native_format(deck, image))
    time.sleep(0.2)

deck.reset()
deck.close()
