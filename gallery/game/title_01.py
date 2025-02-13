#!/usr/bin/env python3
"""
Omikuji Shuffle:
Stream Deck XL 用の簡単な占いゲームです。
キーを押すと「Shuffling...」と表示され、1秒後にランダムな占い結果が表示されます。

占い結果: 大吉, 中吉, 小吉, 末吉, 吉, 凶, 大凶
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

# 占い結果のリスト
FORTUNES = ["大吉", "中吉", "小吉", "末吉", "吉", "凶", "大凶"]

def create_text_image(text: str, width: int, height: int, font_size: int = 40,
                      text_color: tuple = (255, 255, 255),
                      background_color: tuple = (0, 0, 0)) -> Image.Image:
    """
    指定したテキストを中央に表示した PIL Image を生成します。

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
        # macOS の場合、日本語表示に適したフォントのフルパスを指定します。
        # Hiragino Sans W3 は日本語に対応しており、UTF-8 での表示に適しています。
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

def shuffle_fortune() -> str:
    """
    ランダムな占い結果を返します。

    Returns:
        str: 占い結果の文字列。
    """
    return random.choice(FORTUNES)

def key_callback(deck, key, state_pressed):
    """
    キー押下時のコールバック関数です。
    キーが押されると、まず「Shuffling...」と表示し、1秒後にランダムな占い結果を表示します。
    """
    if state_pressed:
        shuffling_img = create_text_image("判定中", w, h, font_size=30)
        native_shuffling = PILHelper.to_native_format(deck, shuffling_img)
        deck.set_key_image(key, native_shuffling)
        time.sleep(1)
        fortune = shuffle_fortune()
        fortune_img = create_text_image(fortune, w, h, font_size=40)
        native_fortune = PILHelper.to_native_format(deck, fortune_img)
        deck.set_key_image(key, native_fortune)

def main() -> None:
    """
    メイン関数:
      - Stream Deck を初期化し、キーサイズを取得します。
      - キー0 に初期ラベル「Omikuji」を表示します。
      - キー押下で占い結果が表示されるよう、コールバックを登録します。
      - ユーザーがキーを押すまでループで待機します。
    """
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    global w, h  # キーサイズ（グローバル変数として利用）
    key_format = deck.key_image_format()
    w, h = key_format["size"]

    # 初期画像として「Omikuji」を表示
    init_img = create_text_image("占い", w, h, font_size=30)
    native_init = PILHelper.to_native_format(deck, init_img)
    deck.set_key_image(0, native_init)

    deck.set_key_callback(key_callback)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()

if __name__ == "__main__":
    main()
