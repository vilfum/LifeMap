"""
Упрощенная версия Карты Жизни для тестирования
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsTextItem, QVBoxLayout, QWidget,
    QInputDialog, QMenu, QAction, QColorDialog
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath


class SimpleNodeItem(QGraphicsRectItem):
    """Упрощенный узел без БД"""
    
    def __init__(self, title: str, x: float, y: float, color: str = "#3498db"):
        super().__init__(0, 0, 200, 60)
        self.setPos(x, y)
        self.title = title
        self.color = QColor(color)
        self.setBrush(QBrush(self.color))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        
        # Текст
        self.text_item = QGraphicsTextItem(self.title, self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.update_text_position()
    
    def update_text_position(self):
        """Центрирование текста"""
        text_rect = self.text_item.boundingRect()
        text_x = (self.rect().width() - text_rect.width()) / 2
        text_y = (self.rect().height() - text_rect.height()) / 2
        self.text_item.setPos(text_x, text_y)
    
    def paint(self, painter, option, widget=None):
        """Отрисовка со скругленными углами"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Скругленный прямоугольник
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        
        # Заливка
        painter.fillPath(path, self.brush())
        
        # Рамка
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.yellow, 3))
        else:
            painter.setPen(self.pen())
        painter.drawPath(path)


class SimpleMainWindow(QMainWindow):
    """Упрощенное главное окно"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Карта Жизни (Упрощенная версия)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Сцена и вид
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.view)
        
        # Добавляем корневой узел
        self.add_node("Жизнь", 400, 300)
        
        # Настройка
        self.scene.setBackgroundBrush(QColor(240, 240, 240))
        
        # Двойной клик для добавления узлов
        self.view.mouseDoubleClickEvent = self.add_node_on_click
    
    def add_node(self, title: str, x: float, y: float):
        """Добавление узла"""
        node = SimpleNodeItem(title, x, y)
        self.scene.addItem(node)
        
        # Контекстное меню
        node.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        node.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
    
    def add_node_on_click(self, event):
        """Добавление узла по двойному клику"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Получаем позицию в координатах сцены
            scene_pos = self.view.mapToScene(event.pos())
            
            # Запрашиваем название
            text, ok = QInputDialog.getText(
                self, "Новый узел", "Введите название узла:"
            )
            if ok and text:
                self.add_node(text, scene_pos.x(), scene_pos.y())
        
        # Вызываем родительский метод
        QGraphicsView.mouseDoubleClickEvent(self.view, event)


def main():
    app = QApplication(sys.argv)
    window = SimpleMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()