#!/usr/bin/env python3
import subprocess, time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

# 実行するカスタムスクリプトのパス（実行権限を付与しておくこと）
script_path = "./scripts/custom_script.sh"

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()
key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_label(text):
    image = Image.new("RGB", (w, h), color=(30,30,30))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((w-tw)//2, (h-th)//2), text, fill=(255,255,255), font=font)
    return image

def key_callback(deck, key, state_pressed):
    if state_pressed and key == 0:
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Running...")))
        try:
            subprocess.run([script_path], check=True)
            deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Done")))
        except subprocess.CalledProcessError:
            deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Error")))
        time.sleep(1)
        deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Run Script")))
        
deck.set_key_callback(key_callback)
deck.set_key_image(0, PILHelper.to_native_format(deck, draw_label("Run Script")))

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    deck.reset()
    deck.close()
