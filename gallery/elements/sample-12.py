#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

# ※ 適宜、存在するアイコンファイルのパスに変更してください
icon_path = "assets/sample2.png"
try:
    icon = Image.open(icon_path).resize((w, h))
except Exception as e:
    print(f"アイコン読み込みエラー: {e}")
    deck.reset()
    deck.close()
    exit()

try:
    for angle in range(0, 360, 5):
        rotated = icon.rotate(angle)
        deck.set_key_image(0, PILHelper.to_native_format(deck, rotated))
        time.sleep(0.05)
except KeyboardInterrupt:
    pass

deck.reset()
deck.close()
