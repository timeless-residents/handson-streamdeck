#!/usr/bin/env python3
"""
パイソンのくねくね脱出
STREAM DECK 用ゲーム例

【操作方法】
・ゲーム盤は 4×4 のグリッド（キー: 
    Row0: 0,1,2,3; 
    Row1: 8,9,10,11;
    Row2: 16,17,18,19;
    Row3: 24,25,26,27）
  で表示します。
・プレイ可能エリアは盤面の中央2列（列1,2）で、左右端（列0,3）は壁として描画します。
・蛇（🐍）は下段（初期位置：(3,1)）から上方向へ自動移動します。
・操作キーは以下の通り：
    ・左操作：キー 4　←　（現在の進行列が 2 なら 1 へ切替）
    ・右操作：キー 5　→　（現在の進行列が 1 なら 2 へ切替）
    ・ドアオープン：キー 6　（蛇のヘッドが上段（row0）に到達しているとき押すとドアが開き、クリア）
    ・リセット：キー 31　（ゲーム状態を初期化）
"""

import time
import io

import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

import cairo
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# --- キー定義 ---
# ゲーム盤（4x4グリッド）に対応するキー番号
MEMORY_KEYS = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27]

# 各グリッド位置のキー番号マッピング（row, col）→ key
GRID_KEYS = {
    (0, 0): 0,
    (0, 1): 1,
    (0, 2): 2,
    (0, 3): 3,
    (1, 0): 8,
    (1, 1): 9,
    (1, 2): 10,
    (1, 3): 11,
    (2, 0): 16,
    (2, 1): 17,
    (2, 2): 18,
    (2, 3): 19,
    (3, 0): 24,
    (3, 1): 25,
    (3, 2): 26,
    (3, 3): 27,
}

# 操作キー（表示領域外）
LEFT_KEY = 4  # 左操作
RIGHT_KEY = 5  # 右操作
OPEN_KEY = 13  # ドアオープン（スペース相当）
RESET_KEY = 31  # ゲームリセット

# --- ゲーム状態のグローバル変数 ---
# ゲーム盤は 4x4、ただしプレイ可能は中央2列（col1, col2）。
# 外枠（col0, col3）は壁として描画します。
snake_body = []  # (row, col) のリスト。末尾がヘッド
next_col = 1  # 現在の進行予定の列（1 または 2）
door_open = False
game_over = False
win = False

# 自動移動の更新間隔（秒）
update_interval = 1.0
last_update_time = 0

# 差分更新用キャッシュ（key 番号 → (text, font_size, background_color)）
last_key_state = {}


