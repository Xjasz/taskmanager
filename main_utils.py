import ctypes
import json
import os
import re
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk
import pyautogui
import pytesseract
from PIL import ImageOps, ImageGrab
from pytesseract import pytesseract

from main_logger import logger, application_error_handler

movement_check_interval = 0.05

def is_user_active():
    last_position = pyautogui.position()
    start_time = time.time()
    while time.time() - start_time < movement_check_interval:
        current_position = pyautogui.position()
        if current_position != last_position:
            return True
        time.sleep(0.01)
    if is_key_pressed():
        return True
    if is_left_button_down() or is_right_button_down() or is_mouse_scrolled():
        return True
    return False

def is_key_pressed():
    for key_code in range(0x00, 0xFF):
        if (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0:
            return True
    return False

def is_left_button_down():
    return (ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000) != 0

def is_right_button_down():
    return (ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000) != 0

def is_mouse_scrolled():
    scroll_up = ctypes.windll.user32.GetAsyncKeyState(0x0800) & 0x8000
    scroll_down = ctypes.windll.user32.GetAsyncKeyState(0x0400) & 0x8000
    return scroll_up != 0 or scroll_down != 0

def load_json_file(file_path):
    logger.debug(f"load_json_file{file_path}")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_json_file(file_path, json_data):
    logger.debug(f"save_json_file{file_path}")
    with open(file_path, 'w') as f:
        json.dump(json_data, f, indent=4)

def center_dialog_on_window(parent, dlg_width=300, dlg_height=150):
    window_width = parent.winfo_width()
    window_height = parent.winfo_height()
    window_x = parent.winfo_x()
    window_y = parent.winfo_y()
    position_top = window_y + (window_height // 2) - (dlg_height // 2)
    position_left = window_x + (window_width // 2) - (dlg_width // 2)
    dlg = tk.Toplevel(parent)
    dlg.geometry(f'{dlg_width}x{dlg_height}+{position_left}+{position_top}')
    dlg.transient(parent)
    dlg.grab_set()
    return dlg

def ask_selection(root, options, title="Select", prompt="Please choose:"):
    try:
        if not options:
            return None
        dlg = center_dialog_on_window(root, dlg_width=300, dlg_height=150)
        dlg.title(title)
        dlg.result = None
        tk.Label(dlg, text=prompt).pack(padx=10, pady=(10, 0))
        combo = ttk.Combobox(dlg, values=options, state="readonly")
        combo.current(0)
        combo.pack(padx=10, pady=5)
        def on_ok():
            dlg.result = combo.get()
            dlg.destroy()
        btn_frame = tk.Frame(dlg)
        btn_frame.pack(padx=10, pady=5)
        tk.Button(btn_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dlg.destroy, width=10).pack(side=tk.LEFT)
        root.wait_window(dlg)
        return dlg.result
    except Exception as e:
        application_error_handler(f"Error in ask_selection: {e}")
        return None

def grab_region(x, y, w, h):
    return ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)

def get_text_from_view(root, save_screenshot=False):
    x, y = root.winfo_x(), root.winfo_y()
    w, h = root.winfo_width(), root.winfo_height()
    img = grab_region(x, y, w, h)
    proc = preprocess(img)
    if save_screenshot:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        proc.save(f"dbg_{ts}.png")
        logger.debug(f"Saved debug image: dbg_{ts}.png at X:{x} Y:{y} W:{w} H:{h}")
    raw = pytesseract.image_to_string(proc)
    text = raw
    logger.debug(f"OCR raw='{raw}'")
    if not raw:
        raw = pytesseract.image_to_string(proc, config="--oem 3 --psm 6")
        text = re.sub(r"[^A-Za-z0-9.]", '', raw).strip()
        logger.debug(f"OCR pass2 raw='{raw}' -> cleaned='{text}'")
    return text

def get_color_from_view(root):
    x, y = root.winfo_x(), root.winfo_y()
    w, h = root.winfo_width(), root.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    cx, cy = w // 2, h // 2
    return img.getpixel((cx, cy))

def preprocess(img, min_h=30, upscale=2, contrast_thresh=30):
    gray = ImageOps.grayscale(img)
    w, h = gray.size
    hist = gray.histogram()
    contrast = max(hist) - min(hist)
    if contrast < contrast_thresh:
        bw = gray.point(lambda px: 0 if px < 128 else 255, mode='1')
        return bw
    return gray
