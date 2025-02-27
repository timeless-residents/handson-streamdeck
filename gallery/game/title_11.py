#!/usr/bin/env python3
"""
落ちものパズル
Stream Deck を利用した簡易版テトリス風ゲーム

【操作方法】
- ゲーム画面は 4×4 グリッドで遊ぶシンプルな落ちものパズルです。
- 上部からブロック（🟥🟦🟩🟨）がランダムに落ちてきます。
- 矢印キー（キー 4, 5）で左右に移動、スペースキー（キー 13）で回転します。
- 横一列が揃うと消えて得点が入ります。
- 積み上がったブロックが上端に達するとゲームオーバーです。
- リセットキー（キー 31）でゲームをいつでも初期化できます。
"""

import time
import io
import random

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
LEFT_KEY = 4      # 左移動
RIGHT_KEY = 5     # 右移動
ROTATE_KEY = 13   # 回転（スペースキー）
RESET_KEY = 31    # ゲームリセット

# ブロックの色とテキスト表現
BLOCK_TYPES = [
    ("🟥", (255, 0, 0)),     # 赤
    ("🟦", (0, 0, 255)),     # 青
    ("🟩", (0, 255, 0)),     # 緑
    ("🟨", (255, 255, 0)),   # 黄
]

# --- ゲーム状態のグローバル変数 ---
game_board = []           # ゲームボード
current_block = None      # 現在操作中のブロックの種類
current_pos = [0, 0]      # 操作中ブロックの座標 [行, 列]
game_active = True        # ゲーム進行中フラグ
score = 0                 # スコア

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
    global game_board, current_block, current_pos, game_active, score, last_update_time, last_key_state
    # 空のゲームボードを作成（4×4）
    game_board = [[None for _ in range(4)] for _ in range(4)]
    # 新しいブロックを生成
    spawn_new_block()
    game_active = True
    score = 0
    last_update_time = time.time()
    last_key_state = {}


# --- 新しいブロックの生成 ---
def spawn_new_block() -> None:
    global current_block, current_pos
    # ランダムなブロックタイプを選択
    current_block = random.choice(BLOCK_TYPES)
    # 最上段の中央から開始
    current_pos = [0, 1]


# --- ブロックの移動 ---
def move_block(direction):
    global current_pos
    new_pos = current_pos.copy()
    
    if direction == "left":
        new_pos[1] = max(0, current_pos[1] - 1)
    elif direction == "right":
        new_pos[1] = min(3, current_pos[1] + 1)
    
    # 移動先が空いているか確認
    if is_valid_position(new_pos):
        current_pos = new_pos
        return True
    return False


# --- ブロックの回転（簡易実装、回転による変形なし） ---
def rotate_block():
    # この単純なバージョンでは回転効果はありません（ただ見栄えのため）
    return True


# --- 位置の有効性チェック ---
def is_valid_position(pos):
    row, col = pos
    # 範囲内かチェック
    if not (0 <= row < 4 and 0 <= col < 4):
        return False
    # 既存ブロックとの衝突チェック
    if game_board[row][col] is not None:
        return False
    return True


# --- ブロックの固定 ---
def lock_block():
    global game_board, current_block
    row, col = current_pos
    game_board[row][col] = current_block
    # ライン消去チェック
    check_lines()
    # ゲームオーバーチェック
    if check_game_over():
        return
    # 新しいブロックを生成
    spawn_new_block()


# --- ラインが揃ったかチェック ---
def check_lines():
    global game_board, score
    for row in range(4):
        if all(cell is not None for cell in game_board[row]):
            # ラインが揃った場合、その行を削除
            score += 10
            # 上の行を全て1つ下に移動
            for r in range(row, 0, -1):
                game_board[r] = game_board[r-1].copy()
            # 最上段は空に
            game_board[0] = [None for _ in range(4)]


# --- ゲームオーバーチェック ---
def check_game_over():
    global game_active
    # 最上段にブロックがあればゲームオーバー
    if any(cell is not None for cell in game_board[0]):
        game_active = False
        return True
    return False


# --- ゲーム状態更新 ---
def update_game_state() -> None:
    global last_update_time, current_pos
    if not game_active:
        return
        
    current_time = time.time()
    if current_time - last_update_time >= update_interval:
        last_update_time = current_time
        
        # ブロックを下に移動
        new_pos = [current_pos[0] + 1, current_pos[1]]
        
        # 移動先が有効なら移動
        if current_pos[0] < 3 and is_valid_position(new_pos):
            current_pos = new_pos
        else:
            # 移動できない場合は固定
            lock_block()


# --- 画面更新 ---
def update_display(deck, key_width: int, key_height: int) -> None:
    # ゲームオーバーの場合は全体に「🔴」を表示
    if not game_active:
        for key in GRID_KEYS.values():
            update_key(deck, key, ("🔴", 40, (0, 0, 0)), key_width, key_height)
        update_key(deck, LEFT_KEY, ("←", 25, (50, 50, 50)), key_width, key_height)
        update_key(deck, RIGHT_KEY, ("→", 25, (50, 50, 50)), key_width, key_height)
        update_key(deck, ROTATE_KEY, ("⟳", 25, (50, 50, 50)), key_width, key_height)
        update_key(
            deck, RESET_KEY, (f"Score:{score}", 15, (255, 0, 0)), key_width, key_height
        )
        return

    # 現在のゲームボードを表示
    for row in range(4):
        for col in range(4):
            key = GRID_KEYS[(row, col)]
            # 固定ブロックの表示
            if game_board[row][col] is not None:
                block_text, block_color = game_board[row][col]
                update_key(deck, key, (block_text, 40, (30, 30, 30)), key_width, key_height)
            # 現在操作中のブロックの表示
            elif row == current_pos[0] and col == current_pos[1]:
                block_text, block_color = current_block
                update_key(deck, key, (block_text, 40, (30, 30, 30)), key_width, key_height)
            # 空マスの表示
            else:
                update_key(deck, key, ("", 40, (0, 0, 0)), key_width, key_height)

    # 操作キーの更新
    update_key(deck, LEFT_KEY, ("←", 25, (0, 0, 0)), key_width, key_height)
    update_key(deck, RIGHT_KEY, ("→", 25, (0, 0, 0)), key_width, key_height)
    update_key(deck, ROTATE_KEY, ("⟳", 25, (255, 165, 0)), key_width, key_height)
    update_key(deck, RESET_KEY, (f"Score:{score}", 15, (255, 69, 0)), key_width, key_height)


# --- キー操作コールバック ---
def key_callback(deck, key, state_pressed) -> None:
    global game_active
    if not state_pressed:
        return
        
    # リセットキーでゲーム初期化
    if key == RESET_KEY:
        init_game()
        update_display(deck, w, h)
        return
        
    # ゲームが終了していたら操作を受け付けない
    if not game_active:
        return
        
    # 左移動
    if key == LEFT_KEY:
        move_block("left")
        update_display(deck, w, h)
        return
        
    # 右移動
    if key == RIGHT_KEY:
        move_block("right")
        update_display(deck, w, h)
        return
        
    # 回転
    if key == ROTATE_KEY:
        rotate_block()
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