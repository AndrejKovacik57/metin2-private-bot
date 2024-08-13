import pyautogui
# import pydirectinput
# import autoit
import keyboard
import cv2
import numpy as np
import time
import os
import pygetwindow as gw
from PIL import ImageGrab
import json
import tkinter as tk


class Metin:
    def __init__(self):
        self.window_top = None
        self.window_left = None
        self.window_right = None
        self.window_bottom = None
        self.metin_window = None
        self.lower = None
        self.upper = None
        self.contour_low = 0
        self.contour_high = 0

    def locate_metin(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        masked_img = cv2.bitwise_and(image, image, mask=mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for contour in contours:
                print('contourArea:')
                print(cv2.contourArea(contour))
                if 7000 > cv2.contourArea(contour) > 2500:  # 900
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle
        return image


def get_window_screenshot(window):
    # Get the position and size of the window
    left, top, right, bottom = window.left, window.top, window.right, window.bottom
    # Take a screenshot of the specified region
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=False, all_screens=True)

    return screenshot


def load_config(name):
    with open(name, 'r') as config:
        config_dict = json.load(config)
    return config_dict


def create_low_upp(metin_config):
    hMin = metin_config['mask']['hMin']
    sMin = metin_config['mask']['sMin']
    vMin = metin_config['mask']['vMin']
    hMax = metin_config['mask']['hMax']
    sMax = metin_config['mask']['sMax']
    vMax = metin_config['mask']['vMax']
    lower = np.array([hMin, sMin, vMin])
    upper = np.array([hMax, sMax, vMax])

    return lower, upper


def run():
    window_title = "EmtGen"
    config = load_config('Config.json')
    metin = Metin()
    metin_config = config[0]
    lower, upper = create_low_upp(metin_config)

    metin.contour_low = metin_config['contourLow']
    metin.contour_high = metin_config['contourHigh']
    while True:
        metin_window = gw.getWindowsWithTitle(window_title)[0]
        screenshot = get_window_screenshot(metin_window)
        width, height = screenshot.size

        metin.window_top = metin_window.left
        metin.window_left = metin_window.top
        metin.window_right = metin_window.right
        metin.window_bottom = metin_window.bottom
        metin.metin_window = metin_window

        left = int(width * 0.2)
        top = int(height * 0.2)
        right = int(width * 0.8)
        bottom = int(height * 0.7)
        cropped_image = screenshot.crop((left, top, right, bottom))

        metin.locate_metin(cropped_image)


run()
