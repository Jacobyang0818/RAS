import os, sys, json, signal, ctypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                               QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QDialog, QListWidget,
                               QSystemTrayIcon, QMenu, QFileDialog, QDateTimeEdit, QComboBox, QDialogButtonBox, QListWidgetItem, QCheckBox, QTimeEdit, QRadioButton)
from PySide6.QtCore import Qt, QEvent, QDateTime, QTime, QDate, QTimer, QProcess
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from src.remove import MonitoredFilePicker
from datetime import datetime

WEEKDAYS = ["一","二","三","四","五","六","日"]  # 1..7

class ReportAutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 設定主視窗與工具列圖示
        icon_path = Path(__file__).resolve().parent / "assets" / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            print("⚠️ 找不到圖示:", icon_path)

        self.setWindowTitle("Report Automation System v1.0")
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

        # 關鍵：視窗關閉不結束程式
        QApplication.instance().setQuitOnLastWindowClosed(False)

        # 系統匣
        self.tray = None
        self._shown_tray_tip = False
        self.setup_tray()

        self.scheduler_on = False
        self.scheduler_timer = None
        self._fired_keys = set()   # 防止同分鐘重複觸發

        self.monitored_set = set()
        # self.schedules = {}
        
        self.config_path = 'config/config.json'
        self.config = {
            'monitored_files'      : [],
            'schedules'            : {},  
        }
        
        self.proc = None

        self.read_config()
        self.schedules = self.config.get("schedules", [])

    def setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            # 沒系統匣就維持預設行為
            return

        self.tray = QSystemTrayIcon(self)
        # 換成你的圖示路徑
        self.tray.setIcon(QIcon("assets/app.ico"))
        self.tray.setToolTip("Report Automation System")

        menu = QMenu()
        act_show = menu.addAction("Show")
        act_show.triggered.connect(self.restore_from_tray)
        act_exit = menu.addAction("Exit")
        act_exit.triggered.connect(QApplication.instance().quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        # 雙擊或單擊圖示時還原
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_from_tray()

    def restore_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    # 攔截打叉：不結束，改為隱藏到右下角
    def closeEvent(self, event):
        if self.tray and self.tray.isVisible():
            event.ignore()
            self.hide()
            if not self._shown_tray_tip:
                self.tray.showMessage(
                    "仍在執行",
                    "程式已縮到系統匣。右鍵圖示選 Exit 才會結束。",
                    QSystemTrayIcon.Information,
                    3000
                )
                self._shown_tray_tip = True
        else:
            # 沒有系統匣可用，就照常關閉
            event.accept()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(layout)
        
        title = QLabel("Report Automation System")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(title)
        
        self.status_label = QLabel("Ready - Choose Action")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        
        # Bottens
        btn1 = QPushButton("Select File")
        btn1.clicked.connect(self.select_file)
        btn1.setStyleSheet("QPushButton {background-color: #0052CC; color: white; font-size: 14px; padding: 10px; border-radius: 5px;}")
        button_layout.addWidget(btn1)
        
        btn4 = QPushButton("Remove Files")
        btn4.clicked.connect(self.remove_files_from_monited_file)
        btn4.setStyleSheet("QPushButton {background-color: #36B37E; color: white; font-size: 14px; padding: 10px; border-radius: 5px;}")
        button_layout.addWidget(btn4)

        btn5 = QPushButton("Setting Report Time")
        btn5.clicked.connect(self.setting_report_time)
        btn5.setStyleSheet("QPushButton {background-color: #FF5630; color: white; font-size: 14px; padding: 10px; border-radius: 5px;}")
        button_layout.addWidget(btn5)
        
        # Generate Report
        btn2 = QPushButton("Once Now")
        btn2.clicked.connect(self.once_now) # 使用import的方式管理
        btn2.setStyleSheet("QPushButton {background-color: #FFAB00; color: white; font-size: 14px; padding: 10px; border-radius: 5px;}")
        button_layout.addWidget(btn2)
        
        # On Scheduling
        # btn3 = QPushButton("On Scheduling")
        # btn3.clicked.connect(self.on_scheduling) # 持續監聽時間，當時間到達時，立即發送。 這是一個開關 可以On OFF。
        # btn3.setStyleSheet("QPushButton {background-color: #FF9800; color: white; font-size: 14px; padding: 10px; border-radius: 5px;}")
        # button_layout.addWidget(btn3)

        self.btn3 = QPushButton("On Scheduling")
        self.btn3.clicked.connect(self.on_scheduling)
        self.btn3.setStyleSheet("QPushButton {background-color: #6554C0; color: white; font-size: 14px; padding: 10px; border-radius: 5px;}")
        button_layout.addWidget(self.btn3)

        layout.addLayout(button_layout)

        # Monitered Files List
        monitored_label = QLabel("Monitored Files:")
        monitored_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(monitored_label)

        self.monitored_list_widget = QListWidget()
        self.monitored_list_widget.setFont(QFont("Consolas", 10))
        self.monitored_list_widget.setMaximumHeight(180)
        layout.addWidget(self.monitored_list_widget)

        # Log Block
        result_label = QLabel("Operation Result:")
        result_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(200)
        self.result_text.setPlaceholderText("Operation results will appear here...")
        self.result_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.result_text)

    def write_config(self):
        self.config['monitored_files'] = sorted(self.monitored_set)

        def sort_key(s):
            if s.get('mode') == 'once':
                return (0, s.get('datetime', ''))
            return (1, tuple(sorted(s.get('weekdays', []))), s.get('time', ''))

        self.config['schedules'] = sorted(self.schedules, key=sort_key)

        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.result_text.append(f"💾 已儲存設定到 {self.config_path}")
        except Exception as e:
            self.result_text.append(f"❌ 儲存設定失敗: {e}")

    # 原始
    # def write_config(self):
    #     self.config['monitored_files'] = sorted(self.monitored_set)
    #     self.config['schedules'] = sorted(
    #         self.schedules,
    #         key=lambda s: (
    #             0 if s['mode'] == 'once' else 1,  # 單次在前
    #             s.get('datetime', ''),            # 單次以 datetime 排
    #             s.get('time', '')                 # weekly 以 time 排
    #         )
    #     )

    #     try:
    #         os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    #         with open(self.config_path, "w", encoding="utf-8") as f:
    #             json.dump(self.config, f, ensure_ascii=False, indent=4)
    #         self.result_text.append(f"💾 已儲存設定到 {self.config_path}")

    #     except Exception as e:
    #         self.result_text.append(f"❌ 儲存設定失敗: {e}")

    def read_config(self):
        """讀取設定檔並載入 monitored_files"""

        if not os.path.exists(self.config_path):
            # 若沒有設定檔就初始化一個空的 config
            self.result_text.append("📄 不存在已知設定檔。")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            # 載入監控清單
            files = self.config.get("monitored_files", [])
            self.monitored_set = set(files)

            self.schedules = self.config.get("schedules", {})
            
            self.result_text.append(f"📂 已載入設定，共 {len(files)} 個監控檔案。")
            self.result_text.append(f"📅 已載入，共 {len(self.schedules)}個排程時刻。")
            # 若 UI 有清單區塊則同步刷新
            if hasattr(self, "update_monitored_view"):
                self.update_monitored_view()

        except Exception as e:
            self.config = {"monitored_files": []}
            self.monitored_set = set()
            self.result_text.append(f"⚠️ 讀取設定失敗: {e}")

    # Refresh the monitored files list
    def update_monitored_view(self):
        """刷新顯示目前被監控的檔案清單"""
        self.monitored_list_widget.clear()
        for f in sorted(self.monitored_set):
            self.monitored_list_widget.addItem(f)
        
        # 寫入state.json
        self.write_config()
        
        self.status_label.setText(f"✅ {len(self.monitored_set)} files monitored")
    
    # Select    
    def select_file(self):

        self.status_label.setText("Selecting files...")

        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "選擇多個Excel檔案", 
            "C:/Users/ADMIN/Desktop",  # 預設Desktop
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if files:  # files是LIST！
            self.result_text.append(f"✅ 選擇了 {len(files)} 個檔案：")
            # for i, file in enumerate(files, 1):
            #     self.result_text.append(f"  {i}. {file}")

            # 需確認選取的檔案不存在於已監控的清單中
            msgs = []
            for i, f in enumerate(files, 1):
                if f in self.monitored_set:
                    status = "Already in monitored list."
                else:
                    self.monitored_set.add(f)
                    status = "Selected."
                # i 佔 3 位右對齊，f 限 50 字符（多則截斷）
                msgs.append(f"{i:03}: {f:<100} | {status}")

            # 一次性寫入訊息，避免多次重繪
            self.result_text.append("\n".join(msgs))
            self.update_monitored_view()

        else:
            self.result_text.append("❌ 未選擇檔案")
            self.status_label.setText("Ready - Choose Action")

    # Remove
    def remove_files_from_monited_file(self):
        if not self.monitored_set:
            self.result_text.append("ℹ️ 目前沒有被監控的檔案。")
            self.status_label.setText("Ready - Choose Action")
            return

        dialog = MonitoredFilePicker(self.monitored_set, parent=self)
        if dialog.exec() != QDialog.Accepted:
            self.result_text.append("❎ 已取消移除。")
            self.update_monitored_view()
            return

        to_remove = dialog.selected_files()
        if not to_remove:
            self.result_text.append("ℹ️ 未選取任何檔案。")
            self.update_monitored_view()
            return

        self.result_text.append(f"🗑️ 申請移除 {len(to_remove)} 個檔案：")
        msgs = []
        removed = 0
        for i, f in enumerate(to_remove, 1):
            if f in self.monitored_set:
                self.monitored_set.remove(f)
                removed += 1
                status = "Removed."
            else:
                status = "Not in monitored list."
            msgs.append(f"{i:03}: {f:<100} | {status}")

        self.result_text.append("\n".join(msgs))
        self.status_label.setText(f"✅ {len(self.monitored_set)} files monitored | {removed} removed")
        self.update_monitored_view()
    
    # Scheduling 
    def _next_date_for_weekday(self, target_wd: int, base: QDate) -> QDate:
        # target_wd: 1=Mon ... 7=Sun ; QDate.dayOfWeek(): 1..7
        diff = (target_wd - base.dayOfWeek()) % 7
        if diff == 0:
            # 今天還沒過這個時間才算今天，交由上層決定；這裡回今天
            return base
        return base.addDays(diff)

    def _save_report_schedules(self, out):
        
        # remove duplicate
        seen = set()
        result = []
        for s in out:
            if s["mode"] == "once":
                key = ("once", s.get("datetime"))
            else:  # weekly
                # weekdays 排序避免 [2,3] 與 [3,2] 被視為不同
                key = ("weekly", tuple(sorted(s.get("weekdays", []))), s.get("time"))

            if key not in seen:
                print(key)
                seen.add(key)
                result.append(s)

        # sort
        def sort_key(s):
            if s.get("mode") == "once":
                # 若 datetime 為 None，用空字串以免比較錯
                return (0, s.get("datetime") or "")
            # weekly
            return (1, tuple(sorted(s.get("weekdays", []))), s.get("time") or "")

        result.sort(key=sort_key)

        self.schedules = result

        self.write_config()
            
    def setting_report_time(self):

        # format output
        def fmt_item(s):
            wd_txt = "、".join(f"週{WEEKDAYS[w-1]}" for w in s["weekdays"])
            mode_txt = "單次" if s["mode"] == "once" else "每週"
            return f"{wd_txt} @ {s['time'].toString('HH:mm')} 〔{mode_txt}〕"

        def add_schedule():
            sel_wds = [cb.property("weekday") for cb in day_checks if cb.isChecked()]

            if not sel_wds:
                return
            
            s = {
                "weekdays": sel_wds,                 # list[int] 1..7
                "time": time_edit.time(),            # QTime
                "mode": "once" if r_once.isChecked() else "weekly"
            }

            # 單次：計算下一個執行日期（每個 weekday 各一筆），展平成多列顯示
            if s["mode"] == "once":
                base_date = QDate.currentDate()
                now_time = QTime.currentTime()
                for w in sel_wds:
                    d = self._next_date_for_weekday(w, base_date)
                    # 若今天且時間已過，推到下一週
                    if d == base_date and now_time > s["time"]:
                        d = d.addDays(7)
                    s_one = {
                        "weekdays": [w],
                        "time": s["time"],
                        "mode": "once",
                        "next_run": QDateTime(d, s["time"])
                    }
                    schedules.append(s_one)
                    QListWidgetItem(f"單次：{fmt_item(s_one)} → {s_one['next_run'].toString('yyyy-MM-dd HH:mm')}", lst)
            else:
                # 每週：單筆可含多個 weekday
                schedules.append(s)
                QListWidgetItem(fmt_item(s), lst)

        def del_selected():
            rows = sorted([lst.row(i) for i in lst.selectedItems()], reverse=True)
            for r in rows:
                lst.takeItem(r)
                schedules.pop(r)

        dlg = QDialog(self)
        dlg.setWindowTitle("設定排程")
        root = QVBoxLayout(dlg)

        # 週期區
        week_row = QHBoxLayout()
        week_row.addWidget(QLabel("星期："))
        day_checks = []
        for i, name in enumerate(WEEKDAYS, start=1):
            cb = QCheckBox(name)
            cb.setProperty("weekday", i)
            day_checks.append(cb)
            week_row.addWidget(cb)

        # 時間與模式
        line2 = QHBoxLayout()
        line2.addWidget(QLabel("時間："))
        time_edit = QTimeEdit(QTime.currentTime())
        time_edit.setDisplayFormat("HH:mm")
        line2.addWidget(time_edit)

        mode_row = QHBoxLayout()
        r_once = QRadioButton("單次")
        r_weekly = QRadioButton("每次（每週）")
        r_weekly.setChecked(True)
        mode_row.addWidget(QLabel("模式："))
        mode_row.addWidget(r_once)
        mode_row.addWidget(r_weekly)

        # 清單 + 新增/刪除
        lst = QListWidget()
        btn_row = QHBoxLayout()
        btn_add = QPushButton("新增")
        btn_del = QPushButton("刪除所選")
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)

        # 內部狀態：每筆為 dict
        schedules = []

        # Init from schedules
        if hasattr(self, 'schedules'):
            for s in self.schedules:
                if s["mode"] == "weekly":
                    # time: "HH:mm" -> QTime
                    t = s["time"]
                    if isinstance(t, str):
                        t = QTime.fromString(t, "HH:mm")
                    s_row = {"weekdays": s["weekdays"], "time": t, "mode": "weekly"}
                    schedules.append(s_row)
                    QListWidgetItem(fmt_item(s_row), lst)

                else:  # once：config 內是單筆 datetime 字串，UI 需要展平成一列且有 next_run
                    dt = s.get("datetime")
                    if isinstance(dt, str):
                        qdt = QDateTime.fromString(dt, "yyyy-MM-dd HH:mm")
                    elif isinstance(dt, QDateTime):
                        qdt = dt
                    else:
                        continue  # 防呆

                    w = qdt.date().dayOfWeek()
                    t = qdt.time()
                    s_one = {"weekdays": [w], "time": t, "mode": "once", "next_run": qdt}
                    schedules.append(s_one)
                    QListWidgetItem(f"單次：{fmt_item(s_one)} → {qdt.toString('yyyy-MM-dd HH:mm')}", lst)

        

        btn_add.clicked.connect(add_schedule)
        btn_del.clicked.connect(del_selected)

        # 確認/取消
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # return a dict for record...
        def accept():
            out = []
            for s in schedules:
                if s["mode"] == "weekly":
                    t = s["time"]
                    if isinstance(t, str):
                        t = QTime.fromString(t, "HH:mm")  # 標準化
                    out.append({
                        "mode": "weekly",
                        "weekdays": s["weekdays"],
                        "time": t.toString("HH:mm")
                    })
                else:  # once
                    dt = s.get("next_run")
                    print(dt)
                    if isinstance(dt, str):
                        dt = QDateTime.fromString(dt, "yyyy-MM-dd HH:mm")  # 保險
                    
                    out.append({
                        "mode": "once",
                        "datetime": dt.toString("yyyy-MM-dd HH:mm")
                    })

            self._save_report_schedules(out)  # 直接呼叫
            dlg.accept()

        box.accepted.connect(accept)
        box.rejected.connect(dlg.reject)

        # 佈局
        root.addLayout(week_row)
        root.addLayout(line2)
        root.addLayout(mode_row)
        root.addWidget(lst)
        root.addLayout(btn_row)
        root.addWidget(box)

        dlg.exec()
        
   
    def once_now(self):
        if not self.monitored_set:
            self.result_text.append("ℹ️ 無監聽檔案可執行。")
            return
        self.status_label.setText("Running task on monitored files...")
        start = datetime.now()
        succeeded, failed = 0, 0

        for f in sorted(self.monitored_set):
            try:
                self._run_task(f)  # 實際任務
                self.result_text.append(f"✅ Done: {f}")
                succeeded += 1
            except Exception as e:
                self.result_text.append(f"❌ Failed: {f} | {e}")
                failed += 1

        secs = (datetime.now() - start).total_seconds()
        self.status_label.setText(f"Done. {succeeded} ok, {failed} fail.")
        self.result_text.append(f"⏱ 完成。耗時 {secs:.1f}s")

    def _run_task(self, file_path: str):
        # 如果已在跑，就不重複啟動
        if self.proc and self.proc.state() != QProcess.NotRunning:
            self.result_text.append("ℹ️ Task is still running…")
            return

        base = Path(__file__).resolve().parent            # .../src
        task_py = str(base / "src/task.py")                   # src/task.py
        python_exe = sys.executable                       # 目前 venv 的 Python

        self.result_text.append(f"▶ Running: {python_exe} {task_py}")
        self.status_label.setText("Running task...")

        self.proc = QProcess(self)
        self.proc.setProgram(python_exe)
        self.proc.setArguments([task_py])

        # 可選：設定工作目錄；task.py 內已用 __file__ 取路徑，這行可有可無
        self.proc.setWorkingDirectory(str(base))

        # 抓兩路輸出
        self.proc.readyReadStandardOutput.connect(
            lambda: self.result_text.append(
                bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="ignore").rstrip()
            )
        )
        self.proc.readyReadStandardError.connect(
            lambda: self.result_text.append(
                bytes(self.proc.readAllStandardError()).decode("utf-8", errors="ignore").rstrip()
            )
        )

        def _done(exitCode, exitStatus):
            self.status_label.setText(f"Task finished. code={exitCode}")
            self.result_text.append(f"✅ Done. ExitCode={exitCode}, Status={exitStatus}")
        
        self.proc.finished.connect(_done)
        self.proc.start()
    
    def on_scheduling(self):
        if not self.scheduler_on:
            if not self.schedules:
                self.result_text.append("ℹ️ 尚無排程。請先在 Setting Report Time 設定。")
                return
            # 啟動
            self.scheduler_timer = self.scheduler_timer or QTimer(self)
            self.scheduler_timer.timeout.connect(self._check_due_schedules)
            self.scheduler_timer.start(15_000)  # 每 15 秒檢查一次
            self.scheduler_on = True
            self.btn3.setText("Off Scheduling")
            self.status_label.setText("Scheduling ON")
            self.result_text.append("🟢 排程已啟動。")
        else:
            # 停止
            if self.scheduler_timer:
                self.scheduler_timer.stop()
            self.scheduler_on = False
            self.btn3.setText("On Scheduling")
            self.status_label.setText("Scheduling OFF")
            self.result_text.append("🔴 排程已關閉。")

    def _check_due_schedules(self):
        now = QDateTime.currentDateTime()
        now_min = now.toString("yyyy-MM-dd HH:mm")

        # 清除前一分鐘的 fired key
        self._fired_keys = {k for k in self._fired_keys if k.startswith(now_min)}

        due = False
        remaining = []
        for s in self.schedules:
            if s.get("mode") == "weekly":
                wds = s.get("weekdays", [])
                tstr = s.get("time")  # "HH:mm"
                if not isinstance(wds, list) or not tstr:
                    remaining.append(s)
                    continue

                if now.date().dayOfWeek() in wds and now.time().toString("HH:mm") == tstr:
                    key = f"{now_min}|weekly|{tuple(sorted(wds))}|{tstr}"
                    if key not in self._fired_keys:
                        self._fired_keys.add(key)
                        due = True
                remaining.append(s)  # weekly 不移除

            else:  # once
                dts = s.get("datetime")  # "yyyy-MM-dd HH:mm"
                if not dts:
                    # 異常資料，跳過但保留
                    remaining.append(s)
                    continue
                dt = QDateTime.fromString(dts, "yyyy-MM-dd HH:mm")
                if not dt.isValid():
                    remaining.append(s)
                    continue

                if now >= dt:
                    key = f"{now_min}|once|{dts}"
                    if key not in self._fired_keys:
                        self._fired_keys.add(key)
                        due = True
                    # once 觸發後不回存，達成自動移除
                else:
                    remaining.append(s)

        if due:
            self.result_text.append(f"⏰ 觸發排程：{now.toString('yyyy-MM-dd HH:mm:ss')}")
            self.once_now()

        # 若有變更（例如移除已執行的 once）則回存
        if len(remaining) != len(self.schedules):
            self.schedules = remaining
            self.write_config()


    # RUN ALL NOW : 按下去不管時程，跑全部的報表。
    def generate_report(self):
        self.status_label.setText("Generating report...")
        self.result_text.append("Report generated!\nTotal: 1,234 records\nGrowth: +15.3%")
        self.status_label.setText("Report ready!")
    
    def export_excel(self):
        self.status_label.setText("Exporting...")
        self.result_text.append("Excel saved!\nPath: C:/Reports/AutoReport_2025.xlsx")
        self.status_label.setText("Export complete!")

if __name__ == '__main__':
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("nycu.ReportAutomationSystem.1.0")
    except Exception:
        pass  # 不是 Windows 時忽略

    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 現代化風格

    signal.signal(signal.SIGINT, signal.SIG_IGN)  # 忽略 Ctrl+C

    window = ReportAutomationGUI()  # ← ✅ 跑完整GUI！
    window.show()
    sys.exit(app.exec())