#!/usr/bin/env python3
"""
Mini Slot Machine (Vertical Reels with Grid Result):
Stream Deck XL 用の 3×3 グリッドを使ったミニスロットマシンゲームです。

【キー配置】
- 盤面（各リール）の表示キー:
    第1列: keys [0, 8, 16]
    第2列: keys [1, 9, 17]
    第3列: keys [2, 10, 18]
- 各列のストップボタン:
    第1列: key 24
    第2列: key 25
    第3列: key 26
- スタートボタン: key 31

各リールは、固定順序リストに沿って連続的にシンボルを回転させます。
ストップボタンで各列を個別に停止し、停止時に列のオフセットを調整して表示状態を「クリーン」にします。
全列停止後、グリッド全体（3×3）で横・縦・斜めのいずれかに３つのシンボルが揃っていれば "Win!"、そうでなければ "Lose" と判定します。
"""

# pylint: disable=wrong-import-position,no-member

import os
import time
import random
import threading

import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

import cairo  # Pycairo (pip install pycairo)
from PIL import Image, ImageDraw, ImageFont

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# --- キー設定 ---
COLUMN_KEYS = [
    [0, 8, 16],    # 第1列（左）
    [1, 9, 17],    # 第2列（中央）
    [2, 10, 18]    # 第3列（右）
]
STOP_KEYS = [24, 25, 26]  # 各列のストップボタン（左～右）
START_KEY = 31            # スタートボタン

# --- スロットシンボル設定 ---
SLOT_SYMBOLS = ["cherry", "lemon", "orange", "grape", "star", "diamond"]

# --- グローバル変数 ---
reel_spinning = [False, False, False]  # 各列の回転状態
reel_results = [None, None, None]        # 各列の最終状態（各列は長さ３のリスト）
animation_threads = [None, None, None]   # 各列のアニメーション用スレッド
game_active = False                      # ゲーム進行状態
# 各列の固定順序リストと現在のオフセット（列ごとに SLOT_SYMBOLS を複数回連結したリスト）
column_orders = [[], [], []]
reel_offsets = [0, 0, 0]

# グローバルロック（キー更新用）
deck_lock = threading.Lock()

# --- 画像読み込み ---
SLOT_IMAGES = {}
IMAGE_DIR = "assets/slot_images"
for symbol in SLOT_SYMBOLS:
    path = os.path.join(IMAGE_DIR, f"{symbol}.png")
    try:
        img = Image.open(path).convert("RGB")
        SLOT_IMAGES[symbol] = img
    except IOError:
        print(f"Error: Unable to load image for {symbol} at {path}")

def create_text_image(text: str, width: int, height: int, font_size: int = 40,
                      text_color: tuple = (255, 255, 255),
                      background_color: tuple = (0, 0, 0)) -> Image.Image:
    """
    指定テキストを中央に表示する画像を生成します.
    """
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)
    return image

def init_column_orders() -> None:
    """
    各列の固定順序リストを初期化します.
    各列について、SLOT_SYMBOLS を 10 回繰り返したリストをランダムにシャッフルして設定します.
    """
    global column_orders, reel_offsets
    for i in range(3):
        order = []
        for _ in range(10):
            temp = SLOT_SYMBOLS.copy()
            random.shuffle(temp)
            order.extend(temp)
        column_orders[i] = order
        reel_offsets[i] = 0

def animate_column(col_index: int, deck, width: int, height: int) -> None:
    """
    指定列 (col_index) の垂直回転アニメーションを実行します.
    COLUMN_KEYS[col_index] のキー群に対して、順序リストに沿った連続的な表示（上・中・下）を更新します.
    """
    global reel_spinning, reel_offsets, column_orders, reel_results
    keys = COLUMN_KEYS[col_index]
    order = column_orders[col_index]
    while reel_spinning[col_index]:
        offset = reel_offsets[col_index]
        # 画面に表示するのは、上、中、下の 3 つのシンボル
        visible = [order[(offset + j) % len(order)] for j in range(3)]
        # 各キーに対応する画像を更新
        for j, key in enumerate(keys):
            symbol = visible[j]
            if symbol in SLOT_IMAGES:
                img = SLOT_IMAGES[symbol].resize((width, height))
            else:
                img = create_text_image(symbol, width, height, font_size=50)
            native_img = PILHelper.to_native_format(deck, img)
            with deck_lock:
                deck.set_key_image(key, native_img)
        reel_offsets[col_index] = (offset + 1) % len(order)
        time.sleep(0.2)
    # 停止時、調整：列内の表示が「整合」するよう、オフセットを最も近い整った位置に調整する
    remainder = reel_offsets[col_index] % len(keys)
    if remainder != 0:
        reel_offsets[col_index] -= remainder  # 下方向に調整
    # 最終表示の更新
    final = [order[(reel_offsets[col_index] + j) % len(order)] for j in range(3)]
    for j, key in enumerate(keys):
        symbol = final[j]
        if symbol in SLOT_IMAGES:
            img = SLOT_IMAGES[symbol].resize((width, height))
        else:
            img = create_text_image(symbol, width, height, font_size=50)
        with deck_lock:
            deck.set_key_image(key, PILHelper.to_native_format(deck, img))
    reel_results[col_index] = final

