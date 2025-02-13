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

text = "Gradient"
font = ImageFont.load_default()

def draw_gradient_text(offset):
    image = Image.new("RGB", (w, h), color=(0, 0, 0))
    # グラデーションオーバーレイ作成
    gradient = Image.new("RGB", (w, h))
    for x in range(w):
        r = int(255 * (((x + offset) % w) / w))
        g = int(255 * (1 - ((x + offset) % w) / w))
        b = 128
        for y in range(h):
            gradient.putpixel((x, y), (r, g, b))
    # テキストマスク作成
    text_mask = Image.new("L", (w, h))
    mask_draw = ImageDraw.Draw(text_mask)
    bbox = mask_draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    mask_draw.text(((w - tw) // 2, (h - th) // 2), text, fill=255, font=font)
    # 合成
    image = Image.composite(gradient, image, text_mask)
    return image

for offset in range(0, w, 5):
    image = draw_gradient_text(offset)
    deck.set_key_image(0, PILHelper.to_native_format(deck, image))
    time.sleep(0.1)

deck.reset()
deck.close()
