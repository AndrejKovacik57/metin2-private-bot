import threading
import time
from Modules.GameWindow import GameWindow
from Modules.CharacterActions import CharacterActions
from Modules.AntiBot import AntiBot
from Modules.Respawn import Respawn
from Modules.MetinHunter import MetinHunter
from Modules.FishBot import FishBot
from Modules.MiningBot import MiningBot
from Modules.MessageCheck import MessageCheck
import random
import json
import os


class BotManager:

    def __init__(self, display_screenshot, metin_config:dict, fishing_config:dict, mining_config:dict, show_img=False):

        self.running = False
        self.lock = threading.Lock()
        self.upper_sleep_limit = 0.5
        self.lower_sleep_limit = 0.1

        self.text_hash_map = {}
        self.metin_config = metin_config
        self.__initialize()

        self.game_window = GameWindow()
        self.character_actions = CharacterActions(self.game_window)
        self.anti_bot = AntiBot(self.text_hash_map, self.game_window)
        self.respawn = Respawn(self.game_window)
        self.metin_hunter = MetinHunter(self.game_window,self.text_hash_map, self.__stop_running)
        self.fish_bot = FishBot(self.game_window, fishing_config)
        self.mining_bot = MiningBot(mining_config, self.game_window)
        self.message_check = MessageCheck(self.game_window)


        self.show_img = show_img
        self.display_screenshot = display_screenshot
        self.image_to_display = None

    def load_values(self,
                    window_name:str,
                    bot_check_location:tuple[int, int, int, int],
                    tesseract_path:str,
                    scan_window_location:tuple[int, int, int, int],
                    hp_bar_location:tuple[int, int, int, int],
                    metin_stack_location:tuple[int, int, int, int],
                    skills_cfg,
                    selected_class,
                    cape_time_min:int,
                    cape_time_max:int,
                    not_destroying_metin_treshold:int,
                    selected_metin:str,
                    cape_key:str,
                    metin_treshold:int,
                    ore_check_location:tuple[int, int, int, int],
                    mining_wait_time_min:int,
                    mining_wait_time_max:int,
                    webhook:str,
                    user_id:str,
                    circle_r):

        self.game_window.window_name = window_name
        self.character_actions.load_values(skills_cfg, selected_class, cape_time_min, cape_time_max, cape_key)
        self.anti_bot.load_values(tesseract_path, bot_check_location)
        self.metin_hunter.load_values(scan_window_location, hp_bar_location, metin_stack_location, not_destroying_metin_treshold,
                                      selected_metin, metin_treshold, cape_key, circle_r)
        self.mining_bot.load_values(ore_check_location, mining_wait_time_min, mining_wait_time_max)
        self.respawn.reset_not_destroying_metin_callback = self.metin_hunter.reset_not_destroying_metin_callback
        self.message_check.load_values(webhook, user_id)



    def __initialize(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        hash_json_path = os.path.join(script_dir, "../hash_combinations.json")

        if not os.path.exists(hash_json_path):
            return {}

        with open(hash_json_path, "r") as json_file:
            self.text_hash_map = json.load(json_file)

    def __stop_running(self):
        self.running = False
        for i in range(5):
            if self.game_window.terminate_process():
                break
        local_time = time.localtime(time.time())
        payload = self.message_check.get_payload(f"Metin okno zatvorene - {time.strftime('%Y-%m-%d %H:%M:%S', local_time)}")
        self.message_check.send_message_new_thread(payload)

    def run_metin_hunter(self):
        time.sleep(2)
        print('idem vybrat pocasie')
        weather = self.metin_hunter.initialize_contour_parameters(self.metin_config)
        self.character_actions.choose_weather(weather)

        while self.running:
            with self.lock:
                loop_time = time.time()
                sleep_time = random.random() * (self.upper_sleep_limit - self.lower_sleep_limit) + self.lower_sleep_limit
                time.sleep(sleep_time)
                np_image = self.game_window.get_np_image()
                if self.running:
                    self.anti_bot.bot_solver(np_image)
                if self.running:
                    self.respawn.death_check(np_image)
                if self.running:
                    self.character_actions.activate_skills()
                if self.running:
                    self.character_actions.activate_buffs()
                if self.running:
                    self.character_actions.use_cape()
                if self.running:
                    self.character_actions.check_pirate_elixir()
                if self.running:
                    self.character_actions.cancel_leader_board(np_image)
                if self.running:
                    self.message_check.locate_messages(np_image)
                if self.running:
                    is_clan_meet = self.character_actions.check_clan_meet(np_image)
                    if is_clan_meet:
                        payload = self.message_check.get_payload(
                            f"Je cehové stretnutie!!!")
                        self.message_check.send_message_new_thread(payload)
                # must be last alters np_image
                if self.running:
                    self.image_to_display = self.metin_hunter.hunt_metin(np_image)
                    if self.show_img:
                        self.display_screenshot()

                print(f'Iteration execution time {time.time() - loop_time}s')

    def run_fish_bot(self):
        time.sleep(2)
        upper_limit = 0.5
        lower_limit = 0.1
        while self.running:
            with self.lock:
                loop_time = time.time()
                sleep_time = random.random() * (upper_limit - lower_limit) + lower_limit
                time.sleep(sleep_time)
                np_image = self.game_window.get_np_image()
                if self.running:
                    self.anti_bot.bot_solver(np_image)
                if self.running:
                    self.fish_bot.catch_fish()
                print(f'Iteration execution time {time.time() - loop_time}s')

    def run_miner_bot(self):
        time.sleep(2)
        self.character_actions.choose_weather(self.mining_bot.weather)

        upper_limit = 0.5
        lower_limit = 0.1
        while self.running:
            with self.lock:
                sleep_time = random.random() * (upper_limit - lower_limit) + lower_limit
                time.sleep(sleep_time)
                np_image = self.game_window.get_np_image()
                if self.running:
                    self.anti_bot.bot_solver(np_image)
                if self.running:
                    self.image_to_display = self.mining_bot.mine_ore(np_image)
                    if self.show_img:
                        self.display_screenshot()
