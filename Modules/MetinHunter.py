import random
import time
import hashlib
import numpy as np
from Modules import GameWindow
from Utils.Utils import load_image, crop_image, preprocess_image, press_button, cancel_all, mouse_left_click, \
    is_subimage, create_low_upp, locate_image
import cv2
import keyboard


class bonus_stone_class:
    def __init__(self, name:str, lower_bonus, upper_bonus, contour_low:int, contour_high:int, aspect_low:int, aspect_high:int, circularity:int):
        self.name = name
        self.lower = lower_bonus, 
        self.upper = upper_bonus
        self.contour_low = contour_low
        self.contour_high = contour_high
        self.aspect_low = aspect_low
        self.aspect_high = aspect_high
        self.circularity = circularity
    
class MetinHunter:
    def __init__(self, game_window:GameWindow, text_hash_map, stop_running):

        self.game_window = game_window

        self.scan_window_location = None
        self.hp_bar_location = None
        self.metin_stack_location = None
        self.text_hash_map = text_hash_map
        self.stop_running = stop_running

        self.not_destroying_metin = 0
        self.not_destroying_metin_diff = 0
        self.not_destroying_metin_treshold = 15

        self.clicked_at_mob_timer = 0
        self.clicked_at_mob_diff = 0
        self.clicked_at_mob_duration = 3

        self.metin_stuck_time = 18
        self.metin_stuck_timer = 0
        self.metin_stuck_timer_diff = 0

        self.event_timer = 0
        self.event_timer_diff = 0
        self.event_search_timer = 2

        self.last_num_in_stack = 0
        self.circle_r = 150

        self.destroying_metins = False
        self.premium = False
        self.destroy_event_stones = False
        self.selected_metin = None
        self.is_event_stone_selected = False

        self.lower = None
        self.upper = None
        self.contour_low = 0
        self.contour_high = 0
        self.aspect_low = 0
        self.aspect_high = 0
        self.circularity = 0

        self.lower_event = None
        self.upper_event = None
        self.contour_low_event = 0
        self.contour_high_event = 0
        self.aspect_low_event = 0
        self.aspect_high_event = 0
        self.circularity_event = 0

        self.bosses = []
        self.cape_key = ''
        self.boss_check_timer = 5
        self.boss_check_time = 0
        self.killing_boss = False

        self.tree_not_found_counter = 0
        self.tree_check_time = 0
        self.tree_check_timer = 5

        self.bonus_stones = []
        self.bonus_stone_timer = 0
        self.bonus_stone_timer_diff = 0
        self.bonus_stone_search_timer = 2

        self.metin_hp_img = load_image('../bot_images/metin_hp2.png')
        self.cancel_img = load_image('../bot_images/cancel_metin_button.png')
        self.tree_img = load_image('../bot_images/tree.png')


    def load_values(self, scan_window_location, hp_bar_location, metin_stack_location, not_destroying_metin_treshold,
                    selected_metin, metin_treshold, cape_key, circle_r=150):
        self.scan_window_location = scan_window_location
        self.hp_bar_location = hp_bar_location
        self.metin_stack_location = metin_stack_location
        self.not_destroying_metin_treshold = not_destroying_metin_treshold
        self.selected_metin = selected_metin
        self.metin_stuck_time = metin_treshold
        self.cape_key = cape_key
        self.circle_r = circle_r

    def initialize_contour_parameters(self, metin_stones):
        for metin_config in metin_stones:
            if metin_config['name'] == self.selected_metin:
                self.contour_low = metin_config['contourLow']
                self.contour_high = metin_config['contourHigh']
                self.aspect_low = metin_config['aspect_low'] / 100.0
                self.aspect_high = metin_config['aspect_high'] / 100.0
                self.circularity = metin_config['circularity'] / 1000.0
                if 'event_stones' in metin_config:
                    self.is_event_stone_selected = self.is_event_stone_selected = True
                    event_config = metin_config['event_stones'][0]
                    self.contour_low_event = event_config['contourLow']
                    self.contour_high_event = event_config['contourHigh']
                    self.aspect_low_event = event_config['aspect_low'] / 100.0
                    self.aspect_high_event = event_config['aspect_high'] / 100.0
                    self.circularity_event = event_config['circularity'] / 1000.0
                    self.lower_event, self.upper_event = create_low_upp(event_config)
                else:
                    self.is_event_stone_selected = False

                if 'bonus_stones' in metin_config:
                    bonus_stones = metin_config['bonus_stones']
                    self.bonus_stones = []
                    for bonus_stone_item in bonus_stones:
                        lower_bonus, upper_bonus = create_low_upp(bonus_stone_item)
                        bonus_stone = bonus_stone_class(bonus_stone_item['name'],
                                                        lower_bonus, 
                                                        upper_bonus,
                                                        bonus_stone_item['contourLow'],
                                                        bonus_stone_item['contourHigh'],
                                                        bonus_stone_item['aspect_low'],
                                                        bonus_stone_item['aspect_high'],
                                                        bonus_stone_item['circularity'])
                        self.bonus_stones.append(bonus_stone)
                else:
                    self.bonus_stones = []

                self.lower, self.upper = create_low_upp(metin_config)

                self.bosses = metin_config['bosses']

                return metin_config['weather']

    def reset_not_destroying_metin_callback(self):
        self.not_destroying_metin = 0

    def hunt_metin(self, np_image:np.ndarray):
        np_image_crop = crop_image(np_image, self.scan_window_location)
        height, width  = np_image.shape[:2]
        scan_x1, scan_y1, _, _ = self.scan_window_location
        x_middle = self.game_window.window_left + (width // 2) - scan_x1
        y_middle = self.game_window.window_top + (height // 2) - scan_y1
        print('step1')
        tree_active = self.__locate_tree(np_image)
        if not tree_active: return np_image_crop
        print('step2')

        stop_bot = self.__handle_metin_destruction_timer()
        if stop_bot: return np_image_crop
        print('step3')

        # boss_exists = self.__handle_boss_check_timer(np_image)
        # if boss_exists: return np_image_crop

        hp_bar = crop_image(np_image, self.hp_bar_location)
        metin_is_alive = self.__locate_metin_hp(hp_bar)   # check if metin was destroyed
        self.__update_metin_status(metin_is_alive)

        metin_num, metins_in_stack = self.__process_metin_stack(np_image, metin_is_alive)
        print(f'metin_num {metin_num} metins_in_stack{metins_in_stack}')
        print('step4')
        self.__check_metin_destruction_stuck(metins_in_stack)

        if self.bonus_stones:
            self.__handle_bonus_stones(np_image_crop, metin_num, x_middle, y_middle)


        if self.is_event_stone_selected:
            image_to_display_event = self.__handle_event_stones(np_image_crop, metin_num, x_middle, y_middle)
            if image_to_display_event is not None: return image_to_display_event

        print(f'METIN NUM: {metin_num}')
        image_to_display = self.__handle_metin_stones(np_image_crop, hp_bar, metin_num, x_middle, y_middle)
        if image_to_display is not None: return image_to_display

    def __locate_tree(self, np_image):
        tree_check_time_diff = time.time() - self.tree_check_time
        if self.tree_check_time == 0 or tree_check_time_diff >= self.tree_check_timer:
            self.tree_check_time = time.time()
            location = locate_image(self.tree_img, np_image)
            if location is None:
                if self.tree_not_found_counter == 5:
                    print('Strom vypnuty')
                    self.stop_running()
                    return False
                self.tree_not_found_counter += 1
        self.tree_not_found_counter = 0
        print('Strom zapnuty')
        return True

    def __handle_boss_check_timer(self, np_image:np.ndarray) -> bool:
        boss_check_time_diff = time.time() - self.boss_check_time
        if self.killing_boss or self.boss_check_time == 0 or boss_check_time_diff >= self.boss_check_timer:
            self.boss_check_time = time.time()
            boss_exists = self.__boss_check(np_image)
            if boss_exists:
                self.not_destroying_metin = 0
                self.metin_stuck_timer = 0
                self.__attack_boss()
                self.killing_boss = True
                print('NASIEL SA BOSS')
                print('NASIEL SA BOSS')
                print('NASIEL SA BOSS')
                print('NASIEL SA BOSS')
                return True

        return False

    def __handle_metin_destruction_timer(self) -> bool:
        self.not_destroying_metin_diff = time.time() - self.not_destroying_metin if self.not_destroying_metin else 0
        print(f'self.not_destroying_metin_diff {self.not_destroying_metin_diff} self.not_destroying_metin_treshold {self.not_destroying_metin_treshold}')
        if self.not_destroying_metin_diff > self.not_destroying_metin_treshold:
            self.stop_running()
            self.destroying_metins = False
            self.not_destroying_metin = 0
            formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            print(f'{formatted_time}')
            return True

        return False

    def __boss_check(self, np_image:np.ndarray) -> bool:
        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)

        for boss in self.bosses:
            lower, upper = create_low_upp(boss)
            contour_low = boss['contourLow']
            contour_high = boss['contourHigh']
            aspect_low = boss['aspect_low'] / 100.0
            aspect_high = boss['aspect_high'] / 100.0
            circularity = boss['circularity'] / 1000.0

            mask = cv2.inRange(hsv, lower, upper)
            # np_image = cv2.bitwise_and(np_image, np_image, mask=mask)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                for contour in contours:
                    if contour_high > cv2.contourArea(contour) > contour_low:
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = float(w) / h
                        area = cv2.contourArea(contour)
                        perimeter = cv2.arcLength(contour, True)
                        item_circularity = 4 * np.pi * (area / (perimeter * perimeter))

                        if aspect_low < aspect_ratio < aspect_high and item_circularity > circularity:
                            # found boss
                            return True
        self.killing_boss = False
        return False

    def __attack_boss(self):
        if not self.killing_boss:
            press_button(self.cape_key, self.game_window.window_name)
            time.sleep(0.15)

        keyboard.press('space')
        time.sleep(5)
        keyboard.release('space')

    def __update_metin_status(self, metin_is_alive:bool) -> None:
        if not metin_is_alive and not self.not_destroying_metin and self.destroying_metins:
            self.not_destroying_metin = time.time()
            self.metin_stuck_timer = 0
            print('RESET self.metin_stuck_time 2')
            print('RESET self.metin_stuck_time 2')
            print('RESET self.metin_stuck_time 2')
        print(f'nici sa metin {metin_is_alive}')
        if metin_is_alive:
            self.not_destroying_metin_diff = 0
            self.not_destroying_metin = 0

    def __process_metin_stack(self, np_image:np.ndarray, metin_is_alive:bool) -> (int, int):
        metin_stack_img = crop_image(np_image, self.metin_stack_location)
        metin_stack_img_processed = preprocess_image(metin_stack_img)
        metin_stack_hash = hashlib.md5(metin_stack_img_processed).hexdigest()

        if metin_stack_hash in self.text_hash_map:
            return self.__extract_metin_info(metin_stack_hash)
        else:
            return self.__handle_unmatched_metin(metin_is_alive)

    def __extract_metin_info(self, metin_stack_hash:str) -> (int, int):
        self.clicked_at_mob_timer = 0
        self.clicked_at_mob_diff = 0
        metin_stack_string = self.text_hash_map[metin_stack_hash]
        stack = int(metin_stack_string[3])
        stack = 3 #temp stack limiter
        metins_in_stack = int(metin_stack_string[1])
        metin_num = stack - metins_in_stack
        print('nasiel sa metin hash')
        return metin_num, metins_in_stack

    def __handle_unmatched_metin(self, metin_is_alive:bool) -> (int, int):
        if metin_is_alive:
            self.__update_clicked_mob_timer()
        print('nenasiel sa metin hash')
        return 1, 0

    def __update_clicked_mob_timer(self) -> None:
        if self.clicked_at_mob_timer == 0:
            self.clicked_at_mob_timer = time.time()
        else:
            self.clicked_at_mob_diff = time.time() - self.clicked_at_mob_timer

        if self.clicked_at_mob_diff >= self.clicked_at_mob_duration:
            self.__reset_mob_interaction()

    def __reset_mob_interaction(self):
        print('nenasla sa fronta pri hp bare, rusim frontu')
        keyboard.press('space')
        time.sleep(0.15)
        press_button('w', self.game_window.window_name)
        keyboard.release('space')
        time.sleep(0.15)
        np_image = self.game_window.get_np_image()
        cancel_all(np_image, self.cancel_img, self.game_window)

    def __check_metin_destruction_stuck(self, metins_in_stack: int) -> None:
        if metins_in_stack == self.last_num_in_stack:
            if self.metin_stuck_timer == 0:
                self.metin_stuck_timer = time.time()
            else:
                self.metin_stuck_timer_diff = time.time() - self.metin_stuck_timer
                if self.metin_stuck_timer_diff >= self.metin_stuck_time:
                    print('SEKAS DLHO METIN')
                    print('SEKAS DLHO METIN')
                    print('SEKAS DLHO METIN')
                    print('SEKAS DLHO METIN')
                    print('SEKAS DLHO METIN')
                    print('SEKAS DLHO METIN')
                    print(f'metins_in_stack {metins_in_stack} self.last_num_in_stack {self.last_num_in_stack}')
                    print(f'metin_stuck_timer_diff {self.metin_stuck_timer_diff} metin_stuck_time {self.metin_stuck_time}')
                    time.sleep(10)
                    self.__reset_mob_interaction()
        else:
            print('RESET self.metin_stuck_time')
            print('RESET self.metin_stuck_time')
            print('RESET self.metin_stuck_time')
            print(f'metins_in_stack {metins_in_stack} self.last_num_in_stack {self.last_num_in_stack}')
            self.metin_stuck_timer = 0
        self.last_num_in_stack = metins_in_stack

    def __cancel_stack(self):
        keyboard.press('space')
        time.sleep(0.15)
        press_button('w', self.game_window.window_name)
        keyboard.release('space')
        time.sleep(0.15)


    def __handle_bonus_stones(self, np_image_crop: np.ndarray, metin_num: int, x_middle: int,
                              y_middle: int) -> np.ndarray | None:
        
        self.bonus_stone_timer_diff = time.time() - self.bonus_stone_timer
        if self.bonus_stone_timer == 0 or self.bonus_stone_timer != 0 and self.bonus_stone_timer_diff >= self.bonus_stone_search_timer:
           
            self.bonus_stone_timer = time.time()
            for bonus_stone in self.bonus_stones:
                print(f'hladam bonus kamen!! {bonus_stone.name}')
                metin_positions_bonus, _ = self.__locate_metin(np_image_crop, metin_num, x_middle, y_middle,
                                                                                    bonus_stone.lower, 
                                                                                    bonus_stone.upper,
                                                                                    bonus_stone.contour_high,
                                                                                    bonus_stone.contour_low,
                                                                                    bonus_stone.aspect_low,
                                                                                    bonus_stone.aspect_high,
                                                                                    bonus_stone.circularity)
                if metin_positions_bonus is not None:
                    self.event_search_timer = 10
                    print(f'nasiel sa bonus kamen!  {bonus_stone.name}')
                    # self.__cancel_stack()
                    self.__click_on_metins(metin_positions_bonus, None, event=True)
                    press_button('q', self.game_window.window_name)

                else:
                    self.event_search_timer = 2
                    press_button('q', self.game_window.window_name)

    def __handle_event_stones(self, np_image_crop: np.ndarray, metin_num: int, x_middle: int,
                              y_middle: int) -> np.ndarray | None:
        if self.destroy_event_stones:
            self.event_timer_diff = time.time() - self.event_timer
            if self.event_timer == 0 or self.event_timer != 0 and self.event_timer_diff >= self.event_search_timer:
                print(f'hladam event kamen!!')
                self.event_timer = time.time()
                metin_positions_event, image_to_display_event = self.__locate_metin(np_image_crop, metin_num, x_middle,
                                                                                    y_middle,
                                                                                    self.lower_event, self.upper_event,
                                                                                    self.contour_high_event,
                                                                                    self.contour_low_event,
                                                                                    self.aspect_low_event,
                                                                                    self.aspect_high_event,
                                                                                    self.circularity_event)
                if metin_positions_event is not None:
                    self.event_search_timer = 10
                    print(f'nasiel sa event kamen!')
                    self.__cancel_stack()
                    self.__click_on_metins(metin_positions_event, None, event=True)
                    press_button('q', self.game_window.window_name)
                    return image_to_display_event

                else:
                    self.event_search_timer = 2
                    press_button('q', self.game_window.window_name)
                    return np_image_crop

    def __click_on_metins(self, metin_positions, hp_bar: np.ndarray | None, event=False):
        for metin_position in metin_positions:
            metin_pos_x, metin_pos_y = metin_position

            np_image_mob_check = crop_image(self.game_window.get_np_image(), self.scan_window_location)
            pixel_to_check = np_image_mob_check[metin_pos_y, metin_pos_x]

            if np.all(np.all(np.abs(pixel_to_check - [0, 0, 0]) <= 5)):
                print("The pixel is black.")
            else:
                event_message = 'event ' if event else ''
                print(f'Click at {event_message}metin')
                scan_x1, scan_y1, _, _ = self.scan_window_location
                metin_pos_x += self.game_window.window_left + scan_x1
                metin_pos_y += self.game_window.window_top + scan_y1

                self.__collect_loot()
                sleep_time = 0
                if event:
                    mouse_left_click(metin_pos_x, metin_pos_y, self.game_window.window_name)
                    self.destroying_metins = True
                    sleep_time = random.random() * (1.5 - 2.1) + 2.1

                else:
                    metin_is_alive = self.__locate_metin_hp(hp_bar)
                    print(f'metin_is_alive {metin_is_alive} not_destroying_metin_diff {self.not_destroying_metin_diff}')
                    if not metin_is_alive and self.not_destroying_metin_diff > 3:
                        mouse_left_click(metin_pos_x, metin_pos_y, self.game_window.window_name)
                        self.destroying_metins = True
                    elif not metin_is_alive and self.not_destroying_metin_diff == 0:
                        self.not_destroying_metin = time.time()
                    elif metin_is_alive:
                        mouse_left_click(metin_pos_x, metin_pos_y, self.game_window.window_name)
                        self.destroying_metins = True
                        sleep_time = random.random() * (0.3 - 0.15) + 0.15

                time.sleep(sleep_time)

    def __collect_loot(self):
        if not self.premium:
            press_button('z', self.game_window.window_name)
            time.sleep(0.15)
            press_button('y', self.game_window.window_name)

    def __handle_metin_stones(self, np_image_crop: np.ndarray, hp_bar:np.ndarray, metin_num: int, x_middle: int, y_middle: int) -> np.ndarray | None:
        metin_positions, image_to_display = self.__locate_metin(np_image_crop, metin_num, x_middle, y_middle, self.lower,
                                                                self.upper, self.contour_high, self.contour_low,
                                                                self.aspect_low, self.aspect_high, self.circularity)

        if metin_positions is not None and metin_num > 0:
            print('Metin Found')
            print(f'metin_positions: {len(metin_positions)}')

            self.__click_on_metins(metin_positions, hp_bar)
            press_button('q', self.game_window.window_name)
            return image_to_display

        else:
            press_button('q', self.game_window.window_name)
            return np_image_crop

    def __locate_metin(self, np_image, metin_num, x_middle, y_middle, lower, upper, contour_high,
                       contour_low, aspect_low, aspect_high, circularity, use_circle_r=True):
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

                        cv2.rectangle(np_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                        contour_center_x = x + w // 2
                        contour_center_y = y + h // 2

                        cv2.line(np_image, (x_middle, y_middle), (contour_center_x, contour_center_y),
                                 (255, 190, 200), 2)
                        cur_distance = abs(x_middle - contour_center_x) + abs(y_middle - contour_center_y)

                        if use_circle_r:

                            if cur_distance <= self.circle_r:
                                continue

                        a = cur_distance, contour
                        contour_list.append(a)

        contour_list.sort(key=lambda cont: cont[0])
        print(f'pocet zhod metinov { len(contour_list) }')
        closest_contours = contour_list[:metin_num]

        selected_contour_positions = []
        for _, contour in closest_contours:
            x, y, w, h = cv2.boundingRect(contour)
            contour_center_x = x + w // 2
            contour_center_y = y + h // 2
            selected_contour_positions.append((contour_center_x, contour_center_y))

        cv2.circle(np_image, (x_middle, y_middle), self.circle_r, (255, 190, 200),
                   2)

        if not closest_contours:
            return None, np_image

        print(f'posielam pocet { len(selected_contour_positions) }')
        return selected_contour_positions, np_image

    def __locate_metin_hp(self, np_image_hp_bar):
        return is_subimage(np_image_hp_bar, self.metin_hp_img)
