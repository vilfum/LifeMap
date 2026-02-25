"""
Вкладка со списком
"""

"""
========================================================================
ВКЛАДКА-СПИСОК
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Логика работы со списком является
                 интеллектуальной собственностью автора.
========================================================================
"""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from widgets import BaseTabWidget
from core.content_service import ContentService

class ListTabWidget(BaseTabWidget):
    """Виджет для вкладки со списком"""
    def __init__(self, node_content, tab, parent=None):
        super().__init__(node_content, tab, parent)
        
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Подключаем сигнал изменений элементов
        self.list_widget.itemChanged.connect(self.on_item_changed)
        # Сигналы для отслеживания перемещений
        # 1. При изменении данных (включая перемещение)
        self.list_widget.model().dataChanged.connect(self.on_data_changed)
        # 2. При изменении структуры (перемещение строк)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)
        
        self.add_button = QPushButton("Добавить")
        self.remove_button = QPushButton("Удалить")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)
        
        # Подключаем кнопки
        self.add_button.clicked.connect(self.add_item)
        self.remove_button.clicked.connect(self.remove_item)
        
        # Загружаем данные
        self.load_from_model()

    def add_item(self):
        """Добавить новый элемент в список"""
        item_text = f"Новый элемент {self.list_widget.count() + 1}"
        item = QListWidgetItem(item_text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.list_widget.addItem(item)
        self.list_widget.setCurrentItem(item)
        self.mark_dirty()  # Помечаем как измененное

    def remove_item(self):
        """Удалить выбранный элемент из списка"""
        current_item = self.list_widget.currentItem()
        if current_item:
            row = self.list_widget.row(current_item)
            self.list_widget.takeItem(row)
            self.mark_dirty()  # Помечаем как измененное

    def on_item_changed(self, item):
        """Вызывается при изменении текста элемента (редактировании)"""
        self.mark_dirty()  # Помечаем как измененное

    def on_data_changed(self, topLeft, bottomRight, roles):
        """Вызывается при изменении данных в модели"""
        self.mark_dirty()

    def on_rows_moved(self, parent, start, end, destination, row):
        """Вызывается при перемещении строк (drag and drop)"""
        self.mark_dirty()

    def load_from_model(self):
        """Загружает данные из модели в виджет"""
        items = self.tab.data.get("items", [])
        
        # Временно отключаем сигнал, чтобы не вызывать mark_dirty при загрузке
        self.list_widget.itemChanged.disconnect(self.on_item_changed)
        
        self.list_widget.clear()
        for item_text in items:
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.list_widget.addItem(item)
        
        # Включаем сигнал обратно
        self.list_widget.itemChanged.connect(self.on_item_changed)
        
        self._dirty = False  # Сбрасываем флаг изменений после загрузки

    def save_to_model(self):
        """Сохранить данные из виджета в модель"""
        if not self._dirty:
            print("💾 ListTabWidget: нет изменений для сохранения")
            return  # Если нет изменений, не сохраняем
        
        # Собираем все элементы списка
        #items = []
        #for i in range(self.list_widget.count()):
        #    item = self.list_widget.item(i)
        #    items.append(item.text())
        
        # Сохраняем в модель вкладки
        #self.tab.data["items"] = items
        items = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        new_data = {"items": items}
        ContentService.update_tab_data(self.node_content, self.tab.tab_id, new_data)

        self._dirty = False  # Сбрасываем флаг изменений
        
        print(f"💾 ListTabWidget: сохранено {len(items)} элементов")

