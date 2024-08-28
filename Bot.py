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
import gc
import logging
import os


custom_config_text = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


# Configure logging
logging.basicConfig(
    filename='bot_solver.log',  # Log to a file
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S'  # Date format
)


class NoCudaOrCPUModuleFound(ValueError):
    def __init__(self, message):
        super().__init__(message)


class ApplicationWindow:
    def __init__(self, title="Metin Bot", debug_bot=0):
        self.root = tk.Tk()
        self.root.title(title)

        # Set window size
        self.root.geometry(f"{450}x{600}")

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
        self.start_bot_loop_button = tk.Button(self.root, text="Start bot_loop", command=self.start_bot_loop)
        self.start_bot_loop_button.grid(row=2, column=0, pady=10, padx=10)

        self.stop_bot_loop_button = tk.Button(self.root, text="Stop bot_loop", command=self.stop_bot_loop)
        self.stop_bot_loop_button.grid(row=2, column=1, pady=10, padx=10)

        self.dropdown_label = tk.Label(self.root, text="Choose Metin Stone:")
        self.dropdown_label.grid(row=1, column=2, columnspan=2, pady=5)

        self.metin_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        self.dropdown = ttk.Combobox(self.root, values=self.metin_options, state="readonly")
        self.dropdown.grid(row=2, column=2, columnspan=2, pady=5)
        # Bind event to the dropdown
        self.dropdown.bind("<<ComboboxSelected>>", self.save_selected_option)

        self.entry_tesseract_path = tk.Label(self.root, text="Tesseract Path:")
        self.entry_tesseract_path.grid(row=4, column=0, pady=5)
        self.text_tesseract_path = tk.Entry(self.root, width=30)
        self.text_tesseract_path.grid(row=5, column=0, pady=5)

        self.entry_metin_hp_check = tk.Label(self.root, text="Metin HP Img:")
        self.entry_metin_hp_check.grid(row=4, column=1, pady=5)
        self.text_metin_hp_check = tk.Entry(self.root, width=30)
        self.text_metin_hp_check.grid(row=5, column=1, pady=5)

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

        self.apply = tk.Button(self.root, text="Reset skill", command=self.reset_skill)
        self.apply.grid(row=8, column=0, columnspan=4, pady=10)

        # Create a button to take a screenshot and center it
        self.screenshot_button = tk.Button(self.root, text="Take Screenshot", command=self.take_screenshot)
        self.screenshot_button.grid(row=8, column=0, columnspan=4, pady=10)

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

        self.set_bio_button = tk.Button(text="Set bio wait time",
                                        command=self.apply_bio_button_location)
        self.set_bio_button.grid(row=11, column=2, pady=10)

        # Create the Apply button and center it
        self.apply = tk.Button(self.root, text="Apply", command=self.apply_fields)
        self.apply.grid(row=12, column=0, columnspan=4, pady=10)

        self.cfg = {}
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
        self.cfg = cfg

        pytesseract.pytesseract.tesseract_cmd = cfg['tesseract_path']
        self.metin = Metin(cfg['metin_hp_img_path'], cfg['skills_to_activate'].split(), self.display_screenshot, debug_bot)
        self.metin.metin_stones = cfg['metin_stones']
        self.metin_options = [item['name'] for item in self.metin.metin_stones]
        self.metin.skills_cd = int(cfg['skills_cd']) if cfg['skills_cd'].isdigit() else 0
        self.metin.bio_cd = (int(cfg['bio_cd']) if cfg['bio_cd'].isdigit() else 0) * 60
        self.metin.bio_item_num = int(cfg['bio_item_num']) if cfg['bio_item_num'].isdigit() else 0
        self.dropdown['values'] = self.metin_options
        if self.metin_options:
            self.dropdown.set(self.metin_options[0])
            self.metin.selected_metin = self.metin_options[0]

        self.metin.window_title = self.cfg['window_name']

        self.metin.hp_bar_location = cfg['information_locations']['hp_bar_location']
        self.metin.hp_full_location = cfg['information_locations']['hp_full_location']
        self.metin.hp_full_pixel_colour = cfg['information_locations']['hp_full_pixel_colour']
        self.metin.scan_window_location = cfg['information_locations']['scan_window_location']
        self.metin.bio_location = cfg['information_locations']['bio_location']
        self.metin.cancel_location = cfg['information_locations']['cancel_location']
        self.metin.respawn_location = cfg['information_locations']['respawn_button_location']

        self.text_tesseract_path.insert(0, cfg['tesseract_path'])
        self.text_metin_hp_check.insert(0, cfg['metin_hp_img_path'])
        self.text_skills_check.insert(0, cfg['skills_to_activate'])
        self.text_window_name.insert(0, cfg['window_name'])
        self.text_skills_cd.insert(0, cfg['skills_cd'])
        self.text_bio_cd.insert(0, cfg['bio_cd'])
        self.text_bio_item_num.insert(0, cfg['bio_item_num'])

    def apply_fields(self):
        pytesseract.pytesseract.tesseract_cmd = self.text_tesseract_path.get()
        self.metin.window_title = self.text_window_name.get()

        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.cfg['metin_hp_img_path'] = self.text_metin_hp_check.get()
        self.cfg['skills_to_activate'] = self.text_skills_check.get()
        self.cfg['window_name'] = self.text_window_name.get()
        self.cfg['skills_cd'] = self.text_skills_cd.get()
        self.cfg['bio_cd'] = self.text_bio_cd.get()
        self.cfg['bio_item_num'] = self.text_bio_item_num.get()

        self.metin.skills_cd = int(self.text_skills_cd.get()) if self.text_skills_cd.get().isdigit() else 0
        self.metin.bio_cd = (int(self.text_bio_cd.get()) if self.text_bio_cd.get().isdigit() else 0) * 60 + 15
        self.metin.bio_item_num = int(self.text_bio_item_num.get()) if self.text_bio_item_num.get().isdigit() else 0
        self.metin.hp_bar_location = self.cfg['information_locations']['hp_bar_location']
        self.metin.hp_full_location = self.cfg['information_locations']['hp_full_location']
        self.metin.hp_full_pixel_colour = self.cfg['information_locations']['hp_full_pixel_colour']
        self.metin.scan_window_location = self.cfg['information_locations']['scan_window_location']
        self.metin.bio_location = self.cfg['information_locations']['bio_location']
        self.metin.cancel_location = self.cfg['information_locations']['cancel_location']
        self.metin.respawn_location = self.cfg['information_locations']['respawn_button_location']

        self.metin.skills_to_activate = self.cfg['skills_to_activate'].split()
        save_config(self.cfg, 'Config.json')

    def reset_skill(self):
        self.metin.skill_timer = 0

    def save_selected_option(self, event):
        self.metin.selected_metin = self.dropdown.get()

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
            self.cfg['information_locations']['hp_bar_location'] = output

    def apply_respawn_button_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]
            self.cfg['information_locations']['respawn_button_location'] = output

    def apply_hp_full_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            np_img = np.array(self.screenshot_image)
            np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
            pixel = np_img[self.end_y + self.screenshot_image_top, self.end_x + self.screenshot_image_left]
            self.cfg['information_locations']['hp_full_pixel_colour'] = pixel.tolist()

            self.cfg['information_locations']['hp_full_location'] = [self.end_x, self.end_y, self.start_x, self.start_y]

    def apply_bio_button_location(self):
        print('biooo')
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            self.cfg['information_locations']['bio_location'] = [self.end_x, self.end_y, self.start_x, self.start_y]

    def apply_scan_window_location(self):
        # z lava, z hora, z prava, z dola
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg['information_locations']['scan_window_location'] = output

    def apply_cancel_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg['information_locations']['cancel_location'] = output

    def start_bot_loop(self):
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
                self.image_label.grid(row=13, column=0, columnspan=4, pady=10)

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
    def __init__(self, metin_hp_img, skills_to_activate, display_screenshot, debug_bot):
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
        self.metin_hp_img = metin_hp_img
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
        self.hp_bar_location = None
        self.hp_full_location = None
        self.hp_full_pixel_colour = None
        self.scan_window_location = None
        self.bio_location = None
        self.cancel_location = None
        self.respawn_location = None
        self.skills_cd = 0
        self.bio_cd = 0
        self.running = False
        self.metin_stones = []
        self.selected_metin = None
        self.skill_timer_diff = 0
        self.bio_timer_diff = 0
        self.bio_cd_random = random.randint(10, 70)
        self.metin_destroy_time_diff = 0
        self.bot_time_diff = 0
        self.respawn_timer_diff = 0
        self.show_img = False
        self.image_to_display = None
        self.bio_item_num = 0
        self.aspect_low = 0
        self.aspect_high = 0
        self.circularity = 0
        self.weather = 0
        self.selected_weather = 0

        self.display_screenshot = display_screenshot
        self.lock = threading.Lock()
        self.model_initialize()

    def model_initialize(self):

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
        # upper_limit = 0.5
        # lower_limit = 0.1
        self.choose_weather()
        while self.running:
            with self.lock:
                # sleep_time = random.random() * (upper_limit - lower_limit) + lower_limit
                # time.sleep(sleep_time)

                np_image = self.get_np_image()
                if self.running:
                    self.bot_solver(np_image)
                if self.running:
                    self.death_check(np_image)
                if self.running:
                    self.deliver_bio()
                if self.running:
                    self.activate_skills()
                if self.running:
                    self.destroy_metin(np_image)

    def bot_solver(self, np_image):
        # 433 x 280
        box = 64
        space = 15

        try:
            location = pyautogui.locate('bot_images\\bot_check_bar2.png', np_image, confidence=0.7)
        except pyautogui.ImageNotFoundException:
            location = None

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

            np_image_text = preprocess_image(np_image[y1: y2, x1: x2])
            result = pytesseract.image_to_string(np_image_text, config=custom_config_text)

            result = result.strip()
            print(f'text to find {result}')
            logging.debug(f'Text to find: {result}')

            no_outputs = []
            outputs = []
            found = False
            for row in range(2):
                if found:
                    break
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
                        logging.debug(f'Output: {output}')
                        logging.debug(f'{output} in {result} -> {output in result}')
                        print(f'{output} in {result} -> {output in result}')
                        if output in result or output.lower() in result.lower():
                            print('BOT OCHRANA PRELOMENA')
                            logging.debug('Bot protection bypassed')
                            x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
                            y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
                            mouse_left_click(x_to_click, y_to_click, self.window_title)
                            self.bot_timer = 0
                            self.bot_time_diff = time.time() - self.bot_timer
                            found = True
                            time.sleep(2)
                            break
                # lower check
                if len(no_outputs) > 0 and not found:
                    logging.debug('No outputs found, random click')
                    print('**********************************')
                    print('***********ADO KUKAJ**************')
                    print('**********************************')
                    x1, x2, y1, y2 = random.choice(no_outputs)
                    print('RANDOM KLIK NA OCHRANU')
                    x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
                    y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
                    mouse_left_click(x_to_click, y_to_click, self.window_title)
                    self.bot_timer = 0
                    self.bot_time_diff = time.time() - self.bot_timer
                    found = True
                    if self.debug_bot == 1:
                        save_debug_image(np_image_captcha, np_image_text)
                    time.sleep(2)

                if len(no_outputs) == 0 and not found:
                    new_option, coords = try_common_replacements(result, outputs)
                    if new_option:
                        found = True
                        x1, x2, y1, y2 = coords
                        print('ZAMENENY KLIK NA OCHRANU')
                        logging.debug(f'Click after replacement: {new_option}')
                        x_to_click = self.window_left + location.left + 6 + x1 + (x2 - x1) / 2
                        y_to_click = self.window_top + location.top + 28 + y1 + (y2 - y1) / 2
                        mouse_left_click(x_to_click, y_to_click, self.window_title)
                        self.bot_timer = 0
                        self.bot_time_diff = time.time() - self.bot_timer

                if self.bot_time_diff > 5 and not found:
                    print('BOT OCHRANA ZATVORENA')
                    logging.debug('Bot protection closed')
                    mouse_left_click(cancel_x, cancel_y, self.window_title)
                    self.bot_timer = 0
                    time.sleep(2)
                    if self.debug_bot == 1:
                        save_debug_image(np_image_captcha, np_image_text)

            del np_image_captcha
            del np_img_captcha_option_resized
            del np_image_text
            gc.collect()

    def death_check(self, np_image):
        self.respawn_timer_diff = time.time() - self.respawn_timer
        if self.respawn_timer == 0 or self.respawn_timer != 0 and self.respawn_timer_diff >= 10:
            print('death_check')
            self.respawn_timer = time.time()
            try:
                respawn_location = pyautogui.locate('bot_images\\restart_img.png', np_image, confidence=0.7)
            except pyautogui.ImageNotFoundException:
                respawn_location = None

            if respawn_location is not None:
                respawn_x = self.window_left + respawn_location.left + respawn_location.width / 2
                respawn_y = self.window_top + respawn_location.top + respawn_location.height / 2
                mouse_left_click(respawn_x, respawn_y, self.window_title)
                time.sleep(0.5)
                press_button_multiple('ctrl+g', self.window_title)

    def deliver_bio(self):
        self.bio_timer_diff = time.time() - self.bio_timer
        if (self.bio_timer == 0 and self.bio_item_num > 0 or self.bio_timer != 0 and self.bio_timer_diff >= self.bio_cd
                + self.bio_cd_random and self.bio_item_num > 0):
            print('deliver_bio')
            self.bio_cd_random = random.randint(10, 70)
            self.bio_timer = time.time()
            self.bio_item_num -= 1
            bio_x, bio_y = self.bio_location[:2]
            bio_x += self.window_left
            bio_y += self.window_top
            mouse_left_click(bio_x, bio_y, self.window_title)
            time.sleep(1)
            np_image_bio = self.get_np_image()

            try:
                location = pyautogui.locate('bot_images\\bio_deliver.png', np_image_bio, confidence=0.7)
            except pyautogui.ImageNotFoundException:
                location = None

            if location is not None:
                deliver_x = self.window_left + location.left + location.width / 2
                deliver_y = self.window_top + location.top + location.height / 4
                mouse_left_click(deliver_x, deliver_y, self.window_title)

                press_button('esc', self.window_title)
                time.sleep(0.15)

            del np_image_bio
            gc.collect()

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

        selected_contour_pos, output_image = self.locate_metin(np_image_crop, x_middle, y_middle)
        # there are metins on screen
        if selected_contour_pos is not None:
            print('Metin Found')
            metin_pos_x, metin_pos_y = selected_contour_pos

            metin_pos_x += self.window_left + x1
            metin_pos_y += self.window_top + y1

            # no metin is being destroyed
            if not self.destroying_metin:
                print('Click at metin')
                press_button('z', self.window_title)
                time.sleep(0.15)
                press_button('y', self.window_title)
                mouse_left_click(metin_pos_x, metin_pos_y, self.window_title)
                self.destroying_metin = True
                self.metin_destroying_time = time.time()
                # # click at metin to show hp to see if its being destroyed already
                # a = time.time()
                # mouse_right_click(metin_pos_x, metin_pos_y, self.window_title)
                #
                # pixel_x, pixel_y = self.hp_full_location[:2]
                # pixel_x += self.window_left
                # pixel_y += self.window_top
                #
                # # pyautogui.moveTo(pixel_x, pixel_y)
                # time.sleep(0.5)
                # check_hp_np_image = self.get_np_image()
                # pixel_to_check = check_hp_np_image[pixel_y, pixel_x]
                #
                # print(
                #     f'pixel_to_check {pixel_to_check} | target_pixel_value {target_pixel_value}| click delay {a - time.time()}s')
                #
                # # press_button('esc', self.window_title)
                # if np.all(np.abs(pixel_to_check - target_pixel_value) <= 5):
                #     print('klik na metin')
                #     mouse_left_click(metin_pos_x, metin_pos_y, self.window_title)
                #     self.destroying_metin = True
                #     self.metin_destroying_time = time.time()
                # else:
                #     print('METIN SA UZ NICI')
                #     press_button('q', self.window_title)

                # HERE I WANT TO display_screenshot(output_image)
                if self.show_img:
                    self.image_to_display = output_image
                    self.display_screenshot()

            else:
                hp_bar_x1, hp_bar_y1, hp_bar_x2, hp_bar_y2 = self.hp_bar_location

                hp_bar = np_image[hp_bar_y1: hp_bar_y2, hp_bar_x1: hp_bar_x2]

                # check if metin was destroyed
                metin_is_alive = self.locate_metin_hp(hp_bar, 0.9)
                self.destroying_metin = metin_is_alive
                print(f'nici sa metin {metin_is_alive}')

                # HERE I WANT TO display_screenshot(output_image)
                if self.show_img:
                    self.image_to_display = output_image
                    self.display_screenshot()

                press_button('q', self.window_title)

                if not metin_is_alive:
                    # Cleanup
                    if 'output_image' in locals():
                        del output_image
                    if 'np_image_crop' in locals():
                        del np_image_crop
                    gc.collect()
                    return

                self.metin_destroy_time_diff = time.time() - self.metin_destroying_time

                if metin_is_alive and self.metin_destroy_time_diff > 4:
                    pixel_x, pixel_y = self.hp_full_location[:2]
                    pixel_x += self.window_left
                    pixel_y += self.window_top

                    pixel_to_check = np_image[pixel_y, pixel_x]
                    # HERE I WANT TO display_screenshot(output_image)
                    if self.show_img:
                        self.image_to_display = output_image
                        self.display_screenshot()

                    # check if after 10s metin is being destroyed or player is stuck
                    if np.all(np.abs(pixel_to_check - target_pixel_value) <= 5):
                        print('zatvaram metin okno')
                        choices = ['a', 'd']
                        cancel_x1, cancel_y1, cancel_x2, cancel_y2 = self.cancel_location

                        x_to_cancel = (self.window_left + cancel_x1 + (cancel_x2 - cancel_x1) / 2)
                        y_to_cancel = (self.window_top + cancel_y1 + (cancel_y2 - cancel_y1) / 2)

                        mouse_left_click(x_middle, y_middle, self.window_title)
                        metin_is_alive = False
                        time.sleep(0.2)
                        mouse_left_click(x_to_cancel, y_to_cancel, self.window_title)
                        press_button(random.choice(choices), self.window_title)
                        time.sleep(0.2)
                        press_button('q', self.window_title)
                        time.sleep(0.2)
                        press_button('q', self.window_title)
                        time.sleep(0.2)

        else:
            # HERE I WANT TO display_screenshot(np_image_crop)
            if self.show_img:
                self.image_to_display = np_image_crop
                self.display_screenshot()

            press_button('q', self.window_title)
            print("Searching for metin")

        # Cleanup
        if 'output_image' in locals():
            del output_image
        if 'np_image_crop' in locals():
            del np_image_crop
        # if 'check_hp_np_image' in locals():
        #     del check_hp_np_image
        if 'hp_bar' in locals():
            del hp_bar
        gc.collect()

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
                        cv2.circle(np_image, (x_middle, y_middle), 200, (255, 190, 200),
                                   2)  # The color is (255, 190, 200) and the thickness is 2

                        cur_distance = abs(x_middle - contour_center_x) + abs(y_middle - contour_center_y)

                        if cur_distance <= 200:
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

    def locate_metin_hp(self, np_image, confidence=0.8):
        try:
            location = pyautogui.locate(self.metin_hp_img, np_image, confidence=confidence)
        except pyautogui.ImageNotFoundException:
            location = None

        if location is not None:
            return True
        else:
            return False

    def bot_detection_solver(self, np_image):
        image = Image.fromarray(np_image)

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
        location = locate_image('bot_images\\settings_options.png', np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.5)

        np_image = self.get_np_image()
        # system options
        location = locate_image('bot_images\\system_options.png', np_image, 0.9)
        if location is None:
            return
        self.click_location_middle(location)
        time.sleep(0.45)

        np_image = self.get_np_image()
        # options menu
        location = locate_image('bot_images\\options_menu.png', np_image, 0.9)
        if location is None:
            return
        cancel_x = self.window_left + location.left + location.width - 15
        cancel_y = self.window_top + location.top + 15
        graphic_settings_x = self.window_left + location.left + 210
        graphic_settings_y = self.window_top + location.top + 50
        mouse_left_click(graphic_settings_x, graphic_settings_y, self.window_title)
        time.sleep(0.27)

        np_image = self.get_np_image()
        # graphics options
        location = locate_image('bot_images\\graphics_settings.png', np_image, 0.9)
        if location is None:
            return
        segment = location.height / 4
        graphic_options_x = self.window_left + location.left + location.width / 2
        graphic_options_y = self.window_top + location.top + segment * 3 + segment / 4
        mouse_left_click(graphic_options_x, graphic_options_y, self.window_title)
        time.sleep(0.33)

        np_image = self.get_np_image()
        # graphics options
        location = locate_image('bot_images\\weather.png', np_image, 0.9)
        if location is None:
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

                    move_x = self.window_left +  x1 + (x2 - x1) / 2
                    move_y = self.window_top + y1 + (y2 - y1) / 2
                    mouse_left_click(move_x, move_y, self.window_title)
                    self.selected_weather = counter + 1

                counter += 1
        time.sleep(0.2)

        mouse_left_click(cancel_x, cancel_y, self.window_title)

    def click_location_middle(self, location):
        system_options_x = self.window_left + location.left + location.width / 2
        system_options_y = self.window_top + location.top + location.height / 2
        mouse_left_click(system_options_x, system_options_y, self.window_title)


