#!/usr/bin/env python3
import subprocess
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# Stream Deck の初期化
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_label(text):
    image = Image.new("RGB", (w, h), color=(20, 20, 20))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(255,255,255), font=font)
    return image

def launch_app():
    # 例: Google Chrome を起動
    subprocess.run(["open", "-a", "Google Chrome"])

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        launch_app()
        # 押下時は一瞬「Launching...」を表示
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Launching...")))
        time.sleep(1)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Chrome")))

# キー0に「Chrome」と表示＆コールバック登録
deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Chrome")))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
