"""
========================================================================
ГРАФИЧЕСКАЯ СЦЕНА ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Алгоритмы визуализации и управления сценой
                 являются интеллектуальной собственностью автора.
========================================================================
"""

"""
Графическая сцена для отображения карты
"""
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu, QFrame
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QPoint
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
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        
        # Словари для хранения элементов
        self.nodes = {}  # node_id -> NodeItem
        self.edges = {}  # edge_id -> EdgeItem
        self.node_edges = {}
        
        # Состояние
        #self.dragging = False
        #self.drag_start = QPointF()

        # Отключаем индексирование для производительности (может вызывать артефакты)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        
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
        node_item.addChildRequested.connect(self.addChildNodeRequested.emit)
        node_item.deleteRequested.connect(self.deleteNodeRequested.emit)
        node_item.editRequested.connect(self.nodeDoubleClicked.emit)  # редактирование = двойной клик
        
        self.addItem(node_item)
        self.nodes[node_id] = node_item

        print(f"DEBUG add_node: Добавлен узел {node_id} в словарь nodes")
        print(f"  Текущие узлы: {list(self.nodes.keys())}")
        
        return node_item
    
    def add_edge(self, edge_id: int, from_node_id: int, to_node_id: int,
                 line_type: LineType = LineType.SOLID, color: str = "#000000") -> EdgeItem:
        """Добавление связи на сцену"""
        from_item = self.nodes.get(from_node_id)
        to_item = self.nodes.get(to_node_id)

        print(f"DEBUG add_edge: edge_id={edge_id}, from={from_node_id}, to={to_node_id}")
        print(f"  from_item in nodes: {from_node_id in self.nodes}")
        print(f"  to_item in nodes: {to_node_id in self.nodes}")
        print(f"  Все узлы в сцене: {list(self.nodes.keys())}")
        
        if not from_item or not to_item:
            return None
        
        try:
            edge_item = EdgeItem(edge_id, from_item, to_item, line_type, color)
            #if hasattr(edge_item, 'deleted'):
                #edge_item.deleted.connect(self.deleteEdgeRequested.emit)
            
            self.addItem(edge_item)
            edge_item.setZValue(-1)  # Помещаем под узлы
            self.edges[edge_id] = edge_item

            if from_node_id not in self.node_edges:
                self.node_edges[from_node_id] = set()
            if to_node_id not in self.node_edges:
                self.node_edges[to_node_id] = set()
            
            self.node_edges[from_node_id].add(edge_id)
            self.node_edges[to_node_id].add(edge_id)

            return edge_item
        except Exception as e:
            print(f"Ошибка при создании связи: {e}")
            return None
        
    def remove_edge(self, edge_id: int):
        """Удаление связи со сцены"""
        edge_item = self.edges.pop(edge_id, None)
        if edge_item:
            self.removeItem(edge_item)
            print(f"DEBUG: Удалена связь {edge_id}")
            
            # Удаляем из словаря node_edges
            # Получаем node_id из edge_item
            try:
                from_node_id = edge_item.from_item.node_id
                to_node_id = edge_item.to_item.node_id
                
                if from_node_id in self.node_edges:
                    self.node_edges[from_node_id].discard(edge_id)
                    if not self.node_edges[from_node_id]:
                        del self.node_edges[from_node_id]
                
                if to_node_id in self.node_edges:
                    self.node_edges[to_node_id].discard(edge_id)
                    if not self.node_edges[to_node_id]:
                        del self.node_edges[to_node_id]
            except AttributeError:
                pass  # Если что-то пошло не так

    def remove_node(self, node_id: int):
        """Удаление узла и всех его связей со сцены"""
        # 1. Удаляем все связанные связи
        self.remove_edges_for_node(node_id)
    
        # 2. Удаляем узел
        node_item = self.nodes.pop(node_id, None)
        if node_item:
            self.removeItem(node_item)
            print(f"DEBUG: Удален узел {node_id} со всеми связями")
    
    def remove_edges_for_node(self, node_id: int):
        """Удаляет все связи, связанные с узлом"""
        if node_id in self.node_edges:
            # Копируем список, так как мы будем изменять словарь во время итерации
            edge_ids = list(self.node_edges[node_id])
            for edge_id in edge_ids:
                self.remove_edge(edge_id)
    
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
    
    #def mousePressEvent(self, event):
        #"""Обработка нажатия мыши"""
        #if event.button() == Qt.MouseButton.RightButton:
            # Если клик по пустому месту
            #item = self.get_node_at(event.scenePos())
            #if not item:
                #self.dragging = True
                #self.drag_start = event.scenePos()
                #event.accept()
                #return
        
        #super().mousePressEvent(event)
    
    #def mouseMoveEvent(self, event):
        #"""Обработка перемещения мыши"""
        #if self.dragging:
            # Перетаскивание всей сцены
            #delta = event.scenePos() - self.drag_start
            #self.drag_start = event.scenePos()
            
            # Перемещаем все видимые элементы
            #for item in self.items():
                #if isinstance(item, (NodeItem, EdgeItem)):
                    #item.setPos(item.pos() + delta)
            
            #event.accept()
        #else:
            #super().mouseMoveEvent(event)
    
    #def mouseReleaseEvent(self, event):
        #"""Обработка отпускания мыши"""
        #if self.dragging and event.button() == Qt.MouseButton.RightButton:
            #self.dragging = False
            #event.accept()
            #return
        
        #super().mouseReleaseEvent(event)
    
    def drawBackground(self, painter, rect):
        """Отрисовка фона с сеткой - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        # ВАЖНО: сначала вызываем родительский метод для очистки
        super().drawBackground(painter, rect)
        
        # Рисуем сетку ТОЛЬКО если нужно
        painter.save()
        
        # Устанавливаем перо для сетки
        grid_pen = QPen(QColor(230, 230, 230), 1)  # Светло-серая сетка
        grid_pen.setCosmetic(True)  # Важно: косметическое перо (не зависит от масштаба)
        painter.setPen(grid_pen)
        
        # Используем целочисленные координаты для избежания артефактов
        grid_size = 50
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())
        
        # Рисуем сетку ТОЛЬКО в видимой области
        # Вертикальные линии
        x = left
        while x <= right:
            painter.drawLine(x, top, x, bottom)
            x += grid_size
        
        # Горизонтальные линии
        y = top
        while y <= bottom:
            painter.drawLine(left, y, right, y)
            y += grid_size
        
        painter.restore()

    def remove_all_references_to_node(self, node_id: int):
        """Удалить все ссылки на узел из сцены"""
        # Удаляем узел из словаря
        if node_id in self.nodes:
            del self.nodes[node_id]
        
        # Удаляем связи, связанные с этим узлом
        edges_to_delete = []
        for edge_id, edge_item in self.edges.items():
            try:
                if (edge_item.from_item.node_id == node_id or 
                    edge_item.to_item.node_id == node_id):
                    edges_to_delete.append(edge_id)
            except:
                continue
        
        for edge_id in edges_to_delete:
            edge_item = self.edges.pop(edge_id, None)
            if edge_item:
                self.removeItem(edge_item)
    
    def clear_selection_for_node(self, node_id: int):
        """Снять выделение с узла"""
        node_item = self.nodes.get(node_id)
        if node_item:
            node_item.setSelected(False)


class GraphView(QGraphicsView):
    """Вид для графической сцены с поддержкой масштабирования"""
    
    def __init__(self, scene: GraphScene, parent=None):
        super().__init__(scene, parent)
        
        self.scene = scene

        #Состояние
        self.panning = False
        self.pan_start = QPoint()
        
        # Настройки вида
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        # Устанавливаем RubberBandDrag
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        # Отключаем оптимизации, которые могут вызывать артефакты
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        # Настройки прокрутки
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Убираем рамку у view
        self.setFrameShape(QFrame.Shape.NoFrame)  # ← Вместо 0 QFrame.Shape.NoFrame
        
        # Устанавливаем стиль для rubber band (выделения области)
        #self.setStyleSheet("""
            #QGraphicsView {
                #border: 0px;
                #background: transparent;
            #}
            #QGraphicsView::rubberBand {
                #border: 2px dashed #2196F3;
                #background-color: rgba(33, 150, 243, 30);
            #}
        #""")

        # Масштабирование
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Устанавливаем режим обновления для избежания артефактов
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        if event.button() == Qt.MouseButton.RightButton:
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши"""
        if self.panning:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания мыши"""
        if event.button() == Qt.MouseButton.RightButton and self.panning:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)
    
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