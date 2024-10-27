import random
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
import logging
import os
import hashlib

custom_config = r'--oem 3 --psm 6 outputbase digits'

# Configure logging
logging.basicConfig(
    filename='bot_solver2.log',  # Log to a file
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S'  # Date format
)


class NoCudaOrCPUModuleFound(ValueError):
    def __init__(self, message):
        super().__init__(message)


class ApplicationWindow:
    def __init__(self, title='Metin Bot', debug_bot=0):
        self.root = tk.Tk()
        self.root.title(title)

        # Set window size
        self.root.geometry(f'{450}x{600}')

        # Create a grid layout for better organization
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        self.display_images_var = tk.BooleanVar()
        self.destroy_event_stones = tk.BooleanVar()

        # Add the "Display" checkbox on the left side of the input field for "Window name"
        self.display_checkbox = tk.Checkbutton(self.root, text="Display", variable=self.display_images_var)
        self.display_checkbox.grid(row=0, column=0, padx=5, pady=5)

        self.display_images_var.trace_add("write", self.toggle_display_images)

        # Create a text entry field for window name
        self.entry_window_name = tk.Label(self.root, text="Window name:")
        self.entry_window_name.grid(row=0, column=0, columnspan=4, pady=5)
        self.text_window_name = tk.Entry(self.root, width=15)
        self.text_window_name.grid(row=1, column=0, columnspan=4, pady=5)

        # Create buttons for start/stop Metin location and label on top for choose metin stone
        self.start_bot_loop_button = tk.Button(self.root, text="Start bot_loop", command=self.start_bot_loop_thread)
        self.start_bot_loop_button.grid(row=2, column=0, pady=10, padx=10)

        self.stop_bot_loop_button = tk.Button(self.root, text="Start mining", command=self.stop_bot_loop)
        self.stop_bot_loop_button.grid(row=2, column=1, pady=10, padx=10)

        self.stop_bot_loop_button = tk.Button(self.root, text="Stop bot", command=self.stop_bot_loop)
        self.stop_bot_loop_button.grid(row=2, column=2, pady=10, padx=10)

        self.entry_tesseract_path = tk.Label(self.root, text="Tesseract Path:")
        self.entry_tesseract_path.grid(row=4, column=0, pady=5)
        self.text_tesseract_path = tk.Entry(self.root, width=20)
        self.text_tesseract_path.grid(row=5, column=0, pady=5)

        self.entry_skills_check = tk.Label(self.root, text="Skills to Activate:")
        self.entry_skills_check.grid(row=4, column=1, pady=5)
        self.text_skills_check = tk.Entry(self.root, width=20)
        self.text_skills_check.grid(row=5, column=1, pady=5)


        self.dropdown_label = tk.Label(self.root, text="Choose Metin Stone:")
        self.dropdown_label.grid(row=4, column=2, columnspan=2, pady=5)
        self.metin_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        self.dropdown = ttk.Combobox(self.root, values=self.metin_options, state="readonly")
        self.dropdown.grid(row=5, column=2, pady=5)
        # Bind event to the dropdown
        self.dropdown.bind("<<ComboboxSelected>>", self.save_selected_option_metins)

        self.event_checkbox = tk.Checkbutton(self.root, text="Event stone", variable=self.destroy_event_stones)
        self.event_checkbox.grid(row=8, column=0, padx=5, pady=5)

        self.destroy_event_stones.trace_add("write", self.toggle_destroy_event_stones)

        self.reset_skill = tk.Button(self.root, text="Reset skill", command=self.reset_skill)
        self.reset_skill.grid(row=8, column=1, pady=10)

        # Create a button to take a screenshot and center it
        self.screenshot_button = tk.Button(self.root, text="Take Screenshot", command=self.take_screenshot)
        self.screenshot_button.grid(row=9, column=1, pady=10)

        # self.entry_circle_r = tk.Label(self.root, text="Circle radius (px):")
        # self.entry_circle_r.grid(row=8, column=2, pady=5)
        # self.text_circle_r = tk.Entry(self.root, width=30)
        # self.text_circle_r.grid(row=9, column=2, pady=5)

        self.set_metin_hp_bar_location = tk.Button(text="Set HP bar location", command=self.apply_hp_bar_location)
        self.set_metin_hp_bar_location.grid(row=10, column=0, pady=10)

        self.set_metin_hp_full_location = tk.Button(text="Set full HP location", command=self.apply_hp_full_location)
        self.set_metin_hp_full_location.grid(row=10, column=1, pady=10)

        self.set_respawn_button_location = tk.Button(text="Set respawn location", command=self.apply_respawn_button_location)
        self.set_respawn_button_location.grid(row=10, column=2, pady=9)

        self.set_cancel_location = tk.Button(text="Set cancel location", command=self.apply_cancel_location)
        self.set_cancel_location.grid(row=11, column=0, pady=10)

        self.set_scan_window = tk.Button(text="Set scan window", command=self.apply_scan_window_location)
        self.set_scan_window.grid(row=11, column=1, pady=10)

        self.set_metin_stack = tk.Button(text="Set metin stack location", command=self.apply_metin_stack_location)
        self.set_metin_stack.grid(row=11, column=2, pady=10)

        self.set_bot_check = tk.Button(text="Set bot check location", command=self.apply_bot_check_location)
        self.set_bot_check.grid(row=12, column=0, pady=10)

        # Create the Apply button and center it
        self.apply = tk.Button(self.root, text="Apply", command=self.apply_fields)
        self.apply.grid(row=13, column=0, columnspan=4, pady=10)

        self.cfg = {}
        self.cfg_local = {}
        self.information_locations = {}

        self.metin = None
        self.tesseract_path = ''
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
        self.image_label = None

        self.load_config_values(debug_bot)

    def load_config_values(self, debug_bot):
        cfg = load_config('Config2.json')
        cfg_local = load_config('Config-local2.json')
        self.cfg = cfg
        self.cfg_local = cfg_local

        pytesseract.pytesseract.tesseract_cmd = cfg['tesseract_path']

        self.text_tesseract_path.insert(0, cfg['tesseract_path'])

        if cfg_local:
            self.metin = Metin(cfg_local['skills_to_activate'].split(), self.display_screenshot, debug_bot)
            self.metin.window_title = self.cfg_local['window_name']
            self.text_skills_check.insert(0, cfg_local['skills_to_activate'])
            self.text_window_name.insert(0, cfg_local['window_name'])
            if 'information_locations' not in self.cfg_local:
                self.cfg_local['information_locations'] = {}

            self.load_cfg_local()

        else:
            self.cfg_local['information_locations'] = {}
            self.metin = Metin([], self.display_screenshot, debug_bot)

        self.metin.metin_stones = cfg['metin_stones']
        self.metin_options = [item['name'] for item in self.metin.metin_stones]

        self.dropdown['values'] = self.metin_options
        if self.metin_options:
            self.dropdown.set(self.metin_options[0])
            self.metin.selected_metin = self.metin_options[0]

    def apply_fields(self):
        pytesseract.pytesseract.tesseract_cmd = self.text_tesseract_path.get()
        self.metin.window_title = self.text_window_name.get()

        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.cfg_local['skills_to_activate'] = self.text_skills_check.get()
        self.cfg_local['window_name'] = self.text_window_name.get()

        self.load_cfg_local()

        self.metin.skills_to_activate = self.cfg_local['skills_to_activate'].split()
        save_config(self.cfg, 'Config2.json')
        save_config(self.cfg_local, 'Config-local2.json')

    def load_cfg_local(self):
        if 'information_locations' in self.cfg_local:
            info_locs = self.cfg_local['information_locations']

            if 'hp_bar_location' in info_locs:
                self.metin.hp_bar_location = info_locs['hp_bar_location']

            if 'hp_full_location' in info_locs:
                self.metin.hp_full_location = info_locs['hp_full_location']

            if 'hp_full_pixel_colour' in info_locs:
                self.metin.hp_full_pixel_colour = info_locs['hp_full_pixel_colour']

            if 'scan_window_location' in info_locs:
                self.metin.scan_window_location = info_locs['scan_window_location']

            if 'cancel_location' in info_locs:
                self.metin.cancel_location = info_locs['cancel_location']

            if 'metin_stack_location' in info_locs:
                self.metin.metin_stack_location = info_locs['metin_stack_location']

            if 'bot_check_location' in info_locs:
                self.metin.bot_check_location = info_locs['bot_check_location']

            if 'respawn_button_location' in info_locs:
                self.metin.respawn_location = info_locs['respawn_button_location']


    def reset_skill(self):
        self.metin.skill_timer = 0

    def save_selected_option_metins(self, event):
        self.metin.selected_metin = self.dropdown.get()

    def toggle_display_images(self, *args):
        if self.display_images_var.get() == 1:
            print("Image display is enabled.")
            self.metin.show_img = True
        else:
            print("Image display is disabled.")
            self.metin.show_img = False

    def toggle_destroy_event_stones(self, *args):
        if self.destroy_event_stones.get() == 1:
            self.metin.destroy_event_stones = True
            print(f'metin.destroy_event_stones T {self.metin.destroy_event_stones}')
        else:
            self.metin.destroy_event_stones = False
            print(f'metin.destroy_event_stones F {self.metin.destroy_event_stones}')

    def apply_hp_bar_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]
            self.cfg_local['information_locations']['hp_bar_location'] = output

    def apply_respawn_button_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]
            self.cfg_local['information_locations']['respawn_button_location'] = output

    def apply_hp_full_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            np_img = np.array(self.screenshot_image)
            # np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
            pixel = np_img[self.end_y + self.screenshot_image_top, self.end_x + self.screenshot_image_left]
            print(f'ukladam {pixel}')
            self.cfg_local['information_locations']['hp_full_pixel_colour'] = pixel.tolist()

            self.cfg_local['information_locations']['hp_full_location'] = [self.end_x, self.end_y, self.start_x,
                                                                           self.start_y]

    def apply_metin_stack_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg_local['information_locations']['metin_stack_location'] = output

    def apply_bot_check_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg_local['information_locations']['bot_check_location'] = output

    def apply_scan_window_location(self):
        # z lava, z hora, z prava, z dola
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg_local['information_locations']['scan_window_location'] = output

    def apply_thief_glove_button_location(self):
        # z lava, z hora, z prava, z dola
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            print(f'thief_glove_location {output}')
            self.cfg_local['information_locations']['thief_glove_location'] = output

    def apply_cancel_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg_local['information_locations']['cancel_location'] = output

    def start_bot_loop_thread(self):
        if not self.metin.running:  # Prevent starting multiple threads
            self.metin.running = True
            threading.Thread(target=self.metin.bot_loop, daemon=True).start()

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

    def display_screenshot(self):
        screenshot = self.metin.image_to_display

        def update_image(screenshot=screenshot):
            # If the screenshot is not a PIL image, convert it
            if not isinstance(screenshot, Image.Image):
                screenshot = screenshot[:, :, ::-1]
                screenshot = Image.fromarray(screenshot)

            # Resize the image to fit the width of the window and half the height
            img = screenshot.resize((self.root.winfo_width(), int(self.root.winfo_height() / 2)))

            # Convert the image to a format that can be displayed in Tkinter
            self.screenshot_img = ImageTk.PhotoImage(img)

            # Update or create the label to display the image at the bottom of the grid
            if self.image_label:
                self.image_label.config(image=self.screenshot_img)
            else:
                # Create the label and place it at the bottom of the grid
                self.image_label = tk.Label(self.root, image=self.screenshot_img)
                self.image_label.grid(row=14, column=0, columnspan=4, pady=10)

        # Use `after` to safely update the GUI from the main thread
        self.root.after(0, update_image)

    def on_button_press(self, event, canvas):
        # Store the initial coordinates on mouse button press
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            canvas.delete(self.rect)
        self.rect = canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='green')

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

    def stop_bot_loop(self):
        self.metin.running = False
        self.metin.not_destroying_metin = 0
        self.metin.destroying_metins = False

    def run(self):
        self.root.mainloop()


