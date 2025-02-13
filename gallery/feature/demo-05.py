#!/usr/bin/env python3
import subprocess
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# 各キーに対応するウェブサイトのURLとラベルを定義
shortcuts = {
    0: {"label": "Gmail", "url": "https://mail.google.com/"},
    1: {"label": "YouTube", "url": "https://www.youtube.com/"},
    2: {"label": "Twitter", "url": "https://twitter.com/"},
    3: {"label": "News", "url": "https://news.google.com/"},
}

def draw_label(text):
    image = Image.new("RGB", (w, h), color=(0, 0, 40))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(255,255,255), font=font)
    return image

def open_url(url):
    subprocess.run(["open", url])

# 初期化
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def key_callback(deck, key, state_pressed):
    if state_pressed and key in shortcuts:
        url = shortcuts[key]["url"]
        open_url(url)
        # 一瞬フィードバック表示
        deck.set_key_image(key, PILHelper.to_native_format(deck, draw_label("Opening...")))
        time.sleep(0.5)
        deck.set_key_image(key, PILHelper.to_native_format(deck, draw_label(shortcuts[key]["label"])))

deck.set_key_callback(key_callback)

# 各キーに初期ラベルを設定
for key, info in shortcuts.items():
    deck.set_key_image(key, PILHelper.to_native_format(deck, draw_label(info["label"])))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
