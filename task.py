
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

class Task:
    def __init__(self, name, total_time=0):
        """
        Initialize a Task instance.

        Parameters:
        - name (str): Name of the task.
        - total_time (float): Total accumulated time in seconds (default is 0).
        """
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
        """
        Manually set the total time of the task.

        Parameters:
        - total_seconds (float): Total time to be set in seconds.
        """
        self.total_time = total_seconds

    def bind_ui(self, row_widget, timer_label):
        """
        Bind the UI components to the task for future updates.

        Parameters:
        - row_widget (tk.Frame): The row/frame widget containing the task's UI.
        - timer_label (tk.Label): The label showing the task's time.
        """
        self.row_widget = row_widget
        self.timer_label = timer_label

# NEGATIVE TIME FUNCTION
def add_negative_time_button_handler(root, cursor, tasks, format_time):
    """
    Opens a modal window allowing the user to subtract time from a task.

    Parameters:
    - root (tk.Tk): Main application root window.
    - cursor (sqlite3.Cursor): Database cursor to execute SQL queries.
    - tasks (dict): Dictionary of currently loaded Task instances.
    - format_time (function): Function to format seconds into hh:mm:ss.
    """
    cursor.execute("SELECT DISTINCT name FROM tasks")
    task_names = [row[0] for row in cursor.fetchall()]

    if not task_names:
        messagebox.showinfo("No Tasks", "No tasks found in the database.", parent=root)
        return

    modal = tk.Toplevel(root)
    modal.title("Add Negative Time")
    modal.geometry("400x360")
    modal.grab_set()
    modal.config(bg="#f5f5f5")

    # Task dropdown
    tk.Label(modal, text="Select Task:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(15, 5))
    selected_task = tk.StringVar()
    dropdown = ttk.Combobox(modal, textvariable=selected_task, values=task_names, state="readonly", font=("Arial", 10))
    dropdown.pack(pady=5, padx=30, fill=tk.X)

    # Time input (hh:mm:ss)
    tk.Label(modal, text="Time to subtract:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(15, 0))

    label_frame = tk.Frame(modal, bg="#f5f5f5")
    label_frame.pack()
    tk.Label(label_frame, text="Hours", font=("Arial", 9), bg="#f5f5f5").pack(side=tk.LEFT, padx=10)
    tk.Label(label_frame, text="Minutes", font=("Arial", 9), bg="#f5f5f5").pack(side=tk.LEFT, padx=10)
    tk.Label(label_frame, text="Seconds", font=("Arial", 9), bg="#f5f5f5").pack(side=tk.LEFT, padx=10)

    time_frame = tk.Frame(modal, bg="#f5f5f5")
    time_frame.pack(pady=5)

    hour_var = tk.StringVar(value="00")
    minute_var = tk.StringVar(value="00")
    second_var = tk.StringVar(value="00")

    tk.Spinbox(time_frame, from_=0, to=23, textvariable=hour_var, width=4, format="%02.0f").pack(side=tk.LEFT, padx=14)
    tk.Spinbox(time_frame, from_=0, to=59, textvariable=minute_var, width=4, format="%02.0f").pack(side=tk.LEFT, padx=14)
    tk.Spinbox(time_frame, from_=0, to=59, textvariable=second_var, width=4, format="%02.0f").pack(side=tk.LEFT, padx=14)

    # Date input with calendar
    tk.Label(modal, text="Date to apply correction:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(15, 5))
    date_entry = DateEntry(modal, date_pattern="yyyy-mm-dd", font=("Arial", 10), background='darkblue', foreground='white', borderwidth=2)
    date_entry.pack(pady=5, padx=30, fill=tk.X)

    # Submit button
    def submit_negative_time():
        """
        Submits the negative time correction to the database.
        Subtracts time from the selected task and optionally updates the UI.
        """
        task_name = selected_task.get()
        if not task_name:
            messagebox.showwarning("Missing Fields", "Please select a task.", parent=modal)
            return

        try:
            seconds_to_remove = int(hour_var.get()) * 3600 + int(minute_var.get()) * 60 + int(second_var.get())
            date_input = date_entry.get_date().strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO tasks (name, start_time, end_time, total_time, status, date)
                VALUES (?, NULL, NULL, ?, 'correction', ?)
            """, (task_name, -seconds_to_remove, date_input))
            cursor.connection.commit()

            # Update label if task is loaded and correction is for today
            today = datetime.now().strftime("%Y-%m-%d")
            if date_input == today and task_name in tasks:
                cursor.execute("SELECT SUM(total_time) FROM tasks WHERE name = ? AND date = ?", (task_name, today))
                total = cursor.fetchone()[0] or 0
                tasks[task_name].set_manual_time(total)
                tasks[task_name].timer_label.config(text=format_time(total))

            messagebox.showinfo("Correction Added", f"Removed {format_time(seconds_to_remove)} from '{task_name}' on {date_input}.", parent=modal)
            modal.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Invalid input or error: {str(e)}", parent=modal)

    confirm_btn = tk.Button(
        modal,
        text="Submit",
        bg="#1980e6",
        fg="white",
        font=("Arial", 10, "bold"),
        command=submit_negative_time
    )
    confirm_btn.pack(pady=20)
