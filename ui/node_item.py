"""
========================================================================
ГРАФИЧЕСКИЙ ЭЛЕМЕНТ УЗЛА ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Алгоритмы отрисовки и поведения узлов
                 являются интеллектуальной собственностью автора.
========================================================================
"""

"""
Графический элемент узла для QGraphicsScene
"""
from PyQt6.QtWidgets import (
    QGraphicsObject, QGraphicsTextItem, QGraphicsItem, 
    QMenu, QInputDialog, QColorDialog, QStyle
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QBrush, QPen, QFont, QAction
import re


class NodeItem(QGraphicsObject):
    """Графический элемент узла"""
    
    # Сигналы
    addChildRequested = pyqtSignal(int, str, float, float)  # node_id, title, x, y
    deleteRequested = pyqtSignal(int)  # node_id
    editRequested = pyqtSignal(int)  # node_id
    doubleClicked = pyqtSignal(int)  # ID узла
    positionChanged = pyqtSignal(int, float, float)  # ID узла, x, y
    collapsedChanged = pyqtSignal(int, bool)  # ID узла, collapsed
    colorChanged = pyqtSignal(int, str)  # ID узла, цвет
    
    def __init__(self, node_id: int, title: str, x: float, y: float, 
                 color: str = "#3498db", parent=None):
        super().__init__(parent)
        
        self.node_id = node_id
        self.title = title
        self.color = QColor(color)
        self.collapsed = False
        self.is_root = (node_id == 1)  # Предполагаем, что корневой узел имеет ID 1
        
        # Размеры узла (1 сетка высота × 4 сетки ширина)
        self.grid_size = 50  # Размер одной ячейки сетки
        self.width = self.grid_size * 4  # 4 сетки = 200 пикселей
        self.height = self.grid_size * 1  # 1 сетка = 50 пикселей
        self.corner_radius = 8
        
        # Параметры магнитизма
        self.magnetic_radius = 30  # Радиус притягивания к сетке (в пикселях)
        self.auto_snap_radius = 15  # Радиус автоприлипания (полное притягивание)
        self.magnetic_strength = 0.2  # Сила притягивания (0-1), чем выше - тем сильнее
        
        # Примагничивание позиции к сетке
        snapped_x = self._snap_to_grid(x)
        snapped_y = self._snap_to_grid(y)
        self.setPos(snapped_x, snapped_y)
        
        # Настройки
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Текст заголовка
        self.text_item = QGraphicsTextItem(self.title, self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont()
        font.setPointSize(8)
        self.text_item.setFont(font)
        self.text_item.setTextWidth(self.width - 20)
        
        # Иконка свертывания (если есть дети)
        self.has_children = False
        
        # Обновляем внешний вид
        self.update_appearance()
    
    def boundingRect(self):
        """Определяет область для отрисовки"""
        return QRectF(0, 0, self.width, self.height)
    
    def update_appearance(self):
        """Обновление внешнего вида узла"""
        # Обновляем текст
        self.text_item.setPlainText(self.title)
        
        # Устанавливаем размер шрифта меньше для размещения в узкий узел
        font = self.text_item.font()
        font.setPointSize(8)
        self.text_item.setFont(font)
        
        # Ограничиваем ширину текста
        self.text_item.setTextWidth(self.width - 20)
        
        # Центрируем текст
        text_rect = self.text_item.boundingRect()
        text_x = (self.width - text_rect.width()) / 2
        text_y = (self.height - text_rect.height()) / 2
        self.text_item.setPos(text_x, text_y)
        
        # Обновляем отрисовку
        self.update()
    
    def set_has_children(self, has_children: bool):
        """Установка флага наличия дочерних узлов"""
        self.has_children = has_children
        self.update()
    
    def _snap_to_grid(self, value: float) -> float:
        """Примагничивание значения координаты к сетке"""
        return round(value / self.grid_size) * self.grid_size
    
    def _apply_magnetic_force(self, value: float) -> float:
        """Применяет магнитное притягивание к сетке"""
        # Ближайшая позиция на сетке
        snapped_value = self._snap_to_grid(value)
        
        # Расстояние до сетки
        distance = abs(value - snapped_value)
        
        # Если расстояние очень маленькое - полностью прилипаем к сетке
        if distance <= self.auto_snap_radius:
            return snapped_value
        
        # Если расстояние в пределах магнитного радиуса - плавное притягивание
        if distance <= self.magnetic_radius:
            # Плавно перемещаем узел к сетке
            # Чем ближе к сетке, тем сильнее притягивание
            force_factor = 1.0 - (distance / self.magnetic_radius)
            pull_force = force_factor * self.magnetic_strength
            
            # Плавная интерполяция между текущей позицией и позицией на сетке
            result = value + (snapped_value - value) * pull_force
            return result
        
        # Если далеко от сетки - возвращаем как есть
        return value
    
    def mouseDoubleClickEvent(self, event):
        """Обработка двойного клика"""
        self.doubleClicked.emit(self.node_id)
        event.accept()
    
    def itemChange(self, change, value):
        """Обработка изменений элемента"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Применяем магнитное притягивание к сетке
            new_pos = value
            magnetic_x = self._apply_magnetic_force(new_pos.x())
            magnetic_y = self._apply_magnetic_force(new_pos.y())
            new_pos = QPointF(magnetic_x, magnetic_y)
            
            if self.scene():
                self.scene().update()  # Очищает "шлейф" при перетаскивании
            
            # Эмитируем изменение позиции
            self.positionChanged.emit(self.node_id, new_pos.x(), new_pos.y())
            return new_pos
        
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Контекстное меню"""
        menu = QMenu()
        
        # Действия
        edit_action = QAction("Редактировать", menu)
        edit_action.triggered.connect(lambda: self.doubleClicked.emit(self.node_id))
        
        add_child_action = QAction("Добавить дочерний узел", menu)
        add_child_action.triggered.connect(self._add_child)
        
        change_color_action = QAction("Изменить цвет", menu)
        change_color_action.triggered.connect(self._change_color)
        
        delete_action = QAction("Удалить", menu)
        delete_action.triggered.connect(self._delete_node)
        
        if self.has_children:
            collapse_text = "Свернуть" if not self.collapsed else "Развернуть"
            collapse_action = QAction(collapse_text, menu)
            collapse_action.triggered.connect(self._toggle_collapse)
            menu.addAction(collapse_action)
            menu.addSeparator()
        
        menu.addAction(edit_action)
        menu.addAction(add_child_action)
        menu.addAction(change_color_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        menu.exec(event.screenPos())
    
    def _add_child(self):
        """Добавление дочернего узла"""
        text, ok = QInputDialog.getText(
            None, "Новый узел", "Введите название узла:"
        )
        if ok and text:
            vertical_gap = 120  # расстояние между узлами
            # Сигнал будет обработан в главном окне
            self.addChildRequested.emit(self.node_id, 
                                        text, 
                                        self.x(), 
                                        self.y() + self.height + vertical_gap
                                        )
    
    def _change_color(self):
        """Изменение цвета узла"""
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color
            self.update_appearance()
            self.colorChanged.emit(self.node_id, color.name())
    
    def _delete_node(self):
        """Удаление узла"""
        self.deleteRequested.emit(self.node_id)
    
    def _toggle_collapse(self):
        """Переключение состояния свертывания"""
        self.collapsed = not self.collapsed
        self.collapsedChanged.emit(self.node_id, self.collapsed)
        self.update()
    
    def paint(self, painter, option, widget=None):
        """Кастомная отрисовка"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # ⛔ Отключаем стандартное выделение Qt (ВАЖНО)
        option.state &= ~QStyle.StateFlag.State_Selected
        option.state &= ~QStyle.StateFlag.State_HasFocus
        
        # Определяем цвета
        brush_color = self.color
        pen_color = Qt.GlobalColor.black
        
        if self.isSelected():
            pen_color = Qt.GlobalColor.green
            pen_width = 3
        else:
            # Рамка темнее цвета узла на 30%
            pen_color = self.color.darker(130)
            pen_width = 2
            
        pen = QPen(pen_color, pen_width)
        
        # Рисуем скругленный прямоугольник
        rect = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # Заливка
        painter.fillPath(path, QBrush(brush_color))
        
        # Рамка
        pen = QPen(pen_color, 2)
        if self.isSelected():
            pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Рисуем индикатор свертывания если есть дети
        if self.has_children:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            
            # Маленький треугольник в правом углу
            indicator_size = 12
            indicator_x = rect.right() - indicator_size - 3
            indicator_y = (rect.height() - indicator_size) / 2
            indicator_rect = QRectF(indicator_x, indicator_y, indicator_size, indicator_size)
            indicator_path = QPainterPath()
            
            if self.collapsed:
                # Треугольник вправо (свернуто)
                indicator_path.moveTo(indicator_rect.left(), indicator_rect.top())
                indicator_path.lineTo(indicator_rect.left(), indicator_rect.bottom())
                indicator_path.lineTo(indicator_rect.right(), indicator_rect.center().y())
            else:
                # Треугольник вниз (развернуто)
                indicator_path.moveTo(indicator_rect.left(), indicator_rect.top())
                indicator_path.lineTo(indicator_rect.right(), indicator_rect.top())
                indicator_path.lineTo(indicator_rect.center().x(), indicator_rect.bottom())
            
            indicator_path.closeSubpath()
            painter.drawPath(indicator_path)
            painter.restore()

    def shape(self):
        path = QPainterPath()
        path.addRoundedRect(
            0,
            0,
            self.width,
            self.height,
            self.corner_radius,
            self.corner_radius
        )
        return path