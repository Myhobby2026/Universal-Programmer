"""Qt desktop shell: honest status, dockable panels, and functional workspace tabs."""

from __future__ import annotations

from pathlib import Path

from core.models import FirmwareInfo
from core.settings import SettingsStore
from core.theme import Theme, stylesheet
from devices import DeviceCatalog
from file_formats import read_binary, read_intel_hex
from memory import MemoryBuffer

try:
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import (
        QComboBox, QDockWidget, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
        QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPlainTextEdit,
        QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
        QTextEdit, QVBoxLayout, QWidget, QInputDialog,
    )
except ImportError as exc:  # pragma: no cover - exercised only without optional GUI deps
    raise RuntimeError("PySide6 is required to run the desktop application. Install requirements.txt first.") from exc


class MainWindow(QMainWindow):
    TAB_NAMES = [
        "Dashboard", "Device Explorer", "Device Database", "SWD Programmer", "JTAG Programmer",
        "UART Bootloader", "SPI NOR Flash", "I²C EEPROM", "Parallel NAND", "Memory Editor",
        "File Manager", "Device Identification", "Operations", "Logic Analyzer", "Serial Terminal",
        "Pin Mapping", "Operation History", "Settings",
    ]

    def __init__(self, settings: SettingsStore | None = None):
        super().__init__()
        self.settings = settings or SettingsStore()
        self.catalog = DeviceCatalog()
        self.firmware = FirmwareInfo()
        self.buffer = MemoryBuffer()
        self.setWindowTitle("Universal Programmer Studio")
        self.resize(1400, 900)
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_docks()
        self._restore_layout()
        self.apply_theme(self.settings.get("theme", Theme.DARK.value))

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("Open binary/HEX…", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        workspace = self.menuBar().addMenu("&Workspace")
        default_action = QAction("Restore default layout", self)
        default_action.triggered.connect(self.restore_default_layout)
        workspace.addAction(default_action)
        save_action = QAction("Save named layout…", self)
        save_action.triggered.connect(self.save_workspace)
        workspace.addAction(save_action)
        load_action = QAction("Restore named layout…", self)
        load_action.triggered.connect(self.load_workspace)
        workspace.addAction(load_action)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        connect = QPushButton("Connect Teensy")
        connect.clicked.connect(self.show_not_connected)
        toolbar.addWidget(connect)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Theme"))
        themes = QComboBox()
        themes.addItems([theme.value for theme in Theme])
        themes.setCurrentText(self.settings.get("theme", Theme.DARK.value))
        themes.currentTextChanged.connect(self.apply_theme)
        toolbar.addWidget(themes)

    def _build_workspace(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        for name in self.TAB_NAMES:
            self.tabs.addTab(self._tab_content(name), name)
        self.setCentralWidget(self.tabs)

    def _tab_content(self, name: str) -> QWidget:
        if name == "Dashboard":
            widget = QWidget(); layout = QVBoxLayout(widget)
            title = QLabel("Universal Programmer Studio")
            title.setStyleSheet("font-size: 22px; font-weight: 600;")
            layout.addWidget(title)
            for label, value in (("Controller", "Not connected"), ("Firmware", "Unknown"), ("Target", "No target selected"), ("Operation", "Idle")):
                row = QHBoxLayout(); row.addWidget(QLabel(label)); row.addStretch(); row.addWidget(QLabel(value)); layout.addLayout(row)
            note = QLabel("Hardware operations remain disabled until a compatible Teensy capability and validated target profile are available.")
            note.setWordWrap(True); layout.addWidget(note); layout.addStretch(); return widget
        if name in {"Device Explorer", "Device Database"}:
            widget = QWidget(); layout = QVBoxLayout(widget)
            search = QLineEdit(); search.setPlaceholderText("Search manufacturer, family, or part number")
            table = QTableWidget(0, 5); table.setHorizontalHeaderLabels(("Manufacturer", "Part", "Interface", "Support", "Operations"))
            def refresh(text: str = "") -> None:
                profiles = self.catalog.search(text); table.setRowCount(len(profiles))
                for row, profile in enumerate(profiles):
                    values = (profile.manufacturer, profile.part_number, profile.interface.value, profile.support_level.value, ", ".join(profile.operations))
                    for column, value in enumerate(values): table.setItem(row, column, QTableWidgetItem(value))
            search.textChanged.connect(refresh); refresh()
            layout.addWidget(search); layout.addWidget(table); return widget
        if name == "Memory Editor":
            widget = QWidget(); layout = QVBoxLayout(widget)
            info = QLabel("No local buffer loaded. Open a binary or Intel HEX file to begin editing.")
            editor = QPlainTextEdit(); editor.setReadOnly(True); editor.setPlaceholderText("Hex preview")
            self.memory_info, self.memory_preview = info, editor
            layout.addWidget(info); layout.addWidget(editor); return widget
        widget = QWidget(); layout = QVBoxLayout(widget)
        heading = QLabel(name); heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(heading)
        status = QLabel("Unavailable until the required hardware, adapter, and validated algorithm are present.")
        status.setWordWrap(True); layout.addWidget(status)
        layout.addWidget(QLabel("This workspace is intentionally capability-gated; no simulated detection or programming result is shown."))
        layout.addStretch(); return widget

    def _build_docks(self) -> None:
        self.explorer_dock = self._dock("Device Explorer", QListWidget([p.part_number for p in self.catalog.search()]), Qt.LeftDockWidgetArea)
        details = QWidget(); details_layout = QFormLayout(details)
        details_layout.addRow("Controller", QLabel("Not connected")); details_layout.addRow("Voltage", QLabel("Unavailable")); details_layout.addRow("Interface", QLabel("None"))
        self._dock("Target Information", details, Qt.RightDockWidgetArea)
        terminal = QPlainTextEdit(); terminal.setReadOnly(True); terminal.setPlainText("Terminal idle — no serial transport is connected.")
        self._dock("Terminal", terminal, Qt.BottomDockWidgetArea)
        log = QPlainTextEdit(); log.setReadOnly(True); log.setPlainText("Operation log ready.")
        self._dock("Operation Log", log, Qt.BottomDockWidgetArea)
        progress = QProgressBar(); progress.setRange(0, 100); progress.setValue(0); progress.setFormat("Idle")
        self._dock("Progress", progress, Qt.BottomDockWidgetArea)

    def _dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self); dock.setObjectName(title.replace(" ", "_")); dock.setWidget(widget)
        self.addDockWidget(area, dock); return dock

    def _restore_layout(self) -> None:
        state = self.settings.get("window_state", "")
        geometry = self.settings.get("window_geometry", "")
        if state:
            self.restoreState(QByteArray.fromBase64(state.encode()))
        if geometry:
            self.restoreGeometry(QByteArray.fromBase64(geometry.encode()))

    def restore_default_layout(self) -> None:
        for dock in self.findChildren(QDockWidget):
            dock.show()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.explorer_dock)
        self.statusBar().showMessage("Default layout restored")

    def save_workspace(self) -> None:
        name, accepted = QInputDialog.getText(self, "Save workspace", "Workspace name:")
        if not accepted or not name.strip():
            return
        workspaces = dict(self.settings.get("workspaces", {}))
        workspaces[name.strip()] = {
            "state": bytes(self.saveState().toBase64()).decode(),
            "geometry": bytes(self.saveGeometry().toBase64()).decode(),
        }
        self.settings.set("workspaces", workspaces); self.settings.save()
        self.statusBar().showMessage(f"Workspace '{name.strip()}' saved")

    def load_workspace(self) -> None:
        workspaces = self.settings.get("workspaces", {})
        if not workspaces:
            self.statusBar().showMessage("No named workspaces saved")
            return
        name, accepted = QInputDialog.getItem(self, "Restore workspace", "Workspace:", list(workspaces), 0, False)
        if not accepted:
            return
        saved = workspaces[name]
        self.restoreState(QByteArray.fromBase64(saved["state"].encode()))
        self.restoreGeometry(QByteArray.fromBase64(saved["geometry"].encode()))
        self.statusBar().showMessage(f"Workspace '{name}' restored")

    def apply_theme(self, value: str) -> None:
        try: theme = Theme(value)
        except ValueError: theme = Theme.DARK
        self.settings.set("theme", theme.value); self.settings.save()
        effective = theme
        if theme == Theme.SYSTEM:
            scheme = self.styleHints().colorScheme()
            effective = Theme.DARK if scheme == Qt.ColorScheme.Dark else Theme.LIGHT
        self.setStyleSheet(stylesheet(effective, self.settings.get("accent")))

    def show_not_connected(self) -> None:
        self.statusBar().showMessage("Teensy: Not connected — no hardware operation started", 5000)

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open firmware or dump", "", "Firmware (*.bin *.hex);;All files (*.*)")
        if path:
            try:
                if Path(path).suffix.casefold() == ".hex":
                    image = read_intel_hex(path)
                    data, address = image.data, image.start_address
                else:
                    data, address = read_binary(path), 0
                self.buffer = MemoryBuffer(data, base_address=address)
                preview = "\n".join(f"{address + offset:08X}  {data[offset:offset + 16].hex(' ')}" for offset in range(0, len(data), 16))
                self.memory_info.setText(f"{Path(path).name} · {len(data)} bytes · address range 0x{address:X}–0x{address + len(data):X}")
                self.memory_preview.setPlainText(preview)
                self.statusBar().showMessage(f"Loaded {Path(path).name}")
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Unable to open file", str(exc))

    def closeEvent(self, event) -> None:  # noqa: N802
        self.settings.set("window_state", bytes(self.saveState().toBase64()).decode())
        self.settings.set("window_geometry", bytes(self.saveGeometry().toBase64()).decode())
        self.settings.save()
        event.accept()
