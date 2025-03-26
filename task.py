# task.py

from datetime import datetime


class Task:
    def __init__(self, name, total_time=0):
        self.name = name
        self.total_time = total_time
        self.running = False
        self.start_time = None
        self.row_widget = None
        self.timer_label = None

    def start(self):
        """Start tracking time for the task."""
        if not self.running:
            self.start_time = datetime.now()
            self.running = True

    def pause(self):
        """Pause the task and update total time."""
        if self.running and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.total_time += elapsed
            self.running = False
            self.start_time = None

    def get_elapsed_time(self):
        """Return total tracked time (including current session if running)."""
        if self.running and self.start_time:
            return self.total_time + (datetime.now() - self.start_time).total_seconds()
        return self.total_time

    def set_manual_time(self, total_seconds):
        """Manually set the total time."""
        self.total_time = total_seconds

    def bind_ui(self, row_widget, timer_label):
        """Link UI elements to the task."""
        self.row_widget = row_widget
        self.timer_label = timer_label
