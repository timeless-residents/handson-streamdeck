#!/usr/bin/env python3
import time, os
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

todo_file = "assets/todo.txt"  # タスク一覧のテキストファイル

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def get_todo_count():
    if not os.path.exists(todo_file):
        return 0
    with open(todo_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        count = len([line for line in lines if line.strip() != ""])
    return count

def draw_todo(count):
    text = f"ToDo: {count}"
    image = Image.new("RGB", (w, h), color=(10,10,50))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(255,255,0), font=font)
    return image

try:
    while True:
        count = get_todo_count()
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_todo(count)))
        time.sleep(5)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
