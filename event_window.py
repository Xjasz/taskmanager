import operator as op
import random
import time
import tkinter as tk
from datetime import datetime
from tkinter.ttk import Combobox

import pyautogui

import main_globals as mag
import main_utils as mau
from main_logger import logger, application_error_handler

EVENT_BUTTON = 'EVENT_BUTTON'
EVENT_LOGIC = 'EVENT_LOGIC'
EVENT_BUTTON_COLOR = 'green'
EVENT_LOGIC_COLOR = 'yellow'

class EventWindow(tk.Toplevel):
    def __init__(self, root, event_type, event_name, event_data=None, delete_callback=None, *args, **kwargs):
        _geometry = kwargs.pop("geometry", "200x200")
        _run_at_start = False if not event_data else event_data.get("run_at_start", False)
        _repeat = False if not event_data else event_data.get("repeat", False)
        _repeat_delay = 0 if not event_data else event_data.get("repeat_delay", 0)
        super().__init__(*args, **kwargs)
        self.root = root
        self.event_type = event_type
        self.event_name = event_name
        self.delete_callback = delete_callback
        self.geometry(_geometry)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.3)
        self.color = EVENT_BUTTON_COLOR if self.event_type == EVENT_BUTTON else EVENT_LOGIC_COLOR if self.event_type == EVENT_LOGIC else 'black'
        self.border_color = "black"
        self.border_width = 5
        self.config(bg=self.color, highlightbackground=self.border_color, highlightthickness=self.border_width)
        self.label = tk.Label(self, text=self.event_name, bg=self.color, fg="black")
        self.label.place(relx=0.5, rely=0.0, anchor="n")
        self.delete_button = tk.Button(self, text="X", command=self.delete_button, bg="red", fg="white", bd=0, highlightthickness=0)
        self.delete_button.place(relx=1.0, rely=0.0, anchor="ne")
        self.thread = None
        self.drag_data = {"x": 0, "y": 0}
        self.resize_data = {"x": 0, "y": 0, "width": 0, "height": 0}
        self.resizing = False
        self.moving = False
        self.grip_size = 10
        self.grip = self.create_grip()
        self.event_data = {
            "run_at_start": tk.BooleanVar(value=_run_at_start),
            "repeat": tk.BooleanVar(value=_repeat),
            "repeat_delay": tk.IntVar(value=int(_repeat_delay))
        }

    def update_event(self, update_type, update_value):
        logger.debug(f"UpdateEvent: ({self.event_name}) - {update_type} -> {update_value}")
        if update_type not in self.event_data:
            return
        var = self.event_data[update_type]
        try:
            var.set(update_value)
        except Exception:
            var.set(type(var.get())(update_value))

    def start_event(self):
        logger.debug(f"StartEvent: ({self.event_name})")
        if not mag.task_running:
            return
        if mau.is_user_active():
            logger.debug("User active retrying in 5s")
            self.root.after(5000, self.start_event)
            return
        for w in mag.event_windows:
            w.attributes("-alpha", 0.0)
        try:
            result = self.execute()
            self.handle_next(result)
            if self.event_data["repeat"].get():
                self.schedule_repeat_event()
        except Exception as e:
            application_error_handler(f"Error executing {self.event_name}: {e}")
        for w in mag.event_windows:
            w.attributes("-alpha", 0.3)

    def stop_event(self):
        logger.debug(f"StopEvent: ({self.event_name})")
        mag.task_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def execute(self):
        raise NotImplementedError("execute() must be implemented by subclasses")

    def schedule_repeat_event(self):
        delay = self.event_data["repeat_delay"].get()
        logger.debug(f"RepeatEvent: ({self.event_name}) in {delay} seconds")
        self.root.after(int(delay * 1000), self.start_event)

    def handle_next(self, result):
        if "next_event" not in self.event_data:
            return
        name = self.event_data["next_event"].get()
        delay = self.event_data["next_event_delay"].get()
        if name and name != "None":
            win = next((w for w in mag.event_windows if w.event_name == name), None)
            if win:
                logger.debug(f"NextEvent: ({name}) in ({delay}) seconds")
                self.root.after(int(delay * 1000), win.start_event)

    def create_grip(self):
        overlay_grip = tk.Frame(self, cursor="size_nw_se", bg=self.border_color, width=self.grip_size, height=self.grip_size)
        overlay_grip.bind("<Button-1>", self.start_resize)
        overlay_grip.bind("<B1-Motion>", self.do_resize)
        overlay_grip.bind("<ButtonRelease-1>", self.stop_resize)
        overlay_grip.place(x=0, y=0)
        return overlay_grip

    def update_grip(self):
        self.grip.place(x=0, y=0)

    def start_move(self, event):
        if not self.resizing and not mag.task_running:
            self.moving = True
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def do_move(self, event):
        if self.moving:
            x = self.winfo_x() + event.x - self.drag_data["x"]
            y = self.winfo_y() + event.y - self.drag_data["y"]
            self.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        if self.moving:
            self.moving = False
            self.drag_data = {"x": 0, "y": 0}
            logger.debug(f"Stopped move: {self.event_name} at {self.winfo_x()},{self.winfo_y()}")

    def start_resize(self, event):
        if not mag.task_running:
            self.resizing = True
            self.resize_data = {"x": event.x,"y": event.y,"width": self.winfo_width(),"height": self.winfo_height(),}

    def do_resize(self, event):
        if not self.resizing:
            return
        delta_x = event.x - self.resize_data["x"]
        delta_y = event.y - self.resize_data["y"]
        new_width = self.resize_data["width"] + delta_x
        new_height = self.resize_data["height"] + delta_y
        self.geometry(f"{new_width}x{new_height}")
        self.update_grip()

    def stop_resize(self, event):
        if self.resizing:
            self.resizing = False
            self.resize_data = {"x": 0, "y": 0, "width": 0, "height": 0}
            logger.debug(f"Stopped resize: {self.event_name} size {self.winfo_width()}x{self.winfo_height()}")

    def delete_button(self):
        if not mag.task_running:
            self.delete_callback(self)
            self.destroy()

