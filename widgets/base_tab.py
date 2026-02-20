from PyQt6.QtWidgets import QWidget

class BaseTabWidget(QWidget):
    """Контракт для виджетов вкладок узла"""
    def __init__(self, node_content, tab, parent=None):
        super().__init__(parent)
        self.node_content = node_content
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
