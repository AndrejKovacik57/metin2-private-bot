import hashlib
import numpy as np
from Modules.GameWindow import GameWindow
from Utils.Utils import load_image, locate_image, resize_image, preprocess_image ,mouse_left_click, crop_image
import pytesseract
import cv2
import time
import logging


class AntiBot:
    def __init__(self, text_hash_map: dict[str:str], game_window:GameWindow):
        self.bot_img_path = None
        self.bot_check_location = None
        self.text_hash_map = text_hash_map

        self.game_window = game_window

        self.custom_config = r'--oem 3 --psm 6 outputbase digits'
        # Configure logging
        logging.basicConfig(
            filename='../bot_solver2.log',  # Log to a file
            level=logging.INFO,  # Set the logging level
            format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
            datefmt='%Y-%m-%d %H:%M:%S'  # Date format
        )
        pytesseract.pytesseract.tesseract_cmd = ''

        self.__load_images()



    def load_values(self, tesseract_path:str, bot_check_location:tuple[int, int, int, int]):
        self.bot_check_location = bot_check_location
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def  __load_images(self) -> None:
        self.bot_img_path = load_image('../bot_images/bot_ochrana.png')


    def bot_solver(self, np_image:np.ndarray) -> None:
        cropped_image_x1, cropped_image_y1, cropped_image_x2, cropped_image_y2 = self.bot_check_location
        cropped_image = np_image[cropped_image_y1:cropped_image_y2, cropped_image_x1:cropped_image_x2]
        location = locate_image(self.bot_img_path, cropped_image, confidence=0.70)
        if location is not None:
            crop = 15
            options = [  # coords for options menu buttons
                (location.left + crop, location.top, location.left + (location.width // 2) - crop, location.top + location.height // 3), # lavo,hore, lavo+polka sirky, hore+ tretina vrchu
                (location.left + crop + location.width // 2, location.top, location.left + location.width - crop, location.top + location.height // 3),# lavo + pola sirky,hore, lavo+polka sirky + sirka, hore+ tretina vrchu
                (location.left + crop, location.top + location.height // 3, location.left + (location.width // 2) - crop, location.top + 2* (location.height // 3)),
                (location.left + crop + location.width // 2, location.top + location.height // 3, location.left + location.width - crop, location.top + 2* (location.height // 3)),
                (location.left + crop + location.width // 4, location.top + 2 * (location.height // 3) + 8, location.left + ((location.width // 4) + 2 * (location.width // 4)) - crop, location.top + 3 *(location.height // 3))
            ]
            # code to find
            x_find = location.left + location.width//2 # middle
            x_find_width = x_find + 55   # width i would like to have
            y_find = location.top - 34 # top location of what i want
            y_find_height = y_find + 20 # its height
            resized_code_to_find = resize_image(cropped_image[y_find:y_find_height, x_find:x_find_width])
            extracted_text_code_to_find = pytesseract.image_to_string(resized_code_to_find, config=self.custom_config)
            code_to_find_number = extracted_text_code_to_find[:4]
            print(f'code_to_find_number {code_to_find_number}')
            logging.info(f'code_to_find_number {code_to_find_number}')
            if len(code_to_find_number) < 4:
                logging.info(f'code_to_find_number is not length of 4')
                return
            smallest_difference = 999
            output = None
            smallest_difference_num = None
            exact_match = False
            out_num = ''
            for option_tuple in options:
                result_x1, result_y1, result_x2, result_y2 = option_tuple
                option = cropped_image[result_y1:result_y2, result_x1:result_x2]
                preprocess_image(option)
                option_hash = hashlib.md5(preprocess_image(option)).hexdigest()

                if option_hash in self.text_hash_map:
                    option_number = self.text_hash_map[option_hash]
                else:
                    resized_option = resize_image(option)
                    extracted_text_option = pytesseract.image_to_string(resized_option, config= self.custom_config)
                    option_number = extracted_text_option[:4]
                    logging.info(f'tesseract fallback')

                print(f'option_number {option_number}')
                logging.info(f'option_number {option_number}')

                result_center_x = result_x1 + (result_x2 - result_x1) // 2
                result_center_y = result_y1 + (result_y2 - result_y1) // 2

                pos_x = result_center_x + cropped_image_x1 + self.game_window.window_left + 5
                pos_y = result_center_y + cropped_image_y1 + self.game_window.window_top + 1

                if option_number == code_to_find_number:
                    print(f'found matching option {option_number}')
                    logging.info(f'found matching option {option_number}')
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
            mouse_left_click(to_click_x, to_click_y, self.game_window.window_name)
            time.sleep(3)