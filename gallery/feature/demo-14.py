#!/usr/bin/env python3
import time
import cv2
import math
import os
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


def slice_image_to_keys(full_image, rows, cols, key_width, key_height):
    """
    全体画像 full_image を、各キーサイズ (key_width x key_height) ごとに切り出し、
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
    num_keys = deck.key_count()  # 数値として取得するためにメソッド呼び出し
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

# キーレイアウト（行数, 列数）の取得
rows, cols = get_deck_layout(deck)
full_width = cols * key_width
full_height = rows * key_height

# 再生する動画ファイルのパス（事前にダウンロードしておく）
video_path = "assets/movie.mp4"
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise Exception(f"動画ファイルが開けませんでした: {video_path}")

# 動画のFPSを取得（取得できなければデフォルト25fps）
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 25
frame_delay = 1.0 / fps

print("動画再生を開始します。Ctrl+Cで終了。")

try:
    while True:
        start_frame_time = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            # 動画の終端に達したら先頭に戻す
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # OpenCVはBGRなのでRGBに変換
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # NumPy配列からPIL Imageに変換
        pil_frame = Image.fromarray(frame)
        # 動画フレームをStreamDeck全体のサイズにBICUBICでリサイズ
        full_image = pil_frame.resize((full_width, full_height), Image.BICUBIC)
        # 全体画像を各キーのサイズに分割
        key_images = slice_image_to_keys(full_image, rows, cols, key_width, key_height)

        # 各キーに画像を更新
        for idx, key_img in enumerate(key_images):
            if idx >= deck.key_count():
                break
            deck.set_key_image(idx, PILHelper.to_native_format(deck, key_img))

        # フレーム処理にかかった時間を計測し、次フレームまで待機
        elapsed = time.perf_counter() - start_frame_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
except KeyboardInterrupt:
    print("\n終了します...")
finally:
    cap.release()
    deck.reset()
    deck.close()
