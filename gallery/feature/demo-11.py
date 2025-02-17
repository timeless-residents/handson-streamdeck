#!/usr/bin/env python3
import time
import datetime
import os
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper


def greeting():
    """現在の時刻に応じた日本語の挨拶を返す"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "おはよう"
    elif hour < 18:
        return "こんにちは"
    else:
        return "こんばんは"


def create_full_image(message, width, height):
    """
    幅width、高さheightの全体画像を生成し、
    中央にmessageを描画して返す
    """
    # 背景色を暗めの青色に設定
    image = Image.new("RGB", (width, height), color=(0, 30, 60))
    draw = ImageDraw.Draw(image)

    # 日本語フォントをロード（環境に合わせてパスを指定）
    try:
        font_paths = [
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",  # Debian/Ubuntu
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Newer systems
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS
            "C:\\Windows\\Fonts\\msgothic.ttc",  # Windows
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # その他Linux
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(
                    path, 48
                )  # 全体用なので大きめのフォントサイズ
                break
        if font is None:
            font = ImageFont.load_default()
            print(
                "Warning: 日本語フォントが見つかりません。表示が正しくない可能性があります。"
            )
    except Exception as e:
        print(f"フォント読み込みエラー: {e}")
        font = ImageFont.load_default()

    # テキストのサイズを取得して中央に描画
    bbox = draw.textbbox((0, 0), message, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    pos = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(pos, message, fill=(255, 255, 0), font=font)

    return image


def slice_image_to_keys(full_image, rows, cols, key_width, key_height):
    """
    全体画像full_imageをキーサイズ (key_width x key_height) ごとに切り出し、
    キー順（左上→右下、行単位）に並んだリストとして返す。
    """
    key_images = []
    for row in range(rows):
        for col in range(cols):
            left = col * key_width
            upper = row * key_height
            cropped = full_image.crop(
                (left, upper, left + key_width, upper + key_height)
            )
            key_images.append(cropped)
    return key_images


def get_deck_layout(deck):
    """
    接続しているStreamDeckのキー数から、一般的なモデルのレイアウトを推測する。
    ※環境に合わせて適宜変更してください。
    """
    num_keys = deck.key_count()  # メソッドを呼び出してキー数を取得
    if num_keys == 6:
        return 2, 3  # StreamDeck Mini
    elif num_keys == 15:
        return 3, 5  # 標準モデル
    elif num_keys == 32:
        return 4, 8  # StreamDeck XL
    else:
        # キー数からおおよその正方形レイアウトとする
        cols = int(num_keys**0.5)
        rows = (num_keys + cols - 1) // cols
        return rows, cols


# StreamDeckの初期化
streamdecks = DeviceManager().enumerate()
if not streamdecks:
    raise Exception("StreamDeckが見つかりませんでした。")
deck = streamdecks[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
key_width, key_height = key_format["size"]

# キーレイアウト（行数、列数）の取得
rows, cols = get_deck_layout(deck)
full_width = cols * key_width
full_height = rows * key_height

print("StreamDeck全体を1つのキャンバスとして表示します。Ctrl+Cで終了。")

try:
    while True:
        # 挨拶メッセージを取得し、全体画像を作成
        message = greeting()
        full_image = create_full_image(message, full_width, full_height)
        # 全体画像を各キーサイズに分割
        key_images = slice_image_to_keys(full_image, rows, cols, key_width, key_height)

        # 各キーに画像をセット
        for idx, key_img in enumerate(key_images):
            # キー番号が実際のキー数を超えたらbreak
            if idx >= deck.key_count():
                break
            deck.set_key_image(idx, PILHelper.to_native_format(deck, key_img))

        time.sleep(60)  # 1分ごとに更新
except KeyboardInterrupt:
    print("\n終了します...")
finally:
    deck.reset()
    deck.close()