class Metin:
    def __init__(self, skills_to_activate, display_screenshot, debug_bot):
        self.debug_bot = debug_bot
        self.window_top = None
        self.window_left = None
        self.window_right = None
        self.window_bottom = None
        self.metin_window = None
        self.window_title = None
        self.skill_timer = 0
        self.skills_to_activate = skills_to_activate
        self.respawn_timer = 0
        self.hp_bar_location = None
        self.hp_full_location = None
        self.hp_full_pixel_colour = None
        self.scan_window_location = None
        self.cancel_location = None
        self.respawn_location = None
        self.skills_cd = 60 * 60 * 2 + 10
        self.running = False
        self.metin_stones = []
        self.selected_metin = None
        self.skill_timer_diff = 0
        self.respawn_timer_diff = 0
        self.not_destroying_metin = 0
        self.not_destroying_metin_diff = 0
        self.buff_timer = 0
        self.buff_timer_diff = 0
        self.event_timer = 0
        self.event_timer_diff = 0
        self.buff_cd = 30 * 60
        self.destroying_metins = False
        self.show_img = False
        self.lower = None
        self.upper = None
        self.contour_low = 0
        self.contour_high = 0
        self.aspect_low = 0
        self.aspect_high = 0
        self.circularity = 0
        self.weather = 0
        self.lower_event = None
        self.upper_event = None
        self.contour_low_event = 0
        self.contour_high_event = 0
        self.aspect_low_event = 0
        self.aspect_high_event = 0
        self.circularity_event = 0
        self.selected_weather = 999
        self.circle_r = 50
        self.settings_options = None
        self.game_settings = None
        self.sky_settings = None
        self.restart = None
        self.destroy_event_stones = False
        self.image_to_display = None
        self.cancel_img = None
        self.metin_hp_img = None
        self.weather_image = None
        self.text_hash_map = None
        self.bot_img_path = None
        self.metin_stack_location = None
        self.bot_check_location = None
        self.options = [ # coords for options menu buttons
                (35, 70, 80, 90),
                (100, 70, 150, 90),
                (35, 100, 80, 120),
                (100, 100, 150, 120),
                (70, 130, 120, 150)
            ]
        self.premium = True

        self.load_images()

        self.display_screenshot = display_screenshot
        self.lock = threading.Lock()
        self.initialize()

    def initialize(self):
        with open("hash_combinations2.json", "r") as json_file:
            self.text_hash_map = json.load(json_file)

    def load_images(self):
        self.restart = load_image('bot_images\\restart_img.png')
        self.settings_options = load_image('bot_images\\settings_options.png')
        self.sky_settings = load_image('bot_images\\sky_settings.png')
        self.game_settings = load_image('bot_images\\game_settings.png')
        self.weather_image = load_image('bot_images\\weather.png')
        self.bot_img_path = load_image('bot_images\\bot_ochrana.png')
        self.cancel_img = load_image('bot_images\\cancel_metin_button.png')
        self.metin_hp_img = load_image('bot_images\\metin_hp2.png')

    def bot_loop(self):
        metin_mask = {}
        event_mask = {}
        for metin_config in self.metin_stones:
            if metin_config['name'] == self.selected_metin:
                metin_mask = metin_config
                self.contour_low = metin_config['contourLow']
                self.contour_high = metin_config['contourHigh']
                self.aspect_low = metin_config['aspect_low'] / 100.0
                self.aspect_high = metin_config['aspect_high'] / 100.0
                self.circularity = metin_config['circularity'] / 1000.0
                self.weather = metin_config['weather']

                event_config = metin_config['event_stones'][0]
                event_mask = event_config
                self.contour_low_event = event_config['contourLow']
                self.contour_high_event = event_config['contourHigh']
                self.aspect_low_event = event_config['aspect_low'] / 100.0
                self.aspect_high_event = event_config['aspect_high'] / 100.0
                self.circularity_event =  event_config['circularity'] / 1000.0

                break
        self.lower, self.upper = create_low_upp(metin_mask)
        self.lower_event, self.upper_event = create_low_upp(event_mask)

        time.sleep(2)
        print('idem vybrat pocasie')
        self.choose_weather()
        upper_limit = 0.5
        lower_limit = 0.1

        while self.running:
            with self.lock:
                loop_time = time.time()
                sleep_time = random.random() * (upper_limit - lower_limit) + lower_limit
                time.sleep(sleep_time)
                np_image = self.get_np_image()
                if self.running:
                    self.bot_solver(np_image)
                if self.running:
                    self.death_check(np_image)
                if self.running:
                    self.activate_skills()
                if self.running:
                    self.activate_buffs()
                if self.running:
                    self.image_to_display = self.destroy_metin(np_image)
                    if self.show_img:
                        self.display_screenshot()
                    print(f'Iteration execution time {time.time() - loop_time}s')

    def bot_solver(self, np_image):
        cropped_image_x1, cropped_image_y1, cropped_image_x2, cropped_image_y2 = self.bot_check_location
        cropped_image = np_image[cropped_image_y1:cropped_image_y2, cropped_image_x1:cropped_image_x2]

        location = locate_image(self.bot_img_path, cropped_image, confidence=0.60)
        # cv2.imwrite('bottest/cropped_image.png', cropped_image)
        if location is not None:
            # code to find
            x1, y1 = 90, 30  # Top-left corner
            x2, y2 = 140, 60  # Bottom-right corner
            resized_code_to_find = resize_image(cropped_image[y1:y2, x1:x2])

            cv2.imwrite('bottest/code_to_find.png', cropped_image[y1:y2, x1:x2])
            extracted_text_code_to_find = pytesseract.image_to_string(resized_code_to_find, config=custom_config)
            code_to_find_number = extracted_text_code_to_find[:4]
            print(f'code_to_find_number {code_to_find_number}')
            logging.info(f'code_to_find_number {code_to_find_number}')
            smallest_difference = 999
            output = None
            smallest_difference_num = None
            exact_match = False
            out_num = ''
            for option_tuple in self.options:
                result_x1, result_y1, result_x2, result_y2 = option_tuple
                option = cropped_image[result_y1:result_y2, result_x1:result_x2]
                option_hash = hashlib.md5(preprocess_image(option)).hexdigest()

                if option_hash in self.text_hash_map:
                    option_number = self.text_hash_map[option_hash]
                else:
                    resized_option = resize_image(option)
                    extracted_text_option = pytesseract.image_to_string(resized_option, config=custom_config)
                    option_number = extracted_text_option[:4]
                    logging.info(f'tesseract fallback')

                print(f'option_number {option_number}')
                logging.info(f'option_number {option_number}')

                result_center_x = result_x1 + (result_x2 - result_x1) // 2
                result_center_y = result_y1 + (result_y2 - result_y1) // 2

                pos_x = result_center_x + cropped_image_x1 + self.window_left + 5
                pos_y = result_center_y + cropped_image_y1 + self.window_top + 1

                if option_number == code_to_find_number:
                    print('found matching option')
                    logging.info(f'found matching option')
                    output = pos_x, pos_y
                    exact_match = True
                    out_num = option_number
                    break
                else:
                    differences = sum(1 for a, b in zip(option_number, code_to_find_number) if a != b)
                    if smallest_difference > differences:
                        smallest_difference_num = option_number
                        smallest_difference = differences
                        output = pos_x, pos_y
                        out_num = option_number

            if smallest_difference_num is not None and not exact_match:
                logging.info(f'using smallest difference on {smallest_difference_num}')

            logging.info(f'----------------------------------')
            logging.info(f'selected {out_num}')
            to_click_x, to_click_y = output
            mouse_left_click(to_click_x, to_click_y, self.window_title)
            time.sleep(3)

    def death_check(self, np_image):
        self.respawn_timer_diff = time.time() - self.respawn_timer
        if self.respawn_timer == 0 or self.respawn_timer != 0 and self.respawn_timer_diff >= 5:
            print('death_check')
            self.respawn_timer = time.time()

            respawn_location = locate_image(self.restart, np_image, confidence=0.8)
            if respawn_location is not None:
                respawn_x = self.window_left+20 + respawn_location.left + respawn_location.width / 2
                respawn_y = self.window_top + respawn_location.top + respawn_location.height / 2
                time.sleep(1)
                print('death_check - klik')
                pyautogui.moveTo(respawn_x, respawn_y)
                time.sleep(0.2)
                pyautogui.click()
                time.sleep(1)
                press_button_multiple('ctrl+g', self.window_title)

    def activate_skills(self):
        self.skill_timer_diff = time.time() - self.skill_timer
        if self.skill_timer == 0 or self.skill_timer != 0 and self.skill_timer_diff >= self.skills_cd:
            time.sleep(2)
            print('activate_skills')
            self.skill_timer = time.time()
            print('zosadam')
            press_button_multiple('ctrl+g', self.window_title)
            time.sleep(0.15)

            for skill in self.skills_to_activate:
                print(f'skill {skill}')
                press_button(skill, self.window_title)
                time.sleep(2)
            press_button_multiple('ctrl+g', self.window_title)
            print('nasadam')

    def activate_buffs(self):
        self.buff_timer_diff = time.time() - self.buff_timer
        if self.buff_timer >= 0 and self.skill_timer_diff >= self.buff_cd:
            print('activate_skills')
            self.buff_cd = 60 + random.randint(1, 30)
            self.skill_timer = time.time()
            press_button('F9', self.window_title)
            time.sleep(0.15)

    def destroy_metin(self, np_image):
        x1, y1, x2, y2 = self.scan_window_location  # z lava, z hora, z prava, z dola
        np_image_crop = np_image[y1: y2, x1: x2]
        x_middle = self.window_left + (x2 - x1) // 2
        y_middle = self.window_top + (y2 - y1) // 2
        self.not_destroying_metin_diff = time.time() - self.not_destroying_metin if self.not_destroying_metin else 0


        if self.not_destroying_metin_diff > 15:
            self.running = False
            self.destroying_metins = False
            self.not_destroying_metin = 0
            formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            print(f' {formatted_time}')
            return np_image_crop


        hp_bar_x1, hp_bar_y1, hp_bar_x2, hp_bar_y2 = self.hp_bar_location
        hp_bar = np_image[hp_bar_y1: hp_bar_y2, hp_bar_x1: hp_bar_x2]
        # check if metin was destroyed
        metin_is_alive = self.locate_metin_hp(hp_bar)
        if not metin_is_alive and not self.not_destroying_metin and self.destroying_metins:
            self.not_destroying_metin = time.time()

        print(f'nici sa metin {metin_is_alive}')

        if metin_is_alive:
            self.not_destroying_metin_diff = 0
            self.not_destroying_metin = 0

        stack_x1, stack_y1, stack_x2, stack_y2 = self.metin_stack_location
        metin_stack_img = np_image[stack_y1:  stack_y2, stack_x1:  stack_x2]
        metin_stack_img_processed = preprocess_image(metin_stack_img)

        metin_stack_hash = hashlib.md5(metin_stack_img_processed).hexdigest()

        if metin_stack_hash in self.text_hash_map:
            metin_stack_string = self.text_hash_map[metin_stack_hash]
            stack = int(metin_stack_string[3])
            metins_in_stack = int(metin_stack_string[1])
            metin_num = stack - metins_in_stack
            print('nasiel sa metin hash')
        else:
            if not metin_is_alive and self.not_destroying_metin and self.destroying_metins:
                time.sleep(2)
                return np_image_crop
            print('nenasiel sa metin hash')
            metin_num = 1
        if self.destroy_event_stones:
            self.event_timer_diff = time.time() - self.event_timer
            if self.event_timer == 0 or self.event_timer != 0 and self.event_timer_diff >= 10:
                print(f'hladam event kamen')
                print(f'hladam event kamen')
                print(f'hladam event kamen')
                self.event_timer = time.time()
                metin_positions_event, image_to_display_event = self.locate_metin(np_image_crop, metin_num, x_middle, y_middle,
                                                                                  self.lower_event, self.upper_event,
                                                                                  self.contour_high_event, self.contour_low_event,
                                                                                  self.aspect_low_event, self.aspect_high_event,
                                                                                  self.circularity_event)
                if metin_positions_event is not None:
                    print(f'nasiel sa event kamen')
                    print(f'nasiel sa event kamen')
                    print(f'nasiel sa event kamen')
                    print(f'metin_positions_event {len(metin_positions_event)}')
                    # cancel stack
                    press_button('w', self.window_title)
                    time.sleep(0.15)
                    for metin_event_pos in metin_positions_event:
                        metin_pos_x, metin_pos_y = metin_event_pos

                        if np.all(np_image_crop[metin_pos_y, metin_pos_x] == [0, 0, 0]):
                            print("The pixel is black.")
                        else:
                            print("The pixel is not black.")
                            # no metin is being destroyed
                            print('Click at event metin')
                            metin_pos_x += self.window_left + x1
                            metin_pos_y += self.window_top + y1
                            if not self.premium:
                                press_button('z', self.window_title)
                                time.sleep(0.15)
                                press_button('y', self.window_title)

                            mouse_left_click(metin_pos_x, metin_pos_y, self.window_title)
                            self.destroying_metins = True
                            sleep_time = random.random() * (0.3 - 0.15) + 0.15
                            time.sleep(sleep_time)

                            return image_to_display_event


        # return np_image_crop
        metin_positions, image_to_display = self.locate_metin(np_image_crop, metin_num, x_middle, y_middle, self.lower,
                                                              self.upper, self.contour_high, self.contour_low,
                                                              self.aspect_low, self.aspect_high, self.circularity)

        if metin_positions is not None and metin_num > 0:
            print('Metin Found')
            for metin_pos in metin_positions:
                metin_pos_x, metin_pos_y = metin_pos

                if np.all(np_image_crop[metin_pos_y, metin_pos_x] == [0, 0, 0]):
                    print("The pixel is black.")
                else:
                    # no metin is being destroyed
                    print('Click at metin')
                    metin_pos_x += self.window_left + x1
                    metin_pos_y += self.window_top + y1
                    if not self.premium:
                        press_button('z', self.window_title)
                        time.sleep(0.15)
                        press_button('y', self.window_title)

                    mouse_left_click(metin_pos_x, metin_pos_y, self.window_title)
                    self.destroying_metins = True
                    sleep_time = random.random() * (0.3 - 0.15) + 0.15
                    time.sleep(sleep_time)

        else:
            press_button('q', self.window_title)
            print("Searching for metin")

        return image_to_display

    def cancel_metin_window(self, np_image, x_middle, y_middle):
        print('zatvaram metin okno')
        choices = ['a', 'd']
        cancel_x1, cancel_y1, cancel_x2, cancel_y2 = self.cancel_location
        cancel_area = np_image[cancel_y1:cancel_y2, cancel_x1:cancel_x2]
        location = locate_image(self.cancel_img, cancel_area)
        if location is not None:
            x_to_cancel = self.window_left + cancel_x1 + location.left + location.width / 2
            y_to_cancel = self.window_top + cancel_y1 + location.top + location.height / 2

            mouse_left_click(x_to_cancel, y_to_cancel, self.window_title)
            time.sleep(0.2)
            mouse_left_click(x_middle, y_middle, self.window_title)
            time.sleep(0.2)
            press_button(random.choice(choices), self.window_title)
            time.sleep(0.2)
            press_button('q', self.window_title)
            time.sleep(0.2)
            press_button('q', self.window_title)
            time.sleep(0.2)

    def locate_metin(self, np_image, metin_num, x_middle, y_middle, lower, upper, contour_high,
                     contour_low, aspect_low, aspect_high, circularity, use_circle_r=True):
        # Convert the image to HSV
        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_list = []
        if contours:
            for contour in contours:
                if contour_high > cv2.contourArea(contour) > contour_low:  # 900
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    area = cv2.contourArea(contour)
                    perimeter = cv2.arcLength(contour, True)
                    circularity_obj = 4 * np.pi * (area / (perimeter * perimeter))
                    if aspect_low < aspect_ratio < aspect_high and circularity_obj > circularity:

                        cv2.rectangle(np_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle

                        contour_center_x = x + w // 2
                        contour_center_y = y + h // 2

                        # Draw a line from the middle of the screenshot to the center of the contour
                        cv2.line(np_image, (x_middle, y_middle), (contour_center_x, contour_center_y),
                                 (255, 190, 200), 2)
                        cur_distance = abs(x_middle - contour_center_x) + abs(y_middle - contour_center_y)

                        if use_circle_r:
                            # Draw a circle around the point (x_middle, y_middle) with a radius of 300px
                            cv2.circle(np_image, (x_middle, y_middle), self.circle_r, (255, 190, 200),
                                       2)  # The color is (255, 190, 200) and the thickness is 2
                            if cur_distance <= self.circle_r:
                                continue

                        a = cur_distance, contour
                        contour_list.append(a)

        contour_list.sort(key=lambda cont: cont[0])
        closest_contours = contour_list[:metin_num]

        selected_contour_positions = []  # List to store positions of the 5 closest contours
        for _, contour in closest_contours:
            x, y, w, h = cv2.boundingRect(contour)
            contour_center_x = x + w // 2
            contour_center_y = y + h // 2
            selected_contour_positions.append((contour_center_x, contour_center_y))

        if not closest_contours:
            return None, np_image

        # Return the positions of the 5 closest contours and the image
        return selected_contour_positions, np_image

    def locate_metin_hp(self, np_image_hp_bar):
        return is_subimage(np_image_hp_bar, self.metin_hp_img)

    def get_np_image(self):
        metin_window = gw.getWindowsWithTitle(self.window_title)[0]
        screenshot = get_window_screenshot(metin_window)
        self.window_left = metin_window.left
        self.window_top = metin_window.top
        self.window_right = metin_window.right
        self.window_bottom = metin_window.bottom
        self.metin_window = metin_window

        np_image = np.array(screenshot)

        np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
        return np_image

    def choose_weather(self):
        if self.selected_weather == self.weather:
            return
        np_image = self.get_np_image()
        # options

        print('hladam nastavenia')
        location = locate_image(self.settings_options, np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.5)

        np_image = self.get_np_image()
        print('hladam nastavenia hry')
        location = locate_image(self.game_settings, np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.5)

        np_image = self.get_np_image()
        print('hladam nastavenia oblohy')
        location = locate_image(self.sky_settings, np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.5)
        np_image = self.get_np_image()
        # weather
        location = locate_image(self.weather_image, np_image, 0.9)
        if location is None:
            print('weather none')
            return

        space = 10
        width = 81
        height = 49
        counter = 0
        for row in range(6):
            for column in range(3):
                if counter == self.weather - 1:
                    y1 = location.top + height * row
                    y2 = y1 + height
                    x1 = location.left + width * column + space * column
                    x2 = x1 + width

                    move_x = self.window_left + x1 + (x2 - x1) / 2
                    move_y = self.window_top + y1 + (y2 - y1) / 2

                    mouse_left_click(move_x, move_y, self.window_title)
                    self.selected_weather = counter + 1

                counter += 1

        time.sleep(0.5)
        try:
            locations = pyautogui.locateAll(self.cancel_img, np_image, confidence=0.9)
        except pyautogui.ImageNotFoundException:
            locations = None
        if locations is not None:
            for location in locations:
                self.click_location_middle(location)
                time.sleep(0.5)

    def click_location_middle(self, location):
        x = self.window_left + location.left + location.width / 2
        y = self.window_top + location.top + location.height / 2
        print(f'click x {x} y {x}')
        mouse_left_click(x, y, self.window_title)


def resize_image(image):
    height, width = image.shape[:2]
    new_width = int(width * 2)
    new_height = int(height * 2)

    # Resize the image using a better upscaling method
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)


