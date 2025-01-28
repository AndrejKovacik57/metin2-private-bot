import time
from PIL import ImageGrab, Image
import numpy as np
import pyautogui
import pyscreeze
import cv2
import json
import pygetwindow as gw
import os
import keyboard
from Modules import GameWindow
import re

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


def load_config(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, filename)

    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'r') as config:
        config_dict = json.load(config)

    return config_dict


def save_config(config_dict, filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, filename)
    with open(config_path, 'w') as config:
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
        print(f'button {button} pressed')
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


def mouse_left_click(pos_x, pos_y, window_title :str) -> None:
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        pyautogui.moveTo(pos_x, pos_y)
        print('KLIK KLIK KLIK')
        pyautogui.click()


def mouse_right_click(pos_x, pos_y, window_title :str) -> None:
    active_window = gw.getActiveWindow()
    if active_window and window_title in active_window.title:
        pyautogui.moveTo(pos_x, pos_y)
        pyautogui.rightClick()


def preprocess_image(image, ik = 0):
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
        # image = image[x - 1:x + w + 1, y - 1:y + h + 1]
        x_start = max(0, x - 1)
        y_start = max(0, y - 1)
        x_end = min(image.shape[0], x + w + 1)
        y_end = min(image.shape[1], y + h + 1)
        image = image[x_start:x_end, y_start:y_end]
    else:
        print('No mask')
        # return image

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

    cv2.imshow(f'image2 {ik}',image)
    cv2.waitKey(0)


    return image


def locate_image(path, np_image, confidence=0.9):
    try:
        location = pyautogui.locate(path, np_image, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        location = None
    return location


def load_image(path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    joined_path = os.path.join(script_dir, path)

    image = Image.open(joined_path)
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

def cancel_all(np_image:np.ndarray, cancel_img:np.ndarray, game_window:GameWindow) -> None:
    try:
        locations = pyautogui.locateAll(cancel_img, np_image, confidence=0.8)
    except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException) as e:
        locations = None

    if locations is not None:
        try:
            for location in locations:
                click_location_middle(location, game_window)
                time.sleep(0.5)
        except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException) as e:
            print("fix")

def click_location_middle(location, game_window:GameWindow) -> None:
    x = game_window.window_left + location.left + location.width / 2
    y = game_window.window_top + location.top + location.height / 2
    print(f'click x {x} y {x}')
    mouse_left_click(x, y, game_window.window_name)

def crop_image(image:np.ndarray, location:list[int]):
    x1, y1, x2, y2 = location
    return image[y1: y2, x1: x2]

def process_possible_double_values(value:str) -> (int, int):
    value = value.strip()
    if value == '':
        value_min = 0
        value_max = 0
    elif value.isdigit():
        value_min = int(value)
        value_max = 0
    else:
        value_list = re.split(r'[ ,/|-]', value)
        value_min = int(value_list[0].strip())
        value_max = int(value_list[1].strip())

    return value_min, value_max
