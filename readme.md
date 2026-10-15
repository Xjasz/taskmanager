# Task Manager with Event Handling

This project is a task manager application that allows you to define and manage tasks through a GUI. It can automate interactions such as mouse clicks and keyboard actions based on user-defined events. The application is built using `Tkinter` for the GUI and includes features such as event creation, event chaining, task execution, and more.

## Features
- **Event Handling:** Create events such as mouse clicks or logic checks (text or color).
- **Task Management:** Create, save, and load tasks consisting of multiple events.
- **Event Execution:** Define whether an event should run at the start, repeat, or trigger other events based on conditions.
- **GUI Interface:** A clean and interactive Tkinter-based interface for managing events and tasks.

## Prerequisites

Make sure you have the following Python libraries installed:

```bash
pip install -r requirements.txt
```

Logic events that read screen text also need the Tesseract OCR program installed and on `PATH` (https://github.com/tesseract-ocr/tesseract).

Windows only: the user-activity checks call `ctypes.windll`.

## Run

```bash
python task_manager.py
```

## How a task works

- A task is a named list of events saved to `data/tm.json` next to the scripts.
- Each event is a see-through overlay box you place over a spot on the screen.
- A button event clicks inside its box and can type text, a random digit, Enter or Backspace, then optionally moves the mouse back.
- A logic event reads the text (OCR) or the colour inside its box and chains to a success or a fail event.
- Every event can run at start, repeat after a delay, and name the event that runs next.

## Limitations

- Events run on the GUI thread, so the window is unresponsive while an event executes and Stop takes effect between events.
- Moving the mouse into a screen corner triggers the pyautogui fail-safe and aborts the run.
