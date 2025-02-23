#!/usr/bin/env python3
"""
Memory Match Challenge:
Stream Deck XL 用のシンプルな神経衰弱ゲームです。

4x4 のグリッド（使用するキー: 
  Row 0: 0,1,2,3; 
  Row 1: 8,9,10,11; 
  Row 2: 16,17,18,19; 
  Row 3: 24,25,26,27）に野菜の絵文字カードを配置します。
各カードは、8種類の野菜絵文字のペアとなっており、カードが伏せられている状態は「❓」で表示されます。
RESET_KEY (キー 31) を押すとゲームをリセットします。
"""

import time
import random
import io

import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

import cairo
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# 使用するキー番号の定義（4x4 グリッド）
MEMORY_KEYS = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27]
RESET_KEY = 31  # リセットボタン（グリッド外のキー）

# カードシンボル（8種類の野菜絵文字、各2枚ずつ）
CARD_SYMBOLS = ["🥕", "🥦", "🍅", "🥬", "🥑", "🍆", "🌽", "🥔"]

# ゲーム状態のグローバル変数
memory_cards = {}  # MEMORY_KEYS -> カードシンボルの割り当て
flipped_cards = []  # 現在表向きのカードのキー番号（最大2枚）
solved_cards = set()  # 既に一致したカードのキー番号
selection_count = 0  # 選択回数のカウンター
COUNTER_KEY = 7  # カウンター表示用のキー


def create_text_image(
    text: str,
    width: int,
    height: int,
    font_size: int = 40,
    text_color: tuple = (255, 255, 255),
    background_color: tuple = (0, 0, 0),
) -> Image.Image:
    """
    Cairo と PangoCairo を利用してテキスト（絵文字）を中央配置した PIL Image を生成します。

    Args:
        text (str): 表示するテキスト（絵文字を含む）。
        width (int): 画像の幅。
        height (int): 画像の高さ。
        font_size (int): フォントサイズ。
        text_color (tuple): テキストカラー (R, G, B)。
        background_color (tuple): 背景色 (R, G, B)。

    Returns:
        Image.Image: 生成された画像。
    """
    # Cairo のイメージサーフェスを作成
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # 背景色を塗りつぶし（RGB値を 0-1 に変換）
    r_bg, g_bg, b_bg = tuple(c / 255 for c in background_color)
    ctx.set_source_rgb(r_bg, g_bg, b_bg)
    ctx.paint()

    # Pango レイアウトを作成し、テキストを設定
    layout = PangoCairo.create_layout(ctx)
    layout.set_text(text, -1)
    # Apple Color Emoji フォントで指定（Mac環境ならカラー絵文字をレンダリング）
    font_desc = Pango.FontDescription(f"Apple Color Emoji {font_size}")
    layout.set_font_description(font_desc)

    # テキストカラーの設定（RGBを 0-1 に変換）
    r_text, g_text, b_text = tuple(c / 255 for c in text_color)
    ctx.set_source_rgb(r_text, g_text, b_text)

    # テキストのサイズを取得して中央に配置
    _, logical_rect = layout.get_pixel_extents()
    x = (width - logical_rect.width) // 2 - logical_rect.x
    y = (height - logical_rect.height) // 2 - logical_rect.y
    ctx.move_to(x, y)
    PangoCairo.show_layout(ctx, layout)

    # Cairo サーフェスの内容を PNG バイトデータに変換し、PIL Image として読み込む
    output = io.BytesIO()
    surface.write_to_png(output)
    output.seek(0)
    image = Image.open(output)
    return image


def init_memory_cards() -> None:
    """
    MEMORY_KEYS にランダムなカード割り当てを行い、グローバル変数を初期化します.
    """
    global memory_cards, flipped_cards, solved_cards, selection_count
    deck_cards = CARD_SYMBOLS * 2  # 16 枚 (8ペア)
    random.shuffle(deck_cards)
    memory_cards = {key: deck_cards[i] for i, key in enumerate(MEMORY_KEYS)}
    flipped_cards = []
    solved_cards = set()
    selection_count = 0


def update_counter_display(deck, key_width: int, key_height: int) -> None:
    """
    選択回数カウンターを表示します.
    """
    counter_img = create_text_image(
        f"{selection_count}回",
        key_width,
        key_height,
        font_size=30,
        background_color=(70, 130, 180),  # スチールブルー
    )
    deck.set_key_image(COUNTER_KEY, PILHelper.to_native_format(deck, counter_img))


def update_memory_board(deck, key_width: int, key_height: int) -> None:
    """
    MEMORY_KEYS の状態に合わせて、各キーにカードの内容を表示します.

    - カードが伏せられている場合は「❓」を表示（背景はライトグレー）。
    - カードが表向き（flipped または solved）の場合は実際の野菜絵文字を表示（背景は黒）。
    - RESET_KEY には「Reset」をオレンジレッド背景で表示します.
    """
    global memory_cards, flipped_cards, solved_cards
    for key in MEMORY_KEYS:
        if key in flipped_cards or key in solved_cards:
            symbol = memory_cards[key]
        else:
            symbol = "❓"
        bg_color = (
            (0, 0, 0) if symbol != "❓" else (173, 216, 230)
        )  # 黒 or ライトブルー
        img = create_text_image(
            symbol, key_width, key_height, font_size=50, background_color=bg_color
        )
        deck.set_key_image(key, PILHelper.to_native_format(deck, img))
    # RESET_KEY 表示（オレンジレッド背景）
    reset_img = create_text_image(
        "Reset", key_width, key_height, font_size=30, background_color=(255, 69, 0)
    )
    deck.set_key_image(RESET_KEY, PILHelper.to_native_format(deck, reset_img))
    update_counter_display(deck, key_width, key_height)


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
    global memory_cards, flipped_cards, solved_cards, selection_count
    if not state_pressed:
        return
    if key == RESET_KEY:
        init_memory_cards()
        update_memory_board(deck, w, h)
        return
    if key in MEMORY_KEYS and key not in flipped_cards and key not in solved_cards:
        selection_count += 1
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
                        img = create_text_image(
                            "🎉", w, h, font_size=50, background_color=(0, 128, 0)
                        )
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
