"""Application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
    except (ImportError, RuntimeError) as exc:
        if isinstance(exc, ImportError):
            exc = RuntimeError("PySide6 is required to run the desktop application. Install requirements.txt first.")
        print(exc, file=sys.stderr)
        return 2
    app = QApplication(sys.argv)
    app.setApplicationName("Universal Programmer Studio")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
