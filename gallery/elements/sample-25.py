#!/usr/bin/env python3
import time
import random
import math
from dataclasses import dataclass
from typing import Tuple, List
from StreamDeck.DeviceManager import DeviceManager
from PIL import Image, ImageDraw, ImageEnhance
from StreamDeck.ImageHelpers import PILHelper

@dataclass
class WeatherState:
    type: str
    color_primary: Tuple[int, int, int]
    color_secondary: Tuple[int, int, int]
    
class WeatherIcon:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.weather_states = {
            "sunny": WeatherState("sunny", (255, 215, 0), (255, 165, 0)),
            "cloudy": WeatherState("cloudy", (200, 200, 200), (150, 150, 150)),
            "rainy": WeatherState("rainy", (180, 180, 180), (0, 0, 255))
        }
        
    def create_base_image(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("RGB", (self.width, self.height), color=(0, 0, 0))
        return image, ImageDraw.Draw(image)
    
    def draw_sunny(self, draw: ImageDraw.ImageDraw) -> None:
        # メインの太陽
        center_x, center_y = self.width // 2, self.height // 2
        radius = min(self.width, self.height) // 3
        draw.ellipse(
            [(center_x - radius, center_y - radius),
             (center_x + radius, center_y + radius)],
            fill=self.weather_states["sunny"].color_primary
        )
        
        # 光線効果
        for i in range(8):
            angle = math.radians(i * 45)
            ray_length = radius * 1.2
            x1 = center_x + int(radius * math.cos(angle))
            y1 = center_y + int(radius * math.sin(angle))
            x2 = center_x + int(ray_length * math.cos(angle))
            y2 = center_y + int(ray_length * math.sin(angle))
            draw.line([(x1, y1), (x2, y2)],
                     fill=self.weather_states["sunny"].color_secondary,
                     width=2)
    
    def draw_cloud(self, draw: ImageDraw.ImageDraw,
                  color: Tuple[int, int, int],
                  offset_x: int = 0, offset_y: int = 0) -> None:
        # 雲を複数の楕円で構成
        base_color = color
        highlight_color = tuple(min(255, c + 20) for c in color)
        shadow_color = tuple(max(0, c - 20) for c in color)
        
        # 雲の中心位置
        center_x = offset_x + self.width // 2
        center_y = offset_y + self.height // 2
        
        # ベースとなる大きな楕円
        draw.ellipse(
            [(center_x - 25, center_y - 10),
             (center_x + 25, center_y + 10)],
            fill=base_color
        )
        
        # 上部の小さな楕円群
        cloud_parts = [
            # (x_offset, y_offset, width, height, color)
            (-20, -5, 20, 15, highlight_color),
            (0, -8, 25, 15, highlight_color),
            (15, -3, 20, 15, base_color),
        ]
        
        for x_off, y_off, w, h, c in cloud_parts:
            draw.ellipse(
                [(center_x + x_off, center_y + y_off),
                 (center_x + x_off + w, center_y + y_off + h)],
                fill=c
            )
            
        # 下部の影となる部分
        shadow_parts = [
            (-15, 5, 25, 15),
            (5, 8, 20, 12),
        ]
        
        for x_off, y_off, w, h in shadow_parts:
            draw.ellipse(
                [(center_x + x_off, center_y + y_off),
                 (center_x + x_off + w, center_y + y_off + h)],
                fill=shadow_color
            )
    
    def draw_rain(self, draw: ImageDraw.ImageDraw, start_y: int) -> None:
        rain_color = self.weather_states["rainy"].color_secondary
        drops = 5
        spacing = self.width // (drops + 1)
        
        for i in range(drops):
            x = spacing * (i + 1)
            draw.line(
                [(x, start_y), (x - 3, start_y + 10)],
                fill=rain_color,
                width=2
            )
    
    def draw_weather(self, weather_type: str) -> Image.Image:
        image, draw = self.create_base_image()
        
        if weather_type == "sunny":
            self.draw_sunny(draw)
        
        elif weather_type == "cloudy":
            cloud_color = self.weather_states["cloudy"].color_primary
            self.draw_cloud(draw, cloud_color, 0, -5)
            self.draw_cloud(draw, cloud_color, 10, 5)
        
        elif weather_type == "rainy":
            cloud_color = self.weather_states["rainy"].color_primary
            self.draw_cloud(draw, cloud_color, 0, -5)
            self.draw_rain(draw, self.height * 2 // 3)
        
        return image

class StreamDeckWeather:
    def __init__(self):
        self.deck = DeviceManager().enumerate()[0]
        self.deck.open()
        self.deck.reset()
        
        key_format = self.deck.key_image_format()
        self.width, self.height = key_format["size"]
        self.weather_icon = WeatherIcon(self.width, self.height)
        self.current_weather = random.choice(["sunny", "cloudy", "rainy"])
    
    def transition_weather(self, old_type: str, new_type: str, steps: int = 10) -> None:
        old_image = self.weather_icon.draw_weather(old_type)
        new_image = self.weather_icon.draw_weather(new_type)
        
        for i in range(steps + 1):
            alpha = i / steps
            blended = Image.blend(old_image, new_image, alpha)
            self.deck.set_key_image(0, PILHelper.to_native_format(self.deck, blended))
            time.sleep(0.05)
    
    def run(self, iterations: int = 10, interval: float = 1.0) -> None:
        try:
            for _ in range(iterations):
                new_weather = random.choice(["sunny", "cloudy", "rainy"])
                while new_weather == self.current_weather:
                    new_weather = random.choice(["sunny", "cloudy", "rainy"])
                
                self.transition_weather(self.current_weather, new_weather)
                self.current_weather = new_weather
                time.sleep(interval)
        
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        self.deck.reset()
        self.deck.close()

if __name__ == "__main__":
    weather_display = StreamDeckWeather()
    weather_display.run()