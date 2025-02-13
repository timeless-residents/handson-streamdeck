#!/usr/bin/env python3
import time, datetime
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper
import os

def greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "おはよう"
    elif hour < 18:
        return "こんにちは"
    else:
        return "こんばんは"

def draw_text(text):
    # Create a new black image
    image = Image.new("RGB", (w, h), color=(0, 30, 60))
    draw = ImageDraw.Draw(image)
    
    # Try to load a Japanese font
    try:
        # Try different common Japanese font paths
        font_paths = [
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",  # Debian/Ubuntu
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Newer systems
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS
            "C:\\Windows\\Fonts\\msgothic.ttc",  # Windows
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Some Linux
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 24)  # Smaller font size for full text
                break
                
        if font is None:
            # Fallback to default font if no Japanese fonts found
            font = ImageFont.load_default()
            print("Warning: No Japanese font found. Text may not display correctly.")
    
    except Exception as e:
        print(f"Font loading error: {e}")
        font = ImageFont.load_default()
    
    # Get text size for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    
    # Add some padding and draw text centered
    padding = 4
    if (tw + padding * 2) > w:
        # If text is too wide, reduce font size
        scale_factor = (w - padding * 2) / tw
        font_size = int(font.size * scale_factor)
        font = ImageFont.truetype(font.path, font_size)
        # Recalculate text size with new font
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    
    # Draw text centered with padding
    draw.text(
        ((w-tw)//2, (h-th)//2),
        text,
        fill=(255, 255, 0),  # Yellow text
        font=font
    )
    
    return image

# Initialize Stream Deck
deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

print("Stream Deck initialized. Press Ctrl+C to exit.")

try:
    while True:
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_text(greeting())))
        time.sleep(60)
except KeyboardInterrupt:
    print("\nShutting down...")
    deck.reset()
    deck.close()
except Exception as e:
    print(f"Error: {e}")
    deck.reset()
    deck.close()