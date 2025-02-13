#!/usr/bin/env python3
import time
import qrcode
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image
from StreamDeck.ImageHelpers import PILHelper

url = "https://www.example.com"

deck = DeviceManager().enumerate()[0]
deck.open()
deck.reset()

key_format = deck.key_image_format()
w, h = key_format["size"]

qr = qrcode.QRCode(border=1)
qr.add_data(url)
qr.make(fit=True)
img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((w, h))

deck.set_key_image(0, PILHelper.to_native_format(deck, img_qr))
time.sleep(5)
deck.reset()
deck.close()
