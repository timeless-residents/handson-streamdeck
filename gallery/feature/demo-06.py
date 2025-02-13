#!/usr/bin/env python3
import time, os, subprocess
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

# スクリーンショットの一時保存先
screenshot_path = "screenshot.png"

# Stream Deck 初期化
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def capture_screenshot():
    # macOS の screencapture でスクリーンショット取得（-x: サウンド無し）
    subprocess.run(["screencapture", "-x", screenshot_path])
    try:
        # Convert RGBA to RGB when opening the image
        img = Image.open(screenshot_path).convert('RGB').resize((w, h))
        return img
    except Exception as e:
        print("スクリーンショット読み込みエラー:", e)
        return None

def draw_label(text):
    from PIL import ImageDraw, ImageFont
    image = Image.new("RGB", (w, h), color=(20,20,20))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(255,255,255), font=font)
    return image

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Capturing...")))
        img = capture_screenshot()
        if img:
            deck.set_key_image(0, PILHelper.to_native_format(deck, img))
            time.sleep(5)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Screenshot")))
        
deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Screenshot")))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
    # 任意: スクリーンショットファイル削除
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
