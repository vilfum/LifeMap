"""
Графический элемент узла
"""

"""
========================================================================
ЭЛЕМЕНТ УЗЛА ДЛЯ ГРАФИЧЕСКОЙ СЦЕНЫ
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Внешний вид и поведение узла являются
                 интеллектуальной собственностью автора.
========================================================================
"""

from PyQt6.QtWidgets import (
    QGraphicsObject, QGraphicsTextItem, QGraphicsItem, 
    QMenu, QInputDialog, QColorDialog, QStyle,
    QDialog, QVBoxLayout, QLineEdit, QComboBox, QDialogButtonBox
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
        
        # Размеры узла (1 сетка высота  4 сетки ширина)
        self.grid_size = 50  # Размер одной ячейки сетки
        self.width = self.grid_size * 4  # 4 сетки = 200 пикселей
        self.height = self.grid_size * 1  # 1 сетка = 50 пикселей
        self.corner_radius = 8
        
        # Параметры магнитизма
        self.magnetic_radius = 30  # Радиус притягивания к сетке (в пикселях)
        self.auto_snap_radius = 15  # Радиус автоприлипания (полное притягивание)
        self.magnetic_strength = 0.0
        
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
        self.text_item.setPlainText(self.title)
        font = self.text_item.font()
        font.setPointSize(8)
        self.text_item.setFont(font)
        self.text_item.setTextWidth(self.width - 20)
        text_rect = self.text_item.boundingRect()
        text_x = (self.width - text_rect.width()) / 2
        text_y = (self.height - text_rect.height()) / 2
        self.text_item.setPos(text_x, text_y)
        self.update()
    
    def set_has_children(self, has_children: bool):
        self.has_children = has_children
        self.update()
    
    def _snap_to_grid(self, value: float) -> float:
        return round(value / self.grid_size) * self.grid_size
    
    def _apply_magnetic_force(self, value: float) -> float:
        snapped_value = self._snap_to_grid(value)
        distance = abs(value - snapped_value)
        if distance <= self.auto_snap_radius:
            return snapped_value
        if distance <= self.magnetic_radius:
            force_factor = 1.0 - (distance / self.magnetic_radius)
            pull_force = force_factor * self.magnetic_strength
            result = value + (snapped_value - value) * pull_force
            return result
        return value
    
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.node_id)
        event.accept()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            magnetic_x = self._apply_magnetic_force(new_pos.x())
            magnetic_y = self._apply_magnetic_force(new_pos.y())
            new_pos = QPointF(magnetic_x, magnetic_y)
            if self.scene():
                self.scene().update()
            self.positionChanged.emit(self.node_id, new_pos.x(), new_pos.y())
            return new_pos
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("Редактировать", menu)
        edit_action.triggered.connect(lambda: self.doubleClicked.emit(self.node_id))
        add_child_action = QAction("Добавить дочерний узел", menu)
        add_child_action.triggered.connect(self._add_child)
        change_parent_action = QAction("Изменить родительский узел", menu)
        change_parent_action.triggered.connect(self._on_change_parent)
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
        menu.addAction(change_parent_action)
        menu.addAction(change_color_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(event.screenPos())
    
    def _add_child(self):
        text, ok = QInputDialog.getText(
            None, "Новый узел", "Введите название узла:"
        )
        if ok and text:
            vertical_gap = 120
            self.addChildRequested.emit(self.node_id,
                                        text,
                                        self.x(),
                                        self.y() + self.height + vertical_gap)
    
    def _on_change_parent(self):
        """Обработка команды изменения родителя"""
        print(f"DEBUG node_item._on_change_parent start node={self.node_id}")
        old_parent = None
        node_obj = None
        if self.scene() and hasattr(self.scene(), 'graph_service'):
            node_obj = self.scene().graph_service.get_node(self.node_id)
            old_parent = node_obj.parent_id if node_obj else None
        dialog = ChangeParentDialog(
            self.node_id,
            self.scene().graph_service,
            parent=self.scene().views()[0] if self.scene() else None
        )
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_node_id:
            new_parent_id = dialog.selected_node_id
            print(f"DEBUG selected new parent {new_parent_id}")

            # если корневой узел получает родителя, отметим это
            if self.is_root:
                print(f"DEBUG node {self.node_id} перестаёт быть корнем")
                self.is_root = False

            old_pid, new_pid, old_eid, new_eid = self.scene().graph_service.change_parent(
                self.node_id, new_parent_id)
            print(f"DEBUG service.change_parent returned {old_pid},{new_pid},{old_eid},{new_eid}")

            # обновляем отображение связей
            if self.scene():
                if old_eid is not None:
                    print(f"DEBUG удаляю старую связь {old_eid}")
                    self.scene().remove_edge(old_eid)
                if new_eid is not None:
                    print(f"DEBUG добавляю новую связь {new_eid}")
                    self.scene().add_edge(new_eid, new_parent_id, self.node_id)

                # флаги has_children
                if old_parent is not None:
                    has = len(self.scene().graph_service.get_children(old_parent)) > 0
                    self.scene().update_node_children_flag(old_parent, has)
                self.scene().update_node_children_flag(new_parent_id, True)

                # переместить узел и перерисовать ребра под ним
                self.scene().relocate_subtree(self)
        print(f"DEBUG node_item._on_change_parent end node={self.node_id}")
    
    def _change_color(self):
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color
            self.update_appearance()
            self.colorChanged.emit(self.node_id, color.name())
    
    def _delete_node(self):
        self.deleteRequested.emit(self.node_id)
    
    def _toggle_collapse(self):
        self.collapsed = not self.collapsed
        self.collapsedChanged.emit(self.node_id, self.collapsed)
        self.update()
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        option.state &= ~QStyle.StateFlag.State_Selected
        option.state &= ~QStyle.StateFlag.State_HasFocus
        brush_color = self.color
        pen_color = Qt.GlobalColor.black
        if self.isSelected():
            pen_color = Qt.GlobalColor.green
            pen_width = 3
        else:
            pen_color = self.color.darker(130)
            pen_width = 2
        pen = QPen(pen_color, pen_width)
        rect = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        painter.fillPath(path, QBrush(brush_color))
        pen = QPen(pen_color, 2)
        if self.isSelected():
            pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPath(path)
        if self.has_children:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            indicator_size = 12
            indicator_x = rect.right() - indicator_size - 3
            indicator_y = (rect.height() - indicator_size) / 2
            indicator_rect = QRectF(indicator_x, indicator_y, indicator_size, indicator_size)
            indicator_path = QPainterPath()
            if self.collapsed:
                indicator_path.moveTo(indicator_rect.left(), indicator_rect.top())
                indicator_path.lineTo(indicator_rect.left(), indicator_rect.bottom())
                indicator_path.lineTo(indicator_rect.right(), indicator_rect.center().y())
            else:
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


class ChangeParentDialog(QDialog):
    """Диалог выбора нового родителя узла"""

    def __init__(self, node_id: int, graph_service, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.service = graph_service
        self.selected_node_id = None

        self.setWindowTitle("Изменить родительский узел")
        self.resize(400, 120)

        layout = QVBoxLayout(self)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Поиск по названию…")
        layout.addWidget(self.search)

        self.combo = QComboBox(self)
        layout.addWidget(self.combo)

        # Подправим палитру выпадающего списка и поля, чтобы они
        # не были абсолютно черными в светлой теме и сохраняли
        # соответствие глобальной палитре приложения.
        pal = self.palette()
        from ui.themes import is_dark_mode
        if is_dark_mode():
            # тёмная тема: используем чуть светлее фон для элементов
            pal.setColor(pal.ColorRole.Base, QColor("#303030"))
            pal.setColor(pal.ColorRole.Text, QColor("#e0e0e0"))
        else:
            # светлая тема: умеренный серый фон и не слишком яркий текст
            pal.setColor(pal.ColorRole.Base, QColor("#f5f5f5"))
            pal.setColor(pal.ColorRole.Text, QColor("#202020"))

        self.search.setPalette(pal)
        self.combo.setPalette(pal)
        # view (список) тоже
        try:
            self.combo.view().setPalette(pal)
        except Exception:
            pass
        # также и для самого диалога
        self.setPalette(pal)

        # PyQt6 использует перечисление StandardButton
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | \
                                   QDialogButtonBox.StandardButton.Cancel,
                                   parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._all_candidates = []
        self._populate()
        self.search.textChanged.connect(self._filter)

        # указать стиль из общей темы (если родитель задаёт stylesheet)
        if parent is not None:
            self.setStyleSheet(parent.styleSheet())

    def _populate(self):
        self.combo.clear()
        nodes = [n for n in self.service.get_all_nodes()
                 if n.id != self.node_id and not self.service.is_descendant(n, self.service.get_node(self.node_id))]
        self._all_candidates = nodes
        for n in nodes:
            self.combo.addItem(n.title, n.id)

    def _filter(self, text: str):
        text = text.lower()
        self.combo.clear()
        for n in self._all_candidates:
            if text in n.title.lower():
                self.combo.addItem(n.title, n.id)

    def accept(self) -> None:
        idx = self.combo.currentIndex()
        if idx >= 0:
            self.selected_node_id = self.combo.itemData(idx)
        super().accept()

