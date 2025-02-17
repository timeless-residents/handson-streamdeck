#!/usr/bin/env python3
import time
import datetime
import math
import os
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper


def create_clock_image(width, height):
    """
    指定された幅・高さの画像に、現在時刻に合わせたアナログ時計を描画して返す
    """
    # 背景を暗めの青色に設定
    image = Image.new("RGB", (width, height), color=(0, 30, 60))
    draw = ImageDraw.Draw(image)

    # 時計の中心と半径を計算
    cx, cy = width // 2, height // 2
    margin = 10
    radius = min(cx, cy) - margin

    # 時計の外枠（円）を描く
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        outline=(255, 255, 255),
        width=3,
    )

    # 現在時刻を取得
    now = datetime.datetime.now()
    hour = now.hour % 12
    minute = now.minute
    second = now.second

    # 各針の角度を計算（12時位置が基準：-90度）
    hour_angle = (math.pi * 2) * ((hour + minute / 60) / 12) - math.pi / 2
    minute_angle = (math.pi * 2) * ((minute + second / 60) / 60) - math.pi / 2
    second_angle = (math.pi * 2) * (second / 60) - math.pi / 2

    # 針の長さ（時計の半径に対する比率）
    hour_length = radius * 0.5
    minute_length = radius * 0.8
    second_length = radius * 0.9

    # 各針の先端座標を計算
    hour_x = cx + int(hour_length * math.cos(hour_angle))
    hour_y = cy + int(hour_length * math.sin(hour_angle))
    minute_x = cx + int(minute_length * math.cos(minute_angle))
    minute_y = cy + int(minute_length * math.sin(minute_angle))
    second_x = cx + int(second_length * math.cos(second_angle))
    second_y = cy + int(second_length * math.sin(second_angle))

    # 各針を描画
    # 時針（太く、黄色）
    draw.line((cx, cy, hour_x, hour_y), fill=(255, 255, 0), width=6)
    # 分針（緑色）
    draw.line((cx, cy, minute_x, minute_y), fill=(0, 255, 0), width=4)
    # 秒針（細く、赤色）
    draw.line((cx, cy, second_x, second_y), fill=(255, 0, 0), width=2)

    # 時計の中心に小さな円を描く
    draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(255, 255, 255))

    # 12箇所の目盛りを描く
    for i in range(12):
        angle = (math.pi * 2) * (i / 12) - math.pi / 2
        start_x = cx + int((radius - 10) * math.cos(angle))
        start_y = cy + int((radius - 10) * math.sin(angle))
        end_x = cx + int(radius * math.cos(angle))
        end_y = cy + int(radius * math.sin(angle))
        draw.line((start_x, start_y, end_x, end_y), fill=(255, 255, 255), width=2)

    return image


def slice_image_to_keys(full_image, rows, cols, key_width, key_height):
    """
    全体画像full_imageを、各キーサイズ (key_width x key_height) ごとに切り出し、
    キー順（左上→右下）に並んだリストとして返す
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
    接続しているStreamDeckのキー数から、一般的なモデルのレイアウトを推測する
    """
    num_keys = deck.key_count()  # メソッド呼び出しで数値取得
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

# キーレイアウトの取得
rows, cols = get_deck_layout(deck)
full_width = cols * key_width
full_height = rows * key_height

print("アナログ時計を表示します。Ctrl+Cで終了。")

try:
    while True:
        # 現在時刻に合わせたアナログ時計の全体画像を生成
        full_image = create_clock_image(full_width, full_height)
        # 全体画像を各キーに合わせたサイズに分割
        key_images = slice_image_to_keys(full_image, rows, cols, key_width, key_height)

        # 各キーに画像を設定
        for idx, key_img in enumerate(key_images):
            if idx >= deck.key_count():
                break
            deck.set_key_image(idx, PILHelper.to_native_format(deck, key_img))

        time.sleep(1)  # 毎秒更新
except KeyboardInterrupt:
    print("\n終了します...")
finally:
    deck.reset()
    deck.close()
