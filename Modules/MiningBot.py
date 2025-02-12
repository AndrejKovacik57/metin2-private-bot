import time
from random import random

import  numpy as np
import cv2
from Utils.Utils import create_low_upp, mouse_left_click, crop_image
from Modules.GameWindow import GameWindow
import random


class MiningBot:
    def __init__(self, mining_config:dict, game_window:GameWindow):
        self.config = mining_config
        self.scan_window_location = None
        self.game_window = game_window
        self.weather = mining_config['weather']
        self.is_mining = False

        self.ore_check_time = 0
        self.ore_check_timer = 22
        self.randomized_ore_time = 0
        self.mining_wait_time_min = 0
        self.mining_wait_time_max = 0

    def load_values(self, scan_window_location, mining_wait_time_min, mining_wait_time_max):
        self.scan_window_location = scan_window_location
        self.mining_wait_time_min = mining_wait_time_min
        self.mining_wait_time_max = mining_wait_time_max

    def mine_ore_old(self, np_image:np.ndarray):
        ore_check_time_diff = time.time() - self.ore_check_time
        np_image_crop = crop_image(np_image, self.scan_window_location)

        ore_x, ore_y, np_image_out = self.__ore_check(np_image_crop)

        if self.mining_wait_time_min != 0 and self.mining_wait_time_max != 0:
            if not self.randomized_ore_time:
                self.randomized_ore_time = random.random() * (self.mining_wait_time_min - self.mining_wait_time_max) + self.mining_wait_time_max

            if self.ore_check_time == 0 or ore_check_time_diff >= self.ore_check_timer + self.randomized_ore_time:
                self.randomized_ore_time = random.random() * (self.mining_wait_time_min - self.mining_wait_time_max) + self.mining_wait_time_max
                self.ore_check_time = time.time()
                print(f'idem spat na {self.ore_check_timer+self.randomized_ore_time}s')
                self.__click_at_ore(ore_x, ore_y)
        else:
            if self.ore_check_time == 0 or ore_check_time_diff >= self.ore_check_timer:
                self.ore_check_time = time.time()
                print(f'idem spat na {self.ore_check_timer + self.randomized_ore_time}s')
                self.__click_at_ore(ore_x, ore_y)
        return np_image_out

    def mine_ore(self, np_image:np.ndarray):
        np_image_crop = crop_image(np_image, self.scan_window_location)
        if not self.randomized_ore_time:
            self.randomized_ore_time = random.random() * (self.mining_wait_time_min - self.mining_wait_time_max) + self.mining_wait_time_max

        ore_x, ore_y, np_image_out = self.__ore_check(np_image_crop)

        if self.is_mining:
            ore_check_time_diff = time.time() - self.ore_check_time
            print(f'Tazim {ore_check_time_diff}s')
            if self.mining_wait_time_min != 0 and self.mining_wait_time_max != 0:
                if ore_check_time_diff >= self.ore_check_timer + self.randomized_ore_time:
                    self.is_mining = False
                    print('Koniec tazby')
            else:
                if ore_check_time_diff >= self.ore_check_timer:
                    self.is_mining = False
                    print('Koniec tazby')
        else:

            if ore_x is not None and ore_y is not None:
                self.__click_at_ore(ore_x, ore_y)
                self.ore_check_time = time.time()
                self.randomized_ore_time = random.random() * (self.mining_wait_time_min - self.mining_wait_time_max) + self.mining_wait_time_max
                print(f'Idem tazit {self.ore_check_timer + self.randomized_ore_time}s')
                self.is_mining = True

        return np_image_out

    def __click_at_ore(self, ore_x:int, ore_y:int):
        scan_x1, scan_y1, _, _ = self.scan_window_location
        ore_x += self.game_window.window_left + scan_x1
        ore_y += self.game_window.window_top + scan_y1

        mouse_left_click(ore_x, ore_y, self.game_window.window_name)

    def __ore_check(self, np_image:np.ndarray):
        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)

        lower, upper = create_low_upp(self.config)
        contour_low = self.config['contourLow']
        contour_high = self.config['contourHigh']
        aspect_low = self.config['aspect_low'] / 100.0
        aspect_high = self.config['aspect_high'] / 100.0
        circularity = self.config['circularity'] / 1000.0

        mask = cv2.inRange(hsv, lower, upper)
        np_image = cv2.bitwise_and(np_image, np_image, mask=mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            for contour in contours:
                if contour_high > cv2.contourArea(contour) > contour_low:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    area = cv2.contourArea(contour)
                    perimeter = cv2.arcLength(contour, True)
                    item_circularity = 4 * np.pi * (area / (perimeter * perimeter))

                    if aspect_low < aspect_ratio < aspect_high and item_circularity > circularity:
                        cv2.rectangle(np_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle


                        x, y, w, h = cv2.boundingRect(contour)
                        contour_center_x = x + w // 2
                        contour_center_y = y + h // 2
                        return contour_center_x, contour_center_y, np_image
        return None, None, np_image
