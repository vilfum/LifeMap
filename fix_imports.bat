@echo off
echo Исправление импортов для PyQt6...

rem Исправляем ui_graph_scene.py
powershell -Command "(Get-Content 'ui_graph_scene.py' -Raw) -replace 'from PyQt6\.QtWidgets import QGraphicsScene, QGraphicsView, QMenu, QAction', 'from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu\nfrom PyQt6.QtGui import QAction' | Set-Content 'ui_graph_scene.py'"

rem Исправляем ui_main_window.py
powershell -Command "(Get-Content 'ui_main_window.py' -Raw) -replace 'from PyQt6\.QtWidgets import \(', 'from PyQt6.QtWidgets import (\n    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \n    QToolBar, QStatusBar, QMessageBox, QInputDialog,\n    QApplication, QSplitter, QFileDialog, QDialog, QLabel,\n    QLineEdit, QPushButton, QCheckBox, QAction' | Set-Content 'ui_main_window.py'"

echo Исправления применены!
pause