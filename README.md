# TimeLogTrackr
One more task tracker and time logger, built with Python and Tkinter. Easily manage and monitor your daily tasks, track durations, and save progress — all from a lightweight desktop app.

---

## Features
- Create and manage multiple tasks
- Start, pause and resume timers
- Persistent storage using SQLite
- Daily tracking with auto-saving
- Clean, responsive user interface

## Roadmap
Planned features for upcoming releases:
- [ ] Delete added tasks
- [ ] Filter tasks by date
- [ ] Edit Time on a certain task
- [ ] Auto-pause all running tasks after a set period of user inactivity
- [ ] Generate daily/weekly/monthly time reports/statistics
- [ ] Dark mode toggle
- [ ] Improved UI design (icons, layout polish)
- [ ] Export data
- [ ] Task recurrence or templates
- [ ] Build Windows/macOS/Linux installer with PyInstaller
- [ ] Run the app in the background with a tray icon and menu (pause/resume tasks, toggle idle detection, quick add, etc.)

## Project Structure
```text
timelogtrackr/
├── main.py          # Main GUI application
├── task.py          # Task object logic
├── db.py            # SQLite handling
├── tasks.db         # Auto-created local database
├── README.md
└── requirements.txt #to be added
```

## Database
TimeLogTrackr uses a lightweight local SQLite database (`tasks.db`) to persist all tasks and tracked time.
### Daily Logging Behavior
- Tasks are **saved per day** based on the current date (`YYYY-MM-DD`)
- Each task entry is unique per day — so if you reuse the same task name tomorrow, it creates a new daily entry
- All **timer progress is tracked and added** to that day’s entry
- You can pause/resume the timer as needed — all changes are immediately saved. One of the goals is to be able to edit the time

### Table Schema
| Column       | Type     | Description                                |
|--------------|----------|--------------------------------------------|
| `id`         | INTEGER  | Unique ID (primary key)                    |
| `name`       | TEXT     | Task name                                  |
| `start_time` | TEXT     | (Optional) Start timestamp                 |
| `end_time`   | TEXT     | (Optional) End timestamp                   |
| `total_time` | INTEGER  | Time tracked in seconds (auto-updated)     |
| `status`     | TEXT     | Task state (`paused`, etc.)                |
| `date`       | TEXT     | Date of entry in format `YYYY-MM-DD`       |

> Each day is a fresh start — but your task history is always stored.


## License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
> You are free to use, modify, distribute, and even commercialize this software — just make sure to keep the original license and credit.


## Contributing
Contributions are more than welcome!
If you have an idea for a feature, find a bug, or want to improve the UI — feel free to open an issue or submit a pull request.
### How to contribute:
1. Fork this repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request ✅

