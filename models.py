"""
========================================================================
МОДЕЛИ ДАННЫХ ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Структуры данных и бизнес-логика являются
                 интеллектуальной собственностью автора.
========================================================================
"""

"""
Модели данных для карты жизни
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class LineType(Enum):
    """Типы линий связи"""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    BOLD = "bold"


class DateType(Enum):
    """Типы дат"""
    BIRTHDAY = "birthday"
    DEADLINE = "deadline"
    START_DATE = "start_date"
    END_DATE = "end_date"
    EVENT = "event"
    REMINDER = "reminder"


@dataclass
class TodoItem:
    """Элемент списка дел"""
    id: int
    text: str
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TodoList:
    """Список дел"""
    id: int
    title: str
    items: List[TodoItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def all_completed(self):
        return all(item.completed for item in self.items) if self.items else False


@dataclass
class DateItem:
    """Дата с типом"""
    id: int
    date_type: DateType
    date: datetime
    title: str
    description: str = ""
    reminder_enabled: bool = False
    reminder_days_before: int = 1
    
    def to_dict(self):
        return {
            'id': self.id,
            'date_type': self.date_type.value,
            'date': self.date.isoformat(),
            'title': self.title,
            'description': self.description,
            'reminder_enabled': self.reminder_enabled,
            'reminder_days_before': self.reminder_days_before
        }


@dataclass
class FileAttachment:
    """Прикрепленный файл"""
    id: int
    filename: str
    filepath: str  # Путь в папке attachments
    file_size: int
    mime_type: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat()
        }


@dataclass
class NodeContent:
    """Содержимое узла"""
    node_id: int
    html_content: str = ""
    text_content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Коллекции
    todo_lists: List[TodoList] = field(default_factory=list)
    dates: List[DateItem] = field(default_factory=list)
    attachments: List[FileAttachment] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'node_id': self.node_id,
            'html_content': self.html_content,
            'text_content': self.text_content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'todo_lists': [todo.to_dict() for todo in self.todo_lists],
            'dates': [date.to_dict() for date in self.dates],
            'attachments': [att.to_dict() for att in self.attachments]
        }


@dataclass
class Node:
    """Узел карты"""
    id: int
    title: str
    parent_id: Optional[int] = None
    color: str = "#3498db"  # Синий по умолчанию
    position_x: float = 0.0
    position_y: float = 0.0
    collapsed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    # Связи (заполняются отдельно)
    children: List['Node'] = field(default_factory=list)
    
    # Содержимое
    content: Optional[NodeContent] = None
    
    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'parent_id': self.parent_id,
            'color': self.color,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'collapsed': self.collapsed,
            'created_at': self.created_at.isoformat(),
            'children': [child.to_dict() for child in self.children]
        }
        if self.content:
            data['content'] = self.content.to_dict()
        return data


@dataclass
class Edge:
    """Связь между узлами"""
    id: int
    from_node_id: int
    to_node_id: int
    line_type: LineType = LineType.SOLID
    color: str = "#000000"
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'line_type': self.line_type.value,
            'color': self.color
        }
