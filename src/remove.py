from PySide6.QtWidgets import (
    QDialog, QListWidget, QVBoxLayout, QDialogButtonBox,
    QListWidgetItem, QPushButton
)
from PySide6.QtCore import Qt

class MonitoredFilePicker(QDialog):
    def __init__(self, files, parent=None, title="選擇要移除的檔案"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 420)

        self.listw = QListWidget(self)
        self.listw.setSelectionMode(QListWidget.ExtendedSelection)
        for f in sorted(files):
            QListWidgetItem(f, self.listw)

        self.btn_select_all = QPushButton("全選", self)
        self.btn_clear_sel = QPushButton("清除選取", self)
        self.btn_select_all.clicked.connect(lambda: self._set_all_selected(True))
        self.btn_clear_sel.clicked.connect(lambda: self._set_all_selected(False))

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.listw)
        layout.addWidget(self.btn_select_all)
        layout.addWidget(self.btn_clear_sel)
        layout.addWidget(self.buttons)

    def _set_all_selected(self, checked: bool):
        for i in range(self.listw.count()):
            self.listw.item(i).setSelected(checked)

    def selected_files(self):
        return [it.text() for it in self.listw.selectedItems()]
