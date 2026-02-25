"""
Вкладка со списком задач (TODO)
"""

"""
========================================================================
ВКЛАДКА-СПИСОК ДЕЛ
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Логика управления задачами является
                 интеллектуальной собственностью автора.
========================================================================
"""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout, QAbstractItemView
from PyQt6.QtCore import Qt
from widgets import BaseTabWidget
from core.content_service import ContentService

class TodoTabWidget(BaseTabWidget):
    """
    Вкладка TODO:
    - список задач с чекбоксами
    - автосохранение
    """

    def __init__(self, node_content, content_tab, parent=None):
        super().__init__(node_content, content_tab, parent)
        self.build_ui()
        self.load_from_model()

    # Создание интерфейса
    def build_ui(self):
        layout = QVBoxLayout(self)

        # Список задач
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget)

        # Подключаем сигнал изменений элементов
        self.list_widget.itemChanged.connect(self.on_item_changed)
        # Сигналы для отслеживания перемещений
        # 1. При изменении данных (включая перемещение)
        self.list_widget.model().dataChanged.connect(self.on_data_changed)
        # 2. При изменении структуры (перемещение строк)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)

        # Кнопки управления
        self.add_button = QPushButton("Добавить")
        self.remove_button = QPushButton("Удалить")
        
        # Layout
        layout.addWidget(self.list_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)

        # Разрешаем перетаскивание для изменения порядка задач
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)

        
        # Сигналы
        self.add_button.clicked.connect(self.add_item)
        self.remove_button.clicked.connect(self.remove_item)
        self.list_widget.itemChanged.connect(self.on_item_changed)

    # Добавление задачи
    def add_item(self):
        item_text = f"Новый элемент {self.list_widget.count() + 1}"
        item = QListWidgetItem(item_text)
        self.list_widget.addItem(item) 
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.list_widget.setCurrentItem(item)
        self.list_widget.editItem(item)
        self.mark_dirty()  # Помечаем как измененное

    # Удаление задачи
    def remove_item(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            row = self.list_widget.row(current_item)
            self.list_widget.takeItem(row)
            self.mark_dirty()  # Помечаем как измененное

    # Реакция на чекбокс
    def on_item_changed(self, item):
        self.mark_dirty()  # Помечаем как измененное
        # Ничего не делаем здесь
        # Сохранение произойдёт при деактивации вкладки
        pass

    # Загрузка данных из модели
    def load_from_model(self):
        self.list_widget.clear()

        # Временно отключаем сигнал, чтобы не вызывать mark_dirty при загрузке
        self.list_widget.itemChanged.disconnect(self.on_item_changed)

        items = self.tab.data.get("items", [])
        for obj in items:
            item = QListWidgetItem(obj.get("text", ""))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            item.setCheckState(Qt.CheckState.Checked if obj.get("done") else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

        # Включаем сигнал обратно
        self.list_widget.itemChanged.connect(self.on_item_changed)
        
        self._dirty = False  # Сбрасываем флаг изменений после загрузки

    # Сохранение данных в модель
    def save_to_model(self):
        if not self._dirty:
            print("💾 ListTabWidget: нет изменений для сохранения")
            return  # Если нет изменений, не сохраняем
        
        # Собираем все элементы списка с их состоянием
        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            items.append({
                "text": item.text(),
                "done": item.checkState() == Qt.CheckState.Checked
            })
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)

        #self.tab.data["items"] = items
        new_data = {"items": items}
        ContentService.update_tab_data(self.node_content, self.tab.tab_id, new_data)
        self._dirty = False  # Сбрасываем флаг изменений
        print(f"💾 ListTabWidget: сохранено {len(items)} элементов")

    def on_item_changed(self, item):
        """Вызывается при изменении текста элемента (редактировании)"""
        self.mark_dirty()  # Помечаем как измененное

    def on_data_changed(self, topLeft, bottomRight, roles):
        """Вызывается при изменении данных в модели"""
        self.mark_dirty()

    def on_rows_moved(self, parent, start, end, destination, row):
        """Вызывается при перемещении строк (drag and drop)"""
        self.mark_dirty()
