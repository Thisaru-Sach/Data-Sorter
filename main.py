"""Data Sorter - entry point."""
import sys

from PySide6.QtWidgets import QApplication

from ui import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Data Sorter")
    window = MainWindow()
    window.show()
    # Allows "Open with Data Sorter" / `python main.py file.xlsx`
    if len(sys.argv) > 1:
        window.load_path(sys.argv[1])
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
