#!/usr/bin/env python3
import subprocess
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# AppleScript 経由で現在の音量を取得
def get_volume():
    result = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"],
                            stdout=subprocess.PIPE, universal_newlines=True)
    try:
        return int(result.stdout.strip())
    except:
        return 50

# AppleScript 経由で音量を設定（0～100）
def set_volume(vol):
    vol = max(0, min(100, vol))
    subprocess.run(["osascript", "-e", f"set volume output volume {vol}"])

# ラベル描画
def draw_label(text):
    image = Image.new("RGB", (w, h), color=(30, 30, 30))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(255,255,255), font=font)
    return image

# 初期化
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

# キー0: Volume UP, キー1: Volume DOWN
def key_callback(deck, key, state_pressed):
    if state_pressed:
        vol = get_volume()
        if key == 0:  # Volume Up
            new_vol = vol + 10
            set_volume(new_vol)
            deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label(f"Vol+ {new_vol}")))
        elif key == 1:  # Volume Down
            new_vol = vol - 10
            set_volume(new_vol)
            deck.set_key_image(1, PILHelper.to_native_format(deck, draw_label(f"Vol- {new_vol}")))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Vol+")))
deck.set_key_image(1, PILHelper.to_native_format(deck, draw_label("Vol-")))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
