#!/usr/bin/env python3
"""
Product-02: StreamDeck Web Server with Enhanced Multiline Update

このスクリプトは、Flask を利用して HTTP リクエストを受け付け、
指定されたキー（複数キー可）にテキストを表示することで、Stream Deck の操作をリモートから実行できるようにします。

例:
http://localhost:5000/update?key=0,1&text=稼働中CPU:%2025%25&font_size=40&fg=0,255,0&bg=0,0,0&max_chars=4

※ テキストが長い場合、改行が自動で挿入され、フォントサイズも調整されて領域内に収まるように処理します。
"""

import threading
import time
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from pilmoji import Pilmoji  # 絵文字描画のための pilmoji

app = Flask(__name__)

# グローバル変数：Stream Deck オブジェクト（後で初期化）
deck = None

# キー更新時の排他制御用ロック
deck_lock = threading.Lock()

def parse_color(color_str: str, default: tuple) -> tuple:
    """ "R,G,B" 形式の文字列をタプル (R, G, B) に変換します。 """
    try:
        parts = color_str.split(',')
        if len(parts) == 3:
            return tuple(int(p) for p in parts)
    except Exception:
        pass
    return default

def auto_wrap_text(text: str, max_chars: int) -> str:
    """
    テキストに改行が含まれていない場合、max_chars ごとに改行を挿入します。
    ※ 日本語の場合は単純に max_chars 文字ごとに改行を入れます。
    """
    if "\n" in text:
        return text  # 既に改行がある場合はそのまま
    wrapped = ""
    for i, ch in enumerate(text):
        wrapped += ch
        if (i + 1) % max_chars == 0 and (i + 1) < len(text):
            wrapped += "\n"
    return wrapped
def create_wrapped_text_image(text: str, width: int, height: int, initial_font_size: int = 40,
                              text_color: tuple = (255, 255, 255),
                              background_color: tuple = (0, 0, 0), spacing: int = 4,
                              max_chars: int = 4) -> Image.Image:
    """
    指定テキストを中央に表示する画像を生成します。
    改行がない場合、max_chars ごとに自動で改行を挿入し、
    領域内に収まるようにフォントサイズを調整します。
    pilmoji を利用して、日本語と絵文字の両方をサポートします。
    """
    text = auto_wrap_text(text, max_chars)
    font_size = initial_font_size

    # 絵文字の描画用フォールバックフォント（macOS の場合）
    emoji_font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"

    while font_size > 10:
        image = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(image)
        try:
            # 日本語表示に適したフォントとして、ヒラギノ角ゴシックを使用
            font = ImageFont.truetype(r"/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", font_size)
        except IOError:
            font = ImageFont.load_default()

        # テキストサイズの測定
        try:
            bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
        except AttributeError:
            bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if text_width <= width and text_height <= height:
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            # pilmoji を用いて日本語と絵文字を同時に描画
            with Pilmoji(image) as pilmoji:
                # fallback_fonts をインスタンス生成後に設定
                pilmoji.fallback_fonts = [emoji_font_path]
                pilmoji.text((x, y), text, font=font, fill=text_color, spacing=spacing, align="center")
            return image
        font_size -= 2

    return image


@app.route("/update", methods=["GET"])
def update_key():
    """
    /update エンドポイント:
    クエリパラメーター key, text, font_size, fg, bg, max_chars を受け取り、
    指定されたキーにテキストを表示します。
    
    複数キーはカンマ区切りで指定可能（例: key=0,1,2）。
    """
    global deck
    try:
        key_param = request.args.get("key")
        if not key_param:
            raise ValueError("key parameter is required")
        # 複数キーの場合、カンマ区切りでリストに変換
        keys = [int(k.strip()) for k in key_param.split(",") if k.strip().isdigit()]
        text = request.args.get("text", "")
        font_size = int(request.args.get("font_size", "40"))
        fg_str = request.args.get("fg", "255,255,255")
        bg_str = request.args.get("bg", "0,0,0")
        max_chars = int(request.args.get("max_chars", "4"))
        fg = parse_color(fg_str, (255, 255, 255))
        bg = parse_color(bg_str, (0, 0, 0))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    key_format = deck.key_image_format()
    width, height = key_format["size"]

    # 生成する画像を作成
    img = create_wrapped_text_image(text, width, height, initial_font_size=font_size,
                                    text_color=fg, background_color=bg, max_chars=max_chars)
    native_img = PILHelper.to_native_format(deck, img)
    with deck_lock:
        for key in keys:
            deck.set_key_image(key, native_img)

    print(f"Updated keys {keys} with text: {text}")
    return jsonify({"status": "ok", "keys": keys, "text": text, "font_size": font_size, "fg": fg, "bg": bg, "max_chars": max_chars})


def run_flask_server():
    app.run(host="0.0.0.0", port=5000)


def main() -> None:
    """
    メイン関数:
      - Stream Deck を初期化し、キーサイズを取得します。
      - Flask サーバーを別スレッドで起動し、HTTP リクエストを待ち受けます。
      - メインループは単に待機し、Ctrl+C で終了します。
    """
    global deck
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.reset()

    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()

    print("Stream Deck Web Server is running on localhost:5000. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    main()
