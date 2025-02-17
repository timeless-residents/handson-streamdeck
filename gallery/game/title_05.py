#!/usr/bin/env python3
"""
Whack-a-Mole Challenge:
Stream Deck XL 用のシンプルなモグラたたきゲームです。

4x4 のグリッド（使用するキー: 
  Row 0: 0,1,2,3; 
  Row 1: 8,9,10,11; 
  Row 2: 16,17,18,19; 
  Row 3: 24,25,26,27）上にランダムで「モグラ」が現れ、
プレイヤーはモグラが現れているキーを押してスコアを稼ぎます。
RESET_KEY (キー 31) を押すとゲームがリセットされます。
"""

import time
import random

import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

import cairo  # Pycairo (pip install pycairo)
from PIL import Image, ImageDraw, ImageFont

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# 使用するキー番号の定義（4x4 グリッド）
MEMORY_KEYS = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27]
RESET_KEY = 31  # リセットボタン（グリッド外のキー）

# グローバル変数：ゲーム状態管理
score = 0  # プレイヤースコア
active_mole = None  # 現在モグラが現れているキー（なければ None）
mole_end_time = 0  # 現在のモグラが消える時刻
next_mole_time = 0  # 次のモグラ出現までの時刻
game_end_time = 0  # ゲーム終了時刻
game_over = False  # ゲームオーバーか否か


def create_text_image(
    text: str,
    width: int,
    height: int,
    font_size: int = 40,
    text_color: tuple = (255, 255, 255),
    background_color: tuple = (0, 0, 0),
) -> Image.Image:
    """
    指定したテキストを中央に表示した PIL Image を生成します.
    """
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)
    try:
        # 日本語やアルファベットも含めた表示に適したフォントとして AppleGothic を指定
        font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size
        )
    except IOError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)
    return image


def init_game() -> None:
    """
    ゲームの初期化を行います.
    スコア、出現タイミング、ゲーム終了時刻などをリセットします.
    """
    global score, active_mole, mole_end_time, next_mole_time, game_end_time, game_over
    score = 0
    active_mole = None
    mole_end_time = 0
    next_mole_time = time.time() + random.uniform(0.5, 1.5)
    game_end_time = time.time() + 60  # ゲームは60秒間
    game_over = False


def update_game_board(deck, key_width: int, key_height: int) -> None:
    """
    現在のゲーム状態に応じて、各キーに表示する内容を更新します.

    - ゲーム中の場合:
        * モグラが現れているキーには「Mole!」を表示（茶色背景）
        * その他のキーは穴（グレー背景）
        * RESET_KEY にはスコアと残り時間を表示（ダークグリーン背景）
    - ゲームオーバーの場合:
        * 全キーに「Game Over」を表示（濃い赤背景）
        * RESET_KEY には最終スコアと「Reset」を表示
    """
    global score, active_mole, game_over, game_end_time
    if game_over:
        # ゲームオーバー表示
        for key in MEMORY_KEYS:
            img = create_text_image(
                "Game\nOver",
                key_width,
                key_height,
                font_size=30,
                background_color=(128, 0, 0),
            )
            deck.set_key_image(key, PILHelper.to_native_format(deck, img))
        reset_img = create_text_image(
            f"Score: {score}\nReset",
            key_width,
            key_height,
            font_size=25,
            background_color=(255, 69, 0),
        )
        deck.set_key_image(RESET_KEY, PILHelper.to_native_format(deck, reset_img))
        return

    # ゲーム中の表示更新
    for key in MEMORY_KEYS:
        if active_mole == key:
            # モグラが出現中（茶色背景）
            img = create_text_image(
                "Mole!",
                key_width,
                key_height,
                font_size=30,
                background_color=(139, 69, 19),
            )
        else:
            # 何もない穴（グレー背景）
            img = create_text_image(
                "",
                key_width,
                key_height,
                font_size=30,
                background_color=(169, 169, 169),
            )
        deck.set_key_image(key, PILHelper.to_native_format(deck, img))
    # RESET_KEY にスコアと残り時間を表示
    time_left = max(0, int(game_end_time - time.time()))
    reset_img = create_text_image(
        f"Score: {score}\nTime: {time_left}",
        key_width,
        key_height,
        font_size=20,
        background_color=(0, 100, 0),
    )
    deck.set_key_image(RESET_KEY, PILHelper.to_native_format(deck, reset_img))


def key_callback(deck, key, state_pressed):
    """
    キー押下時のコールバック関数.

    - RESET_KEY が押されるとゲームリセット.
    - MEMORY_KEYS 上で、モグラが出現中のキーが押されるとスコア加点し、モグラを消去.
    """
    global active_mole, score, next_mole_time, game_over
    if not state_pressed:
        return
    if key == RESET_KEY:
        init_game()
        update_game_board(deck, w, h)
        return
    if key in MEMORY_KEYS:
        if active_mole == key:
            # モグラを叩いた → スコア加点＆モグラ消去
            score += 1
            active_mole = None
            next_mole_time = time.time() + random.uniform(0.5, 1.5)
            update_game_board(deck, w, h)


def main() -> None:
    global game_over, active_mole, mole_end_time, next_mole_time, game_end_time
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    global w, h
    key_format = deck.key_image_format()
    w, h = key_format["size"]

    init_game()
    update_game_board(deck, w, h)
    deck.set_key_callback(key_callback)

    try:
        while True:
            current_time = time.time()
            if not game_over:
                if current_time >= game_end_time:
                    game_over = True
                    update_game_board(deck, w, h)
                else:
                    # モグラ出現の処理
                    if active_mole is None and current_time >= next_mole_time:
                        active_mole = random.choice(MEMORY_KEYS)
                        mole_end_time = current_time + 1.0  # 1秒間表示
                    elif active_mole is not None and current_time >= mole_end_time:
                        active_mole = None
                        next_mole_time = current_time + random.uniform(0.5, 1.5)
                    update_game_board(deck, w, h)
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    main()
