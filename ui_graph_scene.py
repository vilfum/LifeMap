"""
========================================================================
ГРАФИЧЕСКАЯ СЦЕНА ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: [Ваше Имя]
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Алгоритмы визуализации и управления сценой
                 являются интеллектуальной собственностью автора.
========================================================================
"""

"""
Графическая сцена для отображения карты
"""
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QAction

from ui_node_item import NodeItem
from ui_edge_item import EdgeItem
from models import LineType


class GraphScene(QGraphicsScene):
    """Графическая сцена для карты жизни"""
    
    # Сигналы
    nodeDoubleClicked = pyqtSignal(int)  # ID узла
    nodePositionChanged = pyqtSignal(int, float, float)  # ID узла, x, y
    nodeCollapsedChanged = pyqtSignal(int, bool)  # ID узла, collapsed
    nodeColorChanged = pyqtSignal(int, str)  # ID узла, цвет
    addNodeRequested = pyqtSignal(float, float)  # x, y
    addChildNodeRequested = pyqtSignal(int, str, float, float)  # parent_id, title, x, y
    deleteNodeRequested = pyqtSignal(int)  # node_id
    deleteEdgeRequested = pyqtSignal(int)  # edge_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Настройки сцены
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Словари для хранения элементов
        self.nodes = {}  # node_id -> NodeItem
        self.edges = {}  # edge_id -> EdgeItem
        
        # Состояние
        self.dragging = False
        self.drag_start = QPointF()
        
        # Контекстное меню
        self.setup_context_menu()
    
    def setup_context_menu(self):
        """Настройка контекстного меню сцены"""
        pass  # Реализуем в главном окне
    
    def add_node(self, node_id: int, title: str, x: float, y: float, 
                 color: str = "#3498db") -> NodeItem:
        """Добавление узла на сцену"""
        node_item = NodeItem(node_id, title, x, y, color)
        
        # Подключаем сигналы
        node_item.doubleClicked.connect(self.nodeDoubleClicked.emit)
        node_item.positionChanged.connect(self.nodePositionChanged.emit)
        node_item.collapsedChanged.connect(self.nodeCollapsedChanged.emit)
        node_item.colorChanged.connect(self.nodeColorChanged.emit)
        
        self.addItem(node_item)
        self.nodes[node_id] = node_item
        return node_item
    
    def add_edge(self, edge_id: int, from_node_id: int, to_node_id: int,
                 line_type: LineType = LineType.SOLID, color: str = "#000000") -> EdgeItem:
        """Добавление связи на сцену"""
        from_item = self.nodes.get(from_node_id)
        to_item = self.nodes.get(to_node_id)
        
        if not from_item or not to_item:
            return None
        
        try:
            edge_item = EdgeItem(edge_id, from_item, to_item, line_type, color)
            if hasattr(edge_item, 'deleted'):
                edge_item.deleted.connect(self.deleteEdgeRequested.emit)
            
            self.addItem(edge_item)
            edge_item.setZValue(-1)  # Помещаем под узлы
            self.edges[edge_id] = edge_item
            return edge_item
        except Exception as e:
            print(f"Ошибка при создании связи: {e}")
            return None
    
    def delete_node(self, node_id: int):
        """Удаление узла со сцены"""
        if node_id in self.nodes:
            node_item = self.nodes[node_id]
            self.removeItem(node_item)
            del self.nodes[node_id]
    
    def delete_edge(self, edge_id: int):
        """Удаление связи со сцены"""
        if edge_id in self.edges:
            edge_item = self.edges[edge_id]
            self.removeItem(edge_item)
            del self.edges[edge_id]
    
    def update_node_children_flag(self, node_id: int, has_children: bool):
        """Обновление флага наличия дочерних узлов"""
        if node_id in self.nodes:
            self.nodes[node_id].set_has_children(has_children)
    
    def get_node_at(self, pos: QPointF) -> NodeItem:
        """Получение узла в указанной позиции"""
        items = self.items(pos)
        for item in items:
            if isinstance(item, NodeItem):
                return item
        return None
    
    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        if event.button() == Qt.MouseButton.RightButton:
            # Если клик по пустому месту
            item = self.get_node_at(event.scenePos())
            if not item:
                self.dragging = True
                self.drag_start = event.scenePos()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши"""
        if self.dragging:
            # Перетаскивание всей сцены
            delta = event.scenePos() - self.drag_start
            self.drag_start = event.scenePos()
            
            # Перемещаем все видимые элементы
            for item in self.items():
                if isinstance(item, (NodeItem, EdgeItem)):
                    item.setPos(item.pos() + delta)
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Обработка отпускания мыши"""
        if self.dragging and event.button() == Qt.MouseButton.RightButton:
            self.dragging = False
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def drawBackground(self, painter, rect):
        """Отрисовка фона с сеткой"""
        super().drawBackground(painter, rect)
        
        # Рисуем сетку
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        
        grid_size = 50
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())
        
        # Вертикальные линии
        x = left
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += grid_size
        
        # Горизонтальные линии
        y = top
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += grid_size


class GraphView(QGraphicsView):
    """Вид для графической сцены с поддержкой масштабирования"""
    
    def __init__(self, scene: GraphScene, parent=None):
        super().__init__(scene, parent)
        
        self.scene = scene
        
        # Настройки вида
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        
        # Настройки прокрутки
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Масштабирование
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.min_zoom = 0.1
        self.max_zoom = 5.0
    
    def wheelEvent(self, event):
        """Обработка колесика мыши для масштабирования"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Масштабирование с зажатым Ctrl
            delta = event.angleDelta().y()
            
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def zoom_in(self):
        """Увеличение масштаба"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor += self.zoom_step
            self.scale(1 + self.zoom_step, 1 + self.zoom_step)
    
    def zoom_out(self):
        """Уменьшение масштаба"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor -= self.zoom_step
            self.scale(1 - self.zoom_step, 1 - self.zoom_step)
    
    def reset_zoom(self):
        """Сброс масштаба"""
        self.resetTransform()
        self.zoom_factor = 1.0
    
    def fit_to_view(self):
        """Подгонка под размер окна"""
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def mouseDoubleClickEvent(self, event):
        """Обработка двойного клика"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Получаем позицию в координатах сцены
            scene_pos = self.mapToScene(event.pos())
            
            # Если клик по пустому месту - создаем новый узел
            item = self.scene.get_node_at(scene_pos)
            if not item:
                self.scene.addNodeRequested.emit(scene_pos.x(), scene_pos.y())
                event.accept()
                return
        
        super().mouseDoubleClickEvent(event)