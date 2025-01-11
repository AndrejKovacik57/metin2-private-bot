import pygetwindow as gw
import cv2
import numpy as np
from Utils.Utils import get_window_screenshot
from Exceptions.ExceptionModels import CustomError
from Utils.Constants import MISSING_METIN_NAME_ERROR

class GameWindow:
    def __init__(self):
        self.window_name = None
        self.window_left = None
        self.window_top = None
        self.window_right = None
        self.window_bottom = None
        self.metin_window = None


    def get_np_image(self, convert_color=True) -> np.ndarray:
        if not self.window_name:
            raise CustomError(MISSING_METIN_NAME_ERROR)

        metin_window = gw.getWindowsWithTitle(self.window_name)[0]
        screenshot = get_window_screenshot(metin_window)
        self.window_left = metin_window.left
        self.window_top = metin_window.top
        self.window_right = metin_window.right
        self.window_bottom = metin_window.bottom
        self.metin_window = metin_window

        np_image = np.array(screenshot)
        if convert_color:
            np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
        return np_image