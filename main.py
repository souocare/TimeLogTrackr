# main.py

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
from db import initialize_database, get_connection
from task import Task


class TaskTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.tasks = {}
        self.task_names = set()

        self.conn = get_connection()
        self.cursor = self.conn.cursor()

        self.build_header()
        self.task_list_frame = tk.Frame(self.root, bg="white")
        self.task_list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_header(self):
        header = tk.Frame(self.root)
        header.pack(fill=tk.X, pady=10, padx=20)

        today_label = tk.Label(
            header,
            text=f"Today, {datetime.now().strftime('%B %d')}",
            font=("Arial", 16, "bold"),
        )
        today_label.pack(side=tk.LEFT)

        add_button = tk.Button(
            header,
            text="Add Task",
            bg="#1980e6",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.add_task,
        )
        add_button.pack(side=tk.LEFT, padx=20)

        pause_all_button = tk.Button(
            header,
            text="Pause All",
            bg="#e7edf3",
            fg="#0e141b",
            font=("Arial", 10, "bold"),
            command=self.pause_all,
        )
        pause_all_button.pack(side=tk.RIGHT)

    def add_task(self):
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
        task = self.tasks[task_name]
        if action_button["text"] == "Start":
            self.start_task(task_name, timer_label, action_button)
        elif action_button["text"] == "Pause":
            self.pause_task(task_name, action_button)
        elif action_button["text"] == "Continue":
            self.start_task(task_name, timer_label, action_button)

    def start_task(self, task_name, timer_label, action_button):
        task = self.tasks[task_name]
        if not task.running:
            task.start()
            action_button.config(text="Pause")
            self.update_timer(task_name, timer_label)

    def pause_task(self, task_name, action_button):
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
        for name, task in self.tasks.items():
            if task.running:
                action_button = task.row_widget.winfo_children()[-1]
                self.pause_task(name, action_button)

    def format_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"

    def on_closing(self):
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    initialize_database()
    root = tk.Tk()
    app = TaskTrackerApp(root)
    root.mainloop()