class EventButton(EventWindow):
    next_event_menu: Combobox
    def __init__(self, root, event_name, event_data=None, delete_callback=None, *args, **kwargs):
        super().__init__(root, EVENT_BUTTON, event_name, event_data, delete_callback, *args, **kwargs)
        default = event_data or {}
        self.event_data.update({
            "next_event": tk.StringVar(value=str(default.get("next_event", "None"))),
            "next_event_delay": tk.IntVar(value=int(default.get("next_event_delay", 0))),
            "type_text": tk.BooleanVar(value=bool(default.get("type_text", False))),
            "entered_text": tk.StringVar(value=str(default.get("entered_text", ""))),
            "press_enter": tk.BooleanVar(value=bool(default.get("press_enter", False))),
            "press_backspace": tk.BooleanVar(value=bool(default.get("press_backspace", False))),
            "random_position": tk.BooleanVar(value=bool(default.get("random_position", True))),
            "move_mouse_back": tk.BooleanVar(value=bool(default.get("move_mouse_back", True))),
            "double_click": tk.BooleanVar(value=bool(default.get("double_click", False))),
        })

    def execute(self):
        try:
            entered_text = self.event_data["entered_text"].get()
            orig_x, orig_y = pyautogui.position()
            w, h = self.winfo_width(), self.winfo_height()
            base_x = self.winfo_x() + w // 4
            base_y = self.winfo_y() + h // 4
            rp = self.event_data["random_position"].get()
            click_x = base_x + (random.randint(0, w//2) if rp else w//2)
            click_y = base_y + (random.randint(0, h//2) if rp else h//2)
            pyautogui.moveTo(click_x, click_y, duration=0.05)
            pyautogui.click()
            time.sleep(0.1)
            if self.event_data["double_click"].get():
                pyautogui.click(); time.sleep(0.1)
            if self.event_data["press_enter"].get():
                pyautogui.press('enter'); time.sleep(0.01)
            if self.event_data["press_backspace"].get():
                pyautogui.press('backspace'); time.sleep(0.01)
            if len(entered_text) > 0:
                pyautogui.write(entered_text, interval=0.02)
            if self.event_data["move_mouse_back"].get():
                pyautogui.moveTo(orig_x, orig_y)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logger.debug(f"Clicked '{self.event_name}' at ({click_x},{click_y}) @ {timestamp}")
        except Exception as e:
            application_error_handler(f"Error in EventButton.execute: {e}")

class EventLogic(EventWindow):
    next_event_success_menu: Combobox
    next_event_fail_menu: Combobox
    def __init__(self, root, event_name, event_data=None, delete_callback=None, *args, **kwargs):
        super().__init__(root, EVENT_LOGIC, event_name, event_data, delete_callback, *args, **kwargs)
        default = event_data or {}
        self.event_data.update({
            "next_event_success": tk.StringVar(value=str(default.get("next_event_success", "None"))),
            "next_event_success_delay": tk.IntVar(value=int(default.get("next_event_success_delay", 0))),
            "logic_type": tk.StringVar(value=str(default.get("logic_type", "="))),
            "next_event_fail": tk.StringVar(value=str(default.get("next_event_fail", "None"))),
            "next_event_fail_delay": tk.IntVar(value=int(default.get("next_event_fail_delay", 0))),
            "logic_action": tk.StringVar(value=str(default.get("logic_action", "text_logic"))),
            "logic_value": tk.StringVar(value=str(default.get("logic_value", ""))),
        })

    def execute(self):
        action = self.event_data["logic_action"].get()
        test_val = self.event_data["logic_value"].get()
        operator_str = self.event_data["logic_type"].get()
        if action == "text_logic":
            text = mau.get_text_from_view(self, save_screenshot=False)
            if operator_str == "contains" or operator_str == "like":
                return test_val.lower() in text.lower()
            if operator_str in ("=", "!="):
                if operator_str == "=":
                    return text == test_val
                else:
                    return text != test_val
            try:
                num_text = float(text)
                num_val = float(test_val)
            except ValueError:
                return False
            ops = {">": op.gt,"<": op.lt,">=": op.ge,"<=": op.le,}
            return ops[operator_str](num_text, num_val)
        elif action == "color_logic":
            current_color = mau.get_color_from_view(self)
            hexv = test_val.lstrip("#")
            target = tuple(int(hexv[i : i+2], 16) for i in (0, 2, 4))
            ops = { "=":op.eq, "!=":op.ne }
            return ops[operator_str](current_color, target)
        return False

    def handle_next(self, result):
        key = "next_event_success" if result else "next_event_fail"
        delay_key = f"{key}_delay"
        name = self.event_data[key].get()
        delay = self.event_data[delay_key].get()
        if name and name != "None":
            win = next((w for w in mag.event_windows if w.event_name == name), None)
            if win:
                self.root.after(int(delay * 1000), win.start_event)