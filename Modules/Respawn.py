import time
import pyautogui
import numpy as np

from Modules.GameWindow import GameWindow
from Utils.Utils import locate_image, load_image


class Respawn:
    def __init__(self, game_window:GameWindow):
        self.respawn_timer_diff = 0
        self.respawn_timer = 0
        self.restart_img = load_image('../bot_images/restart_img.png')
        self.game_window = game_window

    def death_check(self, np_image:np.ndarray) -> None:
        self.respawn_timer_diff = time.time() - self.respawn_timer
        if self.respawn_timer == 0 or self.respawn_timer != 0 and self.respawn_timer_diff >= 2:
            print('death_check')
            self.respawn_timer = time.time()

            respawn_location = locate_image(self.restart_img, np_image, confidence=0.8)
            if respawn_location is not None:
                respawn_x = self.game_window.window_left + 20 + respawn_location.left + respawn_location.width / 2
                respawn_y = self.game_window.window_top + respawn_location.top + respawn_location.height / 2
                time.sleep(1)
                print('death_check - klik')
                pyautogui.moveTo(respawn_x, respawn_y)
                time.sleep(0.2)
                pyautogui.click()
                time.sleep(0.2)
