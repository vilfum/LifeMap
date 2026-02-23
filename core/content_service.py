"""
========================================================================
CONTENT SERVICE
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
Сервис управления содержимым узлов.
Отвечает за бизнес-логику вкладок и их модификацию.
========================================================================
"""

from typing import Optional, List
from core.models import NodeContent, ContentTab, ContentTabType


class ContentService:
    """Сервис для управления вкладками содержимого узла"""

    # =========================
    # TAB CRUD
    # =========================

    @staticmethod
    def add_tab(
        node_content: NodeContent,
        tab_type: ContentTabType,
        title: Optional[str] = None
    ) -> ContentTab:
        """Добавляет новую вкладку"""

        new_id = max((t.tab_id for t in node_content.tabs), default=0) + 1

        if title is None:
            title = tab_type.value.capitalize()

        tab = ContentTab(
            tab_id=new_id,
            tab_type=tab_type,
            title=title,
            data={}
        )

        node_content.tabs.append(tab)
        return tab

    @staticmethod
    def remove_tab(node_content: NodeContent, tab_id: int) -> None:
        """Удаляет вкладку"""
        node_content.tabs = [
            t for t in node_content.tabs
            if t.tab_id != tab_id
        ]

    @staticmethod
    def get_tab(
        node_content: NodeContent,
        tab_id: int
    ) -> Optional[ContentTab]:
        """Возвращает вкладку по ID"""
        for tab in node_content.tabs:
            if tab.tab_id == tab_id:
                return tab
        return None

    @staticmethod
    def move_tab(
        node_content: NodeContent,
        tab_id: int,
        new_index: int
    ) -> None:
        """Перемещает вкладку в новую позицию"""
        tab = ContentService.get_tab(node_content, tab_id)
        if not tab:
            return

        node_content.tabs.remove(tab)
        node_content.tabs.insert(new_index, tab)

    @staticmethod
    def reorder_tabs(
        node_content: NodeContent,
        tab_ids: List[int]
    ) -> None:
        """Переупорядочивает вкладки по списку ID"""

        new_tabs = []

        for tab_id in tab_ids:
            tab = ContentService.get_tab(node_content, tab_id)
            if tab:
                new_tabs.append(tab)

        node_content.tabs = new_tabs

    # =========================
    # TAB DATA UPDATE
    # =========================

    @staticmethod
    def update_tab_data(
        node_content: NodeContent,
        tab_id: int,
        new_data: dict
    ) -> None:
        """Обновляет данные вкладки"""
        tab = ContentService.get_tab(node_content, tab_id)
        if tab:
            tab.data = new_data

    @staticmethod
    def rename_tab(
        node_content: NodeContent,
        tab_id: int,
        new_title: str
    ) -> None:
        """Переименовывает вкладку"""
        tab = ContentService.get_tab(node_content, tab_id)
        if tab:
            tab.title = new_title
