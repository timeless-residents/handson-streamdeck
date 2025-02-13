#!/usr/bin/env python3
import time
import numpy as np
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# 接続されているすべての Stream Deck デバイスを取得
streamdecks = DeviceManager().enumerate()

if not streamdecks:
    print("Stream Deck が接続されていません。")
    exit()

# 最初のデバイスを選択
deck = streamdecks[0]
print(f"接続されたデバイス: {deck.deck_type()}")

# デバイスをオープンして初期化
deck.open()
deck.reset()

# キー画像のサイズを取得
key_format = deck.key_image_format()
key_width, key_height = key_format["size"]
print(f"キーサイズ: {key_width}x{key_height}")

# 白い背景の画像を作成し、中央に「Hello」と描画
image = Image.new("RGB", (key_width, key_height), color=(255, 255, 255))
draw = ImageDraw.Draw(image)
text = "Hello"
font_size = 20
try:
    font = ImageFont.truetype("Arial.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

# Pillow 11以降では textsize() が削除されたので textbbox() を使用
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (key_width - text_width) // 2
text_y = (key_height - text_height) // 2
draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)

# PIL Image をデバイス用のネイティブフォーマット（bytes）に変換
native_image = PILHelper.to_native_format(deck, image)

# 最初のキー (インデックス 0) に画像を設定
deck.set_key_image(0, native_image)

# 5秒間表示
time.sleep(5)

# 終了前にキーをクリア
deck.reset()
deck.close()
