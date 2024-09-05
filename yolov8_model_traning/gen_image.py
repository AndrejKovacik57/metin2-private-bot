import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import os
import numpy as np
import cv2

# Generate a random character
def random_char():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choice(chars) for _ in range(2))


# Generate random color
def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))


# Draw random dots, lines, stars, and crosses
def draw_random_elements(draw, width, height, total_elements=7):
    elements = ["dot", "line", "star", "cross"]
    for _ in range(total_elements):
        dot_size = random.randint(1, 4)
        line_length = random.randint(1, 5)
        element = random.choice(elements)
        if element == "dot":
            # Draw random dots or ovals
            x1 = random.randint(0, width - dot_size)
            y1 = random.randint(0, height - dot_size)
            x2 = x1 + random.randint(dot_size, dot_size * 2)  # Random width for the oval
            y2 = y1 + random.randint(dot_size, dot_size * 2)  # Random height for the oval
            draw.ellipse((x1, y1, x2, y2), fill=random_color())

        elif element == "line":
            # Randomly choose between vertical or horizontal line
            if random.choice(["vertical", "horizontal"]) == "vertical":
                # Draw vertical line
                start_x = random.randint(0, width - line_length)
                start_y = random.randint(0, height - line_length)
                end_x = start_x  # Keep the x-coordinate the same for vertical lines
                end_y = start_y + random.randint(-line_length, line_length)  # Adjust only the y-coordinate
            else:
                # Draw horizontal line
                start_x = random.randint(0, width)
                start_y = random.randint(0, height)
                end_x = start_x + random.randint(-line_length, line_length)  # Adjust only the x-coordinate
                end_y = start_y  # Keep the y-coordinate the same for horizontal lines

            draw.line((start_x, start_y, end_x, end_y), fill=random_color(), width=2)

        elif element == "star":
            # Draw two overlapping ovals to create a star-like shape
            color = random_color()
            center_x = random.randint(dot_size, width - dot_size)
            center_y = random.randint(dot_size, height - dot_size)

            # Draw first oval (horizontal)
            x1 = center_x - dot_size
            y1 = center_y - int(dot_size / 2)
            x2 = center_x + dot_size
            y2 = center_y + int(dot_size / 2)
            draw.ellipse((x1, y1, x2, y2), fill=color)

            # Draw second oval (vertical, intersecting the first)
            x1 = center_x - int(dot_size / 2)
            y1 = center_y - dot_size
            x2 = center_x + int(dot_size / 2)
            y2 = center_y + dot_size
            draw.ellipse((x1, y1, x2, y2), fill=color)


# Create a single image with random characters, rotation, and anti-captcha elements
def create_image(combo_to_id):
    high_res_width, high_res_height = 64, 64
    image = Image.new('RGB', (high_res_width, high_res_height), random_color())
    draw = ImageDraw.Draw(image)

    font_paths = ["C:/Windows/Fonts/comic.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf",
                  "C:/Windows/Fonts/CascadiaCode.ttf", "C:/Windows/Fonts/CascadiaMono.ttf",
                  "C:/Windows/Fonts/constani.ttf"]
    font_path = random.choice(font_paths)
    font = ImageFont.truetype(font_path, random.randint(25, 32))
    text = random_char()  # Generate two characters

    # Get the class ID for the character combination
    class_id = combo_to_id[text]

    # Calculate bounding box for the whole text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    canvas_size = max(text_width, text_height) * 2
    text_image = Image.new('RGBA', (canvas_size, canvas_size), (255, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_image)

    # Draw the text at the center of the larger canvas
    text_x = (canvas_size - text_width) // 2
    text_y = (canvas_size - text_height) // 2
    text_draw.text((text_x, text_y), text, font=font, fill=random_color())

    # Random rotation
    angle = random.uniform(-30, 30)
    rotated_text = text_image.rotate(angle, expand=1, resample=Image.Resampling.BICUBIC)
    rotated_bbox = rotated_text.getbbox()
    # Randomly decide if elements should be drawn in front of or behind the text
    if random.choice(["behind", "in_front"]) == "behind":
        draw_random_elements(draw, high_res_width, high_res_height, random.randint(1, 7))
        paste_x = (high_res_width - rotated_text.width) // 2 + random.randint(-10,10)
        paste_y = (high_res_height - rotated_text.height) // 2 + random.randint(-10,10)
        image.paste(rotated_text, (paste_x, paste_y), rotated_text)
    else:
        paste_x = (high_res_width - rotated_text.width) // 2 + random.randint(-10,10)
        paste_y = (high_res_height - rotated_text.height) // 2 + random.randint(-10,10)
        image.paste(rotated_text, (paste_x, paste_y), rotated_text)
        draw_random_elements(draw, high_res_width, high_res_height, random.randint(2, 7))
    # Scaling factors
    #
    # np_image = np.array(image)
    # np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
    # np_image = cv2.resize(np_image, (128, 128), interpolation=cv2.INTER_CUBIC)

    x = (paste_x + rotated_bbox[0])*2
    y = (paste_y + rotated_bbox[1])*2
    w = (rotated_bbox[2] - rotated_bbox[0])*2
    h = (rotated_bbox[3] - rotated_bbox[1])*2

    # cv2.rectangle(np_image, (x, y), (x+w, y+h), (0, 255, 255), 2)

    x_center = (x + w // 2)
    y_center = (y + h // 2)


    # image = Image.fromarray(np_image)

    return image, text, x_center/128, y_center/128, w/128, h/128, class_id



# Generate and save images
def create_images():
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    combinations = [a + b for a in characters for b in characters]
    combo_to_id = {combo: idx for idx, combo in enumerate(combinations)}

    start_time = time.time()
    if not os.path.exists('training_images'):
        os.makedirs('training_images')

    for i in range(100000):
        img, text, x_center, y_center, bbox_width, bbox_height, class_id = create_image(combo_to_id)
        file_name = f"{text}_{i}.png"
        img.save(os.path.join('training_images', file_name))
        print(f"Saved {file_name}")

        # Save the corresponding .txt file for YOLOv8
        txt_file_name = f"{text}_{i}.txt"
        with open(os.path.join('training_images', txt_file_name), 'w') as f:
            f.write(f"{class_id} {x_center} {y_center} {bbox_width} {bbox_height}\n")

    print(f'Done, {time.time() - start_time}')


create_images()

# Example usage:
