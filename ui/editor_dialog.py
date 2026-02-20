"""
========================================================================
РЕДАКТОР УЗЛА "КАРТА ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Дизайн интерфейса и пользовательские сценарии
                 являются интеллектуальной собственностью автора.
========================================================================
"""

"""
Главное окно приложения
"""
import sys
from pathlib import Path
from typing import Optional, cast, TYPE_CHECKING
import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QToolBar, QStatusBar, QMessageBox, QInputDialog,
    QApplication, QSplitter, QFileDialog, QDialog, QLabel,
    QLineEdit, QPushButton, QCheckBox, QTabWidget, QMenu, QTextEdit, QListWidget,
    QListWidgetItem, QAbstractItemView, QDateEdit, QScrollArea,
    QFileIconProvider
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QPointF, QRectF, QDate, QUrl, QFileInfo
from PyQt6.QtGui import QIcon, QKeySequence, QPalette, QColor, QAction, QPixmap, QPainter, QBrush, QDesktopServices

#from ui_graph_scene import GraphScene, GraphView
#from database import DatabaseManager, EncryptedSQLite
from models import ContentTab, Node, Edge, LineType, NodeContent, ContentTabType

from core.content_service import ContentService
from core.content_repository import ContentRepository

from widgets import (
    BaseTabWidget, TextTabWidget,
    ListTabWidget, TodoTabWidget,
    DatesTabWidget, FilesTabWidget
    )

#if TYPE_CHECKING:
#    from ui_main_window import MainWindow

class TitleEditField(QLineEdit):
    """Редактор названия узла с автозавершением при потере фокуса или Enter"""
    def __init__(self, text, finish_callback, parent=None):
        super().__init__(text, parent)
        self.finish_callback = finish_callback
        self._is_finishing = False
        self.should_save = True  # Флаг: сохранять ли при завершении
    
    def focusOutEvent(self, event):
        """Завершить редактирование при потере фокуса"""
        if not self._is_finishing:
            self._is_finishing = True
            self.should_save = True  # При потере фокуса - сохраняем
            # Даём время для обработки других событий
            QTimer.singleShot(0, self._complete_edit)
        super().focusOutEvent(event)
    
    def _complete_edit(self):
        """Выполнить завершение редактирования"""
        self.finish_callback(save=self.should_save)
        self._is_finishing = False
    
    def keyPressEvent(self, event):
        """Обработать Enter и Escape"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Enter - сохраняем и закрываем
            if not self._is_finishing:
                self._is_finishing = True
                self.should_save = True
                self.finish_callback(save=True)
                self._is_finishing = False
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            # Escape - просто закрываем БЕЗ сохранения
            if not self._is_finishing:
                self._is_finishing = True
                self.should_save = False
                self.finish_callback(save=False)
                self._is_finishing = False
            event.accept()
        else:
            super().keyPressEvent(event)


class TabRenameEditField(QLineEdit):
    """Редактор названия вкладки с автозавершением при потере фокуса или Enter"""
    def __init__(self, text, finish_callback, parent=None):
        super().__init__(text, parent)
        self.finish_callback = finish_callback
        self._is_finishing = False
        self.should_save = True  # Флаг: сохранять ли при завершении
    
    def focusOutEvent(self, event):
        """Завершить редактирование при потере фокуса"""
        if not self._is_finishing:
            self._is_finishing = True
            self.should_save = True  # При потере фокуса - сохраняем
            # Даём время для обработки других событий
            QTimer.singleShot(0, self._complete_edit)
        super().focusOutEvent(event)
    
    def _complete_edit(self):
        """Выполнить завершение редактирования"""
        self.finish_callback(save=self.should_save)
        self._is_finishing = False
    
    def mousePressEvent(self, event):
        """При клике в самом поле - продолжать редактирование"""
        super().mousePressEvent(event)
        event.accept()
    
    def keyPressEvent(self, event):
        """Обработать Enter и Escape"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Enter - сохраняем и закрываем
            if not self._is_finishing:
                self._is_finishing = True
                self.should_save = True
                self.finish_callback(save=True)
                self._is_finishing = False
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            # Escape - просто закрываем БЕЗ сохранения
            if not self._is_finishing:
                self._is_finishing = True
                self.should_save = False
                self.finish_callback(save=False)
                self._is_finishing = False
            event.accept()
        else:
            super().keyPressEvent(event)


