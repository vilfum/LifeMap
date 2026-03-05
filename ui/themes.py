"""
Управление темами оформления
"""

"""
========================================================================
МЕНЕДЖЕР ТЕМ "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Цветовые схемы и логика их применения являются
                 интеллектуальной собственностью автора.
========================================================================
"""

from pathlib import Path
from PyQt6.QtWidgets import QApplication

_dark_mode = False



STYLES_DIR = Path("resources/styles")


def apply_theme(dark_mode: bool):
    """Применяет светлую или темную тему"""

    app = QApplication.instance()

    # отключаем системные стили
    app.setStyle("Fusion")

    theme_file = "dark.qss" if dark_mode else "light.qss"
    theme_path = STYLES_DIR / theme_file

    with open(theme_path, "r", encoding="utf-8") as f:
        stylesheet = f.read()

    app.setStyleSheet(stylesheet)

def set_dark_mode(enabled: bool):
    """Установить глобальное состояние темной темы"""
    global _dark_mode
    _dark_mode = enabled

def is_dark_mode() -> bool:
    """Получить текущее состояние темной темы"""
    return _dark_mode

# def get_stylesheet() -> str:
#     """Загрузить и вернуть stylesheet для текущей темы"""
#     style_file = Path("resources/styles/dark.qss" if _dark_mode else "resources/styles/light.qss")
#     if style_file.exists():
#         return style_file.read_text(encoding='utf-8')
#     return ""