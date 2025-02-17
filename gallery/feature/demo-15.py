#!/usr/bin/env python3
import time
import cv2
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


def precompute_coords(rows, cols, key_width, key_height):
    """各キーの左上座標 (x, y) をリストで返す"""
    coords = []
    for row in range(rows):
        for col in range(cols):
            x = col * key_width
            y = row * key_height
            coords.append((x, y))
    return coords


def get_deck_layout(deck):
    """StreamDeckのキー数からレイアウト（行数, 列数）を推測する"""
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

rows, cols = get_deck_layout(deck)
full_width = cols * key_width
full_height = rows * key_height

# 各キーの左上座標を事前計算
coords = precompute_coords(rows, cols, key_width, key_height)

# 動画ファイルのパス（事前にダウンロードしておく）
video_path = "assets/movie2.mp4"
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise Exception(f"動画ファイルが開けませんでした: {video_path}")

# 動画のFPS取得（取得できなければ25fps）
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 25
frame_delay = 1.0 / fps  # 元のフレームレートに合わせた待機時間

# speed_factorが2なら倍速、3なら3倍速…（整数で指定）
speed_factor = 4

print(f"{speed_factor}倍速再生を開始します。Ctrl+Cで終了。")

try:
    while True:
        start_time = time.perf_counter()

        # 1フレーム読み込む
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # OpenCVで高速リサイズ（BGRのまま）、その後RGB変換
        resized_frame = cv2.resize(
            frame, (full_width, full_height), interpolation=cv2.INTER_AREA
        )
        resized_frame = resized_frame[..., ::-1]  # BGR -> RGB

        # PIL Imageに変換
        full_image = Image.fromarray(resized_frame)

        # 各キーの領域をNumPyスライスで抽出して更新
        for idx, (x, y) in enumerate(coords):
            if idx >= deck.key_count():
                break
            region = resized_frame[y : y + key_height, x : x + key_width]
            key_img = Image.fromarray(region)
            deck.set_key_image(idx, PILHelper.to_native_format(deck, key_img))

        # speed_factor > 1の場合、表示後に余分なフレームを読み飛ばす
        for _ in range(speed_factor - 1):
            cap.grab()

        # FPSに合わせた待機
        elapsed = time.perf_counter() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\n終了します...")
finally:
    cap.release()
    deck.reset()
    deck.close()