class NodeContentEditorDialog(QDialog):
    def __init__(self, node, parent=None, db_session=None, main_window=None):
        super().__init__(parent)
        self.node = node
        self.db_session = db_session
        self.main_window = main_window   # сохраняем ссылку
        self.setWindowTitle("Содержимое узла")
        self.resize(800, 600)

        # ====== ИНИЦИАЛИЗАЦИЯ ФЛАГОВ ======
        self._editing_title = False
        self._tab_edit_active = False

        # ====== ВИДЖЕТЫ ======

        # Название
        self.title_label = QLabel(self.node.title)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.title_edit = TitleEditField(self.node.title, self.finish_title_edit)
        self.title_edit.setVisible(False)
        self.title_edit.setStyleSheet("font-size: 18px;")

        self.edit_title_button = QPushButton("✏️")
        self.edit_title_button.setFixedSize(28, 28)
        self.edit_title_button.setToolTip("Изменить название узла")

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self._current_tab_widget = None

        # Кнопка добавления вкладки
        self.add_tab_button = QPushButton("Добавить вкладку")
        #self.add_tab_button.setFixedSize(28, 28)
        self.add_tab_button.setToolTip("Добавить вкладку")

        self.add_tab_menu = QMenu(self)
        self.add_tab_menu.addAction("Текст")
        self.add_tab_menu.addAction("Файлы")
        self.add_tab_menu.addAction("Список")
        self.add_tab_menu.addAction("Список дел")
        self.add_tab_menu.addAction("Даты")

        self.add_tab_button.setMenu(self.add_tab_menu)

        # Обработчики для меню добавления вкладок
        self.add_tab_menu.triggered.connect(self.add_tab)

        # Переменные для отслеживания состояния
        self._previous_tab_widget = None # Виджет предыдущей вкладки, чтобы сохранять данные при переключении
        self._is_saving = False  # Флаг для предотвращения рекурсии при сохранении

        # ====== СБОРКА UI ======
        self._build_ui()

        # ====== СИГНАЛЫ ======
        self.edit_title_button.clicked.connect(self.start_title_edit)
        # TitleEditField уже подключает editingFinished и returnPressed через _on_finish
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.tabBar().tabBarDoubleClicked.connect(self.start_rename_tab)

        # Загрузка существующих вкладок
        for tab in self.node.content.tabs:
            widget = self.create_tab_widget(tab)
            self.tabs.addTab(widget, tab.title)

        # Применяем тему от родительского окна
        self.apply_theme()

        self.finished.connect(lambda: self.save_node_content())

        
    def get_main_window(self):
        """Получить экземпляр MainWindow, обходя родителей"""
        parent = self.parent()
        while parent:
            #if isinstance(parent, MainWindow):
            if hasattr(parent, 'dark_mode') and hasattr(parent, 'scene'):
                return parent
            parent = parent.parent()
        return None

    def apply_theme(self):
        """Применить тему на основе родительского MainWindow"""
        main_window = self.get_main_window()
        if not main_window:
            return

        self.dark_mode = main_window.dark_mode   # <-- СОХРАНЯЕМ ТЕМУ В ДИАЛОГЕ
        dark_mode = main_window.dark_mode if hasattr(main_window, 'dark_mode') else False
        app = QApplication.instance()
    
        # Копируем палитру и стиль приложения (базовые настройки)
        self.setPalette(app.palette())
        self.setStyle(app.style())
    
        # --- ЯВНЫЕ СТИЛИ ДЛЯ ВСЕХ ВИДЖЕТОВ ДИАЛОГА ---
        if dark_mode:
            self.setStyleSheet("""
                NodeContentEditorDialog {
                    background-color: #353535;
                    color: white;
                }
                NodeContentEditorDialog QLabel {
                    color: white;
                    background-color: transparent;
                }
                NodeContentEditorDialog QLineEdit {
                    background-color: #252525;
                    color: white;
                    border: 1px solid #555;
                    padding: 3px;
                }
                NodeContentEditorDialog QTextEdit {
                    background-color: #252525;
                    color: white;
                    border: 1px solid #555;
                }
                NodeContentEditorDialog QListWidget {
                    background-color: #252525;
                    color: white;
                    border: 1px solid #555;
                }
                NodeContentEditorDialog QListWidget::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                NodeContentEditorDialog QPushButton {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #555;
                    padding: 5px;
                    border-radius: 3px;
                }
                NodeContentEditorDialog QPushButton:hover {
                    background-color: #505050;
                }
                NodeContentEditorDialog QPushButton:pressed {
                    background-color: #606060;
                }
                NodeContentEditorDialog QTabWidget::pane {
                    border: 1px solid #555;
                    background-color: #353535;
                }
                NodeContentEditorDialog QTabBar::tab {
                    background-color: #404040;
                    color: white;
                    padding: 8px 15px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                NodeContentEditorDialog QTabBar::tab:selected {
                    background-color: #505050;
                }
                NodeContentEditorDialog QTabBar::tab:hover:!selected {
                    background-color: #454545;
                }
                NodeContentEditorDialog QDateEdit {
                    background-color: #252525;
                    color: white;
                    border: 1px solid #555;
                    padding: 3px;
                }
                
                NodeContentEditorDialog QMenu {
                    background-color: #353535;
                    color: white;
                    border: 1px solid #555;
                }
                NodeContentEditorDialog QMenu::item:selected {
                    background-color: #2a82da;
                }
            """)
        else:
            self.setStyleSheet("""
                NodeContentEditorDialog {
                    background-color: #f5f5f5;
                    color: black;
                }
                NodeContentEditorDialog QLabel {
                    color: black;
                    background-color: transparent;
                }
                NodeContentEditorDialog QLineEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 3px;
                }
                NodeContentEditorDialog QTextEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                }
                NodeContentEditorDialog QListWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                }
                NodeContentEditorDialog QListWidget::item:selected {
                    background-color: #e0e0e0;
                    color: black;
                }
                NodeContentEditorDialog QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                NodeContentEditorDialog QPushButton:hover {
                    background-color: #e0e0e0;
                }
                NodeContentEditorDialog QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                NodeContentEditorDialog QTabWidget::pane {
                    border: 1px solid #ccc;
                    background-color: #f5f5f5;
                }
                NodeContentEditorDialog QTabBar::tab {
                    background-color: #e0e0e0;
                    color: black;
                    padding: 8px 15px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                NodeContentEditorDialog QTabBar::tab:selected {
                    background-color: #d0d0d0;
                }
                NodeContentEditorDialog QTabBar::tab:hover:!selected {
                    background-color: #d0d0d0;
                }
                NodeContentEditorDialog QDateEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 3px;
                }
                
                NodeContentEditorDialog QMenu {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                }
                NodeContentEditorDialog QMenu::item:selected {
                    background-color: #e0e0e0;
                }
           """)
        # Обновляем тему во всех вкладках
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, 'refresh_theme'):
                widget.refresh_theme()
                

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.update()
        # Принудительно обновляем геометрию и перерисовываем
        self.update()
        self.repaint()
        QApplication.processEvents()
    

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Шапка ---
        header_layout = QHBoxLayout()

        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.title_edit)
        title_layout.addWidget(self.edit_title_button)

        header_layout.addWidget(title_container)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # --- Панель вкладок + кнопка ---
        tabs_header = QHBoxLayout()
        tabs_header.addStretch()
        tabs_header.addWidget(self.add_tab_button)

        main_layout.addLayout(tabs_header)
        main_layout.addWidget(self.tabs)

        # Контекстное меню вкладок
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.on_tab_context_menu)
        
        # Установим event filter для перехвата кликов
        self.tabs.installEventFilter(self)

    # ====== ЛОГИКА ======

    def start_title_edit(self):
        # Логика переключения: если поле видно - закрыть его, если скрыто - открыть
        if self.title_edit.isVisible():
            # Поле видно - сохранить и закрыть
            self.finish_title_edit()
        else:
            # Поле скрыто - открыть для редактирования
            self.title_label.setVisible(False)
            self.title_edit.setVisible(True)
            self._editing_title = True
            self.title_edit.setText(self.node.title)
            self.title_edit.setFocus()
            # Выделяем текст в отдельном вызове после setFocus
            QTimer.singleShot(0, self.title_edit.selectAll)

    # Сохранение нового названия узла
    def finish_title_edit(self, save=True):
        # Проверяем флаг, чтобы не обрабатывать дважды
        if not hasattr(self, "_editing_title") or not self._editing_title:
            # Если не в режиме редактирования, просто скрыть поле
            self.title_edit.setVisible(False)
            self.title_label.setVisible(True)
            return
        
        self._editing_title = False
        
        if save:
            new_title = self.title_edit.text().strip()
            if new_title:
                if new_title != self.node.title:
                    self.node.title = new_title
                    self.title_label.setText(new_title)

                    # --- СОХРАНЕНИЕ В БД ---
                    try:
                        #parent = cast(MainWindow, self.parent())
                        #parent.db_session.update_node_title(self.node.id, new_title)
                        if self.main_window:
                            self.main_window.db_session.update_node_title(self.node.id, new_title)
                        
                        # Обновляем название в сцене
                        node_item = self.main_window.scene.nodes.get(self.node.id)
                        if node_item:
                            node_item.title = new_title
                            node_item.update_appearance()
                            
                    except Exception as e:
                        print("Ошибка сохранения названия узла:", e)
                else:
                    # Название не изменилось - просто обновляем label
                    self.title_label.setText(self.node.title)
        else:
            # Отмена - восстанавливаем исходное название
            self.title_label.setText(self.node.title)

        # Скрываем поле редактирования и показываем label
        self.title_edit.setVisible(False)
        self.title_label.setVisible(True)

    def start_rename_tab(self, index):
        if index < 0:
            return

        # Проверяем, может ли быть максимально одно поле редактирования одновременно
        # Если уже открыто другое поле - закрыть его
        existing_edit = getattr(self, "_tab_rename_edit", None)
        if existing_edit is not None:
            self.finish_rename_tab()

        tab_bar = self.tabs.tabBar()
        rect = tab_bar.tabRect(index)

        # Создаем поле редактирования
        self._tab_rename_edit = TabRenameEditField(self.tabs.tabText(index), self.finish_rename_tab, tab_bar)
        self._tab_rename_edit.setGeometry(rect)
        self._tab_rename_edit.show()
        self._tab_rename_edit.setFocus()
        # Выделяем текст в отдельном вызове после setFocus
        QTimer.singleShot(0, self._tab_rename_edit.selectAll)

        self._renaming_tab_index = index
        self._tab_edit_active = True

    def finish_rename_tab(self, save=True):
        # Проверяем флаг, чтобы не обрабатывать дважды
        if not getattr(self, "_tab_edit_active", False):
            return
            
        self._tab_edit_active = False
        
        edit = getattr(self, "_tab_rename_edit", None)
        if edit is None:
            return

        # Сохраняем данные ДО удаления виджета
        if save:
            new_title = edit.text().strip()
            index = self._renaming_tab_index

            if new_title:
                self.tabs.setTabText(index, new_title)

                widget = self.tabs.widget(index)
                tab = getattr(widget, "_content_tab", None)
                if tab:
                    if tab.title != new_title:  # Только если название действительно изменилось
                        # Используем сервис для переименования
                        ContentService.rename_tab(self.node.content, tab.tab_id, new_title)
                        # Сохраняем изменение в БД
                        print(f"Сохраняю изменение названия вкладки: {new_title}")
                        self.save_node_content()

        # Удаляем редактор
        if edit:
            edit.blockSignals(True)  # Блокируем сигналы перед удалением
            edit.hide()
            edit.deleteLater()
        if hasattr(self, "_tab_rename_edit"):
            del self._tab_rename_edit

    def add_tab(self, action):
        """Добавление новой вкладки"""
        tab_type_map = {
            "Текст": ContentTabType.TEXT,
            "Файлы": ContentTabType.FILES,
            "Список": ContentTabType.LIST,
            "Список дел": ContentTabType.TODO,
            "Даты": ContentTabType.DATES,
        }

        tab_type = tab_type_map.get(action.text())
        if not tab_type:
            return

        tab = ContentService.add_tab(self.node.content, tab_type) 

        #if tab not in self.node.content.tabs:
        #    self.node.content.tabs.append(tab)

        widget = self.create_tab_widget(tab)
        index = self.tabs.addTab(widget, tab.title)
        self.tabs.setCurrentIndex(index)

        # Применяем тему к новой вкладке
        if hasattr(widget, 'refresh_theme'):
            widget.refresh_theme()

        self.save_node_content()

    # Создание UI для вкладки (фабрика)
    def create_tab_widget(self, tab: ContentTab):
        node_content = self.node.content   # объект NodeContent
        if tab.tab_type == ContentTabType.TEXT:
            widget = TextTabWidget(node_content, tab)
        elif tab.tab_type == ContentTabType.LIST:
            widget = ListTabWidget(node_content, tab)
        elif tab.tab_type == ContentTabType.TODO:
            widget = TodoTabWidget(node_content, tab)
        elif tab.tab_type == ContentTabType.DATES:
            widget = DatesTabWidget(node_content, tab)
        elif tab.tab_type == ContentTabType.FILES:
            widget = FilesTabWidget(node_content, tab)
        else:
            widget = QLabel(f"{tab.tab_type.value} — в разработке")

        # Привяжем объект ContentTab к виджету, чтобы можно было сохранять/удалять
        try:
            widget._content_tab = tab
        except Exception:
            pass

        return widget
    

    # Улучшенная версия сохранения с поддержкой флага "грязности" и специализированных виджетов
    def save_node_content(self):
        if self._is_saving:
            return

        self._is_saving = True
        try:
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)

                if hasattr(widget, "is_dirty") and widget.is_dirty():
                    print(f"🟡 save_node_content: вкладка {i} грязная → сохраняю")
                    widget.save_to_model()
                else:
                    print(f"⚪ save_node_content: вкладка {i} чистая")

            ContentRepository.save(self.node.content, self.db_session)
            print("💾 save_node_content: данные узла сохранены")

        except Exception as e:
            print("❌ Ошибка сохранения содержимого узла:", e)

        finally:
            self._is_saving = False

    # Обработка смены вкладки
    # Обработка событий
    def eventFilter(self, obj, event):
        """Перехватываем клики внутри QTabWidget для завершения редактирования"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent
        
        if obj == self.tabs and event.type() == QEvent.Type.MouseButtonPress:
            # Если идет редактирование вкладки - проверим, кликнули ли на сам редактор
            if getattr(self, "_tab_edit_active", False):
                edit = getattr(self, "_tab_rename_edit", None)
                if edit and isinstance(event, QMouseEvent):
                    # Получаем координаты клика в системе координат редактора
                    editor_rect = edit.geometry()
                    click_pos = event.pos()
                    
                    # Если клик вне редактора - завершить редактирование
                    if not editor_rect.contains(click_pos):
                        self.finish_rename_tab(save=True)
        
        return super().eventFilter(obj, event)

    # Обработка смены вкладки
    def on_tab_changed(self, index):
        if self._previous_tab_widget and hasattr(self._previous_tab_widget, "on_deactivate"):
            print("🔄 Переключение вкладки: деактивация предыдущей вкладки")
            self._previous_tab_widget.on_deactivate()

        self._previous_tab_widget = self.tabs.widget(index)

    # Контекстное меню вкладок
    def on_tab_context_menu(self, pos):
        index = self.tabs.tabBar().tabAt(pos)
        if index < 0:
            return

        menu = QMenu(self)
        rename_action = menu.addAction("Переименовать")
        delete_action = menu.addAction("Удалить")

        action = menu.exec(self.tabs.mapToGlobal(pos))
        if action == rename_action:
            self.start_rename_tab(index)
        elif action == delete_action:
            self.confirm_delete_tab(index)

    # Подтверждение удаления вкладки
    def confirm_delete_tab(self, index):
        reply = QMessageBox.question(
            self,
            "Удаление вкладки",
            "Удалить вкладку без возможности восстановления?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_tab(index)

    # Удаление вкладки + сохранение
    def delete_tab(self, index):
        widget = self.tabs.widget(index)
        tab = getattr(widget, "_content_tab", None)

        # Если это вкладка с файлами — сначала удаляем все её файлы с диска
        if isinstance(widget, FilesTabWidget):
            widget.delete_all_files()

        self.tabs.removeTab(index)

        if tab:
            ContentService.remove_tab(self.node.content, tab.tab_id)
            self.save_node_content()

    # Сохранение перед закрытием
    def closeEvent(self, event):
        self.save_node_content()
        super().closeEvent(event)