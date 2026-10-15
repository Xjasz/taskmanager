import os

taskmanager_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tm.json")
task_running = False
event_windows = []