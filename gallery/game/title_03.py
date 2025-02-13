#!/usr/bin/env python3
"""
Memory Match Challenge:
Stream Deck XL 用のシンプルな神経衰弱ゲームです。

4x4 のグリッド（使用するキー: 
  Row 0: 0,1,2,3; 
  Row 1: 8,9,10,11; 
  Row 2: 16,17,18,19; 
  Row 3: 24,25,26,27）にカードを配置します。
各カードは、8種類のシンボル ("A"～"H") のペアとなっており、カードが伏せられている状態は「?」で表示されます。
RESET_KEY (キー 31) を押すとゲームをリセットします。
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

# 使用するキー番号の定義（4x4 グリッド）
MEMORY_KEYS = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27]
RESET_KEY = 31  # リセットボタン（グリッド外のキー）

# キー番号からグリッドのインデックスへのマッピング
BOARD_KEY_MAP = {key: index for index, key in enumerate(MEMORY_KEYS)}

# カードシンボル（8種類、各2枚ずつ）
CARD_SYMBOLS = ["A", "B", "C", "D", "E", "F", "G", "H"]

# ゲーム状態のグローバル変数
memory_cards = {}     # MEMORY_KEYS -> カードシンボルの割り当て
flipped_cards = []    # 現在表向きのカードのキー番号（最大2枚）
solved_cards = set()  # 既に一致したカードのキー番号

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
        # 日本語やアルファベットも含めた表示に適したフォントとして AppleGothic を指定
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

def init_memory_cards() -> None:
    """
    MEMORY_KEYS にランダムなカード割り当てを行い、グローバル変数を初期化します.
    """
    global memory_cards, flipped_cards, solved_cards
    deck_cards = CARD_SYMBOLS * 2  # 16 枚 (8ペア)
    random.shuffle(deck_cards)
    memory_cards = {key: deck_cards[i] for i, key in enumerate(MEMORY_KEYS)}
    flipped_cards = []
    solved_cards = set()

def update_memory_board(deck, key_width: int, key_height: int) -> None:
    """
    MEMORY_KEYS の状態に合わせて、各キーにカードの内容を表示します.
    
    - カードが伏せられている場合は「?」を表示（背景はライトグレー）。
    - カードが表向き（flipped または solved）の場合は実際のシンボルを表示（背景は黒）。
    - RESET_KEY には「Reset」をオレンジレッド背景で表示します.
    """
    global memory_cards, flipped_cards, solved_cards
    for key in MEMORY_KEYS:
        if key in flipped_cards or key in solved_cards:
            symbol = memory_cards[key]
        else:
            symbol = "?"
        bg_color = (0, 0, 0) if symbol != "?" else (173, 216, 230)  # 黒 or ライトブルー
        img = create_text_image(symbol, key_width, key_height, font_size=50, background_color=bg_color)
        deck.set_key_image(key, PILHelper.to_native_format(deck, img))
    # RESET_KEY 表示（オレンジレッド背景）
    reset_img = create_text_image("Reset", key_width, key_height, font_size=30, background_color=(255, 69, 0))
    deck.set_key_image(RESET_KEY, PILHelper.to_native_format(deck, reset_img))

def check_all_solved() -> bool:
    """
    全ての MEMORY_KEYS が解決済みか判定します.
    
    Returns:
        bool: 全て解決なら True を返す.
    """
    return len(solved_cards) == len(MEMORY_KEYS)

def key_callback(deck, key, state_pressed):
    """
    キー押下時のコールバック関数です.
    
    - RESET_KEY が押された場合、ゲームをリセットします.
    - MEMORY_KEYS のうち、まだ解決されておらず伏せられているカードを選択した場合、カードを表向きにします.
    - 2 枚表向きになった場合、一致するかを判定し、一致すればそのカードは解決状態に、そうでなければ伏せ直します.
    """
    global memory_cards, flipped_cards, solved_cards
    if not state_pressed:
        return
    if key == RESET_KEY:
        init_memory_cards()
        update_memory_board(deck, w, h)
        return
    if key in MEMORY_KEYS and key not in flipped_cards and key not in solved_cards:
        flipped_cards.append(key)
        update_memory_board(deck, w, h)
        if len(flipped_cards) == 2:
            key1, key2 = flipped_cards
            if memory_cards[key1] == memory_cards[key2]:
                solved_cards.add(key1)
                solved_cards.add(key2)
                flipped_cards.clear()
                update_memory_board(deck, w, h)
                if check_all_solved():
                    # 全ペアが解決されたら、全てのキーに結果を表示
                    for k in MEMORY_KEYS:
                        img = create_text_image("Clear!", w, h, font_size=30, background_color=(0, 128, 0))
                        deck.set_key_image(k, PILHelper.to_native_format(deck, img))
            else:
                time.sleep(1)
                flipped_cards.clear()
                update_memory_board(deck, w, h)

def main() -> None:
    """
    メイン関数:
      - Stream Deck を初期化し、キーサイズを取得します.
      - MEMORY_KEYS にランダムなカード割り当てを行い、初期状態（全伏せ）を表示します.
      - RESET_KEY にリセットボタンを表示します.
      - キー押下時のコールバックを登録し、ユーザー入力を待機します.
    """
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    global w, h
    key_format = deck.key_image_format()
    w, h = key_format["size"]

    init_memory_cards()
    update_memory_board(deck, w, h)

    deck.set_key_callback(key_callback)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()

if __name__ == "__main__":
    main()