def resize_image(image):
    height, width = image.shape[:2]
    new_width = int(width * 2)
    new_height = int(height * 2)

    # Resize the image using a better upscaling method
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)


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
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([90, 255, 255])

    # Create a mask for green areas in the image
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Bitwise-AND the mask and the original image
    result = cv2.bitwise_and(image, image, mask=mask)

    # Convert the result to RGB for plotting with matplotlib
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    # Convert the image to grayscale for finding the non-black columns
    gray = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2GRAY)

    # Find the first and last column that contains non-black pixels
    non_black_columns = np.where(gray.max(axis=0) > 0)[0]
    if non_black_columns.size > 0:
        # Calculate the difference between consecutive column indices
        differences = np.diff(non_black_columns)

        # Identify segments of continuous columns (no large gaps)
        large_jump_indices = np.where(differences > 10)[0]  # Threshold for detecting gaps

        if large_jump_indices.size > 0:
            # Focus on the largest continuous segment (between two large jumps)
            segments = np.split(non_black_columns, large_jump_indices + 1)
            longest_segment = max(segments, key=len)

            # Set the left and right bounds to the start and end of the largest segment
            left_bound = longest_segment[0]
            right_bound = longest_segment[-1]
        else:
            # If there are no large jumps, consider the full range
            left_bound = non_black_columns[0]
            right_bound = non_black_columns[-1]

        # Crop the image to remove black areas from left and right
        cropped_image = result_rgb[:, left_bound - 5:right_bound + 5]
    else:
        # If no non-black pixels are found, return the original result_rgb
        cropped_image = result_rgb

    # Apply a binary threshold to make the text more distinct

    # Optionally, resize the image to make the characters more distinguishable
    resized_image = cv2.resize(cropped_image, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)

    return resized_image


