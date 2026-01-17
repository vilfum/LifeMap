"""
========================================================================
ГРАФИЧЕСКИЙ ЭЛЕМЕНТ СВЯЗИ ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: Жариков Артем Леонидович
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Алгоритмы отрисовки и управления связями
                 являются интеллектуальной собственностью автора.
========================================================================
"""

"""
Графический элемент связи между узлами
"""
from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor, QAction

from models import LineType


class EdgeItem(QGraphicsPathItem):
    """Графический элемент связи"""
    
    # Сигналы
    deleted = pyqtSignal(int)  # ID связи
    
    def __init__(self, edge_id: int, from_item: 'NodeItem', to_item: 'NodeItem',
                 line_type: LineType = LineType.SOLID, color: str = "#000000"):
        super().__init__()
        
        self.edge_id = edge_id
        self.from_item = from_item
        self.to_item = to_item
        self.line_type = line_type
        self.color = QColor(color)
        
        # Настройки
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Привязываем к узлам
        self.from_item.positionChanged.connect(self.update_path)
        self.to_item.positionChanged.connect(self.update_path)
        
        # Обновляем путь
        self.update_path()
        self.update_appearance()
    
    def update_path(self):
        """Обновление пути связи"""
        path = QPainterPath()
        
        # Начальная точка (центр правой стороны from_item)
        from_rect = self.from_item.rect()
        from_pos = self.from_item.pos()
        start = QPointF(
            from_pos.x() + from_rect.width(),
            from_pos.y() + from_rect.height() / 2
        )
        
        # Конечная точка (центр левой стороны to_item)
        to_rect = self.to_item.rect()
        to_pos = self.to_item.pos()
        end = QPointF(
            to_pos.x(),
            to_pos.y() + to_rect.height() / 2
        )
        
        # Создаем плавную кривую Безье
        path.moveTo(start)
        
        # Контрольные точки для плавности
        ctrl1 = QPointF(start.x() + 50, start.y())
        ctrl2 = QPointF(end.x() - 50, end.y())
        
        path.cubicTo(ctrl1, ctrl2, end)
        
        self.setPath(path)
    
    def update_appearance(self):
        """Обновление внешнего вида связи"""
        pen = QPen(self.color, 2)
        
        # Настройка типа линии
        if self.line_type == LineType.DASHED:
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 4])
        elif self.line_type == LineType.DOTTED:
            pen.setStyle(Qt.PenStyle.DotLine)
            pen.setDashPattern([2, 2])
        elif self.line_type == LineType.BOLD:
            pen.setWidth(4)
        else:  # SOLID
            pen.setStyle(Qt.PenStyle.SolidLine)
        
        if self.isSelected():
            pen.setColor(Qt.GlobalColor.red)
            pen.setWidth(pen.width() + 1)
        
        self.setPen(pen)
    
    def paint(self, painter, option, widget=None):
        """Кастомная отрисовка"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        super().paint(painter, option, widget)
        
        # Рисуем стрелку на конце
        if self.path().length() > 0:
            painter.save()
            painter.setPen(self.pen())
            painter.setBrush(self.pen().color())
            
            # Получаем конечную точку и направление
            path = self.path()
            percent = 0.99  # Положение стрелки (99% от длины)
            point = path.pointAtPercent(percent)
            angle = path.angleAtPercent(percent)
            
            # Рисуем стрелку
            arrow_size = 10
            arrow_p1 = point + QPointF(
                arrow_size * 0.8, 0
            ).rotated(angle + 150)
            arrow_p2 = point + QPointF(
                arrow_size * 0.8, 0
            ).rotated(angle - 150)
            
            arrow_path = QPainterPath()
            arrow_path.moveTo(point)
            arrow_path.lineTo(arrow_p1)
            arrow_path.lineTo(arrow_p2)
            arrow_path.closeSubpath()
            
            painter.drawPath(arrow_path)
            painter.restore()
    
    def contextMenuEvent(self, event):
        """Контекстное меню"""
        menu = QMenu()
        
        delete_action = QAction("Удалить связь", menu)
        delete_action.triggered.connect(lambda: self.deleted.emit(self.edge_id))
        
        menu.addAction(delete_action)
        menu.exec(event.screenPos())
    
    def hoverEnterEvent(self, event):
        """Обработка наведения курсора"""
        self.setZValue(100)  # Поднимаем над другими элементами
        pen = self.pen()
        pen.setWidth(pen.width() + 2)
        self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Обработка выхода курсора"""
        self.setZValue(0)
        pen = self.pen()
        pen.setWidth(pen.width() - 2)
        self.setPen(pen)
        super().hoverLeaveEvent(event)