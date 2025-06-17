import random
import time
import numpy as np

from Modules import GameWindow
from Utils.Utils import load_image, press_button, locate_image, press_button_multiple, click_location_middle, \
    mouse_left_click, cancel_all, right_click_location_middle


class CharacterActions:
    def __init__(self, game_window:GameWindow):
        self.cape_time_min = 0
        self.cape_time_max = 0
        self.randomized_cape_time = 0.0
        self.cape_timer = 10
        self.cape_key = ''

        self.buff_timer = 0
        self.buff_timer_diff = 0
        self.buff_cd = 30 * 60

        self.skills_cfg = None
        self.skill_timer_diff = 0
        self.skill_timer = 0
        self.skills_cd = 30

        self.board_timer = 0
        self.board_cd = 30

        self.clan_meet_timer = 0
        self.clan_meet_cd = 10

        self.selected_class = None

        self.game_window = game_window

        self.use_pirate_elixir = False
        self.elixir_timer = 0
        self.elixir_cd = 10


        self.use_faraon_elixir = False
        
        self.use_snake_elixir = False

        self.spin_timer = 0
        self.spin_cd = 10

        self.selected_weather = 999
        self.settings_options = load_image('../bot_images/settings_options.png')
        self.sky_settings = load_image('../bot_images/sky_settings.png')
        self.game_settings = load_image('../bot_images/game_settings.png')
        self.weather_image = load_image('../bot_images/weather.png')
        self.cancel_img = load_image('../bot_images/cancel_metin_button.png')
        self.leaderboard_img = load_image('../bot_images/leaderboard.png')
        self.clan_meeting = load_image('../bot_images/schudze.png')
        self.inventory = load_image('../bot_images/inventar.png')
        self.inventory_slots = load_image('../bot_images/stranky_inventar.png')
        self.pirate_buff = load_image('../bot_images/elik_pirat_buff.png')
        self.snake_buff = load_image('../bot_images/elik_had_buff.png')
        self.faraon_buff = load_image('../bot_images/elik_faraon_buff.png')
        self.pirate_item = load_image('../bot_images/elik_pirat_item.png')
        self.snake_item = load_image('../bot_images/elik_had_item.png')
        self.faraon_item = load_image('../bot_images/elik_faraon_item.png')
        self.spin = load_image('../bot_images/spin.png')

    def load_values(self, skills_cfg:dict, selected_class:str, cape_time_min:int, cape_time_max:int, cape_key:str):
        self.skills_cfg = skills_cfg
        self.selected_class = selected_class
        self.cape_time_min = cape_time_min
        self.cape_time_max = cape_time_max
        self.cape_key = cape_key


    def use_cape(self):
        cape_timer_diff = time.time() - self.cape_timer
        if self.cape_time_min != 0 and self.cape_time_max != 0:
            if not self.randomized_cape_time:
                self.randomized_cape_time = random.random() * (self.cape_time_min - self.cape_time_max) + self.cape_time_max

            if self.cape_timer != 0 and cape_timer_diff >= self.randomized_cape_time:
                self.cape_timer = time.time()
                self.randomized_cape_time = random.random() * (self.cape_time_min - self.cape_time_max) + self.cape_time_max

                print('Plastujem')
                press_button(self.cape_key, self.game_window.window_name)
                time.sleep(0.5)

        if self.cape_time_min != 0:
            if self.cape_timer == 0 or self.cape_timer != 0 and cape_timer_diff >= self.cape_time_min:
                self.cape_timer = time.time()

                print('Plastujem')
                press_button(self.cape_key, self.game_window.window_name)
                time.sleep(0.5)


    def activate_skills(self):
        horse_flag = False
        self.skill_timer_diff = time.time() - self.skill_timer
        if self.skill_timer == 0 or self.skill_timer_diff >= self.skills_cd:
            np_img = self.game_window.get_np_image()
            class_skills = self.skills_cfg[self.selected_class]

            for skill in class_skills.keys():
                path = class_skills[skill]['skill_active_img_path']
                skill_key_bind = class_skills[skill]['key_bind'].strip()
                if skill_key_bind == '':
                    continue

                location = locate_image(path, np_img)
                if location is None:
                    print(f'Zapinam {skill}')
                    if not horse_flag:
                        horse_flag = True
                        self.skill_timer = time.time()
                        print('zosadam z kona')
                        press_button_multiple('ctrl+g', self.game_window.window_name)
                        time.sleep(0.15)

                    press_button(skill_key_bind, self.game_window.window_name)
                    time.sleep(2)
                else:
                    print('skill je aktivny')
            if horse_flag:
                press_button_multiple('ctrl+g', self.game_window.window_name)
                print('nasadam na kona')

    def activate_buffs(self):
        self.buff_timer_diff = time.time() - self.buff_timer
        print(f'self.buff_timer_diff {self.buff_timer_diff}')
        if self.buff_timer == 0 or self.buff_timer_diff >= self.buff_cd:
            print('activate_skills')
            self.buff_cd = 60 + random.randint(1, 30)
            self.buff_timer = time.time()
            press_button('F9', self.game_window.window_name)
            time.sleep(0.15)

    def cancel_leader_board(self, np_image:np.ndarray):
        board_timer_diff = time.time() - self.board_timer
        if self.board_timer == 0 or board_timer_diff >= self.board_cd:
            self.board_timer = time.time()
            location = locate_image(self.leaderboard_img, np_image, 0.9)
            if location is None:
                return
            print('Zatvaram leaderboard')
            click_location_middle(location, self.game_window)

    def check_clan_meet(self, np_image:np.ndarray):
        clan_timer_diff = time.time() - self.clan_meet_timer

        print("clan_timer_diff ", clan_timer_diff)
        if self.clan_meet_timer == 0 or clan_timer_diff >= self.clan_meet_cd:
            print("kontrolujeeem cech")
            self.clan_meet_timer = time.time()
            location = locate_image(self.clan_meeting, np_image, 0.8)

            if location is not None:
                return True
        return False

    def check_spin(self):
        spin_timer_diff = time.time() - self.spin_timer

        if self.spin_timer == 0 or spin_timer_diff >= self.spin_cd:
            self.clan_meet_timer = time.time()

            np_image = self.game_window.get_np_image()
            location = locate_image(self.spin, np_image, 0.8)
            if location is None:
                return
            print('klikam spin')
            click_location_middle(location, self.game_window)

    def check_pirate_elixir(self):
        if not self.use_pirate_elixir and not self.use_pirate_elixir and not self.use_faraon_elixir :
            return

        elixir_timer_diff = time.time() - self.elixir_timer
        if self.elixir_timer == 0 or elixir_timer_diff >= self.elixir_cd:
            self.elixir_timer = time.time()
            np_image = self.game_window.get_np_image()
            if self.use_faraon_elixir:
                item_to_locate = self.faraon_item
                buff_to_locate = self.faraon_buff
            elif self.use_pirate_elixir:
                item_to_locate = self.pirate_item
                buff_to_locate = self.pirate_buff
            else:
                item_to_locate = self.snake_item
                buff_to_locate = self.snake_buff

            location = locate_image(buff_to_locate, np_image, 0.9)

            if location is not None:
                print("elik je aktivovany")
                return

            np_image = self.game_window.get_np_image()
            location = locate_image(self.inventory, np_image, 0.9)

            if location is None:
                return

            click_location_middle(location, self.game_window)
            time.sleep(0.5)

            np_image = self.game_window.get_np_image()
            location = locate_image(self.inventory_slots, np_image, 0.9)

            if location is None:
                return
            left, slot_top, width, height = location
            slot_middle_y = slot_top + height // 2
            for slot_index in range(0,4):
                print(slot_index)
                slot_left =  left + slot_index * 30
                slot_middle_x = slot_left + 15
                mouse_left_click(slot_middle_x, slot_middle_y, self.game_window.window_name)
                time.sleep(0.5)

                np_image = self.game_window.get_np_image()
                location = locate_image(item_to_locate, np_image, 0.9)

                if location is None:
                    continue
                right_click_location_middle(location, self.game_window)
                break


    def choose_weather(self, weather):
        print(f'weather num {weather}')
        if self.selected_weather == weather:
            print('weather none0')
            return
        np_image = self.game_window.get_np_image()

        for item in [self.settings_options, self.game_settings, self.sky_settings]:
            print('skusam')
            location = locate_image(item, np_image, 0.9)
            if location is None:
                print('weather none1')
                return
            click_location_middle(location, self.game_window)
            time.sleep(0.5)
            np_image = self.game_window.get_np_image()

        np_image = self.game_window.get_np_image()
        # weather
        location = locate_image(self.weather_image, np_image, 0.9)
        if location is None:
            print('weather none2')
            return

        space = 10
        width = 81
        height = 49
        counter = 0
        for row in range(6):
            for column in range(3):
                if counter == weather - 1:
                    y1 = location.top + height * row
                    y2 = y1 + height
                    x1 = location.left + width * column + space * column
                    x2 = x1 + width

                    move_x = self.game_window.window_left + x1 + (x2 - x1) / 2
                    move_y = self.game_window.window_top + y1 + (y2 - y1) / 2

                    mouse_left_click(move_x, move_y, self.game_window.window_name)
                    self.selected_weather = counter + 1

                counter += 1

        time.sleep(0.5)
        cancel_all(np_image, self.cancel_img, self.game_window)