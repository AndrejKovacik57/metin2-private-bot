import pygetwindow as gw
import numpy as np
from PIL import ImageGrab
import cv2
import json

def nothing(x):
    pass

def get_window_screenshot(window):
    left, top, right, bottom = window.left, window.top, window.right, window.bottom
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=False, all_screens=True)
    return screenshot

def export_settings_to_json(filename="settings_export.json"):
    settings = {
        "mask": {
            "hMin": cv2.getTrackbarPos('HMin', 'image'),
            "sMin": cv2.getTrackbarPos('SMin', 'image'),
            "vMin": cv2.getTrackbarPos('VMin', 'image'),
            "hMax": cv2.getTrackbarPos('HMax', 'image'),
            "sMax": cv2.getTrackbarPos('SMax', 'image'),
            "vMax": cv2.getTrackbarPos('VMax', 'image')
        },
        "contourLow": cv2.getTrackbarPos('contour_low', 'image'),
        "contourHigh": cv2.getTrackbarPos('contour_high', 'image'),
        "aspect_low": int(cv2.getTrackbarPos('aspect_ratio_low', 'image') / 100 * 100),
        "aspect_high": int(cv2.getTrackbarPos('aspect_ratio_high', 'image') / 100 * 100),
        "circularity": int(cv2.getTrackbarPos('circularity', 'image') / 1000 * 100)
    }

    with open(filename, 'w') as f:
        json.dump(settings, f, indent=4)
    print(f"[INFO] Settings exported to '{filename}'")

def main(window_title):
    cv2.namedWindow('image')

    # Trackbars
    cv2.createTrackbar('HMin', 'image', 0, 255, nothing)
    cv2.createTrackbar('SMin', 'image', 0, 255, nothing)
    cv2.createTrackbar('VMin', 'image', 0, 255, nothing)
    cv2.createTrackbar('HMax', 'image', 255, 255, nothing)
    cv2.createTrackbar('SMax', 'image', 255, 255, nothing)
    cv2.createTrackbar('VMax', 'image', 255, 255, nothing)
    cv2.createTrackbar('contour_low', 'image', 2500, 10000, nothing)
    cv2.createTrackbar('contour_high', 'image', 7000, 50000, nothing)
    cv2.createTrackbar('aspect_ratio_low', 'image', int(0.8 * 100), int(3.0 * 100), nothing)
    cv2.createTrackbar('aspect_ratio_high', 'image', int(1.3 * 100), int(3.0 * 100), nothing)
    cv2.createTrackbar('circularity', 'image', int(0.7 * 1000), int(1000), nothing)

    while True:
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            print(f"[ERROR] No window found with title '{window_title}'")
            return
        metin_window = windows[0]
        screenshot = get_window_screenshot(metin_window)

        x1, y1 = 259, 212
        x2, y2 = 2000, 1000
        np_image = np.array(screenshot)
        np_image = np_image[y1:y2, x1:x2]
        np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        hsv = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)

        hMin = cv2.getTrackbarPos('HMin', 'image')
        sMin = cv2.getTrackbarPos('SMin', 'image')
        vMin = cv2.getTrackbarPos('VMin', 'image')
        hMax = cv2.getTrackbarPos('HMax', 'image')
        sMax = cv2.getTrackbarPos('SMax', 'image')
        vMax = cv2.getTrackbarPos('VMax', 'image')
        contour_low = cv2.getTrackbarPos('contour_low', 'image')
        contour_high = cv2.getTrackbarPos('contour_high', 'image')
        aspect_ratio_low = cv2.getTrackbarPos('aspect_ratio_low', 'image') / 100.0
        aspect_ratio_high = cv2.getTrackbarPos('aspect_ratio_high', 'image') / 100.0
        circularity_min = cv2.getTrackbarPos('circularity', 'image') / 1000.0

        lower = np.array([hMin, sMin, vMin])
        upper = np.array([hMax, sMax, vMax])
        mask = cv2.inRange(hsv, lower, upper)
        masked_image = cv2.bitwise_and(np_image, np_image, mask=mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Contours found: {len(contours)}")

        for contour in contours:
            area = cv2.contourArea(contour)
            if contour_low < area < contour_high:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                circularity = 4 * np.pi * (area / (perimeter * perimeter))
                if aspect_ratio_low <= aspect_ratio <= aspect_ratio_high and circularity >= circularity_min:
                    cv2.rectangle(masked_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('image', masked_image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('e'):
            export_settings_to_json()

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main('EmtGen')
