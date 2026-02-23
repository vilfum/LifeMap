print("app.py loaded")
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def run():
    print("app.run() started")
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
