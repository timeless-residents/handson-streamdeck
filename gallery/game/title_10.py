#!/usr/bin/env python3
"""
トビウオのグライド競争
矢印キーで海面を飛び出し、スペースキーで空中滑空して遠くまで飛ぶゲーム例

【操作方法】
- ゲーム画面は 4×4 グリッドで、下段 (row3) が海面（🌊）として描画されます。
- 初期状態では魚（🐟）は海中（水面上）にいます。
- 矢印キー（ここではキー 4 および 5）を押すとジャンプ開始し、魚は最大高度（3）から飛び出します。
- 更新ごとに魚は自動で前進し（水平距離が増加）、重力により高度が 1 ずつ低下します。
- 空中にいる間、スペースキー（キー 13）を押すとグライド状態となり、高度低下が抑えられます。
- 魚が海面（高度 0）に落下するとゲームオーバー。得点は進んだ距離（fish_x）です。
- リセットキー（キー 31）でゲームを初期化します。
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
# ゲーム盤（4×4グリッド）のキー番号
MEMORY_KEYS = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27]

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

# 操作キー
JUMP_KEYS = [4, 5]  # 矢印キーとしてジャンプ開始に使用
GLIDE_KEY = 13  # スペースキーとしてグライド操作に使用
RESET_KEY = 31  # ゲームリセット

# --- ゲーム状態のグローバル変数 ---
# fish_x: 水平距離（進行状況）; fish_alt: 高度（0:海面、1〜3:空中の高さ）
fish_x = 0
fish_alt = 0  # 0 = 海面、3 = 最高高度
game_active = False  # ゲーム中かどうか（ジャンプ後は True）
glide_flag = False  # 現在の更新でグライド操作が有効かどうか

# 自動更新の間隔（秒）
update_interval = 0.5
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
    r_text, g_text, b_text = (c / 255 for c in text_color)
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
    指定キーの表示状態が前回と異なる場合のみ再描画します。
    new_state: (text, font_size, background_color)
    """
    global last_key_state
    if last_key_state.get(key) == new_state:
        return  # 変化がなければ更新不要
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
    global fish_x, fish_alt, game_active, glide_flag, last_update_time, last_key_state
    fish_x = 0
    fish_alt = 0
    game_active = False
    glide_flag = False
    last_update_time = time.time()
    last_key_state = {}


# --- ゲーム状態更新 ---
def update_game_state() -> None:
    global fish_x, fish_alt, game_active, glide_flag, last_update_time
    if not game_active:
        return
    current_time = time.time()
    if current_time - last_update_time >= update_interval:
        last_update_time = current_time
        fish_x += 1  # 前進
        # グライド操作がなければ高度低下（重力）
        if not glide_flag:
            if fish_alt > 0:
                fish_alt -= 1
        # 今回のグライド操作は消費済み
        glide_flag = False
        # 着水（高度 0 になったら）でゲームオーバー
        if fish_alt == 0:
            game_active = False


# --- 画面更新 ---
def update_display(deck, key_width: int, key_height: int) -> None:
    # ゲームオーバーの場合（ジャンプ後に着水したら）は全体に「💦」を表示
    if not game_active and fish_x > 0:
        for key in GRID_KEYS.values():
            update_key(deck, key, ("💦", 40, (0, 0, 255)), key_width, key_height)
        update_key(deck, JUMP_KEYS[0], ("Jump", 15, (0, 0, 0)), key_width, key_height)
        update_key(deck, GLIDE_KEY, ("Glide", 15, (255, 165, 0)), key_width, key_height)
        update_key(
            deck, RESET_KEY, (f"Score:{fish_x}", 15, (255, 0, 0)), key_width, key_height
        )
        return

    # 通常のゲーム盤描画（水平スクロール表示）
    # 表示するウィンドウの開始 x 座標：魚が右へ進んだら右シフト
    window_start = 0 if fish_x < 2 else fish_x - 1
    # 魚の表示位置（ウィンドウ内の相対座標）
    fish_rel_x = fish_x - window_start
    # 高度に応じた表示行: 高度 3 → row0, 高度 2 → row1, 高度 1 → row2, 0 → row3（海面）
    fish_disp_row = 3 - fish_alt if fish_alt <= 3 else 0

    for row in range(4):
        for col in range(4):
            key = GRID_KEYS[(row, col)]
            # 下段は海面（青）
            if row == 3:
                cell_state = ("🌊", 40, (0, 0, 255))
            else:
                # 空中は青空
                cell_state = ("", 40, (135, 206, 250))
            # 魚の表示位置と一致する場合は魚の絵文字を表示
            if col == fish_rel_x and row == fish_disp_row:
                cell_state = ("🐟", 40, (255, 215, 0))
            update_key(deck, key, cell_state, key_width, key_height)

    # 操作キーの更新
    update_key(deck, JUMP_KEYS[0], ("Jump", 15, (0, 0, 0)), key_width, key_height)
    update_key(deck, JUMP_KEYS[1], ("Jump", 15, (0, 0, 0)), key_width, key_height)
    update_key(deck, GLIDE_KEY, ("Glide", 15, (255, 165, 0)), key_width, key_height)
    update_key(deck, RESET_KEY, ("Reset", 15, (255, 69, 0)), key_width, key_height)


# --- キー操作コールバック ---
def key_callback(deck, key, state_pressed) -> None:
    global game_active, fish_alt, glide_flag, fish_x
    if not state_pressed:
        return
    # リセットキーでゲーム初期化
    if key == RESET_KEY:
        init_game()
        update_display(deck, w, h)
        return
    # ジャンプキー（矢印キー）：ゲーム未開始の場合にジャンプ開始
    if key in JUMP_KEYS:
        if not game_active and fish_x == 0:
            game_active = True
            fish_alt = 3  # 最大高度からスタート
        update_display(deck, w, h)
        return
    # スペースキー（グライド操作）
    if key == GLIDE_KEY:
        if game_active:
            glide_flag = True
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
