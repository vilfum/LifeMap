"""
========================================================================
ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ "КАРТА ЖИЗНИ"
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
from typing import Optional, cast
import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QToolBar, QStatusBar, QMessageBox, QInputDialog,
    QApplication, QSplitter, QFileDialog, QDialog, QLabel,
    QLineEdit, QPushButton, QCheckBox, QTabWidget, QMenu, QTextEdit, QListWidget,
    QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QPointF, QRectF
from PyQt6.QtGui import QIcon, QKeySequence, QPalette, QColor, QAction, QPixmap, QPainter, QBrush

from ui_graph_scene import GraphScene, GraphView
from database import DatabaseManager, EncryptedSQLite
from models import ContentTab, Node, Edge, LineType, NodeContent, ContentTabType


class PasswordDialog(QDialog):
    """Диалог ввода пароля"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Карта жизни - Ввод пароля")
        self.setModal(True)
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        # Информация
        info_label = QLabel("Введите пароль для доступа к карте жизни")
        layout.addWidget(info_label)
        
        # Поле пароля
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_edit)
        
        # Чекбокс запомнить
        self.remember_check = QCheckBox("Запомнить пароль")
        layout.addWidget(self.remember_check)
        
        # Кнопки
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Отмена")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_password(self) -> str:
        """Получение введенного пароля"""
        return self.password_edit.text()
    
    def get_remember(self) -> bool:
        """Получение состояния чекбокса"""
        return self.remember_check.isChecked()


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    CONFIG_FILE = Path("data/config.json")
    
    def __init__(self):
        super().__init__()
        
        # Инициализация
        self.db_manager = None
        self.db_session = None
        self.current_file = None
        self.password = None
        
        # Настройки - загружаем из конфига
        self.dark_mode = self.load_theme_setting()
        
        # Запуск
        self.init_ui()
        # Применяем сохраненную тему при инициализации (всегда, с задержкой)
        QTimer.singleShot(50, self.apply_theme)
        self.show_login_dialog()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Карта жизни")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        main_layout.setSpacing(0)
        
        # Создаем сцену и вид
        self.scene = GraphScene()
        self.view = GraphView(self.scene)

        # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ДЛЯ УДАЛЕНИЯ ГРАНИЦ:
        #self.view.setStyleSheet("""
        #    QGraphicsView {
        #        border: 0px;
        #        padding: 0px;
        #        margin: 0px;
        #        outline: none;
        #        background: transparent;
        #    }
        #    QGraphicsView:focus {
        #        border: 0px;
        #        outline: none;
        #    }
        #""")
        
        # Подключаем сигналы сцены
        self.scene.nodeDoubleClicked.connect(self.open_node_editor)
        self.scene.nodePositionChanged.connect(self.update_node_position)
        self.scene.nodeCollapsedChanged.connect(self.toggle_node_collapsed)
        self.scene.nodeColorChanged.connect(self.update_node_color)
        self.scene.addNodeRequested.connect(self.add_node_at_position)
        self.scene.addChildNodeRequested.connect(self.add_child_node)
        self.scene.deleteNodeRequested.connect(self.delete_node)
        self.scene.deleteEdgeRequested.connect(self.delete_edge)
        
        # Добавляем вид в layout
        main_layout.addWidget(self.view)
        
        # Создаем тулбар
        self.create_toolbar()
        
        # Создаем статусбар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")
        
        # Таймер автосохранения (каждые 30 секунд)
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)  # 30 секунд
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar("Основные инструменты")
        self.addToolBar(toolbar)
        
        # Действия
        # Новый узел
        new_node_action = QAction("➕ Новый узел", self)
        new_node_action.setShortcut(QKeySequence("Ctrl+N"))
        new_node_action.triggered.connect(self.add_root_node)
        toolbar.addAction(new_node_action)
        
        toolbar.addSeparator()
        
        # Сохранить
        save_action = QAction("💾 Сохранить", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_data)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Масштабирование
        zoom_in_action = QAction("🔍 Увеличить", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.view.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍 Уменьшить", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.view.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("🔍 Сбросить", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(self.view.reset_zoom)
        toolbar.addAction(reset_zoom_action)
        
        toolbar.addSeparator()
        
        # Свернуть/развернуть все
        collapse_all_action = QAction("▼ Свернуть все", self)
        collapse_all_action.triggered.connect(self.collapse_all_nodes)
        toolbar.addAction(collapse_all_action)
        
        expand_all_action = QAction("▲ Развернуть все", self)
        expand_all_action.triggered.connect(self.expand_all_nodes)
        toolbar.addAction(expand_all_action)
        
        toolbar.addSeparator()
        
        # Темная/светлая тема
        self.theme_action = QAction("🌙 Темная тема", self)
        self.theme_action.setCheckable(True)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)
    
    def show_login_dialog(self):
        """Показать диалог входа"""
        dialog = PasswordDialog(self)
        
        # Пробуем загрузить сохраненный пароль
        try:
            settings_path = Path("data/settings.json")
            if settings_path.exists():
                import json
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if 'remember_password' in settings and settings['remember_password']:
                        # TODO: Безопасное хранение пароля
                        pass
        except:
            pass
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.password = dialog.get_password()
            self.init_database()
            
            if dialog.get_remember():
                # TODO: Сохранить настройку
                pass
        else:
            QApplication.quit()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            self.db_manager = DatabaseManager(password=self.password)
            self.db_session = self.db_manager.get_session()
            self.db_session.connect()
            
            # Создаем корневой узел если его нет
            root_node = self.db_session.create_root_node()
            
            # Загружаем данные
            self.load_data()
            
            self.status_bar.showMessage("База данных загружена")
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", 
                f"Не удалось загрузить базу данных: {str(e)}"
            )
            QApplication.quit()
    
    def load_data(self):
        """Загрузка данных из БД"""
        # Очищаем сцену
        self.scene.clear()
        self.scene.nodes.clear()
        self.scene.edges.clear()
        
        # Загружаем узлы
        nodes = self.db_session.get_all_nodes()
        node_items = {}
        
        for node in nodes:
            node_item = self.scene.add_node(
                node.id, node.title, 
                node.position_x, node.position_y,
                node.color
            )
            node_items[node.id] = node_item
        
        # Загружаем связи
        edges = self.db_session.get_all_edges()
        for edge in edges:
            self.scene.add_edge(
                edge.id, edge.from_node_id, edge.to_node_id,
                edge.line_type, edge.color
            )
        
        # Устанавливаем флаги детей
        for node in nodes:
            if node.parent_id:
                parent_item = self.scene.nodes.get(node.parent_id)
                if parent_item:
                    # TODO: Обновить флаг has_children
                    pass
        
        # Центрируем вид на корневом узле
        if nodes:
            self.view.centerOn(node_items[1] if 1 in node_items else node_items[nodes[0].id])
    
    def add_root_node(self):
        """Добавление корневого узла"""
        text, ok = QInputDialog.getText(
            self, "Новый корневой узел", "Введите название узла:"
        )
        if ok and text:
            node = self.db_session.add_node(text, None, 0, 0)
            self.scene.add_node(node.id, node.title, 0, 0, node.color)
    
    def add_node_at_position(self, x: float, y: float):
        """Добавление узла в указанной позиции"""
        text, ok = QInputDialog.getText(
            self, "Новый узел", "Введите название узла:"
        )
        if ok and text:
            node = self.db_session.add_node(text, None, x, y)
            self.scene.add_node(node.id, node.title, x, y, node.color)
    
    def add_child_node(self, parent_id: int, title: str, x: float, y: float):
        """Добавление дочернего узла"""
        print(f"DEBUG add_child_node: parent_id={parent_id}, title={title}, x={x}, y={y}")
        print(f"DEBUG scene.nodes keys: {list(self.scene.nodes.keys())}")
        try:
            # Создаем узел в БД
            node = self.db_session.add_node(title, parent_id, x, y)
        
            # Создаем графический элемент узла
            node_item = self.scene.add_node(node.id, node.title, x, y, node.color)
        
            # Создаем связь в БД
            edge = self.db_session.add_edge(parent_id, node.id)
            # Проверка
            if edge is None:
                print(f"ОШИБКА: Не удалось создать связь в БД между {parent_id} и {node.id}")
                return None
        
            # Создаем графический элемент связи
            edge_item = self.scene.add_edge(edge.id, parent_id, node.id)
            if edge_item is None:
                print(f"ОШИБКА: EdgeItem не создан для связи {edge.id}")
                print(f"  from_node_id={parent_id}, to_node_id={node.id}")
                print(f"  from_item exists: {parent_id in self.scene.nodes}")
                print(f"  to_item exists: {node.id in self.scene.nodes}")
                # Можно попробовать получить узлы напрямую
                from_item = self.scene.nodes.get(parent_id)
                to_item = self.scene.nodes.get(node.id)
                print(f"  from_item: {from_item}")
                print(f"  to_item: {to_item}")
        
            # ИСПРАВЛЕНИЕ: ОБНОВЛЯЕМ ФЛАГ has_children 
            parent_item = self.scene.nodes.get(parent_id)
            if parent_item:
                parent_item.set_has_children(True)  # Теперь родитель знает, что у него есть дети
            
            return node_item
        
        except Exception as e:
            print(f"Ошибка при создании дочернего узла: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def delete_node(self, node_id: int):
        """Удаление узла и всех его потомков"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить узел и ВСЕ его дочерние узлы (включая внуков и т.д.)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
    
        if reply == QMessageBox.StandardButton.Yes:
            try:
                print(f"=== РЕКУРСИВНОЕ УДАЛЕНИЕ УЗЛА {node_id} ===")
            
                # 1. Получаем информацию об узле до удаления
                node = self.db_session.get_node(node_id)
                if not node:
                    print(f"Узел {node_id} не найден в БД")
                    return
            
                parent_id = node.parent_id
            
                # 2. Получаем ВСЕХ потомков узла (рекурсивно)
                try:
                    # Пробуем рекурсивный метод
                    all_descendants = self.db_session.get_all_descendants(node_id)
                except RecursionError:
                # Если слишком глубокая рекурсия, используем итеративный
                    all_descendants = self.db_session.get_all_descendants_iterative(node_id)
            
                print(f"Удаляемые узлы: {all_descendants}")
                print(f"Количество удаляемых узлов: {len(all_descendants)}")
            
                # 3. Удаляем узел из БД (потомки удалятся каскадно благодаря ON DELETE CASCADE)
                self.db_session.delete_node(node_id)
                print(f"Узел {node_id} и все его потомки удалены из БД")
            
                # 4. Удаляем все связи и узлы из сцены
                # 4.1. Собираем все связи, которые нужно удалить
                edges_to_delete = []
                for edge_id, edge_item in list(self.scene.edges.items()):
                    try:
                        # Проверяем, связана ли связь с любым из удаляемых узлов
                        if (edge_item.from_item.node_id in all_descendants or 
                            edge_item.to_item.node_id in all_descendants):
                            edges_to_delete.append(edge_id)
                    except AttributeError:
                        continue
            
                print(f"Удаляемые связи: {edges_to_delete}")
            
                # 4.2. Удаляем связи
                for edge_id in edges_to_delete:
                    edge_item = self.scene.edges.pop(edge_id, None)
                    if edge_item:
                        self.scene.removeItem(edge_item)
                        print(f"Удалена связь {edge_id}")
            
                # 4.3. Удаляем все узлы (включая потомков)
                for descendant_id in all_descendants:
                    node_item = self.scene.nodes.get(descendant_id)
                    if node_item:
                        self.scene.removeItem(node_item)
                        del self.scene.nodes[descendant_id]
                        print(f"Удален узел {descendant_id} из сцены")
            
                # 5. Обновляем родительский узел (если он не был удален)
                if parent_id and parent_id not in all_descendants:
                    # Проверяем, остались ли у родителя другие дети
                    remaining_children = self.db_session.get_children(parent_id)
                    has_children_remaining = len(remaining_children) > 0
                
                    parent_item = self.scene.nodes.get(parent_id)
                    if parent_item:
                        parent_item.set_has_children(has_children_remaining)
                        print(f"Родительский узел {parent_id} обновлен, has_children={has_children_remaining}")
            
                print(f"=== РЕКУРСИВНОЕ УДАЛЕНИЕ УЗЛА {node_id} ЗАВЕРШЕНО ===\n")
            
            except Exception as e:
                print(f"КРИТИЧЕСКАЯ ОШИБКА при рекурсивном удалении узла {node_id}: {e}")
                import traceback
                traceback.print_exc()
            
                QMessageBox.critical(
                    self, "Ошибка удаления",
                    f"Не удалось удалить узел и всех его потомков:\n{str(e)}"
                )
            
    def delete_edge(self, edge_id: int):
        """Удаление связи"""
        self.db_session.delete_edge(edge_id)
        self.scene.delete_edge(edge_id)
    
    def update_node_position(self, node_id: int, x: float, y: float):
        """Обновление позиции узла"""
        self.db_session.update_node_position(node_id, x, y)
    
    def update_node_color(self, node_id: int, color: str):
        """Обновление цвета узла"""
        self.db_session.update_node_color(node_id, color)
    
    def toggle_node_collapsed(self, node_id: int, collapsed: bool):
        """Переключение состояния свернутоности узла"""
        self.db_session.toggle_node_collapsed(node_id)
        # TODO: Скрыть/показать дочерние узлы
    
    def collapse_all_nodes(self):
        """Свернуть все узлы"""
        # TODO: Реализовать
        pass
    
    def expand_all_nodes(self):
        """Развернуть все узлы"""
        # TODO: Реализовать
        pass
    
    def open_node_editor(self, node_id: int):
        """Открытие редактора узла"""
        node = self.db_session.get_node(node_id)

        if node.content is None:
            node.content = NodeContent(node_id=node.id)

        dialog = NodeContentEditorDialog(node, self, self.db_session)
        dialog.exec()
    
    def save_data(self):
        """Сохранение данных"""
        try:
            self.db_session.conn.commit()
            self.status_bar.showMessage("Данные сохранены", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить данных: {str(e)}")
    
    def autosave(self):
        """Автосохранение"""
        if self.db_session:
            self.save_data()
    
    def toggle_theme(self):
        """Переключение темы и сохранение выбора"""
        self.dark_mode = not self.dark_mode
        self.save_theme_setting(self.dark_mode)
        self.apply_theme()
    
    def apply_theme(self):
        """Применить текущую тему на основе self.dark_mode"""
        # Получаем текущее приложение
        app = QApplication.instance()
    
        if self.dark_mode:
            # ТЕМНАЯ ТЕМА
            # Устанавливаем темную палитру
            dark_palette = QPalette()
        
            # Базовые цвета
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
            # Устанавливаем палитру
            app.setPalette(dark_palette)
        
            # Устанавливаем стиль для темной темы
            app.setStyleSheet("""
                /* Стиль для всех меню в темной теме */
                QMenu {
                    background-color: #353535;
                    border: 1px solid #555555;
                    color: #ffffff;
                    padding: 4px;
                }
            
                QMenu::item {
                    background-color: transparent;
                    padding: 6px 24px 6px 8px;
                    margin: 2px 4px;
                    border-radius: 3px;
                }
            
                QMenu::item:selected {
                    background-color: #2a82da;
                    color: #ffffff;
                }
            
                QMenu::item:disabled {
                    color: #777777;
                }
            
                QMenu::separator {
                    height: 1px;
                    background-color: #555555;
                    margin: 4px 8px;
                }
            
                /* Стиль для панели инструментов в темной теме */
                QToolBar {
                    background-color: #2b2b2b;
                    border: none;
                    spacing: 3px;
                    padding: 2px;
                }
            
                QToolBar QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    padding: 4px;
                    color: #ffffff;
                }
            
                QToolBar QToolButton:hover {
                    background-color: #404040;
                    border: 1px solid #505050;
                }
            
                QToolBar QToolButton:pressed {
                    background-color: #505050;
                }
            
                /* Стиль для статусбара */
                QStatusBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
            
                /* Стиль для QGraphicsView */
                QGraphicsView {
                    border: 0px;
                    outline: 0px;
                    background: transparent;
                }
            
                QGraphicsView::rubberBand {
                    border: 2px dashed #2196F3;
                    background-color: rgba(33, 150, 243, 30);
                }
            """)
        
            # Фон сцены для темной темы
            self.scene.setBackgroundBrush(QColor(45, 45, 45))
            self.theme_action.setText("☀️ Светлая тема")
        
        else:
            # СВЕТЛАЯ ТЕМА
            # Восстанавливаем стандартную палитру Fusion
            app.setPalette(app.style().standardPalette())
        
            # Устанавливаем стиль для светлой темы
            app.setStyleSheet("""
                /* Стиль для всех меню в светлой теме */
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    color: #333333;
                    padding: 4px;
                }
            
                QMenu::item {
                    background-color: transparent;
                    padding: 6px 24px 6px 8px;
                    margin: 2px 4px;
                    border-radius: 3px;
                }
            
                QMenu::item:selected {
                    background-color: #e0e0e0;
                    color: #000000;
                }
            
                QMenu::item:disabled {
                    color: #999999;
                }
            
                QMenu::separator {
                    height: 1px;
                    background-color: #dddddd;
                    margin: 4px 8px;
                }
            
                /* Стиль для панели инструментов в светлой теме */
                QToolBar {
                    background-color: #f0f0f0;
                    border: none;
                    spacing: 3px;
                    padding: 2px;
                }
            
                QToolBar QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    padding: 4px;
                    color: #333333;
                }
            
                QToolBar QToolButton:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #d0d0d0;
                }
            
                QToolBar QToolButton:pressed {
                    background-color: #d0d0d0;
                }
            
                /* Стиль для статусбара */
                QStatusBar {
                    background-color: #f0f0f0;
                    color: #333333;
                }
            
                /* Стиль для QGraphicsView */
                QGraphicsView {
                    border: 0px;
                    outline: 0px;
                    background: transparent;
                }
            
                QGraphicsView::rubberBand {
                    border: 2px dashed #2196F3;
                    background-color: rgba(33, 150, 243, 30);
                }
            """)
        
            # Фон сцены для светлой темы
            self.scene.setBackgroundBrush(QColor(245, 245, 245))
            self.theme_action.setText("🌙 Темная тема")
    
        # Обновляем все виджеты
        app.processEvents()
        self.update()
        
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.save_data()
        
        if self.db_session:
            self.db_session.close()
        
        event.accept()

    def add_child_node(self, parent_id: int, title: str, x: float, y: float):
        """Добавление дочернего узла"""
        try:
            node = self.db_session.add_node(title, parent_id, x, y)
            node_item = self.scene.add_node(node.id, node.title, x, y, node.color)

             # Добавляем связь
            edge = self.db_session.add_edge(parent_id, node.id)
            self.scene.add_edge(edge.id, parent_id, node.id)
        
            # Обновляем флаг родителя
            parent_item = self.scene.nodes.get(parent_id)
            if parent_item:
                parent_item.set_has_children(True)
            
        except Exception as e:
            print(f"Ошибка при создании дочернего узла: {e}")

    # ====== УПРАВЛЕНИЕ ТЕМОЙ И КОНФИГОМ ======
    
    @staticmethod
    def load_theme_setting() -> bool:
        """Загрузить сохраненную тему из конфига"""
        config_file = MainWindow.CONFIG_FILE
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('dark_mode', False)
        except Exception as e:
            print(f"Ошибка при загрузке конфига: {e}")
        
        # По умолчанию - светлая тема
        return False
    
    @staticmethod
    def save_theme_setting(dark_mode: bool):
        """Сохранить выбранную тему в конфиг"""
        config_file = MainWindow.CONFIG_FILE
        
        try:
            # Создаем папку если не существует
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Загружаем существующий конфиг или создаём новый
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Обновляем значение темы
            config['dark_mode'] = dark_mode
            
            # Сохраняем конфиг
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            print(f"Тема сохранена: {'Темная' if dark_mode else 'Светлая'}")
        except Exception as e:
            print(f"Ошибка при сохранении конфига: {e}")


class BaseTabWidget(QWidget):
    """Контракт для виджетов вкладок узла"""
    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.tab = tab          # данные вкладки
        self._dirty = False     # изменялась ли вкладка
        self.ensure_data()      # гарантируем, что данные вкладки существуют

    # Гарантируем, что data всегда существует
    def ensure_data(self):
        if self.tab.data is None:
            self.tab.data = {}

    def mark_dirty(self):
        if not self._dirty:
            print(f"✏️ BaseTabWidget: вкладка {self.tab.title} стала грязной")
        self._dirty = True

    def is_dirty(self):
        return self._dirty

    def load_from_model(self):
        pass

    def save_to_model(self):
        if not self._dirty:
            return

        html = self.editor.toHtml()
        self.tab.data["html"] = html
        self._dirty = False

        print("✅ TextTabWidget: данные сохранены, вкладка очищена")

    # Вызывается при уходе с вкладки
    def on_deactivate(self):
        if hasattr(self, "is_dirty") and self.is_dirty():
            self.save_to_model()

class TextTabWidget(BaseTabWidget):
    """Виджет для текстовой вкладки"""
    def __init__(self, tab, parent=None):
        super().__init__(tab, parent)

        self.editor = QTextEdit(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)

        # Загружаем содержимое из модели при создании виджета
        try:
            self.load_from_model()
        except Exception:
            pass

        # Подключаем обработчики событий *после* загрузки,
        # чтобы программная установка текста не пометила вкладку как изменённую
        self.editor.textChanged.connect(self.mark_dirty)
        #self.editor.textChanged.connect(self._on_text_changed)

    #def _on_text_changed(self):
    #    self._dirty = True

    # Загрузка текста из узла
    def load_from_model(self):
        html = self.tab.data.get("html", "")
        self.editor.setHtml(html)
        self._dirty = False

    # Сохранение текста в узел
    def save_to_model(self):
        if not self._dirty:
            print("💾 TextTabWidget: нет изменений для сохранения")
            return  # Если нет изменений, не сохраняем
        
        self.tab.data["html"] = self.editor.toHtml()
        super().save_to_model()
        self._dirty = False  # Сбрасываем флаг изменений
        print("💾 TextTabWidget: данные сохранены, вкладка очищена")


class ListTabWidget(BaseTabWidget):
    """Виджет для вкладки со списком"""
    def __init__(self, tab, parent=None):
        super().__init__(tab, parent)
        
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
        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            items.append(item.text())
        
        # Сохраняем в модель вкладки
        self.tab.data["items"] = items
        self._dirty = False  # Сбрасываем флаг изменений
        
        print(f"💾 ListTabWidget: сохранено {len(items)} элементов")


class TodoTabWidget(BaseTabWidget):
    """
    Вкладка TODO:
    - список задач с чекбоксами
    - автосохранение
    """

    def __init__(self, content_tab, parent=None):
        super().__init__(content_tab, parent)
        self.build_ui()
        self.load_from_model()

    # Создание интерфейса
    def build_ui(self):
        layout = QVBoxLayout(self)

        # Список задач
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget)

        # Кнопки управления

        self.add_button = QPushButton("Добавить")
        self.remove_button = QPushButton("Удалить")
        
        # Layout
        layout.addWidget(self.list_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)
        
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

        self.tab.data["items"] = items
        self._dirty = False  # Сбрасываем флаг изменений
        
        print(f"💾 ListTabWidget: сохранено {len(items)} элементов")


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
    def __init__(self, node, parent=None, db_session=None):
        super().__init__(parent)
        self.node = node
        self.db_session = db_session
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
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(28, 28)
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

        self.finished.connect(lambda: self.save_node_content())
        

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
                        parent = cast(MainWindow, self.parent())
                        parent.db_session.update_node_title(self.node.id, new_title)
                        
                        # Обновляем название в сцене
                        node_item = parent.scene.nodes.get(self.node.id)
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
                        tab.title = new_title
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

        tab = self.node.content.add_tab(tab_type)

        if tab not in self.node.content.tabs:
            self.node.content.tabs.append(tab)

        widget = self.create_tab_widget(tab)
        index = self.tabs.addTab(widget, tab.title)
        self.tabs.setCurrentIndex(index)

        self.save_node_content()

    # Создание UI для вкладки (фабрика)
    def create_tab_widget(self, tab: ContentTab):
        if tab.tab_type == ContentTabType.TEXT:
            # Используем специализированный виджет, чтобы отслеживать изменения
            widget = TextTabWidget(tab)
        elif tab.tab_type == ContentTabType.LIST:
            widget = ListTabWidget(tab)
        elif tab.tab_type == ContentTabType.TODO:
            widget = TodoTabWidget(tab) 
        else:
            widget = QLabel(f"{tab.tab_type.value} — в разработке")

        # Привяжем объект ContentTab к виджету, чтобы можно было сохранять/удалять
        try:
            widget._content_tab = tab
        except Exception:
            pass

        return widget
    
    #def save_tab_data(self, widget, tab):
    #    if tab.tab_type == ContentTabType.TEXT:
    #        tab.data['text'] = widget.toPlainText()
    #    elif tab.tab_type == ContentTabType.LIST:
    #        tab.data['items'] = [widget.item(i).text() for i in range(widget.count())]
    
    # Сохранение вкладок узла
    #def save_node_content(self):
    #    try:
    #        # Сохранить данные всех вкладок
    #        for i in range(self.tabs.count()):
    #            widget = self.tabs.widget(i)
    #            tab = getattr(widget, "_content_tab", None)
    #
    #            if hasattr(widget, "is_dirty") and widget.is_dirty():
    #                print(f"🟡 save_node_content: вкладка {i} грязная → сохраняю")
    #                widget.save_to_model()
    #                # Для собственных виджетов типа BaseTabWidget
    #                #widget.save_to_model()
    #            elif isinstance(widget, QTextEdit) and tab is not None:
    #                # Сохраняем plain text в модель
    #                tab.data['text'] = widget.toPlainText()
    #            elif isinstance(widget, QListWidget) and tab is not None:
    #                tab.data['items'] = [widget.item(j).text() for j in range(widget.count())]
    #
    #        # Сохраняем весь контент узла в БД
    #        self.node.content.save(self.db_session)
    #        print("💾 save_node_content: данные узла сохранены")
    #    except Exception as e:
    #        print("Ошибка сохранения содержимого узла:", e)

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

            self.node.content.save(self.db_session)
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

        self.tabs.removeTab(index)

        if tab:
            self.node.content.remove_tab(tab.tab_id)
            self.save_node_content()

    # Сохранение перед закрытием
    def closeEvent(self, event):
        self.save_node_content()
        super().closeEvent(event)

    