def start_game(deck, width: int, height: int) -> None:
    """
    ゲーム開始: 各列の回転状態を True にしてアニメーションを開始します.
    各列の順序リストを初期化します.
    """
    global reel_spinning, animation_threads, game_active, reel_results
    game_active = True
    reel_results = [None, None, None]
    init_column_orders()
    for i in range(3):
        reel_spinning[i] = True
        t = threading.Thread(target=animate_column, args=(i, deck, width, height))
        t.start()
        animation_threads[i] = t

def stop_column(col_index: int, deck, width: int, height: int) -> None:
    """
    指定列 (col_index) の回転を停止し、整った状態に調整します.
    """
    global reel_spinning, animation_threads
    reel_spinning[col_index] = False
    if animation_threads[col_index] is not None:
        animation_threads[col_index].join()
        animation_threads[col_index] = None

def check_grid_result() -> str:
    """
    盤面（3×3 グリッド）の結果を判定します.
    グリッドは、row r, col c のセルは reel_results[c][r] とします.
    
    Returns:
        str: 任意の行、列、斜めで3つが一致すれば "Win!"、そうでなければ "Lose".
    """
    grid = [[reel_results[c][r] for c in range(3)] for r in range(3)]
    # 横の判定
    for r in range(3):
        if grid[r][0] != "" and grid[r][0] == grid[r][1] == grid[r][2]:
            return "Win!"
    # 縦の判定
    for c in range(3):
        if grid[0][c] != "" and grid[0][c] == grid[1][c] == grid[2][c]:
            return "Win!"
    # 斜めの判定
    if grid[0][0] != "" and grid[0][0] == grid[1][1] == grid[2][2]:
        return "Win!"
    if grid[0][2] != "" and grid[0][2] == grid[1][1] == grid[2][0]:
        return "Win!"
    return "Lose"

def show_result(deck, width: int, height: int, result: str) -> None:
    """
    盤面全体に結果メッセージを表示します.
    """
    overlay = create_text_image(result, width, height, font_size=30, background_color=(0, 128, 0))
    for col in COLUMN_KEYS:
        for key in col:
            with deck_lock:
                deck.set_key_image(key, PILHelper.to_native_format(deck, overlay))

def reset_game(deck, width: int, height: int) -> None:
    """
    ゲームをリセットし、各列に "Spin" 表示を戻します.
    """
    global game_active, reel_results
    game_active = False
    reel_results = [None, None, None]
    spin_img = create_text_image("Spin", width, height, font_size=30, background_color=(0, 0, 128))
    for col in COLUMN_KEYS:
        for key in col:
            with deck_lock:
                deck.set_key_image(key, PILHelper.to_native_format(deck, spin_img))

def key_callback(deck, key, state_pressed):
    """
    キー押下時のコールバック関数.
    
    - START_KEY (キー 31) でゲーム開始（各列の回転開始）。
    - 各 STOP_KEYS (キー 24,25,26) で対応する列の回転を停止。
    - 全列停止後、2秒間最終状態を表示し、結果判定して全盤面にオーバーレイ表示、3秒後に自動リセット。
    """
    global game_active
    if not state_pressed:
        return
    if key == START_KEY and not game_active:
        start_game(deck, w, h)
    elif key in STOP_KEYS and game_active:
        col_index = STOP_KEYS.index(key)
        if reel_spinning[col_index]:
            stop_column(col_index, deck, w, h)
        if all(not spin for spin in reel_spinning):
            time.sleep(2)  # 最終状態を確認するため2秒待つ
            result = check_grid_result()
            show_result(deck, w, h, result)
            time.sleep(3)
            reset_game(deck, w, h)

def main() -> None:
    """
    メイン関数:
      - Stream Deck を初期化し、キーサイズを取得します.
      - 各 COLUMN_KEYS に初期表示 "Spin" を、各 STOP_KEYS に "Stop"、START_KEY に "Start" を表示します.
      - キー押下時のコールバックを登録し、ユーザー入力を待機します.
    """
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    global w, h
    key_format = deck.key_image_format()
    w, h = key_format["size"]

    reset_game(deck, w, h)

    # 各 STOP_KEYS 表示 ("Stop")
    stop_img = create_text_image("Stop", w, h, font_size=30, background_color=(255, 69, 0))
    for sk in STOP_KEYS:
        with deck_lock:
            deck.set_key_image(sk, PILHelper.to_native_format(deck, stop_img))
    # START_KEY 表示 ("Start")
    start_img = create_text_image("Start", w, h, font_size=30, background_color=(0, 0, 128))
    with deck_lock:
        deck.set_key_image(START_KEY, PILHelper.to_native_format(deck, start_img))

    deck.set_key_callback(key_callback)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()

if __name__ == "__main__":
    main()