def get_window_screenshot(window):
    # Get the position and size of the window
    left, top, right, bottom = window.left, window.top, window.right, window.bottom
    # Take a screenshot of the specified region
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=False, all_screens=True)

    return screenshot


def load_config(name):
    if not os.path.exists(name):
        return {}

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


def press_button(button, window_title):
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        keyboard.press(button)
        time.sleep(0.15)
        keyboard.release(button)


def press_button_multiple(button, window_title):
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        buttons = button.split('+')
        for button in buttons:
            keyboard.press(button)
            time.sleep(0.3)
        for button in buttons:
            keyboard.release(button)
            time.sleep(0.3)


def mouse_left_click(pos_x, pos_y, window_title):
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        pyautogui.moveTo(pos_x, pos_y)
        print('KLIK KLIK KLIK')
        pyautogui.click()


def mouse_right_click(pos_x, pos_y, window_title):
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        pyautogui.moveTo(pos_x, pos_y)
        pyautogui.rightClick()


def preprocess_image(image):
    # Convert the image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Define the lower and upper range for the white color
    lower_white = np.array([0, 0, 180])  # Lower bound for light gray-white in HSV
    upper_white = np.array([180, 50, 220])  # Upper bound for light gray-white in HSV
    # Create a mask for green areas in the image
    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Bitwise-AND the mask and the original image
    image = cv2.bitwise_and(image, image, mask=mask)
    # Find all non-black pixels in the mask (which should correspond to green)
    coords = np.column_stack(np.where(mask > 0))
    # Check if we found any green text
    if len(coords) > 0:
        # Get the bounding box of the non-black pixels
        x, y, w, h = cv2.boundingRect(coords)

        # Crop the image using the bounding box
        image = image[x - 1:x + w + 1, y - 1:y + h + 1]

    color_to_replace = np.array([199, 199, 199])  # OpenCV uses BGR format

    # Define the tolerance for the color (you may adjust this if needed)
    tolerance = 5

    # Create a mask for the color to replace
    lower_bound = np.maximum(color_to_replace - tolerance, 0)
    upper_bound = np.minimum(color_to_replace + tolerance, 255)
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # Replace the color with white (255, 255, 255)
    image[mask != 0] = [255, 255, 255]

    # Invert the colors (swap black and white)
    image = cv2.bitwise_not(image)

    return image


def locate_image(path, np_image, confidence=0.9):
    try:
        location = pyautogui.locate(path, np_image, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        location = None
    return location


def load_image(path):
    image = Image.open(path)
    # Convert the image to a NumPy array
    image_array = np.array(image)
    return cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)


def is_subimage(image, template):
    # Get dimensions of the image and the template
    image_h, image_w = image.shape[:2]
    template_h, template_w = template.shape[:2]

    # Iterate over every possible starting position in the image
    for y in range(image_h - template_h + 1):
        for x in range(image_w - template_w + 1):
            # Extract the subimage from the main image
            sub_image = image[y:y + template_h, x:x + template_w]

            # Check if the subimage matches the template
            if np.array_equal(sub_image, template):
                return True
    return False


def main():
    app = ApplicationWindow(debug_bot=1)
    app.run()


main()
