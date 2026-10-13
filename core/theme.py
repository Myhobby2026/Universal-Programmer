from __future__ import annotations

from enum import Enum


class Theme(str, Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


PALETTES = {
    Theme.DARK: {
        "window": "#1e2229", "surface": "#252a33", "surface_alt": "#2d333d",
        "input": "#171a20", "text": "#e6eaf0", "muted": "#9aa5b5", "border": "#3b4452",
        "accent": "#43a7e8", "accent_hover": "#66b9ef", "success": "#55c596",
        "warning": "#e7b65c", "error": "#ef6b73", "selection": "#294d69",
    },
    Theme.LIGHT: {
        "window": "#f3f5f8", "surface": "#ffffff", "surface_alt": "#e8edf3",
        "input": "#ffffff", "text": "#202832", "muted": "#657180", "border": "#cbd3de",
        "accent": "#1672b9", "accent_hover": "#0d5d9b", "success": "#18794e",
        "warning": "#9a6800", "error": "#b52835", "selection": "#cfe6f7",
    },
}


def stylesheet(theme: Theme, accent: str | None = None) -> str:
    palette = dict(PALETTES[Theme.LIGHT if theme == Theme.SYSTEM else theme])
    if accent:
        palette["accent"] = accent
    p = palette
    return f"""
    QWidget {{ background: {p['window']}; color: {p['text']}; font-size: 13px; }}
    QMainWindow, QDialog {{ background: {p['window']}; }}
    QToolBar, QMenuBar, QStatusBar {{ background: {p['surface']}; border: 0; }}
    QMenuBar::item, QMenu::item {{ padding: 6px 10px; }}
    QMenu {{ background: {p['surface']}; border: 1px solid {p['border']}; }}
    QMenu::item:selected {{ background: {p['selection']}; }}
    QDockWidget {{ titlebar-close-icon: none; border: 1px solid {p['border']}; }}
    QDockWidget::title {{ background: {p['surface']}; padding: 7px; font-weight: 600; }}
    QTabWidget::pane, QGroupBox {{ border: 1px solid {p['border']}; background: {p['surface']}; }}
    QTabBar::tab {{ background: {p['surface']}; color: {p['muted']}; padding: 8px 14px; border-bottom: 2px solid transparent; }}
    QTabBar::tab:selected {{ color: {p['text']}; border-bottom-color: {p['accent']}; }}
    QTabBar::tab:hover {{ color: {p['accent_hover']}; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{ background: {p['input']}; border: 1px solid {p['border']}; border-radius: 3px; padding: 5px; selection-background-color: {p['selection']}; }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ border-color: {p['accent']}; }}
    QPushButton {{ background: {p['surface_alt']}; border: 1px solid {p['border']}; border-radius: 3px; padding: 6px 12px; }}
    QPushButton:hover {{ border-color: {p['accent']}; }}
    QPushButton:disabled {{ color: {p['muted']}; }}
    QTreeView, QTableView, QListView {{ background: {p['surface']}; alternate-background-color: {p['surface_alt']}; border: 1px solid {p['border']}; gridline-color: {p['border']}; }}
    QHeaderView::section {{ background: {p['surface_alt']}; border: 0; border-right: 1px solid {p['border']}; padding: 6px; }}
    QProgressBar {{ background: {p['input']}; border: 1px solid {p['border']}; text-align: center; }}
    QProgressBar::chunk {{ background: {p['accent']}; }}
    QToolTip {{ background: {p['surface_alt']}; color: {p['text']}; border: 1px solid {p['border']}; }}
    QSplitter::handle {{ background: {p['border']}; }}
    """
