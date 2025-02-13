#!/usr/bin/env python3
import subprocess
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

def toggle_playpause():
    # Apple Music の再生/一時停止を切り替える AppleScript
    script = 'tell application "Music" to playpause'
    subprocess.run(["osascript", "-e", script])

def draw_label(text):
    image = Image.new("RGB", (w, h), color=(10, 10, 10))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(0,255,0), font=font)
    return image

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        toggle_playpause()
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Toggled")))
        time.sleep(0.5)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Play/Pause")))

deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Play/Pause")))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
