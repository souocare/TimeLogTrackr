from tkinter import Toplevel, messagebox, Label, Button, StringVar, ttk
import tkinter as tk
import os
import random
import string
from openpyxl import Workbook


def open_monthly_report_dialog(root, cursor, format_time_callback):
    """
    Open a dialog to select the month and year for which to generate a report.

    Parameters:
    - root (tk.Tk): The main application window.
    - cursor (sqlite3.Cursor): Cursor to execute SQL queries.
    - format_time (function): Function to convert seconds to hh:mm:ss string.
    """
    report_window = Toplevel(root)
    report_window.title("Generate Monthly Report")
    report_window.geometry("300x200")
    report_window.grab_set()

    Label(report_window, text="Select Month:", font=("Arial", 11)).pack(pady=5)
    month_var = StringVar()
    month_combo = ttk.Combobox(report_window, textvariable=month_var, state="readonly")
    month_combo["values"] = [f"{i:02}" for i in range(1, 13)]
    month_combo.pack(pady=5)

    Label(report_window, text="Select Year:", font=("Arial", 11)).pack(pady=5)
    year_var = StringVar()
    year_combo = ttk.Combobox(report_window, textvariable=year_var, state="readonly")

    # Extract distinct years from DB
    cursor.execute("SELECT DISTINCT date FROM tasks")
    years = sorted({row[0][:4] for row in cursor.fetchall()})
    year_combo["values"] = years
    year_combo.pack(pady=5)

    Button(
        report_window,
        text="Generate Report",
        bg="#1980e6",
        fg="white",
        font=("Arial", 10, "bold"),
        command=lambda: generate_monthly_report(
            month_var.get(),
            year_var.get(),
            report_window,
            cursor,
            format_time_callback,
            root
        )
    ).pack(pady=15)


def generate_monthly_report(month, year, window, cursor, format_time, root):
    """
    Generates a monthly report for a given month and year, saves it to an Excel file,
    and displays the results in a popup.

    Parameters:
    - month (str): Month in MM format (e.g., '01' for January).
    - year (str): Year in YYYY format.
    - window (tk.Toplevel): The modal window to destroy after generating.
    - cursor (sqlite3.Cursor): Cursor to access the task data from the database.
    - format_time (function): Function to convert seconds to hh:mm:ss string.
    - root (tk.Tk): The main application root to use as parent for messagebox.
    """
    if not month or not year:
        messagebox.showerror("Missing Fields", "Please select both month and year.")
        return

    cursor.execute("""
        SELECT name, SUM(total_time) 
        FROM tasks 
        WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
        GROUP BY name
    """, (month, year))
    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo("No Data", "No tasks found for the selected month.")
        return

    total_time = sum(row[1] for row in rows)
    if total_time == 0:
        messagebox.showinfo("No Time", "No time tracked for the selected month.")
        return

    # === 1. Generate unique filename ===
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    filename = f"report_{year}_{month}_{rand_str}.xlsx"

    # === 2. Create 'reports' folder if it doesn't exist ===
    report_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(report_dir, exist_ok=True)

    file_path = os.path.join(report_dir, filename)

    # === 3. Save Excel report ===
    wb = Workbook()
    ws = wb.active
    ws.title = f"{year}-{month} Report"
    ws.append(["Task Name", "Total Time", "Percentage"])

    for name, time in rows:
        percent = (time / total_time) * 100
        ws.append([name, format_time(time), f"{percent:.1f}"])

    wb.save(file_path)

    # === 4. Build table text ===
    table_text = f"Monthly Report for {year}-{month}\n\n"
    table_text += f"Time format: hh:mm:ss\n\n"
    table_text += f"{'Task':<20} {'Time':<10} {'%':<5}\n"
    table_text += "-" * 40 + "\n"

    for name, time in rows:
        percent = (time / total_time) * 100
        table_text += f"{name:<20} {format_time(time):<10} {percent:.1f}%\n"

    table_text += f"\nReport saved to:\n{file_path}"

    # === 5. Show report in copyable popup ===
    window.destroy()

    report_window = Toplevel(root)
    report_window.title("Monthly Report")
    report_window.geometry("500x400")
    report_window.grab_set()

    text_widget = tk.Text(report_window, wrap="none", font=("Courier New", 10))
    text_widget.insert("1.0", table_text)
    text_widget.config(state="disabled")
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def copy_report():
        root.clipboard_clear()
        root.clipboard_append(table_text)
        root.update()

    copy_button = tk.Button(
        report_window,
        text="Copy Report to Clipboard",
        font=("Arial", 10, "bold"),
        bg="#1980e6",
        fg="white",
        command=copy_report
    )
    copy_button.pack(pady=10)
