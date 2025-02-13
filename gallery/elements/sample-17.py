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

current_page = 0

def create_page(page):
    image = Image.new("RGB", (w, h), color=(20 * page, 20 * page, 20 * page))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"Page {page}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 255), font=font)
    return image

def key_callback(deck, key, state_pressed):
    global current_page
    # ここではキー0が押されたらページ切替
    if state_pressed and key == 0:
        current_page = (current_page + 1) % 2
        deck.set_key_image(0, PILHelper.to_native_format(deck, create_page(current_page)))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, create_page(current_page)))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
