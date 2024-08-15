import pyautogui
# import pydirectinput
# import autoit
import keyboard
import cv2
import numpy as np
import time
import os
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageTk
import json
import tkinter as tk
import threading

import threading


class ApplicationWindow:
    def __init__(self, title="Metin Bot", width=800, height=800, screenshot=None):
        self.root = tk.Tk()
        self.root.title(title)

        # Set window size
        self.root.geometry(f"{width}x{height}")

        # Create a label (as an example widget)
        self.label = tk.Label(self.root, text="Hello, World!")
        self.label.pack(pady=20)

        # Create a button to start Metin location
        self.start_metin_location_button = tk.Button(self.root, text="Start metin location",
                                                     command=self.start_metin_location_thread)
        self.start_metin_location_button.pack(pady=10)

        self.image_label = None
        self.screenshot_img = None

        # Display the screenshot at the bottom
        if screenshot is not None:
            self.display_screenshot(screenshot)

        self.metin = Metin()

    def display_screenshot(self, screenshot):
        # This method should only be called from the main thread
        def update_image(screenshot=screenshot):
            # If the screenshot is not a PIL image, convert it
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(screenshot)

            img = screenshot.resize((self.root.winfo_width(), int(self.root.winfo_height() / 2)))  # Resize if necessary
            self.screenshot_img = ImageTk.PhotoImage(img)

            # Update or create the label to display the image
            if self.image_label:
                self.image_label.config(image=self.screenshot_img)
            else:
                self.image_label = tk.Label(self.root, image=self.screenshot_img)
                self.image_label.pack(side="bottom", pady=10)

        # Use `after` to safely update the GUI from the main thread
        self.root.after(0, update_image)

    def start_metin_location_thread(self):
        # Start a new thread for the Metin location process
        threading.Thread(target=self.start_metin_location, daemon=True).start()

    def start_metin_location(self):
        window_title = "EmtGen"
        config = load_config('Config.json')
        metin_config = config[0]
        self.metin.lower, self.metin.upper = create_low_upp(metin_config)
        self.metin.contour_low = metin_config['contourLow']
        self.metin.contour_high = metin_config['contourHigh']

        while True:
            metin_window = gw.getWindowsWithTitle(window_title)[0]
            screenshot = get_window_screenshot(metin_window)
            width, height = screenshot.size

            self.metin.window_top = metin_window.left
            self.metin.window_left = metin_window.top
            self.metin.window_right = metin_window.right
            self.metin.window_bottom = metin_window.bottom
            self.metin.metin_window = metin_window

            left = int(width * 0.2)
            top = int(height * 0.2)
            right = int(width * 0.8)
            bottom = int(height * 0.7)
            cropped_image = screenshot.crop((left, top, right, bottom))

            selected_contour_pos, output_image = self.metin.locate_metin(cropped_image)

            # Convert the OpenCV image (output_image) to a PIL image before displaying it
            output_image = Image.fromarray(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))

            # Display the screenshot using the main thread
            self.display_screenshot(output_image)

    def run(self):
        self.root.mainloop()


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
        np_image = np.array(image)
        # Convert the image from RGB (PIL format) to BGR (OpenCV format)
        np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
        # Convert the image to HSV
        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        masked_img = cv2.bitwise_and(np_image, np_image, mask=mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        selected_contour = None
        selected_contour_pos = None
        min_distance = float('inf')
        width, height = image.size
        image_center = (width // 2, height // 2)
        if contours:
            for contour in contours:
                if 7000 > cv2.contourArea(contour) > 2500:  # 900
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(np_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle
                    cur_distance = abs(image_center[0] - contour[0][0][0]) + abs(
                        image_center[1] - contour[0][0][1])
                    if cur_distance < min_distance:
                        min_distance = cur_distance
                        selected_contour = contour

        if selected_contour is not None:
            x, y, w, h = cv2.boundingRect(selected_contour)
            selected_contour_pos = (x + w / 2, y + h / 2)
            cv2.rectangle(np_image, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw rectangle

        return selected_contour_pos, np_image


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


def main():
    app = ApplicationWindow()
    app.run()


main()
