#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# Stream Deck の取得と初期化
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

# 0～100% のプログレスバーをアニメーション表示
for percent in range(101):
    image = Image.new("RGB", (w, h), color=(30, 30, 30))
    draw = ImageDraw.Draw(image)
    # プログレスバーの長さ
    bar_width = int(w * (percent / 100))
    draw.rectangle([(0, h // 2 - 10), (bar_width, h // 2 + 10)], fill=(0, 255, 0))
    # パーセンテージテキスト
    font = ImageFont.load_default()
    text = f"{percent}%"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (h - text_h) // 2), text, fill=(255, 255, 255), font=font)
    native_image = PILHelper.to_native_format(deck, image)
    deck.set_key_image(0, native_image)
    time.sleep(0.05)

deck.reset()
deck.close()
