#!/usr/bin/env python3
import time
import os
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper


def create_full_image(width, height):
    """
    幅width、高さheightのキャンバスを作成し、
    中央に赤い円を描画して返す
    """
    # 黒い背景の画像を作成
    image = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 円を描く。円の外接矩形の座標を計算
    margin = 20
    left = margin
    top = margin
    right = width - margin
    bottom = height - margin
    draw.ellipse(
        (left, top, right, bottom), fill=(255, 0, 0), outline=(255, 255, 0), width=5
    )

    return image


def slice_image_to_keys(full_image, rows, cols, key_width, key_height):
    """
    全体画像full_imageをキーサイズ (key_width x key_height) ごとに切り出し、
    キー順（左上→右下）に並んだリストとして返す。
    """
    key_images = []
    for row in range(rows):
        for col in range(cols):
            left = col * key_width
            upper = row * key_height
            cropped = full_image.crop(
                (left, upper, left + key_width, upper + key_height)
            )
            key_images.append(cropped)
    return key_images


def get_deck_layout(deck):
    """
    接続しているStreamDeckのキー数から、一般的なモデルのレイアウトを推測する。
    ※環境に合わせて適宜変更してください。
    """
    num_keys = deck.key_count()  # メソッド呼び出しでキー数を取得
    if num_keys == 6:
        return 2, 3  # StreamDeck Mini
    elif num_keys == 15:
        return 3, 5  # 標準モデル
    elif num_keys == 32:
        return 4, 8  # StreamDeck XL
    else:
        cols = int(num_keys**0.5)
        rows = (num_keys + cols - 1) // cols
        return rows, cols


# StreamDeckの初期化
streamdecks = DeviceManager().enumerate()
if not streamdecks:
    raise Exception("StreamDeckが見つかりませんでした。")
deck = streamdecks[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
key_width, key_height = key_format["size"]

# キーレイアウト（行数、列数）の取得
rows, cols = get_deck_layout(deck)
full_width = cols * key_width
full_height = rows * key_height

print("StreamDeck全体を1つのキャンバスとして表示します。Ctrl+Cで終了。")

try:
    while True:
        # 全体画像に絵（円）を描画
        full_image = create_full_image(full_width, full_height)
        # 全体画像を各キーサイズに分割
        key_images = slice_image_to_keys(full_image, rows, cols, key_width, key_height)

        # 各キーに画像をセット
        for idx, key_img in enumerate(key_images):
            if idx >= deck.key_count():
                break
            deck.set_key_image(idx, PILHelper.to_native_format(deck, key_img))

        time.sleep(10)  # 10秒ごとに更新
except KeyboardInterrupt:
    print("\n終了します...")
finally:
    deck.reset()
    deck.close()
