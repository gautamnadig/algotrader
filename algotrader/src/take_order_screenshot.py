from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time

import pyautogui
from datetime import datetime
import os

def take_screenshot(output_dir="/home/ayandas100/data/screenshots", prefix="order"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)

    screenshot = pyautogui.screenshot()
    screenshot.save(output_path)
    print(f"✅ Screenshot saved instantly to {output_path}")
