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
from tkinter import ttk
import threading
import pytesseract


custom_config = r'--oem 3 --psm 6 outputbase digits'



class Screenshot:
    def __init__(self, screenshot, left_up, right_down, on_found_callback=None):
        self.screenshot = screenshot
        self.left_up = left_up
        self.right_down = right_down
        self.on_found_callback = on_found_callback

    def find_anti_bot(self):
        # cropped_image = Image.fromarray(self.screenshot)
        # Now use pyautogui to locate the template in the cropped screenshot
        try:
            location = pyautogui.locate('', self.screenshot, confidence=0.60)
        except pyautogui.ImageNotFoundException:
            print('not found')
            return None
        if location is not None:
            print(f'Object found at location: {location}')
            if self.on_found_callback:
                self.on_found_callback()
            # Bot check found, now defeat it
            return self.__defeat_anti_bot()

    def __defeat_anti_bot(self):
        options = list()
        x1, y1 = 90, 30  # Top-left corner
        x2, y2 = 140, 60  # Bottom-right corner
        code_to_find = Screenshot(self.screenshot[y1:y2, x1:x2], (x1, y1), (x2, y2))
        x1, y1 = 25, 70  # z lava, z hora
        x2, y2 = 80, 90  # z prava, z dola
        options.append(Screenshot(self.screenshot[y1:y2, x1:x2], (x1, y1), (x2, y2)))

        x1, y1 = 100, 70  # z lava, z hora
        x2, y2 = 150, 90  # z prava, z dola
        options.append(Screenshot(self.screenshot[y1:y2, x1:x2], (x1, y1), (x2, y2)))

        x1, y1 = 25, 100  # z lava, z hora
        x2, y2 = 80, 120  # z prava, z dola
        options.append(Screenshot(self.screenshot[y1:y2, x1:x2], (x1, y1), (x2, y2)))

        x1, y1 = 100, 100  # z lava, z hora
        x2, y2 = 150, 120  # z prava, z dola
        options.append(Screenshot(self.screenshot[y1:y2, x1:x2], (x1, y1), (x2, y2)))

        x1, y1 = 70, 130  # z lava, z hora
        x2, y2 = 120, 150  # z prava, z dola
        resized_code_to_find = resize_image(code_to_find.screenshot)
        options.append(Screenshot(self.screenshot[y1:y2, x1:x2], (x1, y1), (x2, y2)))
        extracted_text_code_to_find = pytesseract.image_to_string(resized_code_to_find, config=custom_config)
        code_to_find_number = extracted_text_code_to_find[:4]
        print(f'code_to_find_number {code_to_find_number}')
        for option in options:
            resized_option = resize_image(option.screenshot)
            extracted_text_option = pytesseract.image_to_string(resized_option, config=custom_config)
            option_number = extracted_text_option[:4]
            print(f'option_number {option_number}')
            if option_number == code_to_find_number:
                print('found matching option')
                result_x1, result_y1 = option.left_up
                result_x2, result_y2 = option.right_down

                result_center_x = result_x1 + (result_x2 - result_x1) // 2
                result_center_y = result_y1 + (result_y2 - result_y1) // 2

                pos_x = result_center_x + 10
                pos_y = result_center_y + 90

                return pos_x, pos_y