def try_common_replacements(result, outputs, additional_replacements=None):
    # Define a dictionary of common OCR misrecognitions
    replacements = {
        '0': ['O'], 'O': ['0'],
        '1': ['I'], 'I': ['1'], 'l': ['1'], 'L': ['1'],
        '5': ['S'], 'S': ['5', '3'],
        '2': ['Z'], 'Z': ['2'],
        '6': ['G'], 'G': ['6'],
        '8': ['B'], 'B': ['8'],
        'F': ['7'], '7': ['F'],
        '3': ['S'], 'V': ['y'],
        'y': ['V'], 'h': ['A'],
        'A': ['h']
    }

    # If additional replacements are provided, extend the dictionary
    if additional_replacements:
        replacements.update(additional_replacements)
        # Ensure the additional replacements are bidirectional
        additional_reversed = {v: k for k, v in additional_replacements.items()}
        replacements.update(additional_reversed)

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


def save_image(img, name, folder):
    # Initialize file number
    file_number = 0

    # Check for the next available filename
    while True:
        file_name = f"{name}_{file_number}.png"
        file_path = os.path.join(folder, file_name)

        if not os.path.exists(file_path):
            break
        file_number += 1

    # Convert the numpy array to an image and save it
    image = Image.fromarray(img)
    image.save(file_path)
    print(f"Image saved as {file_path}")


def locate_image(path, np_image, confidence=0.9):
    try:
        location = pyautogui.locate(path, np_image, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        location = None
    return location


def main():
    app = ApplicationWindow(debug_bot=1)
    app.run()


main()
