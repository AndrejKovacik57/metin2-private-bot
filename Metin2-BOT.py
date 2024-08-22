from random import random
import pyautogui
import cv2
import numpy as np
import time
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageTk
import json
import tkinter as tk
from tkinter import ttk, Canvas
import threading
import pytesseract
import keyboard


custom_config = r'--oem 3 --psm 6 outputbase digits'


class Screenshot:
    def __init__(self, screenshot, left_up, right_down, on_found_callback=None):
        self.screenshot = screenshot
        self.left_up = left_up
        self.right_down = right_down
        self.on_found_callback = on_found_callback


class ApplicationWindow:
    def __init__(self, title="Metin Bot", width=800, height=800, screenshot=None):
        self.root = tk.Tk()
        self.root.title(title)

        # Set window size
        self.root.geometry(f"{width}x{height}")

        # Create a text entry field
        self.entry_window_name = tk.Label(self.root, text="Window name:")
        self.entry_window_name.pack(pady=5)
        self.text_window_name = tk.Entry(self.root, width=50)
        self.text_window_name.pack(pady=5)

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
        self.dropdown = ttk.Combobox(self.root, values=self.metin_options, state="readonly")
        self.dropdown.pack(pady=5)

        # Create a button to start Metin location
        self.apply = tk.Button(self.root, text="Apply", command=self.apply_fields)
        self.apply.pack(pady=10)

        # Create a button to take a screenshot and allow rectangle selection
        self.screenshot_button = tk.Button(self.root, text="Take Screenshot", command=self.take_screenshot)
        self.screenshot_button.pack(pady=10)

        self.set_metin_hp_bar_location = tk.Button(self.root, text="Set location for metin hp bar", command=self.apply_hp_bar_location)
        self.set_metin_hp_bar_location.pack(pady=10)
        self.set_metin_hp_full_location = tk.Button(self.root, text="Set location for metin full hp", command=self.apply_hp_full_location)
        self.set_metin_hp_full_location.pack(pady=10)
        self.set_cancel_location = tk.Button(self.root, text="Set location cancel button", command=self.apply_cancel_location)
        self.set_cancel_location.pack(pady=10)
        self.set_scan_window = tk.Button(self.root, text="Set scan window", command=self.apply_scan_window_location)
        self.set_scan_window.pack(pady=10)

        self.cfg = {}
        self.information_locations = {}

        self.image_label = None
        self.screenshot_img = None

        self.metin = None

        self.hp_bar_location = None
        self.hp_full_location = None
        self.hp_full_pixel_colour = None
        self.scan_window_location = None
        self.cancel_location = None

        self.canvas = None
        self.screenshot_image = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selected_area = None
        self.screenshot_image_left = None
        self.screenshot_image_top = None

        self.running = False

        self.tesseract_path = ''
        self.metin_stones = []
        self.load_config_values()

    def load_config_values(self):
        cfg = load_config('Config.json')
        self.cfg = cfg

        pytesseract.pytesseract.tesseract_cmd = cfg['tesseract_path']
        self.metin = Metin(cfg['bot_test_img_path'], cfg['metin_hp_img_path'], cfg['skills_to_activate'].split())
        self.metin_stones = cfg['metin_stones']
        self.metin_options = [item['name'] for item in self.metin_stones]

        self.dropdown['values'] = self.metin_options
        if self.metin_options:
            self.dropdown.set(self.metin_options[0])

        self.metin.window_title = self.cfg['window_name']

        self.hp_bar_location = cfg['information_locations']['hp_bar_location']
        self.hp_full_location = cfg['information_locations']['hp_full_location']
        self.hp_full_pixel_colour = cfg['information_locations']['hp_full_pixel_colour']
        self.scan_window_location = cfg['information_locations']['scan_window_location']
        self.cancel_location = cfg['information_locations']['cancel_location']

        self.text_tesseract_path.insert(0, cfg['tesseract_path'])
        self.text_bot_check.insert(0, cfg['bot_test_img_path'])
        self.text_metin_hp_check.insert(0, cfg['metin_hp_img_path'])
        self.text_skills_check.insert(0, cfg['skills_to_activate'])
        self.text_window_name.insert(0, cfg['window_name'])

    def apply_fields(self):
        pytesseract.pytesseract.tesseract_cmd = self.text_tesseract_path.get()
        self.metin.bot_img_path = self.text_bot_check.get()
        self.metin.window_title = self.text_window_name.get()

        self.cfg['bot_test_img_path'] = self.text_bot_check.get()
        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.cfg['metin_hp_img_path'] = self.text_metin_hp_check.get()
        self.cfg['skills_to_activate'] = self.text_skills_check.get()
        self.cfg['window_name'] = self.text_window_name.get()

        self.metin.skills_to_activate = self.cfg['skills_to_activate'].split()

        save_config(self.cfg, 'Config.json')

    def apply_hp_bar_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x), max(self.end_y, self.start_y)]
            self.cfg['information_locations']['hp_bar_location'] = output

    def apply_hp_full_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            np_img = np.array(self.screenshot_image)
            pixel = np_img[self.end_y + self.screenshot_image_top, self.end_x + self.screenshot_image_left]
            self.cfg['information_locations']['hp_full_pixel_colour'] = pixel.tolist()

            self.cfg['information_locations']['hp_full_location'] = [self.end_x, self.end_y, self.start_x, self.start_y]

    def apply_scan_window_location(self):
        # z lava, z hora, z prava, z dola
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x), max(self.end_y, self.start_y)]

            self.cfg['information_locations']['scan_window_location'] = output

    def apply_cancel_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x), max(self.end_y, self.start_y)]

            self.cfg['information_locations']['cancel_location'] = output


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

        selected_value = self.dropdown.get()
        metin_mask = {}
        for metin_config in self.metin_stones:
            if metin_config['name'] == selected_value:
                metin_mask = metin_config
                self.metin.contour_low = metin_config['contourLow']
                self.metin.contour_high = metin_config['contourHigh']
        self.metin.lower, self.metin.upper = create_low_upp(metin_mask)

        target_pixel_value = np.array(self.hp_full_pixel_colour)
        upper_limit = 0.1
        lower_limit = 0.5

        while self.running:
            sleep_time = random() * (upper_limit - lower_limit) + lower_limit
            time.sleep(sleep_time)
            metin_window = gw.getWindowsWithTitle(self.metin.window_title)[0]
            screenshot = get_window_screenshot(metin_window)
            self.metin.window_left = metin_window.left
            self.metin.window_top = metin_window.top
            self.metin.window_right = metin_window.right
            self.metin.window_bottom = metin_window.bottom
            self.metin.metin_window = metin_window

            x1, y1, x2, y2 = self.scan_window_location   # z lava, z hora, z prava, z dola
            print(f'x1:{x1} y1:{y1} x2:{x2} y2:{y2}')
            np_image = np.array(screenshot)
            np_image_crop = np_image[y1: y2, x1: x2]
            x_middle = (x2 - x1) // 2
            y_middle = (y2 - y1) // 2

            selected_contour_pos, output_image = self.metin.locate_metin(np_image_crop, x_middle, y_middle)
            if selected_contour_pos is not None:
                # Display the screenshot using the main thread
                self.display_screenshot(output_image)
                metin_pos_x, metin_pos_y = selected_contour_pos

                metin_pos_x += self.metin.window_left + x1
                metin_pos_y += self.metin.window_top + y1

                if not self.metin.destroying_metin:
                    press_button('z')
                    print('nenici sa metin')
                    mouse_right_click(metin_pos_x, metin_pos_y)
                    screenshot_hp_check = get_window_screenshot(self.metin.metin_window)
                    np_image_hp_check = np.array(screenshot_hp_check)
                    # check for hp missing
                    pixel_x, pixel_y = self.hp_full_location[:2]
                    print(f'pred pixel_y {pixel_y} pixel_x {pixel_x}')
                    pixel_x += self.metin.window_left
                    pixel_y += self.metin.window_top
                    pixel_to_check = np_image_hp_check[pixel_y, pixel_x]
                    print(f'po pixel_y {pixel_y} pixel_x {pixel_x}')
                    print(f'pc {pixel_to_check} tp {target_pixel_value}')
                    if np.array_equal(pixel_to_check, target_pixel_value):
                        mouse_left_click(metin_pos_x, metin_pos_y)

                        self.metin.destroying_metin = True
                        self.metin.metin_destroying_time = time.time()
                        self.metin.metin_is_being_destroyed = False
                else:

                    hp_bar_x1, hp_bar_y1, hp_bar_x2, hp_bar_y2 = self.hp_bar_location
                    hp_bar = np_image[hp_bar_y1: hp_bar_y2, hp_bar_x1: hp_bar_x2]
                    metin_is_alive = self.metin.locate_metin_hp(hp_bar, 0.7)
                    self.metin.destroying_metin = metin_is_alive
                    print(f'nici sa metin {metin_is_alive}')
                    if not metin_is_alive:
                        continue

                    press_button('q')

                    metin_destroy_time_diff = time.time() - self.metin.metin_destroying_time
                    if metin_is_alive and metin_destroy_time_diff > 10 and not self.metin.metin_is_being_destroyed:
                        print('AAAAA')
                        print('AAAAA')
                        print('AAAAA')
                        print('AAAAA')
                        pixel_x, pixel_y = self.hp_full_location[:2]
                        pixel_x += self.metin.window_left
                        pixel_y += self.metin.window_top

                        pixel_to_check = np_image[pixel_y, pixel_x]
                        if np.array_equal(pixel_to_check, target_pixel_value):
                            cancel_x, cancel_y = self.cancel_location[:2]
                            x_to_cancel = (self.metin.window_left + cancel_x) / 2
                            y_to_cancel = (self.metin.window_top + cancel_y) / 2

                            mouse_left_click(x_to_cancel, y_to_cancel)
                            press_button('a')
                        else:
                            self.metin.metin_is_being_destroyed = True


            else:
                self.display_screenshot(output_image)
                press_button('q')
                print("No valid contour found.")

    def take_screenshot(self):
        # Capture the screenshot of the entire screen
        metin_window = gw.getWindowsWithTitle(self.metin.window_title)[0]
        screenshot = get_window_screenshot(metin_window)
        self.screenshot_image = screenshot
        self.screenshot_image_left = metin_window.left
        self.screenshot_image_top = metin_window.top

        # Create a new window to display the screenshot
        new_window = tk.Toplevel(self.root)
        new_window.title("Screenshot")
        new_window.geometry(f"{screenshot.width}x{screenshot.height}")

        # Convert the screenshot to ImageTk format for display
        screenshot_tk = ImageTk.PhotoImage(screenshot)

        # Create a canvas widget to display the screenshot
        canvas = Canvas(new_window, width=screenshot.width, height=screenshot.height)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_tk)

        # Keep a reference to the image to avoid garbage collection
        canvas.image = screenshot_tk

        # Bind mouse events for drawing the rectangle
        canvas.bind("<ButtonPress-1>", lambda event: self.on_button_press(event, canvas))
        canvas.bind("<B1-Motion>", lambda event: self.on_mouse_drag(event, canvas))
        canvas.bind("<ButtonRelease-1>", lambda event: self.on_button_release(event))
        canvas.bind("<Button-3>", lambda event: self.on_right_click(canvas))

        # Store the canvas in the instance for reference
        self.canvas = canvas
        self.rect = None
        self.start_x = None
        self.start_y = None

    def on_button_press(self, event, canvas):
        # Store the initial coordinates on mouse button press
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            canvas.delete(self.rect)
        self.rect = canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_mouse_drag(self, event, canvas):
        # Update the rectangle as the user drags the mouse
        cur_x, cur_y = (event.x, event.y)
        canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        # Finalize the rectangle and print/save the coordinates
        self.end_x, self.end_y = (event.x, event.y)
        print(f"Rectangle coordinates: {self.start_x}, {self.start_y} -> {self.end_x}, {self.end_y}")

        # Save the coordinates or use them in your logic as needed
        self.selected_area = (self.start_x, self.start_y, self.end_x, self.end_y)

    def on_right_click(self, canvas):
        # Delete the rectangle if right-clicked
        if self.rect:
            canvas.delete(self.rect)
            self.rect = None
            print("Rectangle deleted")

    def bot_solver(self):
        metin_window = gw.getWindowsWithTitle(self.metin.window_title)[0]
        screenshot = get_window_screenshot(metin_window)

        self.metin.window_top = metin_window.left
        self.metin.window_left = metin_window.top
        self.metin.window_right = metin_window.right
        self.metin.window_bottom = metin_window.bottom
        self.metin.metin_window = metin_window

        solved = self.metin.look_for_bot_check(screenshot)

        if solved:
            print('solved')
            return True
        else:
            print('no antibot')
            return False

    def stop_metin_location(self):
        self.metin.metin_destroying_time = 0
        self.metin.god_buff_cd = 0
        self.metin.skills_time = 0
        self.metin.solved_at = 0
        self.metin.solving_bot_check = False
        self.running = False

    def run(self):
        self.root.mainloop()


