#!/usr/bin/env python3
import time
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

def draw_chessboard():
    image = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    num_squares = 4
    square_w = w // num_squares
    square_h = h // num_squares
    for i in range(num_squares):
        for j in range(num_squares):
            if (i + j) % 2 == 0:
                draw.rectangle([i * square_w, j * square_h, (i + 1) * square_w, (j + 1) * square_h], fill=(0, 0, 0))
    return image

deck.set_key_image(0, PILHelper.to_native_format(deck, draw_chessboard()))
time.sleep(5)
deck.reset()
deck.close()
