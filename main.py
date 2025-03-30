# main.py

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
from db import initialize_database, get_connection
from task import Task
from task import add_negative_time_button_handler
from reports import open_monthly_report_dialog
from pynput import mouse



class TaskTrackerApp:
    def __init__(self, root):
        """
        Initialize the TaskTrackerApp.

        Parameters:
        - root (tk.Tk): The main Tkinter window.

        Behavior:
        - Connects to the SQLite database.
        - Initializes UI components and idle monitoring.
        - Sets up task management and event handlers.
        """
        self.root = root
        self.root.title("Task Manager")
        self.tasks = {}
        self.task_names = set()

        self.conn = get_connection()
        self.cursor = self.conn.cursor()

        self.idle_timeout = 30 * 60  # 30 minutos em segundos
        self.idle_counter = 0
        self.idle_detection_enabled = tk.BooleanVar(value=True)    # Pode ser mais tarde configurável

        self.build_header()
        self.start_inactivity_monitor()

        self.task_list_frame = tk.Frame(self.root, bg="white")
        self.task_list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_header(self):
        """
        Build the top section of the UI (header).

        Behavior:
        - Adds buttons and labels for date, reports, idle settings.
        - Creates two lines of controls for task actions.
        """
        header = tk.Frame(self.root)
        header.pack(fill=tk.X, pady=10, padx=20)

        # === Linha 1 ===
        top_row = tk.Frame(header)
        top_row.pack(fill=tk.X)

        today_label = tk.Label(
            top_row,
            text=f"Today, {datetime.now().strftime('%B %d')}",
            font=("Arial", 16, "bold"),
        )
        today_label.pack(side=tk.LEFT)

        report_button = tk.Button(
            top_row,
            text="Monthly Report",
            bg="#83df0e",
            fg="white",
            font=("Arial", 10, "bold"),
            command=lambda: open_monthly_report_dialog(self.root, self.cursor, self.format_time)
        )
        report_button.pack(side=tk.LEFT, padx=10)

        idle_toggle = tk.Checkbutton(
            top_row,
            text="Idle Detection",
            variable=self.idle_detection_enabled,
            onvalue=True,
            offvalue=False,
            font=("Arial", 10),
            bg="#f5f5f5"
        )
        idle_toggle.pack(side=tk.LEFT, padx=10)

        idle_config_btn = tk.Button(
            top_row,
            text="Set Idle Time",
            font=("Arial", 10, "bold"),
            bg="#e7edf3",
            fg="#0e141b",
            command=self.set_idle_timeout
        )
        idle_config_btn.pack(side=tk.LEFT, padx=10)

        self.idle_timer_label = tk.Label(
            top_row,
            text=f"Idle pause in: {self.format_time(self.idle_timeout)}",
            font=("Arial", 10),
            fg="red"
        )
        self.idle_timer_label.pack(side=tk.RIGHT, padx=10)

        

        separator = tk.Frame(header, height=2, bd=0, bg="#d0d0d0", relief=tk.SUNKEN)
        separator.pack(fill=tk.X, pady=5)
        # === Linha 2 ===
        bottom_row = tk.Frame(header)
        bottom_row.pack(fill=tk.X, pady=(10, 0))



        add_button = tk.Button(
            bottom_row,
            text="Add Task",
            bg="#1980e6",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.add_task,
        )
        add_button.pack(side=tk.LEFT, padx=10)

        pause_all_button = tk.Button(
            bottom_row,
            text="Pause All",
            bg="#f33b14",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.pause_all,
        )
        pause_all_button.pack(side=tk.LEFT, padx=10)

        add_negative_btn = tk.Button(
            bottom_row,
            text="Add Negative Time",
            bg="#e0a000",
            fg="white",
            font=("Arial", 10, "bold"),
            command=lambda: add_negative_time_button_handler(self.root, self.cursor, self.tasks, self.format_time),
        )
        add_negative_btn.pack(side=tk.LEFT, padx=10)





    def add_task(self):
        """
        Open a modal to add a new task or select an existing one.

        Behavior:
        - Queries existing task names from DB.
        - Displays a dropdown and input field for user choice.
        - Calls confirm_task_handler after selection.
        """
        self.cursor.execute("SELECT DISTINCT name FROM tasks")
        existing_tasks = [row[0] for row in self.cursor.fetchall()]

        modal = tk.Toplevel(self.root)
        modal.title("Select or Add Task")
        modal.geometry("400x250")
        modal.config(bg="#f5f5f5")

        label = tk.Label(modal, text="Select a task or add a new one:", font=("Arial", 12, "bold"), pady=10)
        label.pack()

        dropdown_var = tk.StringVar()
        dropdown = ttk.Combobox(modal, textvariable=dropdown_var, values=existing_tasks, height=10, state="readonly", font=("Arial", 10))
        dropdown.pack(pady=5, padx=20, fill=tk.X)

        entry_label = tk.Label(modal, text="Or enter a new task name:", font=("Arial", 11), pady=5)
        entry_label.pack()

        task_entry = tk.Entry(modal, font=("Arial", 10), relief=tk.GROOVE, bd=2)
        task_entry.pack(pady=5, padx=20, fill=tk.X)

        confirm = tk.Button(
            modal,
            text="Confirm",
            font=("Arial", 11, "bold"),
            bg="#1980e6",
            fg="white",
            command=lambda: self.confirm_task_handler(dropdown_var, task_entry, modal),
        )
        confirm.pack(pady=15)

        for widget in modal.winfo_children():
            if isinstance(widget, (tk.Label, tk.Entry, tk.Button)):
                widget.config(bg="#f5f5f5")

        modal.transient(self.root)
        modal.grab_set()
        self.root.wait_window(modal)

    def confirm_task_handler(self, dropdown_var, task_entry, modal):
        """
        Handle task confirmation and initialization.

        Parameters:
        - dropdown_var: tk.StringVar from dropdown selection.
        - task_entry: Entry widget for new task name.
        - modal: Modal dialog window.

        Behavior:
        - Inserts task in DB if it's new.
        - Updates UI with task row and timer label.
        """
        task_name = dropdown_var.get() or task_entry.get()
        if not task_name:
            return

        self.task_names.add(task_name)
        today = datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute(
            "SELECT total_time FROM tasks WHERE name = ? AND date = ?",
            (task_name, today),
        )
        row = self.cursor.fetchone()

        if not row:
            self.cursor.execute("""
                INSERT INTO tasks (name, start_time, end_time, total_time, status, date)
                VALUES (?, NULL, NULL, 0, 'paused', ?)
            """, (task_name, today))
            self.conn.commit()
            total_time = 0
        else:
            total_time = row[0]

        timer_label = self.create_task_row(task_name)
        task = Task(name=task_name, total_time=total_time)
        task.bind_ui(row_widget=timer_label.master, timer_label=timer_label)
        self.tasks[task_name] = task
        timer_label.config(text=self.format_time(total_time))
        modal.destroy()

    def create_task_row(self, task_name):
        """
        Create a row in the UI for the given task.

        Parameters:
        - task_name (str): Name of the task.

        Returns:
        - tk.Label: Reference to the timer label.

        Behavior:
        - Adds icons, labels, and a start/pause button for the task.
        """
        row = tk.Frame(self.task_list_frame, bg="white")
        row.pack(fill=tk.X, pady=5)

        clock_icon = tk.Label(row, text="🕒", font=("Arial", 14), bg="#e7edf3", width=3)
        clock_icon.pack(side=tk.LEFT, padx=5)

        details = tk.Frame(row, bg="white")
        details.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        label = tk.Label(details, text=task_name, font=("Arial", 12, "bold"), bg="white")
        label.pack(anchor="w")

        timer = tk.Label(details, text="00:00:00", font=("Arial", 12, "bold"), fg="#4e7397", bg="white")
        timer.pack(anchor="w")
        timer.bind("<Button-1>", lambda e: self.edit_time(task_name, timer))

        button = tk.Button(
            row,
            text="Start",
            font=("Arial", 10, "bold"),
            bg="#1980e6",
            fg="white",
            command=lambda: self.toggle_task(task_name, timer, button),
        )
        button.pack(side=tk.RIGHT, padx=10)
        task = Task(name=task_name)
        task.bind_ui(row_widget=row, timer_label=timer)
        self.tasks[task_name] = task

        return timer

    def toggle_task(self, task_name, timer_label, action_button):
        """
        Toggle the task's state (start, pause, continue).

        Parameters:
        - task_name (str)
        - timer_label (tk.Label)
        - action_button (tk.Button)

        Behavior:
        - Switches between running/paused states.
        - Calls appropriate handler based on button label.
        """
        task = self.tasks[task_name]
        if action_button["text"] == "Start":
            self.start_task(task_name, timer_label, action_button)
        elif action_button["text"] == "Pause":
            self.pause_task(task_name, action_button)
        elif action_button["text"] == "Continue":
            self.start_task(task_name, timer_label, action_button)

    def start_task(self, task_name, timer_label, action_button):
        """
        Start or resume a task.

        Parameters:
        - task_name (str)
        - timer_label (tk.Label)
        - action_button (tk.Button)

        Behavior:
        - Starts internal timer and UI update.
        - Changes button label to 'Pause'.
        """
        task = self.tasks[task_name]
        if not task.running:
            task.start()
            action_button.config(text="Pause")
            self.update_timer(task_name, timer_label)

    def pause_task(self, task_name, action_button):
        """
        Pause the task.

        Parameters:
        - task_name (str)
        - action_button (tk.Button)

        Behavior:
        - Stops timer and updates time in DB.
        - Changes button to 'Continue'.
        """
        task = self.tasks[task_name]
        if task.running:
            task.pause()
            action_button.config(text="Continue")
            self.cursor.execute(
                "UPDATE tasks SET total_time = ? WHERE name = ?",
                (task.total_time, task.name),
            )
            self.conn.commit()

    def update_timer(self, task_name, timer_label):
        """
        Periodically update the task timer.

        Parameters:
        - task_name (str)
        - timer_label (tk.Label)

        Behavior:
        - Updates UI label and saves time to DB every second.
        """
        task = self.tasks[task_name]
        if task.running:
            total_time = task.get_elapsed_time()
            timer_label.config(text=self.format_time(total_time))
            today = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute(
                "UPDATE tasks SET total_time = ? WHERE name = ? AND date = ?",
                (total_time, task.name, today)
            )
            self.conn.commit()
            self.root.after(1000, lambda: self.update_timer(task_name, timer_label))

    def edit_time(self, task_name, timer_label):
        """
        Allow manual editing of a task's time.

        Parameters:
        - task_name (str)
        - timer_label (tk.Label)

        Behavior:
        - Opens input dialog for hh:mm:ss format.
        - Updates task time in UI and DB.
        """
        new_time = simpledialog.askstring("Edit Timer", "Enter the new time (hh:mm:ss):", parent=self.root)
        if not new_time:
            return
        try:
            h, m, s = map(int, new_time.split(":"))
            total = h * 3600 + m * 60 + s
            self.tasks[task_name].set_manual_time(total)
            timer_label.config(text=self.format_time(total))
            today = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("UPDATE tasks SET total_time = ? WHERE name = ? AND date = ?", (total, task_name, today))
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))

    def pause_all(self):
        """
        Pause all currently running tasks.

        Behavior:
        - Iterates through tasks and pauses those that are active.
        - Updates each task in DB.
        """
        for name, task in self.tasks.items():
            if task.running:
                action_button = task.row_widget.winfo_children()[-1]
                self.pause_task(name, action_button)

    def format_time(self, seconds):
        """
        Format time from seconds to hh:mm:ss.

        Parameters:
        - seconds (int or float): Total seconds to format.

        Returns:
        - str: Time formatted as hh:mm:ss.
        """
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"

    def on_closing(self):
        """
        Handle application shutdown.

        Behavior:
        - Closes DB connection.
        - Destroys Tkinter root window.
        """
        self.conn.close()
        self.root.destroy()


    # IDLE PAUSE METHODS
    def start_inactivity_monitor(self):
        """
        Start monitoring mouse activity for idle detection.

        Behavior:
        - Uses pynput to listen to mouse movements.
        - Starts a loop to check idle timeout.
        """
        self.mouse_listener = mouse.Listener(on_move=self.reset_idle_timer)
        self.mouse_listener.start()
        self.check_idle_loop()

    def reset_idle_timer(self, *args):
        """
        Reset idle counter when activity is detected.
        """
        self.idle_counter = 0

    def check_idle_loop(self):
        """
        Check if user is idle and pause all tasks if threshold exceeded.

        Behavior:
        - Updates idle timer label.
        - Triggers pause_all() if idle timeout is reached.
        """
        if self.idle_detection_enabled.get():
            self.idle_counter += 1
            time_remaining = max(0, self.idle_timeout - self.idle_counter)
            self.idle_timer_label.config(text=f"Idle pause in: {self.format_time(time_remaining)}")

            if self.idle_counter >= self.idle_timeout:
                self.pause_all()
                self.idle_counter = 0
                messagebox.showinfo("Idle", "All tasks have been paused due to inactivity.")
        else:
            self.idle_timer_label.config(text="Idle detection off")

        self.root.after(1000, self.check_idle_loop)



    def set_idle_timeout(self):
        """
        Prompt user to configure idle timeout duration.

        Behavior:
        - Opens input dialog and updates timeout in seconds.
        """
        user_input = simpledialog.askstring("Idle Timeout", "Set idle timeout in minutes:", parent=self.root)
        if not user_input:
            return
        try:
            minutes = int(user_input)
            self.idle_timeout = minutes * 60
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a valid number.")

    


if __name__ == "__main__":
    initialize_database()
    root = tk.Tk()
    app = TaskTrackerApp(root)
    root.mainloop()
