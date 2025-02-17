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
import os

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
active_moles = []  # 現在出現中のモグラのキー（複数可）
mole_end_times = {}  # 各モグラの消える時刻（key -> 時刻）
next_mole_time = 0  # 次のモグラ出現までの時刻
game_end_time = 0  # ゲーム終了時刻
game_over = False  # ゲームオーバーか否か
start_time = 0  # ゲーム開始時刻


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
        # 絵文字なども表示可能なフォントとして AppleGothic を利用（環境に合わせて調整）
        font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size
        )
    except IOError:
        try:
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


def load_mole_image(width: int, height: int) -> Image.Image:
    """
    mole.png という画像ファイルからモグラの画像を読み込み、指定サイズにリサイズします。
    読み込みに失敗した場合は、代わりに絵文字（🐹）を描画した画像を返します。
    """
    try:
        if not os.path.exists("mole.png"):
            raise FileNotFoundError("mole.png が存在しません。")
        img = Image.open("mole.png").convert("RGB")
        img = img.resize((width, height))
    except Exception as e:
        print("mole.png の読み込みに失敗しました:", e)
        img = create_text_image(
            "🐹", width, height, font_size=30, background_color=(139, 69, 19)
        )
    return img


def init_game() -> None:
    """
    ゲームの初期化を行います。
    スコア、モグラ出現タイミング、ゲーム終了時刻などをリセットします。
    """
    global score, active_moles, mole_end_times, next_mole_time, game_end_time, game_over, start_time
    score = 0
    active_moles = []
    mole_end_times = {}
    # ゲーム開始時にすぐモグラ追加できるよう、next_mole_time を現在時刻に設定
    next_mole_time = time.time()
    start_time = time.time()
    game_end_time = start_time + 60  # ゲームは60秒間
    game_over = False


def update_game_board(deck, key_width: int, key_height: int) -> None:
    """
    現在のゲーム状態に応じて、各キーに表示する内容を更新します。
    ゲーム中は出現中のモグラは画像、その他は穴（グレー背景）として表示。
    RESET_KEY にはスコアと残り時間を表示し、ゲームオーバー時は全キーに Game Over を表示します。
    """
    global score, active_moles, game_over, game_end_time
    if game_over:
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

    for key in MEMORY_KEYS:
        if key in active_moles:
            img = load_mole_image(key_width, key_height)
        else:
            img = create_text_image(
                "",
                key_width,
                key_height,
                font_size=30,
                background_color=(169, 169, 169),
            )
        deck.set_key_image(key, PILHelper.to_native_format(deck, img))

    time_left = max(0, int(game_end_time - time.time()))
    reset_img = create_text_image(
        f"Score: {score}\nTime: {time_left}",
        key_width,
        key_height,
        font_size=14,
        background_color=(0, 100, 0),
    )
    deck.set_key_image(RESET_KEY, PILHelper.to_native_format(deck, reset_img))


def key_callback(deck, key, state_pressed):
    """
    キー押下時のコールバック関数です。
    - RESET_KEY が押されるとゲームをリセットします。
    - MEMORY_KEYS 上で、出現中のモグラを叩くとスコアが加算され、そのモグラは消えます。
    """
    global active_moles, score, next_mole_time, game_over, mole_end_times
    if not state_pressed:
        return
    if key == RESET_KEY:
        init_game()
        update_game_board(deck, w, h)
        return
    if key in MEMORY_KEYS:
        if key in active_moles:
            score += 1
            active_moles.remove(key)
            if key in mole_end_times:
                del mole_end_times[key]
            # 次のモグラ出現タイミングを更新
            next_mole_time = time.time() + random.uniform(0.5, 1.5)
            update_game_board(deck, w, h)


def main() -> None:
    global game_over, active_moles, mole_end_times, next_mole_time, game_end_time, start_time
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
                    # 常に同時に最大2匹のモグラを出現させる
                    allowed = 2

                    # 1秒経過したモグラは消す
                    for key in active_moles[:]:
                        if current_time >= mole_end_times.get(key, 0):
                            active_moles.remove(key)
                            del mole_end_times[key]

                    # while ループで、許容数に達するまでモグラを追加
                    while (
                        len(active_moles) < allowed and current_time >= next_mole_time
                    ):
                        available_keys = [
                            k for k in MEMORY_KEYS if k not in active_moles
                        ]
                        if available_keys:
                            new_key = random.choice(available_keys)
                            active_moles.append(new_key)
                            mole_end_times[new_key] = (
                                current_time + 1.0
                            )  # 各モグラは1秒間表示
                            # 次のモグラ出現タイミングを短めに設定
                            next_mole_time = current_time + random.uniform(0.1, 0.3)
                        else:
                            break

                    update_game_board(deck, w, h)
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    main()

