"""
========================================================================
БАЗА ДАННЫХ ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfim
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Структура базы данных и алгоритмы шифрования
                 являются интеллектуальной собственностью автора.
========================================================================
"""


"""
Работа с базой данных SQLite с шифрованием
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

from core.models import *


class EncryptedSQLite:
    """SQLite с шифрованием на уровне приложения"""
    
    def __init__(self, db_path: str, password: str = None):
        self.db_path = db_path
        self.password = password
        self.conn = None
        self.cursor = None
        
        # Генерация ключа из пароля
        if password:
            self.key = self._generate_key(password)
        else:
            self.key = None
    
    def _generate_key(self, password: str) -> bytes:
        """Генерация ключа AES из пароля"""
        return hashlib.sha256(password.encode()).digest()
    
    def encrypt_data(self, data: str) -> str:
        """Шифрование данных"""
        if not self.key:
            return data
        
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return json.dumps({'iv': iv, 'ciphertext': ct})
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Дешифрование данных"""
        if not self.key:
            return encrypted_data
        
        try:
            data = json.loads(encrypted_data)
            iv = base64.b64decode(data['iv'])
            ct = base64.b64decode(data['ciphertext'])
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except:
            return encrypted_data
    
    def connect(self):
        """Подключение к базе данных"""
        # Создаем папку если не существует
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Включаем внешние ключи
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
        # Создаем таблицы если они не существуют
        self._create_tables()
    
    def _create_tables(self):
        """Создание таблиц базы данных"""
        
        # Таблица узлов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                parent_id INTEGER,
                color TEXT DEFAULT '#3498db',
                position_x REAL DEFAULT 0,
                position_y REAL DEFAULT 0,
                collapsed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES nodes (id) ON DELETE CASCADE
            )
        """)
        
        # Таблица связей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_node_id INTEGER NOT NULL,
                to_node_id INTEGER NOT NULL,
                line_type TEXT DEFAULT 'solid',
                color TEXT DEFAULT '#000000',
                FOREIGN KEY (from_node_id) REFERENCES nodes (id) ON DELETE CASCADE,
                FOREIGN KEY (to_node_id) REFERENCES nodes (id) ON DELETE CASCADE,
                UNIQUE(from_node_id, to_node_id)
            )
        """)
        
        # Таблица содержимого узлов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS node_content (
                node_id INTEGER PRIMARY KEY,
                content TEXT DEFAULT '{}',
                FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
            )
        """)
        
        # Таблица списков дел
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS todo_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
            )
        """)
        
        # Таблица элементов списков дел
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS todo_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                todo_list_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (todo_list_id) REFERENCES todo_lists (id) ON DELETE CASCADE
            )
        """)
        
        # Таблица дат
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                date_type TEXT NOT NULL,
                date TIMESTAMP NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                reminder_enabled INTEGER DEFAULT 0,
                reminder_days_before INTEGER DEFAULT 1,
                FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
            )
        """)
        
        # Таблица файлов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
            )
        """)
        
        # Таблица настроек
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Миграция таблицы node_content
        self.cursor.execute("PRAGMA table_info(node_content)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if 'content' not in columns:
            self.cursor.execute("ALTER TABLE node_content ADD COLUMN content TEXT DEFAULT '{}'")
        
        self.conn.commit()
    
    def save_setting(self, key: str, value: str):
        """Сохранение настройки"""
        encrypted_value = self.encrypt_data(value) if self.key else value
        self.cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, encrypted_value))
        self.conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Получение настройки"""
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        if row:
            value = row['value']
            return self.decrypt_data(value) if self.key else value
        return default
    
    def create_root_node(self) -> Node:
        """Создание корневого узла 'Жизнь'"""
        # Проверяем, существует ли уже корневой узел
        self.cursor.execute("SELECT * FROM nodes WHERE parent_id IS NULL")
        root = self.cursor.fetchone()
        
        if root:
            return self._row_to_node(root)
        
        # Создаем корневой узел
        self.cursor.execute("""
            INSERT INTO nodes (title, parent_id, position_x, position_y)
            VALUES (?, NULL, 0, 0)
        """, ("Жизнь",))
        self.conn.commit()
        
        node_id = self.cursor.lastrowid
        return Node(
            id=node_id,
            title="Жизнь",
            parent_id=None,
            position_x=0,
            position_y=0
        )
    
    def add_node(self, title: str, parent_id: Optional[int] = None, 
                 x: float = 0, y: float = 0) -> Node:
        """Добавление нового узла"""
        self.cursor.execute("""
            INSERT INTO nodes (title, parent_id, position_x, position_y)
            VALUES (?, ?, ?, ?)
        """, (title, parent_id, x, y))
        self.conn.commit()
        
        node_id = self.cursor.lastrowid
        return Node(
            id=node_id,
            title=title,
            parent_id=parent_id,
            position_x=x,
            position_y=y
        )
    
    def delete_node(self, node_id: int):
        """Удаление узла и всех его потомков"""
        self.cursor.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        self.conn.commit()
    
    def update_node_position(self, node_id: int, x: float, y: float):
        """Обновление позиции узла"""
        self.cursor.execute("""
            UPDATE nodes SET position_x = ?, position_y = ? WHERE id = ?
        """, (x, y, node_id))
        self.conn.commit()
    
    def update_node_title(self, node_id: int, title: str):
        """Обновление заголовка узла"""
        self.cursor.execute("""
            UPDATE nodes SET title = ? WHERE id = ?
        """, (title, node_id))
        self.conn.commit()
    
    def update_node_color(self, node_id: int, color: str):
        """Обновление цвета узла"""
        self.cursor.execute("""
            UPDATE nodes SET color = ? WHERE id = ?
        """, (color, node_id))
        self.conn.commit()
    
    def toggle_node_collapsed(self, node_id: int):
        """Переключение состояния свернутости узла"""
        self.cursor.execute("""
            UPDATE nodes SET collapsed = NOT collapsed WHERE id = ?
        """, (node_id,))
        self.conn.commit()
    
    def add_edge(self, from_node_id: int, to_node_id: int, 
                 line_type: LineType = LineType.SOLID, color: str = "#000000") -> Edge:
        """Добавление связи между узлами"""
        self.cursor.execute("""
            INSERT INTO edges (from_node_id, to_node_id, line_type, color)
            VALUES (?, ?, ?, ?)
        """, (from_node_id, to_node_id, line_type.value, color))
        self.conn.commit()
        
        edge_id = self.cursor.lastrowid
        return Edge(
            id=edge_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            line_type=line_type,
            color=color
        )
    
    def delete_edge(self, edge_id: int):
        """Удаление связи"""
        self.cursor.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        self.conn.commit()
    
    def get_node(self, node_id: int) -> Optional[Node]:
        """Получение узла по ID"""
        self.cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = self.cursor.fetchone()
        if row:
            return self._row_to_node(row)
        return None
    
    def get_all_nodes(self) -> List[Node]:
        """Получение всех узлов"""
        self.cursor.execute("SELECT * FROM nodes ORDER BY parent_id")
        rows = self.cursor.fetchall()
        return [self._row_to_node(row) for row in rows]
    
    def get_children(self, parent_id: int) -> List[Node]:
        """Получение дочерних узлов"""
        self.cursor.execute("SELECT * FROM nodes WHERE parent_id = ?", (parent_id,))
        rows = self.cursor.fetchall()
        return [self._row_to_node(row) for row in rows]
    
    def get_all_edges(self) -> List[Edge]:
        """Получение всех связей"""
        self.cursor.execute("SELECT * FROM edges")
        rows = self.cursor.fetchall()
        return [self._row_to_edge(row) for row in rows]
    
    def get_edges_from_node(self, node_id: int) -> List[Edge]:
        """Получение исходящих связей узла"""
        self.cursor.execute("SELECT * FROM edges WHERE from_node_id = ?", (node_id,))
        rows = self.cursor.fetchall()
        return [self._row_to_edge(row) for row in rows]
    
    def _row_to_node(self, row) -> Node:
        """Преобразование строки БД в объект Node"""
        node = Node(
            id=row['id'],
            title=row['title'],
            parent_id=row['parent_id'],
            color=row['color'],
            position_x=row['position_x'],
            position_y=row['position_y'],
            collapsed=bool(row['collapsed']),
            created_at=datetime.fromisoformat(row['created_at']) 
            if isinstance(row['created_at'], str) else row['created_at']
        )
        node.content = self.load_node_content(node.id)
        return node
    
    def _row_to_edge(self, row) -> Edge:
        """Преобразование строки БД в объект Edge"""
        return Edge(
            id=row['id'],
            from_node_id=row['from_node_id'],
            to_node_id=row['to_node_id'],
            line_type=LineType(row['line_type']),
            color=row['color']
        )
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_node_edges(self, node_id: int):
        """Получение всех связей узла (и входящих, и исходящих)"""
        self.cursor.execute("""
            SELECT * FROM edges 
            WHERE from_node_id = ? OR to_node_id = ?
        """, (node_id, node_id))
        rows = self.cursor.fetchall()
        return [self._row_to_edge(row) for row in rows]

    def has_children(self, node_id: int) -> bool:
        """Проверка, есть ли у узла дочерние узлы"""
        self.cursor.execute("SELECT COUNT(*) as count FROM nodes WHERE parent_id = ?", (node_id,))
        row = self.cursor.fetchone()
        return row['count'] > 0 if row else False

    def get_node_by_id(self, node_id: int):
        """Получение узла по ID (альтернативное имя для get_node)"""
        return self.get_node(node_id)
    
    def get_all_descendants(self, node_id: int) -> List[int]:
        """Рекурсивно получить ID всех потомков узла (включая сам узел)"""
        descendants = [node_id]
    
        # Получаем прямых детей
        self.cursor.execute("SELECT id FROM nodes WHERE parent_id = ?", (node_id,))
        children = self.cursor.fetchall()
    
        # Рекурсивно получаем потомков каждого ребенка
        for child in children:
            child_id = child['id']
            descendants.extend(self.get_all_descendants(child_id))
    
        return descendants
    
    def get_all_descendants_iterative(self, node_id: int) -> List[int]:
        """Итеративно получить ID всех потомков узла (включая сам узел)"""
        descendants = []
        stack = [node_id]
    
        while stack:
            current_id = stack.pop()
            descendants.append(current_id)
        
            # Получаем детей текущего узла
            self.cursor.execute("SELECT id FROM nodes WHERE parent_id = ?", (current_id,))
            children = self.cursor.fetchall()
        
            for child in children:
                stack.append(child['id'])
    
        return descendants
    
    def save_node_content(self, node_content):
        """Сохранение содержимого узла"""
        content_json = json.dumps(node_content.to_dict())
        encrypted = self.encrypt_data(content_json)
        self.cursor.execute("""
            INSERT OR REPLACE INTO node_content (node_id, content)
            VALUES (?, ?)
        """, (node_content.node_id, encrypted))
        self.conn.commit()
    
    def load_node_content(self, node_id: int):
        """Загрузка содержимого узла"""
        self.cursor.execute("SELECT content FROM node_content WHERE node_id = ?", (node_id,))
        row = self.cursor.fetchone()
        if row:
            decrypted = self.decrypt_data(row['content'])
            data = json.loads(decrypted)
            tabs = []
            for tab_data in data.get('tabs', []):
                tab = ContentTab(
                    tab_id=tab_data['tab_id'],
                    tab_type=ContentTabType(tab_data['tab_type']),
                    title=tab_data['title'],
                    data=tab_data['data']
                )
                tabs.append(tab)
            return NodeContent(node_id=node_id, tabs=tabs)
        return None


class DatabaseManager:
    """Менеджер базы данных с поддержкой сессий"""
    
    def __init__(self, db_path: str = "data/lifemap.db", password: str = None):
        self.db_path = db_path
        self.password = password
        self._attachments_dir = Path("data/attachments")
        self._attachments_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session(self) -> EncryptedSQLite:
        """Получение новой сессии БД"""
        return EncryptedSQLite(self.db_path, self.password)
    
    @property
    def attachments_dir(self) -> Path:
        """Директория для вложений"""
        return self._attachments_dir
