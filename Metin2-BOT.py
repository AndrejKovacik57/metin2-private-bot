import pyautogui
import cv2
import numpy as np
import time
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageTk
import json
import tkinter as tk
from tkinter import ttk
import threading
import pytesseract
import pydirectinput

custom_config = r'--oem 3 --psm 6 outputbase digits'


class Screenshot:
    def __init__(self, screenshot, left_up, right_down, on_found_callback=None):
        self.screenshot = screenshot
        self.left_up = left_up
        self.right_down = right_down
        self.on_found_callback = on_found_callback

    def find_anti_bot(self, needle):
        # cropped_image = Image.fromarray(self.screenshot)
        # Now use pyautogui to locate the template in the cropped screenshot
        try:
            location = pyautogui.locate(needle, self.screenshot, confidence=0.60)
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

        # Create a button to start Metin location
        self.start_metin_location_button = tk.Button(self.root, text="Start metin location",
                                                     command=self.start_metin_location_thread)
        self.start_metin_location_button.pack(pady=10)

        # Create a button to stop Metin location
        self.stop_metin_location_button = tk.Button(self.root, text="Stop Metin Location",
                                                    command=self.stop_metin_location)
        self.stop_metin_location_button.pack(pady=10)

        # Create a text entry field
        self.entry_tesseract_path = tk.Label(self.root, text="tesseract path:")
        self.entry_tesseract_path.pack(pady=5)
        self.text_tesseract_path = tk.Entry(self.root, width=50)
        self.text_tesseract_path.pack(pady=5)

        # Create a text entry field
        self.entry_bot_check = tk.Label(self.root, text="bot check img:")
        self.entry_bot_check.pack(pady=5)
        self.text_bot_check = tk.Entry(self.root, width=50)
        self.text_bot_check.pack(pady=5)

        # Create a text entry field
        self.entry_metin_hp_check = tk.Label(self.root, text="metin hp img:")
        self.entry_metin_hp_check.pack(pady=5)
        self.text_metin_hp_check = tk.Entry(self.root, width=50)
        self.text_metin_hp_check.pack(pady=5)

        # Create a text entry field
        self.entry_skills_check = tk.Label(self.root, text="Skills to activate:")
        self.entry_skills_check.pack(pady=5)
        self.text_skills_check = tk.Entry(self.root, width=50)
        self.text_skills_check.pack(pady=5)

        # Create a dropdown (Combobox) to choose from specific values
        self.dropdown_label = tk.Label(self.root, text="Choose metin stone:")
        self.dropdown_label.pack(pady=5)
        self.metin_options = ["Option 1", "Option 2", "Option 3", "Option 4"]  # Add your specific options here
        self.dropdown = ttk.Combobox(self.root, values=self.metin_options)
        self.dropdown.pack(pady=5)

        # Create a button to start Metin location
        self.apply = tk.Button(self.root, text="Apply", command=self.apply_fields)
        self.apply.pack(pady=10)

        self.cfg = {}

        self.image_label = None
        self.screenshot_img = None

        self.metin = None

        self.running = False

        self.tesseract_path = ''
        self.metin_stones = []
        self.load_config_values()

    def load_config_values(self):
        cfg = load_config('Config.json')
        self.cfg = cfg

        pytesseract.pytesseract.tesseract_cmd = cfg['tesseract_path']
        self.metin = Metin(cfg['bot_test_img_path'], cfg['metin_hp_img_path'])
        self.metin_stones = cfg['metin_stones']
        self.metin_options = [item['name'] for item in self.metin_stones]

        self.dropdown['values'] = self.metin_options
        if self.metin_options:
            self.dropdown.set(self.metin_options[0])

        self.text_tesseract_path.insert(0, cfg['tesseract_path'])
        self.text_bot_check.insert(0, cfg['bot_test_img_path'])
        self.text_metin_hp_check.insert(0, cfg['metin_hp_img_path'])
        self.text_skills_check.insert(0, cfg['skills_to_activate'])

    def apply_fields(self):
        pytesseract.pytesseract.tesseract_cmd = self.text_tesseract_path.get()
        self.metin.bot_img_path = self.text_bot_check.get()

        self.cfg['bot_test_img_path'] = self.text_bot_check.get()
        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.cfg['metin_hp_img_path'] = self.text_metin_hp_check.get()
        self.cfg['skills_to_activate'] = self.text_skills_check.get()

        save_config(self.cfg, 'Config.json')

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
        if not self.running:  # Prevent starting multiple threads
            self.running = True
            threading.Thread(target=self.start_metin_location, daemon=True).start()

    def start_metin_location(self):
        window_title = "EmtGen"
        selected_value = self.dropdown.get()
        metin_mask = {}
        for metin_config in self.metin_stones:
            if metin_config['name'] == selected_value:
                metin_mask = metin_config
                self.metin.contour_low = metin_config['contourLow']
                self.metin.contour_high = metin_config['contourHigh']
        self.metin.lower, self.metin.upper = create_low_upp(metin_mask)

        target_pixel_value = np.array([187, 19, 19])

        while self.running:
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

            np_image = np.array(screenshot)
            np_image_crop = np_image[y1: y2, x1: x2]

            x_middle = (x2 - x1) // 2
            y_middle = (y2 - y1) // 2
            if self.metin.god_buff_cd == 0:
                print('klik1')
                self.metin.god_buff_cd = time.time()
                pydirectinput.press('F9')
            else:
                god_buff_timr_diff = time.time() - self.metin.god_buff_cd
                if god_buff_timr_diff > 1860:
                    print('klik2')
                    pydirectinput.press('F9')
            pydirectinput.press('F4')
            values = self.metin.locate_metin(np_image_crop, x_middle, y_middle)
            if values is not None:
                selected_contour_pos, output_image = values
                # Convert the OpenCV image (output_image) to a PIL image before displaying it
                output_image = Image.fromarray(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
                # Display the screenshot using the main thread
                self.display_screenshot(output_image)
                metin_pos_x, metin_pos_y = selected_contour_pos

                metin_pos_x += self.metin.window_left + x1
                metin_pos_y += self.metin.window_top + y1

                if not self.metin.destroying_metin:
                    pydirectinput.press('z')
                    print('nenici sa metin')
                    pyautogui.moveTo(metin_pos_x, metin_pos_y)
                    pyautogui.click()
                    self.metin.destroying_metin = True
                    self.metin.metin_destroying_time = time.time()
                    self.metin.metin_is_being_destroyed = False
                else:

                    x1, y1 = 432, 70  # z lava, z hore
                    x2, y2 = 450, 90  # z prava, z dola
                    hp_bar = np_image[y1: y2, x1: x2]
                    metin_is_alive = self.metin.locate_metin_hp(hp_bar, 0.7)
                    self.metin.destroying_metin = metin_is_alive
                    print(f'nici sa metin {metin_is_alive}')
                    pydirectinput.press('e')
                    metin_destroy_time_diff = time.time() - self.metin.metin_destroying_time
                    if metin_is_alive and metin_destroy_time_diff > 5 and not self.metin.metin_is_being_destroyed:
                        x1, y1 = 832, 75  # z lava, z hore
                        x2, y2 = 850, 85  # z prava, z dola
                        red_hp = np_image[y1: y2, x1: x2]
                        height, width, _ = red_hp.shape

                        center_y = height // 2
                        center_x = width // 2

                        center_pixel = red_hp[center_y, center_x]

                        if np.array_equal(center_pixel, target_pixel_value):
                            print("The pixel value matches [187, 19, 19].")
                            # 850, 60
                            x_to_cancel = self.metin.window_left + 850
                            y_to_cancel = self.metin.window_top + 60
                            pyautogui.moveTo(x_to_cancel, y_to_cancel)
                            pyautogui.click()
                            pydirectinput.press('a')

                    time.sleep(0.5)
                if self.metin.solved_at is not None:
                    time_diff = time.time() - self.metin.solved_at
                    if time_diff > 30:
                        self.bot_solver()
                        self.metin.solved_at = time.time()
                else:
                    self.metin.solved_at = time.time()
                    self.bot_solver()
            else:
                self.display_screenshot(np_image_crop)
                pydirectinput.press('q')
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

    def stop_metin_location(self):
        self.running = False

    def run(self):
        self.root.mainloop()


class Metin:
    def __init__(self, bot_img_path, metin_hp_img):
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
        self.metin_hp_img = metin_hp_img
        self.bot_img_path = bot_img_path
        self.destroying_metin = False
        self.metin_destroying_time = 0
        self.metin_is_being_destroyed = False
        self.god_buff_cd = 0

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

                    contour_center_x = x + w // 2
                    contour_center_y = y + h // 2

                    # Draw a line from the middle of the screenshot to the center of the contour
                    cv2.line(np_image, (x_middle, y_middle), (contour_center_x, contour_center_y), (255, 190, 200), 2)
                    # Optionally, you can calculate the distance between the middle of the screenshot and the contour center
                    cur_distance = abs(x_middle - contour_center_x) + abs(y_middle - contour_center_y)
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
        result = screenshot.find_anti_bot(self.bot_img_path)
        print(f'result = {result}')
        if result is not None:
            pos_x, pos_y = result
            to_click_x = pos_x + self.window_left
            to_click_y = pos_y + self.window_top
            pyautogui.moveTo(to_click_x, to_click_y)
            pyautogui.click()

            return True

        return False

    def locate_metin_hp(self, np_image, confidence=0.8):
        location = None
        try:
            location = pyautogui.locate(self.metin_hp_img, np_image, confidence=confidence)
        except pyautogui.ImageNotFoundException:
            return False
        if location is not None:
            return True


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


def save_config(config_dict, name):
    with open(name, 'w') as config:
        json.dump(config_dict, config, indent=4)


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
