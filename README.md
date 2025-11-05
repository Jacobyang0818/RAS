# Report Automation System 🚀

This application monitors selected data files and can generate reports either manually (**Once Now**) or automatically based on scheduled time settings.

## ✨ Features
- 📂 Monitor one or more files
- 🗑 Remove monitored files
- ⏱ Set scheduled report times (once or weekly)
- ⚡ Run report immediately
- 🔄 Optional background auto-run
- 🪟 System tray support

---

## ⚠ Notice

The included **`weasyprint.exe`** is used **only for converting HTML → PDF**.  
No Python `weasyprint` package and no system-level Cairo/Pango libraries are required.

---

## 🛠 Installation
Requires **Python 3.10+**.

### 1. Change your working directory to `RSA`
```bash
cd RSA
```

### 2. Install dependencies

#### Option A — Using **uv**
```bash
uv sync

# Create sample test data (optional):
uv run create_test_file.py

# Run the application:
uv run main.py
```

#### Option B — Using **pip**
```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install .

# Create sample test data (optional):
python create_test_file.py

# Run the application:
python main.py
```

---

## 🎯 Usage

### 1. Select Files
Click **Select File**, then choose the data files you want to monitor.

Example sample files in `files/`:
```
client.csv
sales_info.csv
sales.csv
```

### 2. (Optional) Remove Files
Click **Remove Files**, choose files, confirm deletion.

### 3. Set Report Schedule
Click **Setting Report Time** to configure:
- 🗓 Weekday(s)
- 🕒 Time (HH:mm)
- 🔁 Mode (once / weekly)

### 4. Run Reports
| Button | Description |
|--------|-------------|
| **Once Now** | Immediately generate report |
| **On Scheduling** | Toggle automatic scheduled reports |

### 5. 📄 Report Output

Generated files are stored in the `output/` folder:

| Type | Example | Notes |
|------|---------|-------|
| **HTML** | `output/report_2025-02-14.html` | Viewable in browser |
| **PDF** | `output/report_2025-02-14.pdf` | Ready to share or archive |

---

## 🪟 System Tray Behavior
Closing the window **minimizes to tray instead of exiting**.  
To exit completely: right‑click tray icon → **Exit**.

---

## 📁 File Structure
```
project/
  main.py
  create_test_file.py
  config/config.json
  files/
  src/remove.py
  assets/app.ico
```

---

## ⚙ Custom Logic
Edit this function to customize processing:
```python
def _run_task(self, file_path):
    pass
```

---

## 📊 Default Task Overview

This task automatically collects and analyzes sales-related data, then generates a visual report.

### Data Sources
- **sales** → Transaction history
- **sales_info** → Product details and categories
- **client** → Customer region and identity

These are merged on shared keys such as **client_id** and **product_code**.

### Visual Output
- 🥧 **Three pie charts** (distribution insights)
- 📈 **One line trend chart** (time-based sales)
- 📝 **Summary insights included in report**

### Final Report
✅ Charts  
✅ Key statistics  
Rendered and exported as **PDF**.
