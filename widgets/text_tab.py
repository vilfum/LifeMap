"""
Вкладка с текстовым редактором
"""

"""
========================================================================
ТЕКСТОВАЯ ВКЛАДКА
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Реализация текстового редактора является
                 интеллектуальной собственностью автора.
========================================================================
"""

from PyQt6.QtWidgets import QTextEdit, QVBoxLayout
from widgets import BaseTabWidget
from core.content_service import ContentService

class TextTabWidget(BaseTabWidget):
    """Виджет для текстовой вкладки"""
    def __init__(self, node_content, tab, parent=None):
        super().__init__(node_content, tab, parent)

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
        
        #self.tab.data["html"] = self.editor.toHtml()
        new_data = {"html": self.editor.toHtml()}
        ContentService.update_tab_data(self.node_content, self.tab.tab_id, new_data)
        #super().save_to_model()
        self._dirty = False  # Сбрасываем флаг изменений
        print("💾 TextTabWidget: данные сохранены, вкладка очищена")

