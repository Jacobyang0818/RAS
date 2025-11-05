# Report Automation System

This application monitors selected data files and can generate reports either manually ("Once Now") or automatically based on scheduled time settings.

## Features
- Monitor one or more files
- Remove monitored files
- Set scheduled report times (once or weekly)
- Run report immediately
- Optional background auto-run
- System tray support


## ⚠ Notice

The `weasyprint.exe` included in this project is used **only for converting HTML → PDF**.  
No Python `weasyprint` package is required and no system-level Cairo/Pango libraries need to be installed.


## Installation
Requires Python 3.10+.

Install dependencies:
```
uv sync
```

Create sample test data (optional):
```
uv run create_test_file.py
```

Run the application:
```
uv run main.py
```


## Usage

### 1. Select Files
Click `Select File`, then choose the data files you want to monitor.

Sample files (in `files/` folder):
```
client.csv
sales_info.csv
sales.csv
```

### 2. (Optional) Remove Files
Click `Remove Files`, select files to remove, and confirm.

### 3. Set Report Time
Click `Setting Report Time` to configure:
- Weekday(s)
- Time (HH:mm)
- Execution mode (once / weekly)

### 4. Run Reports
| Button | Action |
|-------|--------|
| **Once Now** | Immediately run the report on monitored files |
| **On Scheduling** | Toggle scheduled automatic execution |

Scheduling ON → system checks and runs when time matches  
Scheduling OFF → no automatic execution

### 5. Report Output

After the report is executed, the generated files will be stored in the `output/` directory.

| Format | File Name Pattern | Description |
|--------|------------------|-------------|
| **HTML** | `output/report_{timestamp}.html` | Viewable directly in any web browser |
| **PDF** | `output/report_{timestamp}.pdf` | Suitable for sharing, archiving, or printing |

**File Name Parameters:**

- `{timestamp}` — Execution time in the format `YYYY-MM-DD`

**Examples:**
```
output/report_2025-02-14.html
output/report_2025-02-14.pdf
```

## System Tray Behavior
Closing the window hides the app to tray instead of exiting.  
To exit completely: right-click tray icon → Exit.

## File Structure
```
project/
  main.py
  create_test_file.py
  config/config.json
  files/
  src/remove.py
  assets/app.ico
```

## Custom Logic
Edit this function in `main.py` to define how each file is processed:
```python
def _run_task(self, file_path):
    pass
```

## License
MIT