class ApplicationWindow:
    def __init__(self, title="Metin Bot", width=800, height=800, screenshot=None):
        self.root = tk.Tk()
        self.root.title(title)

        # Set window size
        self.root.geometry(f"{width}x{height}")

        # Create a label (as an example widget)
        self.label = tk.Label(self.root, text="Metin2 bot :-)")
        self.label.pack(pady=20)

        # Create a button to start Metin location
        self.start_metin_location_button = tk.Button(self.root, text="Start metin location",
                                                     command=self.start_metin_location_thread)
        self.start_metin_location_button.pack(pady=10)

        # Create a text entry field
        self.entry_label = tk.Label(self.root, text="Enter something:")
        self.entry_label.pack(pady=5)
        self.text_entry = tk.Entry(self.root, width=50)
        self.text_entry.pack(pady=5)

        # Create a dropdown (Combobox) to choose from specific values
        self.dropdown_label = tk.Label(self.root, text="Choose metin stone:")
        self.dropdown_label.pack(pady=5)
        self.metin_options = ["Option 1", "Option 2", "Option 3", "Option 4"]  # Add your specific options here
        self.dropdown = ttk.Combobox(self.root, values=self.metin_options)
        self.dropdown.pack(pady=5)

        self.image_label = None
        self.screenshot_img = None

        self.metin = None

        self.tesseract_path = ''
        self.metin_stones = []
        self.load_config_values()

    def load_config_values(self):
        cfg = load_config('Config.json')
        pytesseract.pytesseract.tesseract_cmd = cfg['tesseract_path']
        self.metin = Metin(cfg['bot_test_img_path'])
        self.metin_stones = cfg['metin_stones']
        self.metin_options = [item['name'] for item in self.metin_stones]

        self.dropdown['values'] = self.metin_options

        # Optionally, set the default value (if needed)
        if self.metin_options:
            self.dropdown.set(self.metin_options[0])



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
        selected_value = self.dropdown.get()
        metin_mask = {}
        for metin_config in self.metin_stones:
            if metin_config['name'] == selected_value:
                metin_mask = metin_config['mask']
                self.metin.contour_low = metin_config['contourLow']
                self.metin.contour_high = metin_config['contourHigh']
        self.metin.lower, self.metin.upper = create_low_upp(metin_mask)

        while True:
            metin_window = gw.getWindowsWithTitle(window_title)[0]
            screenshot = get_window_screenshot(metin_window)

            self.metin.window_top = metin_window.left
            self.metin.window_left = metin_window.top
            self.metin.window_right = metin_window.right
            self.metin.window_bottom = metin_window.bottom
            self.metin.metin_window = metin_window

            # original: width: 1296, height: 1063
            x1, y1 = 259, 212  # z lava, z hora
            x2, y2 = 1036, 744  # z prava, z dola
            x_middle = x2 - x1
            y_middle = y2 - y1

            np_image = np.array(screenshot)
            np_image_crop = np_image[y1: y2, x1: x2]

            values = self.metin.locate_metin(np_image_crop, x_middle, y_middle)
            if values is not None:
                selected_contour_pos, output_image = values
                # Convert the OpenCV image (output_image) to a PIL image before displaying it
                output_image = Image.fromarray(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
                # Display the screenshot using the main thread
                self.display_screenshot(output_image)
                metin_pos_x, metin_pos_y = selected_contour_pos

                metin_pos_x += self.metin.window_left
                metin_pos_y += self.metin.window_top

                pyautogui.moveTo(metin_pos_x, metin_pos_y)

                if self.metin.solved_at is not None:
                    time_diff = time.time() - self.metin.solved_at
                    if time_diff > 30:
                        self.bot_solver()
                else:
                    self.metin.solved_at = time.time()
                    self.bot_solver()
            else:
                self.display_screenshot(np_image_crop)
                print("No valid contour found.")

    def bot_solver(self):
        window_title = "EmtGen"
        metin_window = gw.getWindowsWithTitle(window_title)[0]
        screenshot = get_window_screenshot(metin_window)

        self.metin.window_top = metin_window.left
        self.metin.window_left = metin_window.top
        self.metin.window_right = metin_window.right
        self.metin.window_bottom = metin_window.bottom
        self.metin.metin_window = metin_window

        solved = self.metin.look_for_bot_check(screenshot)

        if solved:
            print('solved')
        else:
            print('no antibot')

    def run(self):
        self.root.mainloop()


class Metin:
    def __init__(self, bot_img_path):
        self.window_top = None
        self.window_left = None
        self.window_right = None
        self.window_bottom = None
        self.metin_window = None
        self.lower = None
        self.upper = None
        self.solved_at = None
        self.solving_bot_check = False
        self.contour_low = 0
        self.contour_high = 0
        self.template = cv2.imread(bot_img_path, cv2.IMREAD_COLOR)
        self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)

    def on_found(self):
        self.solving_bot_check = True

    def locate_metin(self, np_image, x_middle, y_middle):
        # Convert the image from RGB (PIL format) to BGR (OpenCV format)
        np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
        # Convert the image to HSV
        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        selected_contour = None
        selected_contour_pos = None
        min_distance = float('inf')
        # width, height = image.size

        if contours:
            for contour in contours:
                if self.contour_high > cv2.contourArea(contour) > self.contour_low:  # 900
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(np_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle
                    cur_distance = abs(x_middle - contour[0][0][0]) + abs(
                        y_middle - contour[0][0][1])
                    if cur_distance < min_distance:
                        min_distance = cur_distance
                        selected_contour = contour

        if selected_contour is not None:
            x, y, w, h = cv2.boundingRect(selected_contour)
            selected_contour_pos = (x + w / 2, y + h / 2)
            cv2.rectangle(np_image, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw rectangle
        if selected_contour_pos is None:
            return None
        return selected_contour_pos, np_image

    def look_for_bot_check(self, image):
        np_image = np.array(image)
        x1, y1 = 10, 80  # Top-left corner
        x2, y2 = 190, 240  # Bottom-right corner
        cropped_image = np_image[y1:y2, x1:x2]
        screenshot = Screenshot(cropped_image, (10, 80), (190, 240), on_found_callback=self.on_found())
        result = screenshot.find_anti_bot()
        print(f'result = {result}')
        if result is not None:
            pos_x, pos_y = result
            to_click_x = pos_x + self.window_left
            to_click_y = pos_y + self.window_top
            pyautogui.moveTo(to_click_x, to_click_y)

            return True

        return False


def resize_image(image):
    height, width = image.shape[:2]
    new_width = int(width * 2)
    new_height = int(height * 2)

    # Resize the image
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)


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


def create_low_upp(metin_mask):
    hMin = metin_mask['mask']['hMin']
    sMin = metin_mask['mask']['sMin']
    vMin = metin_mask['mask']['vMin']
    hMax = metin_mask['mask']['hMax']
    sMax = metin_mask['mask']['sMax']
    vMax = metin_mask['mask']['vMax']
    lower = np.array([hMin, sMin, vMin])
    upper = np.array([hMax, sMax, vMax])

    return lower, upper


def main():
    app = ApplicationWindow()
    app.run()


main()
