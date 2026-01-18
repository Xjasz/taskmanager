import os
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from typing import Optional

import main_globals as mag
import main_utils as mau

from event_window import EventButton, EventLogic, EVENT_LOGIC, EVENT_BUTTON
from main_logger import logger, application_error_handler


class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("400x600")
        self.task_name = ""
        self.overlays_visible = True
        self.tasks = mau.load_json_file(mag.taskmanager_file)
        if self.task_name == '':
            self.label = tk.Label(root, text=f"Create or Load Task", font=("Arial", 14, "bold"), anchor="center")
        else:
            self.label = tk.Label(root, text=f"Loaded: {self.task_name}", font=("Arial", 14, "bold"), anchor="center")
        self.label.pack(padx=5, pady=(15, 0))
        action_frame = tk.Frame(self.root)
        action_frame.pack(pady=5)
        self.new_task_button = tk.Button(action_frame, text="Create Task", command=self.new_task, width=15)
        self.save_button = tk.Button(action_frame, text="Save Task", command=self.save_task, width=15)
        self.load_button = tk.Button(action_frame, text="Load Task", command=self.load_task, width=15)
        self.new_task_button.pack(side=tk.LEFT, padx=5, pady=(10, 0))
        self.save_button.pack(side=tk.LEFT, padx=5, pady=(10, 0))
        self.load_button.pack(side=tk.LEFT, padx=5, pady=(10, 0))
        runtime_frame = tk.Frame(self.root)
        runtime_frame.pack(pady=5)
        self.start_button = tk.Button(runtime_frame, text="Start Task", command=self.start_task, width=15, bg="green", fg="white")
        self.stop_button = tk.Button(runtime_frame, text="Stop Task", command=self.stop_task, width=15, bg="red", fg="white")
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.status_label = tk.Label(root, text="Status: Idle", font=("Arial", 10), anchor="center")
        self.status_label.pack(pady=5)
        sep = tk.Frame(self.root, height=2, bd=1, relief=tk.SUNKEN)
        sep.pack(fill='x', padx=30, pady=10)
        self.create_event_button = tk.Button(root, text="Add Event Button", command=lambda: self.create_new_event(EVENT_BUTTON), width=15)
        self.create_event_button.pack(pady=5)
        self.create_event_logic = tk.Button(root, text="Add Event Logic", command=lambda: self.create_new_event(EVENT_LOGIC), width=15)
        self.create_event_logic.pack(pady=5)
        self.toggle_overlays_button = tk.Button(root, text="Toggle Overlays", command=self.toggle_overlays, width=15)
        self.toggle_overlays_button.pack(pady=5)
        self.box_container = tk.Frame(self.root)
        self.box_container.pack(fill="both", expand=True, pady=10)
        self.box_canvas = tk.Canvas(self.box_container, highlightthickness=0)
        self.box_scrollbar = tk.Scrollbar(self.box_container,orient="vertical",command=self.box_canvas.yview)
        self.box_canvas.configure(yscrollcommand=self.box_scrollbar.set)
        self.box_scrollbar.pack(side="right", fill="y")
        self.box_canvas.pack(side="left", fill="both", expand=True)
        self.box_label_frame = tk.Frame(self.box_canvas)
        self.box_canvas.create_window((0, 0), window=self.box_label_frame, anchor="nw")
        self.box_label_frame.bind("<Configure>",lambda e: self.box_canvas.configure(scrollregion=self.box_canvas.bbox("all")))
        self.box_canvas.bind_all("<MouseWheel>",lambda e: self.box_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self._vcmd = (self.root.register(self._only_digits), '%P')

    def _only_digits(self, proposed: str) -> bool:
        return proposed.isdigit() or proposed == ''

    def toggle_overlays(self, force_visible=False, force_hide=False):
        if not hasattr(self, 'overlays_visible'):
            self.overlays_visible = True
        self.overlays_visible = not self.overlays_visible
        if force_visible:
            self.overlays_visible = True
        if force_hide:
            self.overlays_visible = False
        for window in mag.event_windows:
            if self.overlays_visible:
                window.deiconify()
            else:
                window.withdraw()

    def new_task(self):
        task_name = simpledialog.askstring("New Task", "Enter the name of the new task:", parent=self.root)
        if task_name:
            self.tasks[task_name] = []
            mau.save_json_file(mag.taskmanager_file, self.tasks)
            self.task_name = task_name
            self.clear_events()
            self.label.config(text=f"Loaded: {self.task_name}")

    def get_task_events(self):
        task_events = self.tasks[self.task_name]
        return task_events

    def get_task_event_names(self):
        event_names = [e["event_name"] for e in self.get_task_events()]
        available_events = ["None"] if len(event_names) < 1 else ["None"] + event_names
        return available_events

    def update_task_ui(self):
        current = []
        for ev in mag.event_windows:
            d = {
                "event_type": ev.event_type,
                "event_name": ev.event_name,
                "geometry": ev.geometry(),
                "run_at_start": ev.event_data["run_at_start"].get(),
                "repeat": ev.event_data["repeat"].get(),
                "repeat_delay": ev.event_data["repeat_delay"].get(),
            }
            if isinstance(ev, EventButton):
                d.update({
                    "next_event": ev.event_data["next_event"].get(),
                    "next_event_delay": ev.event_data["next_event_delay"].get(),
                    "type_text": ev.event_data["type_text"].get(),
                    "entered_text": ev.event_data["entered_text"].get(),
                    "input_random_int": ev.event_data["input_random_int"].get(),
                    "press_enter": ev.event_data["press_enter"].get(),
                    "press_backspace": ev.event_data["press_backspace"].get(),
                    "random_position": ev.event_data["random_position"].get(),
                    "move_mouse_back": ev.event_data["move_mouse_back"].get(),
                    "double_click": ev.event_data["double_click"].get(),
                })
            elif isinstance(ev, EventLogic):
                d.update({
                    "next_event_success": ev.event_data["next_event_success"].get(),
                    "next_event_success_delay": ev.event_data["next_event_success_delay"].get(),
                    "logic_type": ev.event_data["logic_type"].get(),
                    "next_event_fail": ev.event_data["next_event_fail"].get(),
                    "next_event_fail_delay": ev.event_data["next_event_fail_delay"].get(),
                    "logic_action": ev.event_data["logic_action"].get(),
                    "logic_value": ev.event_data["logic_value"].get(),
                })
            current.append(d)
        names = [e["event_name"] for e in current]
        return ["None"] + names if names else ["None"]

    def create_new_event(self, event_type):
        event_name = simpledialog.askstring("New Item", "Enter the name of the new item:", parent=self.root)
        if event_name:
            if event_type == EVENT_BUTTON:
                self.place_event_button(event_name, reload_view=True)
            if event_type == EVENT_LOGIC:
                self.place_event_logic(event_name, reload_view=True)

    def place_event_logic(self, event_name, event_data=None, event_params=None, reload_view=False):
        event_params = {} if event_params is None else event_params
        logic_event = EventLogic(self.root,event_name,event_data=event_data,delete_callback=self.delete_event,**event_params)
        logic_event.lift()
        # Create Main Frame
        event_container = tk.Frame(self.box_label_frame, bd=2, relief="solid")
        event_container.pack(fill="x", padx=5, pady=5)
        header = tk.Frame(event_container)
        header.pack(fill="x", pady=2)
        logic_event.ui_frame = header
        logic_event.event_container = event_container
        tk.Label(header, text=event_name, anchor="w", padx=10, font=("Helvetica", 10, "bold")).pack(side="left")
        tk.Button(header, text="X", bg="red", fg="white", bd=0, command=lambda eb=logic_event: self.delete_event(eb)).pack(side="right", padx=(5, 0))
        tk.Button(header, text="−", bg="gray", fg="white", bd=0, command=lambda eb=logic_event: self.toggle_event_view(eb)).pack(side="right", padx=(5, 0))
        logic_event.minimize_btn = header.winfo_children()[-1]
        # Body (settings)
        body = tk.Frame(event_container)
        body.pack(fill="x", padx=5, pady=5)
        logic_event.settings_frame = body
        # ── Group 1: Event Settings ──
        es = tk.LabelFrame(body, text="Event Settings", padx=5, pady=5)
        es.pack(fill="x", pady=3)
        tk.Checkbutton(es, text="RunAtStart",variable=logic_event.event_data["run_at_start"], command=lambda eb=logic_event: eb.update_event("run_at_start",eb.event_data["run_at_start"].get())).pack(side="left", padx=5)
        tk.Checkbutton(es, text="Repeat",variable=logic_event.event_data["repeat"], command=lambda eb=logic_event: eb.update_event("repeat",eb.event_data["repeat"].get())).pack(side="left", padx=5)
        rd = tk.Entry(es, textvariable=logic_event.event_data["repeat_delay"],width=5, validate="key", validatecommand=self._vcmd)
        rd.pack(side="left", padx=5)
        rd.bind("<FocusOut>", lambda e, eb=logic_event: eb.update_event("repeat_delay", eb.event_data["repeat_delay"].get()))
        # ── Group 2: Next Event Settings ──
        ne = tk.LabelFrame(body, text="Next Event Settings", padx=5, pady=5)
        ne.pack(fill="x", pady=3)
        names = self.get_task_event_names()
        # Success path
        tk.Label(ne, text="Success:", fg="green").pack(side="left", padx=(0, 2))
        logic_event.next_event_success_menu = ttk.Combobox(ne,textvariable=logic_event.event_data["next_event_success"],values=names,state="readonly",width=10)
        logic_event.next_event_success_menu.pack(side="left", padx=(0, 5))
        logic_event.next_event_success_menu.current(names.index(logic_event.event_data["next_event_success"].get()))
        sd = tk.Entry(ne, textvariable=logic_event.event_data["next_event_success_delay"],width=4, validate="key", validatecommand=self._vcmd)
        sd.pack(side="left", padx=(0, 10))
        sd.bind("<FocusOut>", lambda e, eb=logic_event: eb.update_event("next_event_success_delay", eb.event_data["next_event_success_delay"].get()))
        # Failure path
        tk.Label(ne, text="Fail:", fg="red").pack(side="left", padx=(0, 2))
        logic_event.next_event_fail_menu = ttk.Combobox(ne,textvariable=logic_event.event_data["next_event_fail"],values=names,state="readonly",width=10)
        logic_event.next_event_fail_menu.pack(side="left", padx=(0,5))
        logic_event.next_event_fail_menu.current(names.index(logic_event.event_data["next_event_fail"].get()))
        fd = tk.Entry(ne, textvariable=logic_event.event_data["next_event_fail_delay"],width=4,validate="key",validatecommand=self._vcmd)
        fd.pack(side="left")
        fd.bind("<FocusOut>", lambda e, eb=logic_event: eb.update_event("next_event_fail_delay", eb.event_data["next_event_fail_delay"].get()))
        # ── Group 3: Actions ──
        af = tk.LabelFrame(body, text="Actions", padx=5, pady=5)
        af.pack(fill="x", pady=3)
        # Action type (text_logic / color_logic)
        action_menu = ttk.Combobox(af,textvariable=logic_event.event_data["logic_action"],values=["text_logic", "color_logic"],state="readonly",width=12)
        action_menu.pack(side="left", padx=(0, 8))
        # Logic operator
        tk.Label(af, text="Operator:").pack(side="left", padx=(0, 2))
        op_menu = ttk.Combobox(af,textvariable=logic_event.event_data["logic_type"],values=["=", ">", ">=", "<", "<=", "!=", "contains", "like"],state="readonly",width=8)
        op_menu.pack(side="left", padx=(0, 8))
        val_entry = tk.Entry(af, textvariable=logic_event.event_data["logic_value"], width=15)
        val_entry.pack(side="left", padx=5)
        self.event_boiler_plate(logic_event)
        mag.event_windows.append(logic_event)
        if reload_view:
            self.update_task_events()

    def place_event_button(self, event_name, event_data=None, event_params=None, reload_view=False):
        event_params = {} if event_params is None else event_params
        event_button = EventButton(self.root,event_name,event_data=event_data,delete_callback=self.delete_event,**event_params)
        # event_button = EventWindow(self.root, event_type=EVENT_BUTTON, event_name=event_name, event_data=event_data, delete_callback=self.delete_event, **event_params)
        event_button.lift()
        # Create Main Frame
        event_container = tk.Frame(self.box_label_frame, bd=2, relief="solid")
        event_container.pack(fill="x", padx=5, pady=5)
        # Create Header Frame
        label_frame = tk.Frame(event_container)
        event_button.ui_frame = label_frame
        event_button.event_container = event_container
        label_frame.pack(fill="x", pady=2)
        # Event Name
        label_text = tk.Label(label_frame, text=event_name, anchor="w", padx=10, font=("Helvetica", 10, "bold"))
        label_text.pack(side="left")
        # Delete and Minimize Buttons
        delete_btn = tk.Button(label_frame,text="X",command=lambda eb=event_button: self.delete_event(eb),anchor="e",bg="red",fg="white",bd=0,highlightthickness=0)
        delete_btn.pack(side="right", padx=(5, 0))
        minimize_btn = tk.Button(label_frame,text="−",command=lambda eb=event_button: self.toggle_event_view(eb),anchor="e",bg="gray",fg="white",bd=0,highlightthickness=0)
        minimize_btn.pack(side="right", padx=(5, 0))
        event_button.minimize_btn = minimize_btn
        # Create Body Frame
        settings_frame = tk.Frame(event_container)
        event_button.settings_frame = settings_frame
        settings_frame.pack(fill="x", padx=5, pady=5)
        # Group 1: Event Settings (RunAtStart, Repeat, Repeat Delay)
        event_settings_frame = tk.LabelFrame(settings_frame, text="Event Settings", padx=5, pady=5)
        event_settings_frame.pack(fill="x", padx=5, pady=3)
        run_at_start_checkbox = tk.Checkbutton(event_settings_frame,text="RunAtStart",variable=event_button.event_data["run_at_start"],command=lambda eb=event_button: eb.update_event('run_at_start', eb.event_data["run_at_start"].get()))
        run_at_start_checkbox.pack(side="left", padx=5)
        repeat_checkbox = tk.Checkbutton(event_settings_frame,text="Repeat",variable=event_button.event_data["repeat"],command=lambda eb=event_button: eb.update_event('repeat', eb.event_data["repeat"].get()))
        repeat_checkbox.pack(side="left", padx=5)
        repeat_delay = tk.Entry(event_settings_frame,textvariable=event_button.event_data["repeat_delay"],width=5,validate='key',validatecommand=self._vcmd)
        repeat_delay.pack(side="left", padx=5)
        repeat_delay.bind("<FocusOut>", lambda e, eb=event_button: eb.update_event('repeat_delay', eb.event_data["repeat_delay"].get()))
        # Group 2: Next Event Settings (Next Event and Delay)
        next_event_frame = tk.LabelFrame(settings_frame, text="Next Event Settings", padx=5, pady=5)
        next_event_frame.pack(fill="x", padx=5, pady=3)
        task_event_names = self.get_task_event_names()
        next_event_menu = ttk.Combobox(next_event_frame,textvariable=event_button.event_data["next_event"],values=task_event_names,state="readonly")
        next_event_menu.pack(side="left", padx=5)
        next_event_menu.current(task_event_names.index(event_button.event_data["next_event"].get()))
        event_button.next_event_menu = next_event_menu
        next_event_delay = tk.Entry(next_event_frame,textvariable=event_button.event_data["next_event_delay"],width=5,validate='key',validatecommand=self._vcmd)
        next_event_delay.pack(side="left", padx=5)
        next_event_delay.bind("<FocusOut>", lambda e, eb=event_button: eb.update_event('next_event_delay', eb.event_data["next_event_delay"].get()))
        # Group 3: Actions (Text and Mouse Actions)
        actions_frame = tk.LabelFrame(settings_frame, text="Actions", padx=5, pady=5)
        actions_frame.pack(fill="x", padx=5, pady=3)
        text_actions_frame = tk.Frame(actions_frame)
        text_actions_frame.pack(side="top", fill="x", pady=3)
        type_text_checkbox = tk.Checkbutton(text_actions_frame,text="Type Text",variable=event_button.event_data["type_text"],command=lambda eb=event_button: eb.update_event('type_text', eb.event_data["type_text"].get()))
        type_text_checkbox.pack(side="left", padx=5)
        text_entry = tk.Entry(text_actions_frame,textvariable=event_button.event_data["entered_text"],width=10)
        text_entry.pack(side="left", padx=5)
        input_random_int_checkbox = tk.Checkbutton(text_actions_frame, text="Random Int", variable=event_button.event_data["input_random_int"],command=lambda eb=event_button: eb.update_event('input_random_int', eb.event_data["input_random_int"].get()))
        input_random_int_checkbox.pack(side="left", padx=5)
        press_enter_checkbox = tk.Checkbutton(text_actions_frame,text="Press Enter",variable=event_button.event_data["press_enter"],command=lambda eb=event_button: eb.update_event('press_enter', eb.event_data["press_enter"].get()))
        press_enter_checkbox.pack(side="left", padx=5)
        press_backspace_checkbox = tk.Checkbutton(text_actions_frame,text="Press Backspace",variable=event_button.event_data["press_backspace"],command=lambda eb=event_button: eb.update_event('press_backspace', eb.event_data["press_backspace"].get()))
        press_backspace_checkbox.pack(side="left", padx=5)
        mouse_actions_frame = tk.Frame(actions_frame)
        mouse_actions_frame.pack(side="top", fill="x", pady=3)
        random_position_checkbox = tk.Checkbutton(mouse_actions_frame,text="Random Position",variable=event_button.event_data["random_position"],command=lambda eb=event_button: eb.update_event('random_position', eb.event_data["random_position"].get()))
        random_position_checkbox.pack(side="left", padx=5)
        move_mouse_back_checkbox = tk.Checkbutton(mouse_actions_frame,text="Move Mouse Back",variable=event_button.event_data["move_mouse_back"],command=lambda eb=event_button: eb.update_event('move_mouse_back', eb.event_data["move_mouse_back"].get()))
        move_mouse_back_checkbox.pack(side="left", padx=5)
        double_click_checkbox = tk.Checkbutton(mouse_actions_frame,text="Double Click",variable=event_button.event_data["double_click"],command=lambda eb=event_button: eb.update_event('double_click', eb.event_data["double_click"].get()))
        double_click_checkbox.pack(side="left", padx=5)
        self.event_boiler_plate(event_button)
        mag.event_windows.append(event_button)
        if reload_view:
            self.update_task_events()

    def toggle_event_view(self, event_button):
        settings_frame = event_button.settings_frame
        minimize_btn = event_button.minimize_btn
        event_container = event_button.event_container
        self.box_label_frame.update_idletasks()
        if settings_frame.winfo_ismapped():
            settings_frame.pack_forget()
            minimize_btn.config(text="+")
            event_container.pack(anchor="n", fill="x", pady=5)
        else:
            settings_frame.pack(fill="x", pady=5)
            minimize_btn.config(text="−")
            event_container.pack(anchor="n", fill="x", pady=5)

    def delete_event(self, event_object):
        if mag.task_running:
            return
        if event_object in mag.event_windows:
            mag.event_windows.remove(event_object)
        event_object.destroy()
        if hasattr(event_object, "event_container") and event_object.event_container:
            event_object.event_container.destroy()
        if hasattr(event_object, "event_name"):
            self.tasks[self.task_name] = [ev for ev in self.tasks[self.task_name]if ev.get("event_name") != event_object.event_name]

    def update_task_events(self):
        names = self.update_task_ui()
        for ev in mag.event_windows:
            if isinstance(ev, EventButton):
                ev.next_event_menu["values"] = names
                ev.next_event_menu.current(names.index(ev.event_data["next_event"].get()))
            elif isinstance(ev, EventLogic):
                ev.next_event_success_menu["values"] = names
                ev.next_event_success_menu.current(names.index(ev.event_data["next_event_success"].get()))
                ev.next_event_fail_menu["values"] = names
                ev.next_event_fail_menu.current(names.index(ev.event_data["next_event_fail"].get()))
            else:
                logger.error(f"Unknown event type in update_task_events: {ev}")

    def event_boiler_plate(self, event_obj):
        event_obj.bind("<Button-1>", event_obj.start_move)
        event_obj.bind("<B1-Motion>", event_obj.do_move)
        event_obj.bind("<ButtonRelease-1>", event_obj.stop_move)
        return event_obj

    def save_task(self):
        if not self.task_name:
            messagebox.showwarning("No Task Selected", "Please create or load a task before saving.")
            return
        events_to_save = []
        for ev in mag.event_windows:
            data = {"event_type": ev.event_type,"event_name": ev.event_name,"geometry": ev.geometry(),"run_at_start": ev.event_data["run_at_start"].get(),"repeat": ev.event_data["repeat"].get(),"repeat_delay": ev.event_data["repeat_delay"].get(),}
            if isinstance(ev, EventButton):
                data.update({
                    "next_event": ev.event_data["next_event"].get(),
                    "next_event_delay": ev.event_data["next_event_delay"].get(),
                    "type_text": ev.event_data["type_text"].get(),
                    "entered_text": ev.event_data["entered_text"].get(),
                    "input_random_int": ev.event_data["input_random_int"].get(),
                    "press_enter": ev.event_data["press_enter"].get(),
                    "press_backspace": ev.event_data["press_backspace"].get(),
                    "random_position": ev.event_data["random_position"].get(),
                    "move_mouse_back": ev.event_data["move_mouse_back"].get(),
                    "double_click": ev.event_data["double_click"].get(),
                })
            elif isinstance(ev, EventLogic):
                data.update({
                    "next_event_success": ev.event_data["next_event_success"].get(),
                    "next_event_success_delay": ev.event_data["next_event_success_delay"].get(),
                    "logic_type": ev.event_data["logic_type"].get(),
                    "next_event_fail": ev.event_data["next_event_fail"].get(),
                    "next_event_fail_delay": ev.event_data["next_event_fail_delay"].get(),
                    "logic_action": ev.event_data["logic_action"].get(),
                    "logic_value": ev.event_data["logic_value"].get(),
                })
            events_to_save.append(data)

        self.tasks[self.task_name] = events_to_save
        mau.save_json_file(mag.taskmanager_file, self.tasks)
        logger.debug(f"Task '{self.task_name}' saved.")

    def load_task(self):
        task_list = list(self.tasks.keys())
        if not task_list:
            messagebox.showerror("Error", "No tasks available to load.")
            return
        selected_item = self.ask_selection(task_list,title="Load Task",prompt="Choose a task to load:")
        if not selected_item:
            return
        self.task_name = selected_item
        self.clear_events()
        self.toggle_overlays(force_visible=True)
        self.label.config(text=f"Loaded: {self.task_name}")
        for event_item in self.get_task_events():
            geom = {"geometry": event_item.get("geometry", "200x200")}
            base_data = {"run_at_start": event_item["run_at_start"],"repeat": event_item["repeat"],"repeat_delay": event_item["repeat_delay"],}
            if event_item["event_type"] == EVENT_BUTTON:
                btn_data = {
                    **base_data,
                    "next_event": event_item["next_event"],
                    "next_event_delay": event_item["next_event_delay"],
                    "type_text": event_item["type_text"],
                    "entered_text": event_item["entered_text"],
                    "input_random_int": event_item["input_random_int"],
                    "press_enter": event_item["press_enter"],
                    "press_backspace": event_item["press_backspace"],
                    "random_position": event_item["random_position"],
                    "move_mouse_back": event_item["move_mouse_back"],
                    "double_click": event_item["double_click"],
                }
                self.place_event_button(event_name=event_item["event_name"],event_data=btn_data,event_params=geom)
            elif event_item["event_type"] == EVENT_LOGIC:
                logic_data = {
                    **base_data,
                    "next_event_success": event_item["next_event_success"],
                    "next_event_success_delay": event_item["next_event_success_delay"],
                    "logic_type": event_item["logic_type"],
                    "next_event_fail": event_item["next_event_fail"],
                    "next_event_fail_delay": event_item["next_event_fail_delay"],
                    "logic_action": event_item["logic_action"],
                    "logic_value": event_item["logic_value"],
                }
                self.place_event_logic(event_name=event_item["event_name"],event_data=logic_data,event_params=geom)
            else:
                logger.debug(f"Unknown event type: {event_item['event_type']}")
        logger.debug(f"Task '{self.task_name}' loaded.")
        self.update_task_events()

    def clear_events(self):
        for ev in mag.event_windows:
            ev.destroy()
        mag.event_windows.clear()
        for child in self.box_label_frame.winfo_children():
            child.destroy()

    def start_task(self):
        if not mag.task_running:
            mag.task_running = True
            self.toggle_overlays(force_hide=True)
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Status: Running")
            for window in mag.event_windows:
                run_at_start = window.event_data["run_at_start"].get()
                if run_at_start:
                    window.start_event()

    def stop_task(self):
        if mag.task_running:
            self.toggle_overlays(force_visible=True)
            mag.task_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Status: Idle")
            for window in mag.event_windows:
                window.stop_event()

    def ask_selection(self, options, title="Select", prompt="Please choose:") -> Optional[str]:
        from main_utils import ask_selection
        return ask_selection(self.root, options, title, prompt)

if __name__ == "__main__":
    try:
        if not os.path.exists('data'):
            os.makedirs('data')
        root = tk.Tk()
        task_manager = TaskManager(root)
        root.task_manager = task_manager
        root.mainloop()
    except Exception as e:
        application_error_handler(e)
