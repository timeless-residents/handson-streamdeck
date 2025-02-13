#!/usr/bin/env python3
import gi, cairo
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
from PIL import Image
import sys

def generate_emoji_image(emoji, output_filename, width=200, height=200, pointsize=120):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)  # type: ignore
    ctx = cairo.Context(surface)  # type: ignore

    # 白背景で塗りつぶし
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()

    layout = PangoCairo.create_layout(ctx)
    layout.set_text(emoji, -1)
    # Apple Color Emoji フォントを利用（PangoCairo ならうまくレンダリングできるはず）
    font_desc = Pango.FontDescription(f"Apple Color Emoji {pointsize}")
    layout.set_font_description(font_desc)

    _, logical_rect = layout.get_pixel_extents()
    x = (width - logical_rect.width) // 2 - 20
    y = (height - logical_rect.height) // 2 + 4
    ctx.move_to(x, y)
    PangoCairo.show_layout(ctx, layout)

    surface.write_to_png(output_filename)

if __name__ == "__main__":
    emojis = {
        "cherry": "🍒",
        "lemon": "🍋",
        "orange": "🍊",
        "grape": "🍇",
        "star": "⭐",
        "diamond": "💎"
    }
    for name, emoji in emojis.items():
        output = f"assets/slot_images/{name}.png"
        generate_emoji_image(emoji, output)
        print(f"Generated {output}")
