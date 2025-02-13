#!/usr/bin/env python3
"""
Tic Tac Toe Blitz:
Stream Deck XL 用のシンプルな三目並べゲームです。

盤面は 3x3 として、以下のキーを使用します:
    Row 0 (上段):      keys 0, 1, 2
    Row 1 (中段):      keys 8, 9, 10
    Row 2 (下段):      keys 16, 17, 18
リセットボタンは、最下段左端のキー (key 24) を使用します。
また、右上（キー 7）には「XOゲーム」と表示します。

プレイヤーは交互に "X" と "O" を入力し、勝敗または引き分けが決まると結果が全盤面に表示されます。
"""

# pylint: disable=wrong-import-position,no-member

import time
import random

import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

import cairo  # Pycairo (pip install pycairo)
from PIL import Image, ImageDraw, ImageFont

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# 使用するキー番号の定義
BOARD_KEYS = [0, 1, 2, 8, 9, 10, 16, 17, 18]  # 盤面のキー (3x3)
RESET_KEY = 24  # リセットボタン (最下段左端)
# キー番号から盤面インデックスへのマッピング
BOARD_KEY_MAP = {key: index for index, key in enumerate(BOARD_KEYS)}

# ゲームの状態
board = [None] * 9  # 各セルは None, "X", "O"
current_player = "X"
game_over = False

def create_text_image(text: str, width: int, height: int, font_size: int = 40,
                      text_color: tuple = (255, 255, 255),
                      background_color: tuple = (0, 0, 0)) -> Image.Image:
    """
    指定したテキストを中央に表示した PIL Image を生成します.

    Args:
        text (str): 表示するテキスト。
        width (int): 画像の幅。
        height (int): 画像の高さ。
        font_size (int): フォントサイズ。
        text_color (tuple): テキストカラー (R, G, B)。
        background_color (tuple): 背景色 (R, G, B)。

    Returns:
        Image.Image: 生成された画像。
    """
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)
    try:
        # macOS の場合、日本語表示に適したフォントのフルパスを指定（例: AppleGothic）
        # font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size)
        font = ImageFont.truetype(r"/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", font_size)
    except IOError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)
    return image

def update_board(deck, key_width: int, key_height: int) -> None:
    """
    盤面の状態に合わせて、各 BOARD_KEYS にセルの内容 ("X", "O" または空) を表示します。
    空セルはライトブルーの背景色で表示し、既入力セルは黒背景で表示します。
    また、RESET_KEY にはオレンジレッド背景で "Reset" を表示します。
    """
    global board
    for key in BOARD_KEYS:
        cell_index = BOARD_KEY_MAP[key]
        if board[cell_index] is None:
            bg_color = (173, 216, 230)  # ライトブルー
            cell_text = ""
        else:
            bg_color = (0, 0, 0)
            cell_text = board[cell_index]
        img = create_text_image(cell_text, key_width, key_height, font_size=50, background_color=bg_color)
        deck.set_key_image(key, PILHelper.to_native_format(deck, img))
    # Reset ボタン表示（オレンジレッド背景）
    reset_img = create_text_image("Reset", key_width, key_height, font_size=30, background_color=(255, 69, 0))
    deck.set_key_image(RESET_KEY, PILHelper.to_native_format(deck, reset_img))

def check_winner() -> str:
    """
    盤面から勝者 ("X" または "O") または引き分け ("Draw") を判定します.

    Returns:
        str: 勝者がいれば "X" または "O"、引き分けなら "Draw"、ゲーム継続なら空文字列 "" を返す。
    """
    winning_positions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # 行
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # 列
        (0, 4, 8), (2, 4, 6)              # 斜め
    ]
    for a, b, c in winning_positions:
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a]
    if all(cell is not None for cell in board):
        return "Draw"
    return ""

def reset_game(deck, key_width: int, key_height: int) -> None:
    """
    ゲームをリセットし、盤面と状態を初期化します.
    """
    global board, current_player, game_over
    board = [None] * 9
    current_player = "X"
    game_over = False
    update_board(deck, key_width, key_height)

def key_callback(deck, key, state_pressed):
    """
    キー押下時のコールバック関数です.

    - RESET_KEY が押されるとゲームをリセットします。
    - BOARD_KEYS のいずれかが押され、空セルの場合、現在のプレイヤーの印 ("X" または "O") を入力します。
    - 勝者または引き分けが判定された場合、盤面全体に結果メッセージを表示します。
    """
    global board, current_player, game_over
    if not state_pressed:
        return
    if key == RESET_KEY:
        reset_game(deck, w, h)
        return
    if key in BOARD_KEY_MAP and not game_over:
        index = BOARD_KEY_MAP[key]
        if board[index] is None:
            board[index] = current_player
            update_board(deck, w, h)
            winner = check_winner()
            if winner:
                game_over = True
                if winner == "Draw":
                    message = "引き分け"
                else:
                    message = f"勝者: {winner}"
                # 結果を盤面全体に表示
                for k in BOARD_KEYS:
                    img = create_text_image(message, w, h, font_size=20)
                    deck.set_key_image(k, PILHelper.to_native_format(deck, img))
                return
            # プレイヤー交代
            current_player = "O" if current_player == "X" else "X"

def main() -> None:
    """
    メイン関数:
      - Stream Deck を初期化し、キーサイズを取得します。
      - BOARD_KEYS に初期状態の盤面を表示し、RESET_KEY にリセットボタンを表示します。
      - さらに、右上（物理キー番号 7）には "XOゲーム" を表示して初見でもゲームであることを示します。
      - キー押下時のコールバックを登録し、ユーザーの入力を待機します。
    """
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    global w, h
    key_format = deck.key_image_format()
    w, h = key_format["size"]

    reset_game(deck, w, h)
    # タイトル表示：右上（キー 7）に "OXゲーム" を表示
    title_img = create_text_image("OXゲーム", w, h, font_size=15, background_color=(0, 0, 128))
    deck.set_key_image(7, PILHelper.to_native_format(deck, title_img))

    deck.set_key_callback(key_callback)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()

if __name__ == "__main__":
    main()
