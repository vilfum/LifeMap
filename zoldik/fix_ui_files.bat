@echo off
echo Исправление файлов UI...

rem Исправляем ui_graph_scene.py
echo from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu > ui_graph_scene_fixed.py
echo from PyQt6.QtCore import Qt, QPointF, pyqtSignal >> ui_graph_scene_fixed.py
echo from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QAction >> ui_graph_scene_fixed.py
echo. >> ui_graph_scene_fixed.py
echo from ui_node_item import NodeItem >> ui_graph_scene_fixed.py
echo from ui_edge_item import EdgeItem >> ui_graph_scene_fixed.py
echo from models import LineType >> ui_graph_scene_fixed.py

rem Копируем остальное содержимое файла
more +7 ui_graph_scene.py >> ui_graph_scene_fixed.py
move /y ui_graph_scene_fixed.py ui_graph_scene.py

echo Файлы исправлены!
echo Запустите программу: python main.py
pause