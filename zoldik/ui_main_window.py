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
print("ui_main_window.py loaded")
import sys
from pathlib import Path
from typing import Optional, cast
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

from ui.graph_scene import GraphScene, GraphView

from core import (
    FileService, ContentService, ContentRepository, GraphService,
    DatabaseManager, EncryptedSQLite, ContentTab, Node, 
    Edge, LineType, NodeContent, ContentTabType
)
from ui import (
    NodeContentEditorDialog, set_dark_mode, get_stylesheet,
    is_dark_mode
)



class PasswordDialog(QDialog):
    """Диалог ввода пароля"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print("PasswordDialog.__init__ start")
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
        print("PasswordDialog.__init__ end")
    
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
        print("MainWindow.__init__ start")
        super().__init__()
        
        # Инициализация
        self.db_manager = None
        self.db_session = None
        self.current_file = None
        self.password = None

        self._login_shown = False

        self.last_node_pos = (0, 0)

        self.graph_service = GraphService(self.db_session)

        # Инициализация сервиса для работы с файлами
        self.file_service = FileService()
        
        # Настройки - загружаем из конфига
        self.dark_mode = self.load_theme_setting()
        
        # Запуск
        self.init_ui()
        # Применяем сохраненную тему при инициализации (всегда, с задержкой)
        QTimer.singleShot(50, self.apply_theme)
        self.show_login_dialog()
        print("MainWindow.__init__ end")
    
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
        #print("show_login_dialog: start")
        #dialog = PasswordDialog(self)
        #print("show_login_dialog: dialog created")
        #result = dialog.exec()
        #print(f"show_login_dialog: dialog.exec() returned {result}")
        #if result == QDialog.DialogCode.Accepted:
        #    self.password = dialog.get_password()
        #    print("show_login_dialog: accepted, calling init_database")
        #    self.init_database()
        #    if dialog.get_remember():
        #        print("show_login_dialog: remember checked")
        #else:
        #    print("show_login_dialog: rejected, quitting")
        #    QApplication.quit()
        #print("show_login_dialog: end")
        #dialog = PasswordDialog(self)
        
        # Пробуем загрузить сохраненный пароль
        #try:
        #    settings_path = Path("data/settings.json")
        #    if settings_path.exists():
        #        import json
        #        with open(settings_path, 'r', encoding='utf-8') as f:
        #            settings = json.load(f)
        #            if 'remember_password' in settings and settings['remember_password']:
                        # TODO: Безопасное хранение пароля
        #                pass
        #except:
        #    pass
        
        #if dialog.exec() == QDialog.DialogCode.Accepted:
        #    self.password = dialog.get_password()
        #    self.init_database()
            
        #    if dialog.get_remember():
        #        # TODO: Сохранить настройку
        #        pass
        #else:
        #    QApplication.quit()
        if self._login_shown:
            return
        self._login_shown = True
        print("show_login_dialog: start")
        dialog = PasswordDialog(self)
        print("show_login_dialog: dialog created")
        result = dialog.exec()
        print(f"show_login_dialog: dialog.exec() returned {result}")
        if result == QDialog.DialogCode.Accepted:
            self.password = dialog.get_password()
            print("show_login_dialog: accepted, calling init_database")
            self.init_database()
            if dialog.get_remember():
                # TODO: Сохранить настройку
                print("show_login_dialog: remember checked")
        else:
            print("show_login_dialog: rejected, quitting")
            QApplication.quit()
        print("show_login_dialog: end")
    
    def init_database(self):
        """Инициализация базы данных"""
        print("init_database start")
        try:
            self.db_manager = DatabaseManager(password=self.password)
            self.db_session = self.db_manager.get_session()
            self.db_session.connect()
            
            # Создаем корневой узел если его нет
            root_node = self.db_session.create_root_node()
            
            # Инициализируем сервис графа (теперь db_session существует)
            self.graph_service = GraphService(self.db_session)

            # Загружаем данные
            self.load_data()
            
            self.status_bar.showMessage("База данных загружена")
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", 
                f"Не удалось загрузить базу данных: {str(e)}"
            )
            QApplication.quit()
            print("init_database end")
    
    def load_data(self):
        """Загрузка данных из БД"""
        # Очищаем сцену
        self.scene.clear()
        self.scene.nodes.clear()
        self.scene.edges.clear()
        
        # Загружаем узлы
        nodes = self.graph_service.get_all_nodes()
        if nodes:
            last = max(nodes, key=lambda n: n.id)
            self.last_node_pos = (last.position_x, last.position_y)
        node_items = {}
        
        for node in nodes:
            node_item = self.scene.add_node(
                node.id, node.title, 
                node.position_x, node.position_y,
                node.color
            )
            node_items[node.id] = node_item
        
        # Загружаем связи
        edges = self.graph_service.get_all_edges()
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
            if not hasattr(self, 'last_node_pos'):
                self.last_node_pos = (0, 0)
        
            if self.last_node_pos == (0, 0) and not self.graph_service.get_all_nodes():
                # Если узлов нет – ставим в центр экрана с привязкой к сетке
                viewport_rect = self.view.viewport().rect()
                center = self.view.mapToScene(viewport_rect.center())
                x, y = self.snap_to_grid(center.x(), center.y())
            else:
                # Берем последнюю позицию и смещаем вниз на одну ячейку
                x, y = self.last_node_pos
                y += self.scene.grid_size
                x, y = self.snap_to_grid(x, y)
        
            node = self.graph_service.add_node(text, None, x, y)
            if node:
                self.scene.add_node(node.id, node.title, x, y, node.color)
                self.last_node_pos = (x, y)
    
    def add_node_at_position(self, x: float, y: float):
        """Добавление узла в указанной позиции"""
        text, ok = QInputDialog.getText(
            self, "Новый узел", "Введите название узла:"
        )
        if ok and text:
            x, y = self.snap_to_grid(x, y)
            node = self.graph_service.add_node(text, None, x, y)
            if node:
                self.scene.add_node(node.id, node.title, x, y, node.color)
                self.last_node_pos = (x, y)
    
    def add_child_node(self, parent_id: int, title: str, x: float, y: float):
        """Добавление дочернего узла"""
        print(f"DEBUG add_child_node: parent_id={parent_id}, title={title}, original x={x}, y={y}")
        print(f"DEBUG scene.nodes keys: {list(self.scene.nodes.keys())}")
    
        try:
            parent_item = self.scene.nodes.get(parent_id)
            if not parent_item:
                print(f"ОШИБКА: родительский узел {parent_id} не найден в сцене")
                return None
        
            # Позиция родителя
            parent_x = parent_item.pos().x()
            parent_y = parent_item.pos().y()
            # Размер ячейки сетки (должен быть определен в GraphScene)
            grid = self.scene.grid_size
        
            # Вычисляем позицию дочернего узла: по X как у родителя, по Y + 2 ячейки
            child_x = round(parent_x / grid) * grid
            child_y = round((parent_y + 2 * grid) / grid) * grid
        
            # Создаём узел в БД
        #     node = self.db_session.add_node(title, parent_id, child_x, child_y)
        #     if not node:
        #         print("ОШИБКА: не удалось создать узел в БД")
        #         return None
        
        #     # Добавляем узел на сцену (один раз!)
        #     node_item = self.scene.add_node(node.id, node.title, child_x, child_y, node.color)
        
        #     # Создаём связь в БД
        #     edge = self.db_session.add_edge(parent_id, node.id)
        #     if edge is None:
        #         print(f"ОШИБКА: Не удалось создать связь в БД между {parent_id} и {node.id}")
        #         return None
        
        #     # Добавляем связь на сцену
        #     edge_item = self.scene.add_edge(edge.id, parent_id, node.id)
        #     if edge_item is None:
        #         print(f"ОШИБКА: EdgeItem не создан для связи {edge.id}")
        #         print(f"  from_node_id={parent_id}, to_node_id={node.id}")
        #         print(f"  from_item exists: {parent_id in self.scene.nodes}")
        #         print(f"  to_item exists: {node.id in self.scene.nodes}")
        #         from_item = self.scene.nodes.get(parent_id)
        #         to_item = self.scene.nodes.get(node.id)
        #         print(f"  from_item: {from_item}")
        #         print(f"  to_item: {to_item}")
        
        #     # Обновляем флаг наличия детей у родителя
        #     parent_item.set_has_children(True)
        
        #     # Сохраняем позицию для последующих корневых узлов (опционально)
        #     self.last_node_pos = (child_x, child_y)
        
        #     print(f"Дочерний узел {node.id} создан на позиции ({child_x}, {child_y})")
        #     return node_item
        
        # except Exception as e:
        #     print(f"Ошибка при создании дочернего узла: {e}")
        #     import traceback
        #     traceback.print_exc()
        #     return None
            node, edge = self.graph_service.add_child_node(parent_id, title, child_x, child_y)

            node_item = self.scene.add_node(node.id, node.title, child_x, child_y, node.color)
            edge_item = self.scene.add_edge(edge.id, parent_id, node.id)

            if edge_item is None:
                print(f"ОШИБКА: EdgeItem не создан для связи {edge.id}")

            parent_item.set_has_children(True)
            self.last_node_pos = (child_x, child_y)

            print(f"Дочерний узел {node.id} создан на позиции ({child_x}, {child_y})")
            return node_item

        except Exception as e:
            print(f"Ошибка при создании дочернего узла: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def snap_to_grid(self, x: float, y: float) -> tuple[float, float]:
        """Округляет координаты до ближайшего узла сетки"""
        grid = self.scene.grid_size
        return (round(x / grid) * grid, round(y / grid) * grid)
    
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
                node = self.graph_service.get_node(node_id)
                if not node:
                    print(f"Узел {node_id} не найден в БД")
                    return
            
                parent_id = node.parent_id
                # 2. Получаем ВСЕХ потомков узла (рекурсивно)
                # try:
                #     # Пробуем рекурсивный метод
                #     all_descendants = self.db_session.get_all_descendants(node_id)
                # except RecursionError:
                # # Если слишком глубокая рекурсия, используем итеративный
                #     all_descendants = self.db_session.get_all_descendants_iterative(node_id)
                deleted_nodes, deleted_edges = self.graph_service.delete_node(node_id)
            
                print(f"Удаляемые узлы: {deleted_nodes}")
                print(f"Количество удаляемых узлов: {len(deleted_nodes)}")
                print(f"Удаляемые связи: {deleted_edges}")
            
            #     # 3. Удаляем узел из БД (потомки удалятся каскадно благодаря ON DELETE CASCADE)
            #     self.db_session.delete_node(node_id)
            #     print(f"Узел {node_id} и все его потомки удалены из БД")
            #     # 3.1 Удаляем папки attachments всех удаляемых узлов
            #     for descendant_id in all_descendants:
            #         try:
            #             self.file_service.delete_node_folder(descendant_id)
            #         except Exception as e:
            #             print(f"Ошибка удаления папки узла {descendant_id}: {e}")

            #     # 4. Удаляем все связи и узлы из сцены
            #     # 4.1. Собираем все связи, которые нужно удалить
            #     edges_to_delete = []
            #     for edge_id, edge_item in list(self.scene.edges.items()):
            #         try:
            #             # Проверяем, связана ли связь с любым из удаляемых узлов
            #             if (edge_item.from_item.node_id in all_descendants or 
            #                 edge_item.to_item.node_id in all_descendants):
            #                 edges_to_delete.append(edge_id)
            #         except AttributeError:
            #             continue
            
            #     print(f"Удаляемые связи: {edges_to_delete}")
            
            #     # 4.2. Удаляем связи
            #     for edge_id in edges_to_delete:
            #         edge_item = self.scene.edges.pop(edge_id, None)
            #         if edge_item:
            #             self.scene.removeItem(edge_item)
            #             print(f"Удалена связь {edge_id}")
            
            #     # 4.3. Удаляем все узлы (включая потомков)
            #     for descendant_id in all_descendants:
            #         node_item = self.scene.nodes.get(descendant_id)
            #         if node_item:
            #             self.scene.removeItem(node_item)
            #             del self.scene.nodes[descendant_id]
            #             print(f"Удален узел {descendant_id} из сцены")
            
            #     # 5. Обновляем родительский узел (если он не был удален)
            #     if parent_id and parent_id not in all_descendants:
            #         # Проверяем, остались ли у родителя другие дети
            #         remaining_children = self.db_session.get_children(parent_id)
            #         has_children_remaining = len(remaining_children) > 0
                
            #         parent_item = self.scene.nodes.get(parent_id)
            #         if parent_item:
            #             parent_item.set_has_children(has_children_remaining)
            #             print(f"Родительский узел {parent_id} обновлен, has_children={has_children_remaining}")
            
            #     print(f"=== РЕКУРСИВНОЕ УДАЛЕНИЕ УЗЛА {node_id} ЗАВЕРШЕНО ===\n")
            
            # except Exception as e:
            #     print(f"КРИТИЧЕСКАЯ ОШИБКА при рекурсивном удалении узла {node_id}: {e}")
            #     import traceback
            #     traceback.print_exc()
            
            #     QMessageBox.critical(
            #         self, "Ошибка удаления",
            #         f"Не удалось удалить узел и всех его потомков:\n{str(e)}"
            #     )

                # Удаляем связи со сцены
                for edge_id in deleted_edges:
                    self.scene.remove_edge(edge_id)

                # Удаляем узлы со сцены
                for nid in deleted_nodes:
                    node_item = self.scene.nodes.get(nid)
                    if node_item:
                        self.scene.removeItem(node_item)
                        del self.scene.nodes[nid]
                        print(f"Удален узел {nid} из сцены")

                # Обновляем родительский узел (если он не был удалён)
                if parent_id and parent_id not in deleted_nodes:
                    remaining_children = self.graph_service.get_children(parent_id)
                    has_children = len(remaining_children) > 0
                    parent_item = self.scene.nodes.get(parent_id)
                    if parent_item:
                        parent_item.set_has_children(has_children)
                        print(f"Родительский узел {parent_id} обновлен, has_children={has_children}")

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
        self.graph_service.delete_edge(edge_id)
        self.scene.delete_edge(edge_id)
    
    def update_node_position(self, node_id: int, x: float, y: float):
        """Обновление позиции узла"""
        self.graph_service.update_node_position(node_id, x, y)
    
    def update_node_color(self, node_id: int, color: str):
        """Обновление цвета узла"""
        self.graph_service.update_node_color(node_id, color)
    
    def toggle_node_collapsed(self, node_id: int, collapsed: bool):
        """Переключение состояния свернутоности узла"""
        self.graph_service.toggle_node_collapsed(node_id)
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
        node = self.graph_service.get_node(node_id)

        if node.content is None:
            node.content = NodeContent(node_id=node.id)

        dialog = NodeContentEditorDialog(
            node,
            self,
            self.db_session,
            main_window=self
            )
        dialog.exec()
    
    def save_data(self):
        """Сохранение данных"""
        try:
            #self.db_session.conn.commit()
            self.graph_service.commit()
            self.status_bar.showMessage("Данные сохранены", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить данных: {str(e)}")
    
    def autosave(self):
        """Автосохранение"""
        #if self.db_session:
        if hasattr(self, 'graph_service') and self.graph_service:
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
        set_dark_mode(self.dark_mode)

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
            # Фон сцены для темной темы
            self.scene.setBackgroundBrush(QColor(45, 45, 45))
            self.theme_action.setText("☀️ Светлая тема")
        
        else:
            # СВЕТЛАЯ ТЕМА
            # Восстанавливаем стандартную палитру Fusion
            app.setPalette(app.style().standardPalette())
        
            # Фон сцены для светлой темы
            self.scene.setBackgroundBrush(QColor(245, 245, 245))
            self.theme_action.setText("🌙 Темная тема")

        # Загружаем стили из .qss файла
        stylesheet = get_stylesheet()
        app.setStyleSheet(stylesheet)
        # Обновляем все виджеты
        #self.update_all_dialogs_theme()
        app.processEvents()
        self.update()
        
    
    # def closeEvent(self, event):
    #     """Обработка закрытия окна"""
    #     self.save_data()
        
    #     if self.db_session:
    #         self.db_session.close()
        
    #     event.accept()
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.save_data()
        if hasattr(self, 'graph_service') and self.graph_service:
            self.graph_service.close()
        event.accept()

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


    