"""
Сервис для операций с графом (узлы и связи)
"""

"""
========================================================================
СЕРВИС ДЛЯ РАБОТЫ С ГРАФОМ
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Алгоритмы управления графом являются
                 интеллектуальной собственностью автора.
========================================================================
"""

from typing import List, Optional, Tuple
from core.file_service import FileService
from core.models import Node, Edge


class GraphService:
    """Сервис для операций над узлами и связями"""

    def __init__(self, db_session):
        self.db_session = db_session
        self.file_service = FileService()

    # ----- Узлы -----

    def add_node(self, title: str, parent_id: Optional[int], x: float, y: float) -> Node:
        """Создает узел в БД и возвращает его"""
        return self.db_session.add_node(title, parent_id, x, y)

    def add_child_node(self, parent_id: int, title: str, x: float, y: float) -> Tuple[Node, Edge]:
        """Создает дочерний узел и связь с родителем, возвращает (узел, ребро)"""
        node = self.db_session.add_node(title, parent_id, x, y)
        edge = self.db_session.add_edge(parent_id, node.id)
        return node, edge

    def get_node(self, node_id: int) -> Optional[Node]:
        """Возвращает узел по ID"""
        return self.db_session.get_node(node_id)

    def get_all_nodes(self) -> List[Node]:
        """Возвращает все узлы"""
        return self.db_session.get_all_nodes()

    def is_descendant(self, candidate: Node, ancestor: Node) -> bool:
        """Возвращает True, если candidate является (в любом поколении) потомком ancestor."""
        cur_id = candidate.parent_id
        while cur_id is not None:
            if cur_id == ancestor.id:
                return True
            cur = self.get_node(cur_id)
            cur_id = cur.parent_id if cur else None
        return False

    def change_parent(self, node_id: int, new_parent_id: int) -> Tuple[Optional[int], int, Optional[int], int]:
        """Перемещает узел на новый родитель.

        Возвращает кортеж (old_parent_id, new_parent_id, old_edge_id, new_edge_id).
        Если старой связи не было, old_edge_id == None.
        """
        node = self.get_node(node_id)
        if not node:
            return None, new_parent_id, None, None

        old_parent_id = node.parent_id
        if old_parent_id == new_parent_id:
            return old_parent_id, new_parent_id, None, None

        old_edge_id = None
        # Удаляем старую связь (если была)
        if old_parent_id is not None:
            for edge in self.get_all_edges():
                if edge.from_node_id == old_parent_id and edge.to_node_id == node_id:
                    old_edge_id = edge.id
                    self.delete_edge(edge.id)
                    break

        # меняем parent_id непосредственно в таблице nodes
        self.db_session.update_node_parent(node_id, new_parent_id)

        # добавляем новую связь
        new_edge = self.add_edge(new_parent_id, node_id)
        new_edge_id = new_edge.id if new_edge else None

        # debug log
        print(f"GraphService.change_parent: node={node_id} old_parent={old_parent_id} new_parent={new_parent_id} "
              f"old_edge={old_edge_id} new_edge={new_edge_id}")

        return old_parent_id, new_parent_id, old_edge_id, new_edge_id

    def get_children(self, parent_id: int) -> List[Node]:
        """Возвращает прямых потомков узла"""
        return self.db_session.get_children(parent_id)

    def get_all_descendants(self, node_id: int) -> List[int]:
        """Возвращает список ID всех потомков (включая самого себя)"""
        try:
            return self.db_session.get_all_descendants(node_id)
        except RecursionError:
            return self.db_session.get_all_descendants_iterative(node_id)

    def update_node_position(self, node_id: int, x: float, y: float) -> None:
        """Обновляет позицию узла"""
        self.db_session.update_node_position(node_id, x, y)

    def update_node_color(self, node_id: int, color: str) -> None:
        """Обновляет цвет узла"""
        self.db_session.update_node_color(node_id, color)

    def toggle_node_collapsed(self, node_id: int) -> None:
        """Переключает состояние свернутости узла"""
        self.db_session.toggle_node_collapsed(node_id)

    def delete_node(self, node_id: int) -> Tuple[List[int], List[int]]:
        """
        Удаляет узел и всех его потомков.
        Возвращает (список удаленных node_id, список удаленных edge_id)
        """
        node = self.get_node(node_id)
        if not node:
            return [], []

        parent_id = node.parent_id
        all_descendants = self.get_all_descendants(node_id)

        # Удаляем папки attachments для всех удаляемых узлов
        for descendant_id in all_descendants:
            try:
                self.file_service.delete_node_folder(descendant_id)
            except Exception as e:
                print(f"Ошибка удаления папки узла {descendant_id}: {e}")

        # Собираем все ребра, которые будут удалены (те, что связаны с удаляемыми узлами)
        edges_to_delete = []
        for descendant_id in all_descendants:
            edges_to_delete.extend(self.get_edges_for_node(descendant_id))

        # Удаляем узел из БД (потомки удалятся каскадно)
        self.db_session.delete_node(node_id)

        return all_descendants, list(set(edges_to_delete))  # уникальные ID ребер

    # ----- Ребра -----

    def add_edge(self, from_node_id: int, to_node_id: int) -> Edge:
        """Создает связь между узлами"""
        return self.db_session.add_edge(from_node_id, to_node_id)

    def get_all_edges(self) -> List[Edge]:
        """Возвращает все ребра"""
        return self.db_session.get_all_edges()

    def get_edges_for_node(self, node_id: int) -> List[int]:
        """Возвращает ID всех ребер, связанных с узлом"""
        edges = self.db_session.get_node_edges(node_id)
        return [e.id for e in edges]

    def delete_edge(self, edge_id: int) -> None:
        """Удаляет связь по ID"""
        self.db_session.delete_edge(edge_id)

    def commit(self):
        """Фиксирует текущую транзакцию"""
        self.db_session.conn.commit()

    def close(self):
        """Закрывает сессию базы данных"""
        if self.db_session:
            self.db_session.close()