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
import torch
from ultralytics import YOLO
import logging
import os
import hashlib


custom_config_text = f'--oem 1 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


# Configure logging
logging.basicConfig(
    filename='bot_solver.log',  # Log to a file
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

        self.stop_bot_loop_button = tk.Button(self.root, text="Stop bot_loop", command=self.stop_bot_loop)
        self.stop_bot_loop_button.grid(row=2, column=1, pady=10, padx=10)

        self.dropdown_label = tk.Label(self.root, text="Choose Metin Stone:")
        self.dropdown_label.grid(row=1, column=2, columnspan=2, pady=5)

        self.metin_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        self.dropdown = ttk.Combobox(self.root, values=self.metin_options, state="readonly")
        self.dropdown.grid(row=2, column=2, columnspan=2, pady=5)
        # Bind event to the dropdown
        self.dropdown.bind("<<ComboboxSelected>>", self.save_selected_option_metins)

        self.entry_tesseract_path = tk.Label(self.root, text="Tesseract Path:")
        self.entry_tesseract_path.grid(row=4, column=0, pady=5)
        self.text_tesseract_path = tk.Entry(self.root, width=30)
        self.text_tesseract_path.grid(row=5, column=0, pady=5)

        self.thief_gloves = ["Thief gloves 30m", "Thief gloves 5h"]
        self.entry_glove_cd = ttk.Combobox(self.root, values=self.thief_gloves, state="readonly")
        self.entry_glove_cd.grid(row=5, column=1, pady=5)
        # Bind event to the dropdown
        self.entry_glove_cd.bind("<<ComboboxSelected>>", self.save_selected_option_gloves)

        self.entry_bio_item_num = tk.Label(self.root, text="Bio item num:")
        self.entry_bio_item_num.grid(row=4, column=2, pady=5)
        self.text_bio_item_num = tk.Entry(self.root, width=30)
        self.text_bio_item_num.grid(row=5, column=2, pady=5)

        self.entry_skills_check = tk.Label(self.root, text="Skills to Activate:")
        self.entry_skills_check.grid(row=6, column=0, pady=5)
        self.text_skills_check = tk.Entry(self.root, width=30)
        self.text_skills_check.grid(row=7, column=0, pady=5)

        self.entry_skills_cd = tk.Label(self.root, text="Skills Cooldown:")
        self.entry_skills_cd.grid(row=6, column=1, pady=5)
        self.text_skills_cd = tk.Entry(self.root, width=30)
        self.text_skills_cd.grid(row=7, column=1, pady=5)

        self.entry_bio_cd = tk.Label(self.root, text="Bio Cooldown (min):")
        self.entry_bio_cd.grid(row=6, column=2, pady=5)
        self.text_bio_cd = tk.Entry(self.root, width=30)
        self.text_bio_cd.grid(row=7, column=2, pady=5)

        self.reset_skill = tk.Button(self.root, text="Reset skill", command=self.reset_skill)
        self.reset_skill.grid(row=8, column=1, pady=10)

        self.entry_metin_time = tk.Label(self.root, text="Metin time limit:")
        self.entry_metin_time.grid(row=8, column=0, pady=5)
        self.text_metin_time = tk.Entry(self.root, width=15)
        self.text_metin_time.grid(row=9, column=0, pady=5)

        # Create a button to take a screenshot and center it
        self.screenshot_button = tk.Button(self.root, text="Take Screenshot", command=self.take_screenshot)
        self.screenshot_button.grid(row=9, column=1, pady=10)

        self.entry_circle_r = tk.Label(self.root, text="Circle radius (px):")
        self.entry_circle_r.grid(row=8, column=2, pady=5)
        self.text_circle_r = tk.Entry(self.root, width=30)
        self.text_circle_r.grid(row=9, column=2, pady=5)

        self.set_metin_hp_bar_location = tk.Button(text="Set HP bar location",
                                                   command=self.apply_hp_bar_location)
        self.set_metin_hp_bar_location.grid(row=10, column=0, pady=10)

        self.set_metin_hp_full_location = tk.Button(text="Set full HP location",
                                                    command=self.apply_hp_full_location)
        self.set_metin_hp_full_location.grid(row=10, column=1, pady=10)

        self.set_respawn_button_location = tk.Button(text="Set respawn location",
                                                     command=self.apply_respawn_button_location)
        self.set_respawn_button_location.grid(row=10, column=2, pady=9)

        self.set_cancel_location = tk.Button(text="Set cancel location",
                                             command=self.apply_cancel_location)
        self.set_cancel_location.grid(row=11, column=0, pady=10)

        self.set_scan_window = tk.Button(text="Set scan window",
                                         command=self.apply_scan_window_location)
        self.set_scan_window.grid(row=11, column=1, pady=10)

        self.set_bio_button = tk.Button(text="Set bio",
                                        command=self.apply_bio_button_location)
        self.set_bio_button.grid(row=11, column=2, pady=10)

        self.set_thief_glove_button = tk.Button(text="Set thief glove", command=self.apply_thief_glove_button_location)
        self.set_thief_glove_button.grid(row=12, column=0, pady=10)

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
        cfg = load_config('Config.json')
        cfg_local = load_config('Config-local.json')
        self.cfg = cfg
        self.cfg_local = cfg_local

        pytesseract.pytesseract.tesseract_cmd = cfg['tesseract_path']

        self.text_tesseract_path.insert(0, cfg['tesseract_path'])

        if cfg_local:
            self.metin = Metin(cfg_local['skills_to_activate'].split(), self.display_screenshot, debug_bot)
            self.metin.skills_cd = int(cfg_local['skills_cd']) if cfg_local['skills_cd'].isdigit() else 0
            self.metin.bio_cd = (int(cfg_local['bio_cd']) if cfg_local['bio_cd'].isdigit() else 0) * 60
            self.metin.bio_item_num = int(cfg_local['bio_item_num']) if cfg_local['bio_item_num'].isdigit() else 0

            self.metin.window_title = self.cfg_local['window_name']
            self.text_skills_check.insert(0, cfg_local['skills_to_activate'])
            self.text_window_name.insert(0, cfg_local['window_name'])
            self.text_skills_cd.insert(0, cfg_local['skills_cd'])
            self.text_bio_cd.insert(0, cfg_local['bio_cd'])
            self.text_bio_item_num.insert(0, cfg_local['bio_item_num'])
            if 'information_locations' not in self.cfg_local:
                self.cfg_local['information_locations'] = {}

            if 'metin_time' not in self.cfg_local:
                self.cfg_local['metin_time'] = '0'

            if 'circle_r' not in self.cfg_local:
                self.cfg_local['circle_r'] = '50'

            self.load_cfg_local()
            self.metin.metin_time = int(cfg_local['metin_time']) if cfg_local['metin_time'].isdigit() else 0
            self.metin.circle_r = int(cfg_local['circle_r']) if cfg_local['circle_r'].isdigit() else 50
            self.text_metin_time.insert(0, cfg_local['metin_time'])
            self.text_circle_r.insert(0, cfg_local['circle_r'])

        else:

            self.cfg_local['information_locations'] = {}
            self.cfg_local['metin_time'] = '0'
            self.cfg_local['circle_r'] = '50'
            self.metin = Metin([], self.display_screenshot, debug_bot)
            self.metin.metin_time = 0
            self.metin.circle_r = 50

        self.metin.metin_stones = cfg['metin_stones']
        self.metin_options = [item['name'] for item in self.metin.metin_stones]

        self.dropdown['values'] = self.metin_options
        if self.metin_options:
            self.dropdown.set(self.metin_options[0])
            self.metin.selected_metin = self.metin_options[0]

        self.entry_glove_cd.set(self.thief_gloves[0])
        self.metin.selected_glove = self.thief_gloves[0]
        self.metin.thief_glove_cd = 60 * 30

        self.metin.replacements = cfg['replacements']

    def apply_fields(self):
        pytesseract.pytesseract.tesseract_cmd = self.text_tesseract_path.get()
        self.metin.window_title = self.text_window_name.get()

        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.cfg_local['skills_to_activate'] = self.text_skills_check.get()
        self.cfg_local['window_name'] = self.text_window_name.get()
        self.cfg_local['skills_cd'] = self.text_skills_cd.get()
        self.cfg_local['bio_cd'] = self.text_bio_cd.get()
        self.cfg_local['bio_item_num'] = self.text_bio_item_num.get()
        self.cfg_local['metin_time'] = self.text_metin_time.get()
        self.cfg_local['circle_r'] = self.text_circle_r.get()


        self.metin.skills_cd = int(self.text_skills_cd.get()) if self.text_skills_cd.get().isdigit() else 0
        self.metin.bio_cd = (int(self.text_bio_cd.get()) if self.text_bio_cd.get().isdigit() else 0) * 60 + 15
        self.metin.bio_item_num = int(self.text_bio_item_num.get()) if self.text_bio_item_num.get().isdigit() else 0
        self.metin.metin_time = int(self.text_metin_time.get()) if self.text_metin_time.get().isdigit() else 0
        self.metin.circle_r = int(self.text_circle_r.get()) if self.text_circle_r.get().isdigit() else 50

        self.load_cfg_local()

        self.metin.skills_to_activate = self.cfg_local['skills_to_activate'].split()
        save_config(self.cfg, 'Config.json')
        save_config(self.cfg_local, 'Config-local.json')

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

            if 'thief_glove_location' in info_locs:
                self.metin.thief_glove_location = info_locs['thief_glove_location']

            if 'bio_location' in info_locs:
                self.metin.bio_location = info_locs['bio_location']

            if 'cancel_location' in info_locs:
                self.metin.cancel_location = info_locs['cancel_location']

            if 'respawn_button_location' in info_locs:
                self.metin.respawn_location = info_locs['respawn_button_location']

    def reset_skill(self):
        self.metin.skill_timer = 0

    def save_selected_option_metins(self, event):
        self.metin.selected_metin = self.dropdown.get()

    def save_selected_option_gloves(self, event):
        value = self.entry_glove_cd.get()
        self.metin.selected_glove = value
        if value == 'Thief gloves 30m':
            self.metin.thief_glove_cd = 60 * 30  # 30min
        else:
            self.metin.thief_glove_cd = 5 * 60 * 60  # 5h

    def toggle_display_images(self, *args):
        if self.display_images_var.get() == 1:
            print("Image display is enabled.")
            self.metin.show_img = True
        else:
            print("Image display is disabled.")
            self.metin.show_img = False

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

            self.cfg_local['information_locations']['hp_full_location'] = [self.end_x, self.end_y, self.start_x, self.start_y]

    def apply_bio_button_location(self):
        print('biooo')
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            self.cfg_local['information_locations']['bio_location'] = [self.end_x, self.end_y, self.start_x, self.start_y]

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
        self.metin.metin_destroying_time = 0
        self.metin.solved_at = 0
        self.metin.solving_bot_check = False
        self.metin.running = False

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
        self.lower = None
        self.upper = None
        self.solved_at = 0
        self.solving_bot_check = False
        self.contour_low = 0
        self.contour_high = 0
        self.destroying_metin = False
        self.metin_destroying_time = 0
        self.model_cuda = None
        self.model_cpu = None
        self.window_title = None
        self.skill_timer = 0
        self.label_keys = []
        self.skills_to_activate = skills_to_activate
        self.bot_timer = 0
        self.bio_timer = 0
        self.respawn_timer = 0
        self.metin_time = 0
        self.hp_bar_location = None
        self.hp_full_location = None
        self.hp_full_pixel_colour = None
        self.scan_window_location = None
        self.thief_glove_location = None
        self.bio_location = None
        self.cancel_location = None
        self.respawn_location = None
        self.skills_cd = 0
        self.bio_cd = 0
        self.thief_glove_cd = 0
        self.thief_glove_time_diff = 0
        self.thief_glove_timer = 0
        self.running = False
        self.metin_stones = []
        self.thief_glove = []
        self.selected_metin = None
        self.selected_glove = None
        self.skill_timer_diff = 0
        self.bio_timer_diff = 0
        self.bio_cd_random = random.randint(10, 70)
        self.metin_destroy_time_diff = 0
        self.bot_time_diff = 0
        self.respawn_timer_diff = 0
        self.show_img = False
        self.bio_item_num = 0
        self.aspect_low = 0
        self.aspect_high = 0
        self.circularity = 0
        self.weather = 0
        self.selected_weather = 0
        self.replacements = {}
        self.circle_r = 50
        self.settings_options = None
        self.bot_check_bar = None
        self.restart = None
        self.bio_deliver = None
        self.system_options = None
        self.options_menu = None
        self.graphics_settings = None
        self.weather_image = None
        self.template = None
        self.image_to_display = None
        self.metin_hp_img = None
        self.cancel_metin_img = None
        self.thief_glove_30m = None
        self.thief_glove_5h = None
        self.inventory = None
        self.metin_hp_img = None
        self.text_hash_map = None

        self.load_images()

        self.display_screenshot = display_screenshot
        self.lock = threading.Lock()
        self.initialize()

    def initialize(self):

        path = 'models_yolov8/'
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        if 'cu' in torch.__version__:
            print("CUDA-enabled version of PyTorch is installed.")
            self.model_cuda = YOLO(f'{path}best.pt')
        else:
            print("CPU-only version of PyTorch is installed.")
            self.model_cpu = YOLO(f'{path}best.onnx', task='detect')

        combinations = [a + b for a in characters for b in characters]
        combo_to_id = {combo: idx for idx, combo in enumerate(combinations)}
        self.label_keys = list(combo_to_id.keys())

        with open("hash_combinations.json", "r") as json_file:
            self.text_hash_map = json.load(json_file)

    def load_images(self):
        self.settings_options = load_image('bot_images\\settings_options.png')
        self.bot_check_bar = load_image('bot_images\\bot_check_bar2.png')
        self.restart = load_image('bot_images\\restart_img.png')
        self.cancel_metin_img = load_image('bot_images\\cancel_metin_button.png')
        self.bio_deliver = load_image('bot_images\\bio_deliver.png')
        self.system_options = load_image('bot_images\\system_options.png')
        self.options_menu = load_image('bot_images\\options_menu.png')
        self.graphics_settings = load_image('bot_images\\graphics_settings.png')
        self.weather_image = load_image('bot_images\\weather.png')
        self.template = load_image('bot_images\\metin_hp2.png')
        self.metin_hp_img = load_image('bot_images\\metin_hp2.png')
        self.thief_glove_30m = load_image('bot_images\\zlodejky_male.png')
        self.thief_glove_5h = load_image('bot_images\\zlodejky_velke.png')
        self.inventory = load_image('bot_images\\inventory.png')

    def bot_loop(self):
        metin_mask = {}
        for metin_config in self.metin_stones:
            if metin_config['name'] == self.selected_metin:
                metin_mask = metin_config
                self.contour_low = metin_config['contourLow']
                self.contour_high = metin_config['contourHigh']
                self.aspect_low = metin_config['aspect_low'] / 100.0
                self.aspect_high = metin_config['aspect_high'] / 100.0
                self.circularity = metin_config['circularity'] / 1000.0
                self.weather = metin_config['weather']
                break
        self.lower, self.upper = create_low_upp(metin_mask)

        time.sleep(2)
        upper_limit = 0.5
        lower_limit = 0.1
        self.choose_weather()

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
                    self.deliver_bio()
                if self.running:
                    self.put_thief_glove(np_image)
                if self.running:
                    self.activate_skills()
                if self.running:
                    self.image_to_display = self.destroy_metin(np_image)

                    if self.show_img:
                        self.display_screenshot()
                    print(f'Iteration execution time {time.time() - loop_time}s')

    def bot_solver(self, np_image):
        # 433 x 280
        box = 64
        space = 15
        location = locate_image(self.bot_check_bar, np_image, confidence=0.9)

        if location is not None:
            print('bot_solver')
            logging.info('Bot solver started')

            cancel_x = self.window_left + location.left + location.width + 13
            cancel_y = self.window_top + location.top + location.height / 2

            self.bot_timer = self.bot_timer if self.bot_timer != 0 else time.time()
            self.bot_time_diff = time.time() - self.bot_timer

            x1 = self.window_left + location.left + 6
            x2 = x1 + 222
            y1 = self.window_top + location.top + 28
            y2 = y1 + 143
            np_image_captcha = np_image[y1: y2, x1: x2]

            x1 = self.window_left + location.left
            x2 = x1 + 245
            y1 = self.window_top + location.top + 180
            y2 = y1 + 40
            np_image_text = np_image[y1: y2, x1: x2]
            if self.debug_bot == 1:
                save_debug_image2(np_image_text)

            np_image_text = preprocess_image(np_image_text)
            image_hash = hashlib.md5(np_image_text).hexdigest()

            if image_hash in self.text_hash_map:
                logging.info(f'Hash found in hash map')
                result = self.text_hash_map[image_hash]
            else:
                logging.info(f'Hash not found in hash map')
                result = pytesseract.image_to_string(np_image_text, config=custom_config_text)
                result = result.strip()

            print(f'text to find {result}')
            logging.info(f'Text to find: {result}')
            no_outputs = []
            outputs = []
            for row in range(2):
                for column in range(3):
                    x1, y1 = box * column + space * column, box * row + space * row  # z lava, z hore
                    x2, y2 = box * (column + 1) + space * column, box * (row + 1) + space * row  # z prava, z dola
                    # Extract text using pytesseract
                    np_img_captcha_option_resized = resize_image(np_image_captcha[y1: y2, x1: x2])
                    # self.metin.solve_captcha
                    output = self.bot_detection_solver(np_img_captcha_option_resized)
                    if output is None:
                        no_outputs.append((x1, x2, y1, y2))
                    else:
                        output = output.strip()
                        outputs.append((output, (x1, x2, y1, y2)))

                        print(f'output = {output}')
                        logging.info(f'Output: {output}')
                        logging.info(f'{output} in {result} -> {output in result}')
                        print(f'{output} in {result} -> {output in result}')
                        if self.output_in_result(output, result, location, x1, x2, y1, y2):
                            return

            for output_tup in outputs:
                output, coords = output_tup
                output_reversed = output[::-1]
                if self.output_in_result(output_reversed, result, location, x1, x2, y1, y2):
                    return

            if len(no_outputs) > 0:
                logging.info('No outputs found, random click')
                print('No outputs found, random click')
                x1, x2, y1, y2 = random.choice(no_outputs)
                x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
                y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
                mouse_left_click(x_to_click, y_to_click, self.window_title)
                # pyautogui.moveTo(x_to_click, y_to_click)
                self.bot_timer = 0
                self.bot_time_diff = time.time() - self.bot_timer
                if self.debug_bot == 1:
                    save_debug_image(np_image_captcha, np_image_text)
                return

            else:
                new_option, coords = try_common_replacements(result, outputs, self.replacements)
                if new_option:
                    x1, x2, y1, y2 = coords
                    print(f'Click after replacement: {new_option}')
                    logging.info(f'Click after replacement: {new_option}')
                    x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
                    y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
                    mouse_left_click(x_to_click, y_to_click, self.window_title)
                    # pyautogui.moveTo(x_to_click, y_to_click)
                    self.bot_timer = 0
                    self.bot_time_diff = time.time() - self.bot_timer
                    return

            if len(result) < 2:
                for output_tup in outputs:
                    output, coords = output_tup
                    if result in output or result.lower() in output.lower():
                        print('Bot result less then 2 try')
                        logging.info('Bot result less then 2 try')
                        x1, x2, y1, y2 = coords
                        x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
                        y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
                        mouse_left_click(x_to_click, y_to_click, self.window_title)
                        # pyautogui.moveTo(x_to_click, y_to_click)
                        self.bot_timer = 0
                        self.bot_time_diff = time.time() - self.bot_timer
                        if self.debug_bot == 1:
                            save_debug_image(np_image_captcha, np_image_text)
                        return

            print('Bot protection closed')
            logging.info('Bot protection closed')
            mouse_left_click(cancel_x, cancel_y, self.window_title)
            # pyautogui.moveTo(cancel_x, cancel_y)
            self.bot_timer = 0
            if self.debug_bot == 1:
                save_debug_image(np_image_captcha, np_image_text)

    def output_in_result(self, output, result, location, x1, x2, y1, y2):
        if output.lower() in result.lower():
            print('Bot protection bypassed')
            logging.info('Bot protection bypassed')
            x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
            y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
            mouse_left_click(x_to_click, y_to_click, self.window_title)

            self.bot_timer = 0
            self.bot_time_diff = time.time() - self.bot_timer
            return True

        return False

    def death_check(self, np_image):
        self.respawn_timer_diff = time.time() - self.respawn_timer
        if self.respawn_timer == 0 or self.respawn_timer != 0 and self.respawn_timer_diff >= 5:
            print('death_check')
            self.respawn_timer = time.time()

            respawn_location = locate_image(self.restart, np_image, confidence=0.7)

            if respawn_location is not None:
                respawn_x = self.window_left + respawn_location.left + respawn_location.width / 2
                respawn_y = self.window_top + respawn_location.top + respawn_location.height / 2
                mouse_left_click(respawn_x, respawn_y, self.window_title)
                time.sleep(1)
                press_button_multiple('ctrl+g', self.window_title)

    def deliver_bio(self):
        self.bio_timer_diff = time.time() - self.bio_timer
        if (self.bio_timer == 0 and self.bio_item_num > 0 or self.bio_timer != 0 and self.bio_timer_diff >= self.bio_cd
                + self.bio_cd_random and self.bio_item_num > 0):
            print('deliver_bio')
            self.bio_cd_random = random.randint(30, 300)
            self.bio_timer = time.time()
            self.bio_item_num -= 1
            bio_x, bio_y = self.bio_location[:2]
            bio_x += self.window_left
            bio_y += self.window_top
            mouse_left_click(bio_x, bio_y, self.window_title)
            time.sleep(1)
            np_image_bio = self.get_np_image()

            location = locate_image(self.bio_deliver, np_image_bio, confidence=0.7)

            if location is not None:
                deliver_x = self.window_left + location.left + location.width / 2
                deliver_y = self.window_top + location.top + location.height / 4
                mouse_left_click(deliver_x, deliver_y, self.window_title)

                time.sleep(random.randint(1, 2))
                press_button('esc', self.window_title)
                time.sleep(0.15)

    def put_thief_glove(self, np_image):
        self.thief_glove_time_diff = time.time() - self.thief_glove_timer
        if self.thief_glove_timer == 0 or self.thief_glove_timer != 0 and self.thief_glove_time_diff >= self.thief_glove_cd:
            print('put_thief_glove')

            inventory = locate_image(self.inventory, np_image)

            if inventory is None:
                press_button('i', self.window_title)
                np_image = self.get_np_image()
                time.sleep(2)

            x1, y1, x2, y2 = self.thief_glove_location
            thief_glove_slot = np_image[y1: y2, x1: x2]

            if self.selected_glove == 'Thief gloves 30m':
                gloves = locate_image(self.thief_glove_30m, thief_glove_slot)
            else:
                gloves = locate_image(self.thief_glove_5h, thief_glove_slot)

            if gloves is not None:
                x = x1 + self.window_left + gloves.left + gloves.width / 2
                y = y1 + self.window_top + gloves.top + gloves.height / 2
                print('right click glove')
                mouse_right_click(x, y, self.window_title)
                time.sleep(1)

            self.thief_glove_timer = time.time()

    def activate_skills(self):
        self.skill_timer_diff = time.time() - self.skill_timer
        if self.skill_timer == 0 or self.skill_timer != 0 and self.skill_timer_diff >= self.skills_cd:
            print('activate_skills')
            self.skill_timer = time.time()
            press_button_multiple('ctrl+g', self.window_title)
            time.sleep(0.15)
            for skill in self.skills_to_activate:
                press_button(skill, self.window_title)
                time.sleep(2)
            press_button_multiple('ctrl+g', self.window_title)

    def destroy_metin(self, np_image):
        target_pixel_value = np.array(self.hp_full_pixel_colour)
        x1, y1, x2, y2 = self.scan_window_location  # z lava, z hora, z prava, z dola
        np_image_crop = np_image[y1: y2, x1: x2]
        x_middle = self.window_left + (x2 - x1) // 2
        y_middle = self.window_top + (y2 - y1) // 2
        metin_pos, image_to_display = self.locate_metin(np_image_crop, x_middle, y_middle)
        # there are metins on screen
        if metin_pos is not None:
            print('Metin Found')
            metin_pos_x, metin_pos_y = metin_pos

            metin_pos_x += self.window_left + x1
            metin_pos_y += self.window_top + y1

            # no metin is being destroyed
            if not self.destroying_metin:
                print('Click at metin')

                press_button('z', self.window_title)
                time.sleep(0.15)
                press_button('y', self.window_title)
                
                mouse_right_click(metin_pos_x, metin_pos_y, self.window_title)
                sleep_time = random.random() * (0.5 - 0.3) + 0.3
                time.sleep(sleep_time)
                np_image_check_hp = self.get_np_image()

                pixel_x, pixel_y = self.hp_full_location[:2]
                pixel_x += self.window_left
                pixel_y += self.window_top

                pixel_to_check = np_image_check_hp[pixel_y, pixel_x]
                pixel_to_check = pixel_to_check[::-1]

                print(f'pixel_to_check {pixel_to_check} target_pixel_value {target_pixel_value}')
                if not np.all(np.abs(pixel_to_check - target_pixel_value) <= 5):
                    self.cancel_metin_window(np_image, x_middle, y_middle)
                    return image_to_display


                mouse_left_click(metin_pos_x, metin_pos_y, self.window_title)
                self.destroying_metin = True
                self.metin_destroying_time = time.time()
                time.sleep(2)

            else:
                hp_bar_x1, hp_bar_y1, hp_bar_x2, hp_bar_y2 = self.hp_bar_location

                hp_bar = np_image[hp_bar_y1: hp_bar_y2, hp_bar_x1: hp_bar_x2]

                # check if metin was destroyed
                metin_is_alive = self.locate_metin_hp(hp_bar)
                self.destroying_metin = metin_is_alive
                print(f'nici sa metin {metin_is_alive}')

                # HERE I WANT TO display_screenshot(output_image)
                if not metin_is_alive:
                    # Cleanup
                    return image_to_display

                else:
                    self.metin_destroy_time_diff = time.time() - self.metin_destroying_time
                    press_button('q', self.window_title)

                    if self.metin_time != 0 and self.metin_destroy_time_diff > self.metin_time:
                        print('Metin is not being destroyed, stopping')
                        self.cancel_metin_window(np_image, x_middle, y_middle)

                    if self.metin_time != 0 and self.metin_destroy_time_diff > 8:
                        pixel_x, pixel_y = self.hp_full_location[:2]
                        pixel_x += self.window_left
                        pixel_y += self.window_top

                        pixel_to_check = np_image[pixel_y, pixel_x]
                        pixel_to_check = pixel_to_check[::-1]
                        # HERE I WANT TO display_screenshot(output_image)

                        print(f'pixel_to_check {pixel_to_check} target_pixel_value {target_pixel_value}')
                        # check if after 10s metin is being destroyed or player is stuck
                        if np.all(np.abs(pixel_to_check - target_pixel_value) <= 5):
                            self.cancel_metin_window(np_image, x_middle, y_middle)

        else:
            # HERE I WANT TO display_screenshot(np_image_crop)
            press_button('q', self.window_title)
            print("Searching for metin")

        return image_to_display

    def cancel_metin_window(self, np_image, x_middle, y_middle):
        print('zatvaram metin okno')
        choices = ['a', 'd']
        cancel_x1, cancel_y1, cancel_x2, cancel_y2 = self.cancel_location
        cancel_area = np_image[cancel_y1:cancel_y2, cancel_x1:cancel_x2]
        location = locate_image(self.cancel_metin_img, cancel_area)
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
                    aspect_ratio = float(w) / h
                    area = cv2.contourArea(contour)
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * (area / (perimeter * perimeter))
                    if self.aspect_low < aspect_ratio < self.aspect_high and circularity > self.circularity:

                        cv2.rectangle(np_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle

                        contour_center_x = x + w // 2
                        contour_center_y = y + h // 2

                        # Draw a line from the middle of the screenshot to the center of the contour
                        cv2.line(np_image, (x_middle, y_middle), (contour_center_x, contour_center_y),
                                 (255, 190, 200), 2)
                        # Optionally, you can calculate the distance between the middle of the screenshot and the contour center
                        # Draw a circle around the point (x_middle, y_middle) with a radius of 300px
                        cv2.circle(np_image, (x_middle, y_middle), self.circle_r, (255, 190, 200),
                                   2)  # The color is (255, 190, 200) and the thickness is 2

                        cur_distance = abs(x_middle - contour_center_x) + abs(y_middle - contour_center_y)

                        if cur_distance <= self.circle_r:
                            continue

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

    def locate_metin_hp(self, np_image_hp_bar):
        return is_subimage(np_image_hp_bar, self.template)

    def bot_detection_solver(self, np_image_captcha_option):
        image = Image.fromarray(np_image_captcha_option)

        if self.model_cpu is not None:
            results = self.model_cpu.predict(image, imgsz=(128, 128))
            if len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    class_ids = boxes.cls.cpu().numpy()  # Get class IDs
                    confidences = boxes.conf.cpu().numpy()  # Get confidence scores
                    max_confidence = 0
                    output = None
                    # Print class IDs and their corresponding confidence scores
                    for i, class_id in enumerate(class_ids):
                        confidence = confidences[i]
                        if confidence > max_confidence:
                            max_confidence = confidence
                            output = self.label_keys[int(class_id)]
                    return output
            return None

        elif self.model_cuda is not None:
            results = self.model_cuda.predict(image)
            for result in results:
                boxes = result.boxes
                max_confidence = 0
                output = None
                for box in boxes:
                    confidence = box.conf
                    if confidence > max_confidence:
                        max_confidence = confidence
                        output = self.label_keys[int(box.cls[0])]
                return output
            return None
        else:
            raise NoCudaOrCPUModuleFound

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
        time.sleep(2)
        if self.selected_weather == self.weather:
            return
        np_image = self.get_np_image()
        # options
        location = locate_image(self.settings_options, np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.5)

        np_image = self.get_np_image()
        # system options
        location = locate_image(self.system_options, np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.45)

        np_image = self.get_np_image()
        # options menu
        location = locate_image(self.options_menu, np_image, 0.9)
        if location is None:
            print('options menu none')
            return
        cancel_x = self.window_left + location.left + location.width - 15
        cancel_y = self.window_top + location.top + 15
        graphic_settings_x = self.window_left + location.left + 310
        graphic_settings_y = self.window_top + location.top + 50
        mouse_left_click(graphic_settings_x, graphic_settings_y, self.window_title)
        time.sleep(0.27)

        np_image = self.get_np_image()
        # graphics options
        location = locate_image(self.graphics_settings, np_image, 0.9)
        if location is None:
            print('graphic options none')
            return
        segment = location.height / 4
        graphic_options_x = self.window_left + location.left + location.width / 2
        graphic_options_y = self.window_top + location.top + segment * 3 + segment / 4
        mouse_left_click(graphic_options_x, graphic_options_y, self.window_title)
        time.sleep(0.33)

        np_image = self.get_np_image()
        # weather
        location = locate_image(self.weather_image, np_image, 0.9)
        if location is None:
            print('weather none')
            return
        space = 24
        width = 86
        height = 50
        counter = 0
        for row in range(4):
            for column in range(3):
                if counter == self.weather - 1:
                    print(counter)
                    y1 = location.top + height * row
                    y2 = y1 + height
                    x1 = location.left + width * column + space * column
                    x2 = x1 + width

                    move_x = self.window_left + x1 + (x2 - x1) / 2
                    move_y = self.window_top + y1 + (y2 - y1) / 2
                    mouse_left_click(move_x, move_y, self.window_title)
                    self.selected_weather = counter + 1

                counter += 1
        time.sleep(1)

        mouse_left_click(cancel_x, cancel_y, self.window_title)

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
        pyautogui.click()


def mouse_right_click(pos_x, pos_y, window_title):
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        pyautogui.moveTo(pos_x, pos_y)
        pyautogui.rightClick()


def preprocess_image(image):
    # Convert the image to grayscale
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the lower and upper range for the green color
    lower_green = np.array([40, 100, 100])
    upper_green = np.array([80, 255, 255])

    # Create a mask for green areas in the image
    mask = cv2.inRange(hsv, lower_green, upper_green)

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

    # Define the color you want to replace (red 153, green 255, blue 51)
    color_to_replace = np.array([51, 255, 153])  # OpenCV uses BGR format

    # Define the tolerance for the color (you may adjust this if needed)
    tolerance = 30

    # Create a mask for the color to replace
    lower_bound = np.maximum(color_to_replace - tolerance, 0)
    upper_bound = np.minimum(color_to_replace + tolerance, 255)
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # Replace the color with white (255, 255, 255)
    image[mask != 0] = [255, 255, 255]

    # Invert the colors (swap black and white)
    image = cv2.bitwise_not(image)

    return image


def try_common_replacements(result, outputs, replacements):
    # Iterate through each output in the list
    for output in outputs:
        # Start with the original output
        modified_output, coords = output

        # Try each replacement one by one
        for key, values in replacements.items():
            # Only apply the replacement if the key or value is in the result
            for value in values:
                if key in result or value in result:
                    # Replace the key in the modified output
                    modified_output = modified_output.replace(key, value)

                    # Check if the modified output matches the result
                    if modified_output in result or modified_output.lower() in result.lower():
                        return modified_output, coords  # Found a match

    return '', (0, 0, 0, 0)  # No match found


def save_debug_image(np_image_captcha, np_image_text, folder="debug-images"):
    # Ensure the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    save_image(np_image_captcha, 'debug_captcha', folder)
    save_image(np_image_text, 'debug_desire', folder)

def save_debug_image2(np_image, folder="debug-images"):
    # Ensure the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    save_image(np_image, 'debug_desire_no_processed', folder)


def save_image(img, name, folder):
    # Initialize file number
    file_number = 0

    # Check for the next available filename
    while True:
        file_name = f'{name}_{file_number}.png'
        file_path = os.path.join(folder, file_name)

        if not os.path.exists(file_path):
            break
        file_number += 1

    # Convert the numpy array to an image and save it
    image = Image.fromarray(img)
    image.save(file_path)
    print(f'Image saved as {file_path}')
    logging.info(f'Image saved as {file_path}')


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
