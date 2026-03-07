"""
Вкладка с датами и событиями
"""

"""
========================================================================
ВКЛАДКА-ДАТЫ
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Логика работы с датами является
                 интеллектуальной собственностью автора.
========================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QDateEdit,
    QPushButton, QScrollArea, QMessageBox,
    QTextEdit, QListWidget
)
from PyQt6.QtCore import Qt, QDate
from widgets import BaseTabWidget
from core.content_service import ContentService
from ui.themes import is_dark_mode

class DatesTabWidget(BaseTabWidget):
    """Вкладка для хранения дат и событий"""
    def __init__(self, node_content, tab):
        super().__init__(node_content, tab)
        self.build_ui()
        self.load_from_model()
        self.refresh_theme()

    def build_ui(self):
        """Построение интерфейса вкладки"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)                    # <-- Убираем зазор между scroll и кнопкой

        # Контейнер для событий
        self.container = DatesContainer()
        self.container_layout = self.container.layout
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setContentsMargins(5, 5, 5, 5)
        self.container_layout.setSpacing(5)

        # Разрешаем перетаскивание для добавления событий
        self.container.setAcceptDrops(True)

        # ScrollArea
        self.scroll = QScrollArea()                   # <-- сохраняем как self.scroll
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.container)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setContentsMargins(0, 0, 0, 0)    # <-- убираем отступы
        # self._apply_theme_to_widget(self.scroll)      # <-- сразу применяем тему

        main_layout.addWidget(self.scroll)

        # Кнопка добавления
        self.add_button = QPushButton("Добавить дату")
        self.add_button.clicked.connect(self.add_event_row)
        main_layout.addWidget(self.add_button)

    # def _apply_theme_to_widget(self, widget):
    #     """Применить тему к динамически созданному виджету"""
    #     dark_mode = is_dark_mode()  # получаем состояние темы из глобального модуля

    #     # --- 1. Для контейнеров (QWidget, кроме специальных) ---
    #     if isinstance(widget, QWidget) and not isinstance(widget, 
    #             (QLineEdit, QDateEdit, QPushButton, QTextEdit, QListWidget, QScrollArea)):
    #         color = "#353535" if dark_mode else "#f5f5f5"
    #         widget.setStyleSheet(f"background-color: {color};")
    #         widget.setAutoFillBackground(True)
    #         return

    #     # --- 1.1 Для QScrollArea ---
    #     elif isinstance(widget, QScrollArea):
    #         color = "#353535" if dark_mode else "#f5f5f5"
    #         widget.setStyleSheet(f"QScrollArea {{ background-color: {color}; border: none; }}")
    #         widget.viewport().setStyleSheet(f"background-color: {color};")
    #         widget.setAutoFillBackground(True)
    #         widget.viewport().setAutoFillBackground(True)
    #         return

    #     # --- 2. Для полей ввода и кнопок ---
    #     elif isinstance(widget, QLineEdit):
    #         if dark_mode:
    #             widget.setStyleSheet("""
    #                 QLineEdit {
    #                     background-color: #252525;
    #                     color: white;
    #                     border: 1px solid #555;
    #                     padding: 3px;
    #                 }
    #             """)
    #         else:
    #             widget.setStyleSheet("""
    #                 QLineEdit {
    #                     background-color: white;
    #                     color: black;
    #                     border: 1px solid #ccc;
    #                     padding: 3px;
    #                 }
    #             """)
    #         widget.setAutoFillBackground(True)

    #     elif isinstance(widget, QDateEdit):
    #         if dark_mode:
    #             widget.setStyleSheet("""
    #                 QDateEdit {
    #                     background-color: #252525;
    #                     color: white;
    #                     border: 1px solid #555;
    #                     padding: 3px;
    #                 }
    #                 QDateEdit::drop-down {
    #                     background-color: #404040;
    #                     border: 1px solid #555;
    #                 }
    #             """)
    #         else:
    #             widget.setStyleSheet("""
    #                 QDateEdit {
    #                     background-color: white;
    #                     color: black;
    #                     border: 1px solid #ccc;
    #                     padding: 3px;
    #                 }
    #                 QDateEdit::drop-down {
    #                     background-color: #f0f0f0;
    #                     border: 1px solid #ccc;
    #                 }
    #             """)
    #         widget.setAutoFillBackground(True)

    #     elif isinstance(widget, QPushButton):
    #         if dark_mode:
    #             widget.setStyleSheet("""
    #                 QPushButton {
    #                     background-color: #404040;
    #                     color: white;
    #                     border: 1px solid #555;
    #                     padding: 5px;
    #                     border-radius: 3px;
    #                 }
    #                 QPushButton:hover {
    #                     background-color: #505050;
    #                 }
    #                 QPushButton:pressed {
    #                     background-color: #606060;
    #                 }
    #             """)
    #         else:
    #             widget.setStyleSheet("""
    #                 QPushButton {
    #                     background-color: #f0f0f0;
    #                     color: black;
    #                     border: 1px solid #ccc;
    #                     padding: 5px;
    #                     border-radius: 3px;
    #                 }
    #                 QPushButton:hover {
    #                     background-color: #e0e0e0;
    #                 }
    #                 QPushButton:pressed {
    #                     background-color: #d0d0d0;
    #                 }
    #             """)
    #         widget.setAutoFillBackground(True)

    def add_event_row(self, title="", date=None):
        """Добавление строки события"""
        row_widget = QWidget()
        # self._apply_theme_to_widget(row_widget)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        # Поле названия
        title_edit = QLineEdit()
        title_edit.installEventFilter(self)
        #title_edit.returnPressed.connect(lambda: self.finish_title_edit(title_edit))
        item_text = title if title else f"Событие {self.container_layout.count() + 1}"
        title_edit.setPlaceholderText("Название события")
        title_edit.setText(item_text)
        # self._apply_theme_to_widget(title_edit)

        # Поле даты
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd.MM.yyyy")

        if date:
            date_edit.setDate(date)
        else:
            date_edit.setDate(QDate.currentDate())
        # self._apply_theme_to_widget(date_edit)

        # Кнопка удаления
        remove_button = QPushButton("Удалить дату")
        #remove_button.setFixedWidth(30)
        # self._apply_theme_to_widget(remove_button)

        # Добавляем в layout
        row_layout.addWidget(title_edit, 1)
        row_layout.addWidget(date_edit)
        row_layout.addWidget(remove_button)

        # Добавляем строку в контейнер
        self.container_layout.addWidget(row_widget)

        # Подключения
        title_edit.textChanged.connect(self.mark_dirty)
        date_edit.dateChanged.connect(self.mark_dirty)

        remove_button.clicked.connect(lambda: self.remove_event_row(row_widget))

        self.mark_dirty()

    def remove_event_row(self, row_widget):
        """Удаление строки события"""
        row_widget.setParent(None)
        row_widget.deleteLater()
        self.mark_dirty()

    def refresh_theme(self):
        """Обновить тему для всех элементов вкладки"""
        # # Обновляем фон самой вкладки
        # # self._apply_theme_to_widget(self)
        # # Обновляем фон контейнера
        # # self._apply_theme_to_widget(self.container)
        # # Обновляем фон скролл-области
        # if hasattr(self, 'scroll'):
        #     # self._apply_theme_to_widget(self.scroll)

        # # Обновляем каждую строку событий
        # for i in range(self.container_layout.count()):
        #     item = self.container_layout.itemAt(i)
        #     if not item:
        #         continue
        #     row_widget = item.widget()
        #     if not row_widget:
        #         continue

        #     # Обновляем фон самой строки
        #     # self._apply_theme_to_widget(row_widget)

        #     # Обновляем дочерние виджеты в строке
        #     layout = row_widget.layout()
        #     if layout:
        #         for j in range(layout.count()):
        #             w = layout.itemAt(j).widget()
        #             # if w:
        #             #     self._apply_theme_to_widget(w)
        self.style().polish(self)
        self.update()

    def load_from_model(self):
        """Загружает данные из модели в виджет"""
        # Очистка контейнера
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        events = self.tab.data.get("events", [])
        for event in events:
            title = event.get("title", "")
            date_str = event.get("date")

            date = QDate.fromString(date_str, "dd.MM.yyyy")
            if not date.isValid():
                date = QDate.currentDate()

            self.add_event_row(title, date)

        self._dirty = False

    def save_to_model(self):
        """Сохранение данных в модель"""
        if not self._dirty:
            print("💾 ListTabWidget: нет изменений для сохранения")
            return  # Если нет изменений, не сохраняем
        
        events = []
        for i in range(self.container_layout.count()):
            row = self.container_layout.itemAt(i).widget()
            if not row:
                continue

            layout = row.layout()

            title_edit = layout.itemAt(0).widget()
            date_edit = layout.itemAt(1).widget()

            events.append({
                "title": title_edit.text(),
                "date": date_edit.date().toString("dd.MM.yyyy")
            })

        new_data = {"events": events}
        ContentService.update_tab_data(self.node_content, self.tab.tab_id, new_data)
        self._dirty = False

        print(f"💾 DatesTabWidget: сохранено {len(events)} событий")

    def eventFilter(self, obj, event):
        """Обработка нажатия Enter в QLineEdit для сохранения изменений"""
        if isinstance(obj, QLineEdit) and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                obj.clearFocus()
                self.mark_dirty()
                return True  # БЛОКИРУЕМ дальнейшую обработку

        return super().eventFilter(obj, event)


class DatesContainer(QWidget):
    """Контейнер для событий с поддержкой drag and drop"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def dragEnterEvent(self, event):
        """Разрешаем перетаскивание файлов в контейнер"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Обрабатываем перетаскивание файлов в контейнер"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.add_event_from_file(file_path)

        event.acceptProposedAction()
