import numpy as np
import pygetwindow as gw
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, Canvas, messagebox
import threading
import re
from Modules.BotManager import BotManager
from Utils.Utils import load_config, save_config, get_window_screenshot, process_possible_double_values, \
    process_text_to_digit
import logging


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
    bot_manager: BotManager
    def __init__(self, title='Metin Bot'):
        self.root = tk.Tk()
        self.root.title(title)

        self.root.geometry(f'{450}x{600}')

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        self.pirate_elixir_var = tk.BooleanVar()
        self.display_images_var = tk.BooleanVar()
        self.destroy_event_stones = tk.BooleanVar()

        self.display_checkbox = tk.Checkbutton(self.root, text="Display", variable=self.display_images_var)
        self.display_checkbox.grid(row=0, column=0, padx=5, pady=5)

        self.display_images_var.trace_add("write", self.toggle_display_images)

        self.entry_window_name = tk.Label(self.root, text="Window name:")
        self.entry_window_name.grid(row=0, column=0, columnspan=4, pady=5)
        self.text_window_name = tk.Entry(self.root, width=15)
        self.text_window_name.grid(row=1, column=0, columnspan=4, pady=5)

        self.dropdown_bot_label = tk.Label(self.root, text="Choose Bot:")
        self.dropdown_bot_label.grid(row=1, column=0, pady=5)
        self.bot_options = ["Metin bot", "Fish bot", "Mining bot"]
        self.dropdown_bot = ttk.Combobox(self.root, values=self.bot_options, state="readonly")
        self.dropdown_bot.grid(row=2, column=0, pady=5)

        self.start_bot_button = tk.Button(self.root, text="Start bot", command=self.start_bot_thread)
        self.start_bot_button.grid(row=2, column=1, pady=10, padx=10)

        self.stop_bot_loop_button = tk.Button(self.root, text="Stop bot", command=self.stop_bot_loop)
        self.stop_bot_loop_button.grid(row=2, column=2, pady=10, padx=10)

        self.event_checkbox = tk.Checkbutton(self.root, text="Event stone", variable=self.destroy_event_stones)
        self.event_checkbox.grid(row=4, column=1, padx=5, pady=5)

        self.entry_tesseract_path = tk.Label(self.root, text="Tesseract Path:")
        self.entry_tesseract_path.grid(row=4, column=0, pady=5)
        self.text_tesseract_path = tk.Entry(self.root, width=20)
        self.text_tesseract_path.grid(row=5, column=0, pady=5)

        self.reset_skill = tk.Button(self.root, text="Set skills", command=self.set_skills)
        self.reset_skill.grid(row=5, column=1, pady=10)


        self.dropdown_metin_label = tk.Label(self.root, text="Choose Metin Stone:")
        self.dropdown_metin_label.grid(row=4, column=2, columnspan=2, pady=5)
        self.metin_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        self.dropdown_metin = ttk.Combobox(self.root, values=self.metin_options, state="readonly")
        self.dropdown_metin.grid(row=5, column=2, pady=5)

        self.dropdown_metin.bind("<<ComboboxSelected>>", self.save_selected_option_metins)

        self.mining_wait_time_label = tk.Label(self.root, text="Mining wait time:")
        self.mining_wait_time_label.grid(row=8, column=0, columnspan=1, pady=5)
        self.text_mining_wait_time = tk.Entry(self.root, width=15)
        self.text_mining_wait_time.grid(row=9, column=0, columnspan=1, pady=5)

        self.entry_metin_time_treshold = tk.Label(self.root, text="Metin destroy time MAX:")
        self.entry_metin_time_treshold.grid(row=8, column=1, columnspan=1, pady=5)
        self.text_metin_time_treshold = tk.Entry(self.root, width=15)
        self.text_metin_time_treshold.grid(row=9, column=1, columnspan=1, pady=5)

        self.destroy_event_stones.trace_add("write", self.toggle_destroy_event_stones)
        # self.reset_skill = tk.Button(self.root, text="Reset skill", command=self.reset_skill)
        # self.reset_skill.grid(row=8, column=1, pady=10)
        self.class_skills = {"War-Mental":{"Silne telo":'bot_images\\War-Silne-Telo.png'},
                             "Sura-Weapon": {"Cepel":'bot_images\\Sura-Cepel.png', "Zacarovane brnenie": 'bot_images\\Sura-ZacBrn.png', "Strach":'bot_images\\Sura-Strach.png'},
                             "Sura-Spell": {"Ohen":'bot_images\\Sura-duch-plamen.png', "Magicke brnenie": 'bot_images\\Sura-temn-ochrana.png'},
                             "Shaman-Buff":{"Kritik": 'bot_images\\Saman-Krit.png'}}
        self.dropdown_class_label = tk.Label(self.root, text="Choose class:")
        self.dropdown_class_label.grid(row=8, column=2, columnspan=1, pady=5)
        self.dropdown_class = ttk.Combobox(self.root, values=list(self.class_skills.keys()), state="readonly")
        self.dropdown_class.grid(row=9, column=2, pady=5)
        self.dropdown_class.set("War-Mental")

        self.dropdown_class.bind("<<ComboboxSelected>>", self.save_selected_option_class)


        self.entry_turn_off_bot = tk.Label(self.root, text="Stuck time MAX:")
        self.entry_turn_off_bot.grid(row=10, column=0, columnspan=1, pady=5)
        self.text_turn_off_bot  = tk.Entry(self.root, width=15)
        self.text_turn_off_bot.grid(row=11, column=0, columnspan=1, pady=5)

        self.entry_cape = tk.Label(self.root, text="Cape time:")
        self.entry_cape.grid(row=10, column=1, columnspan=1, pady=5)
        self.text_entry_cape  = tk.Entry(self.root, width=15)
        self.text_entry_cape.grid(row=11, column=1, columnspan=1, pady=5)

        self.entry_cape_key = tk.Label(self.root, text="Cape key:")
        self.entry_cape_key.grid(row=10, column=2, columnspan=1, pady=5)
        self.text_entry_cape_key  = tk.Entry(self.root, width=15)
        self.text_entry_cape_key.grid(row=11, column=2, columnspan=1, pady=5)


        self.entry_web_hook = tk.Label(self.root, text="Webhook:")
        self.entry_web_hook.grid(row=12, column=0, columnspan=1, pady=5)
        self.text_entry_web_hook  = tk.Entry(self.root, width=15)
        self.text_entry_web_hook.grid(row=13, column=0, columnspan=1, pady=5)

        self.entry_user_id = tk.Label(self.root, text="Discord User ID:")
        self.entry_user_id.grid(row=12, column=1, columnspan=1, pady=5)
        self.text_entry_user_id  = tk.Entry(self.root, width=15)
        self.text_entry_user_id.grid(row=13, column=1, columnspan=1, pady=5)


        self.pirate_checkbox = tk.Checkbutton(self.root, text="Pirate elixir", variable=self.pirate_elixir_var)
        self.pirate_checkbox.grid(row=12, column=2, padx=5, pady=5)
        self.pirate_elixir_var.trace_add("write", self.toggle_pirate)


        self.entry_circle_r = tk.Label(self.root, text="No click area (pixels):")
        self.entry_circle_r.grid(row=14, column=1, columnspan=1, pady=5)
        self.text_entry_circle_r  = tk.Entry(self.root, width=15)
        self.text_entry_circle_r.grid(row=15, column=1, columnspan=1, pady=5)

        self.screenshot_button = tk.Button(self.root, text="Take Screenshot", command=self.take_screenshot)
        self.screenshot_button.grid(row=20, column=1, pady=10)

        self.set_metin_hp_bar_location = tk.Button(text="Set HP bar location", command=self.apply_hp_bar_location)
        self.set_metin_hp_bar_location.grid(row=21, column=0, pady=10)

        self.set_scan_window = tk.Button(text="Set scan window", command=self.apply_scan_window_location)
        self.set_scan_window.grid(row=21, column=1, pady=10)

        self.set_metin_stack = tk.Button(text="Set metin stack location", command=self.apply_metin_stack_location)
        self.set_metin_stack.grid(row=21, column=2, pady=10)

        self.set_bot_check = tk.Button(text="Set bot check location", command=self.apply_bot_check_location)
        self.set_bot_check.grid(row=22, column=0, pady=10)

        self.sec_scan_ore_window = tk.Button(text="Set ore check location", command=self.apply_ore_check_location)
        self.sec_scan_ore_window.grid(row=22, column=1, pady=10)

        self.apply = tk.Button(self.root, text="Apply", command=self.apply_fields)
        self.apply.grid(row=23, column=0, columnspan=4, pady=10)

        self.last_row = 24

        self.cfg = {}
        self.cfg_local = {}
        self.information_locations = {}

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

        self.init_bot()

    def init_bot(self):
        self.load_config_values()
        self.load_cfg_local()
        self.bot_manager = BotManager(self.display_screenshot, self.cfg['metin_stones'], self.cfg['fishing'],
                                      self.cfg['mining'], False)

        self.load_values()


    def load_config_values(self):
        config_path ='../Config.json'
        cfg = load_config(config_path)
        self.cfg = cfg
        self.text_tesseract_path.insert(0, cfg['tesseract_path'])

        self.dropdown_bot.set(self.bot_options[0])
        self.metin_options = [item['name'] for item in cfg['metin_stones']]
        self.dropdown_metin['values'] = self.metin_options
        self.dropdown_metin.set(self.metin_options[0])


    def load_cfg_local(self):
        config_local_path ='../Config-local.json'
        cfg_local = load_config(config_local_path)
        self.cfg_local = cfg_local
        locations = ['hp_bar_location', 'scan_window_location', 'metin_stack_location', 'bot_check_location', 'ore_check_location']

        if 'information_locations' not in self.cfg_local:
            self.cfg_local['information_locations'] = {}
        else:
            info_locs = self.cfg_local['information_locations']
            error_items = []
            for loc_item in locations:
                if loc_item not in info_locs:
                    error_items.append(loc_item)
            if error_items:
                error_msg = 'Missing parameters: ' + ', '.join(error_items)
                messagebox.showerror("Missing parameters:", error_msg)

        if 'classes' not in self.cfg_local:
            self.cfg_local['classes'] = {}
        for class_option in self.class_skills.keys():
            if class_option not in self.cfg_local['classes']:
                self.cfg_local['classes'][class_option] = {}
            for skill_option in self.class_skills[class_option]:
                if skill_option not in self.cfg_local['classes'][class_option]:
                    print(f'set null key for {skill_option}')
                    path = self.class_skills[class_option][skill_option]
                    self.cfg_local['classes'][class_option][skill_option] = {'key_bind': "",
                                                                             'skill_active_img_path': path}

        if 'window_name' not in self.cfg_local:
            self.cfg_local['window_name'] = ''

        if 'cape_time' not in self.cfg_local:
            self.cfg_local['cape_time'] = ''

        if 'cape_key' not in self.cfg_local:
            self.cfg_local['cape_key'] = ''

        if 'webhook' not in self.cfg_local:
            self.cfg_local['webhook'] = ''

        if 'user_id' not in self.cfg_local:
            self.cfg_local['user_id'] = ''

        if 'ore_time' not in self.cfg_local:
            self.cfg_local['ore_time'] = ''

        if 'turn_off' not in self.cfg_local:
            self.cfg_local['turn_off'] = '15'

        if 'metin_treshold' not in self.cfg_local:
            self.cfg_local['metin_treshold'] = '30'

        if 'tesseract_path' not in self.cfg_local:
            self.cfg_local['tesseract_path'] = ''

        if 'metin_turn_off' not in self.cfg_local:
            self.cfg_local['metin_turn_off'] = ''

        if 'circle_r' not in self.cfg_local:
            self.cfg_local['circle_r'] = '150'

        if 'bot_check_location' not in self.cfg_local['information_locations']:
            self.cfg_local['information_locations']['bot_check_location'] = [0, 0, 0, 0]

        if 'scan_window_location' not in self.cfg_local['information_locations']:
            self.cfg_local['information_locations']['scan_window_location'] = [0, 0, 0, 0]

        if 'hp_bar_location' not in self.cfg_local['information_locations']:
            self.cfg_local['information_locations']['hp_bar_location'] = [0, 0, 0, 0]

        if 'metin_stack_location' not in self.cfg_local['information_locations']:
            self.cfg_local['information_locations']['metin_stack_location'] = [0, 0, 0, 0]

        if 'ore_check_location' not in self.cfg_local['information_locations']:
            self.cfg_local['information_locations']['ore_check_location'] = [0, 0, 0, 0]

        self.text_window_name.insert(0, self.cfg_local['window_name'])
        self.text_tesseract_path.insert(0, self.cfg_local['tesseract_path'])
        self.text_metin_time_treshold.insert(0, self.cfg_local['metin_treshold'])
        self.text_turn_off_bot.insert(0, self.cfg_local['metin_turn_off'])
        self.text_entry_cape.insert(0, self.cfg_local['cape_time'])
        self.text_entry_cape_key.insert(0, self.cfg_local['cape_key'])
        self.text_entry_user_id.insert(0, self.cfg_local['user_id'])
        self.text_entry_web_hook.insert(0, self.cfg_local['webhook'])
        self.text_mining_wait_time.insert(0, self.cfg_local['ore_time'])
        self.text_entry_circle_r.insert(0, self.cfg_local['circle_r'])

    def apply_fields(self):
        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.save_fields()
        self.load_values()
        save_config(self.cfg_local, '../Config-local.json')

    def load_values(self):
        selected_class = self.dropdown_class.get()
        selected_metin = self.dropdown_metin.get()

        cape_time_min, cape_time_max = process_possible_double_values(self.cfg_local['cape_time'])
        mining_wait_time_min, mining_wait_time_max = process_possible_double_values(self.cfg_local['ore_time'])

        metin_treshold = process_text_to_digit(self.cfg_local['metin_treshold'])
        metin_turn_off = process_text_to_digit(self.cfg_local['metin_turn_off'])
        circle_r = process_text_to_digit(self.cfg_local['circle_r'])

        self.bot_manager.load_values(self.cfg_local['window_name'],
                                     self.cfg_local['information_locations']['bot_check_location'],
                                     self.cfg['tesseract_path'],
                                     self.cfg_local['information_locations']['scan_window_location'],
                                     self.cfg_local['information_locations']['hp_bar_location'],
                                     self.cfg_local['information_locations']['metin_stack_location'],
                                     self.cfg_local['classes'],
                                     selected_class,
                                     cape_time_max,
                                     cape_time_min,
                                     metin_turn_off,
                                     selected_metin,
                                     self.cfg_local['cape_key'],
                                     metin_treshold,
                                     self.cfg_local['information_locations']['ore_check_location'],
                                     mining_wait_time_min,
                                     mining_wait_time_max,
                                     self.cfg_local['webhook'],
                                     self.cfg_local['user_id'],
                                     circle_r)


    def save_fields(self):
        self.cfg['tesseract_path'] = self.text_tesseract_path.get()
        self.cfg_local['window_name'] = self.text_window_name.get()
        self.cfg_local['metin_treshold'] = self.text_metin_time_treshold.get()
        self.cfg_local['metin_turn_off'] = self.text_turn_off_bot.get()
        self.cfg_local['cape_time'] = self.text_entry_cape.get()
        self.cfg_local['cape_key'] = self.text_entry_cape_key.get()
        self.cfg_local['user_id'] = self.text_entry_user_id.get()
        self.cfg_local['circle_r'] = self.text_entry_circle_r.get()
        self.cfg_local['webhook'] = self.text_entry_web_hook.get()
        self.cfg_local['ore_time'] = self.text_mining_wait_time.get()


    def set_skills(self):
        selected_class = self.dropdown_class.get()

        self.skill_window = tk.Toplevel(self.root)
        self.skill_window.title("Set Skills")

        self.skill_labels = []
        self.keyboard_entries = []

        for skill in self.class_skills[selected_class]:
            skill_key = self.cfg_local['classes'][selected_class][skill]['key_bind']
            self.create_row(skill, skill_key)

        apply_button = tk.Button(self.skill_window, text="Apply", command=self.apply_skills)
        apply_button.grid(row=101, column=0, columnspan=2, pady=10)

    def create_row(self, skill_name="", skill_key=""):
        skill_label = tk.Label(self.skill_window, text=skill_name)
        skill_label.grid(row=len(self.skill_labels) + 1, column=0, padx=10, pady=5)

        keyboard_entry = tk.Entry(self.skill_window)
        keyboard_entry.grid(row=len(self.keyboard_entries) + 1, column=1, padx=10, pady=5)

        keyboard_entry.insert(tk.END, skill_key)
        self.skill_labels.append(skill_label)
        self.keyboard_entries.append(keyboard_entry)


    def apply_skills(self):
        selected_class = self.dropdown_class.get()
        for skill_label, keyboard_entry in zip(self.skill_labels, self.keyboard_entries):
            skill_name = skill_label.cget("text").strip()
            keyboard_button = keyboard_entry.get().strip()

            if skill_name and keyboard_button:
                self.cfg_local['classes'][selected_class][skill_name]["key_bind"] = keyboard_button

        print(f"Skills Saved: {self.cfg_local['classes']}")


    def save_selected_option_metins(self, event):
        self.bot_manager.metin_hunter.selected_metin = self.dropdown_metin.get()

    def save_selected_option_class(self, event):
        self.bot_manager.character_actions.selected_class = self.dropdown_class.get()

    def toggle_display_images(self, *args):
        if self.display_images_var.get() == 1:
            print("Image display is enabled.")
            self.bot_manager.show_img = True
        else:
            print("Image display is disabled.")
            self.bot_manager.show_img = False

    def toggle_destroy_event_stones(self, *args):
        if self.destroy_event_stones.get() == 1:
            self.bot_manager.metin_hunter.destroy_event_stones = True
        else:
            self.bot_manager.metin_hunter.destroy_event_stones = False


    def toggle_pirate(self, *args):
        if self.pirate_elixir_var.get() == 1:
            self.bot_manager.character_actions.use_pirate_elixir = True
        else:
            self.bot_manager.character_actions.use_pirate_elixir = False

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

    def apply_ore_check_location(self):
        if None not in [self.start_x, self.start_y, self.end_x, self.end_y]:
            output = [min(self.start_x, self.end_x), min(self.end_y, self.start_y), max(self.start_x, self.end_x),
                      max(self.end_y, self.start_y)]

            self.cfg_local['information_locations']['ore_check_location'] = output

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

    def start_bot_thread(self):
        selected_bot = self.dropdown_bot.get()
        if 'Metin bot' == selected_bot:
            self.start_bot_loop_thread()
        elif 'Fish bot' == selected_bot:
            self.start_fishbot_thread()
        elif 'Mining bot' == selected_bot:
            self.start_miner_bot_thread()
        else:
            messagebox.showerror("Bot selection ERROR:", 'There was error while selecting bot')

    def start_bot_loop_thread(self):
        if not self.bot_manager.running:
            self.bot_manager.running = True
            threading.Thread(target=self.bot_manager.run_metin_hunter, daemon=True).start()

    def start_fishbot_thread(self):
        if not self.bot_manager.running:
            self.bot_manager.running = True
            threading.Thread(target=self.bot_manager.run_fish_bot, daemon=True).start()

    def start_miner_bot_thread(self):
        if not self.bot_manager.running:
            self.bot_manager.running = True
            threading.Thread(target=self.bot_manager.run_miner_bot, daemon=True).start()

    def take_screenshot(self):
        metin_window = gw.getWindowsWithTitle(self.bot_manager.game_window.window_name)[0]
        screenshot = get_window_screenshot(metin_window)
        self.screenshot_image = screenshot
        self.screenshot_image_left = metin_window.left
        self.screenshot_image_top = metin_window.top

        new_window = tk.Toplevel(self.root)
        new_window.title("Screenshot")
        new_window.geometry(f"{screenshot.width}x{screenshot.height}")

        screenshot_tk = ImageTk.PhotoImage(screenshot)

        canvas = Canvas(new_window, width=screenshot.width, height=screenshot.height)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_tk)

        canvas.image = screenshot_tk

        canvas.bind("<ButtonPress-1>", lambda event: self.on_button_press(event, canvas))
        canvas.bind("<B1-Motion>", lambda event: self.on_mouse_drag(event, canvas))
        canvas.bind("<ButtonRelease-1>", lambda event: self.on_button_release(event))
        canvas.bind("<Button-3>", lambda event: self.on_right_click(canvas))

        self.canvas = canvas
        self.rect = None
        self.start_x = None
        self.start_y = None

    def display_screenshot(self):
        screenshot = self.bot_manager.image_to_display

        def update_image(screenshot=screenshot):
            if not isinstance(screenshot, Image.Image):
                screenshot = screenshot[:, :, ::-1]
                screenshot = Image.fromarray(screenshot)

            img = screenshot.resize((self.root.winfo_width(), int(self.root.winfo_height() / 2)))

            self.screenshot_img = ImageTk.PhotoImage(img)

            if self.image_label:
                self.image_label.config(image=self.screenshot_img)
            else:
                self.image_label = tk.Label(self.root, image=self.screenshot_img)
                self.image_label.grid(row=self.last_row, column=0, columnspan=4, pady=10)

        self.root.after(0, update_image)

    def on_button_press(self, event, canvas):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            canvas.delete(self.rect)
        self.rect = canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='green')

    def on_mouse_drag(self, event, canvas):
        cur_x, cur_y = (event.x, event.y)
        if self.rect:
            canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        self.end_x, self.end_y = (event.x, event.y)
        print(f"Rectangle coordinates: {self.start_x}, {self.start_y} -> {self.end_x}, {self.end_y}")

        self.selected_area = (self.start_x, self.start_y, self.end_x, self.end_y)

    def on_right_click(self, canvas):
        if self.rect:
            canvas.delete(self.rect)
            self.rect = None
            print("Rectangle deleted")

    def stop_bot_loop(self):
        self.bot_manager.running = False
        self.bot_manager.metin_hunter.not_destroying_metin = 0
        self.bot_manager.metin_hunter.destroying_metins = False

    def run(self):
        self.root.mainloop()