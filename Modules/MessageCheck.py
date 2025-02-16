import threading
import time
import numpy as np
import requests
import json
import io
from PIL import Image
from Modules.GameWindow import GameWindow
from Utils.Utils import load_image, locate_image, click_location_middle, get_window_screenshot, cancel_all


class MessageCheck:
    def __init__(self, game_window:GameWindow):
        self.game_window = game_window
        self.message_img = load_image('../bot_images/message.png')
        self.cancel_img = load_image('../bot_images/cancel_metin_button.png')
        self.webhook_url = ''
        self.user_id = ''
        self.message_timer = 0
        self.message_cd = 15

    def load_values(self, webhook:str, user_id:str):
        self.webhook_url = webhook
        self.user_id = user_id

    def locate_messages(self, np_image:np.ndarray):
        if self.webhook_url == '' or self.user_id == '':
            return

        timer_diff = time.time() - self.message_timer
        if self.message_timer == 0 or timer_diff >= self.message_cd:
            print('messages check')
            location = locate_image(self.message_img, np_image)
            if location is not None:

                click_location_middle(location, self.game_window)
                time.sleep(1)
                np_image = self.game_window.get_np_image()
                np_image = np_image[:, :, ::-1]
                image_to_send = Image.fromarray(np_image)

                image_bytes = io.BytesIO()
                image_to_send.save(image_bytes, format='PNG')
                image_bytes.seek(0)

                local_time = time.localtime(time.time())
                payload = self.get_payload(f"Nova sprava - {time.strftime('%Y-%m-%d %H:%M:%S', local_time)}")


                files = {
                    'file': ('image.png', image_bytes, 'image/png')
                }
                self.send_message_new_thread(payload, files)

                cancel_all(np_image, self.cancel_img, self.game_window)

    def get_payload(self, message):
        return {
            "content": f"<@{self.user_id}>, {message}",
            "username": "Image Sender"
        }

    def send_message_new_thread(self, payload, files=None):
        def send():
            if files:
                response = requests.post(self.webhook_url, data=payload, files=files)
            else:
                response = requests.post(self.webhook_url, data=payload)

            if response.status_code == 204:
                print("Message sent successfully!")
            else:
                print(f"Failed to send message. Status code: {response.status_code}")

        threading.Thread(target=send).start()