# --- 画像生成ヘルパー ---
def create_text_image(
    text: str,
    width: int,
    height: int,
    font_size: int = 40,
    text_color: tuple = (255, 255, 255),
    background_color: tuple = (0, 0, 0),
) -> Image.Image:
    """
    Cairo / PangoCairo を利用してテキスト（絵文字含む）を中央配置した画像を生成します。
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    # 背景塗り
    r_bg, g_bg, b_bg = (c / 255 for c in background_color)
    ctx.set_source_rgb(r_bg, g_bg, b_bg)
    ctx.paint()
    # テキストレイアウト
    layout = PangoCairo.create_layout(ctx)
    layout.set_text(text, -1)
    font_desc = Pango.FontDescription(f"Apple Color Emoji {font_size}")
    layout.set_font_description(font_desc)
    r_text, g_text, b_text = (c / 255 for c in (255, 255, 255))
    ctx.set_source_rgb(r_text, g_text, b_text)
    _, logical_rect = layout.get_pixel_extents()
    x = (width - logical_rect.width) // 2 - logical_rect.x
    y = (height - logical_rect.height) // 2 - logical_rect.y
    ctx.move_to(x, y)
    PangoCairo.show_layout(ctx, layout)
    output = io.BytesIO()
    surface.write_to_png(output)
    output.seek(0)
    return Image.open(output)


# --- 差分更新用ヘルパー ---
def update_key(deck, key, new_state, key_width, key_height):
    """
    指定の key に対し、新しい状態 new_state が前回と異なる場合のみ再描画します。
    new_state: (text, font_size, background_color)
    """
    global last_key_state
    if last_key_state.get(key) == new_state:
        return  # 状態が変わっていないため、更新不要
    text, font_size, background_color = new_state
    img = create_text_image(
        text,
        key_width,
        key_height,
        font_size=font_size,
        background_color=background_color,
    )
    deck.set_key_image(key, PILHelper.to_native_format(deck, img))
    last_key_state[key] = new_state


# --- ゲーム初期化 ---
def init_game() -> None:
    global snake_body, next_col, door_open, game_over, win, last_update_time, last_key_state
    # 蛇の初期位置：下段、プレイ可能領域の左側（row 3, col 1）
    snake_body = [(3, 1)]
    next_col = 1
    door_open = False
    game_over = False
    win = False
    last_update_time = time.time()
    # キャッシュもクリア
    last_key_state = {}


# --- ゲーム状態更新 ---
def update_game_state() -> None:
    global snake_body, next_col, game_over, win, door_open, last_update_time
    if game_over or win:
        return
    current_time = time.time()
    head_row, head_col = snake_body[-1]
    # ヘッドが既に上段（row 0）に到達している場合は自動更新せずドアオープン待ち
    if head_row == 0:
        return
    if current_time - last_update_time >= update_interval:
        last_update_time = current_time
        new_row = head_row - 1
        new_col = next_col
        # プレイ可能領域は col 1～2 以外は壁との衝突
        if new_col not in (1, 2):
            game_over = True
            return
        if new_row < 0:
            # もしドアが開いていれば勝利、それ以外はゲームオーバー
            if door_open:
                win = True
            else:
                game_over = True
            return
        snake_body.append((new_row, new_col))


# --- 画面更新 ---
def update_display(deck, key_width: int, key_height: int) -> None:
    # ゲーム盤全体の再描画（差分更新）
    if game_over:
        for key in GRID_KEYS.values():
            update_key(deck, key, ("💀", 40, (255, 0, 0)), key_width, key_height)
        # 操作キーも更新
        update_key(deck, LEFT_KEY, ("←", 40, (0, 0, 0)), key_width, key_height)
        update_key(deck, RIGHT_KEY, ("→", 40, (0, 0, 0)), key_width, key_height)
        update_key(deck, OPEN_KEY, ("Open", 30, (255, 165, 0)), key_width, key_height)
        update_key(deck, RESET_KEY, ("Reset", 30, (255, 69, 0)), key_width, key_height)
        return

    if win:
        for key in GRID_KEYS.values():
            update_key(deck, key, ("🎉", 40, (0, 128, 0)), key_width, key_height)
        update_key(deck, LEFT_KEY, ("←", 40, (0, 0, 0)), key_width, key_height)
        update_key(deck, RIGHT_KEY, ("→", 40, (0, 0, 0)), key_width, key_height)
        update_key(deck, OPEN_KEY, ("Open", 30, (255, 165, 0)), key_width, key_height)
        update_key(deck, RESET_KEY, ("Reset", 30, (255, 69, 0)), key_width, key_height)
        return

    # 通常のゲーム盤描画
    for row in range(4):
        for col in range(4):
            key = GRID_KEYS[(row, col)]
            # 外枠（col0, col3）は壁
            if col == 0 or col == 3:
                new_state = ("█", 40, (100, 100, 100))
            # ドアエリア：ここでは (0,1) をドアとする
            elif row == 0 and col == 2:
                if door_open:
                    new_state = ("🚪", 40, (0, 128, 0))
                else:
                    new_state = ("🚪", 40, (0, 0, 255))
            else:
                # 中央セル：蛇があるか？
                if (row, col) in snake_body:
                    if (row, col) == snake_body[-1]:
                        new_state = ("🐍", 40, (255, 0, 0))  # ヘッド
                    else:
                        new_state = ("🐍", 40, (0, 255, 0))
                else:
                    new_state = ("", 40, (200, 200, 200))
            update_key(deck, key, new_state, key_width, key_height)

    # 操作キーの更新
    update_key(deck, LEFT_KEY, ("←", 40, (0, 0, 0)), key_width, key_height)
    update_key(deck, RIGHT_KEY, ("→", 40, (0, 0, 0)), key_width, key_height)
    update_key(deck, OPEN_KEY, ("Open", 30, (255, 165, 0)), key_width, key_height)
    update_key(deck, RESET_KEY, ("Reset", 30, (255, 69, 0)), key_width, key_height)


# --- キー操作コールバック ---
def key_callback(deck, key, state_pressed) -> None:
    global next_col, door_open, win
    if not state_pressed:
        return
    # リセットキー
    if key == RESET_KEY:
        init_game()
        update_display(deck, w, h)
        return
    # 左操作キー
    if key == LEFT_KEY:
        if next_col == 2:
            next_col = 1
        update_display(deck, w, h)
        return
    # 右操作キー
    if key == RIGHT_KEY:
        if next_col == 1:
            next_col = 2
        update_display(deck, w, h)
        return
    # ドアオープンキー
    if key == OPEN_KEY:
        head_row, head_col = snake_body[-1]
        if head_row == 0:
            door_open = True
            # ヘッドがドアセル (0,1) にある場合は勝利
            if (head_row, head_col) == (0, 2):
                win = True
        update_display(deck, w, h)
        return


# --- メインループ ---
def main() -> None:
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()
    global w, h
    key_format = deck.key_image_format()
    w, h = key_format["size"]

    init_game()
    update_display(deck, w, h)
    deck.set_key_callback(key_callback)

    try:
        while True:
            update_game_state()
            update_display(deck, w, h)
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    main()