class Metin:
    def __init__(self, bot_img_path, metin_hp_img, skills_to_activate):
        self.window_top = None
        self.window_left = None
        self.window_right = None
        self.window_bottom = None
        self.metin_window = None
        self.lower = None
        self.upper = None
        self.solved_at = 0
        self.solving_bot_check = False
        self.contour_low = 0
        self.contour_high = 0
        self.metin_hp_img = metin_hp_img
        self.bot_img_path = bot_img_path
        self.destroying_metin = False
        self.metin_destroying_time = 0
        self.metin_is_being_destroyed = False
        self.window_title = None
        self.god_buff_cd = 0
        self.skills_to_activate = skills_to_activate
        self.skill_positions = {'1': 1, '2': 2, '3': 3, '4': 4, 'F1': 5, 'F2': 6, 'F3': 7, 'F4': 8}
        self.skills_time = 0

    def on_found(self):
        self.solving_bot_check = True

    def locate_metin(self, np_image, x_middle, y_middle):
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
            return None, np_image
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
            to_click_x = pos_x + self.window_top
            to_click_y = pos_y + self.window_left
            mouse_left_click(to_click_x, to_click_y)

            return True

        return False

    def locate_metin_hp(self, np_image, confidence=0.8):
        try:
            location = pyautogui.locate(self.metin_hp_img, np_image, confidence=confidence)
        except pyautogui.ImageNotFoundException:
            return False
        if location is not None:
            return True

    def activate_skills(self):
        x1, y1 = 568, 1020  # z lava, z hore
        x2, y2 = 835, 1050  # z prava, z dola
        max_attempts = 10
        went_down = False
        for skill_to_activate in self.skills_to_activate:
            for counter in range(max_attempts):
                print(f'---{skill_to_activate} try {counter}---')
                skill_pos = self.skill_positions[skill_to_activate]
                pixels = []
                offset = 16 if skill_pos < 5 else 30  # 14 pixels between nums and Fs
                skill_pixel_position = 32 * (skill_pos - 1) + offset
                for _ in range(3):
                    np_image = np.array(get_window_screenshot(self.metin_window))
                    skills = np_image[y1: y2, x1: x2]
                    pixel = skills[0, skill_pixel_position].tolist()
                    if pixel not in pixels:
                        pixels.append(pixel)
                    time.sleep(0.1)
                num_of_diff_pixels = len(pixels)
                print(f'num_of_diff_pixels: {num_of_diff_pixels}')
                if num_of_diff_pixels > 1:
                    print('skill active')
                    if went_down and self.metin_window and self.window_title in self.metin_window.title:
                        press_button_multiple('ctrl+g')
                    break
                else:
                    if counter > 1:
                        # couldnt activate skill because character is on horse, we go down from mount
                        if self.metin_window and self.window_title in self.metin_window.title:
                            press_button_multiple('ctrl+g')
                            went_down = True
                    print('skill not active')
                    press_button(skill_to_activate)
                    counter += 1


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


def press_button(button):
    keyboard.press(button)
    time.sleep(0.15)
    keyboard.release(button)


def press_button_multiple(button):
    buttons = button.split('+')
    for button in buttons:
        keyboard.press(button)
        time.sleep(0.15)
    for button in buttons:
        keyboard.release(button)
        time.sleep(0.15)


def mouse_left_click(metin_pos_x, metin_pos_y):
    # active_window = gw.getActiveWindow()
    # if active_window and window_title in active_window.title:
    pyautogui.moveTo(metin_pos_x, metin_pos_y)
    pyautogui.click()


def mouse_right_click(metin_pos_x, metin_pos_y):
    # active_window = gw.getActiveWindow()
    # if active_window and window_title in active_window.title:
    pyautogui.moveTo(metin_pos_x, metin_pos_y)
    pyautogui.rightClick()


def main():
    app = ApplicationWindow()
    app.run()


main()
