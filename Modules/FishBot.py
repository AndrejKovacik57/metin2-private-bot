import random
import time
from Modules import GameWindow
from Utils.Utils import locate_image, press_button, load_image, mouse_left_click, create_low_upp
import cv2
import numpy as np


class FishBot:
    def __init__(self, game_window: GameWindow, fishing_config:dict):
        self.fishing_img = load_image('..\\bot_images\\Fishing.png')
        self.game_window = game_window
        self.lower_fishing = None
        self.upper_fishing = None
        self.contour_low_fishing = None
        self.contour_high_fishing = None
        self.aspect_low_fishing = None
        self.aspect_high_fishing = None
        self.circularity_fishing = None
        self.fish_counter = 0
        self.is_fishing_flag = False
        self.start_fishing_flag  = False
        self.fish_timer = 0
        self.initialize_contour_parameters(fishing_config)

    def initialize_contour_parameters(self, fishing_config):
        self.contour_low_fishing = fishing_config['contourLow']
        self.contour_high_fishing = fishing_config['contourHigh']
        self.aspect_low_fishing = fishing_config['aspect_low'] / 100.0
        self.aspect_high_fishing = fishing_config['aspect_high'] / 100.0
        self.circularity_fishing = fishing_config['circularity'] / 1000.0

        self.lower_fishing, self.upper_fishing = create_low_upp(fishing_config)

    def __check_red_pixels(self, np_image, y1, y2, x1, x2):
        red_pixel_img = np_image[y1:y2, x1:x2]
        red_pixels = (red_pixel_img[:, :, 0] == 255) & \
                     (red_pixel_img[:, :, 1] == 0) & \
                     (red_pixel_img[:, :, 2] == 0)
        return np.any(red_pixels)

    def __manage_fishing_state(self):

        if self.start_fishing_flag and not self.is_fishing_flag:
            print('trying to place bait')
            if self.fish_counter == 5:
                self.__place_bait()
            else:
                self.__retry_fishing()
        else:
            print('No need to place bait')
    def __place_bait(self):
        print("Davam navnadu")
        self.fish_counter = 0
        self.start_fishing_flag = False
        press_button('F1', self.game_window.window_name)
        time.sleep(random.uniform(1.1, 1.5))

    def __retry_fishing(self):
        print("Retrying to catch fish")
        self.fish_counter += 1
        time.sleep(random.uniform(1.1, 1.5))

    def __process_hsv_and_contours(self, np_image, y1, y2, x1, x2):
        np_image = np_image[y1:y2, x1:x2]
        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_fishing, self.upper_fishing)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return np_image, contours

    def __select_contour(self, contours):
        for contour in contours:
            if self.contour_low_fishing < cv2.contourArea(contour) < self.contour_high_fishing:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * (area / (perimeter * perimeter))
                if self.aspect_low_fishing < aspect_ratio < self.aspect_high_fishing and circularity > self.circularity_fishing:
                    return contour
        return None

    def __click_on_fish(self, contour, x1, y1):
        x, y, w, h = cv2.boundingRect(contour)
        x_pos, y_pos = x + w / 2, y + h / 2
        x_click = self.game_window.window_left + x1 + x_pos
        y_click = self.game_window.window_top + y1 + y_pos
        mouse_left_click(x_click, y_click, self.game_window.window_name)
        sleep_time = random.random() * (0.5 - 0.9) + 0.9
        print(f'fish timer {time.time() - self.fish_timer}')
        time.sleep(sleep_time)

    def catch_fish(self):
        np_image = self.game_window.get_np_image(convert_color=False)
        location = locate_image(self.fishing_img, np_image, 0.9)
        if location is None:
            self.is_fishing_flag = False
            print(f'self.start_fishing_flag {self.start_fishing_flag}')
            if not self.start_fishing_flag:
                print('press space')
                press_button('space', self.game_window.window_name)

            self.start_fishing_flag = True
            self.__manage_fishing_state()
            return
        print('Fishing')
        self.fish_counter = 0
        self.is_fishing_flag = True
        self.start_fishing_flag = False
        y1, y2 = location.top, location.top + location.height + 230
        x1, x2 = location.left, location.left + location.width

        if not self.__check_red_pixels(np_image, y1, y2, x1, x2):
            print('ryba nieje v kruhu')
            return

        print('ryba je v kruhu')
        np_image = self.game_window.get_np_image(convert_color=False)
        self.fish_timer = time.time()
        np_image, contours = self.__process_hsv_and_contours(np_image, y1, y2, x1, x2)
        selected_contour = self.__select_contour(contours)

        if selected_contour is not None:
            print("Mam rybu")
            self.__click_on_fish(selected_contour, x1, y1)
            time.sleep(random.uniform(0.5, 0.9))
        else:
            print("No fish detected")