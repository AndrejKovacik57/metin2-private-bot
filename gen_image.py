import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import os

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
        dot_size = random.randint(1, 7)
        line_length = random.randint(1, 7)
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
def create_image():
    # High-resolution dimensions (2x original size)
    high_res_width, high_res_height = 200, 200  # Image size (2x of 100x100)
    image = Image.new('RGB', (high_res_width, high_res_height), random_color())  # Random background color
    draw = ImageDraw.Draw(image)

    # Randomly place the characters
    font_paths = ["C:/Windows/Fonts/comic.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf",
                  "C:/Windows/Fonts/CascadiaCode.ttf", "C:/Windows/Fonts/CascadiaMono.ttf",
                  "C:/Windows/Fonts/constani.ttf"]
    font_path = random.choice(font_paths)
    font = ImageFont.truetype(font_path, random.randint(80, 100))  # Use a larger font for high-res image
    text = random_char()

    # Calculate text size using textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Create a larger canvas for the rotated text to avoid cutting off
    canvas_size = max(text_width, text_height) * 2
    text_image = Image.new('RGBA', (canvas_size, canvas_size), (255, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_image)

    # Draw the text at the center of the larger canvas
    text_x = (canvas_size - text_width) // 2
    text_y = (canvas_size - text_height) // 2
    text_draw.text((text_x, text_y), text, font=font, fill=random_color())

    # Random rotation
    angle = random.uniform(-30, 30)
    rotated_text = text_image.rotate(angle, expand=1, resample=Image.BICUBIC)

    # Randomly decide if elements should be drawn in front of or behind the text
    if random.choice(["behind", "in_front"]) == "behind":
        # Draw elements first, then paste the rotated text on top
        total_elements = random.randint(1, 7)
        draw_random_elements(draw, high_res_width, high_res_height, total_elements)
        # Paste the rotated text at the center of the original image
        paste_x = (high_res_width - rotated_text.width) // 2
        paste_y = (high_res_height - rotated_text.height) // 2
        image.paste(rotated_text, (paste_x, paste_y), rotated_text)
    else:
        # Paste the rotated text first, then draw elements on top
        paste_x = (high_res_width - rotated_text.width) // 2
        paste_y = (high_res_height - rotated_text.height) // 2
        image.paste(rotated_text, (paste_x, paste_y), rotated_text)
        total_elements = random.randint(1, 7)
        draw_random_elements(draw, high_res_width, high_res_height, total_elements)

    # Downscale to original size for smoothness
    final_image = image.resize((100, 100), Image.LANCZOS)

    return final_image, text


# Generate and save images
def create_images():
    start_time = time.time()
    if not os.path.exists('training_images'):
        os.makedirs('training_images')

    for i in range(100000):
        img, text = create_image()
        file_name = f"{text}_{i}.png"  # Save images with their text label and a unique index
        img.save(os.path.join('training_images', file_name))
        print(f"Saved {file_name}")

    print(f'Done, {time.time() - start_time}')


create_images()
