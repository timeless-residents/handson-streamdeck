#!/usr/bin/env python3
"""
System Monitoring Dashboard for Stream Deck XL

このスクリプトは、psutil を使用してシステムの主要なモニタリング項目（CPU使用率、メモリ使用率、ディスク使用率）を取得し、
Stream Deck XL のキー 0, 1, 2 に、2行で情報を表示します。

- キー 0: CPU 使用率 ("CPU:" と使用率)
- キー 1: メモリ 使用率 ("Mem:" と使用率)
- キー 2: ディスク 使用率 ("Disk:" と使用率)

1秒ごとに更新されます。
"""

import time
import psutil

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


def create_multiline_text_image(text: str, width: int, height: int, font_size: int = 40,
                                text_color: tuple = (255, 255, 255),
                                background_color: tuple = (0, 0, 0), spacing: int = 4) -> Image.Image:
    """
    指定したマルチラインテキストを中央に表示する画像を生成します。
    
    Args:
        text (str): 改行で区切られたテキスト。
        width (int): 画像の幅。
        height (int): 画像の高さ。
        font_size (int): フォントサイズ。
        text_color (tuple): テキストカラー (R, G, B)。
        background_color (tuple): 背景色 (R, G, B)。
        spacing (int): 行間のスペース。
    
    Returns:
        Image.Image: 生成された画像。
    """
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)
    try:
        # macOS の場合、日本語も含めた表示に適したフォントのフルパス
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    # Pillow 8.0+ なら multiline_textbbox を利用可能
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    except AttributeError:
        # 古いバージョンの場合は単純に textbbox を利用（改行がうまく計算されない可能性あり）
        bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.multiline_text((x, y), text, fill=text_color, font=font, spacing=spacing, align="center")
    return image


def update_monitor(deck, width: int, height: int) -> None:
    """
    システムのモニタリング情報（CPU、メモリ、ディスク使用率）を取得し、キー 0～2 に2行で表示します。
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    cpu_text = f"CPU:\n{cpu_percent}%"
    mem_text = f"Mem:\n{mem.percent}%"
    disk_text = f"Disk:\n{disk.percent}%"

    cpu_img = create_multiline_text_image(cpu_text, width, height, font_size=20, background_color=(0, 0, 128))
    mem_img = create_multiline_text_image(mem_text, width, height, font_size=20, background_color=(0, 128, 0))
    disk_img = create_multiline_text_image(disk_text, width, height, font_size=20, background_color=(128, 0, 0))

    deck.set_key_image(0, PILHelper.to_native_format(deck, cpu_img))
    deck.set_key_image(1, PILHelper.to_native_format(deck, mem_img))
    deck.set_key_image(2, PILHelper.to_native_format(deck, disk_img))


def main() -> None:
    """
    メイン関数:
      - Stream Deck を初期化し、キーサイズを取得します。
      - 1秒ごとにシステムモニタリング情報を更新して、キー 0,1,2 に表示します。
    """
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    key_format = deck.key_image_format()
    width, height = key_format["size"]

    try:
        while True:
            update_monitor(deck, width, height)
            time.sleep(1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    main()
