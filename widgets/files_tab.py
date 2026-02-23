import os
from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog,
    QMessageBox, QAbstractItemView, QFileIconProvider
)
from PyQt6.QtCore import Qt, QUrl, QFileInfo
from PyQt6.QtGui import QDesktopServices
from widgets import BaseTabWidget
from core.file_service import FileService
from core.content_service import ContentService

class FilesTabWidget(BaseTabWidget):
    """
    Вкладка файлов.
    Хранит список файлов в формате:
    self.tab.data["items"] = [
        {
            "name": "file.txt",
            "path": "C:/path/file.txt",
            "size": 12345
        }
    ]
    """
    
    def __init__(self, node_content, tab, parent=None):
        super().__init__(node_content, tab, parent)
        self.node_id = node_content.node_id # берём из node_content
        self.file_service = FileService()
        self.icon_provider = QFileIconProvider()
        self.build_ui()
        self.load_from_model()

    # --------------------------------------------------
    # Построение интерфейса
    # --------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        # Список файлов
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget)

        # Кнопки снизу
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить")
        self.remove_button = QPushButton("Удалить")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        layout.addLayout(buttons_layout)

        # Настройка drag and drop
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setAcceptDrops(True)

        # Сигналы
        self.add_button.clicked.connect(self.add_file_dialog)
        self.remove_button.clicked.connect(self.remove_selected_file)
        self.list_widget.itemDoubleClicked.connect(self.open_file)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)

    # --------------------------------------------------
    # Загрузка данных в UI
    # --------------------------------------------------
    def load_from_model(self):
        self.list_widget.clear()

        items = self.tab.data.get("items", [])
        for file_data in items:
            file_path = file_data.get("path", "")
            #if not file_path or not os.path.exists(file_path):
            if not file_path or not self.file_service.file_exists(file_path):
                continue
            file_info = QFileInfo(str(file_path))
            icon = self.icon_provider.icon(file_info)
            size = file_data.get("size", 0)
            display_name = f"{file_data['name']} ({self.format_size(size)})"

            item = QListWidgetItem(icon, display_name)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setData(Qt.ItemDataRole.UserRole + 1, size)
            self.list_widget.addItem(item)

        self._dirty = False

    # --------------------------------------------------
    # Сохранение данных в модель
    # --------------------------------------------------
    def save_to_model(self):
        if not self._dirty:
            print("💾 FilesTabWidget: нет изменений для сохранения")
            return

        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            size = item.data(Qt.ItemDataRole.UserRole + 1)
            items.append({
                "name": item.text().split(" (")[0],  # отрезаем размер
                "path": path,
                "size": size
            })

        #self.tab.data["items"] = items
        new_data = {"items": items}
        ContentService.update_tab_data(self.node_content, self.tab.tab_id, new_data)
        self._dirty = False
        print(f"💾 FilesTabWidget: сохранено {len(items)} файлов")

    # --------------------------------------------------
    # Добавление файла через диалог
    # --------------------------------------------------
    def add_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "Все файлы (*)"
        )
        if file_path:
            self.add_file(file_path)

    # --------------------------------------------------
    # Добавление файла (копирование в папку узла)
    # --------------------------------------------------

    def add_file(self, source_path):
        destination_path = self.file_service.add_file(self.node_id, source_path)
        if not destination_path:
            return

        file_info = QFileInfo(str(destination_path))
        icon = self.icon_provider.icon(file_info)
        size = destination_path.stat().st_size
        display_name = f"{destination_path.name} ({self.format_size(size)})"

        item = QListWidgetItem(icon, display_name)
        item.setData(Qt.ItemDataRole.UserRole, str(destination_path))
        item.setData(Qt.ItemDataRole.UserRole + 1, size)

        self.list_widget.addItem(item)
        self.mark_dirty()
        self.save_to_model()
        


    # --------------------------------------------------
    # Удаление выбранного файла
    # --------------------------------------------------
    def remove_selected_file(self):
        """Удалить выбранный файл после подтверждения"""
        row = self.list_widget.currentRow()
        if row < 0:
            return

        item = self.list_widget.item(row)
        file_path = item.data(Qt.ItemDataRole.UserRole)
        file_name = item.text().split(" (")[0]  # отрезаем размер

        # Диалог подтверждения
        reply = QMessageBox.question(
            self,
        "Удаление файла",
            f"Удалить файл «{file_name}»?\nФайл будет также удалён с диска.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Удаляем физический файл, если он существует
            #if file_path and os.path.exists(file_path):
            #    try:
            #        os.remove(file_path)
            if file_path:
                try:
                    self.file_service.remove_file(file_path)
                    print(f"🗑️ Файл удалён с диска: {file_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить файл:\n{str(e)}")
            # Удаляем элемент из списка
            self.list_widget.takeItem(row)
            self.mark_dirty()

    def delete_all_files(self):
        """Удалить все файлы этой вкладки с диска (вызывается при удалении вкладки)"""
        items = self.tab.data.get("items", [])
        deleted_count = 0
        for file_data in items:
            file_path = file_data.get("path")
            #if file_path and os.path.exists(file_path):
            #    try:
            #        os.remove(file_path)
            if file_path:
                try:
                    self.file_service.remove_file(file_path)
                    deleted_count += 1
                    print(f"🗑️ Удалён файл вкладки: {file_path}")
                except Exception as e:
                    print(f"❌ Не удалось удалить {file_path}: {e}")
        if deleted_count:
            print(f"Удалено файлов: {deleted_count}")

    # --------------------------------------------------
    # Открытие файла двойным кликом
    # --------------------------------------------------
    def open_file(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        #if not file_path or not os.path.exists(file_path):
        if not file_path or not self.file_service.file_exists(file_path):
            QMessageBox.warning(self, "Ошибка", "Файл не найден.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    # --------------------------------------------------
    # Drag & drop файлов извне
    # --------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.add_file(file_path)
        event.acceptProposedAction()

    # --------------------------------------------------
    # Изменение порядка элементов (перетаскивание)
    # --------------------------------------------------
    def on_rows_moved(self, *args):
        self.mark_dirty()
        # Порядок сохранится при вызове save_to_model

    # --------------------------------------------------
    # Форматирование размера файла
    # --------------------------------------------------
    @staticmethod
    def format_size(size):
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
