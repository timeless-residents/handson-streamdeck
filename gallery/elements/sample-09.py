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

# ※ 適宜、存在する画像ファイルのパスに変更してください
image_path = "assets/sample2.png"

try:
    image = Image.open(image_path).resize((w, h))
except Exception as e:
    print(f"画像読み込みエラー: {e}")
    deck.reset()
    deck.close()
    exit()

deck.set_key_image(0, PILHelper.to_native_format(deck, image))
time.sleep(5)
deck.reset()
deck.close()
