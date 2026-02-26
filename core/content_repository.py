"""
Репозиторий для сохранения и загрузки контента узлов
"""

"""
========================================================================
РЕПОЗИТОРИЙ СОДЕРЖИМОГО УЗЛОВ
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Методы доступа к данным являются
                 интеллектуальной собственностью автора.
========================================================================
"""

from core.models import NodeContent


class ContentRepository:

    @staticmethod
    def save(node_content: NodeContent, db_session):
        """Сохраняет содержимое узла в БД"""
        db_session.save_node_content(node_content)

    @staticmethod
    def load(node_id: int, db_session) -> NodeContent:
        """Загружает содержимое узла из БД"""
        return db_session.get_node_content(node_id)
